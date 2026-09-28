"""Check that stalled or noisy subprocesses cannot hold the caller forever."""

from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_comparator import bounded_output


class ProcessTests(unittest.TestCase):
    def spawn(self, code):
        return subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, start_new_session=True)

    def test_exit_status_and_diagnostics_remain_available(self):
        process = self.spawn("print('diagnostic'); raise SystemExit(7)")
        output, reason = bounded_output(process, 5)
        self.assertEqual(output, "diagnostic\n")
        self.assertIsNone(reason)
        self.assertEqual(process.returncode, 7)

    def test_output_flood_is_bounded(self):
        process = self.spawn("import os\nwhile True: os.write(1, b'x' * 65536)")
        output, reason = bounded_output(process, 5, max_bytes=1024)
        self.assertEqual(len(output), 1024)
        self.assertEqual(reason, "output_limit")
        self.assertIsNotNone(process.returncode)

    def test_timeout_also_covers_a_process_that_closes_stdout(self):
        process = self.spawn("import os,time; os.close(1); os.close(2); time.sleep(20)")
        _, reason = bounded_output(process, 0.5)
        self.assertEqual(reason, "timeout")
        self.assertIsNotNone(process.returncode)

    def test_timeout_covers_pipe_held_by_a_descendant(self):
        process = self.spawn("import subprocess,sys; "
            "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)'])")
        _, reason = bounded_output(process, 0.5)
        self.assertEqual(reason, "timeout")
        self.assertIsNotNone(process.returncode)


if __name__ == "__main__":
    unittest.main()
