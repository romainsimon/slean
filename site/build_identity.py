#!/usr/bin/env python3
"""Validate an optional source tag and stamp the generated manual artifact."""

import argparse
import html
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "site" / "_out" / "html-multi"
SCHEMA_VERSION = "0.2.0"
LEAN_VERSION = "4.28.0"
PREVIEW_TEXT = {
    "fr": "Version de développement · schéma 0.2.0 · Lean 4.28.0. Aucun tag n'est sélectionné pour ce build.",
    "en": "Development preview · schema 0.2.0 · Lean 4.28.0. No tag is selected for this build.",
}


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise ValueError(f"Git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def source_tag(tag: str | None, repo: Path = ROOT) -> str | None:
    """Accept only a clean checkout whose HEAD is an annotated exact tag."""
    if not tag:
        return None
    git(repo, "check-ref-format", f"refs/tags/{tag}")
    if git(repo, "cat-file", "-t", f"refs/tags/{tag}") != "tag":
        raise ValueError(f"{tag} is not an annotated tag")
    revision = git(repo, "rev-parse", "HEAD")
    if git(repo, "rev-parse", f"refs/tags/{tag}^{{commit}}") != revision:
        raise ValueError(f"{tag} does not point to HEAD")
    if git(repo, "status", "--porcelain"):
        raise ValueError("A tagged build requires a clean source tree")
    return tag


def stamp_pages(output: Path, tag: str, revision: str) -> int:
    pages = sorted(output.rglob("*.html"))
    if not pages:
        raise ValueError("No generated manual pages found")
    roots = {locale: output / ("en/index.html" if locale == "en" else "index.html") for locale in PREVIEW_TEXT}
    if any(not page.is_file() for page in roots.values()):
        raise ValueError("Both French and English title pages are required")

    safe_tag = html.escape(tag, quote=True)
    short_revision = html.escape(revision[:12], quote=True)
    footer_marker = "</div>\n        </main>"
    updated = {}
    for page in pages:
        markup = page.read_text(encoding="utf-8")
        if markup.count("</head>") != 1 or 'name="slean-build-tag"' in markup:
            raise ValueError(f"Expected one unstamped head in {page}")
        if markup.count(footer_marker) != 1:
            raise ValueError(f"Expected one manual content footer position in {page}")
        locale = "en" if "en" in page.relative_to(output).parts else "fr"
        for locale, title_page in roots.items():
            if page != title_page:
                continue
            preview = PREVIEW_TEXT[locale]
            if markup.count(preview) != 1:
                raise ValueError(f"Expected one development-status sentence in {page}")
            replacement = (
                f"Manuel construit depuis le tag {safe_tag} · schéma {SCHEMA_VERSION} · Lean {LEAN_VERSION}."
                if locale == "fr" else
                f"Manual built from tag {safe_tag} · schema {SCHEMA_VERSION} · Lean {LEAN_VERSION}."
            )
            markup = markup.replace(preview, replacement, 1)
        updated[page] = markup.replace(
            "</head>", f'<meta name="slean-build-tag" content="{safe_tag}"></head>', 1
        )
        footer_label = "Identité du build" if locale == "fr" else "Build identity"
        footer_text = (
            f"Tag du build : {safe_tag} · commit {short_revision}"
            if locale == "fr" else f"Build tag: {safe_tag} · commit {short_revision}"
        )
        updated[page] = updated[page].replace(
            footer_marker,
            f'<footer class="slean-build-footer" aria-label="{footer_label}">{footer_text}</footer>\n'
            "          </div>\n        </main>",
            1,
        )
    for page, markup in updated.items():
        page.write_text(markup, encoding="utf-8")
    return len(pages)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("preflight", "stamp"))
    args = parser.parse_args()
    try:
        tag = source_tag(os.environ.get("SLEAN_SITE_TAG"))
        if args.action == "preflight":
            return 0
        revision = git(ROOT, "rev-parse", "HEAD")
        clean = not git(ROOT, "status", "--porcelain", "--", ".", ":(exclude)https:/")
        if tag:
            stamp_pages(OUTPUT, tag, revision)
        OUTPUT.mkdir(parents=True, exist_ok=True)
        (OUTPUT / "build-info.json").write_text(
            json.dumps(
                {
                    "source_revision": revision,
                    "source_tree_clean": clean,
                    "source_tag": tag,
                    "schema_version": SCHEMA_VERSION,
                    "lean_version": LEAN_VERSION,
                },
                separators=(",", ":"),
            ) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError) as error:
        parser.exit(1, f"Build identity: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
