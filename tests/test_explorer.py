"""Artifact and audience boundaries for the local Explorer renderer."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RENDER = ROOT / "explorer" / "render.py"
EXAMPLES = ROOT / "examples"


def render(case: Path, output: Path, *options: str):
    return subprocess.run(
        [sys.executable, str(RENDER), str(case), "--output", str(output), *options],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )


class ExplorerTests(unittest.TestCase):
    def test_agent_artifact_contains_checked_projection_and_owner_requires_opt_in(self):
        with tempfile.TemporaryDirectory() as directory:
            agent_output = Path(directory) / "agent"
            agent = render(EXAMPLES / "valid.json", agent_output)
            self.assertEqual(agent.returncode, 0, agent.stderr)
            html = (agent_output / "index.html").read_text(encoding="utf-8")
            self.assertIn('"format":"slean-explorer-timeline/0.1.0"', html)
            self.assertIn('"prefix":8', html)
            self.assertNotIn("private-observation-1", html)
            self.assertNotIn("private-artifact-1", html)
            self.assertIn('"audience":"agent"', html)
            marker = json.loads((agent_output / ".slean-explorer.json").read_text())
            self.assertEqual(marker["audience"], "agent")
            self.assertTrue((agent_output / "fonts" / "OFL-ibm-plex-sans.txt").is_file())

            owner_output = Path(directory) / "owner"
            owner = render(EXAMPLES / "valid.json", owner_output, "--audience", "owner")
            self.assertEqual(owner.returncode, 0, owner.stderr)
            self.assertIn("private-observation-1", (owner_output / "index.html").read_text())
            self.assertNotEqual(agent_output, owner_output)
            rejected = render(EXAMPLES / "valid.json", agent_output, "--audience", "owner")
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("another case or audience", rejected.stderr)

    def test_invalid_case_does_not_create_artifact_and_case_text_cannot_close_script(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "invalid"
            rejected = render(EXAMPLES / "unit-mismatch.json", output)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("metric_unit", rejected.stderr)
            self.assertFalse(output.exists())

            case = json.loads((EXAMPLES / "valid.json").read_text())
            case["question"]["text"] = '</script><script>alert("x")</script>'
            input_path = Path(directory) / "case.json"
            input_path.write_text(json.dumps(case), encoding="utf-8")
            safe_output = Path(directory) / "safe"
            safe = render(input_path, safe_output)
            self.assertEqual(safe.returncode, 0, safe.stderr)
            html = (safe_output / "index.html").read_text(encoding="utf-8")
            self.assertNotIn('</script><script>alert', html)
            self.assertIn('\\u003c/script\\u003e', html)


if __name__ == "__main__":
    unittest.main()
