# UNSW Marketing Analytics Hackathon Challenge 2026

Team repository for the **UNSW Marketing Analytics Hackathon Challenge 2026**, using loan-level data from the prosocial micro-lending platform **Kiva** (spanning 2016-2025) to study **funding speed** in subsistence marketplaces: which narrative choices in a borrower's loan description are associated with faster funding, for whom, and when.

New to this project? Read this file top to bottom once - it's written to get you from a fresh clone to a green test suite, then to understanding the whole pipeline and where things stand.

## Project Status

- **Proposal round: done.** The proposal (`proposal/proposal.md` / `proposal/proposal.pdf`) was submitted and **the team was selected as one of 8 finalist teams**.
- **Final round: in progress.** Final presentation **slides** (no written report required) are due **2026-09-03, 5:00pm Sydney time**. The organizers provided the full competition dataset and said presentation format/logistics details would follow separately.
- **Final-round judging** (fetched from the organizers' page): a judging panel scores **80%** (originality of research question 20%, analytical approach/execution 20%, insights and communication 20%, practical implications for borrowers/platforms/stakeholders 20%), plus **20%** live audience-choice voting.
- **Full-dataset analysis: done and verified.** The complete pipeline has been run against the real 1,453,846-row dataset (not just the 100-row illustrative sample the proposal round used) - see [Full-Dataset Results](#full-dataset-results) below. Current focus is building the slide deck from these verified numbers.

## Getting Started

**1. Prerequisites:** Python 3.9+.

**2. Create and activate a virtual environment:**

```bash
python3 -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows
```

**3. Install dependencies:**

```bash
pip install -r requirements.txt
```

`requirements.txt` covers everything needed to run the pipeline, notebooks, and test suite: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `openpyxl`, `statsmodels`, `patsy`, `nltk`, `ipykernel`, `notebook`, `pytest`. There is no `xgboost` or `lightgbm` dependency anywhere in the codebase - the nonlinear benchmark uses scikit-learn's built-in `HistGradientBoostingRegressor` instead. Sentiment scoring (VADER, via `nltk`) works out of the box with no separate download step: the lexicon is vendored directly in `resources/nltk_data/` (see that directory's README for its license/provenance) instead of relying on `nltk.download(...)`, which this project's tests/CLI must never call (no network access during import or feature extraction).

`requirements.txt` intentionally uses lower bounds (`>=`) so installs stay possible as new versions ship - a different set of versions satisfying those same bounds can produce different numerical edge cases and warnings on identical code (this project hit exactly that during development). `pip install -r requirements-lock.txt` pins the exact core numerical/statistical package versions this project was verified against, if you ever hit different numerical/warning behavior and want to rule that out first.

**4. Verify the setup - run the full offline test suite** (no dataset or network access required):

```bash
python3 -m pytest -q
```

If this passes, your environment is correctly set up. Everything past this point is about understanding and running the actual analysis.

**5. Get the raw data files.** Two options:

- **Local files:** place them in `data/` using the exact filenames `data/README.md` documents (`Kiva_Loans.pkl` - the full 1.45M-row dataset from the organizers, `Kiva_Loans_Sample.pkl` - the original 100-row illustrative sample, `Kiva Data Dictionary.xlsx`). These are git-ignored (large/competition-restricted); ask a teammate for them or re-download from the organizers' link.
- **Kaggle (no local copy needed):** see [Kaggle Workflow](#kaggle-workflow) below - the team has a private Kaggle Dataset with the same files, mountable into any kernel.

**6. Optional tooling for regenerating committed docs** (not in `requirements.txt`, only needed if you're re-rendering these specific artifacts yourself):

- **Notebooks** (`jupytext`-paired `.py`/`.ipynb` files under `notebooks/`): `pip install jupytext nbconvert`.
- **`proposal/proposal.pdf`** from `proposal/proposal.md`: `pandoc` (e.g. `brew install pandoc`) plus `pip install weasyprint`.

## Repository Structure

```
unsw-ma-hackathon-2026/
├── data/
│   ├── README.md                     # Expected filenames, immutability note
│   ├── Kiva_Loans.pkl                # Full 1.45M-row dataset (git-ignored)
│   ├── Kiva_Loans_Sample.pkl         # Original 100-row illustrative sample (git-ignored)
│   └── Kiva Data Dictionary.xlsx     # Field-level schema reference (git-ignored)
├── docs/superpowers/                  # Design spec, plan, and full collaboration log
├── notebooks/
│   ├── 0_starter_eda.ipynb/.py            # Preliminary - 100-row sample, pipeline demonstration only
│   ├── 1_full_dataset_eda.ipynb/.py       # Real full-dataset EDA (descriptive only)
│   ├── 2_full_dataset_modeling.ipynb/.py  # Real full-dataset modeling (the actual pipeline run)
│   └── kernels/<slug>/kernel-metadata.json  # Kaggle kernel definitions (see Kaggle Workflow)
├── proposal/
│   ├── proposal.md                   # Submitted proposal (source)
│   ├── proposal.pdf                  # Styled, rendered, submitted proposal
│   └── assets/proposal.css           # Stylesheet used to render the PDF
├── reports/
│   ├── generated/                    # Output of a sample-data `run_analysis` call (git-ignored)
│   ├── generated_full_dataset/       # Committed snapshot: the verified full-dataset run
│   └── README.md                     # Explains both of the above
├── resources/nltk_data/sentiment/     # Vendored VADER lexicon + its upstream MIT license/provenance
├── scripts/
│   ├── publish_kaggle_dataset.sh     # Push data/ or src/ to their private Kaggle Datasets
│   └── push_kaggle_kernel.sh         # Push a notebook to its private Kaggle kernel
├── src/
│   ├── __init__.py
│   ├── data_loader.py                # Loads the pickle, parses dates, derives the outcome
│   ├── features.py                   # Deterministic narrative/borrower/financial features
│   ├── text_transformer.py           # Leakage-safe TF-IDF/NMF topic transformer
│   ├── topics.py                     # Full-sample exploratory topic-modeling convenience wrapper
│   ├── validation.py                 # Chronological train/holdout split, InsufficientDataError
│   ├── modeling.py                   # Leakage-safe chronological baseline + Ridge evaluation
│   ├── statistical_analysis.py       # Robust OLS/GLM explanatory (association) models
│   ├── advanced_modeling.py          # Nonlinear (HistGradientBoostingRegressor) benchmark
│   ├── binary_modeling.py            # Leakage-safe chronological classifier for the 24h outcome
│   └── run_analysis.py               # CLI orchestrator: runs all stages, writes reports
├── tests/                             # Offline test suite, no dataset or network required
├── .gitignore
├── requirements.txt
├── requirements-lock.txt              # Exact versions behind every committed artifact
└── README.md                          # This file
```

## Research Questions

**Central question.** Which narrative choices are associated with faster funding, for whom, and when, after separating presentation from structural constraint?

**Supporting questions.** (kept in sync with `proposal/proposal.md`'s Project Aim section - see that file for the authoritative, current wording)

- Which narrative characteristics — specificity, tone, beneficiary focus, agency, and thematic framing — are associated with funding speed after controlling for loan amount, term, sector, region, and borrower structure?
- Does that association differ across pre-specified segments — analysis period, region group, and loan-size band by default, with a sector interaction as an explicitly scoped extension (restricted to adequately represented sectors)?
- Did the narrative–speed association shift across the **pre-pandemic, pandemic-disruption, and post-pandemic** periods — the project's central **evolutionary-perspective** test?
- How well do patterns learned on earlier loans predict later-period outcomes, and which controllable features carry the most practical opportunity?

This project studies **aggregate, loan-level** patterns, not individual lender psychology, and reports **associations, never causal effects**. Every statistical claim in this repository uses association language ("associated with"), never "causes" or "proves." Both outcomes are defined only among loans that were **eventually funded** (confirmed on the full dataset too: only `funded`/`refunded` statuses exist, no true rejected/expired loans) - see `proposal/proposal.md`'s Project Aim section for the outcome-boundary caveat this implies.

## Running the Analysis

**Test the pipeline on the small sample** (seconds, safe to run anytime):

```bash
python3 -m src.run_analysis --data data/Kiva_Loans_Sample.pkl --output-dir reports/generated
```

**Run it on the real full dataset** (this took ~1h37m locally on a 32GB/10-core machine - see [Kaggle Workflow](#kaggle-workflow) if you'd rather not tie up your laptop for that long):

```bash
python3 -m src.run_analysis --data data/Kiva_Loans.pkl --output-dir reports/generated_full_dataset \
    --extra-interaction 'family_mentions_per_100_words:C(sector_group)'
```

The `--extra-interaction` flag activates the sector interaction, which stays opt-in by default because it needs a sample large enough to define "adequately represented sectors" (`src/features.py::MIN_SECTOR_OBSERVATIONS`) - true of the full dataset, not the 100-row sample.

Either command writes `analysis_summary.json` (machine-readable metrics, dataset audit trail, software versions) and `association_summary.txt` (human-readable, association-language narrative) atomically to `--output-dir`. Paths accept relative or absolute forms and resolve against the caller's current working directory - but `python3 -m src.run_analysis` itself must be run from the repository root (or with the repo root on `PYTHONPATH`), since that is what makes the `src` package importable. `--holdout-start` (default `2024-01-01`) sets the chronological train/holdout boundary.

To open and step through the notebook versions of the same analysis:

```bash
jupyter notebook notebooks/0_starter_eda.ipynb          # preliminary, sample-only
jupyter notebook notebooks/1_full_dataset_eda.ipynb     # real EDA, full dataset
jupyter notebook notebooks/2_full_dataset_modeling.ipynb  # real modeling, full dataset
```

or open any `.py` counterpart directly in VS Code / Spyder and run it as a percent-format script.

## Kaggle Workflow

`1_full_dataset_eda.ipynb` and `2_full_dataset_modeling.ipynb` can run as **private Kaggle kernels** instead of locally - useful for the modeling run in particular, which is CPU-heavy and slow to repeat on a laptop. Both are **self-contained**: standard public packages only (pandas, numpy, scikit-learn, statsmodels, patsy, nltk) - deliberately **no dependency on this repo's own `src/` package**, so there is no private "code" dataset to publish or keep in sync, and no risk of the notebook silently failing to find it. `0_starter_eda.ipynb` stays local-only - its whole purpose is to demonstrate the tested `src/` pipeline runs correctly, so it inherently needs that package, and it runs in seconds on the 100-row sample anyway.

One **private** Kaggle Dataset (`tuannm3812/kiva-loans-hackathon-data`: `Kiva_Loans.pkl`, `Kiva_Loans_Sample.pkl`, the data dictionary) supplies the raw inputs - this is competition data used as a hosted compute backend for the team, not a public release. Both kernels run with `enable_internet: true` (only to fetch the public NLTK VADER lexicon on first run - `nltk.download("vader_lexicon")`, cached after that; no other network access happens).

**Publish/update the data** (only needed after `data/Kiva_Loans*.pkl` changes):

```bash
scripts/publish_kaggle_dataset.sh version "describe the change"
# first-time only: create instead of version
```

**Push a notebook to its kernel and run it on Kaggle's compute:**

```bash
scripts/push_kaggle_kernel.sh modeling       # notebooks/2_full_dataset_modeling.ipynb
scripts/push_kaggle_kernel.sh eda            # notebooks/1_full_dataset_eda.ipynb
kaggle kernels status tuannm3812/kiva-hackathon-full-dataset-modeling   # poll until "complete"
```

Each notebook auto-detects whether it's running locally or on Kaggle (checks for `/kaggle/input/...`) and resolves the data path accordingly - the same source file works in both places unchanged. Kaggle's Output tab offers the printed metrics/summary tables for review once a kernel finishes; nothing here is GPU-accelerated (Ridge/HistGradientBoosting/statsmodels are all CPU), so `enable_gpu` is `false` on both kernels.

**Note:** these two notebooks are a deliberately *simpler, streamlined* re-implementation of the same design ideas the tested `src/` pipeline uses (chronological split, robust HC3 standard errors, association-only language) - not a port of its exact code, so their numbers won't match `reports/generated_full_dataset/` exactly. `python3 -m src.run_analysis` (or `0_starter_eda.ipynb`/its full-dataset equivalent, run locally) remains the authoritative source for anything going into the final presentation.

## Chronological Validation and Leakage Protections

All evaluation is **chronological, not random**: models train on loans posted before a cutoff date and are scored only on loans posted on or after it, mirroring how a model would actually be used to score newly posted loans (`src/validation.py::chronological_holdout`). `src/modeling.py`'s Ridge/baseline evaluation, `src/advanced_modeling.py`'s nonlinear regressor, and `src/binary_modeling.py`'s 24-hour classifier (reporting ROC AUC, average precision, and Brier score) all share this exact same split and preprocessing, not three separately derived ones. A dedicated `InsufficientDataError` distinguishes "this split has too little usable data" from unrelated bugs, so a too-small split degrades gracefully into a labeled diagnostic instead of a misleading number or a crash.

Every learned transformation is fit on the training partition only and merely *applied*, never refit, to the holdout:

- Missing-value imputation and feature scaling/encoding (`src/modeling.py::prepare_chronological_matrices`).
- The TF-IDF vectorizer and NMF topic model (`src/text_transformer.py::KivaTopicTransformer`) - `src/topics.py` provides a separate, explicitly labeled full-sample exploratory wrapper around the same transformer, for descriptive use only, never for evaluating held-out predictions.

Predictors are selected via an **explicit allowlist, not a blocklist** (`src/modeling.py::build_predictor_frame`), so a leakage-sensitive or post-outcome field cannot be silently reintroduced by a future edit. A missing outcome is never imputed - only rows with a `valid_completed_outcome` are used for the duration model, and only rows with a non-null `funded_within_24h` are used for the binary model.

## Data Field Groups

**Outcomes** (derived in `src/data_loader.py::prepare_analysis_data`, never used as predictors):

- `funding_speed_days` = `raisedDate - fundraisingDate` (fractional days)
- `log_funding_speed` = `log1p(funding_speed_days)`
- `funded_within_24h` = 1 if `funding_speed_days <= 1`, else 0
- `valid_completed_outcome`, `outcome_issue`, `analysis_period` (bookkeeping / period bucketing)

**Predictors available at or before posting** (the only fields the allowlist permits):

- **Narrative:** `description` (full content-derived features - word/sentence counts, sentiment, per-100-word framing rates, training-fitted topic proportions); `use` and `whySpecial` currently contribute only presence/missingness flags (`use_missing`, `whySpecial_missing`) to the model, not their own content-derived counts
- **Borrower:** `borrowerCount`, group-level `gender` classification (female, male, mixed, or unknown - missingness is preserved as its own category, never defaulted to female)
- **Loan structure:** `loanAmount`, `lenderRepaymentTerm`, `repaymentInterval`
- **Purpose:** `sector`, `activity`, and (explanatory models only) `sector_group` - `sector` collapsed to a fixed observation-count threshold (`src/features.py::MIN_SECTOR_OBSERVATIONS`), used to activate the otherwise opt-in sector interaction
- **Geography/economic context:** `country_iso`, `region`, `country_ppp`, and (explanatory models only) `region_group` - `region` collapsed to a fixed observation-count threshold (`src/features.py::MIN_REGION_OBSERVATIONS`), not a hardcoded region list, so it adapts automatically to whichever regions the data actually supports
- **Time:** year, month, and `analysis_period` derived from `fundraisingDate` (2016-2019, 2020-2021, 2022-2025)

**Excluded from the predictor allowlist** (leakage-sensitive or redundant):

- All post-outcome fields: `raisedDate`, `funding_speed_days`, `log_funding_speed`, `funded_within_24h`, `valid_completed_outcome`, `outcome_issue`, `status`
- `fundsLentInCountry` - excluded by default until its posting-time availability is verified
- `country_name` - the same country identity as `country_iso` at equal cardinality; including both would one-hot encode the same signal twice
- Identifiers, image URLs, borrower names, and raw geographic coordinates

## Full-Dataset Results

Verified 2026-08-27 against the real 1,453,846-row dataset (`reports/generated_full_dataset/`, committed as a labeled snapshot - see `reports/README.md`). Full detail, including the independent cross-check of these numbers, is in the collaboration log; headline results:

- **Both explanatory models fit successfully** (duration OLS and the 24-hour binary GLM) - at the 100-row sample, the binary model hit quasi-complete separation and could only report a diagnostic.
- **Predictive holdout performance** (2024-2025 holdout): Ridge MAE 6.63 days (the sample's catastrophic R² = -12.2 was a small-sample artifact, confirmed); the nonlinear (HistGradientBoosting) benchmark reaches **MAE 5.20 days, R² = 0.54**.
- **24-hour classifier:** ROC AUC 0.90, average precision 0.83.
- Loan amount and repayment term dominate predictive importance, but a narrative topic cluster ranks 8th among ~290 features - a controllable feature genuinely competing with structural ones.
- Family/communal framing is associated with faster funding overall, but - a genuine, honestly-reported surprise relative to the proposal's working hypothesis - that association gets *weaker*, not stronger, during the pandemic-disruption period. Family framing's effect also varies substantially by sector (e.g. strongly slows funding in Water/Clean Energy, speeds it in Personal Use).
- Urgency appeals are associated with faster funding and higher odds of within-24h funding, consistently across both models.

These are the numbers backing the final slide deck - not the illustrative 100-row figures in `notebooks/0_starter_eda.ipynb` or the (now-submitted) `proposal/proposal.md`.

## Proposal (Submitted)

`proposal/proposal.md` (source, 1,421 words excluding references - see `tests/test_proposal.py` for the authoritative count) and `proposal/proposal.pdf` (styled render) were submitted for the proposal round and led to the team's finalist selection. Kept here unchanged as the historical submission record; new analysis and the final slide deck live elsewhere (this README's Full-Dataset Results section, and the eventual slides).

## Known Limitations

- `notebooks/0_starter_eda.ipynb` and `proposal/proposal.md` were both built against `data/Kiva_Loans_Sample.pkl`, a **100-row illustrative sample** - treat every number in either as a pipeline demonstration, not final evidence. The real findings are in [Full-Dataset Results](#full-dataset-results) above.
- Every result in this project is an **association**, never a causal claim - borrowers were not randomly assigned a narrative framing, loan amount, or gender composition.
- `refunded`-status loans are included in the funding-speed analysis on the same footing as `funded` ones (they completed funding normally; the refund is a later, unrelated event) - see `reports/generated_full_dataset/association_summary.txt`'s audit trail for the exact counts this affects.
