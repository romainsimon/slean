#!/usr/bin/env python3
"""Keep URL text out of HTML sinks in the pinned Verso v4.28.0 output."""

from pathlib import Path


ROOT = Path(__file__).parent / "_out" / "html-multi"


def replace_once(source: str, old: str, new: str, path: Path) -> str:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"Expected one pinned Verso fragment in {path}; found {count}")
    return source.replace(old, new, 1)


def replace_section(source: str, start: str, end: str, new: str, path: Path) -> str:
    if source.count(start) != 1 or source.count(end) != 1:
        raise SystemExit(f"Pinned Verso search changed in {path}")
    before, rest = source.split(start, 1)
    _, after = rest.split(end, 1)
    return before + new + end + after


SAFE_HIGHLIGHT = """    // Build highlights as DOM nodes. Search terms and page text are plain text.
    function highlightTextNode(textNode) {
        const text = textNode.textContent || "";
        const matches = [];
        for (const token of tokenizeText(text)) {
            let matchedTerm = null;
            if (expandHlMatches) {
                let bestStem = "";
                for (const termStem of Object.keys(searchTerms)) {
                    if (termStem.length > bestStem.length && token.stem.startsWith(termStem)) {
                        bestStem = termStem;
                    }
                }
                if (bestStem) matchedTerm = searchTerms[bestStem];
            } else if (Object.prototype.hasOwnProperty.call(searchTerms, token.stem)) {
                matchedTerm = searchTerms[token.stem];
            }
            if (matchedTerm !== null) {
                matches.push({ start: token.start, end: token.end, term: matchedTerm });
            }
        }
        if (matches.length === 0 || !textNode.parentNode) return;
        matches.sort((a, b) => a.start - b.start || a.end - b.end);

        const fragment = document.createDocumentFragment();
        const highlights = [];
        let cursor = 0;
        for (const match of matches) {
            if (match.start < cursor || match.end > text.length) continue;
            fragment.appendChild(document.createTextNode(text.slice(cursor, match.start)));
            const span = document.createElement("span");
            span.className = "text-search-results";
            span.title = `Result for “${match.term}”`;
            span.textContent = text.slice(match.start, match.end);
            fragment.appendChild(span);
            highlights.push(span);
            cursor = match.end;
        }
        fragment.appendChild(document.createTextNode(text.slice(cursor)));
        textNode.parentNode.replaceChild(fragment, textNode);
        for (const highlight of highlights) {
            highlight.addEventListener("click", () => {
                const index = allHighlights.indexOf(highlight);
                if (index >= 0) {
                    currentHighlightIndex = index;
                    updateNavigationState();
                }
            });
        }
    }
"""


SAFE_CARET = """function setSearchCaret(element, offset) {
    const selection = window.getSelection();
    if (!selection) return;
    const range = document.createRange();
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    let remaining = Math.max(0, offset);
    let node;
    while ((node = walker.nextNode())) {
        const length = node.textContent?.length || 0;
        if (remaining <= length) {
            range.setStart(node, remaining);
            range.collapse(true);
            selection.removeAllRanges();
            selection.addRange(range);
            return;
        }
        remaining -= length;
    }
    range.selectNodeContents(element);
    range.collapse(offset === 0);
    selection.removeAllRanges();
    selection.addRange(range);
}

"""


def harden_find(path: Path) -> None:
    markup = path.read_text(encoding="utf-8")
    start = "\nif (paramName) {\n"
    if markup.count(start) != 1:
        raise SystemExit(f"Pinned Verso find handler changed in {path}")
    before, rest = markup.split(start, 1)
    old_handler, after = rest.split("</script>", 1)
    if old_handler.count("titleElem.innerHTML") != 3 or old_handler.count("messageElem.innerHTML") != 3:
        raise SystemExit(f"Pinned Verso find HTML sinks changed in {path}")
    safe_handler = (Path(__file__).parent / "safe_find.js").read_text(encoding="utf-8")
    markup = before + "\n" + safe_handler + "\n</script>" + after
    path.write_text(markup, encoding="utf-8")


def harden_highlight(path: Path) -> None:
    script = path.read_text(encoding="utf-8")
    script = replace_once(script, "const searchTerms = {};", "const searchTerms = Object.create(null);", path)
    script = replace_section(
        script,
        "    // Function to highlight text in a text node\n",
        "    /** Function to traverse DOM and find text nodes\n",
        SAFE_HIGHLIGHT + "\n",
        path,
    )
    if "tempDiv.innerHTML" in script:
        raise SystemExit(f"Unsafe highlight HTML remains in {path}")
    path.write_text(script, encoding="utf-8")


def harden_search_box(path: Path) -> None:
    script = path.read_text(encoding="utf-8")
    script = replace_once(
        script,
        'import { Range } from "./unicode-input.min.js";\n'
        'import { InputAbbreviationRewriter } from "./unicode-input-component.min.js";\n',
        SAFE_CARET,
        path,
    )
    script = replace_once(
        script,
        "    /** @type {InputAbbreviationRewriter} */\n    imeRewriter;\n\n",
        "",
        path,
    )
    script = replace_section(
        script,
        "        // Add IME\n",
        "        // Initialize with a full-text result's query, if one is being presented\n",
        "",
        path,
    )
    script = replace_once(
        script,
        "this.imeRewriter.setSelections([new Range(this.filter.length, 0)]);",
        "setSearchCaret(this.comboboxNode, this.filter.length);",
        path,
    )
    script = replace_once(
        script,
        "this.imeRewriter.setSelections([new Range(0, 0)]);",
        "setSearchCaret(this.comboboxNode, 0);",
        path,
    )
    script = replace_once(
        script,
        "this.imeRewriter.setSelections([new Range(length, 0)]);",
        "setSearchCaret(this.comboboxNode, length);",
        path,
    )
    script = replace_section(
        script,
        "        // Sort matches by position (descending) to avoid position shifts during replacement\n",
        "        return elem;\n",
        """        // Render snippets and matches as text nodes, never parsed HTML.
        relativeMatches.sort((a, b) => a.start - b.start || a.end - b.end);
        const prefix = snippet.start > 0 ? " …" : "";
        const suffix = snippet.end < text.length ? "… " : "";
        const elem = document.createElement("span");
        elem.appendChild(document.createTextNode(prefix));
        const content = document.createElement("span");
        let cursor = 0;
        for (const match of relativeMatches) {
            if (match.start < cursor || match.end > snippetText.length) continue;
            content.appendChild(document.createTextNode(snippetText.slice(cursor, match.start)));
            const emphasis = document.createElement("em");
            emphasis.textContent = snippetText.slice(match.start, match.end);
            content.appendChild(emphasis);
            cursor = match.end;
        }
        content.appendChild(document.createTextNode(snippetText.slice(cursor)));
        elem.appendChild(content);
        elem.appendChild(document.createTextNode(suffix));
""",
        path,
    )
    if "imeRewriter" in script or "m.innerHTML = snippetText" in script:
        raise SystemExit(f"Unsafe search HTML remains in {path}")
    path.write_text(script, encoding="utf-8")


def main() -> None:
    for locale in (ROOT, ROOT / "en"):
        harden_find(locale / "find" / "index.html")
        harden_highlight(locale / "-verso-search" / "search-highlight.js")
        harden_search_box(locale / "-verso-search" / "search-box.js")


if __name__ == "__main__":
    main()
