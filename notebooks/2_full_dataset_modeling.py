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
# EDA notebook found funding speed shifted lastingly around 2020 (slower
# through the end of the data, 2025).

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
# **1,174,953 loans** (2016-2023) train the models; **278,887 loans**
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
# flexible model tightens that to **5.56 days** and accounts for **49.0%**
# of the predictive variation in funding speed (R² = 0.490) - roughly half
# of how much loans differ in funding speed lines up with what's knowable
# at posting time; the rest comes down to things this data doesn't
# capture (how compelling individual lenders found it, timing luck, and
# so on) - or simply isn't predictable from these factors alone. The
# scatter plot above shows this
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
# crash. The p-values below use HC3 standard errors, which correct for
# uneven variance but still assume every loan is statistically
# independent of every other loan - Section 7.1 checks that assumption
# directly and substantially revises which of these results hold up.

# %%
FORMULA = (
    "log_funding_speed ~ log_loan_amount + lenderRepaymentTerm + is_group_loan + "
    "C(gender_classification) + family_mentions_per_100_words + agency_mentions_per_100_words + "
    "urgency_mentions_per_100_words + desc_sentiment_compound + C(repaymentInterval) + "
    "C(sector_group) + C(region_group) + C(analysis_period) + C(loan_size_band) + "
    "family_mentions_per_100_words:C(analysis_period) + family_mentions_per_100_words:C(region_group) + "
    "family_mentions_per_100_words:C(loan_size_band)"
)
CATEGORICAL_TERMS = [
    "gender_classification", "repaymentInterval", "sector_group",
    "region_group", "analysis_period", "loan_size_band",
]

# `duration_model` starts as None so the reference-category cell below
# can check whether the fit actually succeeded instead of assuming it did
# and crashing with a NameError if this try block's except branch ran.
duration_model = None
try:
    y, X = patsy.dmatrices(FORMULA, data=valid, return_type="dataframe")
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        duration_model = sm.OLS(y, X).fit(cov_type="HC3")
    print(duration_model.summary())
except Exception as error:  # noqa: BLE001 - reported clearly, not left as a crash
    print(f"Duration explanatory model could not be fit: {error}")

# %% [markdown]
# Every coefficient above is relative to an omitted **reference
# category** (e.g. gender's baseline is `"female"`, the period baseline
# is `"pandemic_disruption"`) - printed explicitly below rather than left
# for a reader to infer from which levels are missing.

# %%
if duration_model is None:
    print("Skipping reference-category report - the duration model above did not fit.")
else:
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
# ### 7.1 Cluster-Robust Sensitivity Check
#
# HC3 corrects for uneven variance across loans, but still assumes every
# loan is an independent observation. Loans from the same country may
# share unobserved influences (a field partner's writing template, local
# conditions) that HC3 can't see - if enough of that dependence exists,
# some of the small p-values above could be more confident than the data
# really supports. This refits the identical design with standard errors
# clustered by `country_name` instead, and checks whether each narrative-
# framing term's significance conclusion (p < 0.05 or not) survives the
# switch, plus a count across every coefficient in the model.

# %%
# Initialised before the guard so Section 7.2 can check whether this refit
# actually happened, instead of raising NameError if it didn't.
duration_model_clustered = None
if duration_model is None:
    print("Skipping cluster-robust sensitivity check - the duration model above did not fit.")
else:
    duration_model_clustered = sm.OLS(y, X).fit(
        cov_type="cluster", cov_kwds={"groups": valid.loc[X.index, "country_name"]}
    )

    framing_terms = [
        name for name in duration_model.params.index
        if "mentions_per_100_words" in name or name == "desc_sentiment_compound"
    ]
    print("Narrative-framing and sentiment terms, HC3 vs. cluster-robust:")
    for name in framing_terms:
        p_hc3 = duration_model.pvalues[name]
        p_clustered = duration_model_clustered.pvalues[name]
        agreement = "same conclusion" if (p_hc3 < 0.05) == (p_clustered < 0.05) else "CONCLUSION CHANGES"
        print(f"  {name}: HC3 p={p_hc3:.4f}, clustered p={p_clustered:.4f} [{agreement}]")

    all_terms = [name for name in duration_model.params.index if name != "Intercept"]
    n_flip = sum(
        (duration_model.pvalues[name] < 0.05) != (duration_model_clustered.pvalues[name] < 0.05)
        for name in all_terms
    )
    print(f"\nAcross all {len(all_terms)} coefficients, {n_flip} change significance conclusion under clustering.")

