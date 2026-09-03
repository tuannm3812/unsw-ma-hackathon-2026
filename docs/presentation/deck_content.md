<!-- Markdown rendering of docs/presentation/deck_content.html (the "Beyond a Good Story" artifact).
     The HTML file is the styled original; this file is the same content for reading on GitHub. -->

Deck content brief · UNSW Marketing Analytics Hackathon 2026 · Team Cultural Blend

# Beyond a Good Story

When — and for whom — does a persuasive loan story actually speed up funding? Slide-ready content, pulled from the verified full-dataset analysis, for the final presentation.

**Deadline** 2026-09-03, 5:00pm Sydney **Format** Slides only **Time limit** 10 min presenting, then 10 min Q&A **Judging** Panel 80% + Audience vote 20%

**Format update from the organizer (2026-08-28):** presentation is strictly timed at 10 minutes, cut off when time is up. **No background/intro slide** — the organizer introduces Kiva and the dataset to everyone, so don't spend a slide on it. Explicit instruction: **quality over quantity of findings.** Below, Slide 3 is trimmed to methods-only for this reason, and Slides 7 and 9 are marked as trim candidates if the deck needs to shrink further to comfortably fit 10 minutes.

## §0 · Research question coverage

Checked against the proposal's central and supporting questions before writing a single slide — every question the project committed to has a real, verified answer.

Central question

Answered

Framing vs. structure

Answered

Segment differences

Answered

Pandemic-era shift

Answered

Predictive value

Answered

**One thing to know before building slides:** two sets of numbers exist in this repo — the `authoritative` full pipeline (`reports/generated_full_dataset/`) and the `notebook` versions (self-contained Kaggle notebooks, built for readability). They agree directionally on most findings, but they do **not** always agree on statistical significance — sentiment tone is significant in one pipeline and not the other (the corrected within-region family slopes agree in all fits: Asia is non-significant everywhere). Where they disagree, this brief reports the disagreement rather than picking a side. **Use the authoritative numbers on slides** — the reference table at the bottom of this document has both, clearly marked.

## §1 · Proposed slide sequence

10 slides, each with a headline, the number to put on it, exactly which notebook section to screenshot for the real chart — and now a full word-for-word speaker script per slide. The scripts are ≈960 spoken words — about 7½ minutes at a measured 130 wpm — and the per-slide labels build in pacing headroom (≈9:45 total after adding the borrower recommendation; the spoken word count is ≈1,015 words ≈ 7:50 at 130 wpm). Rehearse as a pair with a timer and target FINISHING by 9:00, keeping a full minute of buffer under the hard cut-off; Slides 7 and 9 are the first to trim if a run-through goes long. Scripts are now split across the two presenters — Tuan carries the analyst arc (question, method, scrutiny: slides 1–3, 6–7), Sophia the business arc (market, recommendations, close: slides 4–5, 8–10) — with spoken hand-offs built in. Treat them as a floor to edit for your own voices, not lines to memorise.

### Slide 1 · Title

- **Beyond a Good Story** — When (and for whom) does persuasive loan language actually speed up funding?
- Team Cultural Blend · Kiva loan data · **1.45 million** real loans

> **Script · Tuan · ~30s** — "Good morning — we're Cultural Blend: I'm Tuan, and my teammate Sophia will take you through what this means for the business. Kiva is built on stories — every loan page leads with one, the way a landing page leads with copy. We asked 1.45 million real loans a single question: does the story actually move the money?"

### Slide 2 · The question

- When a loan's story leans on family, competence, or urgency — does it get funded faster?
- Does the answer depend on *who's* asking and *when*?

**Why it matters:** framing is the one thing a platform can actually coach. Loan size, sector, and geography can't be rewritten after the fact.

> **Script · Tuan · ~50s** — "Why should a marketing audience care? Because on Kiva, the lender is the customer and the loan page is the product page. Loan size, sector, geography — fixed at listing. The story is the one element a platform can coach, test, and optimise — classic conversion territory. So: when a story leans on family, competence, or urgency, does the loan fund faster? And does that depend on who's asking, and when? That's a testable claim — so we tested it, hard."

> **Backup · if questions land here**
> - **How is 'framing' measured?** Transparent per-100-word lexicon rates (family, agency/competence, urgency, gratitude, first/third-person), VADER sentiment compound, plus topic modeling (an 8-topic NMF exploration of the descriptions in the EDA; 5 topic loadings enter the models as features) — all computed from the loan description text with simple, auditable rules.
> - **Why speed, not success?** The dataset contains completed fundraises (1,452,203 funded + 1,637 refunded that completed funding), so time-to-fund is the observable outcome. Whether a loan funds at all is out of scope — conceded up front on Slide 9.

