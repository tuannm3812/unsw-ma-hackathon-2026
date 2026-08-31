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

10 slides, each with a headline, the number to put on it, exactly which notebook section to screenshot for the real chart — and now a full word-for-word speaker script per slide. Scripts total ≈9½ minutes at a measured pace, inside the strict 10-minute cut-off, but rehearse with a timer — Slides 7 and 9 are the first to cut (their scripts save ~85 seconds) if a run-through goes long. Treat the scripts as a floor to edit for your own voice, not lines to memorise.

### Slide 1 · Title

- **Beyond a Good Story** — When (and for whom) does persuasive loan language actually speed up funding?
- Team Cultural Blend · Kiva loan data · 1.45 million real loans

> **Script · ~20s** — "Good morning — we're Cultural Blend. Kiva is built on stories: every loan page leads with one. So we asked a simple question of 1.45 million real loans: does the story actually move the money?"

### Slide 2 · The question

- When a loan's story leans on family, competence, or urgency — does it get funded faster?
- Does the answer depend on *who's* asking and *when*?

**Why it matters:** framing is the one thing a platform can actually coach. Loan size, sector, and geography can't be rewritten after the fact.

> **Script · ~45s** — "Specifically: when a borrower's story leans on family, on competence, on urgency — does the loan fund faster? And does the answer depend on who's asking, and when? We care because language is the one thing a platform can coach. You can't rewrite a loan's size, sector, or country after the fact — but you could suggest better words. *If* words work. That's the claim we set out to test, not assume."

> **Backup · if questions land here**
> - **How is 'framing' measured?** Transparent per-100-word lexicon rates (family, agency/competence, urgency, gratitude, first/third-person), VADER sentiment compound, plus NMF topic modeling (5 topics) — all computed from the loan description text with simple, auditable rules.
> - **Why speed, not success?** The dataset contains completed fundraises (1,452,203 funded + 1,637 refunded that completed funding), so time-to-fund is the observable outcome. Whether a loan funds at all is out of scope — conceded up front on Slide 9.

### Slide 3 · How we made sure findings are real

- **Predictive claims**: trained only on the past, tested only on loans posted in 2024–2025 — no peeking at the future. (This validates the forecasting models, not the framing findings — those come from a separate full-sample statistical model.)
- **Framing claims**: every "significant" result was re-tested under a country-clustered sensitivity check — one that lets loans from the same country be correlated instead of treating them as independent — and then under a few-cluster reference where a result rests on only a handful of countries. Most headline-looking results didn't survive (Slide 6).
- A machine-learning importance ranking (SHAP) is shown as complementary predictive evidence — it measures what the forecasting model relied on, and cannot by itself confirm or refute the statistical findings.

Source: modeling notebook, §4 Data Split + §7.1 Cluster-Robust Sensitivity Check

Kept to methods only, on the organizer's instruction not to re-cover dataset background they're already introducing.

> **Script · ~60s** — "Two disciplines before any findings. For prediction, we train only on the past and test only on loans posted in 2024–25 — no peeking at the future. For the framing claims, every 'significant' result had to survive re-testing: first with standard errors clustered by country, so ten thousand loans from one country can't masquerade as ten thousand independent pieces of evidence — and where a result rested on just a couple of countries, a deliberately harsher few-cluster reference on top. Most headline-looking results did not survive. That's the point: we'd rather lose a finding than present a fluke."

> **Backup · if questions land here**
> - **Why HC3?** The most conservative of the standard heteroskedasticity-robust estimators — a defensible default when error variance differs across 1.45M loans. It still assumes independence, which is exactly what the clustering re-test relaxes.
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

> **Script · ~60s** — "Before the pandemic, almost half of Kiva loans — 46% — funded within 24 hours. Since 2020, it's been under a third — and through the end of our data in 2025 it has not recovered. That's more than half a million loans on each side of the divide, so this isn't noise. Every result we show next lives inside this slower, tighter marketplace — lenders are more selective now, which makes knowing what actually drives speed more valuable, not less."

> **Backup · if questions land here**
> - **Exact shares:** 46.0% pre-pandemic → 30.3% pandemic-disruption → 30.0% post-pandemic; 589,823 loans before vs 565,474 after.
> - **'Could it be composition?'** Fair question — this is a descriptive period comparison, and the loan mix (countries, sectors, amounts) also shifted. We claim persistence of the slowdown to date, not a causal pandemic effect. The multivariable models on later slides do hold structure fixed, and the period terms stay large there too.

### Slide 5 · Structure beats story

- Loan amount and repayment terms are linked to funding speed roughly **10× more strongly** than any single narrative choice, in simple comparisons.
- Sector alone spans well over a full order of magnitude in speed; region and borrower gender show similarly large gaps.
- Female-posted loans fund in a median 2.3 days; male-posted loans, 7.7 days.

Source: EDA notebook, §5 Categorical Features + §9 Feature Correlations

