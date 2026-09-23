#!/usr/bin/env python3
"""Build two local study conditions from one checked, agent-projected timeline."""

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "explorer"))
from render import render as render_explorer  # noqa: E402


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"Expected one study insertion point: {old}")
    return source.replace(old, new)


def embedded_bundle(html: str) -> dict:
    matches = re.findall(
        r'<script id="slean-data" type="application/json">(.*?)</script>', html, re.DOTALL
    )
    if len(matches) != 1:
        raise ValueError("Expected one checked Explorer timeline bundle")
    return json.loads(matches[0])


def study_page(html: str, prefix: int, spatial: bool) -> str:
    mode = "3d" if spatial else "2d"
    html = replace_once(
        html,
        '<link rel="stylesheet" href="style.css">',
        '<link rel="stylesheet" href="style.css">\n'
        '  <link rel="stylesheet" href="study.css">'
        + ('\n  <link rel="stylesheet" href="three-d.css">' if spatial else ""),
    )
    html = replace_once(
        html,
        '<script defer src="app.js"></script>',
        '<script defer src="app.js"></script>\n'
        '  <script defer src="study.js"></script>'
        + ('\n  <script defer src="three-d.js"></script>' if spatial else ""),
    )
    html = replace_once(
        html,
        "<body>",
        f'<body data-study-prefix="{prefix}" data-study-mode="{mode}">\n'
        '  <p class="study-banner">Local comparison prototype · same checked dossier and '
        'selected prefix in both views · no study result recorded</p>',
    )
    return html


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    parser.add_argument("--prefix", type=int, help="same selected event count in both conditions")
    parser.add_argument("--output", type=Path, help="new empty local directory; defaults to /tmp")
    args = parser.parse_args()

    output = args.output.resolve() if args.output else Path(tempfile.mkdtemp(prefix="slean-3d-study-"))
    if output.exists() and any(output.iterdir()):
        parser.error(f"Refusing to overwrite a populated output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)

    try:
        baseline = output / "2d"
        baseline_page = render_explorer(args.case.resolve(), baseline, "agent")
        original_html = baseline_page.read_text(encoding="utf-8")
        bundle = embedded_bundle(original_html)
        if bundle["case"]["schema_version"] != "0.3.0":
            raise ValueError("The study candidate requires a checked 0.3.0 case")
        events = bundle["case"]["events"]
        prefix = len(events) if args.prefix is None else args.prefix
        if prefix < 0 or prefix > len(events):
            raise ValueError(f"Prefix must be between 0 and {len(events)}")
        if not bundle["snapshots"][prefix].get("dependency_gates"):
            raise ValueError("The chosen prefix contains no recorded dependency gate")

        spatial = output / "3d"
        shutil.copytree(baseline, spatial)
        for folder, mode in ((baseline, False), (spatial, True)):
            shutil.copyfile(HERE / "study.css", folder / "study.css")
            shutil.copyfile(HERE / "study.js", folder / "study.js")
            if mode:
                shutil.copyfile(HERE / "three-d.css", folder / "three-d.css")
                shutil.copyfile(HERE / "three-d.js", folder / "three-d.js")
            (folder / "index.html").write_text(study_page(original_html, prefix, mode), encoding="utf-8")

        if embedded_bundle((baseline / "index.html").read_text(encoding="utf-8")) != embedded_bundle(
            (spatial / "index.html").read_text(encoding="utf-8")
        ):
            raise ValueError("Study conditions do not share an identical checked timeline")
        (output / "study-manifest.json").write_text(
            json.dumps(
                {
                    "status": "prepared_not_run",
                    "case_id": bundle["case"]["case_id"],
                    "schema_version": bundle["case"]["schema_version"],
                    "audience": bundle["audience"],
                    "prefix": prefix,
                    "source_revision": bundle["build"]["base_revision"],
                    "identical_checked_bundle": True,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))

    print(f"2D baseline: {baseline / 'index.html'}")
    print(f"3D candidate: {spatial / 'index.html'}")
    print(f"Study manifest: {output / 'study-manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
