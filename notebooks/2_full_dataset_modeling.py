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
# **Who this notebook is for.** No data science background required.
# Every technical term is explained in plain language the first time it's
# used - look for **"In plain terms."** This notebook picks up right where
# `1_full_dataset_eda.ipynb` left off: that notebook looked at simple,
# one-factor-at-a-time patterns; this one builds statistical models that
# weigh *all* the factors at once, which is the only way to answer "does
# narrative framing matter, once you account for everything else about
# the loan?"
#
# This notebook answers two different questions about the same outcome,
# funding speed:
#
# - **Predictive** (Sections 1-2 below): *how well* can funding speed be
#   forecast for a newly-posted loan, using only information available at
#   posting time? In plain terms: could you build a tool that flags, the
#   moment a loan is posted, "this one looks likely to take a while to
#   fund"? Tested the honest way - on loans posted in 2024-2025 that the
#   model never saw while learning, not loans it's already seen the
#   answer for.
# - **Explanatory** (Section 3): *why* - which loan and narrative
#   characteristics are linked to faster or slower funding, once you
#   account for everything else about the loan at the same time? This
#   reports **association, never causation** - a link between two things
#   doesn't prove one causes the other (see README.md's Known
#   Limitations for why).
#
# **Terms used throughout this notebook** (a quick-reference glossary -
# each is also explained again the first time it comes up):
#
# | Term | In plain terms |
# |---|---|
# | **MAE** (mean absolute error) | On average, how many days off a prediction was. Lower is better. |
# | **R²** | What share of the ups-and-downs in funding speed the model can explain, from 0% (explains nothing) to 100% (explains everything). |
# | **ROC AUC** | How good a model is at telling apart "will fund fast" vs. "won't," from 0.5 (a coin flip) to 1.0 (perfect). |
# | **Holdout set** | Real loans the model never saw while learning - used to test whether it actually works on new loans, not just loans it's already memorized. |
# | **Coefficient** | A number showing how much one factor moves funding speed up or down, once every other factor is held fixed. |
# | **Statistical significance (p-value)** | How confident we can be that a link is real and not just random noise. A very small p-value (e.g. below 0.001) means very confident. |
# | **Reference category** | Every "how much faster/slower" number is a comparison against a chosen baseline group - the printout in Section 3 states exactly what that baseline is for each factor. |
# | **SHAP** | A way of asking a complex model directly "which factors did you actually rely on to make your predictions?" - a second, independent check on what matters. |
#
# **Self-contained**: uses only standard public packages (pandas, numpy,
# scikit-learn, statsmodels, patsy, nltk) - no import of this repo's own
# `src/` package, so it runs as a plain Kaggle kernel with no private
# code dependency. This is a deliberately simpler, streamlined
# re-implementation of the same *design* the project's tested internal
# pipeline uses (a fair, chronological train/test split; statistically
# robust association-only language), not a port of its exact code.
#
# `../reports/generated_full_dataset/` (produced by the actual tested
# pipeline) is the authoritative source for the final presentation's
# numbers; this notebook is for a fast, easy-to-read pass over the same
# data. Every number below comes from this notebook's own verified Kaggle
# run (2026-08-27, ~27 minutes on Kaggle's free CPU tier) - not a
# placeholder. Nothing here needs a GPU. See
# `../scripts/push_kaggle_kernel.sh modeling` and README.md's "Kaggle
# Workflow" section.

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
# ## Step 1: Load the data and prepare every factor we'll test
#
# Same simplified narrative features as `1_full_dataset_eda.ipynb` - see
# that notebook's Section 1 for a real preview of what a loan record
# looks like, and Sections 4-5 for what the family/agency/urgency and
# sentiment scores actually measure. Nothing new is introduced here; this
# step just re-derives the same features so this notebook can run on its
# own.

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
# ## Step 2: Split the data fairly - train on the past, test on the future
#
# **In plain terms:** to know if a model genuinely works, you have to
# test it on loans it hasn't seen before - otherwise it could just be
# "memorizing" the data instead of learning a real pattern. The fairest
# way to do that here is by **time**: train only on loans posted before
# 2024, then test purely on loans posted in 2024-2025. That mirrors
# exactly how this would be used in the real world - a model only ever
# gets to see the past when it's asked to predict something new. A random
# shuffle-based split would be too easy on the model: it could quietly
# learn from loans posted *after* the ones it's being tested on, which
# would never be possible in reality.

