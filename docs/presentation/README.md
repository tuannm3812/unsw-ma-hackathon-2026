# Presentation record

The official living presentation standard and current refined slide deck:
- [Slide Deck Design Standard](DESIGN.md): The institutional 960 × 540 pt design standard, adapted from `aipa-text-to-sql-agent` and Project 15 (Blue `#0F4BEB` & Amber `#E6A23C` palette, exact spatial rails, takeaway column with red paired markers, content hierarchy, and speaker notes pattern).
- [Refined PowerPoint Presentation (16 slides)](output/cultural-blend-beyond-a-good-story-refined.pptx) and [PDF Mirror](output/cultural-blend-beyond-a-good-story-refined.pdf): Complete 12 core slides + 4 technical appendix slides generated natively via `python-pptx` with rich evidence cards, paired takeaway badges, and structured speaker notes. Built by [`scripts/build_presentation_deck.py`](../../scripts/build_presentation_deck.py).

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
