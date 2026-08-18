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
# # UNSW Marketing Analytics Hackathon 2026 - Auditable Evidence Notebook
#
# This notebook is a thin, readable consumer of the leakage-safe, tested
# pipeline in `src/` (Tasks 1-7). It does not re-implement any modeling,
# feature-engineering, or statistical logic itself - every number below
# comes from calling a `src` function exactly as it is documented and
# unit-tested. If a number here looks wrong, the fix belongs in `src/` and
# its tests, not in this notebook.
#
# **SAMPLE DATA WARNING - READ FIRST**
# This notebook runs against `data/Kiva_Loans_Sample.pkl`, a **100-row
# illustrative sample**, not the full competition dataset. Every figure,
# metric, and coefficient produced below exists to demonstrate that the
# pipeline runs end-to-end and to sanity-check its output - **it is not
# final evidence** for any marketing decision. The same pipeline should be
# re-run against the full competition dataset (via `src/run_analysis.py`)
# before drawing conclusions that inform real decisions.

# %% [markdown]
# ## 1. Research question and association caveat
#
# **Research question:** Within this subsistence-marketplace lending
# context, which controllable narrative choices (how a borrower's loan
# description is framed) and structural factors (loan size, term, sector,
# region, borrower gender/group structure) are **associated with** how
# quickly a Kiva loan gets funded - and does that association look
# different across the pre-pandemic, pandemic-disruption, and
# post-pandemic periods?
#
# **Association, not causation.** Loans are not randomly assigned a
# narrative framing or a loan amount; borrowers and field partners choose
# them, and lenders self-select which loans to fund. Nothing in this
# notebook (or in `src/statistical_analysis.py`, which it calls) supports a
# causal claim. Every statistical result is reported as "associated with,"
# holding the other modeled predictors fixed - never as "causes," "drives,"
# "improves," or "proves."

# %%
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def _find_project_root(start: Path) -> Path:
    """
    Walk upward from `start` (at most a few levels) until a directory that
    looks like the repository root is found - one containing both a `src/`
    package and `data/Kiva_Loans_Sample.pkl`. Falls back to `start` if
    nothing is found, so the later `load_kiva_pickle` call raises a clear
    `FileNotFoundError` instead of this helper silently guessing wrong.
    """
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


try:
    # Running as a plain script: `__file__` is notebooks/starter_eda.py.
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
except NameError:
    # Running as a notebook: there is no `__file__`. Jupyter/nbconvert
    # typically execute with cwd set to the notebook's own directory
    # (notebooks/), but this also tolerates being launched from the
    # repository root, so search upward rather than assuming either.
    PROJECT_ROOT = _find_project_root(Path.cwd())

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATA_PATH = PROJECT_ROOT / "data" / "Kiva_Loans_Sample.pkl"
REPORTS_DIR = PROJECT_ROOT / "reports" / "generated"
HOLDOUT_START = "2024-01-01"
N_TOPICS = 5

from src.advanced_modeling import evaluate_boosted_model
from src.data_loader import load_kiva_pickle, prepare_analysis_data
from src.features import extract_deterministic_features
from src.modeling import run_baseline_model
from src.run_analysis import run_analysis
from src.statistical_analysis import fit_explanatory_models, format_association_summary
from src.topics import extract_topics_nmf

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["font.size"] = 12

print(f"Project root resolved to: {PROJECT_ROOT}")
print(f"Loading sample data from: {DATA_PATH}")
print(
    "Reminder: data/Kiva_Loans_Sample.pkl is a 100-row SAMPLE used to "
    "exercise this pipeline - not the full competition dataset."
)

# %% [markdown]
# ## 2. Data validity and outcome distribution
#
# `prepare_analysis_data` parses `fundraisingDate`/`raisedDate`, derives the
# target (`funding_speed_days`), and flags every row's outcome validity. A
# missing or negative duration is **never imputed** - such rows are excluded
# from any speed-based analysis and their exclusion reason is recorded in
# `outcome_issue`, so readers can audit exactly what was dropped and why.

# %%
df_raw = load_kiva_pickle(str(DATA_PATH))
prepared = prepare_analysis_data(df_raw)

n_rows = len(prepared)
n_valid = int(prepared["valid_completed_outcome"].sum())
print(f"Rows loaded: {n_rows} (sample file, not the full competition dataset)")
print(f"Rows with a valid completed outcome: {n_valid}")
print(f"Rows excluded (missing/negative duration, never imputed): {n_rows - n_valid}")