# %%
train_raw = valid.loc[valid["fundraisingDate_parsed"] < pd.Timestamp(HOLDOUT_START, tz="UTC")].copy()
holdout_raw = valid.loc[valid["fundraisingDate_parsed"] >= pd.Timestamp(HOLDOUT_START, tz="UTC")].copy()
print(f"Train rows: {len(train_raw)}  |  Holdout rows: {len(holdout_raw)}")

# %% [markdown]
# **What this shows.** 1,174,953 loans (2005-2023) teach the model;
# 278,887 loans posted in 2024-2025 - genuinely never seen during
# training - test it. That holdout group is about 19% of the whole
# dataset, which is a large, trustworthy sample to test on - not a lucky
# handful of loans that happened to score well.

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
# ## Step 3: Can we predict funding speed at all? Two models, compared
#
# Two different modeling approaches, both trained on the same data, so we
# can compare them fairly:
#
# - **Ridge** - a simple, straightforward model. **In plain terms:** it
#   assigns each factor (loan amount, sector, framing style, etc.) a
#   fixed weight and adds them all up - like a scorecard. Easy to trust,
#   but can't notice "this factor matters *differently* depending on
#   another factor."
# - **Boosted trees (HistGradientBoosting)** - a more flexible model.
#   **In plain terms:** instead of a fixed scorecard, it can learn rules
#   like "urgency language matters more for small loans than large ones."
#   More powerful, but harder to peek inside and see exactly *why* it
#   made a given prediction (that's what Step 5's SHAP analysis is for).
#
# Both models are asked to predict the same thing - how many days a loan
# takes to fund - and are scored the same way (**MAE**: on average, how
# many days off was the prediction; **R²**: what share of the real
# variation in funding speed the model explains).

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
# **What this shows.** Tested on loans neither model had ever seen
# (2024-2025): the simple scorecard model (Ridge) is off by **6.76
# days**, on average. The more flexible model tightens that to **5.53
# days** and explains **49.3%** of why funding speed varies from loan to
# loan (R² = 0.493) - in plain terms, roughly half the story of "why did
# this loan take as long as it did" can be explained just from what we
# know at posting time; the rest comes down to things this data doesn't
# capture (how compelling individual lenders found it, timing luck, and
# so on). The more flexible model beating the simple scorecard by over a
# day of average accuracy is itself a finding: it means funding speed
# isn't just a simple additive checklist - some factors genuinely matter
# *more in combination* than alone (e.g. narrative framing plausibly
# matters differently depending on loan size or sector, which Step 4's
# statistical model tests directly).

# %% [markdown]
# ## Step 4: A simpler, more actionable question - will it fund within a day?
#
# Predicting an exact number of days is a hard, precise task. A simpler,
# more operationally useful version: **will this loan fund within 24
# hours, yes or no?** "Flag loans unlikely to fund quickly" is a much
# more actionable signal for a real platform than a precise day-count
# guess.

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
# **What this shows.** ROC AUC of **0.905** out of a possible 1.0 (where
# 0.5 would mean the model is no better than a coin flip) - **in plain
# terms, this model is genuinely very good** at telling apart, before the
# fact, which loans are likely to fund fast and which are likely to drag
# on. That's on a real, never-seen holdout set, and on a task where the
# honest baseline is hard (recall from notebook 1: only 30-46% of loans
# actually fund within 24 hours, so simply guessing "yes" would do
# poorly). **This is the strongest, most presentation-ready practical
# result in the whole analysis**: a tool built purely from information
# available the moment a loan is posted (loan size, sector, region,
# narrative text) could reliably flag at-risk loans for extra visibility
# - a real, actionable idea for the deck, independent of whether any
# single narrative-framing choice turns out to be the reason why.

