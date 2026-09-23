"""Release builds must name an exact, clean, annotated source tag."""

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("slean_build_identity", ROOT / "site" / "build_identity.py")
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


class BuildIdentityTests(unittest.TestCase):
    def test_tag_requires_exact_annotated_clean_source(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            git(repo, "init", "-q")
            (repo / "source.txt").write_text("first\n", encoding="utf-8")
            git(repo, "add", "source.txt")
            git(repo, "-c", "user.name=Slean Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "first")
            git(repo, "-c", "user.name=Slean Test", "-c", "user.email=test@example.invalid", "tag", "-am", "candidate", "v0.2.0")
            git(repo, "tag", "lightweight")

            self.assertEqual(identity.source_tag("v0.2.0", repo), "v0.2.0")
            self.assertIsNone(identity.source_tag(None, repo))
            with self.assertRaisesRegex(ValueError, "Git cat-file failed"):
                identity.source_tag("missing", repo)
            with self.assertRaisesRegex(ValueError, "not an annotated tag"):
                identity.source_tag("lightweight", repo)

            (repo / "source.txt").write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "clean source tree"):
                identity.source_tag("v0.2.0", repo)
            git(repo, "add", "source.txt")
            git(repo, "-c", "user.name=Slean Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "second")
            with self.assertRaisesRegex(ValueError, "does not point to HEAD"):
                identity.source_tag("v0.2.0", repo)

    def test_tag_is_visible_on_both_title_pages_and_recorded_on_every_page(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for locale, root in (("fr", output), ("en", output / "en")):
                root.mkdir(parents=True, exist_ok=True)
                (root / "index.html").write_text(
                    f"<html><head></head><body><main><div class=\"content-wrapper\">"
                    f"{identity.PREVIEW_TEXT[locale]}</div>\n        </main></body></html>",
                    encoding="utf-8",
                )
            chapter = output / "chapter" / "index.html"
            chapter.parent.mkdir()
            chapter.write_text(
                '<html><head></head><body><main><div class="content-wrapper">'
                'Chapter</div>\n        </main></body></html>', encoding="utf-8"
            )

            self.assertEqual(identity.stamp_pages(output, "v0.2.0", "0123456789abcdef"), 3)
            for page in output.rglob("*.html"):
                markup = page.read_text()
                self.assertIn('<meta name="slean-build-tag" content="v0.2.0">', markup)
                self.assertIn("commit 0123456789ab", markup)
                self.assertEqual(markup.count('class="slean-build-footer"'), 1)
            self.assertIn("Manuel construit depuis le tag v0.2.0", (output / "index.html").read_text())
            self.assertIn("Manual built from tag v0.2.0", (output / "en/index.html").read_text())


if __name__ == "__main__":
    unittest.main()
