<!-- Markdown rendering of docs/presentation/deck_content.html (the "Beyond a Good Story" artifact).
     The HTML file is the styled original; this file is the same content for reading on GitHub. -->

Deck content brief · UNSW Marketing Analytics Hackathon 2026 · Team Cultural Blend

# Beyond a Good Story

When — and for whom — does a persuasive loan story actually speed up funding? Slide-ready content, pulled from the verified full-dataset analysis, for the final presentation.

**Deadline** 2026-09-03, 5:00pm Sydney **Format** Slides only **Time limit** 10 min presenting, then 10 min Q&A **Judging** Panel 80% + Audience vote 20%

**Format update from the organizer (2026-08-28):** presentation is strictly timed at 10 minutes, cut off when time is up. **No background/intro slide** — the organizer introduces Kiva and the dataset to everyone, so don't spend a slide on it. Explicit instruction: **quality over quantity of findings.** Below, Slide 3 is trimmed to methods-only for this reason, and Slides 7 and 9 are marked as trim candidates if the deck needs to shrink further to comfortably fit 10 minutes.

## §0 · Research question coverage

Checked against the proposal's central and supporting questions before writing a single slide — every question the project committed to has a real, verified answer.

- Central question — **Answered**
- Framing vs. structure — **Answered**
- Segment differences — **Answered**
- Pandemic-era shift — **Answered**
- Predictive value — **Answered**

**One thing to know before building slides:** two sets of numbers exist in this repo — the `authoritative` full pipeline (`reports/generated_full_dataset/`) and the `notebook` versions (self-contained Kaggle notebooks, built for readability). They agree directionally on most findings, but they do **not** always agree on statistical significance — two results (family framing in Asia, and sentiment tone) are significant in one pipeline and not the other. Where they disagree, this brief reports the disagreement rather than picking a side. **Use the authoritative numbers on slides** — the reference table at the bottom of this document has both, clearly marked.

## §1 · Proposed slide sequence

10 slides, each with a headline, the number to put on it, and exactly which notebook section to screenshot for the real chart. Speaker notes are the one sentence to say out loud, not read off the slide. At roughly a minute a slide this fits the 10-minute limit, but rehearse with a timer — Slides 7 and 9 are the first to cut if it runs long.

### Slide 1 · Title

- **Beyond a Good Story** — When (and for whom) does persuasive loan language actually speed up funding?
- Team Cultural Blend · Kiva loan data · 1.45 million real loans

### Slide 2 · The question

- When a loan's story leans on family, competence, or urgency — does it get funded faster?
- Does the answer depend on *who's* asking and *when*?

**Why it matters:** framing is the one thing a platform can actually coach. Loan size, sector, and geography can't be rewritten after the fact.

### Slide 3 · How we made sure findings are real

- Trained only on the past, tested only on loans posted in 2024–2025 — no peeking at the future.
- Two independent methods (statistical regression + machine learning) had to agree before a finding made the deck.
- Every "significant" result was re-tested under a stricter, more conservative statistical assumption — several headline-looking results didn't survive (Slide 6).

Source: modeling notebook, §4 Data Split + §7.1 Cluster-Robust Sensitivity Check

Kept to methods only, on the organizer's instruction not to re-cover dataset background they're already introducing.

### Slide 4 · A marketplace that never recovered

46% → 30% → 30% funded within 24 hours

- Pre-pandemic, almost half of all loans funded within a day.
- Since 2020, under a third do — and it has **never** recovered, years after the disruption ended.
- 589,823 loans "before" vs. 565,474 "after" — not a small, noisy sample.

Source: EDA notebook, §4 Categorical Trends (period chart)

This is the single most concrete, non-technical finding in the whole deck — **lead with it.**

### Slide 5 · Structure beats story

- Loan amount and repayment terms are linked to funding speed roughly **10× more strongly** than any single narrative choice, in simple comparisons.
- Sector alone spans well over a full order of magnitude in speed; region and borrower gender show similarly large gaps.
- Female-posted loans fund in a median 2.3 days; male-posted loans, 7.7 days.

Source: EDA notebook, §5 Categorical Features + §9 Feature Correlations

### Slide 6 · What survives scrutiny

~Half of "significant" framing results don't survive a stricter test

- A standard model made **urgency language** look like a clean, universal win. Re-tested under a stricter, more conservative assumption (standard errors clustered by country, not treated as fully independent), that result doesn't hold up — **we're not recommending it.**
- **Family framing** mostly doesn't survive either — and the piece that does is narrower than it first looked. Our original test asked the wrong question (does this region differ from Africa?) instead of the right one (does family framing do anything *here*?). Re-tested correctly, it holds up in **four countries — Palestine, Yemen, Honduras, Nicaragua** (significant under clustering in all three model fits, both pipelines). Strong evidence, but it is not "the Middle East and Central America" as regions, and it is not a platform-wide writing rule — those four countries are ~5% of all loans.
- **Sentiment tone** — counterintuitively, more positive language links to slower funding, but even this finding's significance is model-sensitive: it survives clustering in the authoritative pipeline, not in the simpler notebook model. Reported as genuinely open, not a third confirmed survivor.
- **Competence/agency language** — no link survives the stricter test. (It did look significant in one of the authoritative pipeline's two models before clustering, then failed — the same fragile pattern as urgency, so don't present it as a clean universal null.)
- A second, completely different technique (SHAP feature importance from the machine-learning model) independently agrees on urgency and family framing — neither cracks its top 15 factors. Sentiment does (11th place) despite its disputed significance above: real predictive weight and statistical robustness turn out to be different questions.

