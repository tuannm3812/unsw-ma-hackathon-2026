# Project Coding and Research Standards

Reviewed against the shared master standard on **2026-10-24**.

## 1. Baseline and scope

Follow `~/Documents/GitHub/coding-standards/coding_standards.md` for shared
Python style, Git hygiene, verification, and collaboration rules. This file
contains project-specific additions and deliberate overrides; it does not
copy the master or certify that every existing file is compliant.

This is an inference-led research project using Kiva loan data. Predictive
models provide complementary evidence; there is no competition leaderboard
score to optimise. Prefer defensible associations and clear limitations to
marginal gains in predictive fit.

The hackathon is complete. Cultural Blend was a **finalist**, as confirmed
by the team and the [official UNSW results](https://www.unsw.edu.au/business/our-schools/marketing/news-events/student-events/MA-hackathon).
Preserve submitted materials as historical evidence. Label subsequent
corrections and research extensions so they cannot be mistaken for the
submitted analysis or a prize-winning result.

## 2. Repository structure and authority

**Override of the master's notebook-first default:** the tested pipeline in
`src/`, invoked with `python3 -m src.run_analysis`, is the authoritative
implementation. Its inference, leakage checks, and reporting warrant a
separate tested package. Keep the existing structure:

| Location | Role |
| --- | --- |
| `src/` | Reusable analysis, validation, feature extraction, and reporting |
| `tests/` | Synthetic-fixture tests and notebook/documentation contracts |
| `notebooks/` | Exploration, explanatory walkthroughs, and executable notebook sources |
| `scripts/` | Data-dictionary, presentation, export, and compute helpers |
| `reports/generated_full_dataset/` | Deliberately committed primary full-data snapshot |
| `proposal/` | Submitted proposal; retain its historical sample-data scope |
| `docs/presentation/`, `docs/pdf/` | Presentation sources and selected rendered artifacts |
| `data/` | Gitignored restricted input files and a setup README |

The self-contained EDA and modeling notebooks implement simpler models.
Their estimates are not interchangeable with the primary pipeline's
estimates. Label notebook-derived results with their specification and run.
Expanded feature sensitivity remains a separate analysis until explicitly
reviewed and promoted; it must not silently replace the primary model.

## 3. Naming and documentation

This project's centre of gravity matches the master's **Shape A** modeling
workflow, despite its hackathon name. Preserve existing paths and history:

- Use single-digit numbered notebook names, such as `1_full_dataset_eda`.
  This now agrees with the master; it is not a zero-padding exception.
- Keep numbered top-level reference documents, including this file and
  [the data dictionary](1_data_dictionary.md).
- Retain `docs/superpowers/{plans,specs,collab-logs}/` for the existing
  planning and review history. Do not renumber it for cosmetic consistency.
- Put the project summary, current status, and reproduction entry points
  in [README.md](../README.md). Put detailed evidence beside its analysis.
- Keep `AGENTS.md` as the concise project entry point and `CLAUDE.md` as
  the single-line `@AGENTS.md` reference. Read the referenced standard
  explicitly when an agent does not expand imports automatically.
- Append meaningful changes, verification, and unresolved limitations to
  the [collaboration log](superpowers/collab-logs/2026-08-17-hackathon-upgrade-collab-log.md).
  Correct earlier entries by adding new evidence, not rewriting history.

## 4. Data scope and reproducible evidence

- Research findings use the full **1,453,846-row** input dataset. The
  100-row sample is for demonstrations and smoke tests only. Identify the
  dataset, eligible row count, exclusions, and analysis population for
  every reported result; the input count is not every model's sample size.
- Trace public numbers to a saved report or verified run log. Record the
  command/configuration, source revision and dirty state, data identity,
  run time, software versions, exclusions, and validation boundary.
- Keep primary results, exploratory results, and sensitivity checks
  distinguishable. Report disagreements rather than choosing whichever
  specification gives the most attractive conclusion.
- For the committed primary snapshot, retain both report formats and
  `provenance.json` together, following [reports/README.md](../reports/README.md).
  For new snapshots, capture equivalent provenance. Mark gaps in older
  runs honestly; do not invent missing hashes or execution records.
- Follow the master's run-capture policy: save logs, summary outputs, and
  provenance before the next Kaggle push. Identify each archive by run
  date/version; do not overwrite the only evidence for a published claim.
- `requirements-lock.txt` pins direct dependencies, not the complete
  environment or rendering toolchain. Record actual versions; do not
  promise byte-identical reproduction from that file alone.

## 5. Statistical claims and interpretation

- Describe associations, not causal effects. A non-significant coefficient
  does not establish no effect or a practically negligible effect. Report
  effect sizes, uncertainty, units, and the population to which they apply.
- Distinguish full-sample explanatory inference from chronological
  predictive evaluation. AUC, SHAP, and permutation importance do not
  validate a causal mechanism or a particular explanatory coefficient.
- Use the primary model's HC3 inference alongside country-clustered
  sensitivity where relevant. State the cluster count and dependence
  assumptions. Few-cluster reference calculations are heuristic screens,
  not calibrated confirmation; one-country groups cannot estimate
  between-country uncertainty.
- An interaction relative to a reference category is not a within-group
  association. Estimate the appropriate group-average contrast before
  making a claim about a region or sector.
- For exploratory feature searches, define the multiple-testing family
  and report the correction. Distinguish joint family tests from tests of
  individual features and label changes to controls or model families.
- Interpret coefficient signs against outcome definitions: shorter
  duration and higher probability of funding within 24 hours both mean
  faster funding, even though their coefficient signs differ.
- Results concern records with valid completed funding durations, including
  the separately reported refunded records. They do not estimate funding
  success across all listings. Unfunded/expired listings and censoring
  require additional data and an explicitly revised outcome design.
- Do not equate platform funding duration with borrower waiting time.
  Account for pre-disbursal before discussing borrower or partner impact.
- Treat programme/partner proxies as hypotheses requiring validation.
  Do not describe `whySpecial` as an observed partner identifier, or its
  descriptive differences as causal effects.

## 6. Features, validation, and Python style

Preserve the predictor allowlist and posting-time availability checks.
Exclude outcomes, post-outcome fields, and borrower identifiers from model
inputs. Never impute a missing outcome. Fit imputation, encoding, scaling,
TF-IDF, and topic models only on training data for predictive evaluation.
Use chronological validation consistently across compared models, with
matching rows and outcomes for feature-block comparisons. Keep full-sample
exploratory topic summaries explicitly separate from predictive transforms.

Follow the master's PEP 8, type-hint, and deterministic-seed guidance for
new or changed code. Keep configuration visible and make failures diagnostic
rather than silently substituting results. Preserve `InsufficientDataError`
for genuinely undersized validation partitions.

**Docstring override:** internal helpers may use short prose explaining
assumptions and non-obvious reasoning. Use Google-style parameter/return
documentation when units, shapes, or semantics need explanation. Do not
reformat unrelated code solely to restate typed signatures.

## 7. Notebook and chart workflow

Keep paired `.py` and `.ipynb` sources synchronised. Analysis notebooks need
visible configuration, deterministic seeds, numbered sections, interpretation
beside important outputs, and a closing limitations/next-steps section.
Retain kernel and language metadata and portable local input resolution.

**Output policy override:** `1_full_dataset_eda.ipynb` and
`2_full_dataset_modeling.ipynb` remain output-free, including cleared
execution counts. Verified numbers may appear in Markdown insight cells
with a traceable run source. `0_starter_eda.ipynb` retains genuine sample-run
outputs and must be re-executed after edits. New research notebooks should
start output-free; review any output-retention exception before committing.

Default analytical charts to Viridis. Show units, population, model source,
and uncertainty where relevant, with one clear interpretation per chart.
Presentation styling may follow the established deck design while retaining
legibility and accurate scales. Visually inspect changed charts and rendered
artifacts. Regenerate derived slide text/PDFs through their documented
scripts rather than editing generated mirrors independently.

## 8. Private compute and data protection

Kaggle is a private compute backend; leaderboard submission rules do not
apply. Keep kernels and datasets private and CPU-only by default. Public
code does not imply permission to publish the restricted dataset. Review
notebook outputs, logs, and exported artifacts for identifiers, raw text,
credentials, and local paths before sharing.

Two existing exceptions remain narrowly scoped:

- **Network:** the EDA/modeling kernels enable internet for the guarded
  VADER lexicon download and the modeling kernel's SHAP install fallback.
  Local pipeline/tests use the vendored lexicon and remain offline.
  Record fetched dependency versions; prefer attached/cached dependencies
  when revising this setup. New kernels default to internet-disabled.
- **Input discovery:** those notebooks use two known Kaggle mount candidates
  for this dataset. Preserve this explicit selection while it is valid;
  if generalising discovery, reject missing or ambiguous matches rather
  than silently reading another dataset.

Verify kernel metadata and actual completion/output before reporting a
successful remote run. Upload acceptance alone is not execution evidence.

## 9. Git hygiene and proportional verification

Keep restricted data, credentials, caches, kernel push copies, and large
regenerable artifacts out of Git. Selected aggregate reports, figures,
rendered deliverables, and privacy-reviewed run logs may be committed when
they directly support documented analysis. Make future generated-artifact
exceptions explicit in `.gitignore`; existing selected artifacts remain
part of the historical record.

Before staging, inspect `git status --short` and review every changed path.
Preserve pre-existing untracked research work; do not sweep it into an
unrelated commit or delete it as cleanup. Use scoped Conventional Commits
(`docs(standards): ...`, `fix(inference): ...`) for coherent changes and
avoid rewriting shared history.

| Change | Required evidence before claiming completion |
| --- | --- |
| Documentation only | Check paths/links, factual sources, and `git diff --check`; run relevant existing documentation contracts |
| Chart styling only | Render representative output and inspect it; no full-data inference rerun needed |
| Analysis or feature logic | Relevant synthetic tests and full offline suite; rerun affected full-data analysis before publishing revised findings |
| Notebook logic | Check source-pair consistency, metadata, output policy, and actual execution on the intended platform |
| Dependency changes | Verify imports/tests and rerun affected numerical or rendering workflows before replacing trusted artifacts |
| New result snapshot | Review provenance, population/exclusions, uncertainty, and consistency of reports and public claims |

Use `python3 -m pytest -q` in the project's environment for the full offline
suite. Report the observed count and warnings with the run date; do not
hardcode a moving test count into this standard. A passing test suite does
not establish that the full-data analysis was rerun. If execution is still
pending, label the affected results unverified and retain the trusted
snapshot until replacement evidence is available.