# %% [markdown]
# **This is the most consequential check in the notebook, and it
# substantially revises the picture a reader would take from the raw HC3
# output above.** Comparing each term's significance conclusion
# (p < 0.05 or not) between HC3 and country-clustered standard errors:
#
# - **Urgency framing's apparent "clean win" does not survive.** HC3
#   p ≈ 0.000 looked decisive; clustered by country, p rises to roughly
#   0.44 - no longer distinguishable from no association at all. The
#   correlation in this sample isn't fabricated, but HC3 was overconfident
#   about how precisely it's pinned down, because it can't see that loans
#   from the same country share unobserved influences (a field partner's
#   writing template, local conditions, a partner's typical loan mix)
#   that make them less independent than HC3 assumes.
# - **Family framing's timing and loan-size interactions don't survive
#   either** - p-values move from well under 0.001 under HC3 to well
#   above 0.2 clustered. **Its Middle East and Central America regional
#   interactions do survive** (clustered p ≈ 0.0002 and 0.0070); Asia,
#   North America and Oceania's interactions do not. **But read these
#   interaction results with the caution Section 7.2 spells out**: an
#   interaction term only tests whether a region's slope differs from the
#   Africa baseline's slope - it does *not* test whether family framing
#   does anything within that region. Section 7.2 runs that second,
#   more relevant test - and in this notebook's model it surfaces a
#   *slower*-funding slope for Asia that this interaction row hides,
#   though that one does not replicate in the authoritative pipeline and
#   so is not claimed as a finding (see 7.2).
# - **Agency framing's null result is unchanged** - it wasn't significant
#   under HC3 either (p ≈ 0.46), so clustering doesn't change the
#   conclusion; there was never a case for it.
# - **Sentiment tone's association does not survive in this model either**
#   - HC3 p ≈ 0.000, clustered p ≈ 0.25. This is worth stating plainly
#     because it's the one place this notebook's own result disagrees with
#     this project's separate, richer pipeline (next paragraph) - a
#     reminder that "survives clustering" can itself depend on exactly
#     which other terms are in the model, not just on the finding being
#     tested.
# - Overall, **20 of this model's 45 coefficients (44%) change their
#   significance conclusion under clustering** - concentrated in the
#   narrative-framing and sentiment terms, while the structural terms
#   (sector, region, loan size, gender, repayment structure) mostly don't
#   move.
#
# **Cross-check against this project's separate, authoritative modeling
# pipeline** (`src/statistical_analysis.py`, run independently on the same
# full dataset with a richer formula that also interacts family framing
# with sector, and fitting a 24-hour binary model alongside the duration
# one): structural factors survive clustering there too, and most
# narrative-framing interactions don't - the same pattern as here.
# **Sentiment's association genuinely disagrees across the two
# pipelines**: it survives in both of the richer pipeline's models
# (clustered p ≈ 0.01 duration, ≈ 0.02 for the 24-hour model) but not in
# this notebook's simpler one (clustered p ≈ 0.25). A result that depends
# on which other terms share the formula is a weaker result than one that
# doesn't, even when one specification shows significance, so sentiment's
# status is left genuinely uncertain rather than claimed either way.
# Section 7.2 carries the region-by-region comparison, which is where the
# cross-check actually matters.
#
# **Why this matters more than any individual coefficient**: a model that
# only reports HC3 p-values on 1.45 million rows will find almost
# anything "significant," because that much data makes standard errors
# tiny even when the underlying association is fragile. Checking whether
# a result survives a structurally different, more conservative
# assumption about independence - and whether it survives a different but
# equally reasonable model specification, and whether the *quantity being
# tested is even the right one* (Section 7.2) - is what separates a real,
# useable pattern from one that is numerically precise but practically
# unreliable. **The honest bottom line: narrative framing's
# strongest-looking HC3 result (urgency) doesn't hold up, most of family
# framing's conditional structure doesn't hold up, sentiment's association
# is genuinely uncertain rather than confirmed, and family framing's real
# story - once tested with the correct within-region contrast in
# Section 7.2 - narrows to two pooled two-country categories rather than
# any generalizable writing rule.**

