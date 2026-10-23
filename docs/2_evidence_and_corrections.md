# Evidence map and interpretation corrections

Reviewed 2026-10-24. This is the current interpretation guide for reusing the
project. It qualifies earlier preparation claims while preserving the
[submitted proposal](../proposal/proposal.md), its PDF, and generated
presentation PDF/PPTX artifacts as historical records.

## Which analysis supports which claim?

| Evidence | Scope and authority |
| --- | --- |
| [Primary JSON report](../reports/generated_full_dataset/analysis_summary.json), [text report](../reports/generated_full_dataset/association_summary.txt), [provenance](../reports/generated_full_dataset/provenance.json) | Authoritative tested `src/` pipeline; saved run generated 2026-08-31. Full input: 1,453,846; valid completed durations: 1,453,840; six negative durations excluded. |
| [EDA notebook](../notebooks/1_full_dataset_eda.py) and [modeling notebook](../notebooks/2_full_dataset_modeling.py) | Self-contained walkthroughs; modeling specifications are simpler than the primary pipeline. Do not transfer their coefficients or p-values into primary-model claims. |
| [Expanded sensitivity snapshot](../reports/expanded_feature_sensitivity/expanded_sensitivity.json) and [coefficient table](../reports/expanded_feature_sensitivity/narrative_coefficients.csv) | Exploratory historical snapshot generated 2026-09-03, preserved with recovery provenance. Use the separately reviewed inference extension for current sensitivity claims. The old prediction comparison was not rerun during maintenance. |
| [Reviewed inference extension](../reports/expanded_feature_sensitivity_reviewed/README.md) and [programme audit](../reports/programme_proxy_audit/README.md) | Post-competition full-data research maintenance. Richer OLS/LPM specifications and an unvalidated programme-text control; separate from primary metrics. Completion/provenance and rejected diagnostic outputs are explicitly recorded. |
| [Starter notebook](../notebooks/0_starter_eda.py) and [proposal](../proposal/proposal.md) | 100-row illustrative sample; demonstration and submitted history, not full-data evidence. |
| [Data dictionary](1_data_dictionary.md) | Field definitions and descriptive context. Programme/partner and borrower-impact interpretations need the qualifications below. |

The primary explanatory models use all 1,453,840 eligible completed durations,
including 1,637 refunded records. Chronological predictive evaluation uses
1,174,953 training loans and 278,887 holdout loans from 2024–2025. A full-data
input count is not automatically the sample size for every analysis. Reading
saved reports during maintenance is not a fresh run.

## Corrections that matter when presenting results

**A sign change across differently oriented outcomes is not a reversal.**
In the historical expanded table, the third-person coefficient is −0.009008
for `log(1 + funding days)` and +0.001502 for the linear-probability outcome
`funded_within_24h`. Negative duration and positive fast-funding probability
both point toward faster funding. The coefficients have different units: the
latter is about +0.1502 percentage points per additional mention per 100 words,
not a log-odds coefficient. Historical BH-FDR adjusted p-values were 0.01236
and 0.22748 respectively (26 retained narrative terms per outcome): the
recorded statistical support differs, not the substantive direction. These
numbers explain the old wording error. The reviewed expanded rerun agrees
at the precision shown; use its provenance and the separately reported
programme comparison for current interpretation. Agreement does not recover
the September run's missing execution provenance.

**Failure to reject is not a robust null.** Primary urgency estimates lose
conventional significance under country clustering (duration p = 0.4943;
24-hour p = 0.2233). This is insufficient evidence for a universal writing
recommendation, not proof that urgency or narrative framing has no effect.
Likewise, predictive importance and a small change in holdout error cannot
establish either causal benefit or practical equivalence. No equivalence test
or prespecified negligible-effect bound was used.

**Regional interactions and regional slopes answer different questions.**
A family-framing interaction compares a region with the reference region.
A within-region association requires a contrast averaging over that region's
observed mix of all other moderators, including the sector interaction in
the primary fit. Its saved duration contrasts are:

| Region | Eligible loans | Country clusters | Average duration slope | Country-clustered 95% interval, normal reference | Heuristic few-cluster p |
| --- | ---: | ---: | ---: | --- | ---: |
| Middle East | 14,946 | 2 | −0.0729 | [−0.1003, −0.0456] | 0.1203 |
| Central America | 59,391 | 2 | −0.0742 | [−0.0879, −0.0605] | 0.0597 |