### Slide 3 · How we stress-tested our findings

- **Predictive claims**: trained only on the past, tested only on loans posted in 2024–2025 — no peeking at the future. (This validates the forecasting models, not the framing findings — those come from a separate full-sample statistical model.)
- **Framing claims**: every "significant" result was re-tested under a country-clustered sensitivity check — one that lets loans from the same country be correlated instead of treating them as independent — and then under a few-cluster reference where a result rests on only a handful of countries. Most headline-looking results didn't survive (Slide 6).
- A machine-learning importance ranking (SHAP) is shown as complementary predictive evidence — it measures what the forecasting model relied on, and cannot by itself confirm or refute the statistical findings.

Visual: chronological train/test split schematic (counts from the authoritative snapshot: train 1,174,953 / test 278,887 at 2024-01-01). The boosted forecast-vs-actual exhibit is available in charts/notebook/ as an optional backup; the split/cluster checks themselves are text output (§4 + §7.1).

Kept to methods only, on the organizer's instruction not to re-cover dataset background they're already introducing.

> **Script · Tuan · ~65s** — "Two disciplines before any findings — because in a dataset this size it is dangerously easy to find things that aren't there. For prediction: train only on the past, score only on loans posted in 2024–25 — the models never see the future they're graded on. For the framing claims: every 'significant' result had to survive country-clustered standard errors — ten thousand loans from one country are not ten thousand independent customers — and where a result rested on just a couple of countries, an even harsher few-cluster screen on top. Most headline-looking results did not survive. Hold that thought while Sophia shows you what the market itself looks like."

> **Backup · if questions land here**
> - **Why HC3?** A standard heteroskedasticity-robust estimator whose small-sample leverage adjustment suits a dataset where error variance plainly differs across 1.45M loans — chosen for what it corrects, with no claim of a universal strictness ordering among the HC variants. It still assumes independence, which is exactly what the clustering re-test relaxes.
> - **Why cluster by country?** Same-country loans share an economy, currency, field-partner institutions and lender familiarity — treating them as independent overstates evidence. 48 country clusters in the explanatory sample.
> - **Why call the few-cluster check a 'screen', not a test?** It refers the unchanged clustered SE to t(countries−1) — Cameron & Miller (2015 §VI) treat that as a minimum improvement and warn even it can over-reject; the calibrated small-cluster procedures (bias-corrected CRVE, wild-cluster bootstrap) are named future work. So it can downgrade a claim, never certify one.
> - **Split sizes:** train 1,174,953 (pre-2024) / holdout 278,887 (posted 2024-01-01 onward).

### Slide 4 · A marketplace that hasn't recovered

46% → 30% → 30% funded within 24 hours

- Pre-pandemic, almost half of all loans funded within a day.
- Since 2020, under a third do — and through the end of the data (2025) it has **not** recovered. That's persistence to date, not proof it never will.
- 589,823 loans "before" vs. 565,474 "after" — not a small, noisy sample.

Source: EDA notebook, §4 Categorical Trends (period chart)

This is the single most concrete, non-technical finding in the whole deck — **lead with it.**

> **Script · Sophia · ~60s** — "Thanks, Tuan. Start with the market, because every other number lives inside it. Before the pandemic, 46% of loans funded within 24 hours — nearly half converting same-day. Since 2020 it's been under a third — and through 2025, the 'recovery' is minus 0.3 points. With over half a million loans on each side of that divide, this isn't noise: it's a structurally slower, more selective marketplace. For a marketer that reframes the whole job — when customers get pickier, knowing what actually drives conversion matters more, not less."

> **Backup · if questions land here**
> - **Exact shares:** 46.0% pre-pandemic → 30.3% pandemic-disruption → 30.0% post-pandemic; 589,823 loans before vs 565,474 after.
> - **'Could it be composition?'** Fair question — this is a descriptive period comparison, and the loan mix (countries, sectors, amounts) also shifted. We claim persistence of the slowdown to date, not a causal pandemic effect. The multivariable models on later slides do hold structure fixed, and the period terms stay large there too.

### Slide 5 · Structure beats story

- Loan amount and repayment terms are linked to funding speed roughly **10× more strongly** than any single narrative choice, in simple comparisons.
- Sector alone spans well over a full order of magnitude in speed; region and borrower gender show similarly large gaps.
- Female-posted loans fund in a median **2.3 days**; male-posted loans, 7.7 days.

Source: EDA notebook, §5 Categorical Features + §9 Feature Correlations

