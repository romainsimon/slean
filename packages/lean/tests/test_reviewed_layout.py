"""Regression controls for Lean's namespace-root lookup during reconstruction."""

from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "verification"))
from reviewed import stage_namespace_overlays, check_namespace_overlays
from build_inputs import compiled_parts, module_path


class NamespaceLayoutTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source, self.build = self.root / "source", self.root / "build"
        self.source.mkdir()
        self.build.mkdir()
        self.modules = {"Domain.New": {"kind": "source"}}
        self.artifacts, self.sources = {}, {}
        for name in ("Domain.Existing", "Other.Existing"):
            relative = module_path(name)
            base = (self.root / "cache" / relative).with_suffix(".olean")
            base.parent.mkdir(parents=True, exist_ok=True)
            for suffix in (".olean", ".olean.private", ".ir"):
                base.with_suffix(suffix).write_bytes((name + suffix).encode())
            original = (self.root / "installed-source" / relative).with_suffix(".lean")
            original.parent.mkdir(parents=True, exist_ok=True)
            original.write_text("-- reviewed fixture source\n")
            self.artifacts[name], self.sources[name] = base, original
            self.modules[name] = {"kind": "dependency", "compiled": compiled_parts(base)}

    def stage(self):
        return stage_namespace_overlays(self.modules, list(self.modules), self.artifacts,
                                        self.sources, self.source, self.build)

    def test_shared_namespace_has_all_checked_parts_and_sources(self):
        links = self.stage()
        self.assertEqual(len(links), 4)
        check_namespace_overlays(links)
        for path, original in links:
            self.assertTrue(path.is_symlink())
            self.assertEqual(path.resolve(), original)
            self.assertEqual(path.read_bytes(), original.read_bytes())
        self.assertFalse((self.build / "Other").exists())
        self.assertFalse((self.source / "Other").exists())
        self.assertEqual(compiled_parts(self.artifacts["Domain.Existing"]),
                         self.modules["Domain.Existing"]["compiled"])

    def test_replaced_link_is_rejected_even_with_identical_bytes(self):
        links = self.stage()
        path, original = links[1]
        path.unlink()
        path.write_bytes(original.read_bytes())
        with self.assertRaisesRegex(ValueError, "namespace overlay changed"):
            check_namespace_overlays(links)

    def test_redirected_link_cannot_select_a_different_artifact(self):
        links = self.stage()
        path, original = links[1]
        different = self.root / "different-artifact"
        different.write_bytes(original.read_bytes())
        path.unlink()
        path.symlink_to(different)
        with self.assertRaisesRegex(ValueError, "namespace overlay changed"):
            check_namespace_overlays(links)

    def test_missing_installed_source_is_not_silently_accepted(self):
        self.sources["Domain.Existing"] = self.root / "absent.lean"
        with self.assertRaises(FileNotFoundError):
            self.stage()


if __name__ == "__main__":
    unittest.main()
