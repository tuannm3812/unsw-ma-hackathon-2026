# `reports/`

`reports/generated_full_dataset/` **is** a committed evidence artifact -
a deliberate, labeled snapshot of `src.run_analysis` run against the real
full 1,453,846-row dataset (see below). It, together with
`notebooks/0_starter_eda.ipynb` (real output baked into 9 of its 13 code
cells, from the 100-row sample), is part of this project's committed *executed*
evidence. `notebooks/1_full_dataset_eda.ipynb` and
`notebooks/2_full_dataset_modeling.ipynb` are output-free source pairs.
Their execution must be evidenced separately. The maintained modeling
notebook now consumes a reviewed matched benchmark from shared `src/`
helpers; it no longer contains the historical self-contained Kaggle fits.
Additional selected research snapshots are listed below. Other generated
reports remain ignored unless explicitly selected in `.gitignore`.

## `reports/generated_full_dataset/` (committed)

`analysis_summary.json` and `association_summary.txt` here are the
authoritative source for the full-dataset numbers in `README.md`'s
"Full-Dataset Results" section - produced by `python3 -m src.run_analysis`
against `data/Kiva_Loans.pkl`, **not** by the maintained notebooks.
Historical notebook fits used different measurements/specifications and
must not be relabelled as primary estimates. Consult the
[current evidence corrections](../docs/2_evidence_and_corrections.md)
before reusing those comparisons. The primary predictive split separates
posting dates but does not enforce completion before the training cutoff;
the separate matched benchmark audits that availability constraint.

Beyond the audit trail, classifier metrics and coefficient tables,
`association_summary.txt` contains **two pipeline-generated sections**
(both produced by `run_analysis` itself when
`--cluster-sensitivity-column country_name` is passed; both also have
machine-readable counterparts under `analysis_summary.json`'s
`explanatory` key):

1. **Cluster-Robust Sensitivity Check** - HC3 vs. country-clustered
   standard errors for every coefficient in both explanatory models.
2. **Average Within-Region Family-Framing Slopes** - each region
   category's family-framing slope averaged over that category's own
   moderator composition, which is what the project's headline
   narrative-framing claim actually rests on. An interaction coefficient
   alone does not establish a within-region association, and
   "main effect + region term" is a slope at one unrepresentative cell -
   this section is the correct quantity, computed and tested in
   `src/statistical_analysis.py` (see
   `test_average_group_slopes_match_brute_force_rowwise_average`).

**Provenance of the current snapshot:** regenerated end-to-end on
2026-08-31T12:50 UTC by the Kaggle pipeline kernel
(`notebooks/kernels/full_dataset_pipeline/`, see `README.md`'s
"Regenerating the committed snapshot on Kaggle"), not on a laptop. Its
audit trail therefore records Kaggle's software stack (python 3.12.13,
pandas 2.3.3, numpy 2.0.2, scikit-learn 1.6.1, statsmodels 0.14.6 -
newer than the local venv that produced earlier snapshots) and a
Kaggle-relative `source_path`
(`../input/datasets/.../Kiva_Loans.pkl`). The within-region few-cluster
p-values match the last local run to all four printed decimals, and the
headline predictive metrics are unchanged.

**Provenance binding:** a Kaggle-regenerated snapshot must be committed
together with the `provenance.json` the runner writes beside it, which
records the code dataset's git commit, whether that tree was dirty when
published, the src-tree content hash at publish time, and the runner's
own re-hash of what Kaggle actually mounted. Kaggle kernel metadata
cannot pin dataset versions (it always mounts the latest), so this file
- plus the kernel/dataset version pages on Kaggle - is the audit trail
tying the committed numbers to exact inputs. The runner refuses to run
if the code dataset carries no provenance record. The current (2026-08-31) snapshot carries this record: `provenance.json`
here names commit `5e3e349`, a clean tree, and a mounted-src hash the
runner verified against the publish-time hash. (The superseded 2026-08-30
snapshot predated the mechanism and came from a then-uncommitted tree -
the collaboration log records that honestly.)

