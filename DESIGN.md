---
name: Slean Documentation
description: A quiet research dossier for reading Slean's local checks and their limits.
colors:
  mineral-paper: "#f4f7f2"
  evergreen-ink: "#20302f"
  evergreen-heading: "#18342f"
  evergreen-secondary: "#2b4d42"
  rail-surface: "#e9eee9"
  rail-ink: "#263a36"
  selected-chapter: "#d4e5dd"
  hairline: "#b9c8bd"
  rust-link: "#8b3827"
  rust-hover: "#652b20"
  rust-focus: "#a44931"
  search-field: "white"
  code-surface: "#ecf0ea"
  code-border: "#c3d0c5"
  code-ink: "#1b2f2a"
  inline-code-surface: "#e8ece6"
typography:
  display:
    fontFamily: "Slean Display, Georgia, serif"
    fontSize: "clamp(3.25rem, 5vw, 5.4rem)"
    fontWeight: 600
    lineHeight: 1.06
    letterSpacing: "-0.035em"
  lede:
    fontFamily: "Slean Display, Georgia, serif"
    fontSize: "clamp(1.45rem, 2.5vw, 2.15rem)"
    lineHeight: 1.3
    letterSpacing: "-0.018em"
  section:
    fontFamily: "Slean Display, Georgia, serif"
    fontSize: "1.7rem"
    fontWeight: 600
    lineHeight: 1.5
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Slean Sans, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.58
  label:
    fontFamily: "Slean Sans, sans-serif"
    fontSize: "0.9rem"
    fontWeight: 600
  code:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "0.92rem"
    lineHeight: 1.55
rounded:
  focus: "2px"
  inline-code: "3px"
  code-block: "8px"
spacing:
  page-gutter: "clamp(1.25rem, 3vw, 3.5rem)"
  chapter-row-block: "0.9rem"
  code-block-block: "1rem"
  code-block-inline: "1.2rem"
components:
  search-field:
    backgroundColor: "{colors.search-field}"
    textColor: "{colors.evergreen-ink}"
    height: "auto"
  chapter-rail:
    backgroundColor: "{colors.rail-surface}"
    textColor: "{colors.rail-ink}"
  chapter-rail-current:
    backgroundColor: "{colors.selected-chapter}"
    textColor: "{colors.rail-ink}"
  chapter-index-row:
    textColor: "{colors.evergreen-ink}"
    padding: "0.9rem 0.2rem"
  next-chapter-link:
    textColor: "{colors.rust-link}"
    typography: "{typography.label}"
  code-block:
    backgroundColor: "{colors.code-surface}"
    textColor: "{colors.code-ink}"
    rounded: "{rounded.code-block}"
    padding: "1rem 1.2rem"
  inline-code:
    backgroundColor: "{colors.inline-code-surface}"
    rounded: "{rounded.inline-code}"
---

# Design System: Slean Documentation

## Overview

**Creative North Star: "The Research Dossier"**

This is the visual system for the local Slean Verso manual in **Mode Read**. It makes a research decision legible through a chaptered reading path, executable examples, and explicit scope. The atmosphere is quiet and exact: pale mineral paper, evergreen text, rust wayfinding, rules instead of cards, and type that separates a claim from its supporting detail.