exclusion_counts = (
    prepared.loc[~prepared["valid_completed_outcome"], "outcome_issue"]
    .value_counts()
)
if len(exclusion_counts):
    print("\nExclusion reasons:")
    print(exclusion_counts.to_string())
else:
    print("\nNo excluded rows in this sample.")

valid = prepared.loc[prepared["valid_completed_outcome"]].copy()

print("\nFunding speed (days) summary statistics, valid outcomes only:")
print(valid["funding_speed_days"].describe())

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.histplot(valid["funding_speed_days"], kde=True, bins=20, color="darkblue", ax=axes[0])
axes[0].set_title("Funding speed (days) - valid outcomes")
axes[0].set_xlabel("Funding speed (days)")

sns.histplot(valid["log_funding_speed"], kde=True, bins=20, color="teal", ax=axes[1])
axes[1].set_title("log(1 + funding speed) - valid outcomes")
axes[1].set_xlabel("log(1 + funding speed in days)")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 3. Funding behavior by period
#
# `analysis_period` (from `prepare_analysis_data`) buckets each loan's
# posting year into `pre_pandemic` (<=2019), `pandemic_disruption`
# (2020-2021), or `post_pandemic` (2022+). This is the project's primary
# temporal lens for an evolutionary perspective on funding behavior.

# %%
period_counts = prepared["analysis_period"].value_counts(dropna=False).sort_index()
print("Rows per analysis period (all rows, including excluded outcomes):")
print(period_counts.to_string())

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

sns.boxplot(
    data=valid, x="analysis_period", y="funding_speed_days",
    hue="analysis_period", legend=False, color="steelblue", ax=axes[0],
)
axes[0].set_title("Funding speed by analysis period (valid outcomes)")
axes[0].set_xlabel("Analysis period")
axes[0].set_ylabel("Funding speed (days)")

within_24h_by_period = valid.dropna(subset=["funded_within_24h"]).groupby(
    "analysis_period", observed=True
)["funded_within_24h"].mean()
within_24h_by_period.astype(float).plot(kind="bar", color="darkorange", ax=axes[1])
axes[1].set_title("Share funded within 24 hours, by period")
axes[1].set_xlabel("Analysis period")
axes[1].set_ylabel("Share funded within 24h")
axes[1].tick_params(axis="x", rotation=0)

plt.tight_layout()
plt.show()

print("\nShare funded within 24 hours, by period (valid outcomes only):")
print(within_24h_by_period.to_string())

# %% [markdown]
# ## 4. Controllable narrative versus structural predictors
#
# `extract_deterministic_features` computes two broad families of
# predictors, without fitting anything across rows (safe to call on any
# subset, including a holdout):
#
# - **Controllable narrative features** - choices a borrower/field partner
#   can make when writing a loan description: framing rates per 100 words
#   (`family_mentions_per_100_words`, `agency_mentions_per_100_words`,
#   `urgency_mentions_per_100_words`, and others), description length, and
#   sentiment (`desc_sentiment_compound`).
# - **Structural predictors** - largely fixed by the loan itself:
#   `log_loan_amount`, `lenderRepaymentTerm`, `sector`, `region`,
#   `is_group_loan`, and `gender_classification` (never assumes a missing
#   value means female - missing values are `"unknown"`).

# %%
featured = extract_deterministic_features(prepared)
featured_valid = featured.loc[featured["valid_completed_outcome"]].copy()

print("Gender classification counts (never assumes missing = female):")
print(featured["gender_classification"].value_counts(dropna=False).to_string())

print("\nGroup vs. individual loans:")
print(featured["is_group_loan"].value_counts().rename({0: "individual", 1: "group"}).to_string())

narrative_cols = [
    "family_mentions_per_100_words",
    "agency_mentions_per_100_words",
    "urgency_mentions_per_100_words",
    "desc_sentiment_compound",
    "desc_word_count",
]
structural_cols = ["log_loan_amount", "lenderRepaymentTerm"]

print("\nCorrelation with funding speed (days), valid outcomes only:")
corr_table = featured_valid[narrative_cols + structural_cols + ["funding_speed_days"]].corr()[
    "funding_speed_days"
].drop("funding_speed_days")
print(corr_table.sort_values().to_string())

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

sns.regplot(
    data=featured_valid, x="family_mentions_per_100_words", y="funding_speed_days",
    scatter_kws={"alpha": 0.6}, line_kws={"color": "purple"}, ax=axes[0],
)
axes[0].set_title("Family framing rate vs. funding speed\n(narrative, controllable)")
axes[0].set_xlabel("Family mentions per 100 words")
axes[0].set_ylabel("Funding speed (days)")

