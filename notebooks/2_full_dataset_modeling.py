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
# needing the private package.
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
# information into training.

# %%
train_raw = valid.loc[valid["fundraisingDate_parsed"] < pd.Timestamp(HOLDOUT_START, tz="UTC")].copy()
holdout_raw = valid.loc[valid["fundraisingDate_parsed"] >= pd.Timestamp(HOLDOUT_START, tz="UTC")].copy()
print(f"Train rows: {len(train_raw)}  |  Holdout rows: {len(holdout_raw)}")

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
# ## 4. 24-hour funding classifier

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

try:
    y, X = patsy.dmatrices(FORMULA, data=valid, return_type="dataframe")
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        duration_model = sm.OLS(y, X).fit(cov_type="HC3")
    print(duration_model.summary())
except Exception as error:  # noqa: BLE001 - reported, not crashed, matching the tested pipeline's spirit
    print(f"Duration explanatory model could not be fit: {error}")

# %% [markdown]
# **Insight cell** - fill in after running: how do these numbers compare
# with the already-verified 2026-08-27 run in
# `../reports/generated_full_dataset/analysis_summary.json`? Directional
# agreement is expected; exact coefficients will differ (simplified
# framing patterns, sampled/full sentiment scoring differences, and a
# shorter formula here than the tested pipeline's).
