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
# This notebook answers two different questions about the same outcome,
# funding speed:
#
# - **Predictive** (Sections 3-4): *how well* can funding speed be
#   forecast for a newly-posted loan, using only information available
#   at posting time? This is the "could Kiva build a triage tool"
#   question - if a model can flag loans likely to languish, they could
#   be surfaced more prominently. Evaluated on a genuine chronological
#   holdout (loans posted in 2024-2025), not a random split, so it
#   reflects how a model would perform on loans it hasn't seen yet.
# - **Explanatory** (Section 5): *why* - which loan and narrative
#   characteristics are associated with faster or slower funding, holding
#   the others constant? This uses robust (HC3) standard errors and
#   reports **association, never causation** - see README.md's Known
#   Limitations for why a causal claim isn't supportable here.
#
# **Self-contained**: uses only standard public packages (pandas, numpy,
# scikit-learn, statsmodels, patsy, nltk) - no import of this repo's own
# `src/` package, so it runs as a plain Kaggle kernel with no private
# code dependency. This is a deliberately simpler, streamlined
# re-implementation of the same *design* the tested `src/` pipeline uses
# (chronological - not random - train/holdout split, robust HC3 standard
# errors, association-only language), not a port of its exact code.
#
# `../reports/generated_full_dataset/` (produced by
# `python3 -m src.run_analysis`, the actual tested pipeline) is the
# authoritative source for the final presentation's numbers; this
# notebook is for fast, portable iteration on Kaggle's compute without
# needing the private package. Every insight cell below quotes this
# notebook's own verified Kaggle run (2026-08-27, ~27 min on Kaggle's
# free CPU tier) - not a placeholder.
#
# Nothing here needs a GPU - Ridge/HistGradientBoosting/statsmodels are
# all CPU-only. See `../scripts/push_kaggle_kernel.sh modeling` and
# README.md's "Kaggle Workflow" section.

# %%
import re
import warnings
from pathlib import Path

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

HOLDOUT_START = "2024-01-01"

# %% [markdown]
# ## 1. Load, derive target, engineer features
#
# Same simplified narrative features as `1_full_dataset_eda.ipynb` -
# three theory-guided per-100-word framing rates (family, agency,
# urgency) plus VADER sentiment, vectorized over the whole column.

# %%
# The pickle is a list of row dicts, not a directly-pickled DataFrame
# (pd.read_pickle would raise) - a plain stdlib pickle.load handles both
# shapes, no custom package needed.
import pickle  # noqa: E402

with open(DATA_PATH, "rb") as handle:
    _raw = pickle.load(handle)
df = pd.DataFrame(_raw) if isinstance(_raw, list) else _raw

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

df["log_loan_amount"] = np.log1p(df["loanAmount"])
df["loan_size_band"] = pd.cut(
    df["loanAmount"], bins=[-np.inf, 250, 750, np.inf], labels=["small", "medium", "large"]
).astype(str)
df["gender_classification"] = df["gender"].fillna("unknown").apply(
    lambda g: "mixed" if "," in str(g) else str(g)
)
df["is_group_loan"] = (df["borrowerCount"] > 1).astype(int)

# Region/sector collapsed to a fixed observation-count threshold, not a
# hardcoded name list - a smaller-scale version of the same idea the
# tested pipeline uses (src/features.py) so rare categories don't break
# the model, without porting that module's exact code.
for col, min_obs, new_col in [("region", 10, "region_group"), ("sector", 1000, "sector_group")]:
    counts = df[col].value_counts()
    major = counts[counts >= min_obs].index
    df[new_col] = df[col].where(df[col].isin(major), "Other")

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
# ## 2. Chronological split (not random)
#
# Train on loans posted before `HOLDOUT_START`, evaluate on loans posted
# on/after it - mirrors how a model would actually score newly-posted
# loans. This is the one design choice from the tested pipeline kept
# exactly, not simplified: a random split would silently leak future
# information into training (the model would get to "see" narrative
# styles and market conditions from loans posted after the ones it's
# being tested on).

# %%
train_raw = valid.loc[valid["fundraisingDate_parsed"] < pd.Timestamp(HOLDOUT_START, tz="UTC")].copy()
holdout_raw = valid.loc[valid["fundraisingDate_parsed"] >= pd.Timestamp(HOLDOUT_START, tz="UTC")].copy()
print(f"Train rows: {len(train_raw)}  |  Holdout rows: {len(holdout_raw)}")

