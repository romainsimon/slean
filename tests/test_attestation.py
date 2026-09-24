"""Check that proof references identify bytes users can reproduce from the CLI."""

import hashlib
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from tools import attest_proof


ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / ".lake/build/bin/slean"
CASE = ROOT / "examples/formal-claim.json"


class AttestationTests(unittest.TestCase):
    def test_export_reference_matches_redirected_cli_output(self):
        exported = subprocess.check_output([str(BIN), "export", str(CASE), "agent"], cwd=ROOT)
        self.assertTrue(exported.endswith(b"\n"))
        expected = "sha256:" + hashlib.sha256(exported).hexdigest()

        original_command = attest_proof.command

        def without_rebuild(*args, **kwargs):
            if args == ("lake", "build"):
                return ""
            return original_command(*args, **kwargs)

        # The suite already built the CLI. Skip only the attester's rebuild;
        # this test checks the exported-byte reference, not build provenance.
        with mock.patch.object(attest_proof, "command", side_effect=without_rebuild), \
                mock.patch.object(attest_proof, "require_clean"):
            attestation = attest_proof.attest(CASE, "agent")

        self.assertEqual(attestation["projected_export_id"], expected)
        self.assertEqual(attestation["receipts"][0]["exact_export_ref"], expected)


if __name__ == "__main__":
    unittest.main()
