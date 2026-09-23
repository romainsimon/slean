"""Keep Verso's generated mobile viewport zoomable."""

from pathlib import Path
import re


site = Path(__file__).parent / "_out" / "html-multi"
pages = sorted(site.rglob("*.html"))
if not pages:
    raise SystemExit("No generated HTML pages found")

for page in pages:
    original = page.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'<meta name="viewport" content="[^"]*">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        original,
    )
    if count != 1:
        raise SystemExit(f"Expected one viewport tag in {page}, found {count}")
    page.write_text(updated, encoding="utf-8")