# %% [markdown]
# ## Step 5: The "why" question - what's actually linked to funding speed?
#
# **In plain terms:** Steps 3-4 built models that predict well, but a
# prediction machine doesn't tell you *why*. This step uses a classic
# statistical technique (**regression**) that instead measures, for every
# factor at once, "how much is this one thing linked to funding speed,
# once you've accounted for everything else?" - the fairest way to check
# whether narrative framing genuinely matters on its own, not just
# because it happens to travel alongside something else (like loan size).
#
# Every number this step produces is an **association**, never a cause -
# borrowers weren't randomly assigned a writing style, a loan amount, or
# a gender, so this can show "these two things move together" but never
# "one causes the other." If the model can't be fit for a technical
# reason (rare in practice), that's reported as a clear message instead
# of a crash.

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
# 1,453,840 valid loans (R² = 0.425, meaning this model explains 42.5% of
# why funding speed varies). With this much data, these are well-powered,
# trustworthy findings, not noisy guesses from a small sample. **How to
# read the numbers below: negative = associated with faster funding,
# positive = associated with slower funding**, each compared against a
# baseline group (see the reference-category printout above for exactly
# what that baseline is per factor - e.g. gender's baseline is "female",
# sector's is "Agriculture", the time-period baseline is
# "pandemic_disruption").
#
# - **Narrative framing has a real but conditional story, not a flat
#   one.** Urgency language (words like "urgent," "emergency," "right
#   now") is consistently linked to faster funding, and we can be very
#   confident this isn't a coincidence (statistically significant, p <
#   0.001) - a genuine, clean win for a simple writing choice. Agency/
#   competence language ("I run my own business," "I manage...") shows no
#   real link either way - the "sound capable and independent" hypothesis
#   doesn't hold up at this scale. Family/communal framing has no single
#   flat effect on its own - **but it interacts strongly with timing and
#   location**: the family-framing speed benefit was strongest
#   pre-pandemic and only partially came back post-pandemic - direct,
#   model-based confirmation of notebook 1's "funding dynamics
#   permanently shifted after 2020" story. It also varies sharply by
#   region: the family-framing benefit is far larger in the Middle East
#   and Central America than in North America or Asia, where it's mildly
#   *counterproductive*. **The honest headline for the deck: family
#   framing helps, but who it helps and how much depends heavily on when
#   and where the loan is posted - it is not a universal "always do this"
#   lever.**
# - **Sentiment tone shows a counterintuitive association**: a more
#   positive-sounding description is linked to *slower* funding, and
#   we're confident this isn't noise (p < 0.001). Combined with notebook
#   1's finding that descriptions are almost uniformly positive already,
#   this may simply reflect that longer, more elaborately-written pitches
#   read as more positive *and* naturally take longer to write and
#   review - this is an association, not a reason to write flatter,
#   less-positive descriptions.
# - **Structural factors remain the largest effects by far.** A loan
#   posted under a male borrower takes notably longer to fund than one
#   posted under a female borrower - the single largest factor in the
#   whole model, and a substantial, well-powered gap worth its own slide.
#   Small loans fund far faster than large ones. Loans repaid as a single
#   lump sum at the end of the term are far slower to fund than loans
#   repaid irregularly or monthly. Sector and region matter enormously
#   too - for example, Water and Education-sector loans fund dramatically
#   faster than Agriculture-sector loans, while Clothing and Retail loans
#   fund slower.

# %% [markdown]
# ## Step 6: A second opinion - what does the more powerful model rely on?
#
# **In plain terms:** Step 5's statistical model is easy to interpret,
# but by design it can only look for the specific combinations we told it
# to check (framing x period, framing x region). Step 3's more flexible
# model learned whatever patterns were actually in the data, with no such
# restriction - but on its own, it's a "black box" that doesn't explain
# itself. **SHAP** opens it back up: for every individual prediction, it
# works out exactly how much each factor pushed that prediction up or
# down, then we can average that across many loans to rank what the
# flexible model actually leaned on most. Think of it as asking the model
# directly, "what did you actually pay attention to?" - a second,
# independent check on Step 5's findings, not a replacement for them.
#
# `shap` ships in Kaggle's standard Python image; the `try/except` below
# installs it on the rare environment where it's missing (this project's
# own base requirements don't need it - it's notebook-only tooling).
# Computed on a random sample of 2,000 holdout loans for speed - a larger
# sample would take longer to compute for a negligibly different ranking.