The [Lean Language Reference](https://lean-lang.org/doc/reference/latest/) informs the persistent chapter hierarchy and search placement. [The Rust Programming Language book](https://doc.rust-lang.org/book/) informs the sequence from a working case through concepts and limits, with previous and next chapter navigation. Slean adapts those principles to its five-chapter dossier; it does not copy either site's assets or copy.

The documentation system does not prescribe the local Explorer. Its separate [Mode Operate rules](explorer/DESIGN.md) cover case-state inspection while keeping Slean's evidence boundaries and identity coherent.

**Key Characteristics:**

- A calm, pale reading surface with a fixed chapter rail at desktop widths.
- A serif hierarchy for the title and section heads; sans serif prose and controls; monospace commands and Lean declarations.
- Rust links and sequential navigation, with the synthetic example and the limits visible in the reading path.
- Flat surfaces, fine rules, immediate proof-case expansion, and reduced-motion support.

## Colors

The palette uses a mineral green family for reading and a restrained rust family for navigation and focus.

### Primary

- **Evergreen Ink** (`evergreen-ink`) carries paragraphs and code-adjacent labels. **Evergreen Heading** (`evergreen-heading`) holds the title, brand, and section heads.
- **Rust Link** (`rust-link`) marks reading links and chapter progression. **Rust Hover** (`rust-hover`) deepens a hovered link; **Rust Focus** (`rust-focus`) supplies the visible keyboard outline and native accent color.

### Neutral

- **Mineral Paper** (`mineral-paper`) is the page and header ground. **Rail Surface** (`rail-surface`) separates the chapter table from the reading pane.
- **Rail Ink** (`rail-ink`) keeps chapter labels quieter than the main title. **Evergreen Secondary** (`evergreen-secondary`) supports the opening lede.
- **Selected Chapter** (`selected-chapter`) marks the current rail row. **Hairline** (`hairline`) divides the header, rail, chapter index, and reading progression without elevation.
- **Search Field** (`search-field`) is a white control set inside the pale header. **Code Surface** (`code-surface`) and **Inline Code Surface** (`inline-code-surface`) set examples apart; **Code Border** (`code-border`) and **Code Ink** (`code-ink`) keep them legible.

**The Rust Wayfinding Rule.** Use rust for prose links, previous or next chapter progression, hovered index rows, and keyboard focus, not as a claim of validation or scientific status.

## Typography

**Display Font:** Self-hosted Literata, exposed as `Slean Display`, with Georgia and serif fallbacks.
**Body Font:** Self-hosted IBM Plex Sans, exposed as `Slean Sans`, with a sans serif fallback.
**Code Font:** The platform monospace stack used by Verso.

Literata gives the title and section heads an editorial voice. IBM Plex Sans makes technical prose and chapter labels compact and readable. The search field keeps Verso's standard system control type. Code keeps commands and Lean names visually distinct.

### Hierarchy

- **Display** (`display`): the opening manual title; its size is responsive and its line height stays tight.
- **Lede** (`lede`): one prominent sentence below the title, followed by ordinary prose.
- **Section** (`section`): chapter and section headings. Smaller subheads keep the same family and weight.
- **Body** (`body`): paragraphs and explanations; prose stays near a 69-character measure.
- **Label** (`label`): compact previous and next chapter controls; rail and index rows use the body scale with stronger weight.
- **Code** (`code`): commands, JSON output, and Lean declarations, with horizontal overflow contained inside each code panel.

**The Claim and Detail Rule.** Let the serif heading state the question or section; put qualifications, commands, and boundaries in readable sans serif prose and code.

## Layout

The desktop manual has a fixed header and a left chapter rail (18.5rem) beside a reading pane. The content maximum is 48rem, with a responsive horizontal gutter (`page-gutter`). Body paragraphs and list items are capped near 69ch; the first title page uses wider breathing room above the chapter index. Chapter rows are numbered and separated by hairlines. Previous and next links appear at chapter boundaries.

At 700px and below, the rail becomes a menu controlled from the header and the reading pane takes the width. The header gets shorter, the title scales to the narrow viewport, and a single progression link can occupy a full row. Code blocks scroll within their own bounds rather than widening the page.

**The Bounded Reading Rule.** Keep the document measure controlled on wide screens and preserve a continuous single-column path on mobile.

## Elevation & Depth

The manual is flat. It uses no resting shadows in the header or chapter rail. Background changes, fine borders, and whitespace distinguish the reading pane, rail, code, and search control. The current chapter uses a soft filled row. Do not add floating cards or lifted panels to ordinary prose.

**The Flat Page Rule.** Give documentation hierarchy through measure, tint, border, and whitespace rather than elevation.

## Shapes

Lines and rectangular planes lead the form language. The search control and chapter rows stay square. Code blocks have gently rounded corners (`code-block`); inline code uses the smaller `inline-code` radius. The keyboard outline has a slight `focus` radius and sits outside the focused target.

## Components

### Search Field

The header contains a compact white search control with a simple lower edge. It stays visible beside the title at desktop and mobile widths. Its hover and focused states use Verso's selected tint; keyboard focus remains visible.

### Chapter Rail

The desktop rail uses a pale green plane, numbered chapter entries, dark green labels, and a soft fill for the current row. On mobile, the same hierarchy moves into a dismissible menu. The menu control reports its open state and the closed rail is inert to keyboard navigation.

### Chapter Index and Progression

The title page repeats the five numbered chapters as full-width, hairline-separated evergreen links that turn rust on hover. Previous and next chapter links use rust and point along the reading sequence. Their text stays explicit; the arrow is supplementary.

### Code

Block examples use a pale green panel, a fine border, and inner padding. Long code scrolls horizontally inside the panel. Inline code gets only a quiet tint. Labeled Lean proof cases expand immediately, so inspection is not delayed by motion.

### Focus and Motion

Keyboard focus uses a 3px rust outline offset from links, menu labels, buttons, and native inputs. The search combobox retains Verso's focused tint and outline. Ordinary page movement is smooth, but the reduced-motion preference makes scrolling and transitions immediate. Reading controls must remain interruptible.

## Do's and Don'ts

### Do:

- **Do** keep the documentation in Mode Read: claim, example, provenance, format, and limits remain easy to find.
- **Do** use the numbered chapter rail, search, and previous or next links to support both lookup and linear reading.
- **Do** keep commands and Lean declarations in bounded, horizontally scrollable code panels.
- **Do** preserve visible focus and the reduced-motion behavior.

### Don't:

- **Don't** use color or decoration to imply that a synthetic example proves an empirical result.
- **Don't** turn body prose into cards or add ambient shadows to the reading layout.
- **Don't** copy a complete Lean Reference or Rust Book screen, its protected assets, or its prose.
- **Don't** apply these documentation layout rules to Explorer without a separate Mode Operate design pass.
