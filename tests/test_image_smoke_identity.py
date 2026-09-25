"""Image packaging and site artifacts may come from distinct source revisions."""

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_SHA = "0123456789abcdef0123456789abcdef01234567"
TAG = "local-site-test"
SCRIPT_URL = "https://stats.yukicapital.com/js/pa-70RUKb_J9zQLn67oUHf2d.js"


def site_artifact(root: Path, source_sha: str, source_tree_clean: bool | None = True) -> None:
    (root / "build-info.json").write_text(json.dumps({
        "source_revision": source_sha,
        "source_tree_clean": source_tree_clean,
        "source_tag": TAG,
        "schema_version": "0.3.0",
        "lean_version": "4.28.0",
    }))
    markup = (
        '<html><head><meta name="slean-build-tag" content="' + TAG + '"></head>'
        '<body><footer class="slean-build-footer">Build tag: ' + TAG
        + ' · commit ' + source_sha[:12] + '</footer>'
        '<script data-slean-analytics src="' + SCRIPT_URL + '"></script>'
        '<link href="' + SCRIPT_URL + '"></body></html>'
    )
    for locale in (Path(), Path("en")):
        for index in range(9):
            page = root / locale / ("index.html" if index == 0 else f"chapter-{index}/index.html")
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text(markup)


def mock_commands(root: Path) -> Path:
    bin_dir = root / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text("""#!/usr/bin/env python3
import os
import shutil
import sys
from pathlib import Path

args = sys.argv[1:]
with open(os.environ["MOCK_DOCKER_LOG"], "a", encoding="utf-8") as log:
    log.write(" ".join(args) + "\\n")
if args[0] == "run":
    if os.environ.get("MOCK_RUN_FAILURE") == "1":
        print("mock name collision", file=sys.stderr)
        sys.exit(125)
    print("mock-container-id")
elif args[0] == "port":
    print("127.0.0.1:12345")
elif args[:2] == ["image", "inspect"]:
    print(os.environ["MOCK_LABEL_SHA"])
elif args[0] == "inspect":
    print("healthy")
elif args[0] == "cp":
    shutil.copytree(Path(os.environ["MOCK_SITE_ARTIFACT"]), Path(args[-1]), dirs_exist_ok=True)
""")
    docker.chmod(0o755)
    for name in ("curl", "npm"):
        command = bin_dir / name
        command.write_text("#!/bin/sh\nexit 0\n")
        command.chmod(0o755)
    return bin_dir


class ImageSmokeIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image_sha = os.environ.get("SOURCE_COMMIT")
        if cls.image_sha is None:
            cls.image_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip()
        assert re.fullmatch(r"[0-9a-f]{40}", cls.image_sha)
        assert cls.image_sha != ARTIFACT_SHA

    def helper(self, artifact: Path, image_sha: str, artifact_sha: str,
               schema: str = "0.3.0", tag: str = TAG) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", "tools/smoke_prebuilt_site_image.sh", "--check-only",
             str(artifact), image_sha, artifact_sha, schema, tag],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )

    def smoke(self, artifact: Path, bin_dir: Path, log: Path,
              image_sha: str, artifact_sha: str, *, label_sha: str,
              run_failure: bool = False, production_defaults: bool = False
              ) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env.update({
            "PATH": f"{bin_dir}:{env['PATH']}",
            "MOCK_DOCKER_LOG": str(log),
            "MOCK_SITE_ARTIFACT": str(artifact),
            "MOCK_LABEL_SHA": label_sha,
            "MOCK_RUN_FAILURE": "1" if run_failure else "0",
        })
        args = ["bash", "tools/smoke_site_image.sh", "mock-image", image_sha]
        if not production_defaults:
            args.extend((artifact_sha, "0.3.0", TAG))
        return subprocess.run(args, cwd=ROOT, env=env, capture_output=True,
                              text=True, check=False)

    def test_prebuilt_helper_accepts_distinct_shas_and_rejects_crossed_values(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory)
            site_artifact(artifact, ARTIFACT_SHA)
            self.assertEqual(self.helper(artifact, self.image_sha, ARTIFACT_SHA).returncode, 0)
            wrong_head = self.helper(artifact, ARTIFACT_SHA, self.image_sha)
            self.assertNotEqual(wrong_head.returncode, 0)
            self.assertIn("Image source SHA must match", wrong_head.stderr)
            for artifact_sha, schema, tag in (
                (self.image_sha, "0.3.0", TAG),
                (ARTIFACT_SHA, "0.2.0", TAG),
                (ARTIFACT_SHA, "0.3.0", "wrong-tag"),
            ):
                with self.subTest(artifact_sha=artifact_sha, schema=schema, tag=tag):
                    self.assertNotEqual(
                        self.helper(artifact, self.image_sha, artifact_sha, schema, tag).returncode,
                        0,
                    )

    def test_image_smoke_checks_image_and_artifact_revisions_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "artifact"
            artifact.mkdir()
            site_artifact(artifact, ARTIFACT_SHA)
            bin_dir = mock_commands(root)
            log = root / "docker.log"
            good = self.smoke(artifact, bin_dir, log, self.image_sha, ARTIFACT_SHA,
                              label_sha=self.image_sha)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertIn("exact image and artifact SHAs", good.stdout)
            self.assertIn("clean source checkout", good.stdout)
            self.assertIn("stop mock-container-id", log.read_text())
            self.assertIn("container rm mock-container-id", log.read_text())

            site_artifact(artifact, ARTIFACT_SHA, source_tree_clean=None)
            unknown_cleanliness = self.smoke(
                artifact, bin_dir, log, self.image_sha, ARTIFACT_SHA,
                label_sha=self.image_sha,
            )
            self.assertEqual(unknown_cleanliness.returncode, 0, unknown_cleanliness.stderr)
            self.assertIn("source cleanliness unavailable", unknown_cleanliness.stdout)

            site_artifact(artifact, ARTIFACT_SHA, source_tree_clean=False)
            dirty_source = self.smoke(artifact, bin_dir, log, self.image_sha, ARTIFACT_SHA,
                                      label_sha=self.image_sha)
            self.assertNotEqual(dirty_source.returncode, 0)
            self.assertIn("AssertionError", dirty_source.stderr)

            site_artifact(artifact, ARTIFACT_SHA)
            wrong_label = self.smoke(artifact, bin_dir, log, self.image_sha, ARTIFACT_SHA,
                                     label_sha=ARTIFACT_SHA)
            self.assertNotEqual(wrong_label.returncode, 0)
            self.assertIn("Image revision label mismatch", wrong_label.stderr)

            site_artifact(artifact, self.image_sha)
            crossed_artifact = self.smoke(artifact, bin_dir, log, self.image_sha,
                                          ARTIFACT_SHA, label_sha=self.image_sha)
            self.assertNotEqual(crossed_artifact.returncode, 0)
            self.assertIn("AssertionError", crossed_artifact.stderr)

            production = self.smoke(artifact, bin_dir, log, self.image_sha,
                                    self.image_sha, label_sha=self.image_sha,
                                    production_defaults=True)
            self.assertEqual(production.returncode, 0, production.stderr)

    def test_failed_container_start_never_stops_a_name_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "artifact"
            artifact.mkdir()
            site_artifact(artifact, ARTIFACT_SHA)
            bin_dir = mock_commands(root)
            log = root / "docker.log"
            result = self.smoke(artifact, bin_dir, log, self.image_sha, ARTIFACT_SHA,
                                label_sha=self.image_sha, run_failure=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("mock name collision", result.stderr)
            calls = log.read_text()
            self.assertIn("run -d", calls)
            self.assertNotIn("stop ", calls)
            self.assertNotIn("container rm", calls)


if __name__ == "__main__":
    unittest.main()
