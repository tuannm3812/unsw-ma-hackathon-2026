# Reviewed matched text benchmark

Separate post-competition predictive extension, 2026-11-02. This snapshot
compares the added predictive information in narrative text on the full
1,453,846-record input, retaining 1,453,840 valid completed durations.
It does not replace the August primary report or October inference extension.

Read [the findings](../../docs/6_matched_text_results.md) first. The maintained
[modeling notebook](../../notebooks/2_full_dataset_modeling.ipynb) validates this
bundle and builds its insight tables and charts without retraining by default.

## Contents and acceptance

- `benchmark.json`: all 65 model/arm windows (two targets each), paired gains,
  calibration bins, group diagnostics, fit metadata and recorded warnings.
- `availability_audit.json`: full-data exclusions, missing text, duplicates and
  unavailable training-cohort membership at each annual cutoff.
- `provenance.json`, `source_snapshot.zip`: data/source identities, configuration,
  environment and exact computational sources used by the run.
- `status.json`: completed execution, still named `completed_pending_review` to
  preserve the runner's original state. Technical acceptance is a separate,
  hash-bound `review_status.json`; completion alone is not acceptance.
- `prediction_review.json`: independent checks of saved predictions, metrics,
  calibration, subgroup slices, paired intervals and calendar row identities.
- `actual_warning_review.json`, `synthetic_warning_review.json`: numerical
  investigations of the recorded matrix-multiplication warnings.
- `environment_supplement.json`, `run.log`, `review_scripts.zip`: environment,
  execution trace and exact diagnostic/recomputation code for the review.
- `notebook_execution.json`: verified execution of all 13 report/plot code
  cells, with zero errors and five embedded figures, bound to the notebook
  source pair and benchmark hashes. This is separate from model training.

The run used uncommitted source changes on revision `7afea5f`; the source
archive and file hashes identify the executed code more precisely than that
Git revision alone.

Only aggregate results and source code are selected. Original row positions,
labels, predictions, feature cache and raw narrative text remain ignored and
local. The five private prediction archives are identified by hashes in the
review, without redistributing their contents.

## Numerical review

The run records three matrix-multiplication warnings for each of 15 Ridge
fits containing TF-IDF, for 45 warnings in total. Synthetic vector and CSR
probes reproduced the warning family under NumPy's Apple Accelerate build,
including both float32 and float64 fits. The actual 2021 text-only arm traced
the three warnings to scikit-learn's intercept calculation and reproduced its
saved duration and classification predictions exactly. Its intercept differed
from an explicit float64 product-sum by 5.008e-9 on the log-duration scale.

This supports retaining that reproduced arm and documenting the shared warning
pattern. It is not an exhaustive higher-precision refit of every window.
The full review also checks every saved prediction for finiteness and verifies
that no Ridge/SGD iteration cap was reached. The fixed 100-iteration tree
budget is intentional, not a convergence claim. Warnings remain in the report;
the empty outer warning list in the diagnostic reflects capture inside its
intercept wrapper and does not mean the refit was warning-free.

## Reproduce separately

The recorded runtime reuses a verified deterministic-feature cache and excludes
its original feature-build time.

Use the existing pinned numerical environment in `requirements-lock.txt` and
obtain the restricted dataset through the project's authorised data workflow.
From the repository root, choose a new output directory:

```sh
python -m src.run_text_benchmark \
  --data data/Kiva_Loans.pkl \
  --output-dir reports/text_benchmark_new_run \
  --feature-cache reports/text_benchmark_private/features.pkl
```

An existing output directory is rejected. Cache reuse requires identical data,
feature-source/resource hashes and versions; select a new cache path when
those change. A new run remains pending technical review. Do not copy this
snapshot's acceptance record to another run.

The diagnostic scripts in `review_scripts.zip` target the recorded local run
folder `reports/text_benchmark_20261102` and private cache/predictions. Extract
them to a scratch directory before inspection or execution; adjust paths for a
separate run. The synthetic diagnostic writes its JSON beside its script.
The review can be independently repeated only with the restricted source and
private prediction archives, or after reproducing them.

For current notebook use, run `notebooks/2_full_dataset_modeling.ipynb` from
this repository or its notebooks directory. `KIVA_BENCHMARK_DIR` selects a
reviewed bundle; the default is this folder. `RUN_MODE = "run"` explicitly
launches a fresh benchmark and labels its outputs pending review. Executed
notebook copies and generated figures stay private; the source pair is
output-free.

## Interpretation

All five annual windows are retrospective. Training cohort membership and
outcomes precede each cutoff, but evaluation still selects eventual completed
records. Historical text/field versions, marketplace exposure and all-listing
histories remain unavailable. Programme categories are unvalidated text
proxies. Cluster intervals are pointwise, without multiplicity adjustment. They
condition on fitted models and do not estimate a
writing intervention's benefit. No human annotation, external untouched test,
calibrated deployment model or prospective pilot is part of this snapshot.