Source: modeling notebook, §7.2 within-region slopes (the four-country claim) + §7.1 cluster check + §8 Feature Importance

The most important slide in the deck. Not "framing doesn't matter" — "we tested harder than a typical analysis would, and this is what's actually real." Your answer to "how do we know this isn't a fluke."

### Slide 7 · Beyond keywords

1.5 → 13.5 days across topics, \>9× swing

- Topic modeling (not just keyword counts) surfaces real, coherent themes: livestock, health & sanitation, clean water, farming, general retail.
- Funding speed swings more than ninefold across topics — the largest single gap anywhere in the analysis.

Source: EDA notebook, §8 Topic Modeling

Good "we went further than keyword-spotting" beat for originality. First trim candidate if the deck runs long.

### Slide 8 · What this means in practice

- Don't recommend urgency language platform-wide — it looked like a safe, universal tip, but doesn't survive rigorous testing.
- Family-framing guidance should be a localized A/B test in four countries (Palestine, Yemen, Honduras, Nicaragua) — not a blanket writing rule. Two countries per group is thin evidence, and everywhere else the association vanishes under scrutiny.
- A structural review (why some sectors/regions fund so much slower) still likely outperforms copywriting coaching alone.
- A same-day-funding risk flag is buildable *today* — strong enough (ROC AUC ≈ 0.90) to surface at-risk loans before they stall, no framing insight required.

This is the practical-implications slide — spend real time here. "Test before you recommend" is itself a practical takeaway, not just a methods footnote.

### Slide 9 · What this can't tell us

- Association, never causation — no borrower was randomly assigned a writing style.
- Measures how fast a *funded* loan funds — not whether a loan gets funded at all.
- Framing measured with transparent, simple rules — not a claim to capture every nuance of persuasive writing.

One slide, said plainly, builds more trust than skipping it. Second trim candidate if the deck runs long.

### Slide 10 · Closing

"The story helps — where it's tested.\
The structure decides."

- Thank you — questions.

## §2 · Numbers quick reference

Every figure used above, with its real source. `authoritative` = the tested full pipeline, `reports/generated_full_dataset/` — put these on slides. `notebook` = the Kaggle notebooks — directionally identical, use only if you need a chart the authoritative report doesn't render.

| Finding | Value | Source |
|----|----|----|
| Valid, usable loans | 1,453,840 / 1,453,846 | `authoritative` |
| Funded within 24h — pre-pandemic | 46.0% | `notebook` |
| Funded within 24h — pandemic disruption | 30.3% | `notebook` |
| Funded within 24h — post-pandemic | 30.0% | `notebook` |
| Duration model: gender (male vs. female) | coef +0.430, HC3 p\<0.0001 → clustered p\<0.0001 (survives) | `authoritative` |
| Duration model: urgency framing | coef −0.063, HC3 p\<0.0001 → clustered p=0.49 (does not survive) | `authoritative` |
| Duration model: family framing (baseline) | coef −0.023, HC3 p\<0.0001 → clustered p=0.20 (does not survive) | `authoritative` |
| **Avg within-region slope**: family in Middle East (Palestine, Yemen) | −0.1236 notebook · −0.0729 authoritative duration · +0.1753 authoritative 24h — all clustered p\<0.005, significant in all 3 | `authoritative` |
| **Avg within-region slope**: family in Central America (Honduras, Nicaragua) | −0.0618 notebook · −0.0742 authoritative duration · +0.1025 authoritative 24h — all clustered p\<0.0001, significant in all 3 | `authoritative` |
| **Avg within-region slope**: family in Asia (12 countries) | +0.0338 / +0.0234 / −0.0304 — clustered p=0.0535, 0.0846, 0.2860: not significant in any of the 3 fits | `authoritative` |
| Avg within-region slope: Africa (27) / Oceania (4) / N. America (1) | none significant, except N. America in 1 of 3 fits (p=0.0094) — a single country, not claimed | `authoritative` |
| Countries per region group | Middle East 2 · Central America 2 · North America 1 · Oceania 4 · Asia 12 · Africa 27 | `authoritative` |
| Duration model: agency framing | coef +0.001, p=0.31 → p=0.93 (n.s. either way) | `authoritative` |
| Duration model: sentiment tone | coef +0.136, HC3 p\<0.0001 → clustered p=0.0095 (survives) | `authoritative` |
| Duration model: sentiment tone (notebook's simpler formula) | HC3 p\<0.0001 → clustered p=0.2544 (does not survive) | `notebook` |
| Cluster-robust check: coefficients changing conclusion | 64 / 128 (50%), both explanatory models combined | `authoritative` |
| 24h classifier: holdout ROC AUC / AP | 0.900 / 0.830 | `authoritative` |
| Duration model: R² | 0.54 (boosted) · Ridge MAE 6.63 days · boosted MAE 5.20 days | `authoritative` |
| Gender: median funding speed, female vs. male | 2.3 vs. 7.7 days | `notebook` |
| SHAP: narrative-framing rank | outside the top 15 factors (sentiment 11th) | `notebook` |
| Cluster-robust check: coefficients changing conclusion | 20 / 45 (44%), duration model only | `notebook` |
| Topic modeling: funding-speed range across topics | 1.5 – 13.5 days | `notebook` |

Compiled from the verified 2026-08-27/28 Kaggle runs and `reports/generated_full_dataset/analysis_summary.json` / `association_summary.txt`. Every number above was cross-checked against a real command output before being written here — none are estimated or recalled from memory.
