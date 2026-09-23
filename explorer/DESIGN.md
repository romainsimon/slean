---
name: Slean Explorer
description: A local tool for reviewing a checked case at a chosen journal prefix.
colors:
  canvas: "#f4f7f2"
  surface: "#fff"
  side: "#e9eee9"
  select: "#d4e5dd"
  ink: "#20302f"
  deep: "#18342f"
  muted: "#52645d"
  line: "#c8d3ca"
  accent: "#8b3827"
  accent-dark: "#652b20"
  good: "#215c40"
  quiet: "#66756d"
typography:
  case-title:
    fontFamily: "Slean Sans, sans-serif"
    fontSize: "1.8rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.027em"
  section:
    fontFamily: "Slean Sans, sans-serif"
    fontSize: "1.04rem"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.012em"
  body:
    fontFamily: "Slean Sans, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.48
  compact:
    fontFamily: "Slean Sans, sans-serif"
    fontSize: "0.83rem"
    fontWeight: 400
  record:
    fontFamily: "Slean Sans, sans-serif"
    fontSize: "0.87rem"
    fontWeight: 400
  raw-event:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  tag: "4px"
  control: "5px"
  note: "6px"
  panel: "8px"
spacing:
  page-gutter: "clamp(1rem, 3.1vw, 3rem)"
  panel-gap: "1.2rem"
  detail-padding: "1.25rem 1.4rem"
  mobile-detail-padding: "1rem"
components:
  prefix-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "1rem 1.2rem"
  step-button:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.deep}"
    rounded: "{rounded.control}"
    padding: ".4rem .64rem"
  journal:
    backgroundColor: "{colors.side}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
  journal-current:
    backgroundColor: "{colors.select}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: ".6rem .5rem"
  detail-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "{spacing.detail-padding}"
  decision-status:
    textColor: "{colors.good}"
    rounded: "{rounded.tag}"
  record-link:
    textColor: "{colors.accent}"
  mobile-event-picker:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.deep}"
    rounded: "{rounded.control}"
    padding: ".46rem .5rem"
---

# Design System: Slean Explorer

## Overview

**Creative North Star: "The Journal at a Chosen Prefix"**

Explorer is a local **Mode Operate** surface for an experiment owner asking what the author had when a decision was recorded. The selected projected prefix controls the decision, evidence, and event details together. The interface makes chronological inspection the main task.

It adapts the manual's mineral paper, evergreen ink, rust wayfinding, thin rules, and IBM Plex Sans identity. The manual is **Mode Read**; Explorer uses denser sans serif data, bounded panels, and native controls so a user can compare recorded state across events. A visible scope note and audience label keep this review tool within Slean's validation boundary.

**Key Characteristics:**

- A prominent prefix selector above the journal and case state.
- A persistent desktop journal beside decision, evidence, and event details; a native event picker on mobile.
- Text labels, counts, and explicit source records carry meaning; color only reinforces state.
- Flat surfaces, visible focus, immediate state changes, and no ornamental motion.

## Colors

The inherited canvas, evergreen text, pale side surface, selected tint, and rust action color keep Explorer recognizably Slean. White panels and a slightly cooler line separate dense case facts. Muted text carries explanations and metadata; the quiet token softens future journal entries without disabling them.

**The Scoped Status Rule.** The green decision chip means a decision is recorded at the selected prefix. It does not mean the assessment is empirically true. Rust marks navigation and record links, not proof.

## Typography

Explorer uses the self-hosted IBM Plex Sans family exposed as Slean Sans for the case title, controls, labels, and records. It uses the platform monospace stack only for the exact JSON event record. The manual's Literata display treatment stays with long-form reading; the tool uses a compact sans serif hierarchy.

The case title leads, section headings identify the three inspection areas, compact text explains scope and position, and tabular numbers keep event counts aligned. Long identifiers and digests wrap inside their panels.

## Layout

The workspace is capped at 1600px with a responsive page gutter. The prefix selector spans the width. At desktop widths, a sticky journal up to 20rem wide sits beside the detail column. Evidence groups use two columns. From 900px through 681px, the journal narrows and evidence groups use one column.

At 680px and below, the layout stacks: scope note, prefix selector, journal picker, then state, evidence, and selected event. The desktop journal list is hidden and the native select includes the before-first-event position. Evidence groups return to two columns from 680px through 411px, then become one column at 410px and below. State and event facts retain compact two-column rows where space allows.

**The One Prefix Rule.** Slider, Previous, Next, journal buttons, record links, and the mobile picker all select the same prefix. State, evidence, selected event, count, and current marker update from that position.

## Elevation & Depth

The tool is flat. White panels, the pale journal, thin borders, rules, and spacing separate tasks; there are no resting shadows. The synthetic-fixture tag and decision chip are small status markers within this structure.

## Shapes

Panels have gently rounded 8px corners. Controls and selected journal rows use 5px corners; tags use 4px. The scope note uses 6px. Borders remain thin and rectangular, preserving the manual's restrained character while making tool regions easier to scan.

## Components

### Prefix selector

The current count names the state after N events. The range input uses the rust native accent. Previous is disabled at prefix zero; Next is disabled at the last event. A zero prefix shows the empty start, not a selected event. Buttons use a short background and border transition; reduced motion removes that transition.

### Journal and mobile picker

Desktop journal buttons show order, kind, and event ID. The selected event has a pale fill and current-step semantics; later entries have quieter text but remain selectable. On mobile, a labeled native select replaces the list and stays synchronized with the slider and buttons.

### State, evidence, and event panels

State distinguishes a pending decision from a recorded decision. It shows the recorded result, reason, cited assessment, stated rule, and frozen threshold when available. Evidence groups list only records introduced by the chosen prefix, with explicit empty states. Record links jump to the event that introduced a record. The selected event shows its metadata and a native disclosure for exact JSON; the disclosure closes when the prefix changes.

### Header, scope, and interaction states

The header names the active audience projection; the case heading marks a synthetic fixture when applicable. The scope note states that Slean checks journal structure and stated rules while empirical truth remains unverified. Focusable controls use a 3px rust outline offset 3px. Disabled step buttons remain legible at reduced opacity. The skip link becomes visible on focus. Ordinary scrolling may be smooth, but reduced motion makes it immediate.

## Do's and Don'ts

### Do:

- **Do** keep prefix selection and every visible case section synchronized.
- **Do** keep recorded decisions, local assessment verdicts, and empirical truth distinct in copy and status.
- **Do** expose audience and synthetic-fixture context; owner data belongs in a separate private generated artifact.
- **Do** preserve native slider, select, disclosure, keyboard focus, and reduced-motion behavior.

### Don't:

- **Don't** turn a local pass, recorded relation, or conditional formal receipt into a scientific proof claim.
- **Don't** replace the mobile picker with a cramped copy of the desktop journal.
- **Don't** add decorative motion or shadows to routine historical review.
