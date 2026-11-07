# Presentation record

**Current deck (8 November 2026):** the Cultural Blend portfolio deck in
[`portfolio_deck/`](portfolio_deck/README.md), a native Google Slides deck built
from [`portfolio_deck/storyline.json`](portfolio_deck/storyline.json) under the
[design standard](DESIGN.md). Every number it quotes is listed in the
[claims register](claims_register.md). It merges the August, October and November
evidence and the 8 November equivalence screen.

**Historical, do not reuse without the correction notice:**
- The submitted competition deck and its v3 exports in `output/Team-Cultural-Blend-*`.
- The 16-slide `output/cultural-blend-beyond-a-good-story-refined.*` and the 17-slide
  live Google deck (`17rHwKFX…`) with [`SLIDE_CONTENT_BRIEF.md`](SLIDE_CONTENT_BRIEF.md),
  built on 7–8 November by `scripts/build_presentation_deck.py`, `build_slides_v3.py`
  and `build_slide_03_*.py`. These reuse retired claims.
- The two November research-refresh decks below, which the portfolio deck supersedes
  for presentation but which remain accurate for their own scope.

The current [November research refresh](research_refresh/README.md) contains a
new editable deck, slide-by-slide briefing and sources. Its latest version
includes the separate full-data matched text benchmark. Read the
[research review](../4_research_review.md) and
[ML refinement plan](../5_ml_refinement_plan.md) for the original diagnosis,
and the [new findings](../6_matched_text_results.md) for execution and
interpretation. The earlier research-design deck remains preserved alongside
the update. Neither artifact replaces the submitted presentation.

The deck briefs, rehearsal scripts, Q&A documents, HTML mirrors, and draft
PPTX at this directory's top level record the September 2026 preparation process. They
include superseded interpretations and are retained as historical material.
The submitted deck was a separate team export; the local `slides_draft.pptx`
is not evidence of the exact submitted version.

For current reuse, read [evidence and corrections](../2_evidence_and_corrections.md)
and the [portfolio case study](../3_portfolio_case_study.md). In particular,
phrases such as “robust null”, “won't move the needle”, and the third-person
“sign reversal” must not be reused as current conclusions. Programme text is
an unvalidated proxy, not a field-partner identifier.

`charts/portfolio_uncertainty.png` is a new maintenance exhibit, generated
by `python3 scripts/build_portfolio_chart.py` directly from the saved primary
JSON report. It illustrates normal-reference versus heuristic few-cluster
intervals for two regional contrasts, without treating the heuristic as
calibrated inference. It is not part of the submitted deck.

Regenerating historical PDFs requires Pandoc, Typst, and the external lecture
notes template. `scripts/render_review_pdfs.py --template PATH --output-dir DIR`
accepts explicit locations and defaults to `docs/pdf/generated/` for outputs.
Importing the script is inert. Existing archived PDF copies are not overwritten
by the default command.
