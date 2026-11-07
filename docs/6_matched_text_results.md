# Matched text benchmark findings

Date: 2026-11-02. Separate post-competition research extension for Cultural Blend.

Adding description form, lexical measures and TF-IDF reduced the sparse linear model’s duration MAE in **5 of 5 annual windows**, by 0.259–0.389 days. The median annual gain was 0.293 days. This is a reduction in forecast error among observed completed loans, not time saved by rewriting a narrative.

The compact tree comparison adds form and lexical measures, without TF-IDF. Its gains ranged from 0.001 to 0.042 days. Treat the two families as different representation experiments; their gain difference does not isolate a model-family effect. The next research priority is to validate what the text measures and define a feasible factual presentation experiment.

**Glossary.** S = structured loan context (amount, term, sector, geography, time).
M = description form and presence. L = lexicon, specificity and sentiment measures.
R = TF-IDF fitted on training rows only. P = programme text (`whySpecial`), an
unvalidated proxy. "Gain" = structure-only error minus text-added error, so positive
is better.

## Duration gains and uncertainty

Each comparison uses identical evaluation records and subtracts the text-added model’s absolute error from the structure-only model’s error. Positive values mean better forecasts. S is structured context; M is description form/presence; L is lexicon, specificity and sentiment; R is training-fitted TF-IDF; P is programme text as an unvalidated proxy.

| Posting year | Linear S MAE | Linear S+M+L+R MAE | Linear gain and month 95% interval | Tree S→S+M+L gain and month 95% interval |
| --- | --- | --- | --- | --- |
| 2021 | 8.250 | 7.957 | 0.293 [0.198, 0.384] | 0.035 [-0.073, 0.137] |
| 2022 | 8.570 | 8.197 | 0.372 [0.208, 0.518] | 0.028 [-0.036, 0.084] |
| 2023 | 8.185 | 7.926 | 0.259 [0.088, 0.406] | 0.006 [-0.025, 0.035] |
| 2024 | 7.515 | 7.126 | 0.389 [0.287, 0.500] | 0.001 [-0.020, 0.025] |
| 2025 | 6.406 | 6.147 | 0.260 [0.139, 0.396] | 0.042 [0.013, 0.074] |

The median annual linear MAE gain against S was 0.033 days for description form/presence alone and 0.036 days after adding lexical measures. These are separate total gains against S, not additive stage effects. Richer text may encode programme templates, location or purpose as well as framing; its predictive gain does not identify persuasion.

Country-resampling intervals include zero in 4 of five linear comparisons and 3 of five tree comparisons. Aggregate improvement therefore needs to be read alongside geographic sensitivity, without interpreting an interval spanning zero as proof of no gain.

All duration values are days. Intervals resample complete calendar months 1,000 times with paired losses and record-count weighting. These pointwise fixed-model sensitivity intervals have no multiplicity adjustment, omit retraining uncertainty, and each annual evaluation has only 12 month blocks. The separate country sensitivity is also important because contexts recur across records. It is not a causal interval or a guarantee under dependent clusters.

## Probability quality and programme context

Classification predicts completion within 24 hours among observed completed records. Brier gain uses the same positive-is-better convention; it is a difference in squared probability error, not percentage points of funding benefit. AUC measures ranking and cannot substitute for reliability checks.

| Year | Linear text Brier gain | Tree text Brier gain | Linear MAE gain beyond S+P | Tree MAE gain beyond S+P |
| --- | --- | --- | --- | --- |
| 2021 | 0.01029 | -0.00379 | 0.175 | 0.024 |
| 2022 | 0.00022 | 0.00020 | 0.343 | -0.017 |
| 2023 | 0.00393 | -0.00002 | 0.355 | 0.019 |
| 2024 | 0.01164 | -0.00023 | 0.276 | -0.013 |
| 2025 | 0.01518 | 0.00043 | 0.276 | 0.026 |

P derives from `whySpecial`; it does not identify lending partners or show that confounding has been removed. All paired Brier and country intervals, staged M/L contrasts, reliability-bin counts and subgroup diagnostics are available in the [reviewed aggregate report](../reports/text_benchmark_reviewed/benchmark.json) and [maintained notebook](../notebooks/2_full_dataset_modeling.ipynb).

| 2025 model | MAE days | Day-space R² | ROC AUC | Brier |
| --- | --- | --- | --- | --- |
| linear S | 6.4063 | -0.4189 | 0.8931 | 0.1598 |
| linear S+M+L+R | 6.1465 | -0.3147 | 0.8883 | 0.1446 |
| histogram_boosting S | 4.8746 | 0.4644 | 0.9091 | 0.1274 |
| histogram_boosting S+M+L | 4.8328 | 0.4765 | 0.9083 | 0.1270 |

In 2025, adding the full text block improves linear-model MAE and Brier score,
while AUC falls from 0.8931 to 0.8883 and day-space R² remains negative.
Improvement in one loss does not establish improvement in ranking or tail
error. In plain terms: text makes the typical forecast a little closer and the
probabilities a little better calibrated, but it slightly worsens how well the
model orders loans from fastest to slowest.