# %%
try:
    import shap
except ImportError:
    import subprocess
    import sys

    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "shap"], check=True)
    import shap

import matplotlib.pyplot as plt  # noqa: E402

FEATURE_NAMES = preprocessor.get_feature_names_out()
shap_sample_idx = np.random.RandomState(42).choice(
    X_holdout_dense.shape[0], size=min(2_000, X_holdout_dense.shape[0]), replace=False
)
X_shap_sample = X_holdout_dense[shap_sample_idx]

tree_explainer = shap.TreeExplainer(boosted)
shap_values = tree_explainer.shap_values(X_shap_sample)

mean_abs_shap = pd.Series(np.abs(shap_values).mean(axis=0), index=FEATURE_NAMES).sort_values(ascending=False)
print("Top 15 features by mean |SHAP value| (2,000-row holdout sample, boosted model):")
print(mean_abs_shap.head(15).to_string())

fig, ax = plt.subplots(figsize=(9, 6))
top_15_sorted = mean_abs_shap.head(15).sort_values()
ax.barh(top_15_sorted.index, top_15_sorted.to_numpy(), color=plt.cm.viridis(np.linspace(0.15, 0.85, len(top_15_sorted))))
ax.set_xlabel("mean |SHAP value| (impact on predicted log funding speed)")
ax.set_title("Top 15 features by SHAP importance - boosted model")
plt.tight_layout()
plt.show()

# %% [markdown]
# **What this shows - partial agreement, one honest divergence.** This
# second, independent check confirms the top of Step 5's story: loan
# amount and repayment term are, by a wide margin, the two factors the
# flexible model relied on most - matching Step 5's largest single
# linked factor. The time period (pre-pandemic vs. not) and loan size
# also rank near the top, again agreeing with Step 5's biggest effects.
#
# **The honest divergence, worth saying plainly: narrative framing barely
# registers here.** None of the family, agency, or urgency framing scores
# make it into the top 15 factors this more flexible model actually
# relied on - only overall sentiment tone cracks the list, and even then
# only in 11th place, well behind individual sector and region
# categories. **This doesn't contradict Step 5** - urgency framing's link
# to speed, and family framing's timing/location pattern, are both
# genuinely, robustly real (very unlikely to be random noise). But it's a
# useful, honest check on what "statistically confident" actually means
# with 1.45 million loans: even a small, consistent effect becomes easy
# to detect with that much data. This second check measures something
# different - actual *size* of impact, not *confidence* that an effect is
# real - and by that measure, narrative framing is real but genuinely
# minor next to how a loan is structured. **Both things are true, and
# worth saying together on the same slide**: framing has a statistically
# solid, consistent effect (Step 5's story), and it's a modest one in
# practical terms next to loan size and repayment structure (this step's
# story) - that combined, honest picture is a stronger answer to "does
# narrative framing matter?" than either half alone.

# %% [markdown]
# ## Key takeaways for the deck
#
# 1. **Predictive ceiling**: a model using only information available the
#    moment a loan is posted explains about half the story of funding
#    speed (R² = 0.49, typically off by 5.5 days) and is genuinely very
#    good at flagging which loans will fund within 24 hours (ROC AUC
#    0.90) - strong enough to be a real, usable tool.
# 2. **Urgency framing is the cleanest narrative win** - consistently
#    linked to faster funding, no conditions or caveats needed.
# 3. **Family framing's benefit is real but conditional** on timing and
#    location - strongest before the pandemic and in the Middle East/
#    Central America, weaker or even reversed elsewhere. This nuance,
#    not a flat "always use family framing" rule, is the more honest and
#    more interesting story for a practical-implications slide.
# 4. **How a loan is structured (its size, its repayment terms, its
#    sector, its region, even the borrower's gender) matters far more
#    than how its story is written.** Narrative framing is real and
#    measurable - but a secondary lever, not the main one.
# 5. **A second, independent method agrees.** Asking the more flexible
#    model directly what it relied on (Step 6) lands on the same
#    "structure over framing" conclusion as Step 5's statistical model -
#    two different techniques agreeing is a stronger result than either
#    alone, and a good, presentable example of why "statistically
#    confident" and "practically important" aren't always the same thing.
