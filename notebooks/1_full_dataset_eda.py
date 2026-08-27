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
# **Who this notebook is for.** No data science background required. Every
# statistic below is followed by a plain-language explanation of what it
# means and why it matters. Technical terms are explained the first time
# they're used (look for **"In plain terms"**).
#
# **The research question, in one sentence:** when a Kiva loan write-up
# talks about family, sounds capable/independent, or sounds urgent, does
# that loan get funded by lenders faster - and does the answer change
# depending on the economic climate or the type of loan?
#
# **Research question (full version).** When a Kiva loan description leans
# on family/communal appeals, competence/agency framing, or urgency
# language, is that associated with getting funded faster - and does the
# association hold steady, or does it shift with the economic backdrop
# (pre-pandemic vs. pandemic-disruption vs. post-pandemic) and with the
# sector the loan is in? This notebook is the descriptive first pass over
# the real, complete dataset (not the 100-row illustrative sample the
# original proposal was built on) - it establishes what the data actually
# looks like before `2_full_dataset_modeling.ipynb` fits models to it.
#
# **Why this matters for a marketer.** Kiva is a marketplace: a loan that
# sits unfunded longer is a worse experience for the borrower waiting on
# it, and a worse use of a lender's attention. If *how a loan's story is
# written* has a real, consistent link to how fast it gets funded, that's
# a genuinely actionable lever - the kind of finding you could turn into
# writing guidance for how loans get described. If it turns out framing
# barely matters next to more structural things (like the loan amount),
# that's just as useful to know before investing in a "better copywriting"
# initiative.
#
# **How to read this notebook.** Each numbered section below does three
# things, in order: (1) runs some analysis, (2) prints or plots the raw
# result, (3) explains **"What this shows"** in plain language immediately
# after. You can skim the numbered headers and the "What this shows"
# paragraphs alone and get the full story without reading any code.
#
# **A technical note** (safe to skip): this notebook is self-contained -
# standard public packages only (pandas, numpy, matplotlib, seaborn, nltk)
# - and is a deliberately simpler, streamlined re-implementation of the
# same *ideas* the project's tested internal pipeline uses, not a port of
# its exact code. `../reports/generated_full_dataset/` (produced by the
# actual tested pipeline) is the authoritative source for anything going
# into the final presentation; treat this notebook as a fast, portable,
# easy-to-read read on the same data. Every number below comes from this
# notebook's own verified Kaggle run (2026-08-27), not a placeholder.
# Designed to run as a private Kaggle kernel with internet enabled (only
# to fetch the public NLTK sentiment dictionary - no other network access)
# - see `../scripts/push_kaggle_kernel.sh eda` and README.md's "Kaggle
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
# ## 1. What does the data actually look like?
#
# [Kiva](https://www.kiva.org) is a nonprofit lending platform: everyday
# people ("lenders") each put in a small amount of money to fund a loan
# for a borrower somewhere in the world, usually to grow a small business
# or cover a household need. Once enough lenders chip in, the loan is
# "fully funded" and the money is disbursed. **Every row in this dataset
# is one loan.**

# %%
# The pickle is a list of row dicts, not a directly-pickled DataFrame
# (pd.read_pickle would raise) - a plain stdlib pickle.load handles both
# shapes, no custom package needed. Loaded once here and reused for
# everything below - the full dataset is 1.6GB, so this is the notebook's
# one real "wait" moment.
import pickle  # noqa: E402

with open(DATA_PATH, "rb") as handle:
    _raw = pickle.load(handle)
df = pd.DataFrame(_raw) if isinstance(_raw, list) else _raw
print(f"Shape: {df.shape[0]:,} loans x {df.shape[1]} raw columns")

# %%
# A real sample of rows, restricted to columns that describe the *loan*
# rather than the *borrower* - deliberately excludes name/id/image_url
# and free-text/exact-timestamp fields that can still identify a real
# person even without a name column (the raw description usually opens
# with the borrower's name and a short biography; an exact date is
# specific enough to cross-reference a real loan on Kiva's own site).
# This project only ever analyzes aggregate patterns, never individual
# borrowers, so a preview shouldn't redistribute identifiable rows just
# because the source data happens to include them.
preview_cols = [
    "gender", "borrowerCount", "loanAmount", "sector", "activity",
    "region", "country_name", "repaymentInterval",
]
df[preview_cols].head(8)

# %% [markdown]
# **What this shows.** Each row is one real loan, with the loan and
# borrower attributes you'd expect: who it's for (`gender`,
# `borrowerCount`), how much (`loanAmount`, in USD), what it's for
# (`sector`, `activity`), where (`region`, `country_name`), and the
# repayment structure (`repaymentInterval`). Two more field groups exist
# in the real data but aren't shown row-by-row above, for the privacy
# reason in the code comment: a free-text description written for lenders
# (illustrative opening only, not an actual row - *"Maria is a
# hardworking small-business owner who has run her grocery store for five
# years and is requesting a loan to buy more stock."*), and two dates -
# when the loan was **posted** and when it became **fully funded**. The
# gap between those two dates is this entire notebook's subject: how many
# days it takes a loan to get funded, and what's associated with that
# being faster or slower.