**2025 loss-alignment check (2026-11-08).** The negative day-space R² comes from the
back-transform. In 2025 that works through over-prediction rather than undershoot of long waits. The same
linear fits score R² 0.330 and 0.433 in log space, and Ridge on raw days
scores 0.165 and 0.296 in day space. After exponentiating,
69%–75% of squared error is over-prediction, and predictions reach
1,394 days against a 2025 maximum of 79.5. Capping at the training maximum
lifts R² to -0.079 and -0.099; Duan smearing lowers it to -2.61 and -1.86.
Text lowers MAE under every target, but the size depends on the estimator: 0.26 days on this
estimator and 1.13 on raw days, which has a weaker baseline (MAE 8.14). With the cap, text
slightly worsens RMSE. See the [check](../reports/loss_alignment_2025/README.md). Extreme
predictions need attention before any operational use.

**All five years (exploratory).** Day-space R² is negative under log1p in every year while log-space and raw-days
R² are positive, but the mechanism varies: 2021 is mostly under-prediction, and 2022–2025 mostly over-prediction.
In 2023, 48 records with no description reach predictions of 22,436 days; without them the 2023 gain is 0.364, not
0.259. Capping predictions at the training maximum keeps the MAE gain positive every year (0.265–0.405) and the
country interval excludes zero in 4 of 5 years, against 1 of 5 uncapped. So much of the country fragility comes from
the extreme tail. The cap was chosen after seeing results and does not replace the reviewed figures above. Removing
any one country leaves the gain positive, and over 99% of described evaluation rows use an exact template unseen in training.
See the [check](../reports/loss_alignment_2025/README.md) and [sources](../reports/evidence_sources/README.md).

Both duration families minimise squared error on log1p days and then exponentiate predictions, clipping negative days at zero. This is not generally a conditional mean-days estimate. MAE, RMSE, R² and tail errors answer different questions. No separate probability calibration model or capacity-based allocation policy was fitted.

## Training availability and population

The input contains 1,453,846 records; 1,453,840 have valid completed durations after excluding six negative intervals. The main population retains 1,637 refunded records. There are no duplicated loan IDs, 39,088 missing descriptions, and 5,165 rows belonging to repeated normalised nonblank descriptions. Missing descriptions remain in all matched arms.

The five disjoint evaluation cohorts contain 728,640 records in total; earlier eligible records supply training history.

| Evaluation year | Pre-cutoff postings completing at/after cutoff | Eligible as-of training | Evaluation rows |
| --- | --- | --- | --- |
| 2021 | 7,528 | 717,672 | 163,166 |
| 2022 | 3,918 | 884,448 | 143,354 |
| 2023 | 3,546 | 1,028,174 | 143,233 |
| 2024 | 5,691 | 1,169,262 | 141,725 |
| 2025 | 4,261 | 1,312,417 | 137,162 |

The 2024 replay excludes 5,691 training records that a posting-only split would retain. This quantifies unavailable completed-cohort membership; it does not isolate the effect on the original model’s performance. Multiple specifications changed, so the new scores must not be presented as a controlled before/after correction of August metrics.

Evaluation windows span observed postings in each of 2021–2025. They still select eventual completions. Snapshot field values and narrative versions are not verified listing-time histories. Country PPP and cumulative lending were excluded because their historical availability was unverified. Refunded-only slices below 200 rows are suppressed; funded-only diagnostic errors do not constitute a separately retrained exclusion sensitivity.

## What to do next

1. **Validate the measures.** Develop a small codebook for clarity, specificity, need and agency; independently dual-code development-period narratives, analyse disagreements, then freeze definitions before auditing later periods. Lexicon counts and TF-IDF need not represent the proposed psychological mechanism.
2. **Resolve the decision and missing process data.** Request original text versions, verified partner identifiers, exposure and all-listing outcomes. Agree whether the use is content support, research diagnosis or allocation before choosing thresholds or calibration.
3. **Design one feasible intervention.** With participating partners, define a truthful clarity prompt, control condition, assignment unit, observation horizon, practical benefit threshold, power and guardrails. Include unsuccessful and censored listings, and assess attention displacement. A predictive gain does not identify who benefits from editing.

This follows the consulting sequence in the [research review](4_research_review.md): define the decision, decompose mechanisms, compare options against evidence, and advance only when the next decision has adequate support. More model complexity is useful only if it answers a specific unresolved requirement.

## Reproduction and evidence boundaries

The fixed protocol produced 65 model/arm windows, each with duration and 24-hour outcomes, using expanding training histories, seed 42 and no evaluation-dependent tuning. All preprocessing was fitted on training rows. Sparse text stayed sparse; tree inputs were compact. See the [frozen implementation plan](superpowers/plans/2026-11-02-matched-text-benchmark.md) and [bundle README](../reports/text_benchmark_reviewed/README.md) for commands and technical review.

The full-data run is separate from notebook execution: the notebook’s default mode validates the reviewed bundle and executes insight tables/charts without silently retraining. The committed source pair is output-free. Private prediction archives support independent metric and interval recomputation; only selected aggregates, source code and provenance are included for review.

August primary reports, the recovered September extension and October explanatory sensitivity retain their existing status. All five new windows are retrospective, including previously examined 2024–2025. No untouched external test, human annotation results, all-listing model or measured editing effect is claimed.

Use the [new deck](presentation/research_refresh/output/cultural-blend-matched-benchmark.pptx) and [slide-by-slide brief](presentation/research_refresh/slide_brief_benchmark.md) for this update. The earlier research-design deck remains preserved.
