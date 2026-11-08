# Claims register

Every number the portfolio deck and case study quote, with its source file and
evidence layer. Created 2026-11-08. A slide or paragraph may only quote a number
listed here; add the row first, with its source, before using a new one.

Slide names for the layers (decided 2026-11-08): August = **Explanatory models**,
October = **Robustness checks**, November = **Forecast benchmark**, Equivalence =
**Equivalence test**. The layer column below keeps the run names for provenance.

Layers: **August** = primary saved run (2026-08-31, `src/` pipeline).
**October** = reviewed explanatory sensitivity. **November** = matched predictive
benchmark. **Equivalence** = exploratory screen of October coefficients (2026-11-08).
**Descriptive** = EDA or data-dictionary audit, not a model result.

## Population and outcome

| Claim | Value | Source | Layer |
| --- | --- | --- | --- |
| Rounded record count | 1.45 million | rounds the rows below | August |
| Input records | 1,453,846 | `reports/generated_full_dataset/association_summary.txt` (audit trail) | August |
| Valid completed durations | 1,453,840 (6 negative durations excluded) | same | August |
| Refunded records included | 1,637 | same | August |
| Posting window | 2016-01-01 to 2025-12-31 | same | August |
| Period definitions | pre-pandemic 2016–2019; pandemic 2020–2021; post-pandemic 2022–2025 ("four years") | `src/data_loader.py` | August |
| Loans by period | 589,823 pre-pandemic; 298,549 pandemic; 565,474 post-pandemic | same | August |
| Same-day share by period | 46.0% → 30.3% → 30.0% | `notebooks/1_full_dataset_eda.py` §period trend | Descriptive |
| Yearly same-day share (records) | 2016 43.3% (129,660); 2017 48.7% (162,622); 2018 48.8% (153,492); 2019 42.5% (144,043); 2020 32.3% (135,383); 2021 28.7% (163,166); 2022 29.9% (143,354); 2023 27.5% (143,233); 2024 27.5% (141,725); 2025 35.4% (137,162); 2025 may be incomplete (unfunded loans missing at extraction) | `reports/period_trend/yearly_same_day_share.json` | Descriptive |
| Overall same-day share | 36.6% | `association_summary.txt` | August |
| Illustrative listing values (slide 4) | median loan US$325; median term 12 months; median borrowers 1; most common sector Agriculture (461,563); most common country Philippines (521,586) | `reports/text_benchmark_private/features.pkl`, eligible records (2026-11-08) | Descriptive |
| Framing families measured | 8 rates per 100 words | `src/features.py` `FRAMING_PATTERNS` | Descriptive |
| Funding duration, eligible records | median 2.85 days; interquartile range 0.39–15.95 days | `reports/text_benchmark_private/features.pkl` (2026-11-08) | Descriptive |
| Funded and refunded counts | 1,452,203 funded; 1,637 refunded | `features.metadata.json` audit | August |
| Disbursed after listing | 3.6% (100% − 96.4%) | derived from the row below | Descriptive |
| Pre-disbursal share | 96.4% (median 24.2 days before listing) | `docs/1_data_dictionary.md` (`disbursalDate`) | Descriptive |
| Country clusters | 48 | `reports/expanded_feature_sensitivity_reviewed/README.md` | October |

## Explanatory uncertainty

| Claim | Value | Source | Layer |
| --- | --- | --- | --- |
| Terms significant under HC3 that lose significance under country clustering | 64 of 120 (across both models, 128 terms tested) | `association_summary.txt`, sensitivity blocks (recounted 2026-11-08) | August |
| Lost significance by term type | text terms 42 of 56; control terms 22 of 64 (text includes interactions with a text measure) | `reports/evidence_sources/clustering_split.json` (`src/clustering_split.py`) | August |
| Country concentration | top 10 countries 81.0% of eligible loans; Philippines 35.9%; Kenya 18.3%; 48 countries | `reports/evidence_sources/country_shares.json` (`src/country_shares.py`) | Descriptive |
| Urgency, clustered p | duration 0.4943; 24-hour 0.2233 | `association_summary.txt` | August |
| Middle East family slope | −0.0729, 2 countries, 14,946 loans, heuristic interval [−0.2502, 0.1043] | `docs/2_evidence_and_corrections.md` | August |
| Central America family slope | −0.0742, 2 countries, 59,391 loans, heuristic interval [−0.1629, 0.0145] | same | August |
| Regional clustered normal intervals and heuristic p | Middle East [−0.1003, −0.0456], p 0.1203; Central America [−0.0879, −0.0605], p 0.0597 | same | August |
| Urgency under HC3 | p < 0.001, printed as 0.0000; clustered duration p rounded to 0.49 | `association_summary.txt` | August |
| Third-person framing, duration | −0.009008 → −0.008088 with programme controls; BH p 0.01236 → 0.06062 | `reports/expanded_feature_sensitivity_reviewed/README.md` | October |
| Business framing, 24-hour, programme-adjusted | −0.258 pp per mention per 100 words, BH p 0.00635 | same | October |
| Rounded BH p for slides | third person 0.012 → 0.061; business 0.006; threshold 0.05 | same | October |
| Third-person duration rounded estimates | −0.0090 → −0.0081 | same | October |
| Programme categories | 642 nonblank; 590 confined to one country; 40,012 missing | `docs/2_evidence_and_corrections.md` | October |

## Equivalence screen

