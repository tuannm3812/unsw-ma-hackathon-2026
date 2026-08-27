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
# # Kiva Loans: Full-Dataset Modeling (1.45M loans)
#
# This notebook builds on `1_full_dataset_eda.ipynb`'s descriptive
# groundwork with statistical models that weigh every factor at once -
# the only way to answer whether narrative framing matters once loan
# size, repayment terms, sector, region, and timing are all accounted
# for together. It answers two different questions about the same
# outcome, funding speed:
#
# - **Predictive**: how well can funding speed be forecast for a
#   newly-posted loan, using only information available at posting time?
#   Tested honestly - on loans posted in 2024-2025 that the models never
#   saw while training, not loans they've already seen the answer for.
# - **Explanatory**: which loan and narrative characteristics are linked
#   to faster or slower funding, once every other factor is held fixed?
#   This reports **association, never causation** - a link between two
#   things doesn't prove one causes the other, since borrowers weren't
#   randomly assigned a writing style, a loan amount, or a gender.
#
# **Glossary** - a quick reference for the terms used throughout:
#
# | Term | Meaning |
# |---|---|
# | MAE (mean absolute error) | On average, how many days off a prediction was. Lower is better. |
# | R² | What share of the variation in funding speed the model explains, from 0% to 100%. |
# | ROC AUC | How well a model tells apart "will fund fast" vs. "won't," from 0.5 (a coin flip) to 1.0 (perfect). |
# | Holdout set | Loans a model never saw while training - the fair way to test whether it generalizes to new loans. |
# | Coefficient | How much one factor moves funding speed up or down, holding every other factor fixed. |
# | Statistical significance (p-value) | How confident we can be that a link is real and not random noise; a very small p-value means high confidence. |
# | Reference category | The baseline group every "how much faster/slower" comparison is measured against. |
# | SHAP | A way of measuring which factors a complex model actually relied on to make its predictions. |

# %% [markdown]
# ## 1. Setup

# %%
import re
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import nltk
import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    average_precision_score,
    mean_absolute_error,
    r2_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42
HOLDOUT_START = "2024-01-01"
MIN_REGION_OBSERVATIONS = 10
MIN_SECTOR_OBSERVATIONS = 1000
SMALL_LOAN_MAX_USD = 250
MEDIUM_LOAN_MAX_USD = 750

KAGGLE_DATA_DIR = Path("/kaggle/input/datasets/tuannm3812/kiva-loans-hackathon-data")
if not KAGGLE_DATA_DIR.exists():
    KAGGLE_DATA_DIR = Path("/kaggle/input/kiva-loans-hackathon-data")

if KAGGLE_DATA_DIR.exists():
    DATA_PATH = KAGGLE_DATA_DIR / "Kiva_Loans.pkl"
else:

    def _find_project_root(start: Path) -> Path:
        candidate = start
        for _ in range(5):
            if (candidate / "data" / "Kiva_Loans_Sample.pkl").exists():
                return candidate
            if candidate.parent == candidate:
                break
            candidate = candidate.parent
        return start

    try:
        PROJECT_ROOT = Path(__file__).resolve().parents[1]
    except NameError:
        PROJECT_ROOT = _find_project_root(Path.cwd())
    DATA_PATH = PROJECT_ROOT / "data" / "Kiva_Loans.pkl"

# %% [markdown]
# ## 2. Load Data

# %%
# The pickle is a list of row dicts, not a directly-pickled DataFrame
# (pd.read_pickle would raise) - a plain stdlib pickle.load handles both
# shapes, no custom package needed.
import pickle  # noqa: E402

with open(DATA_PATH, "rb") as handle:
    _raw = pickle.load(handle)
df = pd.DataFrame(_raw) if isinstance(_raw, list) else _raw
print(f"Shape: {df.shape[0]:,} loans x {df.shape[1]} raw columns")

# %%
df.info()

