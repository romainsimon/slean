# Generated from the receiver-owned Lean boundary by generate_runtime.py.
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
