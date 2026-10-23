# Presentation record

The deck briefs, rehearsal scripts, Q&A documents, HTML mirrors, and draft
PPTX in this directory record the September 2026 preparation process. They
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
