#!/usr/bin/env python3
"""Render a self-contained, local Explorer from Slean's checked timeline."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
MARKER = ".slean-explorer.json"


def checked_timeline(path: Path, audience: str) -> dict:
    command = ["lake", "exe", "slean", "timeline", str(path), audience]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        if audience == "agent":
            raise ValueError("Slean returned no agent timeline") from error
        raise ValueError(f"Slean returned no JSON result: {result.stderr.strip()}") from error
    if result.returncode:
        diagnostic = payload.get("error", {})
        code = diagnostic.get("code", "unknown")
        event = diagnostic.get("event_id", "")
        raise ValueError(f"Slean rejected the case: {code} {event}".strip())
    if payload.get("format") != "slean-explorer-timeline/0.1.0":
        raise ValueError("Unsupported Slean timeline format")
    return payload


def source_identity() -> dict:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", ".", ":(exclude)https:/"],
        cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    return {"base_revision": revision, "source_tree_clean": not bool(dirty)}


def prepare_output(path: Path, case_id: str, audience: str) -> None:
    if path.exists() and any(path.iterdir()):
        marker = path / MARKER
        if not marker.is_file():
            raise ValueError(f"Output directory is not a Slean Explorer artifact: {path}")
        previous = json.loads(marker.read_text(encoding="utf-8"))
        if previous.get("case_id") != case_id or previous.get("audience") != audience:
            raise ValueError("Output directory belongs to another case or audience")
    path.mkdir(parents=True, exist_ok=True)


def render(case_path: Path, output: Path, audience: str) -> Path:
    payload = checked_timeline(case_path, audience)
    identity = source_identity()
    case_id = payload["case"]["case_id"]
    prepare_output(output, case_id, audience)
    bundle = {**payload, "build": identity}
    encoded = json.dumps(bundle, ensure_ascii=True, separators=(",", ":"))
    encoded = encoded.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    template = (HERE / "index.html").read_text(encoding="utf-8")
    placeholder = "<!--SLEAN_EXPLORER_DATA-->"
    if template.count(placeholder) != 1:
        raise ValueError("Explorer template must have one data placeholder")
    html = template.replace(
        placeholder, f'<script id="slean-data" type="application/json">{encoded}</script>'
    )
    (output / "index.html").write_text(html, encoding="utf-8")
    shutil.copyfile(HERE / "style.css", output / "style.css")
    shutil.copyfile(HERE / "app.js", output / "app.js")
    fonts = output / "fonts"
    fonts.mkdir(exist_ok=True)
    for name in ("ibm-plex-sans-regular.ttf", "ibm-plex-sans-semibold.ttf", "OFL-ibm-plex-sans.txt"):
        shutil.copyfile(ROOT / "site" / "assets" / "fonts" / name, fonts / name)
    (output / MARKER).write_text(
        json.dumps({"generator": "slean-explorer", "case_id": case_id, "audience": audience}) + "\n",
        encoding="utf-8",
    )
    return output / "index.html"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path, help="Slean case JSON to validate")
    parser.add_argument("--audience", choices=("agent", "owner"), default="agent")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or HERE / "_out" / args.audience
    try:
        artifact = render(args.case.resolve(), output.resolve(), args.audience)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
