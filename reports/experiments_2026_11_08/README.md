# Exploratory experiments, 2026-11-08

Post-competition checks requested for the portfolio deck (gaps A–I). All are
exploratory and chosen after earlier results were known. One independent code
review (Codex, 2026-11-08) is recorded below. Population: 1,453,840 eligible completed durations unless
stated. Unfunded or expired listings are not in the data. Everything is an
association. Nothing here replaces the August primary, October reviewed or
November benchmark results. JSON files hold aggregates only.

Compute: private Kaggle CPU kernels, `kiva-hackathon-experiments-{inference,forecast,loan-details,review-fix}`
(`notebooks/kernels/experiments_*`), recorded in `kaggle_provenance_*.json`. A, E and H were computed locally from saved files.

| Gap | File | Code | Result |
| --- | --- | --- | --- |
| A | `primary_family_interactions.json` | `src/primary_interactions.py` | No family × period or × loan-size interaction clears p < 0.05 under country clustering (clustered p 0.11–0.92). |
| B | `subgroup_programme_adjusted.json`, `subgroup_expanded.json` | `src/subgroup_inference.py` | Programme-adjusted, duration, t(G−1): family, basic needs, business, agency, gratitude and third person stay within ±5% in all 10 subgroups; urgency in 1 of 10. Unadjusted across subgroups; the bootstrap row below is stricter and supersedes these counts. |
| C, G | `wild_cluster.json` | `src/wild_cluster.py` | Equivalence verdicts unchanged in 35 of 36 rows (22 of 23 bounded results hold). After BH within nine terms, one of 36 tests passes: third person, expanded, duration (BH p 0.008, −0.9% per mention); with programme controls its BH p is 0.426. |
| D | `text_placebo.json` | `src/text_placebo.py` | Shuffling text within country × sector × month keeps 42–61% of the linear gain. |
| E | `gain_breakdown.json` | `src/gain_breakdown.py` | TF-IDF carries most of the linear gain in 4 of 5 years. |
| F | `strong_forecaster_large.json`, `strong_forecaster_benchmark_tree.json` | `src/strong_forecaster.py` | Larger boosted tree text gain −0.011 to 0.154 days MAE; country intervals exclude zero only in 2021. |
| H | `triage_value.json` | `src/triage_value.py` | Structure-only boosted tree, flag top 10%: precision 0.53–0.81 for the slowest 20% (lift 2.6–4.0). Text adds about nothing on the tree. |
| B (bootstrap) | `subgroup_bootstrap.json` | `src/subgroup_bootstrap.py` | Corrected wild bootstrap within each subgroup. Programme-adjusted, funding time, within ±5%: family and third person in all 10 subgroups; business and agency 9; sentiment 7; basic needs and gratitude 5; first person 4; urgency 0. Stricter than the t(G−1) counts in row B. |
| Appendix | `appendix_experiments.json` | `src/appendix_experiments.py` | Tuned HistGradientBoosting and XGBoost (tuned on earlier years only), the flag on fixed and tuned models, and NMF themes. See below. |
| I | `loan_detail_coefficients.json` | `src/loan_detail_coefficients.py` | Loan-detail coefficients from the October programme-adjusted model; see below. |

## Checks that the reruns match saved evidence

- C (rerun): all 36 point estimates and clustered standard errors match the October tables.
- F: the benchmark-tree rerun matches the saved S and S+M+L MAE to four decimals.
- I: same 23 narrative terms as the saved table, 906 parameters, 1,453,840 rows, 48 clusters, no rank drops.
  The eight mention-rate framing coefficients match within 1e-7 and the sentiment coefficient within 2e-6
  (`comparison_with_saved_october_table`). They are not bit-identical: the solver stops at a 1e-10 tolerance.
- D: real gains differ from the saved benchmark in the third decimal (for example 0.292 vs 0.293 in 2021),
  probably from the different numerical environment. Use the benchmark figures for headlines.

## Reading experiment I

Duration percentages are changes in (1 + days), from exp(b) − 1, with country-clustered CR1 standard errors and a
t(47) reference. The 24-hour model is a linear probability model, in percentage points. Absorbed: country, posting year and month, programme proxy.
Loan amount and loan-size band are in the model together, so "per doubling" is within a band, and band
contrasts are jumps at fixed log amount. Borrower count and group loan are joint. Activity contrasts use Farming as
the reference; sector contrasts compare a sector's loan-weighted activities with the overall average.
No importance ranking or loan-details-to-framing ratio is computed. These are retired claims.

## Independent review, 2026-11-08

A read-only Codex review of the code and aggregates found three problems, all fixed in commit c9883da:

1. **High, wild cluster bootstrap.** Bootstrap t statistics did not remove shared controls from cluster-flipped residuals. Coefficients and observed standard errors were unaffected. `wild_cluster.json` is now the corrected rerun (`review-fix` kernel); the earlier file is in git history. Tests confirm the fast statistics match a full-model refit, including with rank-deficient nested programme dummies. The main change: third person, expanded, duration moved from BH p 0.136 to 0.008, so "no term survives" no longer holds for that one specification.
2. **Medium, triage interval.** The month-block interval held flags fixed. It now reselects flags and the slowest-20% target in each draw. In `triage_value.json` the boosted tree's 2025 duration interval now excludes zero ([0.001, 0.013]); point precision, recall and lift are unchanged.
3. **Low, loan amount.** "Per doubling" now uses the exact log1p edit at the median amount (US$325 to US$650): duration +44.6% [+32.3, +58.1], 24-hour −14.8 pp [−19.0, −10.5].

## Appendix experiments

Tuning selected settings on the year before each test year, on the structure-only arm. Validation uses only loans completed before the test cutoff, so it favours faster loans. Tuning did not reliably lower error against the fixed trees; the lowest-error model changes by year. Text gain on tuned trees ranges from −0.039 to 0.220 days, below the linear model's 0.26–0.39 in every year. Themes are sample results on the EDA 20,000 descriptions. The saved run is from clean commit c8df3b8 (`kaggle_provenance_appendix.json`). It matches the first run, whose code dataset also held an unrelated uncommitted file, within 1e-9 on every value.
