# Research Maintenance Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for integration and verification. Independent evidence reviews may run in parallel under superpowers:dispatching-parallel-agents.

**Goal:** Apply the approved review improvements and project standard to the completed finalist project, preserving historical evidence and producing an accurate portfolio case study.

**Architecture:** Retain the primary pipeline and its trusted snapshot. Integrate the existing expanded sensitivity as a separately labelled research workflow; audit programme-text grouping before using it as a possible control. Current documentation points to corrected interpretation while submitted and generated historical materials retain their identity.

**Tech Stack:** Existing Python, pandas, SciPy, statsmodels, scikit-learn, pytest, Jupytext, Markdown, and matplotlib tooling.

**Spec:** `docs/0_coding_standards.md`, the project review in this chat, and the user's instruction to apply everything. Finalist recognition only; LinkedIn achievement text rather than a feed post.

## Global constraints

- Use all 1,453,846 input rows for research evidence; synthetic fixtures only for tests.
- Preserve primary reports and original submission history. No unsupported causal or null-effect claims.
- Keep restricted data and borrower text out of Git and public artifacts.
- Do not invent historical provenance. Label recovered snapshots and capture current hashes separately.
- Preserve pre-existing untracked sensitivity work and include it only in its own reviewed change.
- No dependency upgrades, unrelated formatting churn, or external publishing.

## Review focus

- Third-person coefficients on differently oriented outcomes must not be called a reversal.
- A programme-text category is not a verified field-partner identifier.
- Nested controls and rank deficiency must not produce spurious clustered uncertainty.
- Saved run metadata must distinguish a current rerun from recovery of old results.
- Notebook pairs, generated mirrors, report boundaries, and linked docs must remain consistent.

## Tasks

### 1. Documentation and public claims
- [x] Refresh README status and move event logistics into a historical reference.
- [x] Add a current corrections/evidence document and portfolio case study with one source-backed chart.
- [x] Preserve submitted materials; clearly identify superseded preparation claims and correct editable source interpretations.
- [x] Check links and relevant notebook/documentation contracts.

### 2. Expanded sensitivity workflow
- [x] Review untracked module, tests, notebook pair, and saved outputs.
- [x] Fix demonstrated defects with focused regression tests; preserve old results if estimates change.
- [x] Capture honest recovery provenance and document reproduction and inference scope.
- [x] Verify output policy and both synthetic tests and report consistency.

### 3. Programme proxy assessment
- [x] Audit all full-data records for programme-text coverage, cardinality, nesting, and eligible subgroup sizes without exporting raw text.
- [x] Assess feasibility of an additional programme-controlled sensitivity with the reviewed regression machinery.
- [x] Run a full-data extension if the design is identifiable and computationally feasible; otherwise record the concrete limitation and data needed.
- [x] Keep results exploratory, report effect sizes/uncertainty, and trace saved outputs to code/data.

### 4. Repository integration
- [x] Apply narrow portability, artifact-ignore, and evidence-discovery fixes needed by these workflows.
- [x] Run the full offline suite, validate notebook pairs, inspect the chart, and check documentation paths.
- [x] Obtain an independent final review; resolve material findings and update the append-only collaboration log.
- [x] Preserve coherent local commits for standards, sensitivity, extension, and documentation; do not push to shared main.

## Decisions and execution record

- 2026-10-24: Work in the existing checkout on a dedicated branch rather than copy untracked research into a new worktree. This preserves access to the existing data and environment while keeping commits off main.
- Baseline: preceding review passed 121 tests; documentation update passed 8 contract tests. Recheck after implementation; neither run was a fresh full-data analysis.

- Implementation decision: historical slide briefs, scripts, and rendered mirrors
  are retained together rather than silently rewritten. Current interpretation
  is corrected in the evidence guide and portfolio case study, with archive
  notices at their entry points. No historical PDF/PPTX was regenerated.
- The independent estimator review matched a dense OLS calculation (maximum
  coefficient error 1.22e-15; clustered-SE relative error 1.55e-15). All four
  notebook pairs and 45 checked current-document links passed validation.
- Full offline suite: 134 passed, one known joblib physical-core-detection
  warning, 40.92 seconds. Full notebook execution and predictive reruns are
  outside this maintenance run and are not claimed.

- Final full-data inspection found a further absorbed reference-indicator defect:
  `whySpecial_missing` was exactly determined by the programme category, but
  LSMR left relative residue 1.5246e-8 above the original 1e-8 guard. The first
  maintenance run is preserved as rejected diagnostic evidence. A 12,000-row
  synthetic regression reproduced the enormous standard error before the fix.
- Added exact within-category absorption on the complete-case sample before
  numerical projection, using the encoder's string grouping. Independent review
  approved the fix; 15 focused tests and the full 135-test suite passed (one
  known physical-core warning; 18.35 seconds). A corrected full-data rerun is
  required before the programme results are accepted.

- Corrected full-data rerun completed successfully in 23m05s. All four fits
  use 1,453,840 eligible rows and 48 clusters, with no extra exclusions or
  missingness. Programme rank is 883/886 controls and 906 total parameters;
  all three programme-determined text features are absorbed, leaving 23 terms.
  Source/resource hashes, CSV/JSON agreement, t/F inference and BH calculations
  passed independent review. The baseline is bit-for-bit unchanged from the
  first maintenance run. Primary prediction and submission files are unchanged.
- Programme adjustment moves third-person duration q from 0.01236 to 0.06062;
  the business-framing 24-hour q is 0.00635. The corrected auxiliary-family
  tests no longer support the rejected first run's claim. All findings remain
  exploratory associations, with per-outcome/specification multiplicity scope.

- Final independent integration review passed with no blocking findings. The
  corrected run is accepted as exploratory sensitivity only, with an explicit
  review-status receipt; source hashes reconstruct from commit `e57e5f2`.