# %% [markdown]
# ### 7.2 What Family Framing Is Associated With *Within* Each Region
#
# The interaction coefficients above answer a narrower question than they
# look like they answer. `family_mentions_per_100_words:C(region_group)[T.X]`
# tests whether family framing's slope **in region X differs from the
# reference region's slope** (Africa) - it does *not* say the slope inside
# region X is itself different from zero. A significant interaction is
# compatible with family framing doing nothing at all in region X, as long
# as "nothing" is far enough from whatever Africa does.
#
# Getting the within-region quantity right takes one more step than it
# first appears, because **family framing is interacted with three
# moderators here, not one** (period, region, and loan size). Its main
# effect is therefore the family slope only when period *and* loan size
# both sit at their own reference levels - `pandemic_disruption` and
# `large`, a combination covering only a few percent of loans. So
# "main effect + region term" would still be a slope at one unrepresentative
# corner of the data, not a description of the region.
#
# What this computes instead is the **average within-region slope**: for
# each region, family framing's slope averaged over that region's *own*
# mix of periods and loan sizes. Because that average is a weighted sum of
# coefficients, it is still a single linear contrast, so `t_test` gives it
# the same HC3 and cluster-robust treatment as any coefficient. The
# `countries` column is printed alongside because a region's slope is
# identified only by the countries in it - and clustering by country is
# exactly what stops same-country loans counting as independent evidence.

# %%
FAMILY = "family_mentions_per_100_words"

if duration_model is None or duration_model_clustered is None:
    print("Skipping within-region slopes - the duration model or its cluster refit did not run.")
else:
    param_names = list(duration_model.params.index)
    # Family framing is interacted with THREE moderators, not just region.
    # Its main effect is therefore the slope only when period AND loan size
    # both sit at their reference levels - so a contrast of
    # `main + region[X]` alone would silently condition on that one cell
    # (here: pandemic_disruption x large, a few percent of all loans).
    # To get the slope that actually describes region X, average over
    # region X's OWN distribution of the other moderators: weight each
    # non-reference dummy by the share of that region's rows sitting at
    # that level. The result is a proper linear contrast, so `t_test`
    # gives it the same HC3 / cluster-robust treatment as any coefficient.
    other_moderator_terms = [
        name for name in param_names
        if name.startswith(f"{FAMILY}:C(") and ":C(region_group)[" not in name
    ]
    region_terms = {
        name.split("[T.")[1].rstrip("]"): name
        for name in param_names
        if name.startswith(f"{FAMILY}:C(region_group)[T.")
    }
    fitted_rows = valid.loc[X.index]

    print(f"{'region':<17}{'countries':>10}{'loans':>9}   average family-framing slope within that region")
    for level in sorted(fitted_rows["region_group"].astype(str).unique()):
        sub = fitted_rows.loc[fitted_rows["region_group"].astype(str) == level]
        pieces = [FAMILY]
        if level in region_terms:  # the reference region has no term of its own
            pieces.append(region_terms[level])
        for term in other_moderator_terms:
            column = term.split(":C(")[1].split(")[T.")[0]
            moderator_level = term.split(")[T.")[1].rstrip("]")
            weight = float((sub[column].astype(str) == moderator_level).mean())
            if weight > 0:
                pieces.append(f"{weight:.10f} * {term}")
        contrast = " + ".join(pieces) + " = 0"

        t_hc3 = duration_model.t_test(contrast)
        t_clu = duration_model_clustered.t_test(contrast)
        est = float(np.ravel(t_hc3.effect)[0])
        p_hc3_c = float(np.ravel(t_hc3.pvalue)[0])
        p_clu_c = float(np.ravel(t_clu.pvalue)[0])
        verdict = "significant under BOTH" if (p_hc3_c < 0.05 and p_clu_c < 0.05) else "not significant under both"
        print(
            f"  {level:<15}{sub['country_name'].nunique():>10}{len(sub):>9}   "
            f"estimate={est:+.4f}  HC3 p={p_hc3_c:.4f}  clustered p={p_clu_c:.4f}  [{verdict}]"
        )

