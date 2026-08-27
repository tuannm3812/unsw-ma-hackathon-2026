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
# # Full-Dataset EDA (1.45M rows) - Real Findings
#
# This notebook runs the same tested `src/` pipeline as
# `00_starter_eda.ipynb`, just against the **real, full competition
# dataset** instead of the 100-row illustrative sample - these are the
# numbers that back the final presentation, not a demonstration. No model
# fitting here (see `02_full_dataset_modeling.ipynb` for that); this
# notebook is descriptive only, so it stays fast enough to iterate on.
#
# Designed to run both locally and as a private Kaggle kernel (see
# `../scripts/push_kaggle_kernel.sh` and README.md's "Kaggle Workflow"
# section) - it auto-detects which environment it's in and resolves paths
# accordingly, the same portability pattern `00_starter_eda.ipynb` already
# uses for the project root.

# %%
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def _find_project_root(start: Path) -> Path:
    candidate = start
    for _ in range(5):
        looks_like_root = (
            (candidate / "data" / "Kiva_Loans_Sample.pkl").exists()
            and (candidate / "src").is_dir()
        )
        if looks_like_root:
            return candidate
        if candidate.parent == candidate:
            break
        candidate = candidate.parent
    return start


KAGGLE_DATA_DIR = Path("/kaggle/input/kiva-loans-hackathon-data")
KAGGLE_CODE_DIR = Path("/kaggle/input/kiva-hackathon-src")

if KAGGLE_DATA_DIR.exists():
    # Running as a Kaggle kernel: both private datasets are mounted
    # read-only under /kaggle/input/.
    DATA_PATH = KAGGLE_DATA_DIR / "Kiva_Loans.pkl"
    if str(KAGGLE_CODE_DIR) not in sys.path:
        sys.path.insert(0, str(KAGGLE_CODE_DIR))
else:
    try:
        PROJECT_ROOT = Path(__file__).resolve().parents[1]
    except NameError:
        PROJECT_ROOT = _find_project_root(Path.cwd())
    DATA_PATH = PROJECT_ROOT / "data" / "Kiva_Loans.pkl"
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from src.data_loader import load_kiva_pickle, prepare_analysis_data
from src.features import extract_deterministic_features

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["font.size"] = 12

# %% [markdown]
# ## 1. Load and validate

# %%
df_raw = load_kiva_pickle(str(DATA_PATH))
prepared = prepare_analysis_data(df_raw)
valid = prepared.loc[prepared["valid_completed_outcome"]].copy()

print(f"Rows loaded: {len(prepared)}")
print(f"Rows with a valid completed outcome: {len(valid)}")
print(f"Rows excluded: {len(prepared) - len(valid)}")
print(f"Status among valid rows:\n{valid['status'].value_counts()}")

# %% [markdown]
# **Insight cell** - fill in after running: how many rows, what share
# excluded/why, and the funded/refunded split (see
# `src/run_analysis.py`'s audit trail for the exact same numbers computed
# by the production pipeline - this should match).

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.histplot(valid["funding_speed_days"], kde=True, bins=50, color="darkblue", ax=axes[0])
axes[0].set_title("Funding speed (days) - valid outcomes, full dataset")
axes[0].set_xlabel("Funding speed (days)")

sns.histplot(valid["log_funding_speed"], kde=True, bins=50, color="teal", ax=axes[1])
axes[1].set_title("log(1 + funding speed) - valid outcomes")
axes[1].set_xlabel("log(1 + funding speed in days)")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 2. Funding behavior by period

# %%
period_counts = prepared["analysis_period"].value_counts(dropna=False).sort_index()
print("Rows per analysis period:")
print(period_counts.to_string())

within_24h_by_period = valid.dropna(subset=["funded_within_24h"]).groupby(
    "analysis_period", observed=True
)["funded_within_24h"].mean()
print("\nShare funded within 24 hours, by period:")
print(within_24h_by_period.to_string())

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.boxplot(
    data=valid, x="analysis_period", y="funding_speed_days",
    hue="analysis_period", legend=False, color="steelblue", ax=axes[0],
)
axes[0].set_title("Funding speed by analysis period")
axes[0].set_ylabel("Funding speed (days)")

within_24h_by_period.astype(float).plot(kind="bar", color="darkorange", ax=axes[1])
axes[1].set_title("Share funded within 24 hours, by period")
axes[1].tick_params(axis="x", rotation=0)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 3. Narrative and structural feature distributions
#
# `extract_deterministic_features` is the same function `src/modeling.py`
# and `src/statistical_analysis.py` call - nothing here is reimplemented.
# This is the slowest cell in this notebook (regex/VADER passes over 1.45M
# descriptions); expect several minutes.

# %%
featured = extract_deterministic_features(prepared)
featured_valid = featured.loc[featured["valid_completed_outcome"]].copy()

print("region_group distribution:")
print(featured_valid["region_group"].value_counts().to_string())
print("\nsector_group distribution (threshold-based, see src/features.py):")
print(featured_valid["sector_group"].value_counts().to_string())

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.regplot(
    data=featured_valid.sample(min(50_000, len(featured_valid)), random_state=42),
    x="family_mentions_per_100_words", y="funding_speed_days",
    scatter_kws={"alpha": 0.1, "s": 8}, line_kws={"color": "purple"}, ax=axes[0],
)
axes[0].set_title("Family framing rate vs. funding speed\n(50K-row plotting sample; full data used for stats)")

sns.boxplot(
    data=featured_valid, x="loan_size_band", y="funding_speed_days",
    order=["small", "medium", "large"], hue="loan_size_band", legend=False,
    color="seagreen", ax=axes[1],
)
axes[1].set_title("Funding speed by loan-size band")
plt.tight_layout()
plt.show()

# %% [markdown]
# **Insight cell** - fill in after running: how do these full-data
# distributions compare with the 100-row sample's illustrative numbers in
# `00_starter_eda.ipynb`? Report agreement/disagreement honestly - see
# `docs/superpowers/collab-logs/2026-08-17-hackathon-upgrade-collab-log.md`
# for the local full-dataset run's already-verified findings to compare
# against.
