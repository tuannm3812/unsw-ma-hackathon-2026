# Portfolio deck (November 2026)

Current Cultural Blend deck for portfolio readers, detailed and solution-led since 2026-11-08: 19 core
slides and 5 appendix slides. The problem → What drives the wait → Our solution (Predict → Prioritise →
Test) → Safe next steps.

- Content and speaker notes: [`storyline.json`](storyline.json)
- Design: [`../DESIGN.md`](../DESIGN.md), which defers to Mike's text-to-SQL slide standard
- Numbers: [`../claims_register.md`](../claims_register.md); no slide may quote anything else
- **Live deck:** [`1Q7n_sOn_4HL68_Mk-GogDOtS9P_pfPVXLNUeinV7pFM`](https://docs.google.com/presentation/d/1Q7n_sOn_4HL68_Mk-GogDOtS9P_pfPVXLNUeinV7pFM/edit),
  created 2026-11-08. It is authoritative; preserve owner edits and do not rerun the builder over it.
- **Backup before the solution-led restructure:** [`1w0g9cZsPe7PBNzv2ZB47NjGEd08fgp4S5IVTIdtGeo0`](https://docs.google.com/presentation/d/1w0g9cZsPe7PBNzv2ZB47NjGEd08fgp4S5IVTIdtGeo0/edit),
  "Cultural Blend deck, pre-restructure backup 2026-11-08" (19 slides, evidence-led order). Do not edit it.
- Builder: `scripts/build_portfolio_deck_gslides.py --base BASE_ID` copies a blank base into a
  new deck. Base: `1Gu1vP6zpvrWWqp6V2STTbVzj_HtFyNxD-nCfyAzqxZA` (keep blank)
- Base: `scripts/build_portfolio_deck_base.py` writes a 960 x 540 pt .pptx, because
  `gslides mutate create` only makes 720 x 405 pt pages. It is uploaded to Drive with conversion.
- Checks: `scripts/qa_portfolio_deck.py DECK_ID` exports the PDF and previews, then checks the
  frame, fonts and register numbers. `--write-markers` updates `marker_layout.json`
- Outputs: `output/` (Google-rendered PDF and slide previews)

Known limits of the CLI build, all editable by hand in Slides:

- Table header fills are rectangles behind the table, because the CLI cannot fill cells.
- The live base's page-number placeholder keeps a 236 pt box, right-aligned to x919, running off
  the bottom edge; the CLI cannot resize it in place. `build_portfolio_deck_base.py` now writes
  the intended 60 pt box, but that version was not uploaded.
- There are no native bullets, and agenda page chips stay underlined as links.
- Icons from the parent standard's set are not used.

The 17-slide live Google deck from 8 November and earlier decks are historical; see
[`../README.md`](../README.md).
