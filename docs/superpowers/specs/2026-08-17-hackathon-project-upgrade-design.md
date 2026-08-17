# Hackathon Project Upgrade Design

**Date:** 2026-08-17  
**Status:** Approved in chat  
**Submission deadline:** 2026-08-24 at 17:00 Sydney time  
**Primary constraint:** Proposal maximum 1,500 words, excluding references

## Purpose

Upgrade the repository from a broad exploratory starter into a reproducible, submission-ready research project aligned with the Marketing Analytics Hackathon 2026 judging rubric. The project will identify which controllable narrative choices are associated with faster Kiva funding, distinguish those choices from structural loan constraints, test whether associations differ across segments and periods, and turn the findings into ethical managerial guidance.

The project studies aggregate loan-level funding responses. It will not claim to observe or causally identify individual lender decisions.

## Research Positioning

### Working title

**Beyond a Good Story: When and for Whom Persuasive Loan Narratives Accelerate Prosocial Funding**

### Central research question

Which controllable narrative choices accelerate funding, for whom, and when, after separating presentation effects from structural loan constraints?

### Supporting questions

1. Which narrative characteristics—specificity, emotional tone, beneficiary focus, agency, readability, and thematic framing—are associated with faster funding after controlling for loan structure and context?
2. Do these associations vary by region, sector, borrower or group gender classification, group status, loan size, and repayment structure?
3. Did persuasive associations change across the pre-pandemic, disruption, and post-pandemic periods?
4. How well do models trained on earlier loans predict later-period outcomes, and which controllable features offer the greatest practical opportunity for improvement?

## Scope

### Included

- A proposal draft with the organizer's required five sections and no more than 1,500 words excluding references.
- Reliable loading, validation, target construction, and time-period derivation.
- Theory-guided narrative, borrower, financial, geographic, and temporal features.
- Leakage-safe text transformation and chronological evaluation.
- An interpretable duration model and a nonlinear predictive benchmark.
- A complementary binary outcome for funding within 24 hours.
- Pre-specified segment and period comparisons.
- Automated tests for critical transformations and split behavior.
- A reproducible analysis entry point, updated notebook, README, and generated reports.

### Excluded

- Causal claims about narrative effects.
- Individual-lender choice modeling, because individual lender observations are unavailable.
- External data acquisition during the one-week project.
- Extensive hyperparameter searches or simultaneous use of multiple redundant topic and boosting methods.
- A production application or dashboard.

## Data Contract

The source is the organizer-provided Kiva loan sample and data dictionary. Raw files remain unchanged.

### Outcomes

- `funding_speed_days`: `(raisedDate - fundraisingDate)` in fractional days.
- `log_funding_speed`: `log1p(funding_speed_days)` for the primary duration regression.
- `funded_within_24h`: one when `funding_speed_days <= 1`, otherwise zero.

Rows with invalid dates, negative duration, or missing outcomes will be flagged and excluded from completed-loan analyses rather than target-imputed. If the full competition data contain loans without a `raisedDate`, they will be reported separately as potentially censored; the project will not silently convert them into completed durations.

### Predictors available at or before posting

- Narrative: `description`, `use`, and `whySpecial`.
- Borrower: `borrowerCount` and the dataset's group-level `gender` classification.
- Loan structure: `loanAmount`, `lenderRepaymentTerm`, and `repaymentInterval`.
- Purpose: `sector` and `activity`.
- Geography and economic context: `country_iso`, `country_name`, `region`, and `country_ppp`.
- Time: year, month, and analysis period derived from `fundraisingDate`.

`fundsLentInCountry` will be excluded from predictive models by default until its observation timestamp is verified. It may be used in a sensitivity analysis if it can be shown to be available at posting time.

IDs, outcome dates, status, image URLs, and borrower names will not be predictors. Coordinates will not be used in the core model because country and region already provide interpretable geographic controls.

## Feature Design

### Narrative features

- Cleaned text and missing-text indicators.
- Description and use word counts.
- Readability proxy using sentence length and average word length.
- Family or beneficiary, basic-needs, business-investment, agency, gratitude, and urgency framing counts normalized per 100 words.
- Sentiment scores treated as descriptive tone measures, not direct measures of emotion or persuasion.
- Concrete-detail indicators such as numbers, borrower age patterns, and years-in-business patterns.
- First- and third-person counts retained only as writing-style measures. They will not be labeled borrower authenticity.
- Training-fitted TF-IDF plus NMF topic proportions. Topic count will be fixed before final evaluation and topics will be named only after inspecting training-set terms.

### Borrower features

- `is_group_loan` from `borrowerCount > 1`.
- A categorical `gender_classification` with female, male, mixed or unknown values when supported by the raw field.
- No assumption that missing gender is female.
- No `female_ratio` unless the full data demonstrably contain member-level gender lists.

### Structural and contextual features

- `log1p(loanAmount)` and repayment term.
- Repayment-interval categories.
- Sector, region, and country controls where sample size permits.
- Posting year, month, and three analysis periods: 2016–2019, 2020–2021, and 2022–2025.