| Claim | Value | Source | Layer |
| --- | --- | --- | --- |
| Bounded within ±5% of (1 + days) and ±1 pp per mention per 100 words, both specifications | family, basic needs, business, agency, third person | `reports/equivalence_screen_reviewed/README.md` | Equivalence |
| Unresolved in every fit | urgency, first person | same | Equivalence |
| Urgency 90% interval, expanded duration | −0.048 [−0.126, +0.030] log points per mention per 100 words | `equivalence_screen.csv` | Equivalence |
| Expanded duration estimates, 90% intervals (slide 9) | agency 0.0042 [−0.0028, 0.0112]; basic needs 0.0021 [−0.0190, 0.0233]; business 0.0090 [−0.0027, 0.0207]; family 0.0096 [−0.0005, 0.0197]; third person −0.0090 [−0.0130, −0.0050]; gratitude 0.0163 [−0.0701, 0.1027]; sentiment per +0.5 0.0272 [0.0026, 0.0519]; first person −0.0723 [−0.1431, −0.0016]; urgency −0.0482 [−0.1259, 0.0295] | `equivalence_screen.csv` | Equivalence |
| Intervals reach, urgency and first person | 6–14% of (1 + days) per mention, across both specifications | `reports/equivalence_screen_reviewed/README.md` | Equivalence |
| Feature SD, eligible records | urgency 0.102; first person 0.190; third person 3.247; family 1.676; business 2.549; basic needs 2.370 mentions per 100 words | `reports/equivalence_screen_reviewed/feature_distribution.json` | Descriptive |
| Share of records with no mention | urgency 98.7%; first person 99.0%; "over 98%" covers each | same | Descriptive |
| Median words, records with a description | 92 | same | Descriptive |
| Urgency per 1 SD, expanded duration, 90% interval | [−0.0128, 0.0030] log points; SD scale only, not a feasible edit | same | Equivalence |

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
| Linear MAE by year, S → S+M+L+R | 2021 8.250 → 7.957; 2022 8.570 → 8.197; 2023 8.185 → 7.926; 2024 7.515 → 7.126; 2025 6.406 → 6.147 | `docs/6_matched_text_results.md` | November |
| Linear MAE gain, month 95% intervals | 2021 0.293 [0.198, 0.384]; 2022 0.372 [0.208, 0.518]; 2023 0.259 [0.088, 0.406]; 2024 0.389 [0.287, 0.500]; 2025 0.260 [0.139, 0.396] | same | November |
| Tree MAE gain, month 95% intervals | 2021 0.035 [−0.073, 0.137]; 2022 0.028 [−0.036, 0.084]; 2023 0.006 [−0.025, 0.035]; 2024 0.001 [−0.020, 0.025]; 2025 0.042 [0.013, 0.074] | same | November |
| Rounded linear gain range and median | 0.26–0.39 days; 0.29 days; median 0.293 days × 24 ≈ 7 hours | same | November |
| 2025 rounded AUC | 0.893 → 0.888 | same | November |
| As-of cohort, pre-cutoff completing later; eligible training; evaluation rows | 2021 7,528; 717,672; 163,166. 2022 3,918; 884,448; 143,354. 2023 3,546; 1,028,174; 143,233. 2024 5,691; 1,169,262; 141,725. 2025 4,261; 1,312,417; 137,162 | same | November |

## Loss alignment, 2025

Separate extension of the November benchmark; S → S+M+L+R; `reports/loss_alignment_2025/README.md`.

| Claim | Value | Layer |
| --- | --- | --- |
| Log-space R², same fits | 0.330 → 0.433 | November extension |
| Raw-days target | MAE 8.1430 → 7.0134; R² 0.1652 → 0.2960; MAE text gain 1.1296 | November extension |
| Duan smearing | MAE 10.0613 → 8.6351; R² -2.6140 → -1.8556 | November extension |
| Capped at training maximum (173.4 days), diagnostic | R² -0.0794 → -0.0986; RMSE text gain -0.0980 | November extension |
| Share of squared error from over-prediction | 74.7% → 69.0% | November extension |
| Largest prediction, observed 2025 maximum | 1,394 → 714 days; 79.5 days | November extension |

## Exploratory checks, 2026-11-08

Chosen after results were known. `reports/evidence_sources/README.md`; `reports/loss_alignment_2025/README.md`.

| Claim | Value | Layer |
| --- | --- | --- |
| Effective countries, all records | 5.7 of 48; 10 countries hold 80% of records | Descriptive |
| Effective countries, term users | urgency 7.1; first person 11.3 | Descriptive |
| Equivalence screen at t(4) | 21 of 23 bounded results hold; all five duration verdicts hold | Equivalence, heuristic |
| 2023 gain without 48 records with no description | 0.364 days (0.259 all records); largest prediction 22,436 days | November extension |
| Capped MAE gain, all years | 0.324, 0.377, 0.277, 0.405, 0.265 days (2021–2025) | November extension, diagnostic |
| Country interval includes zero | uncapped 4 of 5; capped 1 of 5 | November extension, diagnostic |
| Described rows with unseen exact template | at least 99.2% each year (96.0% of all rows in 2021) | November extension |
| Leave-one-country-out gain | positive in every year; lowest 0.155 days | November extension |

## Exploratory topics

| Claim | Value | Source | Layer |
| --- | --- | --- | --- |
| NMF themes, 20,000-loan sample, unadjusted means | 8 themes; 1.5 days (sanitation) to 13.5 days (group solar and farm plots) | `docs/presentation/qa_answers.md`, `notebooks/1_full_dataset_eda.py` | Descriptive, sample only |

## Retired — do not quote

"The story barely registers", "robust null", "won't move the needle", "myth busted",
"structure beats story ~10×", LightGBM, "SHAP top 10/15 has no narrative feature",
"sign reversal" for third-person framing, country-level A/B advice from two-country
regions, and the 20,000-loan topic results as full-data evidence.
See `docs/2_evidence_and_corrections.md` and `docs/4_research_review.md`.
