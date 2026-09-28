"""Exercise the OS boundary with only task-owned synthetic files and sockets."""

import errno
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from boundary import command, current_limits, child_limits, landrun_arguments, UnsupportedBoundary


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="slean-boundary-test-")
        self.addCleanup(self.temporary.cleanup)
        self.control = Path(self.temporary.name).resolve()
        self.project = self.control / "project"
        self.build = self.project / ".lake"
        self.build.mkdir(parents=True)
        self.python = str(Path(sys.executable).resolve())
        self.config = {"readable": [str(self.project), str(Path(sys.base_prefix).resolve()), "/usr", "/bin"],
            "build_directory": str(self.build), "lake": "/usr/bin/true",
            "exporter": "/usr/bin/true", "environment": {"PATH": "/usr/bin:/bin"},
            "limits": current_limits()}

    def run_python(self, code, *, writable=True):
        script = self.project / "probe.py"
        script.write_text(code)
        result = subprocess.run(command(self.config, [self.python, str(script)],
            [str(self.build)] if writable else [], can_fork=False),
            cwd=self.project, env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
            text=True, capture_output=True, timeout=20,
            preexec_fn=lambda: child_limits(self.config["limits"]))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_read_own_input_and_write_only_build_directory(self):
        (self.project / "input.txt").write_text("allowed")
        report = self.run_python('''import errno,json,pathlib
assert pathlib.Path("input.txt").read_text() == "allowed"
pathlib.Path(".lake/result.txt").write_text("built")
try:
    pathlib.Path("input.txt").write_text("changed")
except PermissionError as error:
    print(json.dumps({"denied":error.errno}))
else:
    raise AssertionError("input changed")
''')
        self.assertIn(report["denied"], (errno.EPERM, errno.EACCES))
        self.assertEqual((self.project / "input.txt").read_text(), "allowed")
        self.assertEqual((self.build / "result.txt").read_text(), "built")

    def test_outside_file_read_write_and_symlink_escape_are_denied(self):
        outside = self.control / "outside.txt"
        outside.write_text("synthetic receiver marker")
        (self.build / "escape").symlink_to(outside)
        report = self.run_python('''import errno,json,pathlib
outside = pathlib.Path(''' + repr(str(outside)) + ''')
blocked = []
for operation in (outside.read_text, lambda: outside.write_text("changed"),
                  lambda: pathlib.Path(".lake/escape").write_text("changed")):
    try:
        operation()
    except PermissionError as error:
        assert error.errno in (errno.EPERM, errno.EACCES)
        blocked.append(True)
    else:
        raise AssertionError("outside access succeeded")
print(json.dumps({"denied":len(blocked)}))
''')
        self.assertEqual(report["denied"], 3)
        self.assertEqual(outside.read_text(), "synthetic receiver marker")

    def test_network_is_denied_even_with_a_live_listener(self):
        listener = socket.socket()
        self.addCleanup(listener.close)
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            connection, _ = listener.accept()
            connection.close()
        report = self.run_python('''import errno,json,socket
try:
    socket.create_connection(("127.0.0.1", ''' + str(port) + '''), timeout=1)
except PermissionError as error:
    print(json.dumps({"denied":error.errno}))
else:
    raise AssertionError("network connection succeeded")
''')
        self.assertIn(report["denied"], (errno.EPERM, errno.EACCES))

    def test_export_phase_has_no_build_write_access(self):
        report = self.run_python('''import errno,json,pathlib
try:
    pathlib.Path(".lake/new.txt").write_text("unexpected")
except PermissionError as error:
    print(json.dumps({"denied":error.errno}))
else:
    raise AssertionError("exporter wrote to build directory")
''', writable=False)
        self.assertIn(report["denied"], (errno.EPERM, errno.EACCES))

    def test_data_volume_alias_does_not_grant_access_to_receiver_files(self):
        outside = self.control / "outside.txt"
        outside.write_text("synthetic receiver marker")
        alias = Path("/System/Volumes/Data") / outside.relative_to("/")
        if not alias.is_file():
            self.skipTest("This host does not expose the Data volume alias")
        report = self.run_python('''import errno,json,pathlib
try:
    pathlib.Path(''' + repr(str(alias)) + ''').read_text()
except PermissionError as error:
    print(json.dumps({"denied":error.errno}))
else:
    raise AssertionError("outside read through Data volume alias succeeded")
''')
        self.assertIn(report["denied"], (errno.EPERM, errno.EACCES))

    def test_pinned_cli_subset_rejects_extra_authority(self):
        for arguments in (("--connect-tcp", "443", "--", "/usr/bin/true"),
                ("--rwx", str(self.control), "--", "/usr/bin/true"),
                ("--env", "SECRET", "--", "/usr/bin/true"),
                ("--", "/bin/sh", "-c", "true")):
            with self.subTest(arguments=arguments), self.assertRaises(UnsupportedBoundary):
                landrun_arguments(self.config, list(arguments))
        child, writable, environment = landrun_arguments(self.config,
            ["--best-effort", "--ro", "/", "--rw", "/dev", "-ldd", "-add-exec",
             "--env", "HOME", "--env", "PATH", "--rwx", str(self.build), "--", "lake", "build", "Solution"])
        self.assertEqual(child, ["/usr/bin/true", "build", "Solution"])
        self.assertEqual(writable, [str(self.build)])
        self.assertNotIn("HOME", environment)
        self.assertEqual(set(environment), {"PATH", "LEAN_ABORT_ON_PANIC", "LEAN_NUM_THREADS", "LEAN_SYSROOT"})
        self.assertEqual(environment["LEAN_SYSROOT"], "/usr")


if __name__ == "__main__":
    unittest.main()
