# Slide deck design standard — Cultural Blend portfolio deck

Status: current living standard, 8 November 2026. Approved by Mike.

## Authority

This deck follows Mike's slide standard in
`~/Documents/GitHub/1. Study/aipa-text-to-sql-agent/docs/showcase/slides/DESIGN.md`
(reconciled with Project 15 on 6 November 2026). Its grid, content levels,
typography, takeaway column, markers, chart rules, speaker-note pattern and
verification rules apply in full. This file records only this project's
overrides. Where the two disagree, this file wins for this deck; otherwise the
parent standard wins. Every number on a slide must appear in the
[claims register](claims_register.md).

The 17-slide yellow/Georgia/Courier standard written on 8 November is superseded;
it is preserved in git history (commit `d9a234f`).

## Overrides

**Palette (Mike's decision, 8 November).** Team colours in the parent's roles:

| Role in parent standard | Parent value | This deck |
| --- | --- | --- |
| Primary evidence, titles | blue #0F4BEB | navy #1C2333 |
| Comparison and callout accent | amber #E6A23C | yellow #FFDD04, shapes only, never text |
| Section label and dark fills | navy #17243B | teal #31688E |
| Card fill | cream #FAF7F0 | paper #FBFAF6 |
| Body grey | #59636E | #59636E |
| Neutral comparison bars | slate #46576C | slate #46576C |
| Paired takeaway markers | red #C64040 | red #C64040 |

Yellow carries no text and is never the only cue: always pair it with a label.
On yellow fills, text is navy. Contrast for every text colour on its fill must
meet WCAG AA.

**Master.** No UTS master or logo. A short yellow accent under the section label,
an edge-reaching navy footer line, and one inherited page number. Cover and close
use a navy ground with white text and a yellow accent shape.

**Sections.** Problem, Approach, Evidence, Next steps; the agenda uses these names.

**Typeface.** Google Sans throughout, as in the parent. No Georgia, Courier New or
DM Sans on slides.

**Evidence labels.** Each evidence slide's subtitle names its layer: August primary
run, October extension, November benchmark, equivalence screen, or descriptive.

## Source of truth

A native Google Slides deck, built by `scripts/build_portfolio_deck_gslides.py`
from `docs/presentation/portfolio_deck/storyline.json`. After the first import,
the live deck is authoritative; preserve owner edits and do not rerun the builder
over it. Previews and the Google-rendered PDF live in
`docs/presentation/portfolio_deck/output/`.
