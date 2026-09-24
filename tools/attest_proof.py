#!/usr/bin/env python3
"""Bind local Lean proof receipts to one clean source tree and exact build."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / ".lake/build/bin/slean"
BUILD_FILES = {
    "executable": BIN,
    "core_olean": ROOT / ".lake/build/lib/lean/Slean/Core.olean",
    "export_olean": ROOT / ".lake/build/lib/lean/Slean/Export.olean",
    "proof_olean": ROOT / ".lake/build/lib/lean/Slean/Proof.olean",
    "library_olean": ROOT / ".lake/build/lib/lean/Slean.olean",
    "main_olean": ROOT / ".lake/build/lib/lean/Main.olean",
    "lake_manifest": ROOT / "lake-manifest.json",
    "lean_toolchain": ROOT / "lean-toolchain",
}


def command(*args: str, input_text: str | None = None) -> str:
    result = subprocess.run(args, cwd=ROOT, input=input_text, text=True,
                            capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"{args[0]} failed ({result.returncode}): {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def digest(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"build artifact is missing: {path.relative_to(ROOT)}")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def require_clean() -> None:
    if command("git", "status", "--porcelain", "--untracked-files=normal"):
        raise ValueError("exact-build attestation requires a clean source tree")


def attest(case_path: Path, audience: str) -> dict:
    require_clean()
    source_revision = command("git", "rev-parse", "HEAD")
    source_tree = command("git", "rev-parse", "HEAD^{tree}")
    toolchain = (ROOT / "lean-toolchain").read_text(encoding="utf-8").strip()
    if toolchain != "leanprover/lean4:v4.28.0":
        raise ValueError("Lean toolchain differs from the reviewed proof pin")
    lean_version = command("lean", "--version")
    if "version 4.28.0" not in lean_version:
        raise ValueError("active Lean version differs from the reviewed proof pin")

    command("lake", "build")
    require_clean()
    built = {name: digest(path) for name, path in BUILD_FILES.items()}
    build = {
        "source_revision": source_revision,
        "source_tree": source_tree,
        "source_tree_clean": True,
        "toolchain": toolchain,
        "lean_version": lean_version,
        "artifacts": built,
    }
    build_bytes = json.dumps(build, sort_keys=True, separators=(",", ":")).encode("utf-8")
    build_id = "sha256:" + hashlib.sha256(build_bytes).hexdigest()

    command(str(BIN), "validate", str(case_path))
    exported = command(str(BIN), "export", str(case_path), audience)
    projected_export_id = "sha256:" + hashlib.sha256(exported.encode("utf-8")).hexdigest()
    pin = json.loads(command(str(BIN), "proof-statement"))
    receipts = json.loads(command(str(BIN), "proof", "-", input_text=exported))
    if not isinstance(receipts, list) or not receipts:
        raise ValueError("case has no formal claim to attest")
    for receipt in receipts:
        if receipt["status"] != "declared":
            raise ValueError("CLI emitted a formal status before exact-build attestation")
        if receipt["attestation_eligible"] is True:
            for key in ("declaration", "elaborated_statement", "toolchain", "dependencies"):
                if receipt[key] != pin[key]:
                    raise ValueError(f"checked proof {key} differs from the reviewed pin")
            receipt["status"] = "kernel_checked"
            receipt["exact_build_ref"] = build_id
            receipt["exact_export_ref"] = projected_export_id
        elif receipt["attestation_eligible"] is False:
            receipt["exact_build_ref"] = None
            receipt["exact_export_ref"] = None
        else:
            raise ValueError("CLI emitted an invalid attestation eligibility flag")
    if built != {name: digest(path) for name, path in BUILD_FILES.items()}:
        raise ValueError("build artifacts changed during receipt generation")
    require_clean()
    if command("git", "rev-parse", "HEAD") != source_revision:
        raise ValueError("source revision changed during receipt generation")
    return {"format": "slean-proof-attestation/0.1.0", "build_id": build_id,
            "build": build, "audience": audience, "projected_export_id": projected_export_id,
            "receipts": receipts,
            "trust_limit": "Lake, the CLI exporter and this Python attester are trusted code; this is not an independent kernel recheck."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path, help="case JSON or versioned export envelope")
    parser.add_argument("--audience", choices=("agent", "owner"), default="agent")
    args = parser.parse_args()
    try:
        result = attest(args.case.resolve(), args.audience)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"proof attestation failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