# %% [markdown]
# **What this shows.** 1,174,953 loans (2005-2023) train the models;
# 278,887 loans posted in 2024-2025 form a genuinely out-of-time holdout
# - about 19% of the full dataset, held back entirely from training.
# That's a large enough holdout to trust the metrics below as a real
# read on generalization, not a lucky split.

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
# ## 3. Predictive models: Ridge baseline + nonlinear benchmark
#
# Ridge is the simple, interpretable linear baseline. HistGradientBoosting
# is the nonlinear benchmark - it can pick up interactions (e.g. "urgency
# language matters more for small loans than large ones") that a linear
# model can't, at the cost of interpretability. Both predict
# `log_funding_speed`, then get transformed back to days for the metric.

# %%
ridge = Ridge(alpha=1.0, random_state=42)
ridge.fit(X_train, y_train_log)
ridge_holdout_days = np.expm1(np.clip(ridge.predict(X_holdout), a_min=0, a_max=None))
print(f"Ridge holdout MAE (days): {mean_absolute_error(y_holdout_days, ridge_holdout_days):.2f}")

boosted = HistGradientBoostingRegressor(random_state=42)
boosted.fit(X_train.toarray() if hasattr(X_train, "toarray") else X_train, y_train_log)
X_holdout_dense = X_holdout.toarray() if hasattr(X_holdout, "toarray") else X_holdout
boosted_holdout_days = np.expm1(np.clip(boosted.predict(X_holdout_dense), a_min=0, a_max=None))
print(f"Boosted holdout MAE (days): {mean_absolute_error(y_holdout_days, boosted_holdout_days):.2f}")
print(f"Boosted holdout R2: {r2_score(y_holdout_days, boosted_holdout_days):.3f}")

# %% [markdown]
# **What this shows.** On loans the models have never seen (2024-2025):
# Ridge's typical prediction is off by **6.76 days**; the nonlinear
# model tightens that to **5.53 days** and explains **49.3%** of the
# variance in funding speed (R² = 0.493). The gap between the two -
# boosted trees beating a linear model by over a day of average error -
# is itself informative: it means funding speed isn't just a weighted
# sum of loan characteristics, there are real nonlinear/interaction
# effects the linear model can't capture (e.g. narrative framing
# plausibly mattering differently across loan sizes or sectors, which is
# exactly what the interaction terms in Section 5 test directly).

# %% [markdown]
# ## 4. 24-hour funding classifier
#
# A binary reframing of the same problem: will this loan fund within a
# day of posting? This is the more operationally useful framing for a
# real triage tool - "flag loans unlikely to fund fast" is a simpler,
# more actionable signal than a precise day-count estimate.

# %%
y_train_binary = train_raw["funded_within_24h"].to_numpy()
y_holdout_binary = holdout_raw["funded_within_24h"].to_numpy()

classifier = HistGradientBoostingClassifier(random_state=42)
X_train_dense = X_train.toarray() if hasattr(X_train, "toarray") else X_train
classifier.fit(X_train_dense, y_train_binary)
holdout_proba = classifier.predict_proba(X_holdout_dense)[:, 1]

print(f"Holdout ROC AUC: {roc_auc_score(y_holdout_binary, holdout_proba):.4f}")
print(f"Holdout average precision: {average_precision_score(y_holdout_binary, holdout_proba):.4f}")

# %% [markdown]
# **What this shows.** ROC AUC of **0.905** and average precision of
# **0.837** on a genuine out-of-time holdout - strong discrimination for
# a real-world, imbalanced-outcome problem (recall from notebook 1: only
# ~30-46% of loans actually fund within 24 hours, depending on period).
# This is the strongest practical-implications result in the whole
# analysis: a model built purely from information available at posting
# time (loan size, sector, region, narrative text) can reliably flag,
# before the fact, which loans are at risk of funding slowly - the kind
# of signal a platform could act on operationally (e.g. surfacing
# at-risk loans more prominently), independent of whether any single
# narrative-framing choice is the reason why.

