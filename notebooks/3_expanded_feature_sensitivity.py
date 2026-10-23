# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Expanded Narrative-Feature Sensitivity
#
# The project's existing explanatory model is still the **pre-specified
# primary specification**. This notebook tests a narrower audit question:
# did that compact model's feature selection hide materially different text
# evidence?
#
# It adds two complementary checks:
#
# 1. A chronological Ridge comparison of structural-only, primary-narrative,
#    and expanded-narrative feature blocks.
# 2. Full-sample partial regressions for log funding duration and funding
#    within 24 hours, using country/activity/year/month controls, standard
#    errors clustered by country, joint feature-family tests, and
#    Benjamini-Hochberg false-discovery-rate adjustment.
#
# The 24-hour sensitivity is a linear-probability model for computationally
# tractable verification with rich fixed effects. It does not replace the
# primary binomial GLM. As everywhere else in this project, results are
# associations among records with valid completed durations, including
# separately identified refunded records; they are not causal effects or
# funding-success estimates across all listings. The recovered September
# snapshot requires a corrected rerun; see the report directory README.

# %%
import gc
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

try:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
except NameError:
    PROJECT_ROOT = Path.cwd()
    if PROJECT_ROOT.name == "notebooks":
        PROJECT_ROOT = PROJECT_ROOT.parent
if not (PROJECT_ROOT / "src").is_dir():
    raise RuntimeError("Run from the repository root or its notebooks directory")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATA_PATH = PROJECT_ROOT / "data" / "Kiva_Loans.pkl"
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
OUTPUT_DIR = PROJECT_ROOT / "reports" / f"expanded_feature_sensitivity_{RUN_ID}"

from src.data_loader import load_kiva_pickle
from src.feature_sensitivity import (
    EXPANDED_NARRATIVE_FEATURES,
    NARRATIVE_FEATURE_FAMILIES,
    PRIMARY_NARRATIVE_FEATURES,
    RICH_CATEGORICAL_CONTROLS,
    RICH_NUMERIC_CONTROLS,
    build_sensitivity_frame,
    evaluate_nested_ridge,
    fit_clustered_partial_regression,
    write_sensitivity_outputs,
)


HOLDOUT_START = "2024-01-01"
N_TOPICS = 5

# %% [markdown]
# ## 1. Feature coverage being tested
#
# The expanded block includes every deterministic narrative measure currently
# engineered by `src/features.py`. Neutral VADER share is the explicit
# reference in inference. Rounding and empty descriptions mean the shares
# do not always sum exactly to one; this is a specification restriction.
# Absorbed and numerically dependent columns are reported separately. Five training-fitted NMF topic loadings
# are added to the chronological prediction comparison only.

# %%
coverage_rows = []
for family, features in NARRATIVE_FEATURE_FAMILIES.items():
    for feature in features:
        coverage_rows.append(
            {
                "family": family,
                "feature": feature,
                "in_primary_explanatory_model": feature in PRIMARY_NARRATIVE_FEATURES,
                "in_expanded_sensitivity": feature in EXPANDED_NARRATIVE_FEATURES,
            }
        )
feature_coverage = pd.DataFrame(coverage_rows)
feature_coverage

# %% [markdown]
# ## 2. Load the complete dataset

# %%
started = time.perf_counter()
raw = load_kiva_pickle(str(DATA_PATH))
print(f"Loaded {len(raw):,} rows and {raw.shape[1]} raw columns in {time.perf_counter() - started:.1f}s")

# %% [markdown]
# ## 3. Incremental out-of-time predictive value
#
# Every block uses the same 2016–2023 training and 2024–2025 holdout split.
# Learned imputations, scaling, one-hot encodings, and NMF topics are fitted
# on training rows only. Ridge is used here as a fast, consistent block test;
# the project's existing nonlinear benchmark remains the main forecasting
# result.

# %%
started = time.perf_counter()
featured = build_sensitivity_frame(raw)
print(f"Prepared deterministic features in {(time.perf_counter() - started) / 60:.1f} minutes")

# %%
started = time.perf_counter()
prediction = evaluate_nested_ridge(
    raw,
    featured_frame=featured,
    holdout_start=HOLDOUT_START,
    n_topics=N_TOPICS,
)
prediction_table = pd.DataFrame(prediction["blocks"]).T
prediction_table["delta_mae_vs_structural"] = (
    prediction_table["holdout_mae_days"]
    - prediction_table.loc["structural_only", "holdout_mae_days"]
)
prediction_table["delta_r2_vs_structural"] = (
    prediction_table["holdout_r2"]
    - prediction_table.loc["structural_only", "holdout_r2"]
)
print(f"Chronological block comparison completed in {(time.perf_counter() - started) / 60:.1f} minutes")
prediction_table