**A regeneration that omits `--cluster-sensitivity-column country_name`
will drop both sections** - see `README.md`'s reproduction command, which
includes the flag for exactly this reason. (Earlier snapshots of this
directory carried these results as manually appended addenda, one of
which - a "Simple-Slope Contrasts" section computing slopes at a single
reference cell - was withdrawn as incorrect; both are now first-class
pipeline output.)

## Regenerating a report

```bash
python3 -m src.run_analysis --data data/Kiva_Loans_Sample.pkl --output-dir reports/generated
```

This writes two auditable reports to `reports/generated/`:

- `association_summary.txt`: the robust HC3 explanatory (association)
  summary for the duration and 24-hour funding models, the posting-date
  chronological classifier's ROC AUC/average precision/Brier score, and
  an audit trail (dataset size, date range, exclusion counts,
  chronological holdout boundary, and software versions).
- `analysis_summary.json`: the same audit trail plus every stage's
  metrics (baseline+Ridge, nonlinear benchmark, binary classifier,
  explanatory models) in machine-readable form.

`reports/generated/` is gitignored (see `.gitignore`) since it is
regenerated from the source data rather than versioned; commit a
specific snapshot only if the team deliberately wants to preserve one
run's output alongside this README.

## History

This file used to be `reports/statistical_summary.txt`, a committed
notice pointing at the reproducible reporting pipeline above, which
replaced an early, non-robust single-OLS report (no heteroskedasticity-
robust standard errors, no leakage-safe train/holdout split, no audit
trail) that version used to write there. The *committed* file was
renamed from a one-off `.txt` notice to a `README.md` so it renders
automatically when browsing this directory on GitHub, instead of being
mistaken for a committed report.

The old filename isn't fully retired at the code level, though:
`src/statistical_analysis.py::run_ols_analysis` is a legacy,
backward-compatible entry point (not called by `src/run_analysis.py` or
the notebook - only by that module's own `if __name__ == "__main__":`
block) that still writes a file literally named `statistical_summary.txt`
if invoked directly. It uses the current, robust `fit_explanatory_models`
internally, so its content is not stale the way the old committed file
was - it just isn't part of this project's actual reporting path.


## Maintained research extensions (October 2026)

- [Expanded sensitivity recovery](expanded_feature_sensitivity/README.md):
  the September output is preserved with honest recovery provenance and
  numerical-audit limitations; it is separate from the primary snapshot.
- [Programme-text audit](programme_proxy_audit/README.md): a fresh full-data
  aggregate audit of coverage and country nesting, with no raw text exported.
- [Reviewed inference](expanded_feature_sensitivity_reviewed/README.md):
  expanded OLS/LPM sensitivity and a programme-text control comparison, with
  source/data hashes, execution log, package versions and matching-population
  checks. It does not rerun prediction or replace the primary specification.
  Reproduce with `python3 -m src.research_review --data data/Kiva_Loans.pkl
  --output-dir reports/reviewed_new`, choosing a fresh output directory.
- [Rejected diagnostic run](expanded_feature_sensitivity_diagnostic/README.md):
  an absorbed missingness indicator survived numerical projection in the first
  programme model. Its outputs are preserved to explain the regression fix;
  do not use its affected coefficients or tests as substantive evidence.

## Matched predictive benchmark (November 2026)

The [separate matched text study](text_benchmark_reviewed/README.md) compares
structured, text and combined feature blocks on the full input using five
annual retrospective evaluations. It requires training outcomes and completed
cohort membership before each cutoff. Its 65 model/arm results and 120 paired
intervals are separate from the primary August predictions and October
explanatory extension. Exact sources, data identity, warnings and technical
review accompany the selected aggregate snapshot.

The maintained notebook 2 reads this bundle through shared `src/` helpers.
It does not silently rerun the models in default reviewed-report mode. Read
[the findings](../docs/6_matched_text_results.md) for interpretation and
[the bundle README](text_benchmark_reviewed/README.md) for reproduction.
