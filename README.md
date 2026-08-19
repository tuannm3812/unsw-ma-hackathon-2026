# UNSW Marketing Analytics Hackathon Challenge 2026

Working repository for our submission to the **UNSW Marketing Analytics Hackathon Challenge 2026**, using loan-level data from the prosocial micro-lending platform **Kiva** (spanning 2016-2025) to study **funding speed** in subsistence marketplaces.

## Submission deadline and constraints

- **Proposal due:** 2026-08-24, 5:00pm Sydney time (AEST/UTC+10), via email to `MA.Hackathon@unsw.edu.au`.
- **Format:** five required proposal sections, 1,500-word maximum excluding references. The current draft (`proposal/proposal.md` / `proposal/proposal.pdf`) is submission-ready at 1,417 words excluding references (via `tests/test_proposal.py`'s authoritative regex count - re-run that test rather than trust this number if the proposal changes again).
- **Judging criteria (weighted):** insightfulness/originality 30%, analytical rigor/relevance 30%, strategic depth/evolutionary perspective 20%, feasibility 10%, clarity 10%.

## Research questions

**Central question.** Which narrative choices are associated with faster funding, for whom, and when, after separating presentation from structural constraint?

**Supporting questions.** (kept in sync with `proposal/proposal.md`'s Project Aim section - see that file for the authoritative, current wording)

- Which narrative characteristics — specificity, tone, beneficiary focus, agency, and thematic framing — are associated with funding speed after controlling for loan amount, term, sector, region, and borrower structure?
- Does that association differ across pre-specified segments — analysis period, region group, and loan-size band by default, with sector, gender, and group-status interactions as explicitly scoped extensions?
- Did the narrative–speed association shift across the **pre-pandemic, pandemic-disruption, and post-pandemic** periods — the project's central **evolutionary-perspective** test?
- How well do patterns learned on earlier loans predict later-period outcomes, and which controllable features carry the most practical opportunity?

This project studies **aggregate, loan-level** patterns, not individual lender psychology, and reports **associations, never causal effects**. Every statistical claim in this repository uses association language ("associated with"), never "causes" or "proves." Both outcomes are defined only among loans that were **eventually funded** - see `proposal/proposal.md`'s Project Aim section for the outcome-boundary caveat this implies.

## Repository structure

```
unsw-ma-hackathon-2026/
├── data/
│   ├── README.md                  # Expected filenames, immutability note
│   ├── Kiva_Loans_Sample.pkl      # Raw competition data (git-ignored)
│   └── Kiva Data Dictionary.xlsx  # Raw competition data (git-ignored)
├── docs/superpowers/               # Design spec, plan, and collaboration log for this upgrade
├── notebooks/
│   ├── starter_eda.ipynb          # Auditable evidence notebook (paired via jupytext)
│   └── starter_eda.py             # Percent-format script counterpart, source of truth
├── proposal/
│   ├── proposal.md                # Submission-ready proposal (source)
│   ├── proposal.pdf                # Styled, rendered proposal
│   └── assets/proposal.css        # Stylesheet used to render the PDF
├── reports/
│   ├── generated/                 # Output of `python3 -m src.run_analysis` (git-ignored)
│   └── statistical_summary.txt    # Superseded-report notice pointing to reports/generated/
├── resources/nltk_data/sentiment/  # Vendored VADER lexicon + its upstream MIT license/provenance
├── src/
│   ├── __init__.py
│   ├── data_loader.py             # Loads the pickle, parses dates, derives the outcome
│   ├── features.py                # Deterministic narrative/borrower/financial features
│   ├── text_transformer.py        # Leakage-safe TF-IDF/NMF topic transformer
│   ├── topics.py                  # Full-sample exploratory topic-modeling convenience wrapper
│   ├── validation.py              # Chronological train/holdout split, InsufficientDataError
│   ├── modeling.py                # Leakage-safe chronological baseline + Ridge evaluation
│   ├── statistical_analysis.py    # Robust OLS/GLM explanatory (association) models
│   ├── advanced_modeling.py       # Nonlinear (HistGradientBoostingRegressor) benchmark
│   ├── binary_modeling.py         # Leakage-safe chronological classifier for the 24h outcome
│   └── run_analysis.py            # CLI orchestrator: runs all stages, writes reports
├── tests/                          # 11 test files, offline, no dataset or network required
├── .gitignore
├── requirements.txt
└── README.md                       # This file
```

## Setup

### 1. Prerequisites

Python 3.9+.

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` covers everything needed to run the pipeline, notebook, and test suite: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `openpyxl`, `statsmodels`, `patsy`, `nltk`, `ipykernel`, `notebook`, `pytest`. There is no `xgboost` or `lightgbm` dependency anywhere in the codebase - the nonlinear benchmark uses scikit-learn's built-in `HistGradientBoostingRegressor` instead, to avoid two redundant third-party gradient-boosting dependencies. Sentiment scoring (VADER, via `nltk`) works out of the box with no separate download step: `pip install nltk` alone does not include the lexicon data, so it is vendored directly in `resources/nltk_data/` (see that directory's README) instead of relying on `nltk.download(...)`, which this project's tests/CLI must never call (no network access during import or feature extraction).

### 4. Optional tooling for regenerating docs (not in `requirements.txt`)

Opening and running the notebook interactively via `jupyter notebook` (below) needs the `notebook` package, which is listed in `requirements.txt`; opening it inside VS Code / Spyder instead only needs `ipykernel` for kernel execution, since those editors bundle their own Jupyter front end. Two extra, ad-hoc toolchains are needed only if you want to regenerate or re-verify these committed artifacts yourself, and are **not** listed in `requirements.txt`:

- **Regenerating/verifying `notebooks/starter_eda.ipynb`** from `notebooks/starter_eda.py` (the jupytext-paired source of truth) requires `pip install jupytext nbconvert`.
- **Re-rendering `proposal/proposal.pdf`** from `proposal/proposal.md` requires `pandoc` (e.g. `brew install pandoc`) plus `pip install weasyprint`.

Place the raw data files in `data/` before running the analysis or notebook - see `data/README.md` for exact filenames. The test suite does not need them (see below).

## Verifying the codebase

Run the full offline test suite (no dataset or network access required):

```bash
python3 -m pytest -q
```

## Running the analysis

Run the full leakage-safe pipeline end to end from the repository root and write auditable reports:

```bash
python3 -m src.run_analysis --data data/Kiva_Loans_Sample.pkl --output-dir reports/generated
```

This writes `reports/generated/analysis_summary.json` (machine-readable metrics, dataset audit trail, software versions) and `reports/generated/association_summary.txt` (human-readable, association-language narrative) atomically. `--data`/`--output-dir` accept relative or absolute paths and are resolved against the caller's current working directory (not a hardcoded machine path) - but `python3 -m src.run_analysis` itself must be run from the repository root (or with the repo root on `PYTHONPATH`), since that is what makes the `src` package importable. `--holdout-start` (default `2024-01-01`) sets the chronological train/holdout boundary.

To open and step through the narrative notebook version of the same analysis:

```bash
jupyter notebook notebooks/starter_eda.ipynb
```

or open `notebooks/starter_eda.py` directly in VS Code / Spyder and run it as a percent-format script.

## Chronological validation and leakage protections

All evaluation is **chronological, not random**: models train on loans posted before a cutoff date and are scored only on loans posted on or after it, mirroring how a model would actually be used to score newly posted loans (`src/validation.py::chronological_holdout`). `src/modeling.py`'s Ridge/baseline evaluation, `src/advanced_modeling.py`'s nonlinear regressor, and `src/binary_modeling.py`'s 24-hour classifier (reporting ROC AUC, average precision, and Brier score) all share this exact same split and preprocessing, not three separately derived ones. A dedicated `InsufficientDataError` distinguishes "this split has too little usable data" from unrelated bugs, so a too-small split degrades gracefully into a labeled diagnostic instead of a misleading number or a crash.

Every learned transformation is fit on the training partition only and merely *applied*, never refit, to the holdout:

- Missing-value imputation and feature scaling/encoding (`src/modeling.py::prepare_chronological_matrices`).
- The TF-IDF vectorizer and NMF topic model (`src/text_transformer.py::KivaTopicTransformer`) - `src/topics.py` provides a separate, explicitly labeled full-sample exploratory wrapper around the same transformer, for descriptive use only, never for evaluating held-out predictions.

Predictors are selected via an **explicit allowlist, not a blocklist** (`src/modeling.py::build_predictor_frame`), so a leakage-sensitive or post-outcome field cannot be silently reintroduced by a future edit. A missing outcome is never imputed - only rows with a `valid_completed_outcome` are used for the duration model, and only rows with a non-null `funded_within_24h` are used for the binary model.

## Data field groups

**Outcomes** (derived in `src/data_loader.py::prepare_analysis_data`, never used as predictors):

- `funding_speed_days` = `raisedDate - fundraisingDate` (fractional days)
- `log_funding_speed` = `log1p(funding_speed_days)`
- `funded_within_24h` = 1 if `funding_speed_days <= 1`, else 0
- `valid_completed_outcome`, `outcome_issue`, `analysis_period` (bookkeeping / period bucketing)

**Predictors available at or before posting** (the only fields the allowlist permits):

- **Narrative:** `description` (full content-derived features - word/sentence counts, sentiment, per-100-word framing rates, training-fitted topic proportions); `use` and `whySpecial` currently contribute only presence/missingness flags (`use_missing`, `whySpecial_missing`) to the model, not their own content-derived counts
- **Borrower:** `borrowerCount`, group-level `gender` classification (female, male, mixed, or unknown - missingness is preserved as its own category, never defaulted to female)
- **Loan structure:** `loanAmount`, `lenderRepaymentTerm`, `repaymentInterval`
- **Purpose:** `sector`, `activity`
- **Geography/economic context:** `country_iso`, `region`, `country_ppp`, and (explanatory models only) `region_group` - `region` collapsed to a fixed observation-count threshold (`src/features.py::MIN_REGION_OBSERVATIONS`), not a hardcoded region list, so it adapts automatically to whichever regions the data actually supports
- **Time:** year, month, and `analysis_period` derived from `fundraisingDate` (2016-2019, 2020-2021, 2022-2025)

**Excluded from the predictor allowlist** (leakage-sensitive or redundant):

- All post-outcome fields: `raisedDate`, `funding_speed_days`, `log_funding_speed`, `funded_within_24h`, `valid_completed_outcome`, `outcome_issue`, `status`
- `fundsLentInCountry` - excluded by default until its posting-time availability is verified
- `country_name` - the same country identity as `country_iso` at equal cardinality; including both would one-hot encode the same signal twice
- Identifiers, image URLs, borrower names, and raw geographic coordinates

## One-week execution schedule

The proposal covers Days 1-7 below as a generic post-proposal analysis week (no fixed calendar dates), mapped to the pipeline's actual stages:

Steps 1-2 and 5-6 below are manual analytical work each week's data requires, not automated pipeline stages; steps 3-4 and 7 reuse code already implemented and tested on the development sample unchanged (see `proposal/proposal.md`'s Expected Outcomes section for this same distinction).

| Day | Focus | Deliverable |
| :-- | :-- | :-- |
| 1 | Full-dataset schema/coverage audit | Confirmed schema, missingness, outcome-validity audit against `src/data_loader.py`; freeze segment-grouping thresholds (`src/features.py::MIN_REGION_OBSERVATIONS`) against the audited counts |
| 2 | Feature engineering at full scale | Narrative, borrower, and financial features (`src/features.py`) verified against the larger sample |
| 3 | Chronological modeling | Baseline + Ridge + nonlinear benchmark + 24-hour classifier re-run via `src/modeling.py` / `src/advanced_modeling.py` / `src/binary_modeling.py` on the full-data chronological split |
| 4 | Explanatory statistics | Full-data OLS/GLM refit (`src/statistical_analysis.py`); the period/region-group/loan-size interactions already run by default - write and test the one remaining opt-in interaction (narrative × sector, restricted to adequately represented sectors) |
| 5 | Diagnostics and sensitivity | Permutation-importance comparison against the explanatory-model coefficients; sensitivity check on `fundsLentInCountry`; build the segment-by-framing managerial opportunity matrix |
| 6 | CLI run and reporting | Full-dataset `python3 -m src.run_analysis` run; review `analysis_summary.json` / `association_summary.txt` for anomalies |
| 7 | Notebook and final write-up | Refresh `notebooks/starter_eda.ipynb` against full-data results; prepare the final analysis write-up/presentation and managerial recommendations for submission (the proposal itself is already submitted by this point) |

## Proposal

The submission-ready proposal lives at `proposal/proposal.md` (source, 1,417 words excluding references - see `tests/test_proposal.py` for the authoritative count) and `proposal/proposal.pdf` (styled render). Team identity (team member name and affiliation) is **already filled in** in both files - Manh Tuan Nguyen, University of Technology Sydney - there is no outstanding placeholder to complete before submission.

## Known limitation

`data/Kiva_Loans_Sample.pkl` is a **100-row illustrative sample**, not the full competition dataset. Every metric, coefficient, and figure produced by this repository's pipeline and notebook demonstrates that the code runs correctly end to end and sanity-checks its own output - it is **not final evidence** for any marketing decision. Several results in the proposal are explicitly framed as illustrative of feasibility on this basis (e.g. the 24-hour binary model hitting quasi-complete separation and correctly reporting a diagnostic instead of an unstable estimate at n=100). The same pipeline must be re-run against the full competition dataset via `python3 -m src.run_analysis` before drawing conclusions that inform real decisions.