sns.boxplot(
    data=featured_valid, x="loan_size_band", y="funding_speed_days",
    order=["small", "medium", "large"], hue="loan_size_band", legend=False,
    color="seagreen", ax=axes[1],
)
axes[1].set_title("Funding speed by loan-size band\n(structural, largely fixed)")
axes[1].set_xlabel("Loan size band")
axes[1].set_ylabel("Funding speed (days)")

plt.tight_layout()
plt.show()

# %% [markdown]
# ### 4.1 Descriptive topic exploration (full-sample, exploratory only)
#
# `extract_topics_nmf` in `src/topics.py` is explicitly documented as a
# **full-sample exploratory convenience function - not for leakage-safe
# evaluation**. It is safe to use here purely to describe recurring themes
# in the loan descriptions, since the results below are never used to
# evaluate held-out predictions - the leakage-safe evaluation in Section 6
# fits its own topic model on the training partition only.

# %%
df_topics, topic_keywords = extract_topics_nmf(prepared, n_topics=N_TOPICS)
df_topics_valid = df_topics.loc[df_topics["valid_completed_outcome"]]

for idx, words in topic_keywords.items():
    print(f"Topic {idx} top words: {', '.join(words[:6])}")

plt.figure(figsize=(10, 6))
topic_labels = [f"Topic {i}\n({', '.join(words[:3])})" for i, words in topic_keywords.items()]
sns.boxplot(
    data=df_topics_valid, x="dominant_topic", y="funding_speed_days",
    hue="dominant_topic", legend=False, palette="Set3",
)
plt.xticks(ticks=range(N_TOPICS), labels=topic_labels, rotation=30, ha="right")
plt.title("Funding speed by dominant description topic (descriptive, full-sample exploratory)")
plt.xlabel("Dominant topic")
plt.ylabel("Funding speed (days)")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 5. Pre-specified period and segment comparisons
#
# `src/statistical_analysis.py` pre-specifies exactly one interaction as
# the project's evolutionary-perspective comparison:
# `family_mentions_per_100_words : C(analysis_period)` - does the
# association between family/communal framing and the outcome differ across
# periods? Looking at it descriptively here, before the robust model in
# Section 7, keeps this a **pre-specified** comparison rather than post-hoc
# data dredging.

# %%
family_by_period = featured_valid.groupby("analysis_period", observed=True)[
    "family_mentions_per_100_words"
].agg(["mean", "median", "count"])
print("Family framing rate by analysis period (pre-specified comparison):")
print(family_by_period.to_string())

speed_by_period_gender = featured_valid.groupby(
    ["analysis_period", "gender_classification"], observed=True
)["funding_speed_days"].median().unstack("gender_classification")
print("\nMedian funding speed (days) by period x gender classification (segment view):")
print(speed_by_period_gender.to_string())

# %%
plt.figure()
sns.lineplot(
    data=family_by_period.reset_index(), x="analysis_period", y="mean",
    marker="o", sort=False,
)
plt.title("Mean family framing rate across periods\n(pre-specified evolutionary comparison)")
plt.xlabel("Analysis period")
plt.ylabel("Mean family mentions per 100 words")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 6. Chronological evaluation results
#
# The primary predictive evaluation design in this project is
# **chronological**, not a random split: `run_baseline_model` trains on
# loans posted before `HOLDOUT_START` and evaluates on loans posted on or
# after it, mirroring how a model would actually be used to score
# newly-posted loans. All learned preprocessing (imputation, scaling,
# one-hot encoding, and the training-fitted topic model) comes from
# `src/modeling.py` and is fit on the training partition only.

# %%
baseline_results = run_baseline_model(str(DATA_PATH), holdout_start=HOLDOUT_START, n_topics=N_TOPICS)

metrics_table = pd.DataFrame(baseline_results["metrics"]).T
print(f"\nChronological split ({HOLDOUT_START} boundary) on the 100-row sample:")
print(f"Train rows: {baseline_results['train_rows']}  |  Holdout rows: {baseline_results['holdout_rows']}")
print("\nBaseline (training-median) vs. Ridge, in day space:")
print(metrics_table[["train_mae_days", "holdout_mae_days", "holdout_r2"]])