# %% [markdown]
# ## 5. Robust explanatory associations (HC3 standard errors)
#
# Fit on the whole valid sample (not the chronological split - the goal
# here is association, not out-of-sample prediction). Association
# language only - never causal. If this fails to fit (e.g. a formula
# term with no variation, or the binary model hitting separation - both
# real possibilities the tested pipeline handles explicitly, simplified
# to a plain try/except here), it's reported as a clear message, not a
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

    # Every coefficient below is *relative to an omitted reference
    # category* (patsy's Treatment coding) - print what that reference
    # actually is for each categorical term, rather than asking a reader
    # to guess it from which levels are missing.
    print("\nReference (omitted) category per categorical term:")
    for col in CATEGORICAL_TERMS:
        all_levels = set(valid[col].astype(str).unique())
        dummy_levels = {
            p.split("[T.")[1].rstrip("]")
            for p in duration_model.params.index
            if p.startswith(f"C({col})")
        }
        print(f"  {col}: {sorted(all_levels - dummy_levels)}")
except Exception as error:  # noqa: BLE001 - reported, not crashed, matching the tested pipeline's spirit
    print(f"Duration explanatory model could not be fit: {error}")

# %% [markdown]
# **What this shows - the core "why" findings for the deck.** Fit on all
# 1,453,840 valid loans with HC3-robust standard errors (R² = 0.425), so
# these are large-sample, well-powered associations, not noisy
# small-sample estimates. Coefficients are on `log_funding_speed`, so
# **positive = slower, negative = faster**, relative to each term's
# omitted reference category (see the reference-category printout above
# for exactly what that baseline is - e.g. gender's reference is
# "female", sector's is "Agriculture", the period reference is
# "pandemic_disruption").
#
# - **Narrative framing has a real but conditional story, not a flat
#   one.** Urgency language is consistently associated with faster
#   funding (coef -0.084, p < 0.001) - a genuine, clean win for a simple
#   framing choice. Agency/competence language shows no association
#   (p = 0.562) - the "sound capable and independent" hypothesis doesn't
#   hold up at this scale. Family/communal framing has no simple flat
#   effect either (its main-effect p = 0.071) - **but its interactions
#   are highly significant**: the family-framing speed benefit was
#   strongest pre-pandemic (interaction -0.023 relative to the
#   pandemic-disruption baseline) and only partially recovered
#   post-pandemic (-0.012) - direct, model-based confirmation of the
#   "funding dynamics permanently shifted after 2020" story from
#   notebook 1. It also varies sharply by region: the family-framing
#   benefit is far larger in the Middle East (-0.114) and Central
#   America (-0.053) than in North America (+0.025) or Asia (+0.045),
#   where it's mildly *counterproductive*. **The honest headline: family
#   framing helps, but who it helps and how much depends heavily on when
#   and where the loan is posted - it is not a universal lever.**
# - **Sentiment tone shows a counterintuitive association**: a more
#   positive description is linked to *slower* funding (coef +0.114,
#   p < 0.001). Combined with notebook 1's finding that descriptions are
#   almost uniformly positive already (median compound 0.88), this may
#   reflect longer, more elaborately-written pitches reading as more
#   positive *and* taking longer to compose/review - association only,
#   not a reason to write flatter descriptions.
# - **Structural factors remain the largest effects by far.** A borrower
#   posted as male takes notably longer to fund than one posted as
#   female (+0.433, the single largest non-sector/region coefficient in
#   the model) - a substantial, well-powered gap worth a slide of its
#   own. Small loans fund far faster than large ones (-0.571), and
#   `"at_end"` repayment (the full loan repaid in one lump sum at
#   maturity - this dataset's actual field value) is far slower than
#   irregular or monthly repayment (-0.377 / -0.104, i.e. faster,
#   relative to `"at_end"` as the omitted reference), and sector/region
#   effects span more than a full log-point
#   (e.g. Water and Education sectors fund dramatically faster than
#   Agriculture, the reference sector; Clothing and Retail fund slower).

# %% [markdown]
# ## Key takeaways for the deck
#
# 1. **Predictive ceiling**: a model using only posting-time information
#    explains about half the variance in funding speed (R² = 0.49,
#    MAE 5.5 days) and discriminates 24-hour funding very well
#    (ROC AUC 0.90) - strong enough to be operationally useful.
# 2. **Urgency framing is the cleanest narrative win** - consistently
#    associated with faster funding, no conditional caveats needed.
# 3. **Family framing's benefit is real but conditional** on period and
#    region - strongest pre-pandemic and in the Middle East/Central
#    America, weaker or reversed elsewhere. This nuance, not a flat
#    "use family framing" rule, is the more defensible and more
#    interesting story for the practical-implications criterion.
# 4. **Structural factors (loan size, repayment structure, sector,
#    region, and borrower gender) dwarf narrative framing in effect
#    size.** Framing is a real, measurable lever - but a secondary one
#    next to how a loan is structured.
