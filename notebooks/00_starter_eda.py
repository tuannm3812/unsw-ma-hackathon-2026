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
# # UNSW Marketing Analytics Hackathon 2026 - Preliminary Evidence Notebook
#
# Every number below comes from the tested `src/` pipeline, called directly
# - no modeling or feature logic is reimplemented here.
#
# **Sample data - preliminary only.** This notebook runs on
# `data/Kiva_Loans_Sample.pkl`, a **100-row illustrative sample**, not the
# full competition dataset - treat every figure below as a pipeline
# demonstration, not final managerial evidence. **For the real, full-dataset
# findings (1.45M rows), see `01_full_dataset_eda.ipynb` and
# `02_full_dataset_modeling.ipynb`** - those, not this notebook, back the
# final presentation's numbers.

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
# them, and lenders self-select which loans to fund. Every statistical
# result below is reported as "associated with," holding other modeled
# predictors fixed - never as "causes," "drives," or "proves."

# %%
import sys
from pathlib import Path

import matplotlib.pyplot as plt
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


KAGGLE_DATA_DIR = Path("/kaggle/input/kiva-loans-hackathon-data")
KAGGLE_CODE_DIR = Path("/kaggle/input/kiva-hackathon-src")

if KAGGLE_DATA_DIR.exists():
    # Running as a Kaggle kernel (see ../scripts/push_kaggle_kernel.sh and
    # README.md's "Kaggle Workflow" section): both private datasets are
    # mounted read-only under /kaggle/input/.
    DATA_PATH = KAGGLE_DATA_DIR / "Kiva_Loans_Sample.pkl"
    REPORTS_DIR = Path("/kaggle/working/reports")
    if str(KAGGLE_CODE_DIR) not in sys.path:
        sys.path.insert(0, str(KAGGLE_CODE_DIR))
else:
    try:
        # Running as a plain script: `__file__` is notebooks/00_starter_eda.py.
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
from src.binary_modeling import evaluate_chronological_binary_classifier
from src.data_loader import load_kiva_pickle, prepare_analysis_data
from src.features import extract_deterministic_features
from src.modeling import run_baseline_model
from src.run_analysis import run_analysis
from src.statistical_analysis import fit_explanatory_models
from src.topics import extract_topics_nmf

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["font.size"] = 12

# %% [markdown]
# ## 2. Dataset Overview
#
# [Kiva](https://www.kiva.org) is a nonprofit microfinance platform:
# individual lenders fund small loans to borrowers around the world,
# usually to grow a small business or cover a household need. Each row
# below is one loan; the fields shown are exactly as provided by the
# sample export, before any feature engineering.

# %%
df_raw = load_kiva_pickle(str(DATA_PATH))
print(f"Shape: {df_raw.shape[0]} loans x {df_raw.shape[1]} raw columns")

schema = pd.DataFrame({
    "dtype": df_raw.dtypes.astype(str),
    "non_null": df_raw.count(),
    "missing": df_raw.isna().sum(),
})
schema

# %%
# Deliberately excludes borrower identifiers (name, id, image_url) *and*
# free-text/exact-timestamp fields that can still identify a real borrower
# even without the name column: raw `description`/`use`/`whySpecial` text
# usually opens with the borrower's name and a short personal biography
# (Kiva's own narrative convention), and an exact `fundraisingDate`/
# `raisedDate` timestamp is specific enough to cross-reference a real loan
# on Kiva's own public site. This project analyzes aggregate narrative/
# structural patterns, never individual borrowers - a public-facing
# preview should not redistribute identifiable rows just because the
# source platform happens to show them.
preview_cols = [
    "gender", "borrowerCount", "loanAmount", "sector", "activity",
    "region", "country_name", "repaymentInterval",
]
df_raw[preview_cols].head(5)