# %% [markdown]
# Same 27-field dataset `1_full_dataset_eda.ipynb` explores in detail
# (see that notebook's Load Data section for a row-level preview) - 27
# raw fields, almost fully populated. The rest of this notebook engineers
# a modeling-ready feature set from these raw fields.

# %% [markdown]
# ## 3. Feature Engineering
#
# Three groups of features feed the models below: the **target**
# (funding speed itself), **structural** features describing the loan,
# and **narrative/sentiment** features describing how the loan's
# description is written.

# %% [markdown]
# ### 3.1 Target Variable
#
# Same derivation as the EDA notebook: `funding_speed_days` is the gap
# between a loan's posted and fully-funded dates, log-transformed into
# `log_funding_speed` for modeling (raw funding speed is heavily
# right-skewed - a log transform makes it easier for the regression
# models below to fit well), plus the simpler `funded_within_24h` yes/no
# version. `analysis_period` buckets each loan into pre-pandemic,
# pandemic-disruption, or post-pandemic eras by posting year, since the
# EDA notebook found funding speed shifted permanently around 2020.

# %%
fundraising = pd.to_datetime(df["fundraisingDate"], errors="coerce", utc=True)
raised = pd.to_datetime(df["raisedDate"], errors="coerce", utc=True)
df["funding_speed_days"] = (raised - fundraising).dt.total_seconds() / 86400
df["log_funding_speed"] = np.log1p(df["funding_speed_days"].clip(lower=0))
df["funded_within_24h"] = (df["funding_speed_days"] <= 1).astype(float)
df["fundraisingDate_parsed"] = fundraising

year = fundraising.dt.year
df["analysis_period"] = pd.cut(
    year, bins=[-np.inf, 2019, 2021, np.inf],
    labels=["pre_pandemic", "pandemic_disruption", "post_pandemic"],
).astype(str)

# %% [markdown]
# ### 3.2 Structural Features
#
# - **`log_loan_amount`** - the loan amount, log-transformed for the same
#   right-skew reason as the target.
# - **`loan_size_band`** - loans bucketed into small (under $250), medium
#   ($250-$750), and large (over $750) - lets the models capture
#   non-linear size effects a single continuous number might miss, and
#   gives the explanatory model in Section 7 an interpretable "small vs.
#   large" comparison.
# - **`gender_classification`** - the borrower's gender, with
#   comma-separated multi-borrower values collapsed to `"mixed"` so the
#   category set stays small and clean.
# - **`is_group_loan`** - whether more than one borrower is listed.
# - **`region_group` / `sector_group`** - region and sector collapsed so
#   that only categories with at least `MIN_REGION_OBSERVATIONS` (10) or
#   `MIN_SECTOR_OBSERVATIONS` (1,000) loans keep their own label;
#   everything else becomes `"Other"`. Sector needs a much higher
#   threshold than region because it has far more rare, thinly-populated
#   categories - without this collapsing, a category with only a handful
#   of loans could produce an unstable, misleading coefficient in
#   Section 7's regression.

# %%
df["log_loan_amount"] = np.log1p(df["loanAmount"])
df["loan_size_band"] = pd.cut(
    df["loanAmount"], bins=[-np.inf, SMALL_LOAN_MAX_USD, MEDIUM_LOAN_MAX_USD, np.inf],
    labels=["small", "medium", "large"],
).astype(str)
df["gender_classification"] = df["gender"].fillna("unknown").apply(
    lambda g: "mixed" if "," in str(g) else str(g)
)
df["is_group_loan"] = (df["borrowerCount"] > 1).astype(int)

for col, min_obs, new_col in [
    ("region", MIN_REGION_OBSERVATIONS, "region_group"),
    ("sector", MIN_SECTOR_OBSERVATIONS, "sector_group"),
]:
    counts = df[col].value_counts()
    major = counts[counts >= min_obs].index
    df[new_col] = df[col].where(df[col].isin(major), "Other")

