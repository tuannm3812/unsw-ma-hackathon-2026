# `reports/`

This directory holds no committed evidence artifact itself - the
notebook (`notebooks/starter_eda.ipynb`) is the sole committed evidence
artifact for this project, with real, current output from the last
execution baked into its cells. Anything under `reports/` is either
generated fresh from the source data or a stale, explicitly-superseded
leftover kept only as a pointer (this file).

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

This file used to be `reports/statistical_summary.txt`, the output path
of a single non-robust OLS fit (no heteroskedasticity-robust standard
errors, no leakage-safe train/holdout split, no audit trail) written by
an early, since-superseded version of the pipeline. That output was
replaced by the reproducible reporting pipeline above; this file was
renamed from a one-off `.txt` notice to a `README.md` so it renders
automatically when browsing this directory on GitHub, instead of being
mistaken for a committed report.
