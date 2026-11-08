# Exploratory experiments, 2026-11-08

Post-competition checks requested for the portfolio deck (gaps A–I). All are
exploratory, chosen after earlier results were known, and have had no
independent review. Population: 1,453,840 eligible completed durations unless
stated. Unfunded or expired listings are not in the data. Everything is an
association. Nothing here replaces the August primary, October reviewed or
November benchmark results. JSON files hold aggregates only.

Compute: three private Kaggle CPU kernels, `kiva-hackathon-experiments-{inference,forecast,loan-details}`
(`notebooks/kernels/experiments_*`), recorded in `kaggle_provenance_*.json`. A, E and H were computed locally from saved files.

| Gap | File | Code | Result |
| --- | --- | --- | --- |
| A | `primary_family_interactions.json` | `src/primary_interactions.py` | No family × period or × loan-size interaction clears p < 0.05 under country clustering (clustered p 0.11–0.92). |
| B | `subgroup_programme_adjusted.json`, `subgroup_expanded.json` | `src/subgroup_inference.py` | Programme-adjusted, duration: family, basic needs, business, agency, gratitude and third person stay within ±5% in all 10 subgroups; urgency in 1 of 10. Unadjusted across subgroups. |
| C, G | `wild_cluster.json` | `src/wild_cluster.py` | Equivalence verdicts unchanged in 35 of 36 rows (22 of 23 bounded results hold). No term is below 0.05 after BH within nine terms (lowest 0.136). |
| D | `text_placebo.json` | `src/text_placebo.py` | Shuffling text within country × sector × month keeps 42–61% of the linear gain. |
| E | `gain_breakdown.json` | `src/gain_breakdown.py` | TF-IDF carries most of the linear gain in 4 of 5 years. |
| F | `strong_forecaster_large.json`, `strong_forecaster_benchmark_tree.json` | `src/strong_forecaster.py` | Larger boosted tree text gain −0.011 to 0.154 days MAE; country intervals exclude zero only in 2021. |
| H | `triage_value.json` | `src/triage_value.py` | Structure-only boosted tree, flag top 10%: precision 0.53–0.81 for the slowest 20% (lift 2.6–4.0). Text adds about nothing on the tree. |
| I | `loan_detail_coefficients.json` | `src/loan_detail_coefficients.py` | Loan-detail coefficients from the October programme-adjusted model; see below. |

## Checks that the reruns match saved evidence

- C: all 36 point estimates and clustered standard errors match the October tables.
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