# %% [markdown]
# ### 3.3 Narrative & Sentiment Features
#
# The same three per-100-word framing rates (family, agency, urgency) and
# VADER sentiment score the EDA notebook introduces - see that notebook's
# Narrative Framing and Sentiment Analysis sections for what each one
# measures and why. Scored on the **full** dataset here (not a sample),
# since these features feed directly into the models below.

# %%
# Raw descriptions carry stray HTML tags (mostly `<br />` line breaks) -
# stripped here so they don't inflate word counts or pollute the framing/
# sentiment features below with a spurious "word".
description = (
    df["description"].fillna("")
    .str.replace(r"<[^>]+>", " ", regex=True)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)
word_count = description.str.split().str.len().clip(lower=1)
FAMILY_PATTERN = re.compile(r"\b(child|children|family|son|daughter|mother|father|wife|husband|school)\b", re.I)
AGENCY_PATTERN = re.compile(r"\b(decide|plan|manage|responsible|hard.?working|independent|own|run|lead)\w*\b", re.I)
URGENCY_PATTERN = re.compile(r"\b(urgent|immediately|emergency|crisis|desperate|asap|quickly)\w*\b", re.I)
for name, pattern in [("family", FAMILY_PATTERN), ("agency", AGENCY_PATTERN), ("urgency", URGENCY_PATTERN)]:
    df[f"{name}_mentions_per_100_words"] = description.str.count(pattern) / word_count * 100

try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)
from nltk.sentiment.vader import SentimentIntensityAnalyzer  # noqa: E402

analyzer = SentimentIntensityAnalyzer()
df["desc_sentiment_compound"] = description.apply(lambda text: analyzer.polarity_scores(text)["compound"])

valid = df.loc[df["funding_speed_days"].notna() & (df["funding_speed_days"] >= 0)].copy()
print(f"Valid rows: {len(valid)} / {len(df)}")

# %% [markdown]
# ## 4. Data Split
#
# To know whether a model genuinely works, it has to be tested on loans
# it hasn't seen before - otherwise it could just be memorizing the data
# rather than learning a real pattern. The fairest split here is **by
# time**: train only on loans posted before 2024, then test purely on
# loans posted in 2024-2025. That mirrors how this would work in
# practice - a model only ever sees the past when asked to predict
# something new. A random shuffle-based split would be too easy on the
# model, since it could quietly learn from loans posted after the ones
# it's being tested on, which would never be possible in reality.

# %%
train_raw = valid.loc[valid["fundraisingDate_parsed"] < pd.Timestamp(HOLDOUT_START, tz="UTC")].copy()
holdout_raw = valid.loc[valid["fundraisingDate_parsed"] >= pd.Timestamp(HOLDOUT_START, tz="UTC")].copy()
print(f"Train rows: {len(train_raw)}  |  Holdout rows: {len(holdout_raw)}")

# %% [markdown]
# **1,174,953 loans** (2005-2023) train the models; **278,887 loans**
# posted in 2024-2025 - genuinely never seen during training - test them.
# That holdout group is about 19% of the whole dataset, large enough to
# trust as a real read on generalization, not a lucky handful of loans.

# %%
NUMERIC_COLS = [
    "borrowerCount", "log_loan_amount", "lenderRepaymentTerm",
    "family_mentions_per_100_words", "agency_mentions_per_100_words",
    "urgency_mentions_per_100_words", "desc_sentiment_compound", "is_group_loan",
]
CATEGORICAL_COLS = ["gender_classification", "loan_size_band", "repaymentInterval", "sector", "region", "analysis_period"]

preprocessor = ColumnTransformer([
    ("numeric", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), NUMERIC_COLS),
    ("categorical", Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ]), CATEGORICAL_COLS),
])
X_train = preprocessor.fit_transform(train_raw[NUMERIC_COLS + CATEGORICAL_COLS])
X_holdout = preprocessor.transform(holdout_raw[NUMERIC_COLS + CATEGORICAL_COLS])
y_train_log = train_raw["log_funding_speed"].to_numpy()
y_holdout_days = holdout_raw["funding_speed_days"].to_numpy()