# %% [markdown]
# **Averaged properly over each region's own composition, the picture is
# simpler and narrower than the interaction table above suggests: exactly
# two regions show an association that survives clustering, and both point
# the same way.** Sign convention: **negative = faster funding, positive =
# slower.**
#
# - **Middle East: -0.1236, clustered p < 0.0001.** More family language
#   is associated with *faster* funding. The largest narrative-framing
#   association anywhere in this analysis.
# - **Central America: -0.0618, clustered p < 0.0001.** Same direction,
#   about half the magnitude.
# - **Asia: +0.0338, clustered p = 0.0535 - not significant**, though only
#   just, and worth stating plainly because an earlier version of this
#   analysis got it wrong. Computing the slope at the model's reference
#   cell instead of averaging over Asia's own composition made this look
#   significant (p = 0.0070) and pointing the opposite way from the
#   surviving regions. It was an artifact of evaluating the slope at an
#   unrepresentative corner of the data (`pandemic_disruption` x `large`),
#   not a real finding - and the corrected value agrees with this
#   project's separate authoritative pipeline, which never found Asia
#   significant.
# - **Africa (p = 0.5536), North America (p = 0.0621) and Oceania
#   (p = 0.6305)** show no association surviving clustering. Africa is the
#   reference region and the largest by country count, so the absence
#   there matters: there is no general "family framing helps" effect that
#   the two surviving regions are merely a strong version of.
#
# **Cross-checked against the authoritative pipeline, the two surviving
# results hold in all three fits.** Recomputing the same averaged
# within-region slopes through `src/statistical_analysis.py` (richer
# formula, plus a separate 24-hour binary model) gives Middle East
# -0.0729 (duration, clustered p < 0.0001) and +0.1753 (24-hour,
# p = 0.0040), and Central America -0.0742 (p < 0.0001) and +0.1025
# (p < 0.0001) - remembering the 24-hour model's sign convention is
# inverted, so positive there also means faster. Three fits, same two
# regions, same direction. Asia is non-significant in all three
# (p = 0.0535 / 0.0846 / 0.2860), which is what resolved the earlier
# contradiction. Note that magnitude is more specification-sensitive than
# significance: Middle East is -0.1236 here and -0.0729 there, roughly a
# 1.7x difference, mostly because that pipeline also interacts family
# framing with sector. North America turns up significant in that
# pipeline's duration model alone (p = 0.0094) and in neither other fit -
# it is a single country (Haiti), one cluster, and is not claimed.
#
# **The `countries` column is where the real limitation lives.** "Middle
# East" in this dataset is **Palestine and Yemen** - two countries.
# "Central America" is **Honduras and Nicaragua** - two countries. "North
# America" is Haiti alone. Mechanically the clustered covariance still
# uses all 48 country clusters, so these standard errors are not computed
# from two clusters; but each region's slope is *identified* only by the
# countries inside it. With two, the estimate cannot separate "family
# framing is associated with faster funding" from "something else is
# different about Palestine and Yemen" - which is precisely the confound
# clustering was introduced to take seriously.
#
# **So the honest reading is narrow and exploratory: within these two
# pooled categories, more family language is associated with faster
# funding on average.** It is not a claim about the Middle East or
# Central America as regions; it is not a claim about any individual
# country either - the model estimates one pooled slope per category, and
# a pooled result can be driven mostly by one constituent country; and it
# is not a writing rule to roll out. All of this is association
# within this sample - clustering adjusts for within-country dependence,
# it does not remove country-level confounding or license a causal
# reading.

