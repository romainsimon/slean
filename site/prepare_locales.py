"""Assemble the two Verso manuals and add static, chapter-preserving language links."""

from pathlib import Path
import shutil


site = Path(__file__).parent
root = site / "_out" / "html-multi"
english_render = site / "_out" / "en-render"
english = root / "en"

# Each pair follows the same chapter in both separately compiled manuals.
chapters = [
    ("commencer-par-un-cas-verifie", "Start-with-a-checked-case"),
    ("lire-la-decision", "Read-the-decision"),
    ("suivre-la-provenance", "Follow-provenance"),
    ("format-et-api", "Format-and-API"),
    ("limites-et-etat-du-developpement", "Limits-and-development-status"),
]


def replace_once(source: str, old: str, new: str, context: str) -> str:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"Expected one {context}; found {count}")
    return source.replace(old, new, 1)


if not (root / "index.html").is_file():
    raise SystemExit("French manual was not generated")
if not (english_render / "html-multi" / "index.html").is_file():
    raise SystemExit("English manual was not generated")
if english.exists():
    raise SystemExit("English output already exists; build from a clean generated directory")
shutil.move(str(english_render / "html-multi"), str(english))
english_render.rmdir()

routes = [("", ""), *chapters, ("find", "find")]
for french_slug, english_slug in routes:
    for locale, slug in (("fr", french_slug), ("en", english_slug)):
        page = (root if locale == "fr" else english) / slug / "index.html"
        if not page.is_file():
            raise SystemExit(f"Missing {locale} page: {page}")
        markup = page.read_text(encoding="utf-8")
        fr_href = f"../{french_slug}/" if locale == "en" else f"{french_slug}/"
        en_href = f"{english_slug}/" if locale == "en" else f"en/{english_slug}/"
        if not french_slug:
            fr_href = "../" if locale == "en" else ""
        if not english_slug:
            en_href = "" if locale == "en" else "en/"

        fr_current = ' aria-current="true"' if locale == "fr" else ""
        en_current = ' aria-current="true"' if locale == "en" else ""
        label = "Langue du document" if locale == "fr" else "Document language"
        switch = (
            f'<nav class="language-switch" aria-label="{label}">'
            f'<a href="{fr_href}" lang="fr" hreflang="fr"{fr_current}>FR</a>'
            '<span aria-hidden="true">/</span>'
            f'<a href="{en_href}" lang="en" hreflang="en"{en_current}>EN</a>'
            "</nav>"
        )
        markup = replace_once(markup, "<html>", f'<html lang="{locale}">', str(page))
        markup = replace_once(markup, "</header>", f"{switch}</header>", str(page))
        alternates = (
            f'<link rel="alternate" hreflang="fr" href="{fr_href}">'
            f'<link rel="alternate" hreflang="en" href="{en_href}">'
        )
        markup = replace_once(markup, '<meta charset="utf-8">', f'<meta charset="utf-8">{alternates}', str(page))
        if locale == "fr":
            if "Table of Contents</span>" not in markup:
                raise SystemExit(f"Missing table of contents label in {page}")
            markup = markup.replace("Table of Contents</span>", "Sommaire</span>")
            markup = markup.replace('title="Permalink"', 'title="Lien permanent"')
            if not slug:
                markup = replace_once(markup, "Contents</h2>", "Sommaire</h2>", str(page))
            if slug == "find":
                markup = markup.replace("Cross-Reference Redirection", "Redirection des références")
                for source, translation in [
                    ("Not found: name '", "Nom introuvable : '"),
                    ("Not found: '", "Introuvable : '"),
                    ("Searched domains:", "Domaines consultés :"),
                    ("Ambiguous: name '", "Nom ambigu : '"),
                    ("Ambiguous: '", "Ambigu : '"),
                    ("<p>Options:</p>", "<p>Possibilités :</p>"),
                    ("From ${xref", "Depuis ${xref"),
                    ("No name provided", "Aucun nom fourni"),
                    (
                        "This page expects a 'name' query parameter, along with documentation domains.",
                        "Cette page attend un paramètre « name » et des domaines de documentation.",
                    ),
                ]:
                    if source not in markup:
                        raise SystemExit(f"Missing French redirection label {source!r} in {page}")
                    markup = markup.replace(source, translation)
        page.write_text(markup, encoding="utf-8")


def translate_search(filename: str, replacements: list[tuple[str, str]]) -> None:
    path = root / "-verso-search" / filename
    content = path.read_text(encoding="utf-8")
    for english_text, french_text in replacements:
        content = replace_once(content, english_text, french_text, str(path))
    path.write_text(content, encoding="utf-8")


translate_search(
    "search-init.js",
    [
        ('"Search..."', '"Rechercher"'),
        ('"Jump to..."', '"Aller à..."'),
        ('aria-label="Search"', 'aria-label="Rechercher"'),
        ('aria-label="Results"', 'aria-label="Résultats"'),
    ],
)
translate_search(
    "search-box.js",
    [
        ('li.title = "Full-text search result";', 'li.title = "Résultat de recherche textuelle";'),
        ('"Full-text search"', '"Texte intégral"'),
        ('"No results"', '"Aucun résultat"'),
        ('Doc domain', 'Domaine documentaire'),
        (
            'Showing ${allResults.length}/${results.total + textResults.length} results',
            'Résultats : ${allResults.length}/${results.total + textResults.length}',
        ),
    ],
)
translate_search(
    "domain-mappers.js",
    [
        ('displayName: "Compiler Option"', 'displayName: "Option du compilateur"'),
        ('displayName: "Terminology"', 'displayName: "Terminologie"'),
        ('displayName: "Conv Tactic"', 'displayName: "Tactique conv"'),
        ('displayName: "Example Definition"', 'displayName: "Définition d’exemple"'),
        ('displayName: "Tactic"', 'displayName: "Tactique"'),
    ],
)