# %% [markdown]
# **Insight:** each row is one loan with borrower/loan attributes (amount,
# sector, region, repayment terms). Two more field groups exist but are
# not shown per-row above for the reason noted in the code comment: a
# free-text `description`/`use`/`whySpecial` narrative (illustrative
# opening only, not an actual row - *"Maria is a hardworking
# small-business owner who has run her grocery store for five years and
# is requesting a loan to buy more stock."*), and two key dates -
# `fundraisingDate` (posted) and `raisedDate` (fully funded) - whose
# difference *is* the funding-speed outcome this project models. No
# column is missing more than 6 of 100 rows (`latitude`/`longitude`);
# every derived feature used from here on (Section 5 onward) comes from
# these raw columns, none newly fetched.

# %% [markdown]
# ## 3. Data validity and outcome distribution
#
# `prepare_analysis_data` derives the funding-speed target and flags outcome
# validity; an invalid/missing duration is excluded, never imputed.

# %%
prepared = prepare_analysis_data(df_raw)
valid = prepared.loc[prepared["valid_completed_outcome"]].copy()

n_rows = len(prepared)
n_valid = int(valid.shape[0])
speed_stats = valid["funding_speed_days"].describe()

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
# **Insight:** all 100 sample rows have a valid, complete funding outcome
# (no exclusions). Funding speed is heavily right-skewed - median 2.6 days,
# but a mean of 8.1 days and a few loans taking up to 35 days - motivating
# the log(1 + days) transform used throughout the modeling
# pipeline (right panel).

# %% [markdown]
# ## 4. Funding behavior by period
#
# `analysis_period` buckets each loan's posting year into `pre_pandemic`
# (<=2019), `pandemic_disruption` (2020-2021), or `post_pandemic` (2022+) -
# the project's primary temporal lens.

# %%
period_counts = prepared["analysis_period"].value_counts(dropna=False).sort_index()

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

# %% [markdown]
# **Insight:** loans are reasonably distributed across the three periods
# (40 pre-pandemic, 17 pandemic-disruption, 43 post-pandemic). The share
# funded within 24 hours is highest pre-pandemic (50%) and lower in both
# the pandemic-disruption (29%) and post-pandemic periods (35%) - a
# descriptive hint of the evolutionary comparison formalized in Section 8.

# %% [markdown]
# ## 5. Controllable narrative versus structural predictors
#
# `extract_deterministic_features` computes two families of predictors
# without fitting anything across rows:
#
# - **Controllable narrative** - framing rates per 100 words (family,
#   agency, urgency, ...), description length, sentiment.
# - **Structural** - largely fixed by the loan itself: loan amount, term,
#   sector, region, group status, gender classification (a missing value is
#   `"unknown"`, never assumed to be female).

# %%
featured = extract_deterministic_features(prepared)
featured_valid = featured.loc[featured["valid_completed_outcome"]].copy()

gender_counts = featured["gender_classification"].value_counts(dropna=False)
group_counts = featured["is_group_loan"].value_counts().rename({0: "individual", 1: "group"})

narrative_cols = [
    "family_mentions_per_100_words",
    "agency_mentions_per_100_words",
    "urgency_mentions_per_100_words",
    "desc_sentiment_compound",
    "desc_word_count",
]
structural_cols = ["log_loan_amount", "lenderRepaymentTerm"]
corr_table = featured_valid[narrative_cols + structural_cols + ["funding_speed_days"]].corr()[
    "funding_speed_days"
].drop("funding_speed_days")

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
# **Insight:** simple bivariate correlations with funding speed are
# dominated by structural factors - loan amount (r=0.58) and repayment
# term (r=0.36) - while every narrative framing measure correlates weakly
# (|r| ≤ 0.16). This is exactly why Section 8's multivariate model holds
# structural predictors fixed before assessing narrative associations. The
# borrower sample also skews heavily female (86 vs. 14 male) - a real
# limitation for any gender-segmented claim.