# %% [markdown]
# ## 2. Turning "two dates" into "funding speed"
#
# **In plain terms:** every loan has a posted date and a fully-funded
# date. Subtract one from the other and you get `funding_speed_days` -
# literally, how many days it took lenders to fully fund that loan. A
# loan that funded the same day it posted scores close to 0; one that
# took three weeks scores 21. A negative or missing value means the
# record is unusable (bad data - dropped, never guessed at). This
# notebook also tracks a simpler yes/no version: did the loan fund within
# 24 hours (`funded_within_24h`)? Both measures only exist for loans that
# **did eventually get funded** - this data can't tell us whether a loan
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

valid = df.loc[df["funding_speed_days"].notna() & (df["funding_speed_days"] >= 0)].copy()

print(f"Rows loaded: {len(df)}")
print(f"Rows with a valid completed outcome: {len(valid)}")
print(f"Rows excluded: {len(df) - len(valid)}")
print(f"Status among valid rows:\n{valid['status'].value_counts().to_string()}")

# %% [markdown]
# **What this shows.** The dataset is almost entirely usable: of
# 1,453,846 loans, 1,453,840 (99.9996%) have a valid, non-negative
# funding duration - only 6 rows are dropped, and those 6 are excluded
# for a data-quality reason (a negative duration, i.e. the "funded" date
# came before the "posted" date - clearly a data error), not because the
# analysis chose to ignore them. Among the valid rows, 1,452,203 loans
# (99.89%) show status `funded` and 1,637 (0.11%) show `refunded` -
# refunded loans are kept on the same footing as funded ones here,
# because a refund is a later, unrelated event (a completed loan that was
# later cancelled/returned); the loan still *did* get fully funded, which
# is the thing this notebook measures. This near-total coverage is
# exactly why the full-dataset run matters for the final deck: with
# 14,500x more rows than the proposal-week sample, findings here are not
# an artifact of small-sample noise.

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.histplot(valid["funding_speed_days"], kde=True, bins=50, color=plt.cm.viridis(0.25), ax=axes[0])
axes[0].set_title("Funding speed (days) - valid outcomes, full dataset")

sns.histplot(valid["log_funding_speed"], kde=True, bins=50, color=plt.cm.viridis(0.65), ax=axes[1])
axes[1].set_title("log(1 + funding speed) - valid outcomes")
plt.tight_layout()
plt.show()

# %% [markdown]
# **What this shows.** The left chart is the raw funding speed in days -
# most loans fund very quickly (the tall bar near 0), with a long tail of
# slower loans stretching out for weeks. The right chart is the same data
# after a **log transform** (`log_funding_speed`). **In plain terms:** a
# log transform squashes that long tail down so the chart looks more like
# an even, symmetric bell shape - modeling techniques (used in notebook 2)
# tend to work better on data shaped like the right chart than the
# heavily lopsided shape on the left. You don't need to interpret the
# log-scale numbers themselves; just know it's the same story, rescaled
# for the math to work better later.

# %% [markdown]
# ## 3. Did funding speed change around the pandemic?
#
# Three eras, split by the year the loan started raising funds:
# **pre_pandemic** (through 2019), **pandemic_disruption** (2020-2021),
# and **post_pandemic** (2022 onward). The question: did COVID-era
# disruption to global lending/logistics show up as slower funding, and
# if so, has it recovered since?

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
# post-pandemic.** In plain terms: before 2020, almost half of all loans
# were fully funded within a day of posting. Since 2020, that's dropped
# to less than a third - and it has **stayed there**, years after the
# pandemic disruption itself ended. This isn't a small blip either:
# 589,823 loans fall in the "before" group and 565,474 in the "after"
# group, so it's not a handful of unusual loans skewing the picture.
# That's a genuinely useful, concrete story for the deck: something
# structural changed about how this marketplace funds loans around 2020,
# and it never bounced back. It also raises a natural follow-up question
# that notebook 2 tests directly: if the overall *pace* of funding
# shifted this much, did the *value of good loan-write-up framing* shift
# with it?