# %% [markdown]
# Fit on all 1,453,840 valid loans (R² = 0.426, meaning the fitted model
# accounts for 42.6% of the variation in funding speed). At this sample
# size, standard errors are precise - the estimates below are not noisy
# small-sample guesses - but precision is not the same as certainty about
# cause, or even about how precise an estimate really is: a large N
# sharpens a point estimate, but if nearby loans share unobserved
# influences, the textbook HC3 formula can overstate how confident that
# estimate should be. Section 7.1 checks this directly; the summary below
# already reflects what survives that check, not the raw HC3 read.
# **Negative coefficients are associated with faster funding, positive
# with slower**, each compared against the reference category printed
# above.
#
# - **Structural factors are the largest effects by far, and this
#   conclusion is unaffected by the robustness check in Section 7.1.**
#   The single biggest swings in the whole model come from sector and
#   region - Water and Education-sector loans fund dramatically faster
#   than Agriculture-sector loans, while Clothing and Retail loans fund
#   slower, and the Middle East funds far faster than the model's
#   reference region. A loan posted under a male borrower takes notably
#   longer to fund than one posted under a female borrower - a smaller
#   effect than the biggest sector/region gaps, but larger than the loan
#   amount itself, and larger than every narrative-framing term combined.
#   Small loans fund far faster than large ones. Loans repaid as a single
#   lump sum at the end of the term are far slower to fund than loans
#   repaid irregularly or monthly.
# - **Sentiment tone's association looks precise under HC3 alone, but
#   Section 7.1 shows it doesn't survive clustering in this model** (p
#   rises from p < 0.001 to roughly 0.25) - even though it does survive in
#   this project's separate, richer pipeline. Treat it as genuinely
#   uncertain rather than confirmed. Worth noting anyway: the direction is
#   a more positive-sounding description linked to **slower** funding -
#   counterintuitive, and, combined with the EDA notebook's finding that
#   descriptions are almost uniformly positive already, plausibly just
#   reflects that longer, more elaborately-written pitches read as more
#   positive *and* naturally take longer to write and review.
# - **Urgency, and most of family framing's conditional structure, looked
#   significant under HC3 alone - Section 7.1 shows that doesn't survive
#   clustering.** Treat "urgency helps" and "family framing depends on
#   timing/loan size" as not supported by this data at a rigorous
#   standard, even though they were the two headline results a
#   single-standard-error read would have reported.
# - **Family framing's regional pattern is the exception that survives.**
#   Tested with the correct within-region contrast (Section 7.2), family
#   framing is associated with *faster* funding in the Middle East and
#   Central America categories - significant under clustering in all
#   three same-data fits (this notebook's, plus the authoritative
#   pipeline's duration and 24-hour models; related specifications, not
#   independent replications). But each category is two countries
#   (Palestine/Yemen; Honduras/Nicaragua) and each estimate is pooled
#   across its pair, so this is a narrow, exploratory pooled-category
#   result - not a region-level finding, and not a per-country one. Everywhere else, and for every other narrative-framing term,
#   the HC3-only significance above is not a reliable finding on its own.
# - **Agency/competence language shows no real link in this notebook's
#   model, under HC3 or clustered** - the "sound capable and independent"
#   hypothesis doesn't hold up here under either standard-error method.
#   Worth flagging so this isn't read as a universal null: this project's
#   separate, richer pipeline's 24-hour funding model *did* show agency as
#   HC3-significant (p < 0.001) before failing to survive clustering
#   (p ≈ 0.20) - the identical apparent-but-fragile pattern urgency shows
#   above. That model isn't reproduced in this notebook (only a duration
#   model is fit here), so it can't be cross-checked directly, but agency
#   isn't a clean, universal non-finding either - it's null here and
#   fragile there.

