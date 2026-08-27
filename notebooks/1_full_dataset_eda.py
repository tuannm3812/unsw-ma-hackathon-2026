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
# # Kiva Loans: Full-Dataset EDA (1.45M loans)
#
# **Research question.** When a Kiva loan description leans on family/
# communal appeals, competence/agency framing, or urgency language, is
# that associated with getting funded faster - and does the association
# hold steady, or does it shift with the economic backdrop (pre-pandemic
# vs. pandemic-disruption vs. post-pandemic) and with the sector the loan
# is in? This notebook is the descriptive first pass over the real,
# complete dataset (not the 100-row illustrative sample the original
# proposal was built on) - it establishes what the data actually looks
# like before `2_full_dataset_modeling.ipynb` fits models to it.
#
# **Why this matters.** Kiva is a marketplace: a loan that funds slowly
# sits unfunded longer, is more exposed to lapsing, and represents a
# borrower waiting longer for capital. If narrative framing has a real,
# consistent association with funding speed, that's an actionable lever
# for how loan write-ups get coached or triaged - if it doesn't, or is
# swamped by structural factors like loan size, that's just as important
# a finding.
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
# Every insight cell below quotes the real output from this notebook's
# own verified Kaggle run (2026-08-27), not a placeholder.
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

sns.set_theme(style="whitegrid", palette="viridis")
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
# **What this shows.** The dataset is almost entirely usable: of
# 1,453,846 loans, 1,453,840 (99.9996%) have a valid, non-negative
# funding duration - only 6 rows are dropped, and those 6 are excluded
# for a data-quality reason (a negative duration, i.e. `raisedDate`
# before `fundraisingDate`), not because the analysis chose to ignore
# them. Among the valid rows, 1,452,203 loans (99.89%) were `funded` and
# 1,637 (0.11%) were `refunded` - refunded loans are kept on the same
# footing as funded ones here, because a refund is a later, unrelated
# event (a completed loan that was later cancelled/returned); the loan
# still *did* complete its funding round, which is what
# `funding_speed_days` measures. This near-total coverage is exactly why
# the full-dataset run matters for the final deck: with 14,500x more
# rows than the proposal-week sample, findings here are not an artifact
# of small-sample noise.

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.histplot(valid["funding_speed_days"], kde=True, bins=50, color=plt.cm.viridis(0.25), ax=axes[0])
axes[0].set_title("Funding speed (days) - valid outcomes, full dataset")

sns.histplot(valid["log_funding_speed"], kde=True, bins=50, color=plt.cm.viridis(0.65), ax=axes[1])
axes[1].set_title("log(1 + funding speed) - valid outcomes")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 2. Funding behavior by period
#
# Three eras, split by the year the loan started raising funds:
# **pre_pandemic** (through 2019), **pandemic_disruption** (2020-2021),
# and **post_pandemic** (2022 onward). The question: did COVID-era
# disruption to global lending/logistics show up as slower funding, and
# if so, has it recovered?

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
    hue="analysis_period", legend=False, palette="viridis", ax=axes[0],
)
axes[0].set_title("Funding speed by analysis period")

within_24h_by_period.astype(float).plot(
    kind="bar", color=plt.cm.viridis(np.linspace(0.2, 0.8, len(within_24h_by_period))), ax=axes[1]
)
axes[1].set_title("Share funded within 24 hours, by period")
axes[1].tick_params(axis="x", rotation=0)
plt.tight_layout()
plt.show()

# %% [markdown]
# **What this shows - the headline finding of this notebook.** The share
# of loans funded within 24 hours nearly *halved* and never recovered:
# **46.0% pre-pandemic → 30.3% during pandemic disruption → 30.0%
# post-pandemic.** Funding speed didn't just dip during 2020-2021 and
# bounce back - it settled at a permanently slower baseline, even years
# after the disruption itself ended (589,823 pre-pandemic loans vs.
# 565,474 post-pandemic loans in this dataset, so this isn't a small,
# noisy post-pandemic bucket either). That's a genuinely useful,
# concrete story for the deck: something structural changed about the
# marketplace's funding dynamics around 2020, and it persisted. It also
# motivates the `analysis_period` interaction terms in the explanatory
# model in notebook 2 - if the *level* of funding speed shifted this
# much, the *association* between narrative framing and speed plausibly
# shifted too, which is exactly what that model tests.

