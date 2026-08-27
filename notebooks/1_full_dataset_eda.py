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
# [Kiva](https://www.kiva.org) is a nonprofit lending platform: everyday
# people ("lenders") each contribute a small amount toward a loan for a
# borrower somewhere in the world, usually to grow a small business or
# cover a household need. Once enough lenders chip in, the loan is fully
# funded and the money is disbursed.
#
# This analysis asks a simple question: does *how a loan's story is
# written* line up with how quickly it gets funded? Specifically, does
# leaning on family/communal appeals, competence/independence framing, or
# urgency language correlate with faster funding - and does that answer
# change depending on the economic climate or the type of loan? A loan
# that sits unfunded longer is a worse experience for the borrower
# waiting on it and a worse use of a lender's attention, so if narrative
# framing has a real, consistent link to funding speed, that's an
# actionable lever - the kind of finding that could shape guidance for
# how loan write-ups get coached. If framing turns out to barely matter
# next to more structural factors, that's just as useful to know.
#
# This notebook covers the descriptive groundwork across the complete,
# real dataset (not the 100-row illustrative sample the original proposal
# was built on); `2_full_dataset_modeling.ipynb` builds on it with
# statistical models that weigh every factor at once.

# %% [markdown]
# ## 1. Setup

# %%
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

SEED = 42

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
# ## 3. Target Variable: Funding Speed
#
# Every loan has a posted date and a fully-funded date. The gap between
# them, `funding_speed_days`, is how many days it took lenders to fully
# fund the loan - close to 0 for a same-day loan, 21 for one that took
# three weeks. A negative or missing value means the record is unusable
# and is dropped, never guessed at. `funded_within_24h` is a simpler
# yes/no version of the same measure. Both only exist for loans that
# **did eventually get funded** - this data can't speak to whether a loan
# gets funded at all, only how fast it did once it succeeded (see
# README.md's Known Limitations).

# %%
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

# %%
valid = df.loc[df["funding_speed_days"].notna() & (df["funding_speed_days"] >= 0)].copy()

print(f"Rows loaded: {len(df)}")
print(f"Rows with a valid completed outcome: {len(valid)}")
print(f"Rows excluded: {len(df) - len(valid)}")
print(f"Status among valid rows:\n{valid['status'].value_counts().to_string()}")

# %% [markdown]
# The dataset is almost entirely usable: of 1,453,846 loans, 1,453,840
# (99.9996%) have a valid, non-negative funding duration - only 6 rows
# are dropped, for a data-quality reason (the funded date preceding the
# posted date), not because they were ignored. Among the valid rows,
# 1,452,203 loans (99.89%) show status `funded` and 1,637 (0.11%) show
# `refunded` - refunded loans are kept on the same footing as funded
# ones, since a refund is a later, unrelated event; the loan still *did*
# get fully funded, which is what this notebook measures. With 14,500x
# more rows than the proposal-week sample, this near-total coverage means
# the findings below aren't an artifact of small-sample noise.

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.histplot(valid["funding_speed_days"], kde=True, bins=50, color=plt.cm.viridis(0.25), ax=axes[0])
axes[0].set_title("Funding speed (days) - valid outcomes, full dataset")

sns.histplot(valid["log_funding_speed"], kde=True, bins=50, color=plt.cm.viridis(0.65), ax=axes[1])
axes[1].set_title("log(1 + funding speed) - valid outcomes")
plt.tight_layout()
plt.show()

# %% [markdown]
# Most loans fund very quickly (the tall bar near 0 on the left), with a
# long tail of slower loans stretching out for weeks. The right chart
# applies a log transform, which pulls that long tail in so the
# distribution looks closer to a symmetric bell shape - modeling
# techniques (used in `2_full_dataset_modeling.ipynb`) tend to perform
# better on data shaped like the right chart than the heavily skewed
# shape on the left; both charts describe the same underlying pattern.

# %% [markdown]
# ## 4. Categorical Insight: Funding Speed by Period
#
# Three eras, split by the year the loan started raising funds:
# `pre_pandemic` (through 2019), `pandemic_disruption` (2020-2021), and
# `post_pandemic` (2022 onward) - checking whether COVID-era disruption
# to global lending and logistics shows up as slower funding, and whether
# it has recovered since.

# %%
period_counts = df["analysis_period"].value_counts(dropna=False).sort_index()
print("Rows per analysis period:")
print(period_counts.to_string())

within_24h_by_period = valid.dropna(subset=["funded_within_24h"]).groupby(
    "analysis_period", observed=True
)["funded_within_24h"].mean()
print("\nShare funded within 24 hours, by period:")
print(within_24h_by_period.to_string())

# %%
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
# The headline finding of this notebook: the share of loans funded within
# 24 hours nearly halved and never recovered - **46.0% pre-pandemic →
# 30.3% during pandemic disruption → 30.0% post-pandemic.** Before 2020,
# almost half of all loans were fully funded within a day of posting;
# since 2020, that's dropped to under a third, and it has stayed there,
# years after the disruption itself ended. This isn't a small blip
# either - 589,823 loans fall in the "before" group and 565,474 in the
# "after" group, so it isn't a handful of unusual loans skewing the
# picture. Something structural changed about how this marketplace funds
# loans around 2020, and it never bounced back. That raises a natural
# follow-up question the modeling notebook tests directly: if the overall
# pace of funding shifted this much, did the value of narrative framing
# shift with it?