# %% [markdown]
# ## 8. Feature Importance
#
# Explanatory Modeling's statistical model is easy to interpret, but by
# design it can only check the specific combinations it's told to look
# for (framing x period, framing x region, framing x loan size). The
# boosted model from
# Regression Modeling learned whatever patterns were actually in the
# data, with no such restriction - but on its own it's a black box that
# doesn't explain itself. **SHAP** opens it back up: for every
# prediction, it works out exactly how much each factor pushed that
# prediction up or down, then averaging across many loans ranks what the
# model actually relied on - a second, independent check on the
# Explanatory Modeling findings, not a replacement for them.
#
# `shap` ships in Kaggle's standard Python image; the fallback below
# installs it on the rare environment where it's missing. Computed on a
# random sample of 2,000 holdout loans for speed - a larger sample would
# take longer for a negligibly different ranking.

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
# Modeling story, with one nuance worth spelling out**: loan amount and
# repayment term are, by a wide margin, the two factors the flexible
# model relied on most. Loan amount lines up directly with Section 7 - its
# coefficient there is solidly large (near-tied with gender, and bigger
# than every narrative-framing term), though Section 7 itself ranks the
# biggest sector and region swings above it, not below.
# Repayment term is a little different: its per-unit coefficient (+0.068)
# looks modest next to a sector or region dummy, but the term itself
# spans a huge range across loans - most cluster between 8 and 14 months
# (the middle 50%), but it runs from 2 months to a long tail past 130 -
# so the *cumulative* swing across that range is large, exactly what SHAP
# measures and something a single per-unit coefficient doesn't show on
# its own. The time period
# (pre-pandemic vs. not) and loan size also rank near the top, again
# agreeing with Section 7's biggest effects.
#
# **The honest divergence worth stating plainly: narrative framing barely
# registers here, and this broadly lines up with Section 7.1's robustness
# check even though the two are completely independent methods.** None of
# the family, agency, or urgency framing scores make it into the top 15
# factors this more flexible model actually relied on - matching 7.1's
# finding that urgency's HC3 significance and most of family framing's
# conditional structure don't survive clustering. Only overall sentiment
# tone cracks the list, in 11th place, well behind individual sector and
# region categories - a more interesting case, because 7.1 found
# sentiment's *statistical significance* doesn't reliably survive
# clustering either (it depends on which other terms are in the model),
# even though it clearly carries some real predictive weight here. That's
# not a contradiction - SHAP importance (how much a feature actually moves
# predictions) and clustered-standard-error significance (how confident
# the association's *sign and size* are) measure genuinely different
# things, and sentiment is the one term in this analysis where they don't
# point the same way. **Two independent methods agree that urgency and
# most of family framing's conditional structure are much smaller than
# Section 7's raw HC3 p-values suggested; sentiment's real-world weight is
# small but non-trivial, even though this analysis can't confidently call
# its statistical significance robust.** This is also a useful reminder of
# what "statistically significant" means with 1.45 million rows: even a
# fragile, non-robust pattern can produce a tiny HC3 p-value simply
# because there's so much data. This check measures something different -
# **predictive contribution in the boosted model, not statistical
# confidence in an inferential association** -
# and by that measure, narrative framing (family/agency/urgency) is minor
# next to how a loan is structured.

# %% [markdown]
# ## 9. Key Findings

# %% [markdown]
# ### 9.1 Technical Interpretation
#
# - A model using only posting-time information accounts for about half
#   the predictive variation in funding speed (R² = 0.49, MAE 5.6 days)
#   and discriminates 24-hour funding strongly (ROC AUC 0.91) - this
#   predictive result doesn't depend on any narrative-framing claim and is
#   unaffected by everything below.
# - Structural factors (loan size, repayment terms, sector, region,
#   borrower gender) have coefficients several times larger than any
#   narrative-framing term, and this ranking is unaffected by the
#   cluster-robust check in Section 7.1.
# - **A cluster-robust sensitivity check (Section 7.1) substantially
#   revised the narrative-framing picture**: 20 of this model's 45
#   coefficients (44%) change their significance conclusion when standard
#   errors are clustered by country instead of assumed independent.
#   Urgency framing's apparent association does not survive; neither does
#   most of family framing's time-period and loan-size structure.
# - **Testing the right quantity mattered as much as testing it
#   robustly.** The interaction coefficients above only test whether a
#   region's slope differs from the Africa baseline - not whether family
#   framing does anything *within* a region. The within-region averages in
#   Section 7.2 test the latter, averaging each region's slope over its
#   own mix of periods and loan sizes. Only two regions survive: family
#   framing is associated with **faster** funding in the Middle East
#   (-0.124, clustered p < 0.0001) and Central America (-0.062,
#   clustered p < 0.0001).
# - **Getting that quantity right mattered, and an earlier version of
#   this analysis got it wrong.** Evaluating the slope at the model's
#   reference cell rather than averaging over each region's composition
#   made Asia look significant in the opposite direction (p = 0.0070).
#   Corrected, Asia is not significant (+0.034, p = 0.0535) - and now
#   agrees with the authoritative pipeline, which never found it
#   significant. Africa (p = 0.5536), North America (p = 0.0621) and
#   Oceania (p = 0.6305) show no association surviving clustering.
# - **The surviving result is two pooled two-country categories, not two
#   regions and not four separate country findings** - "Middle East" here
#   is Palestine and Yemen; "Central America" is Honduras and Nicaragua;
#   the model estimates one pooled slope per category and none for any
#   individual country. Since clustering by country is precisely what
#   stops same-country loans counting as independent evidence, a
#   two-cluster group carries very little of it. Robust across our
#   related, same-data specifications, but narrow and exploratory.
# - Agency framing shows no association either way in this notebook's
#   model - though the authoritative pipeline's separate 24-hour model
#   shows agency following the same apparent-but-fragile pattern as
#   urgency (HC3-significant, doesn't survive clustering), so it isn't a
#   clean null everywhere tested.
# - **Sentiment tone's association is genuinely unresolved, not
#   confirmed** - it survives clustering in the authoritative pipeline's
#   richer model (clustered p ≈ 0.01) but not in this notebook's simpler
#   one (clustered p ≈ 0.25). Rather than pick whichever number is more
#   convenient, this analysis reports the disagreement: sentiment's
#   direction (more positive language links to slower funding) is
#   consistent everywhere tested, but its statistical robustness is not.
# - SHAP feature importance from an independently-trained boosted model
#   (Section 8) corroborates the cluster-robust check for urgency and
#   family framing from a completely different angle: those features fall
#   outside its top 15 factors. Sentiment does crack the top 15 there
#   (11th place) despite its fragile significance - a reminder that
#   predictive weight and statistical robustness are different questions.

