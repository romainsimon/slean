"""Execute the pinned comparator in a fresh, receiver-controlled local project.

This primitive establishes a proof comparison under the recorded local policy.
It does not yet issue Slean module-bound verification receipts.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import tempfile
import time

from boundary import child_limits, current_limits, darwin_profile, real, UnsupportedBoundary

HERE = Path(__file__).resolve().parent
DEFAULT_TOOLCHAIN = Path.home() / ".elan/toolchains/leanprover--lean4---v4.34.1"
TOOLS = HERE / ".lake/packages"
COMPARATOR = TOOLS / "Comparator/.lake/build/bin/comparator"
EXPORTER = TOOLS / "lean4export/.lake/build/bin/lean4export"
MAX_SOURCE_BYTES = 1024 * 1024
MAX_LOG_BYTES = 4 * 1024 * 1024
TOOLCHAIN = "leanprover/lean4:v4.34.1"


def bounded_output(process, timeout, *, max_bytes=MAX_LOG_BYTES):
    """Bound captured diagnostics and wall time, including inherited pipes."""
    output = bytearray()
    deadline = time.monotonic() + timeout
    reason = None
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                reason = "timeout"
                break
            for key, _ in selector.select(min(remaining, 0.1)):
                block = os.read(key.fileobj.fileno(), 65536)
                if not block:
                    selector.unregister(key.fileobj)
                    continue
                available = max_bytes - len(output)
                output.extend(block[:available])
                if len(block) > available:
                    reason = "output_limit"
                    break
            if reason:
                break
    if reason:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=max(0.01, deadline - time.monotonic()) if not reason else 10)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)
        reason = "timeout"
    finally:
        process.stdout.close()
    return output.decode("utf-8", errors="replace"), reason


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def compare(challenge, solution, names, *, toolchain=DEFAULT_TOOLCHAIN, timeout=600):
    if not names or len(set(names)) != len(names):
        raise ValueError("Select distinct theorem names")
    if any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*", name) for name in names):
        raise UnsupportedBoundary("This primitive supports only ordinary ASCII declaration names")
    if not 0 < timeout <= 600:
        raise ValueError("Timeout must be positive and at most 600 seconds")
    toolchain = toolchain.resolve(strict=True)
    for binary in (COMPARATOR, EXPORTER, toolchain / "bin/lean", toolchain / "bin/lake"):
        if not binary.is_file():
            raise UnsupportedBoundary("Missing pinned verification tool: " + str(binary))
    if os.getuid() == 0:
        raise UnsupportedBoundary("Proof comparison must run without root privileges")
    clean_path = str(toolchain / "bin") + ":/usr/bin:/bin"
    version = subprocess.run([str(toolchain / "bin/lean"), "--version"], env={"PATH": clean_path},
        capture_output=True, text=True, timeout=20, check=True).stdout.strip()
    if not version.startswith("Lean (version 4.34.1,"):
        raise UnsupportedBoundary("The pinned Lean 4.34.1 toolchain is required")
    source_bytes = {}
    for name, source in (("Challenge.lean", challenge), ("Solution.lean", solution)):
        with Path(source).open("rb") as stream:
            source_bytes[name] = stream.read(MAX_SOURCE_BYTES + 1)
        if len(source_bytes[name]) > MAX_SOURCE_BYTES:
            raise UnsupportedBoundary("Source exceeds the local primitive's 1 MiB limit")
    expected_sources = {name: hashlib.sha256(value).hexdigest() for name, value in source_bytes.items()}
    before = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="slean-comparator-") as temporary:
        control = Path(temporary).resolve()
        project = control / "project"
        build = project / ".lake"
        build.mkdir(parents=True)
        for name, value in source_bytes.items():
            (project / name).write_bytes(value)
        (project / "lean-toolchain").write_text(TOOLCHAIN + "\n")
        (project / "lakefile.toml").write_text('name = "slean_check"\nversion = "0.1.0"\n'
            '[[lean_lib]]\nname = "Challenge"\n[[lean_lib]]\nname = "Solution"\n')
        (project / "lake-manifest.json").write_text(json.dumps({"version": "1.2.0",
            "packagesDir": ".lake/packages", "packages": [], "name": "slean_check",
            "lakeDir": ".lake", "fixedToolchain": True}))
        config = {"challenge_module": "Challenge", "solution_module": "Solution",
            "theorem_names": names, "permitted_axioms": ["propext", "Quot.sound", "Classical.choice"]}
        config_path = control / "comparator.json"
        config_path.write_text(json.dumps(config))
        environment = {"PATH": clean_path,
            "LEAN_PATH": str(build / "build/lib/lean"), "LEAN_ABORT_ON_PANIC": "1"}
        policy = {"format": "slean-comparator-boundary/0.1-draft.1",
            "project": real(project), "build_directory": real(build),
            "lake": real(toolchain / "bin/lake"), "exporter": real(EXPORTER),
            "readable": [real(project), real(toolchain), real(TOOLS), "/usr", "/bin"],
            "environment": environment, "limits": current_limits()}
        policy_path = control / "boundary.json"
        policy_path.write_text(json.dumps(policy))
        darwin_profile(policy["readable"], [str(build)], can_fork=True)
        child_environment = {**environment, "COMPARATOR_LANDRUN": str(HERE / "darwin_landrun.py"),
            "COMPARATOR_LEAN4EXPORT": str(EXPORTER), "SLEAN_SANDBOX_CONFIG": str(policy_path)}
        process = subprocess.Popen([str(COMPARATOR), str(config_path)], cwd=project, env=child_environment,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True,
            preexec_fn=lambda: child_limits(policy["limits"]))
        output, stop_reason = bounded_output(process, timeout)
        outcome = stop_reason or ("tool_failure" if "PANIC" in output else
            "passed" if process.returncode == 0 and "Your solution is okay!" in output else "failed")
        # Build code cannot write either source or the policy/configuration.
        source_hashes = {name: digest(project / name) for name in ("Challenge.lean", "Solution.lean")}
        if source_hashes != expected_sources:
            raise RuntimeError("Proof source changed during comparison")
        return {"format": "slean-comparator-run/0.1-draft.1", "outcome": outcome,
            "exit_code": process.returncode, "theorems": names, "sources": source_hashes,
            "comparator_sha256": digest(COMPARATOR), "exporter_sha256": digest(EXPORTER),
            "toolchain": TOOLCHAIN, "lean_version": version, "isolation": "macos-sandbox-exec",
            "network": "denied", "environment": "receiver whitelist; no inherited credentials",
            "limits": {**policy["limits"], "wall_seconds": timeout, "log_bytes": MAX_LOG_BYTES,
                       "source_bytes_each": MAX_SOURCE_BYTES},
            "seconds": round(time.monotonic() - before, 3),
            "log": output, "module_receipt": "not_issued", "slean_policy": "unsupported",
            "limitations": ["No hard memory or aggregate disk quota on this backend",
                "Local primitive tested with reviewed fixtures; not a hostile-upload service",
                "No receiver Slean-module reconstruction or receipt authority",
                "No separately implemented external proof kernel"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--challenge", type=Path, required=True)
    parser.add_argument("--solution", type=Path, required=True)
    parser.add_argument("--theorem", action="append", required=True)
    args = parser.parse_args()
    result = compare(args.challenge, args.solution, args.theorem)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["outcome"] == "passed" else 1)
