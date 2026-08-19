UNSW Marketing Analytics Hackathon 2026 - Statistical Analysis Report
========================================================================

SUPERSEDED

The raw-OLS analysis previously in this file (a single non-robust OLS fit
on `funding_speed_days`, without heteroskedasticity-robust standard
errors, a leakage-safe train/holdout split, or an audit trail of dataset
size/date range/exclusions) has been superseded by the reproducible
reporting pipeline added in Task 7.

Regenerate the current report by running, from the repository root:

    python3 -m src.run_analysis --data data/Kiva_Loans_Sample.pkl --output-dir reports/generated

This writes two auditable reports to `reports/generated/`:

  - `association_summary.txt`: the robust HC3 explanatory (association)
    summary for the duration and 24-hour funding models, together with an
    audit trail (dataset size, date range, exclusion counts, chronological
    holdout boundary, and software versions).
  - `analysis_summary.json`: the same audit trail plus the leakage-safe
    chronological baseline+Ridge evaluation and the nonlinear
    (gradient-boosted) benchmark metrics, in machine-readable form.

`reports/generated/` is gitignored (see `.gitignore`) since it is
regenerated from the source data rather than versioned; commit a specific
snapshot only if the team deliberately wants to preserve one run's output.