# %% [markdown]
# ### 5.1 Descriptive topic exploration (full-sample, exploratory only)
#
# `extract_topics_nmf` is a **full-sample exploratory convenience function -
# not for leakage-safe evaluation**. Safe to use here purely to describe
# recurring narrative themes; the leakage-safe evaluation in Section 7 fits
# its own topic model on the training partition only.

# %%
df_topics, topic_keywords = extract_topics_nmf(prepared, n_topics=N_TOPICS)
df_topics_valid = df_topics.loc[df_topics["valid_completed_outcome"]]

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
# **Insight:** five recurring themes emerge - general everyday needs/savings,
# business plus school/children, sanitation (a toilet-specific sub-theme),
# farming/agriculture, and an NWTF-affiliated business-loan cluster (see
# x-axis labels above). Descriptive only; no topic stands out as
# systematically faster- or slower-funded at this sample size.

# %% [markdown]
# ## 6. Pre-specified period and segment comparisons
#
# `src/statistical_analysis.py` pre-specifies three default interactions -
# family framing × analysis period, × region group (a fixed
# observation-count threshold, not a hardcoded region list - see
# `src/features.py`), and × loan-size band. Looking at the period one
# descriptively here, before the robust model in Section 8, keeps it a
# **pre-specified** comparison rather than post-hoc data dredging.

# %%
family_by_period = featured_valid.groupby("analysis_period", observed=True)[
    "family_mentions_per_100_words"
].agg(["mean", "median", "count"])

speed_by_period_gender = featured_valid.groupby(
    ["analysis_period", "gender_classification"], observed=True
)["funding_speed_days"].median().unstack("gender_classification")

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
# **Insight:** family/communal framing declines somewhat over time (mean
# 3.10 → 2.73 → 2.27 mentions per 100 words, pre- to
# post-pandemic) - the raw material for Section 8's formal interaction
# test. Median funding speed by period×gender is noisy at this
# sample size (e.g. only one male loan in the pandemic-disruption period),
# underscoring why the formal model controls for structure rather than
# reading these small cells directly.

# %% [markdown]
# ## 7. Chronological evaluation results
#
# The primary predictive evaluation design is **chronological, not
# random**: `run_baseline_model` trains on loans posted before
# `HOLDOUT_START` and evaluates on loans posted on or after it, mirroring
# real deployment. All learned preprocessing is fit on the training
# partition only.

# %%
baseline_results = run_baseline_model(str(DATA_PATH), holdout_start=HOLDOUT_START, n_topics=N_TOPICS)
metrics_table = pd.DataFrame(baseline_results["metrics"]).T

# %% [markdown]
# **Insight:** on an 80/20 chronological split, the training-median
# baseline reaches a 9.0-day holdout MAE. Ridge overfits sharply at this
# sample size (training R²=0.87 collapses to holdout R²=-12.2) -
# expected with ~115 encoded features against only 80 training rows, and
# the reason the nonlinear benchmark below is weighted more heavily than
# Ridge's holdout number.

# %% [markdown]
# ### 7.1 Nonlinear benchmark
#
# `evaluate_boosted_model` reuses the exact same chronological split and
# preprocessing pipeline, fitting a `HistGradientBoostingRegressor` instead
# of `Ridge`, so its holdout metrics are directly comparable to the ones
# above.

# %%
boosted_results = evaluate_boosted_model(df_raw, holdout_start=HOLDOUT_START, n_topics=N_TOPICS)

# %% [markdown]
# **Insight:** the gradient-boosted benchmark clearly outperforms both
# baselines (6.1-day holdout MAE, R²=0.39). Loan amount is the top
# permutation-important feature, followed by narrative/structural features
# like third-person mentions and repayment term - but with only 20 holdout
# rows, treat this ranking as illustrative, not a stable feature-importance
# estimate. Re-run on the full dataset before comparing models for a
# production decision.

