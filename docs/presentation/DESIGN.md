# Slide deck design standard — Cultural Blend portfolio deck

Status: current living standard, 8 November 2026. Approved by Mike; each rule marked
"Mike's decision" came from his review of the live deck.

## Authority

This deck follows Mike's slide standard in
`~/Documents/GitHub/1. Study/aipa-text-to-sql-agent/docs/showcase/slides/DESIGN.md`
(reconciled with Project 15 on 6 November 2026). Its grid, content levels,
typography, chart rules, speaker-note pattern and verification rules apply in full.
This file records this project's overrides and the conventions settled during review.
Where the two disagree, this file wins for this deck; otherwise the parent standard
wins. Every number on a slide must appear in the [claims register](claims_register.md).

The 17-slide yellow/Georgia/Courier standard written on 8 November is superseded;
it is preserved in git history (commit `d9a234f`).

## Palette and type

| Role in parent standard | Parent value | This deck |
| --- | --- | --- |
| Primary evidence, titles | blue #0F4BEB | navy #1C2333 |
| Comparison and callout accent | amber #E6A23C | yellow #FFDD04, shapes only, never text |
| Section label, takeaway headings, second series | navy #17243B | violet #5B4B8A |
| Card fill | cream #FAF7F0 | paper #FBFAF6 |
| Body grey | #59636E | #59636E |
| Neutral comparison bars, note marks | slate #46576C | slate #46576C |
| Paired takeaway markers | red #C64040 | red #C64040 |

- **Violet (Mike's decision).** Violet #5B4B8A replaced teal #31688E in every role. It reaches about 7.4:1 on white and on paper; text on violet fills is white.
- **Yellow.** Yellow carries no text and is never the only cue: always pair it with a label. On yellow fills, text is navy.
- **Tints.** Light tints of the palette mark highlights and bands: yellow #FFF0A8, violet #E2DCF0 or #EEEBF5, slate #D5DCE5. Every text colour meets WCAG AA on its fill.
- **Typeface.** Google Sans throughout; no Georgia, Courier New or DM Sans on slides.

## Master, header and footer

- **Ground.** White ground on every slide, including the cover and close.
- **Header.** The section label sits at x43.5/y29.5, 10 pt bold uppercase: section in violet, a thin "|" separator in #999999, then the sublabel in #59636E. The parent's #999999 sublabel fails AA on white. A short yellow accent sits under the label. Mike removed the agenda's label in the live deck; `hide_label` in the storyline preserves that.
- **Footer (Mike's decision).** An edge-reaching navy line at y492 with a short yellow accent at its left. Left text, 8 pt: "**Cultural Blend**   Kiva funding speed, 1.45 million loans, 2016–2025". It uses spacing and weight rather than a vertical bar. One inherited page number sits at the right.
- **Sections.** Problem, Approach, Evidence, Next steps; the agenda uses these names.

## Evidence names (Mike's decision)

Slide faces name evidence by what it is, not when it ran, so the deck reads as one
body of work:
- **Explanatory models:** primary saved run, 31 August.
- **Robustness checks:** reviewed expanded-feature sensitivity.
- **Equivalence test:** 8 November, exploratory.
- **Forecast benchmark:** 2 November.

Evidence that comes from none of these is labelled descriptive. Each evidence slide's sublabel and subtitle use these names. Run dates and provenance go
only in speaker-note Reference blocks and the claims register.

## Takeaway column

- Position as in the parent: thin grey rule at x658 from y130 to y476; text area x684/y136, 235 pt wide; 12 pt, 110% line spacing, 6 pt after paragraphs and 14 pt before later headings; content ends by y476.
- **Headings are conclusion statements (Mike's decision),** never questions or topic labels: "Five framings are small", not "What we found". Keep them short enough for one line where possible. 12 pt bold violet.
- **Body** 12 pt body grey, with selective emphasis: only evidence-bearing phrases in bold navy. In `storyline.json` these phrases are wrapped in `**…**`.
- Use the space for one concrete implication, limit or next test when it adds value. Never repeat the figure.

## Markers

- Red #C64040 12 pt circles with centred 8 pt bold white numbers, at x668 beside each takeaway heading. A paired marker sits beside the evidence each point refers to; no unpaired numbers.
- **Construction.** An empty 12 pt ellipse, plus a separate text box centred on it that compensates for the native 7.2 pt insets. A number inside a 12 pt shape overflows its circle in the editor, because the CLI cannot remove the insets. `--fix-markers` rebuilds markers this way in place.
- **Alignment.** Each column marker is centred on its heading's first rendered line. Positions are measured from the Google-rendered PDF (`qa_portfolio_deck.py --write-markers`) after any heading change, never estimated.

## Figures, captions and notes (Mike's decision)

- Every chart, table, diagram or illustration that proves a point has a caption 8 pt below it, left-aligned to it, 8 pt grey, ending by y470. Figures are numbered through the deck (Figure 1, 2, …; appendix Figure A1, A2, …). Key-figure cards, process diagrams and synthesis slides need no caption.
- **Caption content.** One concise line about the content: what is shown, its unit and population or evidence layer. No method boilerplate such as "bars start at zero", and no data-handling detail; that belongs in notes.
- **Element-specific notes** use a small superscript mark (¹, ²) in slate on the exact label, value or bar they qualify. A matching line sits directly under the caption, starting with the same mark.
- **Slide-wide notes** keep a bold "Note:" or "Scope:" prefix on their own line under the caption.

## Charts and illustrations

- Arrows and connectors are thin slate lines (0.75 pt) with a small filled arrowhead, never block-arrow shapes, so every slide matches.
- Native shapes only. Bars start at zero, with direct labels. Value labels may sit inside bar tops in white when a reference line would otherwise cross them.
- Native lines cannot be flipped or rotated through the CLI, so rising lines draw backwards. Use bars, dots or level segments instead of sloped line charts.
- Illustrative examples, such as slide 4's listing, are labelled "Illustrative composite, not a real borrower". Every highlighted word must match the `src/features.py` lexicons.
- Icons: Material Symbols Rounded from the parent's icon set, tinted to violet, navy, slate or white (`portfolio_deck/assets/icons/`).
- Photos: `portfolio_deck/assets/photos/` with `PROVENANCE.md`. Credits go in speaker notes; Mike removed the on-slide credit line.

## Source of truth and editing

A native Google Slides deck, first built by `scripts/build_portfolio_deck_gslides.py`
from `docs/presentation/portfolio_deck/storyline.json`. The live deck is
authoritative and Mike edits it directly:
- Before any change, diff the live render against the last export.
- Mirror owner edits into the storyline and builder.
- Change only affected slides with `--only` or in-place batch edits; never run a full refill.

Previews, the Google-rendered PDF and the preview page (`deck-preview.html`, built by
`scripts/build_deck_preview.py`) live in `docs/presentation/portfolio_deck/output/`.
