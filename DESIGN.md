---
name: Slean Documentation
description: A clear, chaptered reading surface for Slean's checks, evidence, and limits.
colors:
  page: "#ffffff"
  ink: "#17202a"
  muted: "#59636e"
  line: "#e6e9ed"
  soft: "#f7f8fa"
  focus: "#00895f"
  selection: "#dceee8"
typography:
  brand:
    fontFamily: '"Satoshi", "Slean Sans Fallback", ui-sans-serif, sans-serif'
    fontSize: "1.5rem"
    fontWeight: 700
    letterSpacing: "-0.025em"
  display:
    fontFamily: '"Satoshi", "Slean Sans Fallback", ui-sans-serif, sans-serif'
    fontSize: "clamp(2.125rem, 3vw, 2.5rem)"
    fontWeight: 700
    lineHeight: 1.16
    letterSpacing: "-0.03em"
  lede:
    fontFamily: '"Satoshi", "Slean Sans Fallback", ui-sans-serif, sans-serif'
    fontSize: "clamp(1.125rem, 1.5vw, 1.25rem)"
    fontWeight: 500
    lineHeight: 1.5
  chapter:
    fontFamily: '"Satoshi", "Slean Sans Fallback", ui-sans-serif, sans-serif'
    fontSize: "clamp(1.75rem, 2.5vw, 2rem)"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.025em"
  section:
    fontFamily: '"Satoshi", "Slean Sans Fallback", ui-sans-serif, sans-serif'
    fontSize: "1.375rem"
    fontWeight: 700
    lineHeight: 1.35
    letterSpacing: "-0.025em"
  body:
    fontFamily: '"Satoshi", "Slean Sans Fallback", ui-sans-serif, sans-serif'
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: '"Satoshi", "Slean Sans Fallback", ui-sans-serif, sans-serif'
    fontSize: "0.875rem"
    fontWeight: 500
  code:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "0.875rem"
    lineHeight: 1.55
rounded:
  search-field: "6px"
  code-block: "6px"
  inline-code: "3px"
  focus: "2px"
spacing:
  page-gutter: "clamp(1.25rem, 3vw, 2.5rem)"
  content-top: "clamp(2.5rem, 4vw, 3.5rem)"
  chapter-row-block: "0.85rem"
components:
  search-field:
    backgroundColor: "{colors.page}"
    textColor: "{colors.ink}"
    rounded: "{rounded.search-field}"
    height: "2.4rem"
    padding: "0.4rem 0.8rem"
  chapter-rail:
    backgroundColor: "{colors.page}"
    textColor: "{colors.ink}"
    width: "17.5rem"
  chapter-rail-current:
    backgroundColor: "{colors.soft}"
    textColor: "{colors.ink}"
  chapter-index-row:
    textColor: "{colors.ink}"
    padding: "0.85rem 0"
  next-chapter-link:
    textColor: "{colors.ink}"
    typography: "{typography.label}"
  code-block:
    backgroundColor: "{colors.soft}"
    textColor: "{colors.ink}"
    rounded: "{rounded.code-block}"
    padding: "1rem 1.2rem"
  inline-code:
    backgroundColor: "{colors.soft}"
    textColor: "{colors.ink}"
    rounded: "{rounded.inline-code}"
---

# Design System: Slean Documentation

## Overview

**Creative North Star: "The Research Dossier"**

The Slean Verso manual is a quiet white reading surface in **Mode Read**. It helps an experiment owner follow a frozen protocol, an observation, a cost, and a decision through a documented case. Clear type, narrow measure, and numbered chapters carry the hierarchy. The visual system does not suggest that a local check proves an external empirical claim.

Two Mutome references inform this system: `docs/DESIGN_SPEC.md` supplies the restrained white, ink, muted text, and fine-line roles; the `.lab-surface`, `.lab-header`, `.lab-main`, and `.reading` rules in `app/assets/css/main.css` demonstrate a calm one-column reading rhythm. Slean adapts those principles to its own Verso chapter rail, search, code examples, and proof boundaries. It does not reuse Mutome's content or assets.

The local [Explorer design](explorer/DESIGN.md) remains separate. These rules describe the documentation site, not an inspection tool's interaction model.

**Key Characteristics:**

- White page, header, and chapter rail with dark ink and fine neutral rules.
- Satoshi for headings, prose, navigation, and controls; IBM Plex Sans when Satoshi is unavailable.
- A fixed desktop chapter rail and a single reading column with a 45rem maximum.
- Text links, one soft selected-chapter fill, bounded code, visible green focus, and no decorative motion.

## Colors

### Primary

- **Ink** (`ink`) carries headings, prose, code text, and ordinary links. A link stays underlined or gains an underline on hover; color alone does not identify it.
- **Focus Green** (`focus`) identifies keyboard focus and link hover. It does not mean that a scientific claim has passed review.

### Neutral