## Analytical Design

### Descriptive layer

Report target validity, missingness, skew, 24-hour funding share, and funding duration by period and major segment. Avoid interpreting unadjusted differences as effects.

### Interpretable models

The primary explanatory model will regress `log_funding_speed` on pre-specified narrative, structural, contextual, and period variables. It will use heteroskedasticity-robust standard errors. Country and sector controls will be included when estimable without excessive sparsity.

A logistic regression for `funded_within_24h` will provide an intuitive complementary outcome. Results will be reported as associations with confidence intervals, not causal effects.

Pre-specified heterogeneity tests will be limited to:

- Narrative framing × analysis period.
- Narrative framing × broad region.
- Narrative framing × loan-size band.
- Narrative framing × sector, restricted to adequately represented sectors.

Quantile regression for median duration will be a robustness check if supported by the full dataset and one-week schedule.

### Predictive benchmark

One gradient-boosted tree implementation will benchmark nonlinear predictive performance. It will be compared with simple baselines such as the training median and a regularized linear model. Interpretation will use permutation importance or SHAP only on held-out data.

### Validation

The main evaluation will be chronological:

- Development/train: loans posted through 2023.
- Final holdout: loans posted in 2024–2025.

If sample sizes support it, rolling-origin validation will evaluate multiple historical cutoffs. Random cross-validation may appear only as a secondary diagnostic.

All learned transformations—including imputation, scaling, categorical encoding, TF-IDF, and NMF—must fit on training data only. Validation and holdout data are transformed without refitting.

Primary predictive metrics are MAE and median absolute error in days, plus R-squared as a secondary measure. The 24-hour classifier will report ROC AUC, PR AUC, and calibration or Brier score when both classes are present.

## Software Architecture

### Data preparation

`src/data_loader.py` will own raw loading, schema checks, date parsing, target creation, invalid-row flags, and analysis-period derivation. It will not perform feature learning.

### Deterministic features

`src/features.py` will own deterministic row-level features that do not learn from other observations. Its public feature builder will preserve raw fields needed by downstream pipelines.

### Learned text transformation

A new `src/text_transformer.py` will expose a scikit-learn-compatible transformer that fits TF-IDF and NMF on training text and returns stable named numeric columns for later transformations.

### Validation

A new `src/validation.py` will provide chronological split functions and guard against overlapping or reversed time ranges.

### Modeling and reporting

`src/modeling.py` will provide baselines and the main chronological evaluation. `src/statistical_analysis.py` will fit interpretable models with robust inference. `src/advanced_modeling.py` will contain only the selected boosted-tree benchmark and held-out interpretation.

A new `src/run_analysis.py` will serve as the reproducible command-line entry point, create output directories, execute the analysis stages, and write concise machine-readable and human-readable summaries.

### Tests

Tests will cover data validation and duration creation, gender handling, normalized narrative features, period boundaries, chronological splitting, training-only text fitting, exclusion of post-outcome fields, and smoke-level end-to-end execution on synthetic data.

Tests will use synthetic fixtures and will not depend on the ignored competition dataset.

## Deliverables

- `proposal/proposal.md`: submission-ready draft below the word limit, with placeholders only for team names and affiliations.
- `README.md`: accurate structure, setup, reproducible commands, research framing, limitations, and one-week execution schedule.
- Updated source modules and notebook reflecting the approved analysis.
- `tests/`: automated regression tests.
- `reports/`: generated summaries that separate exploratory sample evidence from planned full-data conclusions.

The notebook will call source functions instead of duplicating core modeling logic. Paths will resolve from the repository root rather than a specific operating system or notebook working directory.

## Managerial Output

The final analysis will distinguish:

- Controllable presentation levers, such as clarity, specificity, framing, and description length.
- Structural constraints, such as requested amount and repayment term.
- Contextual moderators, such as period, region, and sector.

Recommendations will be segment-specific and will include uncertainty. Ethical guidance will discourage exaggerating hardship, manipulating emotion, or suppressing relevant borrower information. The objective is clearer and more relevant communication, not emotional exploitation.

## Error Handling and Reproducibility

- Missing required columns raise a clear schema error listing absent fields.
- Invalid or negative durations are flagged and summarized.
- Insufficient rows or single-class outcomes cause a clear diagnostic instead of a misleading metric.
- Randomized estimators use fixed seeds.
- Reports record dataset size, date range, exclusion counts, split dates, and software versions.
- Network downloads, including NLTK resource downloads, will not occur implicitly during module import.

## Acceptance Criteria

1. The proposal follows all five organizer sections and is at most 1,500 words excluding references.
2. No model imputes a missing target or uses post-outcome information as a predictor.
3. Primary evaluation is chronological and all learned transformations fit only on training observations.
4. Time evolution and at least two meaningful segment comparisons are present.
5. Statistical results use association language and robust uncertainty.
6. The repository runs from its root with documented commands on a clean supported Python environment.
7. Automated tests pass without requiring the competition dataset or network access.
8. README links are portable and describe the actual repository contents.