> **Script · ~70s** — "So what does drive speed? Structure. Loan amount and repayment terms are associated with funding speed roughly ten times more strongly than any single narrative choice. Sector alone spans more than an order of magnitude. And the starkest gap in the data: loans posted by women fund in a median of 2.3 days; by men, 7.7 — more than three times longer. None of this is causal — but the pattern is enormous, it's stable, and it dwarfs anything the words do."

> **Backup · if questions land here**
> - **Gender gap robustness:** the duration-model male coefficient is +0.430 with HC3 *and* country-clustered p < 0.0001 — one of the few results that survives every re-test. Still associational: gender correlates with sector, amount, and country.
> - **Where does '10×' come from?** Standardized-correlation comparison in EDA §9: amount/term correlations with speed are an order of magnitude larger than any narrative feature's.
> - **Sector scale example:** Water-sector coefficient −1.12 on log(1+days) ≈ funding in roughly ⅓ the time of the Agriculture baseline (notebook model).

### Slide 6 · What survives scrutiny

Zero narrative-framing results survive at a defensible standard

- A standard model made **urgency language** look like a clean, universal win. Re-tested with standard errors clustered by country (loans from one country allowed to be correlated, not treated as independent), that result doesn't hold up — **we're not recommending it.**
- **Family framing** doesn't survive either — and the one piece that looked like it did turns out to be a descriptive pattern, not a supported result. Our original test asked the wrong question (does this region differ from Africa?) instead of the right one (does family framing do anything *here*?). Re-tested correctly, **two pooled two-country categories — Middle East (Palestine + Yemen) and Central America (Honduras + Nicaragua)** show the same faster-funding direction in every fit. But each rests on exactly two countries, and once the p-value is referred to a few-cluster distribution (t with 1 degree of freedom, critical value 12.7 not 1.96), **neither is significant** — p ≈ 0.06–0.21 across fits. A hypothesis for a country-stratified test, not a finding. Those categories are ~5% of all loans.
- **Sentiment tone** — counterintuitively, more positive language links to slower funding, but even this finding's significance is model-sensitive: it survives clustering in the authoritative pipeline, not in the simpler notebook model. Reported as genuinely open, not a third confirmed survivor.
- **Competence/agency language** — no link survives the clustered check. (It did look significant in one of the authoritative pipeline's two models before clustering, then failed — the same fragile pattern as urgency, so don't present it as a clean universal null.)
- Complementary evidence, not independent confirmation: SHAP importance from the forecasting model (a different model, without the region interactions) shows narrative features carry little overall predictive weight — no family, agency or urgency feature reaches its top 15. It can't corroborate the sign or uncertainty of any specific coefficient. Sentiment does reach 11th place despite its disputed significance: predictive weight and statistical robustness are different questions.

Source: modeling notebook, §7.2 within-region slopes (the pooled-category claim) + §7.1 cluster check + §8 Feature Importance

The most important slide in the deck. Not "framing doesn't matter" — "we tested harder than a typical analysis would, and nothing narrative survived it; here is exactly why the one thing that looked like it did doesn't count." Your answer to "how do we know this isn't a fluke."

> **Script · ~2min** — "Now the question we came to answer — and the honest answer is that nothing about the narrative survives our own scrutiny. Urgency language looked like a clean, universal win: significant at p < 0.001. Cluster by country, and it collapses to p ≈ 0.44. Gone. Family framing — here our own first version got it wrong: we tested whether regions differ from Africa, which is not the same as whether family framing helps *within* a region. Corrected, two pooled categories — Palestine + Yemen, and Honduras + Nicaragua — do show faster funding in every fit we ran. But each rests on exactly two countries, and against the appropriate few-cluster bar — a t distribution with one degree of freedom, where the critical value is 12.7, not 1.96 — neither is significant: p between 0.06 and 0.21. So we report it as a hypothesis worth testing, not a finding. Sentiment tone: more positive language associates with *slower* funding, but its significance flips between our two specifications — we call it open. We'd rather show you three trustworthy nulls than one exciting result we can't defend."

> **Backup · if questions land here**
> - **Urgency, all three fits (clustered p):** authoritative duration 0.4943, authoritative 24h 0.2233, notebook 0.4442 — HC3 said p<0.0001 in all three. The re-test, not the sample, is what changed the answer.
> - **Full few-cluster screen (p), authoritative duration / authoritative 24h / notebook:** Africa (27 countries) 0.33 / 0.42 / 0.56 · Asia (12) 0.11 / 0.31 / 0.08 · Central America (2) 0.06 / 0.14 / 0.07 · Middle East (2) 0.12 / 0.21 / 0.08 · Oceania (4) 0.90 / 0.49 / 0.66 · North America (1 country — Haiti): not estimable, a single cluster has no between-cluster uncertainty.
> - **Sentiment disagreement, precisely:** authoritative duration model survives clustering (p = 0.0095); the notebook's simpler formula does not (p = 0.2544). Same data, different specification — which is why we call it open rather than picking the answer we like.
> - **Scale of the clustering shake-up:** 64 of 128 authoritative coefficients (50%) change significance conclusion; 20 of 45 (44%) in the notebook's duration model.
> - **If pressed on 'isn't t(1) too harsh?':** concede it's deliberately conservative and a heuristic — then point out the direction of the argument: a result identified by two countries shouldn't be certified by a normal approximation either. We choose to under-claim.