Units are change in `log(1 + days)` per additional family mention per 100
words. The few-cluster intervals are [−0.2502, 0.1043] and [−0.1629, 0.0145],
respectively. These use a t(1) reference on the unchanged clustered standard
error; this is a heuristic sensitivity screen, not a calibrated correction.
Passing such a screen would not certify a result. A one-country group cannot
estimate between-country uncertainty. Consequently these patterns are
descriptive, and cannot support advice to individual countries or regions.
Earlier README values −0.124 and −0.062 came from the simpler notebook
specification and must not be labelled primary estimates. The notebook's
reference-cell Asia result was also corrected; the primary average duration
contrast is +0.0234, country-clustered p = 0.0846, not evidence of a supported
within-Asia association.

**Platform funding time is not borrower waiting time.** The dictionary's
full-data descriptive audit reports 96.4% pre-disbursal. For those records,
platform funding follows an earlier disbursal; replenishing partner capital
is a plausible operational interpretation. The outcome does not directly
measure partner liquidity, borrower welfare, or the causal benefit of faster
funding. Do not generalise that interpretation to every record or describe
all borrowers as waiting for these funds.

**Programme text is not a verified partner identifier.** `whySpecial` is
text about what makes a loan special. Repeated categories, country nesting,
or descriptive duration differences do not prove a one-to-one mapping to
field partners. Treat programme controls as a sensitivity hypothesis requiring
coverage, nesting and identifiability checks. The full-data audit finds
642 observed nonblank categories, 590 confined to one country, and 40,012
missing labels among eligible completed durations. The reviewed sensitivity
uses a separate missing category and reports absorbed narrative terms. Neither
text style nor surviving associations can identify who wrote a description.

**Prediction and inference remain separate.** The primary nonlinear model's
holdout MAE is 5.2031 days and R² is 0.5420; the primary classifier's AUC is
0.8997. These are chronological prediction results on completed-funding
records. They do not establish why lenders acted, or imply that editing a
particular narrative feature improves funding time. All substantive
associations remain observational, with possible unmeasured programme,
partner, placement and borrower differences.

## What the reviewed October extension adds

The corrected full-data comparison uses the same 1,453,840 eligible records
and 48 country clusters in all four OLS/LPM fits, with no additional missingness
or row loss. Programme controls absorb all three `whySpecial` narrative
features, leaving 23 retained terms versus 26 in the expanded baseline.
The first programme attempt failed this check and is explicitly rejected in
its [diagnostic record](../reports/expanded_feature_sensitivity_diagnostic/README.md).

The third-person duration coefficient changes from −0.009008 to −0.008088,
while its individual BH-adjusted p-value changes from 0.01236 to 0.06062.
Its pointwise interval still excludes zero; this is compatible with an adjusted
p-value above 0.05 because those intervals are not simultaneous. The association
does not simply disappear. Business framing has a programme-adjusted 24-hour
coefficient of −0.002579 probability units (−0.258 percentage points per
additional mention per 100 words; adjusted p = 0.00635).

Several joint feature families remain associated, while the programme-adjusted
auxiliary-text family is not supported. The [full comparison](../reports/expanded_feature_sensitivity_reviewed/README.md)
reports all coefficients/families, units, uncertainty, multiplicity boundaries
and provenance. It supports neither a blanket null claim nor a causal writing
strategy. This was a fresh explanatory sensitivity run; primary models,
prediction and the full paired notebook were not rerun.

## Next evidence needed

1. Obtain a validated partner/programme identifier and its availability at
   listing. Compare narrative associations within those groups and assess
   how much independent variation remains; repeated text cannot establish
   either partner identity or authorship.
2. Obtain unfunded/expired listings and reliable observation end dates before
   studying funding success or censored time to funding. The current completed
   records cannot answer those questions.
3. Validate text constructs against a documented, independently reviewed
   annotation sample before adding more semantic features. Keep any new
   predictive transformations inside the chronological training split.
4. Before recommending a writing intervention, specify a practical effect
   threshold and a prospective design capable of testing it. More observational
   feature searches cannot establish the benefit of editing a description.

## Historical materials and current use

Use this notice and the [portfolio case study](3_portfolio_case_study.md)
for current summaries. Retained slide preparations and generated artifacts
may contain stronger causal, null-effect, partner, or outcome-reversal
wording; those interpretations are superseded by this notice. The primary
report itself remains a saved historical run with its original provenance.
The expanded snapshot's numerical audit and any reviewed rerun must stay
separate from that primary evidence.

Cultural Blend was a finalist. The [official UNSW results](https://www.unsw.edu.au/business/our-schools/marketing/news-events/student-events/MA-hackathon)
confirm eight finalist teams and the final on 4 September 2026. Event
instructions are archived in [historical logistics](presentation/2026_final_round_logistics.md).
