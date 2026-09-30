"""Byte-preserving, bounded streaming for receiver-owned proof exports."""
import io
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'verification'))
from run_comparator import bounded_output


class StreamedExportTests(unittest.TestCase):
    def child(self, code):
        return subprocess.Popen([sys.executable, '-c', code], stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, start_new_session=True)

    def test_export_bytes_are_preserved_without_a_returned_copy(self):
        sink = io.BytesIO()
        process = self.child('import sys; sys.stdout.buffer.write(bytes(range(256)) * 1024)')
        output, stopped = bounded_output(process, 10, max_bytes=300000, sink=sink)
        self.assertIsNone(stopped)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(output, '')
        self.assertEqual(sink.getvalue(), bytes(range(256)) * 1024)

    def test_export_byte_limit_stops_before_overflow(self):
        sink = io.BytesIO()
        process = self.child('import sys,time; sys.stdout.buffer.write(b"x" * 100000); sys.stdout.flush(); time.sleep(30)')
        _, stopped = bounded_output(process, 10, max_bytes=4096, sink=sink)
        self.assertEqual(stopped, 'output_limit')
        self.assertEqual(sink.getvalue(), b'x' * 4096)
        self.assertIsNotNone(process.returncode)

    def test_export_deadline_terminates_a_live_process(self):
        sink = io.BytesIO()
        process = self.child('import sys,time; sys.stdout.buffer.write(b"prefix"); sys.stdout.flush(); time.sleep(30)')
        _, stopped = bounded_output(process, 0.2, max_bytes=4096, sink=sink)
        self.assertEqual(stopped, 'timeout')
        self.assertEqual(sink.getvalue(), b'prefix')
        self.assertLess(process.returncode, 0)


if __name__ == '__main__':
    unittest.main()