# %% [markdown]
# ### 7.2 24-hour funding classifier
#
# `evaluate_chronological_binary_classifier` reuses the same chronological
# split/preprocessing as the two benchmarks above, fitting a
# `HistGradientBoostingClassifier` for `funded_within_24h` and reporting
# ROC AUC, average precision (AP), and Brier score on the untouched holdout
# - the design spec's predictive-evaluation requirement for the binary
# outcome (distinct from Section 8's *explanatory* GLM, which answers a
# different question and cannot be fit at all on this sample). AP, not the
# trapezoidal PR-AUC, is reported: the two are related but numerically
# different (see `src/binary_modeling.py`'s docstring).

# %%
binary_results = evaluate_chronological_binary_classifier(df_raw, holdout_start=HOLDOUT_START, n_topics=N_TOPICS)

# %% [markdown]
# **Insight:** the classifier discriminates well on this sample (holdout
# ROC AUC 0.88, average precision 0.79, Brier score 0.17) despite a modest
# 20-row holdout (7 funded-within-24h, 13 not) - treat as illustrative of
# the pipeline, not a stable estimate, for the same small-sample reason as
# every other predictive metric in this notebook.

# %% [markdown]
# ## 8. Robust explanatory associations
#
# `fit_explanatory_models` fits two independent, robust (HC3
# heteroskedasticity-consistent) explanatory models on every valid
# observation - a duration OLS on `log_funding_speed` and a binomial GLM on
# `funded_within_24h` - using only rows with a valid outcome (never
# imputed). Each model is fit **independently**, so one failing does not
# discard the other.

# %%
explanatory_results = fit_explanatory_models(df_raw)

# %% [markdown]
# **Insight:** the duration model fits without issue (n=100); none of the
# three pre-specified family-framing interactions (period, region group,
# loan-size band) are distinguishable from zero at this sample size, and
# only loan amount approaches significance (β=0.79, p=0.11) among all
# predictors - expected at n=100, not evidence of no effect. As
# anticipated, the 24-hour binary model hits quasi-complete separation
# (100 observations vs. 34 design columns) and correctly reports a
# diagnostic instead of an unstable estimate - the graceful-degradation
# behavior the design spec requires. Full coefficient-level detail is
# written to `reports/generated/association_summary.txt` by the next cell.

# %% [markdown]
# ## 9. Ethical, managerial interpretation and limitations
#
# **Reading the association results responsibly.**
# - Every coefficient above describes an *association*, holding other
#   modeled predictors fixed - never a causal claim. Borrowers were not
#   randomly assigned a narrative framing, loan amount, or gender
#   composition, so none of these results license a statement like
#   "writing more family-framed descriptions will speed up funding."
# - `gender_classification` never assumes a missing value means female;
#   treating a marketing lever as "target female-presenting borrowers with
#   framing X" from an association alone would risk reinforcing exactly the
#   kind of gender-based targeting this project's design deliberately
#   avoids assuming.
# - A shifting narrative×period association would still just be
#   that - an association that differs by period, not evidence that the
#   pandemic *caused* a change in how framing works.
#
# **Limitations of this run.**
# 1. **Sample size.** ~100 rows is enough to exercise every pipeline stage
#    end-to-end, but far too few to treat any metric, coefficient, or plot
#    above as a stable estimate - especially the chronological holdout (20
#    rows) and the 24-hour binary model (which could not be reliably fit).
# 2. **No causal identification.** An A/B test or quasi-experimental design
#    would be required before recommending a specific narrative change.
# 3. **Not the final deliverable.** Only a re-run against the full
#    competition dataset should inform actual managerial decisions.
#
# The cell below reproduces the full pipeline end-to-end via `run_analysis`
# on the 100-row sample, writing an auditable JSON summary and a plain-text
# association report to `reports/generated/` - the same entry point that
# should be re-pointed at the full competition dataset later.

# %%
full_summary = run_analysis(
    str(DATA_PATH), str(REPORTS_DIR), holdout_start=HOLDOUT_START, n_topics=N_TOPICS
)