> **Script · Sophia · ~65s** — "And what drives it is structure. Loan amount and repayment terms correlate with funding speed roughly ten times more strongly than any narrative signal. Sector alone spans an order of magnitude — sanitation stories fund in under a day, clothing takes twelve. And the starkest gap in the data: loans posted by women fund in a median of 2.3 days, by men 7.7 — three times longer. None of this is causal, but it's enormous, it's stable, and it dwarfs anything the words do. Which brings us to the question we actually came here to answer. Tuan —"

> **Backup · if questions land here**
> - **Gender gap robustness:** the duration-model male coefficient is +0.430 with HC3 *and* country-clustered p < 0.0001 — one of the few results that survives every re-test. Still associational: gender correlates with sector, amount, and country.
> - **Where does '10×' come from?** Standardized-correlation comparison in EDA §9: amount/term correlations with speed are an order of magnitude larger than any narrative feature's.
> - **Sector scale example:** Water-sector coefficient −1.12 on log(1+days) ≈ funding in roughly ⅓ the time of the Agriculture baseline (notebook model).

### Slide 6 · What survives scrutiny

No narrative-framing result is robust enough to support a recommendation

- A standard model made **urgency language** look like a clean, universal win. Re-tested with standard errors clustered by country (loans from one country allowed to be correlated, not treated as independent), that result doesn't hold up — **we're not recommending it.**
- **Family framing** doesn't survive either — and the one piece that looked like it did turns out to be a descriptive pattern, not a supported result. Our original test asked the wrong question (does this region differ from Africa?) instead of the right one (does family framing do anything *here*?). Re-tested correctly, **two pooled two-country categories — Middle East (Palestine + Yemen) and Central America (Honduras + Nicaragua)** show the same faster-funding direction in every fit. But each rests on exactly two countries, and once the p-value is referred to a few-cluster distribution (t with 1 degree of freedom, critical value 12.7 not 1.96), **neither is significant** — p ≈ 0.06–0.21 across fits. A hypothesis for a country-stratified test, not a finding. Those categories are ~5% of all loans.
- **Sentiment tone** — counterintuitively, more positive language links to slower funding, but even this finding's significance is model-sensitive: it survives clustering in the authoritative pipeline, not in the simpler notebook model. Reported as genuinely open, not a third confirmed survivor.
- **Competence/agency language** — no link survives the clustered check. (It did look significant in one of the authoritative pipeline's two models before clustering, then failed — the same fragile pattern as urgency, so don't present it as a clean universal null.)
- Complementary evidence, not independent confirmation: SHAP importance from the forecasting model (a different model, without the region interactions) shows narrative features carry little overall predictive weight — no family, agency or urgency feature reaches its top 15. It can't corroborate the sign or uncertainty of any specific coefficient. Sentiment does reach 11th place despite its disputed significance: predictive weight and statistical robustness are different questions.

Source: modeling notebook, §7.2 within-region slopes (the pooled-category claim) + §7.1 cluster check + §8 Feature Importance

The most important slide in the deck. Not "framing doesn't matter" — "we tested harder than a typical analysis would, and nothing narrative survived it; here is exactly why the one thing that looked like it did doesn't count." Your answer to "how do we know this isn't a fluke."

> **Script · Tuan · ~1m50s** — "So: does the story matter? Our honest answer: no narrative result is robust enough across specifications to support a recommendation. Urgency language looked like a universal win — significant at p below 0.001. Cluster by country, and it collapses to 0.44. Gone. Family framing — and here our own first version got it wrong: we tested whether regions differ from Africa, which is not the same as whether family framing helps within a region. Corrected, two pooled categories — Palestine plus Yemen, and Honduras plus Nicaragua — do show faster funding in every fit we ran. But each rests on exactly two countries, and against a deliberately harsh few-cluster screen — a conservative heuristic, not calibrated inference: a t distribution with one degree of freedom, critical value 12.7, not 1.96 — neither is significant: p between 0.06 and 0.21. So we report a hypothesis worth testing, not a finding. Sentiment is the honest illustration: it survives country clustering in one of our two specifications and not the other — genuinely open, robust in neither direction. We'd rather report no robust evidence than one exciting result we can't defend — because a recommendation you'd ship to real borrowers deserves that bar."

