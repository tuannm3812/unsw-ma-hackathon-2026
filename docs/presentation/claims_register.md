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
| Median wait to full funding by posting year, days (slide 4) | 2016 1.72; 2017 1.11; 2018 1.10; 2019 1.72; 2020 4.57; 2021 5.14; 2022 4.66; 2023 5.35; 2024 4.49; 2025 2.56 | `reports/period_trend/yearly_same_day_share.json` (`src/period_trend.py`) | Descriptive |
| Share and number of loans waiting over two weeks (14 days) by posting year (slide 4) | 2016 23.0% (29,827); 2017 18.9% (30,670); 2018 20.1% (30,894); 2019 19.2% (27,620); 2020 35.8% (48,504); 2021 34.0% (55,408); 2022 32.5% (46,530); 2023 33.6% (48,102); 2024 31.3% (44,379); 2025 23.3% (31,913); 2025 may be incomplete | same | Descriptive |
| Largest one-year fall in same-day share | 2019 → 2020: 42.5% → 32.3%, 10.2 percentage points | derived from the yearly same-day row | Descriptive |
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
| Top 10 countries: loans (share, same-day share) | Philippines 521,586 (35.9%, same-day 48%); Kenya 266,562 (18.3%, same-day 29%); Uganda 69,651 (4.8%, same-day 31%); Tajikistan 68,865 (4.7%, same-day 18%); Cambodia 58,074 (4.0%, same-day 49%); Madagascar 55,670 (3.8%, same-day 67%); Pakistan 42,767 (2.9%, same-day 15%); Nicaragua 38,520 (2.6%, same-day 15%); Liberia 28,847 (2.0%, same-day 28%); Togo 27,513 (1.9%, same-day 38%); other 38 countries 275,785 (19.0%) | `reports/evidence_sources/country_shares.json` | Descriptive |
| Loans by Kiva region (slide 8) | Asia 50.8%; Africa 42.0%; Central America 4.1%; Oceania 1.6%; Middle East 1.0%; North America 0.5%; Asia and Africa together 92.8% | `reports/evidence_sources/country_shares.json` (`src/country_shares.py`, Kiva `region` field) | Descriptive |
| Top 10 countries by Kiva region | Asia: Philippines, Tajikistan, Cambodia, Pakistan; Africa: Kenya, Uganda, Madagascar, Liberia, Togo; Central America: Nicaragua | same | Descriptive |
| Loans waiting over two weeks, all years (slide 5) | 393,847 of 1,453,840 (27.1%) | `reports/evidence_sources/country_shares.json` (`src/country_shares.py`) | Descriptive |
| Countries with the most loans waiting over two weeks (slide 5) | Kenya 96,997 (24.6% of all long waits; 36.4% of its loans; median 5.80 days); Philippines 89,412 (22.7% of all long waits; 17.1% of its loans; median 1.13 days); Tajikistan 34,434 (8.7% of all long waits; 50.0% of its loans; median 14.00 days); Uganda 24,372 (6.2% of all long waits; 35.0% of its loans; median 4.68 days); Nicaragua 17,580 (4.5% of all long waits; 45.6% of its loans; median 11.40 days); Pakistan 16,474 (4.2% of all long waits; 38.5% of its loans; median 8.32 days) | same | Descriptive |
| Share of long waits in the top three countries (Kenya, Philippines, Tajikistan) | 56.1%; top 10 countries by loans hold 77.0% | same | Descriptive |
| Loans by wait band, within 24 hours / 1 day to 2 weeks / over 2 weeks (slide 5) | Kenya 77,721 / 91,844 / 96,997; Philippines 250,124 / 182,050 / 89,412; Tajikistan 12,492 / 21,939 / 34,434; Uganda 21,648 / 23,631 / 24,372; Nicaragua 5,859 / 15,081 / 17,580; Pakistan 6,405 / 19,888 / 16,474 | `reports/evidence_sources/country_shares.json` (`src/country_shares.py`) | Descriptive |
| Terms that kept significance | 56 of 120; 42 controls, 14 text (sentiment in both models plus 12 family-framing interactions) | `reports/evidence_sources/clustering_split.json` | August |
| Urgency, clustered p | duration 0.4943; 24-hour 0.2233 | `association_summary.txt` | August |
| Middle East family slope | −0.0729, 2 countries, 14,946 loans, heuristic interval [−0.2502, 0.1043] | `docs/2_evidence_and_corrections.md` | August |
| Central America family slope | −0.0742, 2 countries, 59,391 loans, heuristic interval [−0.1629, 0.0145] | same | August |
| Regional clustered normal intervals and heuristic p | Middle East [−0.1003, −0.0456], p 0.1203; Central America [−0.0879, −0.0605], p 0.0597 | same | August |
| Family slopes as % of (1 + days) (appendix A1) | Middle East −7.03% ("about 7% faster"); Central America −7.15% | `reports/evidence_sources/region_context.json` (`src/region_context.py`) | August, derived |
| Countries per Kiva region (appendix A1) | Africa 27; Asia 12; Oceania 4; Central America 2; Middle East 2; North America 1 | same | Descriptive |
| Country mix of the two-country regions (appendix A1) | Middle East: Palestine 14,500 (97.0%), Yemen 446 (3.0%); Central America: Nicaragua 38,520 (64.9%), Honduras 20,871 (35.1%) | same | Descriptive |
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
| Expanded duration estimates, 90% intervals (slide 10) | agency 0.0042 [−0.0028, 0.0112]; basic needs 0.0021 [−0.0190, 0.0233]; business 0.0090 [−0.0027, 0.0207]; family 0.0096 [−0.0005, 0.0197]; third person −0.0090 [−0.0130, −0.0050]; gratitude 0.0163 [−0.0701, 0.1027]; sentiment per +0.5 0.0272 [0.0026, 0.0519]; first person −0.0723 [−0.1431, −0.0016]; urgency −0.0482 [−0.1259, 0.0295] | `equivalence_screen.csv` | Equivalence |
| Intervals reach, urgency and first person | 6–14% of (1 + days) per mention, across both specifications | `reports/equivalence_screen_reviewed/README.md` | Equivalence |
| Feature SD, eligible records | urgency 0.102; first person 0.190; third person 3.247; family 1.676; business 2.549; basic needs 2.370 mentions per 100 words | `reports/equivalence_screen_reviewed/feature_distribution.json` | Descriptive |
| Share of records with no mention | urgency 98.7%; first person 99.0%; "over 98%" covers each | same | Descriptive |
| Median words, records with a description | 92 | same | Descriptive |
| Urgency per 1 SD, expanded duration, 90% interval | [−0.0128, 0.0030] log points; SD scale only, not a feasible edit | same | Equivalence |
| Primary bound in hours (slide 10) | ±0.05 on log(1 + days) at the 2.85-day median: 4.51 hours shorter to 4.74 hours longer ("4.5–4.7 hours") | `reports/evidence_sources/bound_ladder.json` (`src/bound_ladder.py`) | Equivalence, exploratory |
| Bands as share of (1 + days) | ±0.02 ≈ ±2% (2.02); ±0.05 ≈ ±5% (5.13); ±0.10 ≈ ±10% (10.52) | same | Equivalence, exploratory |
| Tightest bound held, expanded duration (slide 10) | ±0.02: family, agency, third person; ±0.05: basic needs, business; ±0.10: sentiment; none: gratitude, urgency, first person. Counts 3 / 5 / 6 of 9 | same; ±0.05 BH-adjusted, ±0.02 and ±0.10 unadjusted flags | Equivalence, exploratory |
| Tightest bound held, programme-adjusted duration | ±0.02: family, basic needs, business, agency, third person; ±0.05: gratitude, sentiment; ±0.10: urgency, first person. Counts 5 / 7 / 9 of 9 | same | Equivalence, exploratory |
| Share of records with no mention, all nine terms (slide 10) | third person 2.7%; sentiment 3.4% (score exactly zero); family 11.3%; business 15.0%; agency 45.9%; basic needs 76.7%; gratitude 80.4%; urgency 98.7%; first person 99.0% | same, from `feature_distribution.json` | Descriptive |
| Share of records that mention urgency or first person | urgency 1.3%; first person 1.0%; "under 2%" covers each | complement of the row above | Descriptive |
| Share of records with at least one mention, eight framing measures (slide 7) | family 88.7%; business 85.0%; basic needs 23.3%; agency 54.1%; gratitude 19.6%; urgency 1.3%; first person 1.0%; third person 97.3% | complement of the no-mention row (`feature_distribution.json`) | Descriptive |
| Equivalence reference distribution | t with 47 df on the clustered standard error; stricter heuristic t(4) | `reports/equivalence_screen_reviewed/README.md` | Equivalence |
| Wild cluster bootstrap of the equivalence screen (Webb weights, 9,999 draws, 48 countries) | 35 of 36 verdicts unchanged; 22 of 23 bounded results survive; the one loss is basic needs, programme-adjusted, 24-hour | `reports/evidence_sources/robustness_summary.json` (`src/robustness_summary.py`, from `reports/kaggle_experiments/inference/reports/`) | Equivalence, exploratory |
| One test passes after BH across 36 (corrected bootstrap, slides 9 and 11) | third person, expanded, duration: estimate −0.0090 (−0.9% in 1 + days per extra mention), bootstrap p 0.0009, BH p 0.008. Programme-adjusted: bootstrap p 0.128, BH p 0.426. Lowest BH p among the others 0.156 | `reports/evidence_sources/robustness_summary.json` (`src/robustness_summary.py`), corrected rerun 2026-11-08 | Equivalence, exploratory |
| Bootstrap BH p, business, 24-hour (corrected) | expanded −0.357 pp, BH p 0.156; programme-adjusted −0.258 pp, BH p 0.314 | same | Equivalence, exploratory |
| Tests passing at each stage, p < 0.05 (slide 11): nine measures, two outcomes, two models | 36 tests: 5 pass the clustered t(47) test, 4 the wild cluster bootstrap, 1 the BH-adjusted bootstrap | `reports/evidence_sources/robustness_summary.json` (`src/robustness_summary.py`) | Equivalence, exploratory |
| Third person, shorter funding time per extra mention per 100 words at the 2.85-day median (slide 11) | expanded 49.7 minutes; programme-adjusted 44.7 minutes ("45–50 minutes") | same | Equivalence, exploratory |
| Business, same-day funding per extra mention per 100 words (slide 11) | −0.357 pp expanded; −0.258 pp programme-adjusted ("0.26–0.36 pp lower") | same | Equivalence, exploratory |
| Shrink under programme controls (slide 11) | third person, funding time, 10% (−0.0090 → −0.0081); business, same-day, 28% (−0.357 → −0.258 pp) | same | Equivalence, exploratory |
| Loans with at least one mention (slide 11) | third person 97.3%; business 85.0% | same | Descriptive |
| Subgroups bounded within ±5% (funding time), programme-adjusted model, of 10 (slide 11) | family 10; basic needs 10; business 10; agency 10; gratitude 10; urgency 1; first person 5; third person 10; sentiment 9 | same | Exploratory |
| Subgroups bounded within ±1 pp (24-hour), programme-adjusted model, of 10 | family 9; basic needs 6; business 10; agency 9; gratitude 1; urgency 0; first person 0; third person 10; sentiment 2 | same | Exploratory |
| Subgroups bounded (funding time), expanded model, of 10 | family 10; basic needs 5; business 10; agency 10; gratitude 1; urgency 0; first person 0; third person 10; sentiment 2 | same | Exploratory |
| Subgroup tests and unadjusted hypotheses, programme-adjusted, funding time | 180 tests across both outcomes; agency in female +0.0108 (p 0.0027); agency in male -0.0190 (p 0.0007); urgency in Asia -0.0856 (p 0.0020); unadjusted, exploratory | same | Exploratory |

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
| Larger boosted tree, structure only, MAE against the benchmark-sized tree | lower in 4 of 5 years | `reports/evidence_sources/forecast_experiments.json` (`src/forecast_experiments.py`) | Forecast experiments, exploratory |
| Larger boosted tree, MAE gain from full text, days (month 95% interval) | 2021 0.154 [0.097, 0.212]; 2022 0.059 [0.011, 0.100]; 2023 0.012 [−0.041, 0.067]; 2024 −0.011 [−0.064, 0.037]; 2025 0.064 [0.022, 0.106]; at most about 0.15 days, under 0.07 in four of five years; month intervals exclude zero in 3 of 5 | same | Forecast experiments, exploratory |
| Larger boosted tree, MAE gain from full text, country 95% interval | 2021 [0.071, 0.266]; 2022 [−0.022, 0.153]; 2023 [−0.067, 0.071]; 2024 [−0.090, 0.035]; 2025 [−0.006, 0.159]; exclude zero in 1 of 5 | same | Forecast experiments, exploratory |
| Larger boosted tree, 24-hour Brier gain from full text | 2021 0.0054; 2022 0.0014; 2023 0.0012; 2024 0.0005; 2025 0.0031; positive in 5 of 5 years, all tiny | same | Forecast experiments, exploratory |
| Text placebo, linear MAE gain: context part (text shuffled within country, sector and month), days | 2021 0.121; 2022 0.159; 2023 0.159; 2024 0.220; 2025 0.114; 42–61% of the gain ("about half") | same | Forecast experiments, exploratory |
| Text placebo, loan-specific part of the linear gain, days (month 95% interval) | 2021 0.171 [0.132, 0.216]; 2022 0.213 [0.100, 0.324]; 2023 0.102 [−0.009, 0.188]; 2024 0.165 [0.119, 0.210]; 2025 0.146 [0.102, 0.192]; 0.10–0.21 days; month intervals exclude zero in 4 of 5, country intervals in 2 of 5 | same | Forecast experiments, exploratory |
| Text placebo refit against the benchmark linear gain | within 0.003 days each year; headline gains stay the benchmark's 0.26–0.39 days | same | Forecast experiments, exploratory |
| Triage, Boosted tree, duration, structure only, top 10% flagged vs slowest 20% (slide 15) | precision 2021 0.525; 2022 0.671; 2023 0.697; 2024 0.809; 2025 0.735 (range 0.53–0.81); lift 2021 2.63; 2022 3.36; 2023 3.48; 2024 4.04; 2025 3.67 (range 2.6–4.0×; random = 0.20) | `reports/evidence_sources/triage_summary.json` (`src/triage_summary.py` from `reports/triage_value/triage_value.json`, `src/triage_value.py`) | November, retrospective |
| Triage, Boosted tree, duration: adding text, precision change (slide 15) | -0.003–0.005; month-block interval (flags reselected in each draw, corrected 2026-11-08) includes zero in 4 of 5 years; 2025 +0.005 [0.001, 0.013] | same | November, retrospective |
| Triage, Boosted tree, duration, structure only: within-country precision, 10 largest countries | median 0.49–0.56 across years; range 0.18–0.90 | same | November, retrospective |
| Triage, Boosted tree, 24-hour, structure only, top 10% flagged vs slowest 20% (slide 15) | precision 2021 0.595; 2022 0.655; 2023 0.697; 2024 0.739; 2025 0.679 (range 0.60–0.74); lift 2021 2.98; 2022 3.27; 2023 3.48; 2024 3.69; 2025 3.40 (range 3.0–3.7×; random = 0.20) | `reports/evidence_sources/triage_summary.json` (`src/triage_summary.py` from `reports/triage_value/triage_value.json`, `src/triage_value.py`) | November, retrospective |
| Triage, Boosted tree, 24-hour: adding text, precision change (slide 15) | -0.020–0.008; month-block interval includes zero in 5 of 5 years | same | November, retrospective |
| Lookup baseline (training-only shrunken median by country, sector and month), duration, top 10% flagged vs slowest 20%: lift | 2021 1.97×; 2022 2.12×; 2023 2.50×; 2024 2.74×; 2025 2.58× (1.97–2.74); boosted tree, loan details only, 2.63–4.04; tree higher in 5 of 5 years | `reports/evidence_sources/triage_lookup_summary.json` (`src/triage_lookup_summary.py`), from `reports/experiments_2026_11_08/triage_lookup_baseline.json` | Experiment, retrospective, completed loans only |
| Lookup baseline: median within-country precision | 2021 lookup 0.25, tree 0.52; 2022 lookup 0.28, tree 0.49; 2023 lookup 0.29, tree 0.56; 2024 lookup 0.22, tree 0.50; 2025 lookup 0.26, tree 0.50; lookup 0.22–0.29, tree 0.49–0.56; random 0.20; tree higher in 5 of 5 years | same | Experiment, retrospective, completed loans only |
| Triage, Boosted tree, 24-hour, structure only: within-country precision, 10 largest countries | median 0.44–0.56 across years; range 0.16–0.88 | same | November, retrospective |
| Triage, Linear, duration, structure only, top 10% flagged vs slowest 20% (slide 15) | precision 2021 0.559; 2022 0.556; 2023 0.666; 2024 0.685; 2025 0.679 (range 0.56–0.69); lift 2021 2.80; 2022 2.78; 2023 3.33; 2024 3.43; 2025 3.39 (range 2.8–3.4×; random = 0.20) | `reports/evidence_sources/triage_summary.json` (`src/triage_summary.py` from `reports/triage_value/triage_value.json`, `src/triage_value.py`) | November, retrospective |
| Triage, Linear, duration: adding text, precision change (slide 15) | 0.015–0.082; month-block interval includes zero in 0 of 5 years | same | November, retrospective |
| Triage, Linear, duration, structure only: within-country precision, 10 largest countries | median 0.41–0.55 across years; range 0.13–0.86 | same | November, retrospective |
| Triage, Linear, 24-hour, structure only, top 10% flagged vs slowest 20% (slide 15) | precision 2021 0.507; 2022 0.526; 2023 0.683; 2024 0.688; 2025 0.676 (range 0.51–0.69); lift 2021 2.54; 2022 2.63; 2023 3.41; 2024 3.44; 2025 3.38 (range 2.5–3.4×; random = 0.20) | `reports/evidence_sources/triage_summary.json` (`src/triage_summary.py` from `reports/triage_value/triage_value.json`, `src/triage_value.py`) | November, retrospective |
| Triage, Linear, 24-hour: adding text, precision change (slide 15) | -0.002–0.045; month-block interval includes zero in 1 of 5 years | same | November, retrospective |
| Triage, Linear, 24-hour, structure only: within-country precision, 10 largest countries | median 0.40–0.54 across years; range 0.10–0.87 | same | November, retrospective |
| Linear text gain with month and country 95% intervals, days (slide 12) | 2021 0.293 month [0.198, 0.384] country [-0.042, 0.543]; 2022 0.372 month [0.208, 0.518] country [0.101, 0.847]; 2023 0.259 month [0.088, 0.406] country [-0.056, 0.726]; 2024 0.389 month [0.287, 0.500] country [-0.061, 0.892]; 2025 0.260 month [0.139, 0.396] country [-0.180, 0.565] | `reports/evidence_sources/gain_intervals.json` (`src/gain_intervals.py`, from `benchmark.json`) | November |
| Tree text gain (S → S+M+L) with month and country 95% intervals, days (slide 12) | 2021 0.035 month [-0.073, 0.137] country [0.005, 0.089]; 2022 0.028 month [-0.036, 0.084] country [-0.035, 0.117]; 2023 0.006 month [-0.025, 0.035] country [-0.028, 0.025]; 2024 0.001 month [-0.020, 0.025] country [-0.097, 0.036]; 2025 0.042 month [0.013, 0.074] country [0.006, 0.111] | same | November |
| Capped-forecast linear gain with country 95% interval, days (slide 12) | 2021 0.324 country [0.085, 0.540]; 2022 0.377 country [0.116, 0.810]; 2023 0.277 country [0.027, 0.738]; 2024 0.405 country [0.081, 0.862]; 2025 0.265 country [-0.123, 0.580] | same, from `reports/loss_alignment_2025/` | November extension, diagnostic |
| Intervals that include zero | month: linear 0 of 5; country: linear 4 of 5, capped 1 of 5, tree 3 of 5 | same | November |
| Linear text gain by nested stage, S → +form → +lexicon → +TF-IDF, days (slide 11) | 2021 form 0.025, lexicon 0.010, TF-IDF 0.258 (total 0.293); 2022 form 0.018, lexicon 0.018, TF-IDF 0.336 (total 0.372); 2023 form 0.116, lexicon 0.055, TF-IDF 0.089 (total 0.259); 2024 form 0.063, lexicon 0.014, TF-IDF 0.312 (total 0.389); 2025 form 0.033, lexicon 0.003, TF-IDF 0.224 (total 0.260) | `reports/text_benchmark_reviewed/benchmark.json` via `src/gain_breakdown.py` | November, derived |
| Stage with the largest gain | TF-IDF in 4 of 5 years (all but 2023, where form leads); lexicon, specificity and sentiment add 0.003–0.055 days ("0.003–0.055") | same | November, derived |
| Text only versus structure only, linear MAE (text worse by), days | 2021 0.846; 2022 0.552; 2023 0.859; 2024 1.032; 2025 0.146 | same | November, derived |
| Family × period and × loan-size interactions, duration (contrasts against the reference level, not within-group slopes) | family (reference: pre-pandemic, small) -0.0226, clustered p 0.1983; pandemic_disruption +0.0218, clustered p 0.3040; post_pandemic +0.0135, clustered p 0.2900; medium -0.0238, clustered p 0.1132; large -0.0139, clustered p 0.3799 | `reports/generated_full_dataset/association_summary.txt` via `src/primary_interactions.py` | August |
| Family × period and × loan-size interactions, 24-hour log-odds | family (reference: pre-pandemic, small) +0.0535, clustered p 0.4179; pandemic_disruption -0.0416, clustered p 0.3204; post_pandemic -0.0032, clustered p 0.9019; medium +0.0110, clustered p 0.6862; large +0.0044, clustered p 0.9164 | same | August |
| Period and loan-size family interactions under clustering | none has country-clustered p below 0.11; all 48-cluster normal reference | same | August |
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

