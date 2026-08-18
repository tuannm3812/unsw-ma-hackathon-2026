# UNSW Marketing Analytics Hackathon Challenge 2026

Working repository for our submission to the **UNSW Marketing Analytics Hackathon Challenge 2026**, using loan-level data from the prosocial micro-lending platform **Kiva** (spanning 2016-2025) to study **funding speed** in subsistence marketplaces.

## Submission deadline and constraints

- **Proposal due:** 2026-08-24, 5:00pm Sydney time (AEST/UTC+10), via email to `MA.Hackathon@unsw.edu.au`.
- **Format:** five required proposal sections, 1,500-word maximum excluding references. The current draft (`proposal/proposal.md` / `proposal/proposal.pdf`) is submission-ready at 1,459 words excluding references.
- **Judging criteria (weighted):** insightfulness/originality 30%, analytical rigor/relevance 30%, strategic depth/evolutionary perspective 20%, feasibility 10%, clarity 10%.

## Research questions

**Central question.** Which narrative choices accelerate funding, for whom, and when, after separating presentation from structural constraint?

**Supporting questions.**

- Which narrative characteristics — specificity, tone, beneficiary focus, agency, and thematic framing — are associated with funding speed after controlling for loan amount, term, sector, region, and borrower structure?
- Do these associations differ by region, sector, gender classification, group status, or loan size?
- Did the narrative–speed association shift across the **pre-pandemic, pandemic-disruption, and post-pandemic** periods — the project's central **evolutionary-perspective** test?
- How well do patterns learned on earlier loans predict later-period outcomes, and which controllable features carry the most practical opportunity?

This project studies **aggregate, loan-level** patterns, not individual lender psychology, and reports **associations, never causal effects**. Every statistical claim in this repository uses association language ("associated with"), never "causes" or "proves."

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
│   └── statistical_summary.txt    # Curated, committed statistical summary snapshot
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
│   └── run_analysis.py            # CLI orchestrator: runs all stages, writes reports
├── tests/                          # 10 test files, offline, no dataset or network required
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

`requirements.txt` covers everything needed to run the pipeline and test suite: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `openpyxl`, `statsmodels`, `patsy`, `nltk`, `ipykernel`, `pytest`. There is no `xgboost` or `lightgbm` dependency anywhere in the codebase - the nonlinear benchmark uses scikit-learn's built-in `HistGradientBoostingRegressor` instead, to avoid two redundant third-party gradient-boosting dependencies.

### 4. Optional tooling for regenerating docs (not in `requirements.txt`)

Opening and running the notebook only needs `ipykernel`, already listed above. Two extra, ad-hoc toolchains are needed only if you want to regenerate or re-verify these committed artifacts yourself, and are **not** listed in `requirements.txt`:

- **Regenerating/verifying `notebooks/starter_eda.ipynb`** from `notebooks/starter_eda.py` (the jupytext-paired source of truth) requires `pip install jupytext nbconvert`.
- **Re-rendering `proposal/proposal.pdf`** from `proposal/proposal.md` requires `pandoc` (e.g. `brew install pandoc`) plus `pip install weasyprint`.

Place the raw data files in `data/` before running anything - see `data/README.md` for exact filenames.

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

This writes `reports/generated/analysis_summary.json` (machine-readable metrics, dataset audit trail, software versions) and `reports/generated/association_summary.txt` (human-readable, association-language narrative) atomically, and resolves paths portably regardless of the current working directory. `--holdout-start` (default `2024-01-01`) sets the chronological train/holdout boundary.

To open and step through the narrative notebook version of the same analysis:

```bash
jupyter notebook notebooks/starter_eda.ipynb
```

or open `notebooks/starter_eda.py` directly in VS Code / Spyder and run it as a percent-format script.

## Chronological validation and leakage protections

All evaluation is **chronological, not random**: models train on loans posted before a cutoff date and are scored only on loans posted on or after it, mirroring how a model would actually be used to score newly posted loans (`src/validation.py::chronological_holdout`). A dedicated `InsufficientDataError` distinguishes "this split has too little usable data" from unrelated bugs, so a too-small split degrades gracefully into a labeled diagnostic instead of a misleading number or a crash.

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
- **Geography/economic context:** `country_iso`, `region`, `country_ppp`
- **Time:** year, month, and `analysis_period` derived from `fundraisingDate` (2016-2019, 2020-2021, 2022-2025)

**Excluded from the predictor allowlist** (leakage-sensitive or redundant):

- All post-outcome fields: `raisedDate`, `funding_speed_days`, `log_funding_speed`, `funded_within_24h`, `valid_completed_outcome`, `outcome_issue`, `status`
- `fundsLentInCountry` - excluded by default until its posting-time availability is verified
- `country_name` - the same country identity as `country_iso` at equal cardinality; including both would one-hot encode the same signal twice
- Identifiers, image URLs, borrower names, and raw geographic coordinates

## One-week execution schedule

The proposal covers Days 1-7 below as a generic post-proposal analysis week (no fixed calendar dates), mapped to the pipeline's actual stages:

| Day | Focus | Deliverable |
| :-- | :-- | :-- |
| 1 | Data validation on the full competition dataset | Confirmed schema, missingness, outcome-validity audit against `src/data_loader.py` |
| 2 | Feature engineering at full scale | Narrative, borrower, and financial features (`src/features.py`) verified against the larger sample |
| 3 | Chronological modeling | Baseline + Ridge + nonlinear benchmark re-run via `src/modeling.py` / `src/advanced_modeling.py` on the full-data chronological split |
| 4 | Explanatory statistics | Full-data OLS/GLM refit (`src/statistical_analysis.py`); write and test the pre-specified region/loan-size/sector interaction formulas |
| 5 | Nonlinear benchmark and comparison | Permutation-importance comparison against the explanatory-model coefficients; sensitivity check on `fundsLentInCountry` |
| 6 | CLI run and reporting | Full-dataset `python3 -m src.run_analysis` run; review `analysis_summary.json` / `association_summary.txt` for anomalies |
| 7 | Notebook and write-up | Refresh `notebooks/starter_eda.ipynb` against full-data results; finalize proposal narrative and managerial recommendations |

## Proposal

The submission-ready proposal lives at `proposal/proposal.md` (source, 1,459 words excluding references) and `proposal/proposal.pdf` (styled render). Team identity (team member name and affiliation) is **already filled in** in both files - Manh Tuan Nguyen, University of Technology Sydney - there is no outstanding placeholder to complete before submission.

## Known limitation

`data/Kiva_Loans_Sample.pkl` is a **100-row illustrative sample**, not the full competition dataset. Every metric, coefficient, and figure produced by this repository's pipeline and notebook demonstrates that the code runs correctly end to end and sanity-checks its own output - it is **not final evidence** for any marketing decision. Several results in the proposal are explicitly framed as illustrative of feasibility on this basis (e.g. the 24-hour binary model hitting quasi-complete separation and correctly reporting a diagnostic instead of an unstable estimate at n=100). The same pipeline must be re-run against the full competition dataset via `python3 -m src.run_analysis` before drawing conclusions that inform real decisions.
