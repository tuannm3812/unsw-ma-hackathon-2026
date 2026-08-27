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
# # Full-Dataset Modeling (1.45M rows) - Real Findings
#
# Runs the exact same pipeline `src/run_analysis.py` does (chronological
# baseline+Ridge, nonlinear benchmark, leakage-safe binary classifier, and
# robust explanatory OLS/GLM with the sector interaction activated) against
# the real 1.45M-row competition dataset - no modeling logic is
# reimplemented here, this notebook only calls `run_analysis` directly, so
# results can never drift from what `python3 -m src.run_analysis` itself
# would produce.
#
# **This is the notebook that replaces re-running the full pipeline on a
# laptop.** It's meant to execute as a private Kaggle kernel (see
# `../scripts/push_kaggle_kernel.sh modeling` and README.md's "Kaggle
# Workflow" section) - nothing here needs a GPU (Ridge/HistGradientBoosting/
# statsmodels are all CPU-only), but the full run took ~1h37m locally, so
# expect a similar order of magnitude on Kaggle's CPU kernels.
#
# The already-verified results from the first full-dataset run (2026-08-27,
# run locally before this notebook existed) are recorded in
# `../reports/generated_full_dataset/` and
# `docs/superpowers/collab-logs/2026-08-17-hackathon-upgrade-collab-log.md`.
# Re-running here should reproduce the same numbers (Ridge/statsmodels/
# HistGradientBoosting are all seeded); use this notebook for *future*
# iterations (a new interaction, a different threshold, etc.), not to
# re-derive numbers that are already on record.

# %%
import json
import sys
from pathlib import Path


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
KAGGLE_WORKING_DIR = Path("/kaggle/working")

if KAGGLE_DATA_DIR.exists():
    DATA_PATH = KAGGLE_DATA_DIR / "Kiva_Loans.pkl"
    OUTPUT_DIR = KAGGLE_WORKING_DIR / "reports"
    if str(KAGGLE_CODE_DIR) not in sys.path:
        sys.path.insert(0, str(KAGGLE_CODE_DIR))
else:
    try:
        PROJECT_ROOT = Path(__file__).resolve().parents[1]
    except NameError:
        PROJECT_ROOT = _find_project_root(Path.cwd())
    DATA_PATH = PROJECT_ROOT / "data" / "Kiva_Loans.pkl"
    OUTPUT_DIR = PROJECT_ROOT / "reports" / "generated_full_dataset"
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from src.run_analysis import run_analysis

HOLDOUT_START = "2024-01-01"
N_TOPICS = 5
# Activates the sector interaction (opt-in by design - see
# src/statistical_analysis.py's DEFAULT_SEGMENT_INTERACTIONS comment): the
# full dataset is large enough to define "adequately represented sectors"
# (src/features.py::MIN_SECTOR_OBSERVATIONS), unlike the 100-row sample.
EXTRA_INTERACTIONS = ["family_mentions_per_100_words:C(sector_group)"]

# %% [markdown]
# ## Run the full pipeline
#
# Prints progress per stage as it goes (matches the CLI's own
# `python3 -m src.run_analysis` output) - this cell is the long-running one.

# %%
summary = run_analysis(
    str(DATA_PATH),
    str(OUTPUT_DIR),
    holdout_start=HOLDOUT_START,
    n_topics=N_TOPICS,
    extra_interactions=EXTRA_INTERACTIONS,
)

# %% [markdown]
# ## Headline results

# %%
print("=== Data audit ===")
for key in ("n_rows", "n_valid_completed_outcome", "n_excluded", "status_counts_among_valid"):
    print(f"{key}: {summary['data'][key]}")

print("\n=== Baseline / Ridge (holdout MAE, days) ===")
for name, metrics in summary["baseline_ridge"]["metrics"].items():
    print(f"{name}: train={metrics['train_mae_days']:.2f}  holdout={metrics['holdout_mae_days']:.2f}")

print("\n=== Nonlinear benchmark ===")
print(json.dumps(summary["nonlinear_benchmark"]["metrics"], indent=2))

print("\n=== 24-hour binary classifier ===")
print(json.dumps(summary["binary_classifier"]["metrics"], indent=2))

print("\n=== Explanatory models ===")
print(f"status: {summary['explanatory']['status']}")
print(f"duration_formula: {summary['explanatory']['duration_formula']}")

# %% [markdown]
# **Insight cell** - fill in after running: do these numbers match the
# already-verified 2026-08-27 local run recorded in
# `../reports/generated_full_dataset/analysis_summary.json`? They should,
# exactly, if nothing in `src/` changed - a mismatch means something in the
# pipeline or its inputs changed and needs investigating before trusting
# either run.

# %% [markdown]
# ## Outputs
#
# `run_analysis` already wrote `analysis_summary.json` and
# `association_summary.txt` to `OUTPUT_DIR` above - on Kaggle that's
# `/kaggle/working/reports/`, which Kaggle automatically offers for
# download from the kernel's Output tab after the run finishes.

# %%
print(f"Reports written to: {OUTPUT_DIR}")
for path in sorted(OUTPUT_DIR.glob("*")):
    print(f"  {path.name} ({path.stat().st_size} bytes)")
