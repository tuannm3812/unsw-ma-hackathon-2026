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
#   This reports association, never causation - a link between two
#   things doesn't prove one causes the other (see README.md's Known
#   Limitations).
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
#
# Uses only standard public packages (pandas, numpy, scikit-learn,
# statsmodels, patsy, nltk, shap) - a deliberately simpler, streamlined
# re-implementation of the same design as the project's tested internal
# pipeline (a fair, chronological train/test split; statistically robust,
# association-only language), not a port of its exact code.
# `../reports/generated_full_dataset/` is the authoritative source for
# the final presentation's numbers.

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

# %% [markdown]
# ## 3. Feature Engineering
#
# Same target and narrative features as `1_full_dataset_eda.ipynb` -
# funding speed derived from the posted/funded dates, three theory-guided
# framing rates (family, agency, urgency), and VADER sentiment - plus a
# few structural features this notebook's models need: loan size bands,
# a group-vs-individual flag, and region/sector collapsed to a fixed
# observation-count threshold (rare categories folded into "Other" so
# they don't destabilize the models).

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

# %%
df["log_loan_amount"] = np.log1p(df["loanAmount"])
df["loan_size_band"] = pd.cut(
    df["loanAmount"], bins=[-np.inf, 250, 750, np.inf], labels=["small", "medium", "large"]
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

# %%
description = df["description"].fillna("")
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
# ## 4. Train/Test Split
#
# To know whether a model genuinely works, it has to be tested on loans
# it hasn't seen before - otherwise it could just be memorizing the data
# rather than learning a real pattern. The fairest split here is by time:
# train only on loans posted before 2024, then test purely on loans
# posted in 2024-2025. That mirrors how this would work in practice - a
# model only ever sees the past when asked to predict something new. A
# random shuffle-based split would be too easy on the model, since it
# could quietly learn from loans posted after the ones it's being tested
# on, which would never be possible in reality.

# %%
train_raw = valid.loc[valid["fundraisingDate_parsed"] < pd.Timestamp(HOLDOUT_START, tz="UTC")].copy()
holdout_raw = valid.loc[valid["fundraisingDate_parsed"] >= pd.Timestamp(HOLDOUT_START, tz="UTC")].copy()
print(f"Train rows: {len(train_raw)}  |  Holdout rows: {len(holdout_raw)}")

# %% [markdown]
# 1,174,953 loans (2005-2023) train the models; 278,887 loans posted in
# 2024-2025 - genuinely never seen during training - test them. That
# holdout group is about 19% of the whole dataset, large enough to trust
# as a real read on generalization, not a lucky handful of loans.

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
# ## 5. Predictive Modeling: Funding Speed (Regression)
#
# Two modeling approaches, trained on the same data, compared fairly:
#
# - **Ridge** - a simple, transparent model. It assigns each factor (loan
#   amount, sector, framing style, etc.) a fixed weight and adds them up,
#   like a scorecard. Easy to trust, but can't capture "this factor
#   matters differently depending on another factor."
# - **Boosted trees (HistGradientBoosting)** - a more flexible model that
#   can learn rules like "urgency language matters more for small loans
#   than large ones." More powerful, but harder to inspect directly -
#   Section 8's SHAP analysis opens it back up.
#
# Both predict how many days a loan takes to fund, scored the same way:
# MAE (average days off) and R² (share of the real variation explained).

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

# %% [markdown]
# Tested on loans neither model had seen (2024-2025): the simple
# scorecard model (Ridge) is off by 6.76 days on average. The more
# flexible model tightens that to 5.53 days and explains 49.3% of why
# funding speed varies from loan to loan (R² = 0.493) - roughly half the
# story of "why did this loan take as long as it did" can be explained
# from what's known at posting time; the rest comes down to things this
# data doesn't capture (how compelling individual lenders found it,
# timing luck, and so on). The flexible model beating the scorecard by
# over a day of average accuracy is itself a finding: funding speed isn't
# a simple additive checklist - some factors matter more in combination
# than alone (e.g. narrative framing plausibly matters differently
# depending on loan size or sector, which Section 7's statistical model
# tests directly).

# %% [markdown]
# ## 6. Predictive Modeling: 24-Hour Funding (Classification)
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
# ROC AUC of 0.905 out of a possible 1.0 (0.5 would mean no better than a
# coin flip) - a genuinely strong result for telling apart, before the
# fact, which loans are likely to fund fast versus drag on. That's on a
# real, never-seen holdout set, and on a task where the honest baseline
# is hard (recall from the EDA notebook: only 30-46% of loans actually
# fund within 24 hours, so simply guessing "yes" would do poorly). This
# is the strongest practical result in the analysis: a tool built purely
# from information available the moment a loan is posted (loan size,
# sector, region, narrative text) could reliably flag at-risk loans for
# extra visibility - independent of whether any single narrative-framing
# choice turns out to be the reason why.

# %% [markdown]
# ## 7. Explanatory Modeling: What Drives Funding Speed?
#
# Sections 5-6 built models that predict well, but a prediction machine
# doesn't say why. This section uses regression to measure, for every
# factor at once, how strongly it's linked to funding speed once
# everything else about the loan is held fixed - the fairest way to check
# whether narrative framing genuinely matters on its own, not just
# because it happens to travel alongside something else (like loan
# size). Every number here is an association, never a cause - borrowers
# weren't randomly assigned a writing style, a loan amount, or a gender.
# If the model can't be fit for a technical reason, that's reported as a
# clear message instead of a crash.

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
# Every coefficient above is relative to an omitted reference category
# (e.g. gender's baseline is "female," the period baseline is
# "pandemic_disruption") - printed explicitly below rather than left for
# a reader to infer from which levels are missing.

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
# sample. Negative coefficients are associated with faster funding,
# positive with slower, each compared against the reference category
# printed above.
#
# **Narrative framing has a real but conditional story, not a flat one.**
# Urgency language (words like "urgent," "emergency," "right now") is
# consistently linked to faster funding, and the effect is not a
# coincidence (p < 0.001) - a clean win for a simple writing choice.
# Agency/competence language ("I run my own business," "I manage...")
# shows no real link either way - the "sound capable and independent"
# hypothesis doesn't hold up at this scale. Family/communal framing has
# no single flat effect on its own, but it interacts strongly with timing
# and location: the family-framing speed benefit was strongest
# pre-pandemic and only partially came back post-pandemic - direct,
# model-based confirmation of the EDA notebook's "funding dynamics
# permanently shifted after 2020" finding. It also varies sharply by
# region: the family-framing benefit is far larger in the Middle East and
# Central America than in North America or Asia, where it's mildly
# counterproductive. Family framing helps, but who it helps and how much
# depends heavily on when and where the loan is posted - it isn't a
# universal lever.
#
# Sentiment tone shows a counterintuitive association: a more
# positive-sounding description is linked to slower funding, and this
# isn't noise either (p < 0.001). Combined with the EDA notebook's
# finding that descriptions are almost uniformly positive already, this
# may simply reflect that longer, more elaborately-written pitches read
# as more positive and naturally take longer to write and review - an
# association, not a reason to write flatter descriptions.
#
# Structural factors remain the largest effects by far. A loan posted
# under a male borrower takes notably longer to fund than one posted
# under a female borrower - the single largest factor in the whole model.
# Small loans fund far faster than large ones. Loans repaid as a single
# lump sum at the end of the term are far slower to fund than loans
# repaid irregularly or monthly. Sector and region matter enormously too
# - Water and Education-sector loans fund dramatically faster than
# Agriculture-sector loans, while Clothing and Retail loans fund slower.

# %% [markdown]
# ## 8. Feature Importance (SHAP)
#
# Section 7's statistical model is easy to interpret, but by design it
# can only check the specific combinations it's told to look for (framing
# x period, framing x region). Section 5's more flexible model learned
# whatever patterns were actually in the data, with no such restriction -
# but on its own it's a black box that doesn't explain itself. SHAP opens
# it back up: for every prediction, it works out exactly how much each
# factor pushed that prediction up or down, then averaging across many
# loans ranks what the model actually relied on - a second, independent
# check on Section 7's findings, not a replacement for them.
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
# This second, independent check confirms the top of Section 7's story:
# loan amount and repayment term are, by a wide margin, the two factors
# the flexible model relied on most - matching Section 7's largest single
# linked factor. The time period (pre-pandemic vs. not) and loan size
# also rank near the top, again agreeing with Section 7's biggest
# effects.
#
# The honest divergence worth stating plainly: narrative framing barely
# registers here. None of the family, agency, or urgency framing scores
# make it into the top 15 factors this more flexible model actually
# relied on - only overall sentiment tone cracks the list, in 11th place,
# well behind individual sector and region categories. This doesn't
# contradict Section 7 - urgency framing's link to speed, and family
# framing's timing/location pattern, are both genuinely, robustly real.
# But it's a useful check on what "statistically confident" means with
# 1.45 million loans: even a small, consistent effect becomes easy to
# detect with that much data. This check measures something different -
# actual size of impact, not confidence that an effect is real - and by
# that measure, narrative framing is real but genuinely minor next to how
# a loan is structured. Both things are true, and worth saying together:
# framing has a statistically solid, consistent effect (Section 7's
# story), and it's a modest one in practical terms next to loan size and
# repayment structure (this section's story) - that combined picture is a
# stronger answer to "does narrative framing matter?" than either half
# alone.

# %% [markdown]
# ## 9. Key Findings
#
# 1. **Predictive ceiling**: a model using only information available the
#    moment a loan is posted explains about half the story of funding
#    speed (R² = 0.49, typically off by 5.5 days) and is genuinely strong
#    at flagging which loans will fund within 24 hours (ROC AUC 0.90) -
#    strong enough to be a real, usable tool.
# 2. **Urgency framing is the cleanest narrative win** - consistently
#    linked to faster funding, no conditions or caveats needed.
# 3. **Family framing's benefit is real but conditional** on timing and
#    location - strongest before the pandemic and in the Middle East and
#    Central America, weaker or reversed elsewhere. This nuance, not a
#    flat "always use family framing" rule, is the more honest and more
#    interesting practical-implications story.
# 4. **How a loan is structured matters far more than how its story is
#    written.** Loan size, repayment terms, sector, region, and even
#    borrower gender all outweigh narrative framing. Framing is real and
#    measurable, but a secondary lever, not the main one.
# 5. **A second, independent method agrees.** Asking the more flexible
#    model directly what it relied on (Section 8) lands on the same
#    "structure over framing" conclusion as Section 7's statistical
#    model - two different techniques agreeing is a stronger result than
#    either alone, and a clear example of why statistical significance
#    and practical importance aren't always the same thing.