> **Backup · if questions land here**
> - **Urgency, all three fits (clustered p):** authoritative duration 0.4943, authoritative 24h 0.2233, notebook 0.4442 — HC3 said p<0.0001 in all three. The re-test, not the sample, is what changed the answer.
> - **Full few-cluster screen (p), authoritative duration / authoritative 24h / notebook:** Africa (27 countries) 0.33 / 0.42 / 0.56 · Asia (12) 0.11 / 0.31 / 0.08 · Central America (2) 0.06 / 0.14 / 0.07 · Middle East (2) 0.12 / 0.21 / 0.08 · Oceania (4) 0.90 / 0.49 / 0.66 · North America (1 country — Haiti): not estimable, a single cluster has no between-cluster uncertainty.
> - **Sentiment disagreement, precisely:** authoritative duration model survives clustering (p = 0.0095); the notebook's simpler formula does not (p = 0.2544). Same data, different specification — which is why we call it open rather than picking the answer we like.
> - **Scale of the clustering shake-up:** 64 of 128 authoritative coefficients (50%) change significance conclusion; 20 of 45 (44%) in the notebook's duration model.
> - **If pressed on 'isn't t(1) too harsh?':** concede it's deliberately conservative and a heuristic — then point out the direction of the argument: a result identified by two countries shouldn't be certified by a normal approximation either. We choose to under-claim.

### Slide 7 · Beyond keywords

1.5 → **13.5 days** mean funding speed across topics, >9× swing

- Topic modeling on the descriptions (TF-IDF + NMF, 8 topics — not just keyword counts) surfaces real, coherent themes: sanitation, clean water, pig raising, family business, smallholder farming.
- Mean funding speed swings more than ninefold across topics (1.5 → **13.5 days**) — the largest single gap anywhere in the analysis.

Source: EDA notebook, §8 Topic Modeling

Good "we went further than keyword-spotting" beat for originality. First trim candidate if the deck runs long.

> **Script · Tuan · ~40s** — "One more layer before the recommendations — we went past keyword counting. Topic modelling finds eight coherent story themes, and mean funding speed swings ninefold across them: sanitation and clean-water stories in under two days, group farming closer to two weeks. But notice what a theme mostly encodes: what the loan is FOR. Structure again — not persuasion. So what should Kiva actually do with all of this? Sophia —"

> **Backup · if questions land here**
> - **Method:** TF-IDF + NMF (non-negative matrix factorization), 8 topics in the EDA exploration, seeded/reproducible. Separately, the forecasting pipeline uses 5 topic loadings as features (topic_0…topic_4) — two related but distinct uses.
> - **Speed range:** ~1.5 days (fastest topic: sanitation) to ~13.5 days (slowest: group solar/farm plots) in MEAN funding time — the largest single gap in the analysis.
> - **Why not a persuasion finding:** a topic mostly encodes the loan's purpose (livestock vs clean water vs retail) — that's structure; the framing lexicons measure the how, topics measure the what.

### Slide 8 · What this means in practice

- Don't recommend urgency language platform-wide — it looked like a safe, universal tip, but doesn't survive rigorous testing.
- No writing rule at all from this data. The one family-framing pattern (**Palestine** + Yemen; Honduras + Nicaragua) is a hypothesis worth a *country-stratified* A/B test — not a recommendation, because two countries per category cannot support one.
- A structural review (why some sectors/regions fund so much slower) still likely outperforms copywriting coaching alone.
- A same-day-funding RANKING PROTOTYPE works — holdout ROC AUC ≈ 0.90 among eventually-funded loans, no framing insight required. But its negative class is “funded, just not within 24h” — expired/withdrawn listings aren't in the data — so it is NOT yet validated for early-warning use. Path to a pilot: obtain all posted listings (incl. expired/withdrawn outcomes), define the operational target and censoring window, retrain and validate on that population; only then threshold, calibration, capacity/fairness checks and a prospective test.
- **FOR BORROWERS & FIELD PARTNERS:** don't optimise wording; plan for timing — a bigger ask fills more slowly (~2 days for the smallest decile of loans vs ~19 for the largest). This is **not** a recommendation to ask for less: our outcome is funding *speed*, not whether the borrower got the capital they needed.

This is the practical-implications slide — spend real time here. "Test before you recommend" is itself a practical takeaway, not just a methods footnote.

> **Script · Sophia · ~1m50s** — "Three moves — each with a clear owner. One: don't ship writing tips. For Kiva's content team that's a build spared; for borrowers, it's not being coached into copy we found no robust evidence for. And for borrowers and field partners themselves, the honest advice is timing, not persuasion: a bigger ask fills more slowly — roughly two days for the smallest loans against nineteen for the largest — so post earlier when capital is needed by a date. That is not us telling anyone to ask for less: our outcome is speed, not whether they got the capital they needed. Two: for the growth team and the field partners in exactly four markets — Palestine, Yemen, Honduras, Nicaragua — run the country-stratified A/B test: family-framing prompt versus standard at listing, outcome time-to-fund. That's how a hypothesis becomes a decision — and everyone in this room knows the discipline: test before you ship. Three: for the product team, the structural gaps are the real levers — how the consistently slower sectors and regions get surfaced, bundled, and supported — because those gaps are ten times any wording effect. And the classifier? A retrospective ranking prototype among funded loans — AUC 0.90 on strictly future data — for the data science team to develop toward an early-warning flag, after retraining on all listings including expired ones. And the intended benefits — to be tested, not assumed: better discovery for lenders, fewer stalled loans for borrowers."