- **Page White** (`page`) is the reading pane, header, rail, and search field.
- **Muted Gray** (`muted`) is for navigation captions, numbers, and secondary text.
- **Fine Line** (`line`) separates the header, rail, contents rows, and examples.
- **Soft Gray** (`soft`) marks the current chapter and supports code backgrounds.
- **Selection Tint** (`selection`) makes selected text visible while retaining ink text.

**The Evidence Color Rule.** Use color for navigation and focus, never as a substitute for a labeled check, provenance record, or review status.

## Typography

**Display and Body Font:** Satoshi from the [official Fontshare CSS API](https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&display=swap), then self-hosted IBM Plex Sans as `Slean Sans Fallback`, then the system sans stack. Both headings and prose are sans serif.

**Code Font:** The platform monospace stack used by Verso.

Satoshi files are not committed because its closed-source [ITF Free Font License](https://www.fontshare.com/licenses/itf-ffl) restricts redistribution. The site loads Satoshi through Fontshare's API. The checked-in IBM Plex Sans fallback keeps the manual legible if that request is unavailable.

### Hierarchy

- **Brand** (`brand`): compact, bold site name in the header.
- **Display** (`display`): title page heading, with a restrained responsive range.
- **Lede** (`lede`): one prominent sentence directly under the title.
- **Chapter** (`chapter`) and **Section** (`section`): bold sans headings with tight tracking; smaller subheads keep the same family.
- **Body** (`body`): continuous prose at 1rem and 1.6 line height; paragraphs and lists also have a 70ch cap.
- **Label** (`label`): rail entries and previous/next navigation.
- **Code** (`code`): commands, JSON, and Lean declarations in distinct monospace.

**The One Reading Voice Rule.** Keep titles, prose, search, and navigation in the same sans family; use monospace only for source material and commands.

## Layout

Verso supplies a fixed header and chapter rail. On desktop, the white rail is 17.5rem wide, separated by a fine rule. The reading pane has a 45rem maximum width and a responsive side gutter. The header is 4.5rem high; content begins with generous top space, then follows one vertical reading path. The numbered contents list and previous/next links support both lookup and sequential reading.

At 700px and below, the header becomes 4rem high and the rail moves behind the menu control. The reading pane takes the available width with a 1.25rem gutter. Code examples scroll horizontally inside their own bounds; long code does not widen the page. Keep the menu control and chapter links keyboard accessible.

**The Bounded Reading Rule.** Keep prose within the 45rem reading pane and preserve one continuous column on narrow screens.

## Elevation & Depth

The page, header, and rail are flat at rest. White space, fine borders, and one soft-gray selected row provide hierarchy. Only the search results list has a small shadow, so it reads as a temporary layer over the document. Ordinary prose and code do not become raised cards.

**The Flat Page Rule.** Use measure, spacing, border, and quiet fill before adding elevation.

## Shapes

The manual uses straight rules and restrained corners. Search and block-code containers have a 6px radius; inline code has a 3px radius. Keyboard focus has a 2px outline with a slight corner radius and sits outside its target. Chapter rows and the rail remain square.

## Components

### Search Field

The header search is a white, 6px rounded field with an ink label and a fine border. It stays visible beside the site name on desktop and mobile. Focus changes the border to green and gives keyboard users a separate visible outline. Results use a white list with a fine border, soft hover row, and the only small overlay shadow.

### Chapter Rail

The desktop rail stays fixed beside the text. Its caption and numbers are muted; chapter names are ink. The current chapter receives a soft fill and bold label. On mobile, the same navigation opens from the header menu.

### Chapter Index and Progression

The title page lists numbered chapters as full-width text rows divided by fine lines. Hover uses green while the title stays ink. Previous and next links remain explicit text at chapter boundaries; the arrow is supplementary.

### Code

Block examples use soft gray, a fine line, 6px corners, and inner padding. Overflow stays inside each block. Inline code uses only a quiet tint and 3px corners. Labeled Lean proof cases expand immediately on request.

### Focus and Motion

Keyboard focus is a 2px green outline, offset from the control. Ordinary anchor scrolling may be smooth; the reduced-motion preference makes it immediate and suppresses transitions. No decorative motion is added to the reading flow.

## Do's and Don'ts

### Do:

- **Do** keep the path from claim to protocol, observation, cost, and decision easy to scan.
- **Do** use ink for content, muted text for supporting labels, and green for navigation feedback.
- **Do** keep commands and Lean declarations in bounded, horizontally scrollable code examples.
- **Do** preserve readable mobile text, visible focus, and reduced-motion behavior.

### Don't:

- **Don't** imply that a synthetic example or conditional Lean theorem certifies a measurement, evaluator, or human decision.
- **Don't** add tinted page backgrounds, colored ordinary links, or serif headings.
- **Don't** add decorative cards, gradients, ambient shadows, or motion to fill the page.
- **Don't** apply the documentation layout rules to Explorer without a separate Mode Operate decision.
