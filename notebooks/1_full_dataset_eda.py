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
# **Self-contained**: uses only standard public packages (pandas, numpy,
# matplotlib, seaborn, nltk) - no import of this repo's own `src/`
# package. This is a deliberately simpler, streamlined re-implementation
# of the same *ideas* the tested `src/` pipeline uses (chronological
# periods, per-100-word framing rates, VADER sentiment), not a port of
# its exact code - so treat this notebook's numbers as a fast, portable
# read on the data, and `../reports/generated_full_dataset/` (produced by
# the actual tested pipeline, `python3 -m src.run_analysis`) as the
# authoritative source for anything going into the final presentation.
#
# Designed to run as a private Kaggle kernel with internet enabled (only
# to fetch the public NLTK VADER lexicon - no other network access) -
# see `../scripts/push_kaggle_kernel.sh eda` and README.md's "Kaggle
# Workflow" section.

# %%
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

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

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["font.size"] = 12

# %% [markdown]
# ## 1. Load and derive the target
#
# `funding_speed_days` = time from posting to fully funded. A negative or
# missing value means the loan record is unusable for this analysis
# (dropped, never imputed). `funded_within_24h` is the secondary binary
# outcome. Both outcomes are only defined among loans that **were
# eventually funded** - this cannot speak to whether a loan gets funded
# at all, only how fast it did once it was (see README.md's Known
# Limitations).

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
df["funded_within_24h"] = (df["funding_speed_days"] <= 1).astype("Int64")

year = fundraising.dt.year
df["analysis_period"] = pd.cut(
    year, bins=[-np.inf, 2019, 2021, np.inf],
    labels=["pre_pandemic", "pandemic_disruption", "post_pandemic"],
)

valid = df.loc[df["funding_speed_days"].notna() & (df["funding_speed_days"] >= 0)].copy()

print(f"Rows loaded: {len(df)}")
print(f"Rows with a valid completed outcome: {len(valid)}")
print(f"Rows excluded: {len(df) - len(valid)}")
print(f"Status among valid rows:\n{valid['status'].value_counts().to_string()}")

# %% [markdown]
# **Insight cell** - fill in after running.

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.histplot(valid["funding_speed_days"], kde=True, bins=50, color="darkblue", ax=axes[0])
axes[0].set_title("Funding speed (days) - valid outcomes, full dataset")

sns.histplot(valid["log_funding_speed"], kde=True, bins=50, color="teal", ax=axes[1])
axes[1].set_title("log(1 + funding speed) - valid outcomes")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 2. Funding behavior by period

# %%
period_counts = df["analysis_period"].value_counts(dropna=False).sort_index()
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

within_24h_by_period.astype(float).plot(kind="bar", color="darkorange", ax=axes[1])
axes[1].set_title("Share funded within 24 hours, by period")
axes[1].tick_params(axis="x", rotation=0)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 3. Narrative framing (simplified: 3 theory-guided keyword rates)
#
# Vectorized `pandas.Series.str.count` over a compiled regex - no
# per-row Python loop. Three theoretically distinct framing dimensions
# (communal/family, agentic/competence, urgency), normalized per 100
# words for comparability across description lengths - same theoretical
# grounding as the tested pipeline, simpler patterns.

# %%
FAMILY_PATTERN = re.compile(r"\b(child|children|family|son|daughter|mother|father|wife|husband|school)\b", re.I)
AGENCY_PATTERN = re.compile(r"\b(decide|plan|manage|responsible|hard.?working|independent|own|run|lead)\w*\b", re.I)
URGENCY_PATTERN = re.compile(r"\b(urgent|immediately|emergency|crisis|desperate|asap|quickly)\w*\b", re.I)

description = valid["description"].fillna("")
word_count = description.str.split().str.len().clip(lower=1)


def _rate_per_100_words(pattern: re.Pattern, text: pd.Series, words: pd.Series) -> pd.Series:
    return text.str.count(pattern) / words * 100


valid["family_mentions_per_100_words"] = _rate_per_100_words(FAMILY_PATTERN, description, word_count)
valid["agency_mentions_per_100_words"] = _rate_per_100_words(AGENCY_PATTERN, description, word_count)
valid["urgency_mentions_per_100_words"] = _rate_per_100_words(URGENCY_PATTERN, description, word_count)

# %% [markdown]
# ## 4. Sentiment (VADER, public NLTK corpus)
#
# Requires internet once, to fetch the lexicon (not required if it's
# already cached in this environment).

# %%
import nltk  # noqa: E402

try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)

from nltk.sentiment.vader import SentimentIntensityAnalyzer  # noqa: E402

analyzer = SentimentIntensityAnalyzer()
# Batched, not one .apply() call per row against the full 1.45M rows -
# sampled for speed in this descriptive-only notebook (the tested
# pipeline scores every row; see run_analysis's output for that).
sentiment_sample = valid.sample(min(20_000, len(valid)), random_state=42).copy()
sentiment_sample["sentiment_compound"] = sentiment_sample["description"].fillna("").apply(
    lambda text: analyzer.polarity_scores(text)["compound"]
)

print("Sentiment (compound score) summary, 20K-row sample:")
print(sentiment_sample["sentiment_compound"].describe().to_string())

# %% [markdown]
# ## 5. Structural vs. narrative correlation with funding speed

# %%
narrative_cols = ["family_mentions_per_100_words", "agency_mentions_per_100_words", "urgency_mentions_per_100_words"]
valid["log_loan_amount"] = np.log1p(valid["loanAmount"])
structural_cols = ["log_loan_amount", "lenderRepaymentTerm"]

corr_table = valid[narrative_cols + structural_cols + ["funding_speed_days"]].corr()["funding_speed_days"].drop("funding_speed_days")
print("Correlation with funding speed (days):")
print(corr_table.sort_values().to_string())

# %% [markdown]
# **Insight cell** - fill in after running: how do these full-data
# numbers compare with the tested pipeline's already-verified findings in
# `docs/superpowers/collab-logs/2026-08-17-hackathon-upgrade-collab-log.md`
# and `../reports/generated_full_dataset/`? Report agreement/disagreement
# honestly - this notebook's simplified framing patterns and sampled
# sentiment are not expected to match exactly, only directionally.