## Loan details against framing (slide 11)

Programme-adjusted model; change in (1 + days), not days; country-clustered 95% intervals, t(47). Associations among completed loans, not effects of changing a loan. Exploratory; one independent code review (2026-11-08), recorded in `reports/experiments_2026_11_08/README.md`. No ratio or ranking.

| Claim | Value | Source | Layer |
| --- | --- | --- | --- |
| Loan details | loan amount, per doubling from the US$325 median within its loan-size band +44.6% [+32.3%, +58.1%], and −14.8 pp [−19.0, −10.5] on 24-hour funding; repayment term, per +1 month +8.6% [+2.1%, +15.5%]; male vs female +61.0% [+47.2%, +76.1%]; borrowers, per +1, holding group loan −1.0% [−2.7%, +0.6%] | `reports/evidence_sources/loan_detail_summary.json` (`src/loan_detail_summary.py`), from `reports/experiments_2026_11_08/loan_detail_coefficients.json` | Experiment I, exploratory |
| Framings per +1 mention per 100 words, unless labelled | family +0.9% [−0.2%, +2.1%]; business +0.5% [−0.1%, +1.2%]; basic needs −0.7% [−2.0%, +0.6%]; agency +0.6% [−0.3%, +1.5%]; gratitude +1.5% [−0.9%, +3.9%]; urgency −0.4% [−7.5%, +7.2%]; first person +1.0% [−7.5%, +10.2%]; third person −0.8% [−1.3%, −0.3%]; sentiment per +0.5 score +1.3% [−0.2%, +2.9%]; mention-rate point estimates within about ±1.5% | same | Experiment I, exploratory |