# %% [markdown]
# ## 3. Narrative framing (simplified: 3 theory-guided keyword rates)
#
# Vectorized `pandas.Series.str.count` over a compiled regex - no
# per-row Python loop. Three theoretically distinct framing dimensions,
# each grounded in prosocial-giving and persuasion research, normalized
# per 100 words for comparability across description lengths (a longer
# description isn't "more urgent" just because it's longer):
#
# - **Family/communal** - references to children, family roles (mother,
#   father, spouse) - the classic "identifiable victim" / relatable-need
#   framing.
# - **Agency/competence** - references to deciding, managing, running a
#   business independently - signals the borrower's capability rather
#   than their need.
# - **Urgency** - explicit urgency/emergency language - a time-pressure
#   appeal.
#
# Same theoretical grounding as the tested pipeline, simpler patterns.

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
# already cached in this environment). Scored on a 20,000-row random
# sample for speed in this descriptive-only notebook - the tested
# pipeline scores every row (see `run_analysis`'s output for that).

# %%
import nltk  # noqa: E402

try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)

from nltk.sentiment.vader import SentimentIntensityAnalyzer  # noqa: E402

analyzer = SentimentIntensityAnalyzer()
sentiment_sample = valid.sample(min(20_000, len(valid)), random_state=42).copy()
sentiment_sample["sentiment_compound"] = sentiment_sample["description"].fillna("").apply(
    lambda text: analyzer.polarity_scores(text)["compound"]
)

print("Sentiment (compound score) summary, 20K-row sample:")
print(sentiment_sample["sentiment_compound"].describe().to_string())

# %% [markdown]
# **What this shows.** Kiva loan descriptions are overwhelmingly
# positive in tone: mean compound score **0.78** (scale runs -1 to +1),
# median **0.88**, and the 25th percentile is still a strongly positive
# **0.74**. Fewer than a quarter of descriptions read as anything but
# clearly positive. That's a **ceiling effect worth flagging for the
# deck**: because almost every description is already very positive,
# sentiment has limited room to vary - which matters when interpreting
# any sentiment coefficient in the explanatory model in notebook 2 (a
# small, well-populated positive tail, not a balanced spread from
# negative to positive).

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
# **What this shows.** In simple bivariate terms, **structural loan
# characteristics dominate**: larger loan amounts (r = **+0.43**) and
# longer repayment terms (r = **+0.28**) are the strongest correlates of
# slower funding - unsurprising, a bigger ask takes longer to fill.
# Narrative framing correlates are an order of magnitude weaker: family
# framing r = **-0.019** (very weakly faster), urgency r = **+0.010**
# (essentially flat), agency framing r = **+0.059** (weakly *slower*,
# the opposite of what a naive "confidence framing helps" hypothesis
# would predict). None of that means framing doesn't matter - a raw
# correlation can't separate framing's own effect from the fact that,
# say, larger loans might also happen to use different language. That
# separation is exactly what the multivariate explanatory model in
# `2_full_dataset_modeling.ipynb` is for, and its real result there is
# more nuanced: family framing's association with speed turns out to
# depend on *when* and *where* the loan was posted, not on a single flat
# effect - see that notebook's own findings section.

# %% [markdown]
# ## Key takeaways for the deck
#
# 1. **The dataset is complete and clean** - 1,453,840 of 1,453,846 loans
#    (99.9996%) have a usable funding-speed outcome.
# 2. **Funding got permanently slower after 2019** - the share funded
#    within 24 hours fell from 46.0% to ~30% during the pandemic and has
#    stayed there ever since, across hundreds of thousands of loans in
#    every period. This is the single most concrete, presentation-ready
#    finding in this notebook.
# 3. **Descriptions are almost uniformly positive in tone** (median VADER
#    compound 0.88) - a ceiling effect that limits how much sentiment
#    alone can explain.
# 4. **Loan size and repayment structure - not narrative framing - are
#    the dominant simple correlates of funding speed.** Framing's real
#    story is conditional (on period, on region, on sector), not a flat
#    "mention family more, fund faster" effect - see notebook 2 for the
#    model that actually tests that.