# %% [markdown]
# ## 5. Numerical & Text Features: Narrative Framing and Sentiment
#
# Each loan description is scored on three persuasion styles, each
# grounded in research on what makes an ask persuasive:
#
# - **Family/communal** - mentions of children, family roles (mother,
#   father, spouse) - a "this affects real people you can relate to"
#   appeal.
# - **Agency/competence** - mentions of deciding, managing, running a
#   business independently - signals capability rather than need.
# - **Urgency** - explicit urgency/emergency language ("today," "right
#   now," "before it's too late") - a time-pressure appeal.
#
# Each style is counted as a rate per 100 words rather than a raw count,
# so a longer description doesn't automatically score as "more urgent"
# just because it has more words.

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
# Alongside framing, each description also gets a sentiment score from
# **VADER**, a well-established, off-the-shelf tool that reads text and
# returns a single score from -1 (very negative) to +1 (very positive) -
# the same idea as a star rating summarizing a review. Scored on a random
# sample of 20,000 descriptions for speed in this quick-read notebook
# (the project's tested pipeline scores every row).

# %%
import nltk  # noqa: E402

try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)

from nltk.sentiment.vader import SentimentIntensityAnalyzer  # noqa: E402

analyzer = SentimentIntensityAnalyzer()
sentiment_sample = valid.sample(min(20_000, len(valid)), random_state=SEED).copy()
sentiment_sample["sentiment_compound"] = sentiment_sample["description"].fillna("").apply(
    lambda text: analyzer.polarity_scores(text)["compound"]
)

print("Sentiment (compound score) summary, 20K-row sample:")
print(sentiment_sample["sentiment_compound"].describe().to_string())

# %% [markdown]
# Kiva loan descriptions are overwhelmingly positive in tone: the average
# score is 0.78 out of a possible 1.0, and the typical (median)
# description scores an even higher 0.88; even the more modestly-toned
# quarter of descriptions still scores a strongly positive 0.74. Almost
# every description on this platform is written in an upbeat, hopeful
# voice, with very little genuinely neutral or negative writing. That's a
# ceiling effect worth noting: when nearly everything already sits near
# the top of the scale, sentiment has little room left to vary from loan
# to loan, which matters when interpreting the sentiment result in the
# modeling notebook (it's effectively comparing "very positive" to
# "extremely positive," not "negative" to "positive").

# %% [markdown]
# ## 6. Feature Correlations with Funding Speed
#
# A correlation is a score from -1 to +1 for whether two things tend to
# move together: 0 means no relationship, +1 means they consistently rise
# together, -1 means one falls as the other rises. This section checks
# the raw, one-at-a-time correlation between funding speed and each of
# the three framing styles above, the loan amount, and the repayment term
# (how long the borrower has to repay).

# %%
narrative_cols = ["family_mentions_per_100_words", "agency_mentions_per_100_words", "urgency_mentions_per_100_words"]
valid["log_loan_amount"] = np.log1p(valid["loanAmount"])
structural_cols = ["log_loan_amount", "lenderRepaymentTerm"]

corr_table = valid[narrative_cols + structural_cols + ["funding_speed_days"]].corr()["funding_speed_days"].drop("funding_speed_days")
print("Correlation with funding speed (days):")
print(corr_table.sort_values().to_string())

# %% [markdown]
# In these simple, one-at-a-time comparisons, loan structure dominates
# over narrative framing: larger loan amounts (r = +0.43) and longer
# repayment terms (r = +0.28) are the strongest correlates of *slower*
# funding - a bigger ask naturally takes longer to fill. The three
# framing styles barely register by comparison, an order of magnitude
# weaker: family framing r = -0.019 (a whisper of a link to faster
# funding), urgency r = +0.010 (essentially no relationship either way),
# agency framing r = +0.059 (a whisper of a link to *slower* funding -
# the opposite of what a naive "sound confident and it'll fund faster"
# assumption would predict). This doesn't mean framing doesn't matter at
# all - a simple one-at-a-time correlation can't separate framing's own
# effect from other things that happen to travel together with it (e.g.
# larger loans might also just happen to be written in a different
# style). Untangling that is exactly what the statistical model in
# `2_full_dataset_modeling.ipynb` is for, and its result is more nuanced
# than a flat "framing doesn't matter": family framing's link to speed
# turns out to depend heavily on when and where the loan was posted, not
# on one single, constant effect.

# %% [markdown]
# ## 7. Key Findings
#
# 1. **The dataset is complete and clean** - 1,453,840 of 1,453,846 loans
#    (99.9996%) have a usable funding-speed outcome, so nothing here is
#    limited by a small or messy sample.
# 2. **Funding got permanently slower after 2019.** The share of loans
#    funded within 24 hours fell from 46% to about 30% during the
#    pandemic and has never recovered, across hundreds of thousands of
#    loans in every period - the single most concrete finding here.
# 3. **Loan descriptions are written in an almost uniformly upbeat tone**
#    (typical sentiment score 0.88 out of 1.0) - a ceiling effect that
#    limits how much "positivity" alone can explain.
# 4. **How a loan is structured (its size, its repayment terms) - not how
#    its story is written - is the strongest simple driver of funding
#    speed.** Narrative framing isn't a dead end, but its real story is
#    conditional on period, region, and sector, not a flat "write it this
#    way and it'll always fund faster" rule - see the modeling notebook
#    for the model that tests that directly.