> **Backup · if questions land here**
> - **Classifier detail:** holdout ROC AUC 0.8997, average precision 0.8301, Brier 0.1156, accuracy 0.840 on 278,887 strictly-future loans (87,466 funded within 24h vs 191,421 not). No framing features required for that performance. Boundary to volunteer: the negative class is “eventually funded, but not within 24 hours” — expired/withdrawn listings never enter the data, so this is a retrospective ranking prototype among eventual funders, not a validated early-warning system for all new listings.
> - **What the A/B test looks like:** country-stratified (Palestine, Yemen, Honduras, Nicaragua separately), family-framing writing prompt vs standard prompt at loan-creation, outcome = time-to-fund. Stratification is the point — it answers the question our observational data cannot: which constituent country, if any, drives the pattern.
> - **Stakeholder map (judging criterion: practical implications for borrowers/platforms/stakeholders, 20%):** don't-ship-tips → content team (build spared) + borrowers (no cargo-cult coaching); A/B test → growth team + field partners in PS/YE/HN/NI; structural review → platform product + field partners; classifier prototype → data science team; downstream: lenders get better discovery, borrowers fewer stalled loans.
> - **Pilot guardrails, if asked:** choose an operating threshold, check calibration at it, cap review capacity, test for demographic disparities in flag rates, and measure prospectively whether surfacing flagged loans actually changes outcomes.

### Slide 9 · What this can't tell us

- Association, never causation — no borrower was randomly assigned a writing style.
- Measures how fast a *funded* loan funds — not whether a loan gets funded at all.
- Framing measured with transparent, simple rules — not a claim to capture every nuance of persuasive writing.

One slide, said plainly, builds more trust than skipping it. Second trim candidate if the deck runs long.

> **Script · Sophia · ~35s** — "Three honest limits. Association, never causation — nobody randomly assigned writing styles. We measure how fast funded loans fund — not whether a loan funds at all. And our framing measures are transparent, simple rules — not every nuance of persuasion. We'd rather you know exactly what this can and cannot say — that's what makes the parts we do claim worth trusting."

> **Backup · if questions land here**
> - **Selection, stated exactly:** the data are completed fundraises — expired or withdrawn listings aren't in it, so all speed findings condition on eventual funding.
> - **Why simple lexicons, not an LLM?** Transparency and auditability: every measure can be recomputed by a judge from the stated rule. A richer text model is future work, and would still face the same inference discipline.

### Slide 10 · Closing

"In this data, the story barely registers.\
The structure carries the signal."

- Thank you — questions.

> **Script · Both · ~20s** — "(Sophia) In this data, the story barely registers — the structure carries the signal. (Tuan) And testing hard enough to say, honestly, that there is no robust evidence for the story — that's worth more to a platform than a good-sounding tip. Thank you — we're happy to take your questions."

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
| **Avg within-region slope**: family in Middle East (Palestine, Yemen) | −0.1236 notebook · −0.0729 authoritative duration · +0.1753 authoritative 24h — conventional clustered p\<0.005 in all 3, but few-cluster t(1) p = 0.08 notebook / 0.12 authoritative duration / 0.21 authoritative 24h: NOT significant (2 countries) | `authoritative` |
| **Avg within-region slope**: family in Central America (Honduras, Nicaragua) | −0.0618 notebook · −0.0742 authoritative duration · +0.1025 authoritative 24h — conventional clustered p\<0.0001 in all 3, but few-cluster t(1) p = 0.06 / 0.06 / 0.14: NOT significant (2 countries) | `authoritative` |
| **Avg within-region slope**: family in Asia (12 countries) | +0.0338 / +0.0234 / −0.0304 — clustered p=0.0535, 0.0846, 0.2860: not significant in any of the 3 fits | `authoritative` |
| Avg within-region slope: Africa (27) / Oceania (4) / N. America (1) | none significant, except N. America in 1 of 3 fits (p=0.0094) — a single country, not claimed | `authoritative` |
| Countries per region group | Middle East 2 · Central America 2 · North America 1 · Oceania 4 · Asia 12 · Africa 27 | `authoritative` |

**Numbers quick reference, continued:**

| Finding | Value | Source |
|----|----|----|
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
