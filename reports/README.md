# `reports/`

`reports/generated_full_dataset/` **is** a committed evidence artifact -
a deliberate, labeled snapshot of `src.run_analysis` run against the real
full 1,453,846-row dataset (see below). It, together with
`notebooks/0_starter_eda.ipynb` (real output baked into 9 of its 13 code
cells, from the 100-row sample), is this project's committed *executed*
evidence. `notebooks/1_full_dataset_eda.ipynb`/
`notebooks/2_full_dataset_modeling.ipynb` are different: their code cells
carry zero stored output (they're committed as output-free sources, kept
in sync with their `.py` pairs) - their real numbers are verified by
executing them on Kaggle and cross-checking the run log, not by anything
baked into the committed `.ipynb` file itself; their narrative
conclusions are committed prose, not executed evidence. Everything else
under `reports/` is generated fresh from the source data and gitignored.

## `reports/generated_full_dataset/` (committed)

`analysis_summary.json` and `association_summary.txt` here are the
authoritative source for the full-dataset numbers in `README.md`'s
"Full-Dataset Results" section - produced by `python3 -m src.run_analysis`
against `data/Kiva_Loans.pkl`, **not** by either full-dataset notebook
(those are a deliberately simpler, self-contained re-implementation for
Kaggle; see `README.md`'s Kaggle Workflow section). Note that a few
figures in that README section are deliberately quoted from the
*notebooks'* own models instead - they are labelled as such inline, and
exist to document where the two implementations differ (sentiment tone's
significance is the genuine disagreement; the family-framing
within-region averages agree across all fits). Those numbers will not be
found in the files here; the Kaggle run logs are their source.

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
  summary for the duration and 24-hour funding models, the leakage-safe
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