# %% [markdown]
# ### 9.2 Business Impact
#
# - **A 24-hour-funding risk flag is worth piloting** - holdout ROC AUC
#   0.91 shows a strong ranking signal, without needing any
#   narrative-framing insight at all. Discrimination alone doesn't settle
#   deployment: a rollout still needs a chosen threshold, calibration at
#   that threshold, capacity and fairness checks, and a prospective test
#   that surfacing flagged loans actually helps them fund.
# - **Don't recommend urgency language as a general rule.** Its raw HC3
#   association looked like a clean, simple win, but that doesn't survive
#   a stricter, more realistic check for how loans from the same country
#   relate to each other. Recommending it platform-wide would be advice
#   built on a fragile statistical artifact, not a tested pattern.
# - **Do not issue a platform-wide "mention family" recommendation.**
#   Across Africa (27 countries), Asia (12), North America and Oceania -
#   together ~95% of all loans - no association survives clustering. The
#   only place the evidence holds up is the two pooled Middle East and
#   Central America categories covering the remaining ~5%.
# - **Where it does hold up, the defensible action is a country-stratified
#   test, not a rollout.** Family framing's link to faster funding in the
#   pooled Middle East and Central America categories survives the correct
#   contrast, country clustering, and all three of our same-data fits -
#   genuinely the strongest narrative-framing result in this project. But
#   the estimate is pooled: it cannot say which constituent country drives
#   it, and two countries per category is thin evidence precisely because
#   clustering is what stops same-country loans counting separately. Treat
#   it as a hypothesis for an A/B test *stratified by country* in those
#   markets - designed to locate any real heterogeneity - not a finding to
#   deploy, and don't generalize it to "the Middle East" or "Central
#   America."
# - **Structure, not copywriting, is the strongest association by far** -
#   loan size, repayment terms, sector, and region are linked to funding
#   speed far more strongly than any narrative choice, and this conclusion
#   only got stronger once the framing findings were stress-tested rather
#   than taken at face value. These structural factors aren't something a
#   platform can change on an existing loan, but they're worth a
#   structural review in their own right - a genuinely different kind of
#   action than writing-style coaching, not a "lever" in the same sense
#   narrative framing is.
# - **The broader takeaway is as much about process as writing style**: a
#   typical single-standard-error analysis on this dataset would have
#   confidently recommended urgency language across the board. Testing
#   that recommendation against a more conservative assumption changed
#   the answer. Any narrative-framing recommendation drawn from a large
#   dataset is worth checking the same way before it's acted on.