# %% [markdown]
# ## 5. Regression Modeling
#
# Two modeling approaches, trained on the same data, compared fairly:
#
# - **Ridge** - a simple, transparent model. It assigns each factor (loan
#   amount, sector, framing style, etc.) a fixed weight and adds them up,
#   like a scorecard. Easy to trust, but can't capture "this factor
#   matters differently depending on another factor."
# - **Boosted trees (HistGradientBoosting)** - a more flexible model that
#   can learn rules like "urgency language matters more for small loans
#   than large ones." More powerful, but harder to inspect directly - the
#   Feature Importance section opens it back up.
#
# Both predict how many days a loan takes to fund, scored the same way:
# **MAE** (average days off) and **R²** (share of the real variation
# explained).

# %%
ridge = Ridge(alpha=1.0, random_state=SEED)
ridge.fit(X_train, y_train_log)
ridge_holdout_days = np.expm1(np.clip(ridge.predict(X_holdout), a_min=0, a_max=None))
print(f"Ridge holdout MAE (days): {mean_absolute_error(y_holdout_days, ridge_holdout_days):.2f}")

# %%
boosted = HistGradientBoostingRegressor(random_state=SEED)
boosted.fit(X_train.toarray() if hasattr(X_train, "toarray") else X_train, y_train_log)
X_holdout_dense = X_holdout.toarray() if hasattr(X_holdout, "toarray") else X_holdout
boosted_holdout_days = np.expm1(np.clip(boosted.predict(X_holdout_dense), a_min=0, a_max=None))
print(f"Boosted holdout MAE (days): {mean_absolute_error(y_holdout_days, boosted_holdout_days):.2f}")
print(f"Boosted holdout R2: {r2_score(y_holdout_days, boosted_holdout_days):.3f}")

# %%
plot_sample_idx = np.random.RandomState(SEED).choice(len(y_holdout_days), size=min(5_000, len(y_holdout_days)), replace=False)
plot_max = float(np.percentile(y_holdout_days, 99))

fig, ax = plt.subplots(figsize=(7, 7))
ax.scatter(
    y_holdout_days[plot_sample_idx], boosted_holdout_days[plot_sample_idx],
    alpha=0.15, s=12, color=plt.cm.viridis(0.4),
)
ax.plot([0, plot_max], [0, plot_max], color="black", linestyle="--", linewidth=1, label="Perfect prediction")
ax.set_xlim(0, plot_max)
ax.set_ylim(0, plot_max)
ax.set_xlabel("Actual funding speed (days)")
ax.set_ylabel("Predicted funding speed (days)")
ax.set_title("Predicted vs. actual funding speed (boosted model, holdout sample)")
ax.legend()
plt.tight_layout()
plt.show()

# %% [markdown]
# Tested on loans neither model had seen (2024-2025): the simple
# scorecard model (Ridge) is off by **6.76 days** on average. The more
# flexible model tightens that to **5.56 days** and explains **49.0%** of
# why funding speed varies from loan to loan (R² = 0.490) - roughly half
# the story of "why did this loan take as long as it did" can be
# explained from what's known at posting time; the rest comes down to
# things this data doesn't capture (how compelling individual lenders
# found it, timing luck, and so on). The scatter plot above shows this
# directly: points cluster along the dashed "perfect prediction" line for
# fast-funding loans, and spread out further for slower ones - the model
# is more confident and accurate on the common, fast-funding case than on
# the long tail of slow ones. The flexible model beating the scorecard by
# over a day of average accuracy is itself a finding: funding speed isn't
# a simple additive checklist - some factors matter more in combination
# than alone.

