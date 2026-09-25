"""Release builds must name an exact, clean, annotated source tag."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("slean_build_identity", ROOT / "site" / "build_identity.py")
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


class BuildIdentityTests(unittest.TestCase):
    def test_image_preflight_and_stamped_identity_work_without_git_metadata(self):
        source_sha = "0123456789abcdef0123456789abcdef01234567"
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "source"
            output = repo / "site" / "_out" / "html-multi"
            schema_dir = repo / "schema"
            output.mkdir(parents=True)
            schema_dir.mkdir()
            self.assertFalse((repo / ".git").exists())

            (schema_dir / "v0.3.0.schema.json").write_text(json.dumps({
                "$id": "urn:slean:schema:0.3.0",
                "properties": {
                    "schema_version": {"const": "0.3.0"},
                    "semantics_version": {"const": "0.3.0"},
                },
            }))
            (output / "index.html").write_text(identity.PREVIEW_TEXT["fr"])
            (output / "en").mkdir()
            (output / "en/index.html").write_text(identity.PREVIEW_TEXT["en"])

            self.assertEqual(identity.image_preflight(repo, source_sha), (source_sha, None))
            with self.assertRaisesRegex(ValueError, "full 40-character lowercase"):
                identity.image_preflight(repo, "not-a-full-sha")
            with self.assertRaisesRegex(ValueError, "required for an image build"):
                identity.image_preflight(repo, "")

            with (mock.patch.object(identity, "ROOT", repo),
                  mock.patch.object(identity, "OUTPUT", output),
                  mock.patch.dict(
                      "os.environ",
                      {"SOURCE_COMMIT": source_sha, "SLEAN_SITE_TAG": ""},
                      clear=False,
                  ),
                  mock.patch.object(sys, "argv", ["build_identity.py", "stamp"])):
                self.assertEqual(identity.main(), 0)

            info = json.loads((output / "build-info.json").read_text())
            self.assertEqual(info["source_revision"], source_sha)
            self.assertIsNone(info["source_tree_clean"])

    def test_image_preflight_checks_sha_and_cleanliness_when_git_is_available(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            git(repo, "init", "-q")
            (repo / "source.txt").write_text("source\n", encoding="utf-8")
            git(repo, "add", "source.txt")
            git(repo, "-c", "user.name=Slean Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "source")
            revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

            self.assertEqual(identity.image_preflight(repo, revision), (revision, True))
            with self.assertRaisesRegex(ValueError, "does not match Git HEAD"):
                identity.image_preflight(repo, "f" * 40)

            (repo / "source.txt").write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "clean Git checkout"):
                identity.image_preflight(repo, revision)

    def test_unreadable_git_metadata_is_not_treated_as_an_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / ".git").write_text("invalid gitdir pointer\n")
            with self.assertRaisesRegex(ValueError, "Git metadata is present but cannot be verified"):
                identity.image_preflight(repo, "a" * 40)

    def test_schema_identity_follows_checked_wire_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            schema_dir = root / "schema"
            schema_dir.mkdir()
            for version in ("0.2.0", "0.3.0"):
                schema = {
                    "$id": f"urn:slean:schema:{version}",
                    "properties": {
                        "schema_version": {"const": version},
                        "semantics_version": {"const": version},
                    },
                }
                (schema_dir / f"v{version}.schema.json").write_text(json.dumps(schema))
            self.assertEqual(identity.latest_schema_version(root), "0.3.0")

            output = root / "output"
            (output / "en").mkdir(parents=True)
            (output / "index.html").write_text(identity.PREVIEW_TEXT["fr"])
            (output / "en/index.html").write_text(identity.PREVIEW_TEXT["en"])
            identity.preview_pages(output, identity.latest_schema_version(root))
            self.assertIn("schéma 0.3.0", (output / "index.html").read_text())
            self.assertIn("schema 0.3.0", (output / "en/index.html").read_text())
            self.assertNotIn(identity.SCHEMA_MARKER, (output / "index.html").read_text())

            bad = json.loads((schema_dir / "v0.3.0.schema.json").read_text())
            bad["properties"]["semantics_version"]["const"] = "0.2.0"
            (schema_dir / "v0.3.0.schema.json").write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, "Version fields disagree"):
                identity.latest_schema_version(root)

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
                if "en" in page.relative_to(output).parts:
                    self.assertIn("Build tag: v0.2.0", markup)
                else:
                    self.assertIn("Tag du build : v0.2.0", markup)
            self.assertIn("Manuel construit depuis le tag v0.2.0", (output / "index.html").read_text())
            self.assertIn("Manual built from tag v0.2.0", (output / "en/index.html").read_text())


if __name__ == "__main__":
    unittest.main()
