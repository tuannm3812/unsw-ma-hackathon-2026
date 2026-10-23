# Recovered expanded feature sensitivity

## 1. Status and evidence boundary

This directory preserves three pre-existing aggregate outputs recovered during
maintenance on **2026-10-24**. Their embedded generation timestamp is
`2026-09-03T06:39:30.114468+00:00`; that timestamp is a claim in the saved JSON,
not an independently recovered execution log. These files were not regenerated
or edited during recovery. They are exploratory research evidence, separate
from the [primary pipeline snapshot](../generated_full_dataset/) and submitted
hackathon materials.

**The historical inference requires a corrected full-data rerun before reuse.**
Synthetic regression tests exposed numerical defects in the recovered estimator:
features absorbed by controls could be retained after normalizing solver noise;
redundant controls were counted as extra parameters in the clustered correction;
LSMR convergence was unchecked; and a singular family covariance could produce
a misleading full-family p-value through a pseudoinverse. The corrected source
records rank, exclusions and test availability and refuses singular family tests.
The extent to which these changes affect this saved run has not been measured
by recovery inspection. Do not combine old coefficients with corrected-code
claims or present the saved inference as newly verified.

The Ridge prediction comparison is a separate workflow; these regression fixes
do not themselves change it. Its original execution provenance is still missing.

## 2. Population and interpretation

The repository's full input contains **1,453,846 rows**. The saved JSON reports
1,174,953 training rows and 278,887 holdout rows (1,453,840 combined), split at
2024-01-01, and 1,453,840 rows with 48 country clusters in each inference fit.
The difference of six rows from full input is arithmetic; the old output does
not provide a per-reason exclusion audit. Valid completed durations include
funded and separately identified refunded records. This is not an analysis of
funding success among all listings or of censored/unfunded loans.

Duration inference uses OLS on `log_funding_speed` (log1p of days). The 24-hour
outcome uses a linear-probability model, with coefficients in probability units
(multiply by 100 for percentage points). These replace neither the primary
pipeline's specification nor its binomial GLM. The separate chronological Ridge
comparison uses training-fitted preprocessing and topics; predictive improvement
does not validate a causal narrative mechanism. Rich-control inference is
complete-case; prediction uses train-fitted covariate imputation.

Negative duration and positive 24-hour coefficients both indicate faster
funding. The saved third-person coefficients therefore point in the same speed
direction, not a reversal. Non-significance does not demonstrate no association.
Platform funding duration is not necessarily borrower waiting time, particularly
for pre-disbursed loans. `whySpecial` is text, not a verified partner identifier.

## 3. Multiple testing and rank

The original saved individual `fdr_p_value` values apply Benjamini–Hochberg to
**26 retained narrative terms separately within each outcome**. The five saved
family-level Wald p-values per outcome are **unadjusted**; no correction across
outcomes or all analyses was recorded. Do not treat these as a single study-wide
FDR guarantee. Correlated exploratory feature tests and country-clustered t/F
reference distributions require cautious interpretation.

Corrected code separately applies BH to the reported family tests within each
outcome, retaining unavailable tests conservatively as p=1 in that correction
and displaying their adjusted result as missing. A family after column dropping
tests only retained terms, not the original requested family. Numerical thresholds
and control rank are now recorded. Neutral VADER share is deliberately omitted
as a reference; rounding and empty descriptions mean the shares are not always
an exact composition. This restriction must not be described as proof of exact
linear dependence in the data.

## 4. Reproduction and provenance

From the repository root, with the restricted input and project environment:

```bash
.venv/bin/python -m src.feature_sensitivity \
  --data data/Kiva_Loans.pkl \
  --output-dir reports/expanded_feature_sensitivity_NEW_RUN_ID \
  --holdout-start 2024-01-01 \
  --n-topics 5
```

Choose a fresh run ID. The corrected writer refuses to overwrite existing result
files. Writes are atomic per file, not a transaction across all three files.
The [paired notebook](../../notebooks/3_expanded_feature_sensitivity.ipynb) starts
output-free and chooses a timestamped destination. Notebook source validation is
not evidence of full execution.

Capture the new run's command/configuration, input hash, code revision and dirty
state, actual package versions, start/end times, exclusions and execution log
alongside its outputs before publishing revised findings. Direct dependency pins
do not define a completely reproducible environment.

[recovery_provenance.json](recovery_provenance.json) records inspection hashes
and current environment information. The original source revision, dirty state,
input hash, command, software versions, execution log and per-reason exclusions
were unavailable in the recovered artifacts. Current hashes cannot fill those
historical gaps. No full-data rerun is claimed by this recovery record.