### Slide 7 · Beyond keywords

1.5 → 13.5 days across topics, \>9× swing

- Topic modeling (not just keyword counts) surfaces real, coherent themes: livestock, health & sanitation, clean water, farming, general retail.
- Funding speed swings more than ninefold across topics — the largest single gap anywhere in the analysis.

Source: EDA notebook, §8 Topic Modeling

Good "we went further than keyword-spotting" beat for originality. First trim candidate if the deck runs long.

> **Script · ~45s** — "We also went beyond keyword counting. Topic modeling finds coherent themes in the stories — livestock, health and sanitation, clean water, farming, retail — and funding speed swings ninefold across them, from a day and a half to nearly two weeks. But notice what a topic mostly encodes: what the loan is *for*. Which is structure again — not persuasion."

> **Backup · if questions land here**
> - **Method:** NMF (non-negative matrix factorization), 5 topics, seeded/reproducible; topic loadings enter the models as features (topic_0…topic_4).
> - **Speed range:** ~1.5 days (fastest topic) to ~13.5 days (slowest) in median funding time — the largest single gap in the analysis.
> - **Why not a persuasion finding:** a topic mostly encodes the loan's purpose (livestock vs clean water vs retail) — that's structure; the framing lexicons measure the how, topics measure the what.

### Slide 8 · What this means in practice

- Don't recommend urgency language platform-wide — it looked like a safe, universal tip, but doesn't survive rigorous testing.
- No writing rule at all from this data. The one family-framing pattern (Palestine + Yemen; Honduras + Nicaragua) is a hypothesis worth a *country-stratified* A/B test — not a recommendation, because two countries per category cannot support one.
- A structural review (why some sectors/regions fund so much slower) still likely outperforms copywriting coaching alone.
- A same-day-funding risk flag is worth *piloting* — holdout ROC AUC ≈ 0.90 shows a strong ranking signal, no framing insight required. A rollout still needs a threshold, calibration at it, capacity/fairness checks, and a prospective test that surfacing actually helps.

This is the practical-implications slide — spend real time here. "Test before you recommend" is itself a practical takeaway, not just a methods footnote.

> **Script · ~90s** — "So what should Kiva actually do? Three things. First — don't ship writing tips. A platform-wide 'add urgency' nudge would be built on a result that doesn't survive testing. The family-framing pattern deserves a country-stratified A/B test in exactly those four markets: that's how a hypothesis becomes a decision, and it's cheap to run. Second — the structural gaps are where the real levers are: review how the consistently slower sectors and regions are surfaced, bundled, and supported, because those gaps are ten times the size of any wording effect. Third — speed itself is predictable: our classifier ranks same-day funding at AUC 0.90 on strictly future data, without any framing features. That's strong enough to pilot an early-warning flag for loans likely to stall — pilot, with calibration, capacity and fairness checks, not a blind rollout."

> **Backup · if questions land here**
> - **Classifier detail:** holdout ROC AUC 0.8997, average precision 0.8301, Brier 0.1156, accuracy 0.840 on 278,887 strictly-future loans (87,466 funded within 24h vs 191,421 not). No framing features required for that performance.
> - **What the A/B test looks like:** country-stratified (Palestine, Yemen, Honduras, Nicaragua separately), family-framing writing prompt vs standard prompt at loan-creation, outcome = time-to-fund. Stratification is the point — it answers the question our observational data cannot: which constituent country, if any, drives the pattern.
> - **Pilot guardrails, if asked:** choose an operating threshold, check calibration at it, cap review capacity, test for demographic disparities in flag rates, and measure prospectively whether surfacing flagged loans actually changes outcomes.

### Slide 9 · What this can't tell us

- Association, never causation — no borrower was randomly assigned a writing style.
- Measures how fast a *funded* loan funds — not whether a loan gets funded at all.
- Framing measured with transparent, simple rules — not a claim to capture every nuance of persuasive writing.

One slide, said plainly, builds more trust than skipping it. Second trim candidate if the deck runs long.

> **Script · ~40s** — "Three honest limits. This is association, never causation — no borrower was randomly assigned a writing style. We measure how fast funded loans fund — not whether a loan funds at all. And our framing measures are transparent, simple rules — they don't capture every nuance of persuasion. We'd rather you know exactly what this analysis can and cannot say — that's what makes the parts we do claim worth trusting."

> **Backup · if questions land here**
> - **Selection, stated exactly:** the data are completed fundraises — expired or withdrawn listings aren't in it, so all speed findings condition on eventual funding.
> - **Why simple lexicons, not an LLM?** Transparency and auditability: every measure can be recomputed by a judge from the stated rule. A richer text model is future work, and would still face the same inference discipline.

### Slide 10 · Closing

"In this data, the story barely registers.\
The structure carries the signal."

- Thank you — questions.

> **Script · ~20s** — "In this data, the story barely registers — the structure carries the signal. And testing hard enough to *know* that is worth more to a platform than a good-sounding tip. Thank you — we're happy to take questions."

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
