"""Add the production-only Plausible loader to every generated manual page."""

from pathlib import Path


site = Path(__file__).parent / "_out" / "html-multi"
pages = sorted(site.rglob("*.html"))
if not pages:
    raise SystemExit("No generated HTML pages found")

marker = "data-slean-analytics"
script_url = "https://stats.yukicapital.com/js/script.js"
snippet = f'''<script {marker}>
  (() => {{
    if (window.location.hostname !== "slean.org" ||
        document.querySelector('script[data-domain="slean.org"]')) return;
    const script = document.createElement("script");
    script.defer = true;
    script.dataset.domain = "slean.org";
    script.src = "{script_url}";
    document.head.appendChild(script);
  }})();
</script>
'''

for page in pages:
    original = page.read_text(encoding="utf-8")
    if original.count(marker) == 1:
        continue
    if original.count(marker) > 1 or script_url in original:
        raise SystemExit(f"Existing or duplicate Plausible loader in {page}")
    if original.count("</head>") != 1:
        raise SystemExit(f"Expected one closing head tag in {page}")
    page.write_text(original.replace("</head>", snippet + "</head>"), encoding="utf-8")
