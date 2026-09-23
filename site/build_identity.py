#!/usr/bin/env python3
"""Validate an optional source tag and stamp the generated manual artifact."""

import argparse
import html
import json
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "site" / "_out" / "html-multi"
SCHEMA_MARKER = "SLEANSCHEMAVERSIONTOKEN"
LEAN_VERSION = "4.28.0"
PREVIEW_TEXT = {
    "fr": f"Version de développement · schéma {SCHEMA_MARKER} · Lean 4.28.0. Aucun tag n'est sélectionné pour ce build.",
    "en": f"Development preview · schema {SCHEMA_MARKER} · Lean 4.28.0. No tag is selected for this build.",
}


def latest_schema_version(root: Path = ROOT) -> str:
    """Read the newest checked wire contract, rather than stamping a fixed label."""
    versions = []
    for path in (root / "schema").glob("v*.schema.json"):
        match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)\.schema\.json", path.name)
        if not match:
            continue
        version = ".".join(match.groups())
        schema = json.loads(path.read_text(encoding="utf-8"))
        properties = schema.get("properties", {})
        if (schema.get("$id") != f"urn:slean:schema:{version}"
                or properties.get("schema_version", {}).get("const") != version
                or properties.get("semantics_version", {}).get("const") != version):
            raise ValueError(f"Version fields disagree in {path}")
        versions.append((tuple(map(int, match.groups())), version))
    if not versions:
        raise ValueError("No versioned Slean schema found")
    return max(versions)[1]


def preview_pages(output: Path, schema_version: str) -> None:
    for locale, relative_path in (("fr", "index.html"), ("en", "en/index.html")):
        page = output / relative_path
        markup = page.read_text(encoding="utf-8")
        preview = PREVIEW_TEXT[locale]
        if markup.count(preview) != 1:
            raise ValueError(f"Expected one development-status sentence in {page}")
        page.write_text(markup.replace(preview, preview.replace(SCHEMA_MARKER, schema_version), 1), encoding="utf-8")


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


def stamp_pages(output: Path, tag: str, revision: str, schema_version: str | None = None) -> int:
    schema_version = schema_version or latest_schema_version()
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
        page_locale = "en" if "en" in page.relative_to(output).parts else "fr"
        for root_locale, title_page in roots.items():
            if page != title_page:
                continue
            preview = PREVIEW_TEXT[root_locale]
            if markup.count(preview) != 1:
                raise ValueError(f"Expected one development-status sentence in {page}")
            replacement = (
                f"Manuel construit depuis le tag {safe_tag} · schéma {schema_version} · Lean {LEAN_VERSION}."
                if root_locale == "fr" else
                f"Manual built from tag {safe_tag} · schema {schema_version} · Lean {LEAN_VERSION}."
            )
            markup = markup.replace(preview, replacement, 1)
        updated[page] = markup.replace(
            "</head>", f'<meta name="slean-build-tag" content="{safe_tag}"></head>', 1
        )
        footer_label = "Identité du build" if page_locale == "fr" else "Build identity"
        footer_text = (
            f"Tag du build : {safe_tag} · commit {short_revision}"
            if page_locale == "fr" else f"Build tag: {safe_tag} · commit {short_revision}"
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
        schema_version = latest_schema_version()
        if tag:
            stamp_pages(OUTPUT, tag, revision, schema_version)
        else:
            preview_pages(OUTPUT, schema_version)
        OUTPUT.mkdir(parents=True, exist_ok=True)
        (OUTPUT / "build-info.json").write_text(
            json.dumps(
                {
                    "source_revision": revision,
                    "source_tree_clean": clean,
                    "source_tag": tag,
                    "schema_version": schema_version,
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
