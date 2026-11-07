# Claims register

Every number the portfolio deck and case study quote, with its source file and
evidence layer. Created 2026-11-08. A slide or paragraph may only quote a number
listed here; add the row first, with its source, before using a new one.

Layers: **August** = primary saved run (2026-08-31, `src/` pipeline).
**October** = reviewed explanatory sensitivity. **November** = matched predictive
benchmark. **Equivalence** = exploratory screen of October coefficients (2026-11-08).
**Descriptive** = EDA or data-dictionary audit, not a model result.

## Population and outcome

| Claim | Value | Source | Layer |
| --- | --- | --- | --- |
| Input records | 1,453,846 | `reports/generated_full_dataset/association_summary.txt` (audit trail) | August |
| Valid completed durations | 1,453,840 (6 negative durations excluded) | same | August |
| Refunded records included | 1,637 | same | August |
| Posting window | 2016-01-01 to 2025-12-31 | same | August |
| Loans by period | 589,823 pre-pandemic; 298,549 pandemic; 565,474 post-pandemic | same | August |
| Same-day share by period | 46.0% → 30.3% → 30.0% | `notebooks/1_full_dataset_eda.py` §period trend | Descriptive |
| Overall same-day share | 36.6% | `association_summary.txt` | August |
| Pre-disbursal share | 96.4% (median 24.2 days before listing) | `docs/1_data_dictionary.md` (`disbursalDate`) | Descriptive |
| Country clusters | 48 | `reports/expanded_feature_sensitivity_reviewed/README.md` | October |

## Explanatory uncertainty

| Claim | Value | Source | Layer |
| --- | --- | --- | --- |
| Terms significant under HC3 that lose significance under country clustering | 64 of 120 (across both models, 128 terms tested) | `association_summary.txt`, sensitivity blocks (recounted 2026-11-08) | August |
| Urgency, clustered p | duration 0.4943; 24-hour 0.2233 | `association_summary.txt` | August |
| Middle East family slope | −0.0729, 2 countries, 14,946 loans, heuristic interval [−0.2502, 0.1043] | `docs/2_evidence_and_corrections.md` | August |
| Central America family slope | −0.0742, 2 countries, 59,391 loans, heuristic interval [−0.1629, 0.0145] | same | August |
| Third-person framing, duration | −0.009008 → −0.008088 with programme controls; BH p 0.01236 → 0.06062 | `reports/expanded_feature_sensitivity_reviewed/README.md` | October |
| Business framing, 24-hour, programme-adjusted | −0.258 pp per mention per 100 words, BH p 0.00635 | same | October |
| Programme categories | 642 nonblank; 590 confined to one country; 40,012 missing | `docs/2_evidence_and_corrections.md` | October |

## Equivalence screen

| Claim | Value | Source | Layer |
| --- | --- | --- | --- |
| Bounded within ±5% of (1 + days) and ±1 pp per mention per 100 words, both specifications | family, basic needs, business, agency, third person | `reports/equivalence_screen_reviewed/README.md` | Equivalence |
| Unresolved in every fit | urgency, first person | same | Equivalence |
| Urgency 90% interval, expanded duration | −0.048 [−0.126, +0.030] log points per mention per 100 words | `equivalence_screen.csv` | Equivalence |

## Prediction

| Claim | Value | Source | Layer |
| --- | --- | --- | --- |
| Chronological split | 1,174,953 train; 278,887 holdout (2024–2025) | `association_summary.txt` | August |
| Nonlinear duration benchmark (HistGradientBoosting) | MAE 5.2031 days; R² 0.5420 | `docs/2_evidence_and_corrections.md`, `analysis_summary.json` | August |
| 24-hour classifier (HistGradientBoostingClassifier) | ROC AUC 0.8997; AP 0.8301; Brier 0.1156 | `association_summary.txt` | August |
| Evaluation records, five annual windows | 728,640 (2021–2025) | `docs/6_matched_text_results.md` | November |
| Linear MAE gain from adding text (S → S+M+L+R) | 5 of 5 years; 0.259–0.389 days; median 0.293 | same | November |
| Tree MAE gain (S → S+M+L) | 0.001–0.042 days | same | November |
| Country-resampling intervals including zero | 4 of 5 linear; 3 of 5 tree | same | November |
| 2025 linear AUC | 0.8931 (S) → 0.8883 (S+M+L+R) | same | November |
| 2025 tree MAE | 4.8746 (S) → 4.8328 (S+M+L) | same | November |
| 2024 as-of exclusion | 5,691 training records | same | November |

## Retired — do not quote

"The story barely registers", "robust null", "won't move the needle", "myth busted",
"structure beats story ~10×", LightGBM, "SHAP top 10/15 has no narrative feature",
"sign reversal" for third-person framing, country-level A/B advice from two-country
regions, and the 20,000-loan topic results as full-data evidence.
See `docs/2_evidence_and_corrections.md` and `docs/4_research_review.md`.