# %% [markdown]
# ## 6. Funding Classification
#
# Predicting an exact number of days is a hard, precise task. A simpler,
# more actionable version: will this loan fund within 24 hours, yes or
# no? "Flag loans unlikely to fund quickly" is a more usable signal for a
# real platform than a precise day-count guess.

# %%
y_train_binary = train_raw["funded_within_24h"].to_numpy()
y_holdout_binary = holdout_raw["funded_within_24h"].to_numpy()

classifier = HistGradientBoostingClassifier(random_state=SEED)
X_train_dense = X_train.toarray() if hasattr(X_train, "toarray") else X_train
classifier.fit(X_train_dense, y_train_binary)
holdout_proba = classifier.predict_proba(X_holdout_dense)[:, 1]

print(f"Holdout ROC AUC: {roc_auc_score(y_holdout_binary, holdout_proba):.4f}")
print(f"Holdout average precision: {average_precision_score(y_holdout_binary, holdout_proba):.4f}")

# %% [markdown]
# **ROC AUC of 0.905** out of a possible 1.0 (0.5 would mean no better
# than a coin flip) - a genuinely strong result for telling apart, before
# the fact, which loans are likely to fund fast versus drag on. That's on
# a real, never-seen holdout set, and on a task where the honest baseline
# is hard (recall from the EDA notebook: only 30-46% of loans actually
# fund within 24 hours, so simply guessing "yes" would do poorly). **This
# is the strongest practical result in the analysis**: a tool built
# purely from information available the moment a loan is posted (loan
# size, sector, region, narrative text) could reliably flag at-risk loans
# for extra visibility - independent of whether any single
# narrative-framing choice turns out to be the reason why.

# %% [markdown]
# ## 7. Explanatory Modeling
#
# Regression Modeling and Funding Classification built models that
# predict well, but a prediction machine doesn't say *why*. This section
# uses regression to measure, for every factor at once, how strongly it's
# linked to funding speed once everything else about the loan is held
# fixed - the fairest way to check whether narrative framing genuinely
# matters on its own, not just because it happens to travel alongside
# something else (like loan size). Every number here is an
# **association, never a cause** - borrowers weren't randomly assigned a
# writing style, a loan amount, or a gender. If the model can't be fit
# for a technical reason, that's reported as a clear message instead of a
# crash.

# %%
FORMULA = (
    "log_funding_speed ~ log_loan_amount + lenderRepaymentTerm + is_group_loan + "
    "C(gender_classification) + family_mentions_per_100_words + agency_mentions_per_100_words + "
    "urgency_mentions_per_100_words + desc_sentiment_compound + C(repaymentInterval) + "
    "C(sector_group) + C(region_group) + C(analysis_period) + C(loan_size_band) + "
    "family_mentions_per_100_words:C(analysis_period) + family_mentions_per_100_words:C(region_group)"
)
CATEGORICAL_TERMS = [
    "gender_classification", "repaymentInterval", "sector_group",
    "region_group", "analysis_period", "loan_size_band",
]

try:
    y, X = patsy.dmatrices(FORMULA, data=valid, return_type="dataframe")
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        duration_model = sm.OLS(y, X).fit(cov_type="HC3")
    print(duration_model.summary())
except Exception as error:  # noqa: BLE001 - reported, not crashed, matching the tested pipeline's spirit
    print(f"Duration explanatory model could not be fit: {error}")

# %% [markdown]
# Every coefficient above is relative to an omitted **reference
# category** (e.g. gender's baseline is `"female"`, the period baseline
# is `"pandemic_disruption"`) - printed explicitly below rather than left
# for a reader to infer from which levels are missing.

# %%
print("Reference (omitted) category per categorical term:")
for col in CATEGORICAL_TERMS:
    all_levels = set(valid[col].astype(str).unique())
    dummy_levels = {
        p.split("[T.")[1].rstrip("]")
        for p in duration_model.params.index
        if p.startswith(f"C({col})")
    }
    print(f"  {col}: {sorted(all_levels - dummy_levels)}")