## Text methods

| Claim | Value | Source | Layer |
| --- | --- | --- | --- |
| Framing word lists: entries per measure (an entry is one alternative; some include word forms) | family 11; basic needs 13; business 13; agency 11; gratitude 4; urgency 11; first person 8; third person 10 ("4–13 entries"); rates per 100 words; theory-guided, not yet validated | `reports/evidence_sources/text_methods.json` (`src/text_methods.py`), `src/features.py` | Method |
| Sentiment | VADER compound score, rule-based lexicon, −1 to 1 | same | Method |
| TF-IDF word patterns | words and two-word phrases; up to 5,000 features; in at least 5 training loans; sublinear term frequency; fitted on training rows only | same, `src/benchmark_models.py` | Method |
| Compressed text features, larger boosted tree | truncated SVD of TF-IDF, 64 components, fitted on training rows only | same, `src/strong_forecaster.py` | Method |
| Exploratory topic model | NMF on TF-IDF; eight themes; up to 1,000 features; 20,000-loan sample | same, `notebooks/1_full_dataset_eda.py` | Method, exploratory |
| Language models | none used: no large language model and no pretrained embeddings | `src/` and `notebooks/` reviewed 2026-11-08 | Method |

## Exploratory topics

| Claim | Value | Source | Layer |
| --- | --- | --- | --- |
| NMF themes, 20,000-loan sample, unadjusted means | 8 themes; 1.5 days (sanitation) to 13.5 days (group solar and farm plots) | `docs/presentation/qa_answers.md`, `notebooks/1_full_dataset_eda.py` | Descriptive, sample only |

## Retired — do not quote

"The story barely registers", "robust null", "won't move the needle", "myth busted",
"third person BH p 0.012 → 0.061" and "business framing is the one term below BH 0.05 (BH p 0.006)" (retired 2026-11-08:
superseded by the corrected wild cluster bootstrap), "no term survives" / "0 pass BH", "lowest p 0.136", bootstrap BH p third person 0.136 and 0.261, business 0.275 and 0.337, and loan amount +44.8% (retired 2026-11-09: corrected rerun),
"structure beats story ~10×", LightGBM, "SHAP top 10/15 has no narrative feature",
"sign reversal" for third-person framing, country-level A/B advice from two-country
regions, and the 20,000-loan topic results as full-data evidence.
See `docs/2_evidence_and_corrections.md` and `docs/4_research_review.md`.
