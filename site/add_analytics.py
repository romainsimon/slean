"""Add the production-only Plausible loader to every generated manual page."""

from pathlib import Path


site = Path(__file__).parent / "_out" / "html-multi"
pages = sorted(site.rglob("*.html"))
if len(pages) != 16 or sum("en" in page.relative_to(site).parts for page in pages) != 8:
    raise SystemExit(f"Expected 8 French and 8 English HTML pages; found {len(pages)}")

marker = "data-slean-analytics"
script_url = "https://stats.yukicapital.com/js/pa-70RUKb_J9zQLn67oUHf2d.js"
snippet = f'''<script {marker}>
  (() => {{
    if (window.location.hostname !== "slean.org" ||
        document.querySelector('script[src="{script_url}"]') ||
        document.querySelector('script[data-domain="slean.org"]')) return;
    window.plausible = window.plausible || function() {{
      (window.plausible.q = window.plausible.q || []).push(arguments);
    }};
    window.plausible.init = window.plausible.init || function(options) {{
      window.plausible.o = options || {{}};
    }};
    window.plausible.init();
    const script = document.createElement("script");
    script.async = true;
    script.src = "{script_url}";
    document.head.appendChild(script);
  }})();
</script>
'''

for page in pages:
    original = page.read_text(encoding="utf-8")
    if original.count(marker) == 1:
        if original.count(script_url) != 2:
            raise SystemExit(f"Incomplete Plausible loader in {page}")
        continue
    if original.count(marker) > 1 or script_url in original:
        raise SystemExit(f"Existing or duplicate Plausible loader in {page}")
    if original.count("</head>") != 1:
        raise SystemExit(f"Expected one closing head tag in {page}")
    page.write_text(original.replace("</head>", snippet + "</head>"), encoding="utf-8")

for page in pages:
    markup = page.read_text(encoding="utf-8")
    if markup.count(marker) != 1 or markup.count(script_url) != 2:
        raise SystemExit(f"Expected exactly one site-specific Plausible loader in {page}")
    if "https://stats.yukicapital.com/js/script.js" in markup or "https://plausible.io/js/" in markup:
        raise SystemExit(f"Legacy Plausible loader remains in {page}")
