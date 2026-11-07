# November research refresh

Prepared 2026-11-02 for portfolio and industry readers, using a Kiva/partner
decision case. Presenters: Mike Nguyen and Sophia Nguyen, Cultural Blend.
Recognition: one of eight finalist teams, UNSW Marketing Analytics Hackathon
Challenge 2026.

## Read and present

- [Current editable PowerPoint](output/cultural-blend-matched-benchmark.pptx):
  12 core slides plus four technical appendix slides, with speaker notes and sources.
- [Current slide-by-slide briefing](slide_brief_benchmark.md): each slide's
  message, reader decision, exhibit, evidence status and narration.
- [Matched benchmark findings](../../6_matched_text_results.md): the new
  full-data comparisons, uncertainty, limitations and next research decision.
- [Research review](../../4_research_review.md) and
  [approved ML design](../../5_ml_refinement_plan.md): original diagnosis,
  literature, consulting framework and pre-run design.
- Preserved [research-design deck](output/cultural-blend-research-refresh.pptx)
  and [original briefing](slide_brief.md): the earlier version proposing this study.

The current comparison finds modest linear duration gains from richer text,
with much smaller gains from compact text features in trees. Geographic
uncertainty and differing metric outcomes qualify those findings. The next
steps are construct validation, historical-data requests and a feasible
factual presentation experiment. The consulting structure uses a decision
question, issue tree, evidence matrix and explicit decision gates.

## Evidence boundary

The current deck separates primary August evidence, reviewed October explanatory
sensitivity and the November predictive extension. The full-data benchmark was
run separately from the notebook's report/plot execution. Both remain
retrospective; no editing benefit or all-listing deployment performance is
established. The earlier research-design deck predates the new run and remains
unchanged. Historical submitted materials and primary result snapshots are
preserved. Consult the [evidence corrections](../../2_evidence_and_corrections.md)
before reusing older claims.

## Edit and rebuild

Current content is generated in [storyline_benchmark.json](source/storyline_benchmark.json)
from the accepted aggregate bundle by [build_benchmark_story.py](source/build_benchmark_story.py).
The original design lives in [storyline.json](source/storyline.json). Layout is implemented
in [build_deck.mjs](source/build_deck.mjs) using `@oai/artifact-tool`. Text,
tables and charts are native editable PowerPoint objects. New charts read the
reviewed November results; retained primary exhibits keep their original source
labels. Chart workbook values are rounded to six decimal places for Excel
compatibility; exact values remain in the aggregate report. The MAE bars start
at zero, and the probability chart displays fixed-bin means with straight
segments. No row-level data are used to build the deck.

Install [DM Sans](../fonts/README.md) when editing the deck to avoid font
substitution.

Use the bundled Codex artifact runtime and presentation skill. Set
`ARTIFACT_NODE_MODULES` to the runtime's `node_modules` folder,
`PRESENTATION_SKILL_DIR` to the presentation skill folder, and
`ARTIFACT_PYTHON` to its bundled Python executable. Then run:

```sh
python docs/presentation/research_refresh/source/build_benchmark_story.py \
  --bundle reports/text_benchmark_reviewed
DECK_STORYLINE=docs/presentation/research_refresh/source/storyline_benchmark.json \
DECK_OUTPUT_NAME=cultural-blend-matched-benchmark-new.pptx \
node docs/presentation/research_refresh/source/build_deck.mjs
```

Use the bundled Node executable if it is not on `PATH`. The builder renders
all slides into ignored `.build/previews/`, validates the PPTX package and native
objects, and writes the selected deck into `output/`. It needs no network or
analysis dataset. After content changes, update
the corresponding briefing text, inspect every rendered slide and use a new
output filename for a new reviewed version.

Validation covers all rendered slides, native chart/table objects, package
integrity, layout geometry and artifact-tool re-import. It does not certify
a manual opening in Microsoft PowerPoint. Install DM Sans when editing.