# %% [markdown]
# Fit on all 1,453,840 valid loans (R² = 0.425, meaning this model
# explains 42.5% of why funding speed varies). With this much data, these
# are well-powered, trustworthy findings, not noisy guesses from a small
# sample. **Negative coefficients are associated with faster funding,
# positive with slower**, each compared against the reference category
# printed above.
#
# - **Urgency language** (words like "urgent," "emergency," "right now")
#   is consistently linked to **faster** funding, and the effect is not a
#   coincidence (p < 0.001) - a clean win for a simple writing choice.
# - **Agency/competence language** ("I run my own business," "I
#   manage...") shows no real link either way - the "sound capable and
#   independent" hypothesis doesn't hold up at this scale.
# - **Family/communal framing** has a small but real *slower*-funding
#   link during the pandemic-disruption period specifically (its main
#   effect, p = 0.002) - but that's dominated by much larger interaction
#   effects that flip the direction before and after: pre-pandemic, the
#   combined effect is a clear net *faster*-funding link, and
#   post-pandemic it's still net faster but less than half as strong -
#   direct, model-based confirmation of the EDA notebook's "funding
#   dynamics permanently shifted after 2020" finding. It also varies
#   sharply by region: the benefit is far larger in the Middle East and
#   Central America than in North America or Asia, where it's mildly
#   counterproductive. **Family framing helps, but who it helps and how
#   much depends heavily on when and where the loan is posted - it isn't
#   a universal lever.**
# - **Sentiment tone** shows a counterintuitive association: a more
#   positive-sounding description is linked to **slower** funding, and
#   this isn't noise either (p < 0.001). Combined with the EDA notebook's
#   finding that descriptions are almost uniformly positive already, this
#   may simply reflect that longer, more elaborately-written pitches read
#   as more positive *and* naturally take longer to write and review - an
#   association, not a reason to write flatter descriptions.
# - **Structural factors remain the largest effects by far.** The single
#   biggest swings in the whole model come from sector and region - Water
#   and Education-sector loans fund dramatically faster than
#   Agriculture-sector loans, while Clothing and Retail loans fund
#   slower, and the Middle East funds far faster than the model's
#   reference region. A loan posted under a male borrower takes notably
#   longer to fund than one posted under a female borrower - a smaller
#   effect than the biggest sector/region gaps, but larger than the loan
#   amount itself, and larger than every narrative-framing term combined.
#   Small loans fund far faster than large ones. Loans repaid as a single
#   lump sum at the end of the term are far slower to fund than loans
#   repaid irregularly or monthly.

# %% [markdown]
# ## 8. Feature Importance
#
# Explanatory Modeling's statistical model is easy to interpret, but by
# design it can only check the specific combinations it's told to look
# for (framing x period, framing x region). The boosted model from
# Regression Modeling learned whatever patterns were actually in the
# data, with no such restriction - but on its own it's a black box that
# doesn't explain itself. **SHAP** opens it back up: for every
# prediction, it works out exactly how much each factor pushed that
# prediction up or down, then averaging across many loans ranks what the
# model actually relied on - a second, independent check on the
# Explanatory Modeling findings, not a replacement for them.
#
# `shap` ships in Kaggle's standard Python image; the fallback below
# installs it on the rare environment where it's missing (this project's
# base requirements don't need it - it's notebook-only tooling). Computed
# on a random sample of 2,000 holdout loans for speed - a larger sample
# would take longer for a negligibly different ranking.

# %%
try:
    import shap
except ImportError:
    import subprocess
    import sys

    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "shap"], check=True)
    import shap

FEATURE_NAMES = preprocessor.get_feature_names_out()
shap_sample_idx = np.random.RandomState(SEED).choice(
    X_holdout_dense.shape[0], size=min(2_000, X_holdout_dense.shape[0]), replace=False
)
X_shap_sample = X_holdout_dense[shap_sample_idx]