# %% [markdown]
# ## 4. Reading loan descriptions for narrative "framing"
#
# **In plain terms:** this section counts how often each loan's
# description uses words from three different persuasion styles, then
# checks whether using more of those words lines up with faster funding.
# Three styles, each grounded in research on what makes an ask persuasive:
#
# - **Family/communal** - mentions of children, family roles (mother,
#   father, spouse) - a classic "this affects real people you can relate
#   to" appeal.
# - **Agency/competence** - mentions of deciding, managing, running a
#   business independently - signals "I'm capable," not "I'm needy."
# - **Urgency** - explicit urgency/emergency language - a time-pressure
#   appeal ("today," "right now," "before it's too late").
#
# Each style is counted as a **rate per 100 words** rather than a raw
# count, so a longer description doesn't automatically score as "more
# urgent" just because it has more words in total - this makes
# descriptions of different lengths fairly comparable to each other.

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
# ## 5. Scoring how positive each description sounds
#
# **In plain terms:** this uses a well-known, off-the-shelf tool called
# VADER - think of it as an automated "mood detector" for text. It reads
# a description and outputs a single "sentiment" score from **-1 (very
# negative)** to **+1 (very positive)**, the same way a simple star
# rating summarizes a review. Scored on a random sample of 20,000
# descriptions for speed in this quick-read notebook (the project's
# tested pipeline scores every single row).

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
# positive in tone: the average score is **0.78** out of a possible 1.0,
# and the typical (median) description scores an even higher **0.88**.
# Even the more modestly-toned quarter of descriptions (25th percentile)
# still score a strongly positive **0.74**. In plain terms: almost every
# description on this platform is written in an upbeat, hopeful voice -
# there's very little genuinely neutral or negative writing here. That's
# worth flagging for the deck as a **ceiling effect**: when nearly
# everything is already near the top of the scale, sentiment doesn't have
# much room left to vary from loan to loan - which matters when
# interpreting any sentiment-related result in notebook 2's model (it's
# comparing "very positive" to "extremely positive," not "negative" to
# "positive").

# %% [markdown]
# ## 6. Which of these signals actually tracks with funding speed?
#
# **In plain terms:** a **correlation** is a simple score from -1 to +1
# that says whether two things tend to move together. 0 means no
# relationship at all; +1 means "when one goes up, the other always goes
# up too"; -1 means "when one goes up, the other always goes down." This
# section checks the raw, one-at-a-time correlation between funding speed
# and each of: the three framing styles above, the loan amount, and the
# repayment term (how long the borrower has to repay).

# %%
narrative_cols = ["family_mentions_per_100_words", "agency_mentions_per_100_words", "urgency_mentions_per_100_words"]
valid["log_loan_amount"] = np.log1p(valid["loanAmount"])
structural_cols = ["log_loan_amount", "lenderRepaymentTerm"]

corr_table = valid[narrative_cols + structural_cols + ["funding_speed_days"]].corr()["funding_speed_days"].drop("funding_speed_days")
print("Correlation with funding speed (days):")
print(corr_table.sort_values().to_string())

# %% [markdown]
# **What this shows.** In these simple, one-at-a-time comparisons,
# **loan structure dominates over narrative framing**: larger loan
# amounts (r = **+0.43**) and longer repayment terms (r = **+0.28**) are
# the strongest correlates of *slower* funding - which makes intuitive
# sense, a bigger ask naturally takes longer to fill. The three framing
# styles barely register by comparison - an order of magnitude weaker:
# family framing r = **-0.019** (a whisper of a link to *faster*
# funding), urgency r = **+0.010** (essentially no relationship either
# way), agency framing r = **+0.059** (a whisper of a link to *slower*
# funding - the opposite of what a naive "sound confident and it'll fund
# faster" assumption would predict). This doesn't mean framing doesn't
# matter at all - a simple one-at-a-time correlation can't separate
# framing's own effect from other things that happen to travel together
# with it (e.g. larger loans might also just happen to be written in a
# different style). Untangling that is exactly what the full statistical
# model in `2_full_dataset_modeling.ipynb` is for - and its real result
# is more nuanced than a flat "framing doesn't matter": family framing's
# link to speed turns out to depend heavily on *when* and *where* the
# loan was posted, not on one single, constant effect. See that
# notebook's own findings for the full story.

# %% [markdown]
# ## Key takeaways for the deck
#
# 1. **The dataset is complete and clean** - 1,453,840 of 1,453,846 loans
#    (99.9996%) have a usable funding-speed outcome, so nothing here is
#    limited by a small or messy sample.
# 2. **Funding got permanently slower after 2019 - the single most
#    concrete, presentation-ready finding here.** The share of loans
#    funded within 24 hours fell from 46% to about 30% during the
#    pandemic and has **never recovered**, across hundreds of thousands
#    of loans in every period.
# 3. **Loan descriptions are written in an almost uniformly upbeat tone**
#    (typical sentiment score 0.88 out of 1.0) - there's a ceiling effect
#    here that limits how much "positivity" alone can explain.
# 4. **How a loan is structured (its size, its repayment terms) - not how
#    its story is written - is the strongest simple driver of funding
#    speed.** Narrative framing isn't a dead end, but its real story is
#    conditional (it depends on the period, the region, the sector), not
#    a flat "write it this way and it'll always fund faster" rule - see
#    notebook 2 for the model that actually tests that in detail.
