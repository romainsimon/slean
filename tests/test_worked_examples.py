"""The full Lean programs shown in both manuals match the checked source files."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = (
    "Synthetic.lean",
    "ExactThreshold.lean",
    "ValidateExport.lean",
    "FormalBoundary.lean",
)


class WorkedExampleTests(unittest.TestCase):
    def test_manual_sources_match_executable_files(self):
        for manual, label in (
            (ROOT / "site/SleanDocs.lean", "Complete source:"),
            (ROOT / "site/SleanDocsFr.lean", "Source complète :"),
        ):
            content = manual.read_text(encoding="utf-8")
            for filename in EXAMPLES:
                with self.subTest(manual=manual.name, filename=filename):
                    marker = f"*{label} `examples/{filename}`*\n\n```\n"
                    self.assertEqual(content.count(marker), 1)
                    start = content.index(marker) + len(marker)
                    end = content.index("\n```", start)
                    shown = content[start:end]
                    source = (ROOT / "examples" / filename).read_text(encoding="utf-8").rstrip("\n")
                    self.assertEqual(shown, source)


if __name__ == "__main__":
    unittest.main()