tree_explainer = shap.TreeExplainer(boosted)
shap_values = tree_explainer.shap_values(X_shap_sample)

mean_abs_shap = pd.Series(np.abs(shap_values).mean(axis=0), index=FEATURE_NAMES).sort_values(ascending=False)
print("Top 15 features by mean |SHAP value| (2,000-row holdout sample, boosted model):")
print(mean_abs_shap.head(15).to_string())

# %%
fig, ax = plt.subplots(figsize=(9, 6))
top_15_sorted = mean_abs_shap.head(15).sort_values()
ax.barh(top_15_sorted.index, top_15_sorted.to_numpy(), color=plt.cm.viridis(np.linspace(0.15, 0.85, len(top_15_sorted))))
ax.set_xlabel("mean |SHAP value| (impact on predicted log funding speed)")
ax.set_title("Top 15 features by SHAP importance - boosted model")
plt.tight_layout()
plt.show()

# %% [markdown]
# This second, independent check **confirms the top of the Explanatory
# Modeling story**: loan amount and repayment term are, by a wide margin,
# the two factors the flexible model relied on most - both were also
# among Section 7's largest, most significant coefficients. The time
# period (pre-pandemic vs. not) and loan size also rank near the top,
# again agreeing with its
# biggest effects.
#
# **The honest divergence worth stating plainly: narrative framing barely
# registers here.** None of the family, agency, or urgency framing scores
# make it into the top 15 factors this more flexible model actually
# relied on - only overall sentiment tone cracks the list, in 11th place,
# well behind individual sector and region categories. This doesn't
# contradict the Explanatory Modeling section - urgency framing's link to
# speed, and family framing's timing/location pattern, are both
# genuinely, robustly real. But it's a useful check on what
# "statistically confident" means with 1.45 million loans: even a small,
# consistent effect becomes easy to detect with that much data. This
# check measures something different - **actual size of impact, not
# confidence that an effect is real** - and by that measure, narrative
# framing is real but genuinely minor next to how a loan is structured.

# %% [markdown]
# ## 9. Key Findings

# %% [markdown]
# ### 9.1 Technical Interpretation
#
# - A model using only posting-time information explains about half the
#   variance in funding speed (R² = 0.49, MAE 5.6 days) and discriminates
#   24-hour funding strongly (ROC AUC 0.91).
# - Urgency framing shows a consistent, statistically robust link to
#   faster funding (p < 0.001); agency framing shows none.
# - Family framing's main effect is small but statistically significant
#   (p = 0.002) - slightly slower funding during the pandemic-disruption
#   baseline period specifically - and is dominated by much larger
#   interaction effects with time period and region that flip the net
#   direction to faster before and after that period; the effect is real
#   but conditional, not flat.
# - Structural factors (loan size, repayment terms, sector, region,
#   borrower gender) have coefficients several times larger than any
#   narrative-framing term.
# - SHAP feature importance from the independently-trained boosted model
#   corroborates the same ranking: structural features dominate, and
#   narrative-framing features fall outside the top 15.

# %% [markdown]
# ### 9.2 Business Impact
#
# - **A 24-hour-funding risk flag is buildable today** - ROC AUC 0.91 is
#   strong enough to support a real "surface this loan more prominently"
#   feature, without needing any narrative-framing insight at all.
# - **Urgency language is a safe, general-purpose writing recommendation**
#   - it helps consistently, with no caveats about timing or region.
# - **Family framing needs targeted guidance, not a blanket rule** - it
#   pays off most pre-pandemic and in the Middle East/Central America,
#   and is close to neutral or counterproductive in North America/Asia.
#   A one-size-fits-all "always mention family" recommendation would be
#   wrong for a meaningful share of loans.
# - **Don't over-invest in copywriting at the expense of loan structure**
#   - loan size, repayment terms, sector, and region move funding speed
#   far more than any narrative choice. Framing is a real, secondary
#   lever worth using well, not the primary driver of funding speed.