# %% [markdown]
# ### 6.1 Nonlinear benchmark
#
# `evaluate_boosted_model` (Task 6) reuses the exact same chronological
# split and preprocessing pipeline, fitting a `HistGradientBoostingRegressor`
# instead of `Ridge`, so its holdout metrics are directly comparable to the
# ones above.

# %%
boosted_results = evaluate_boosted_model(df_raw, holdout_start=HOLDOUT_START, n_topics=N_TOPICS)
print("Boosted (HistGradientBoostingRegressor) holdout metrics:")
for name, value in boosted_results["metrics"].items():
    print(f"  {name}: {value:.4f}")

print("\nTop permutation importances (holdout, day-space MAE):")
print(boosted_results["importance"].head(10).to_string(index=False))

print(
    f"\nWith only {baseline_results['holdout_rows']} holdout rows on this sample, "
    "these metrics are illustrative of the pipeline, not a reliable estimate of "
    "real-world predictive accuracy - re-run on the full competition dataset "
    "before comparing models for a production decision."
)

# %% [markdown]
# ## 7. Robust explanatory associations
#
# `fit_explanatory_models` fits two independent, robust (HC3
# heteroskedasticity-consistent standard errors) explanatory models on every
# valid observation - a duration OLS on `log_funding_speed` and a binomial
# GLM on `funded_within_24h` - using only rows with a valid outcome (never
# imputed). Each model is fit **independently**: on this 100-row sample, the
# 24-hour binary model is expected to fail with a quasi-complete-separation
# diagnostic (too little data for its categorical parameters), while the
# duration model fits fine. That is expected behavior, not a bug - the
# function returns a clear diagnostic string instead of unreliable
# coefficients.

# %%
explanatory_results = fit_explanatory_models(df_raw)
association_summary = format_association_summary(explanatory_results)
print(association_summary)

# %% [markdown]
# ## 8. Ethical, managerial interpretation and limitations
#
# **Reading the association results responsibly.**
# - Every coefficient above describes an *association*, holding the other
#   modeled predictors fixed - never a causal claim. Borrowers were not
#   randomly assigned a narrative framing, loan amount, or gender
#   composition, so none of these results license a statement like
#   "writing more family-framed descriptions will speed up funding."
# - `gender_classification` never assumes a missing value means female;
#   treating a marketing lever as "target female-presenting borrowers with
#   framing X" from an association alone would risk reinforcing exactly the
#   kind of gender-based targeting this project's design deliberately
#   avoids assuming.
# - The pre-specified `family_mentions_per_100_words : analysis_period`
#   interaction is the project's evolutionary-perspective test: whether a
#   narrative association looks stable or shifts across the pandemic
#   periods. A shifting association is still just that - an association
#   that differs by period, not evidence that the pandemic *caused* a
#   change in how framing works.
#
# **Limitations of this run.**
# 1. **Sample size.** `data/Kiva_Loans_Sample.pkl` has about 100 rows. That
#    is enough to exercise every stage of this pipeline end-to-end, but far
#    too few to treat any single metric, coefficient, or plot above as a
#    stable estimate - especially the chronological holdout (a double-digit
#    number of holdout rows) and the 24-hour binary model (which could not
#    be reliably fit here at all).
# 2. **No causal identification.** Nothing in this notebook - or in
#    `src/statistical_analysis.py` - estimates a causal effect. A/B tests or
#    a quasi-experimental design would be required before recommending a
#    specific narrative change to field partners.
# 3. **This notebook's numbers are not the final deliverable.** The
#    reproducible pipeline exists precisely so the same analysis can be
#    re-run, unchanged, against the full competition dataset - only that run
#    should inform actual managerial decisions.
#
# The cell below runs that same reproducible pipeline (`run_analysis`, Task
# 7) end-to-end on the 100-row sample one more time, writing an auditable
# JSON summary and a plain-text association report to `reports/generated/`.
# This is the same entry point that should be re-pointed at the full
# competition dataset later.

# %%
full_summary = run_analysis(
    str(DATA_PATH), str(REPORTS_DIR), holdout_start=HOLDOUT_START, n_topics=N_TOPICS
)
print(f"\nWrote auditable reports to: {REPORTS_DIR}")
print(f"Rows in this run: {full_summary['data']['n_rows']} (sample - see Section 1 caveat)")
print(f"Date range covered: {full_summary['data']['date_min']} to {full_summary['data']['date_max']}")
print(
    "\nFINAL REMINDER: all results in this notebook come from the 100-row "
    "sample file and are for pipeline demonstration only, not final "
    "managerial evidence. Re-run against the full competition dataset before "
    "acting on any finding above."
)