# %% [markdown]
# ## 4. Rich-control clustered association sensitivity
#
# Country replaces region and activity replaces sector to avoid exact nesting.
# Posting year and month replace the three broad period main effects. The
# country fixed effects control stable country-level differences; clustering
# by country separately allows residuals within a country to be correlated.

# %%
featured = featured.loc[featured["valid_completed_outcome"]].copy()
del raw
gc.collect()
print(f"Retained {len(featured):,} valid completed-loan rows")

# %%
inference = {}
for outcome in ["log_funding_speed", "funded_within_24h"]:
    started = time.perf_counter()
    inference[outcome] = fit_clustered_partial_regression(
        featured,
        outcome=outcome,
        narrative_features=EXPANDED_NARRATIVE_FEATURES,
        numeric_controls=RICH_NUMERIC_CONTROLS,
        categorical_controls=RICH_CATEGORICAL_CONTROLS,
        cluster_col="country_name",
        feature_families=NARRATIVE_FEATURE_FAMILIES,
    )
    print(f"{outcome} completed in {(time.perf_counter() - started) / 60:.1f} minutes")

# %% [markdown]
# ### Joint feature-family tests
#
# These exploratory tests assess retained terms within each family after
# rich controls. BH adjustment covers the reported family tests separately
# within each outcome, not across both outcomes or all research searches.
# Singular covariance makes a full family test unavailable; inspect rank,
# degrees of freedom and status before interpreting the p-value. A test
# after dropping terms cannot establish a result for the original full family.

# %%
joint_tables = []
for outcome, result in inference.items():
    table = result["joint_tests"].copy()
    table.insert(0, "outcome", outcome)
    joint_tables.append(table)
joint_results = pd.concat(joint_tables, ignore_index=True)
joint_results

# %% [markdown]
# ### Individual narrative coefficients
#
# `fdr_p_value` applies Benjamini-Hochberg adjustment across all retained
# narrative terms within each outcome. These coefficients still do not imply
# that changing the corresponding words would cause funding speed to change.

# %%
coefficient_tables = []
for outcome, result in inference.items():
    table = result["coefficients"].copy()
    table.insert(0, "outcome", outcome)
    coefficient_tables.append(table)
coefficients = pd.concat(coefficient_tables, ignore_index=True)
coefficients.sort_values(["outcome", "fdr_p_value", "p_value"])

# %%
print("Columns removed by the neutral-reference choice, absorption, or numerical rank check:")
for outcome, result in inference.items():
    print(outcome, result["dropped_narrative_features"])

# %% [markdown]
# ## 5. Persist the audit trail
#
# Machine-readable JSON, a coefficient CSV, and a readable text report are
# written to a fresh timestamped directory with per-file atomic writes.
# Existing snapshots cannot be overwritten. Preserve a separate provenance
# record with the command/configuration, code revision and dirty state, data
# identity/hash, software versions and execution log before sharing findings.

# %%
payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "analysis_scope": "expanded_feature_sensitivity_not_primary_specification",
    "prediction": prediction,
    "inference": inference,
}
paths = write_sensitivity_outputs(payload, OUTPUT_DIR)
for name, path in paths.items():
    print(f"{name}: {path}")

# %% [markdown]
# ## 6. Interpretation, limitations and next steps
#
# - If the expanded block adds little holdout value and no feature family is
#   jointly supported under rich controls, report the effect sizes and
#   uncertainty. Non-significance does not establish no association or
#   practical equivalence.
# - If an omitted family adds holdout value or survives clustered/FDR checks,
#   the deck must stop generalizing from the three selected dictionaries and
#   present the new result as a sensitivity finding requiring validation.
# - In either case, `use` and `whySpecial` still enter only through simple
#   lengths/missingness, and contextual semantic/discourse features remain
#   future work.
# - Shorter log duration and higher 24-hour probability both mean faster
#   funding; opposite coefficient signs across these outcomes are concordant.
# - Country-clustered t/F reference distributions are approximate. Few-cluster
#   subgroups and singular family covariance cannot support calibrated claims.
# - Complete-case exclusions are recorded per fit; compare specifications on
#   matching rows. Prediction uses all valid-duration rows and train-fitted
#   imputation, so its population can differ from complete-case inference.
# - This notebook has been source-checked and starts output-free. Execute it
#   on the intended platform and inspect results before publishing a new run.
