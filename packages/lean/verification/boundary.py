"""Restricted local execution for the pinned Comparator integration.

Only a receiver-created policy file can choose filesystem roots. Candidate
code cannot change the policy or choose the sandbox implementation.
"""

import json
import os
from pathlib import Path
import resource
import subprocess
import sys


class UnsupportedBoundary(RuntimeError):
    pass


def real(path):
    return str(Path(path).resolve(strict=True))


def darwin_profile(readable, writable, *, can_fork):
    if sys.platform != "darwin" or not Path("/usr/bin/sandbox-exec").is_file():
        raise UnsupportedBoundary("macOS sandbox-exec is required by this backend")
    # Root-directory reads are required by current macOS process startup.
    # This is a literal directory permission, not a recursive root grant.
    lines = ["(version 1)", "(deny default)", "(deny network*)",
        "(allow process-exec sysctl-read file-read-metadata)",
        '(allow file-read* (literal "/") (subpath "/usr") (subpath "/System/Library") '
        '(subpath "/System/Cryptexes") '
        '(subpath "/Library/Developer") (subpath "/private/preboot") '
        '(subpath "/private/var/db/dyld") (literal "/dev/null") (literal "/dev/urandom"))',
        '(allow file-write* (literal "/dev/null"))',
        '(allow mach-lookup (global-name "com.apple.logd") (global-name "com.apple.system.logger"))']
    if can_fork:
        lines.append("(allow process-fork)")
    for path in sorted(set(map(real, readable))):
        lines.append("(allow file-read* (subpath " + json.dumps(path) + "))")
    for path in sorted(set(map(real, writable))):
        lines.append("(allow file-read* file-write* (subpath " + json.dumps(path) + "))")
    return "\n".join(lines)


def child_limits(limits):
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    for key, limit in (("cpu_seconds", resource.RLIMIT_CPU),
                       ("file_bytes", resource.RLIMIT_FSIZE),
                       ("address_bytes", resource.RLIMIT_AS),
                       ("open_files", resource.RLIMIT_NOFILE),
                       ("user_process_ceiling", resource.RLIMIT_NPROC)):
        value = limits[key]
        if value is not None:
            resource.setrlimit(limit, (value, value))


def command(config, arguments, writable=(), *, can_fork=False):
    profile = darwin_profile(config["readable"], writable, can_fork=can_fork)
    return ["/usr/bin/sandbox-exec", "-p", profile, *arguments]


def current_limits():
    # RLIMIT_NPROC is per user. Count current processes, then allow a bounded
    # allowance for this execution; do not alter limits of existing processes.
    processes = subprocess.check_output(["/bin/ps", "-u", str(os.getuid()), "-o", "pid="], text=True)
    return {"cpu_seconds": 300, "file_bytes": 256 * 1024 * 1024,
        # Darwin aliases RLIMIT_AS to the unsupported RSS limit. Do not report
        # a hard memory cap that this OS cannot enforce through setrlimit.
        "address_bytes": None if sys.platform == "darwin" else 8 * 1024 * 1024 * 1024,
        "open_files": 1024,
        "user_process_ceiling": len(processes.splitlines()) + 32}


def read_policy():
    path = os.environ.get("SLEAN_SANDBOX_CONFIG")
    if not path:
        raise UnsupportedBoundary("Missing receiver sandbox policy")
    config = json.loads(Path(path).read_text())
    if config.get("format") != "slean-comparator-boundary/0.1-draft.1":
        raise UnsupportedBoundary("Unsupported sandbox policy")
    if Path(config["project"]).resolve() != Path.cwd().resolve():
        raise UnsupportedBoundary("Sandbox project mismatch")
    return config


def landrun_arguments(config, arguments):
    """Accept only the pinned upstream CLI subset, capped by receiver roots."""
    writable, env_names = [], []
    index = 0
    while index < len(arguments):
        flag = arguments[index]
        index += 1
        if flag == "--":
            break
        if flag in {"--best-effort", "-ldd", "-add-exec"}:
            continue
        if flag not in {"--ro", "--rw", "--rwx", "--rox", "--env"} or index == len(arguments):
            raise UnsupportedBoundary("Unsupported comparator sandbox flag: " + flag)
        value = arguments[index]
        index += 1
        if flag == "--env":
            if value not in {"PATH", "HOME", "LEAN_PATH", "LEAN_ABORT_ON_PANIC"}:
                raise UnsupportedBoundary("Unsupported environment request")
            env_names.append(value)
        elif flag in {"--rw", "--rwx"}:
            if flag == "--rw" and value == "/dev":
                continue  # Only /dev/null is writable, never arbitrary devices.
            if real(value) != real(config["build_directory"]):
                raise UnsupportedBoundary("Write outside the receiver build directory")
            writable.append(value)
        elif flag == "--ro" and value == "/":
            continue  # Upstream's broad read request is capped by the fixed profile.
        elif not any(Path(real(value)).is_relative_to(Path(root)) for root in config["readable"]):
            raise UnsupportedBoundary("Read/execute request outside receiver roots")
    else:
        raise UnsupportedBoundary("Missing command delimiter")
    child = arguments[index:]
    if not child:
        raise UnsupportedBoundary("Missing sandbox command")
    if child[0] == "lake":
        child[0] = config["lake"]
        if len(child) != 3 or child[1] != "build" or child[2] not in {"Challenge", "Solution"}:
            raise UnsupportedBoundary("Unsupported build command")
    elif real(child[0]) != real(config["exporter"]):
        raise UnsupportedBoundary("Unsupported sandbox executable")
    environment = {name: config["environment"][name] for name in env_names if name in config["environment"]}
    environment["LEAN_ABORT_ON_PANIC"] = "1"
    environment["LEAN_NUM_THREADS"] = "2"
    # findSysroot otherwise spawns `lean --print-prefix`. The exporter needs
    # no child processes: bind its sysroot to the receiver's executable.
    environment["LEAN_SYSROOT"] = str(Path(config["lake"]).resolve().parents[1])
    return child, writable, environment


def landrun_main(arguments):
    config = read_policy()
    child, writable, environment = landrun_arguments(config, arguments)
    child_limits(config["limits"])
    os.execve("/usr/bin/sandbox-exec", command(config, child, writable, can_fork=bool(writable)), environment)
