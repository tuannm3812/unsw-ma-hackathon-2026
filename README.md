# UNSW Marketing Analytics Hackathon Challenge 2026

Team repository for the **UNSW Marketing Analytics Hackathon Challenge 2026**, using loan-level data from the prosocial micro-lending platform **Kiva** (spanning 2016-2025) to study **funding speed** in subsistence marketplaces: which narrative choices in a borrower's loan description are associated with faster funding, for whom, and when.

New to this project? Read this file top to bottom once - it's written to get you from a fresh clone to a green test suite, then to understanding the whole pipeline and where things stand.

## Start Here

The finished work, as files you can open directly:

| Deliverable | What it is |
| --- | --- |
| [Portfolio deck (PDF)](deliverables/deck/cultural-blend-portfolio-deck.pdf) | 30 slides: 22 main and 8 appendix. [Live Google Slides link](deliverables/deck/google-slides-link.md) |
| [Case study (PDF)](deliverables/report/cultural-blend-case-study.pdf) | The written story; source in [docs/3_portfolio_case_study.md](docs/3_portfolio_case_study.md) |
| [A1 poster, portrait (PDF)](deliverables/poster/cultural-blend-poster-a1-portrait.pdf) | One-page summary, 594 × 841 mm |
| [A1 poster, landscape (PDF)](deliverables/poster/cultural-blend-poster-a1-landscape.pdf) | The same content, 841 × 594 mm |
| [Claims register](docs/presentation/claims_register.md) | Every number the deck, posters and case study quote, with its source file |

**What we found, in brief.** All results are associations on loans that eventually funded.

- **Waits got longer after 2019.** Same-day funding fell from 42.5% in 2019 to 32.3% in 2020, and
  393,847 of 1,453,840 loans (27.1%) waited more than two weeks.
- **Slow funding is mostly a lender-side delay.** 96.4% of loans reached the borrower before
  listing, so funding time mainly reflects a partner replenishing capital.
- **Loan details predict who waits; wording adds little.** Five framing measures stay within ±5% of
  funding time (±0.05 on log(1 + days)), while a doubled loan amount goes with +44.6%.
- **A flag at listing beats a simple lookup.** In a retrospective check, a boosted tree on loan
  details catches the slowest fifth of loans 2.63–4.04 times better than chance, against
  1.97–2.74 for a historical lookup, in every test year.
- **Our recommendation:** predict slow loans, prioritise lender-side support for them, and test
  before giving any writing advice. No description edit or support lever has been tested yet.

## Project Status

**Complete — Cultural Blend was one of 8 finalist teams.** The final took
place on 4 September 2026. The competition attracted 44 registered teams,
133 students, 19 universities and 8 countries; Cultural Blend is listed as a
finalist in the [official UNSW results](https://www.unsw.edu.au/business/our-schools/marketing/news-events/student-events/MA-hackathon)
(reviewed 2026-10-24).

The portfolio deliverables above were completed on 10 November 2026; ongoing
work is research maintenance. The primary
full-data results are a verified **saved run**, generated on 2026-08-31, not a
fresh rerun. Start with the [portfolio case study](docs/3_portfolio_case_study.md)
and [current evidence and corrections](docs/2_evidence_and_corrections.md).
Submitted proposal files and generated presentation artifacts are historical;
read the correction notice before reusing their claims. Event instructions
are preserved in [historical final-round logistics](docs/presentation/2026_final_round_logistics.md).

The separate November update adds an as-of training audit and matched text
comparisons across five annual evaluation windows. Read the
[new findings](docs/6_matched_text_results.md), run the
[maintained insight notebook](notebooks/2_full_dataset_modeling.ipynb), or use
the [updated deck and slide briefing](docs/presentation/research_refresh/README.md).
The 8 November [equivalence screen](reports/equivalence_screen_reviewed/README.md)
shows which framing associations are small enough to bound and which remain
unresolved; the [portfolio case study](docs/3_portfolio_case_study.md) now tells
the full story, and the current deck lives in
[docs/presentation/portfolio_deck](docs/presentation/portfolio_deck/README.md).
The [research review](docs/4_research_review.md) explains the decision framework;
the [approved ML design](docs/5_ml_refinement_plan.md) preserves the pre-run plan.

**Field reference:** [`docs/1_data_dictionary.md`](docs/1_data_dictionary.md) documents every
column in the raw data — the official definition from the competition's data dictionary, its
real coverage, and exactly how this project used it (predictor, outcome, clustering unit, or
deliberately omitted, with the reasoning). Regenerate with `python3 scripts/build_data_dictionary.py`.

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

`requirements.txt` covers everything needed to run the pipeline, notebooks, and test suite: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `openpyxl`, `statsmodels`, `patsy`, `scipy`, `nltk`, `ipykernel`, `notebook`, `pytest`. There is no `xgboost` or `lightgbm` dependency in `requirements.txt` - the nonlinear benchmark uses scikit-learn's built-in `HistGradientBoostingRegressor` instead. The one exploratory tuned-XGBoost comparison in the deck's appendix ran on Kaggle; its aggregate results are in `reports/experiments_2026_11_08/`. Sentiment scoring (VADER, via `nltk`) works out of the box with no separate download step: the lexicon is vendored directly in `resources/nltk_data/` (see that directory's README for its license/provenance) instead of relying on `nltk.download(...)`, which this project's tests/CLI must never call (no network access during import or feature extraction).

`requirements.txt` intentionally uses lower bounds (`>=`) so installs stay possible as new versions ship - a different set of versions satisfying those same bounds can produce different numerical edge cases and warnings on identical code (this project hit exactly that during development). `pip install -r requirements-lock.txt` pins the exact core numerical/statistical package versions this project was verified against, if you ever hit different numerical/warning behavior and want to rule that out first.

The current deck and posters use Google Sans and live in Google Slides. The archived September PPTX uses DM Sans: install the fonts in `docs/presentation/fonts/` on any machine that opens it (see that folder's README), or PowerPoint silently substitutes.

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
├── deliverables/                     # Final deck PDF and link, case study PDF, A1 poster PDFs (copies; see its README)
├── docs/
│   ├── 0_coding_standards.md          # This project's coding standards (tailored from the shared baseline)
│   ├── 2_evidence_and_corrections.md   # Current interpretation and historical claim corrections
│   ├── 3_portfolio_case_study.md       # Concise case study and LinkedIn achievement text
│   ├── 4_research_review.md           # Research diagnosis and consulting framework
│   ├── 5_ml_refinement_plan.md        # Approved pre-run study design
│   ├── 6_matched_text_results.md      # Separate November predictive findings
│   ├── presentation/                  # Current portfolio deck, claims register, design standard; earlier material in archive/
│   │   ├── claims_register.md         # Every number the deck, posters and case study quote, with its source
│   │   └── portfolio_deck/            # Deck storyline, assets and rendered slides
│   └── superpowers/                   # Design spec, plan, and full collaboration log
├── notebooks/
│   ├── 0_starter_eda.ipynb/.py            # Preliminary - 100-row sample, pipeline demonstration only
│   ├── 1_full_dataset_eda.ipynb/.py       # Real full-dataset EDA (descriptive only)
│   ├── 2_full_dataset_modeling.ipynb/.py  # Shared-source matched benchmark and reviewed insight workflow
│   ├── 3_expanded_feature_sensitivity.ipynb/.py  # Separate exploratory sensitivity workflow
│   └── kernels/<slug>/kernel-metadata.json  # Kaggle kernel definitions (see Kaggle Workflow)
├── proposal/
│   ├── proposal.md                   # Submitted proposal (source)
│   ├── proposal.pdf                  # Styled, rendered, submitted proposal
│   └── assets/proposal.css           # Stylesheet used to render the PDF
├── reports/
│   ├── generated/                    # Output of a sample-data `run_analysis` call (git-ignored)
│   ├── generated_full_dataset/       # Committed snapshot: the verified full-dataset run
│   ├── expanded_feature_sensitivity/  # Historical sensitivity, preserved after numerical audit
│   ├── expanded_feature_sensitivity_reviewed/  # Corrected inference and programme controls
│   ├── text_benchmark_reviewed/       # Separate matched predictive benchmark and technical review
│   ├── programme_proxy_audit/         # Aggregate full-data coverage and nesting audit
│   ├── equivalence_screen_reviewed/   # Exploratory screen of which framing links are small enough to bound
│   ├── evidence_sources/              # Aggregate summaries the deck and claims register cite
│   ├── experiments_2026_11_08/        # Exploratory subgroup, bootstrap, placebo, forecaster and flag checks
│   ├── loss_alignment_2025/           # Loss-alignment extension of the matched benchmark
│   ├── period_trend/                  # Yearly same-day and long-wait shares
│   └── README.md                     # Evidence boundaries and snapshot guidance
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
│   ├── modeling.py                   # Primary posting-date baseline + Ridge evaluation
│   ├── benchmark_*.py                # Separate as-of cohorts, features, matched models and review contracts
│   ├── run_text_benchmark.py          # Full-data matched benchmark CLI
│   ├── statistical_analysis.py       # Robust OLS/GLM explanatory (association) models
│   ├── advanced_modeling.py          # Nonlinear (HistGradientBoostingRegressor) benchmark
│   ├── binary_modeling.py            # Leakage-safe chronological classifier for the 24h outcome
│   ├── feature_sensitivity.py        # Country-clustered expanded OLS/LPM sensitivity
│   ├── programme_audit.py            # Aggregate programme-text proxy audit
│   ├── research_review.py            # Reviewed inference with programme-control comparison
│   └── run_analysis.py               # Primary CLI orchestrator: runs all stages, writes reports
├── tests/                             # Offline test suite, no dataset or network required
├── .gitignore
├── requirements.txt
├── requirements-lock.txt              # Pins for direct dependencies; not a complete environment
└── README.md                          # This file
```

## Research Questions

**Central question.** Which narrative choices are associated with faster funding, for whom, and when, after separating presentation from structural constraint?

**Supporting questions.** These extend the research aim in the [submitted proposal](proposal/proposal.md), whose numerical examples used the 100-row sample.

- Which narrative characteristics — specificity, tone, beneficiary focus, agency, and thematic framing — are associated with funding speed after controlling for loan amount, term, sector, region, and borrower structure?
- Does that association differ across pre-specified segments — analysis period, region group, and loan-size band by default, with a sector interaction as an explicitly scoped extension (restricted to adequately represented sectors)?
- Did the narrative–speed association shift across the **pre-pandemic, pandemic-disruption, and post-pandemic** periods — the project's central **evolutionary-perspective** test?
- How well do patterns learned on earlier loans predict later-period outcomes, and which controllable features carry the most practical opportunity?

This project studies **aggregate, loan-level** patterns, not individual lender psychology, and reports **associations, never causal effects**. Historical presentation claims require the qualifications in the [correction notice](docs/2_evidence_and_corrections.md). Both outcomes are defined only among loans that were **eventually funded** (confirmed on the full dataset too: only `funded`/`refunded` statuses exist, no true rejected/expired loans) - see `proposal/proposal.md`'s Project Aim section for the outcome-boundary caveat this implies.

## Running the Analysis

**Test the pipeline on the small sample** (seconds, safe to run anytime):

```bash
python3 -m src.run_analysis --data data/Kiva_Loans_Sample.pkl --output-dir reports/generated
```

**Run it on the real full dataset** (this took ~1h37m locally on a 32GB/10-core machine - see [Kaggle Workflow](#kaggle-workflow) if you'd rather not tie up your laptop for that long):

```bash
python3 -m src.run_analysis --data data/Kiva_Loans.pkl --output-dir reports/full_dataset_NEW_RUN_ID \
    --extra-interaction 'family_mentions_per_100_words:C(sector_group)' \
    --cluster-sensitivity-column country_name
```

The `--extra-interaction` flag activates the sector interaction, which stays opt-in by default because it needs a sample large enough to define "adequately represented sectors" (`src/features.py::MIN_SECTOR_OBSERVATIONS`) - true of the full dataset, not the 100-row sample. The `--cluster-sensitivity-column` flag is required to reproduce the cluster-robust sensitivity check the Full-Dataset Results section and both notebooks rely on - omitting it silently regenerates `association_summary.txt`/`analysis_summary.json` without that section, even though this README and the notebooks now cite it as part of the committed snapshot.

Choose a fresh run ID for full-data reruns and capture provenance alongside the outputs; preserve the committed primary snapshot. Either command writes `analysis_summary.json` (machine-readable metrics, dataset audit trail, software versions) and `association_summary.txt` (human-readable, association-language narrative) atomically to `--output-dir`. Paths accept relative or absolute forms and resolve against the caller's current working directory - but `python3 -m src.run_analysis` itself must be run from the repository root (or with the repo root on `PYTHONPATH`), since that is what makes the `src` package importable. `--holdout-start` (default `2024-01-01`) sets the chronological train/holdout boundary.

Open the walkthrough for the intended evidence source:

```bash
jupyter notebook notebooks/0_starter_eda.ipynb          # preliminary, sample-only
jupyter notebook notebooks/1_full_dataset_eda.ipynb     # real EDA, full dataset
jupyter notebook notebooks/2_full_dataset_modeling.ipynb  # reviewed matched-benchmark insights
```

or open any `.py` counterpart directly in VS Code / Spyder and run it as a percent-format script.

Notebook 2 defaults to `RUN_MODE = "reviewed_report"`, reading
`reports/text_benchmark_reviewed/` without loading raw loans or retraining.
It validates execution completeness, artifact hashes and a matching accepted
review. Set `KIVA_BENCHMARK_DIR` to another explicitly reviewed bundle to inspect
it. Run the new benchmark separately, using a fresh output directory:

```bash
LOKY_MAX_CPU_COUNT=4 python3 -m src.run_text_benchmark \
    --data data/Kiva_Loans.pkl \
    --output-dir reports/text_benchmark_NEW_RUN_ID \
    --feature-cache reports/text_benchmark_private/features.pkl
```

The optional private cache is reused only when input, source, resource and
environment identities match; choose a new cache path after a relevant change.
New runs end as `completed_pending_review`. Inspect their source/provenance,
population, convergence, paired comparisons and private recomputable predictions
before selecting aggregate evidence and recording acceptance. The notebook's
explicit `RUN_MODE = "run"` offers the same runner and labels its new output
pending review. This is a separate retrospective study; primary results stay
unchanged.

## Kaggle Workflow

`1_full_dataset_eda.ipynb` retains its private, self-contained Kaggle workflow.
The maintained `2_full_dataset_modeling.ipynb` now uses the repository's shared
benchmark and reviewed aggregate reports. Run it locally from this checkout;
the old modelling kernel metadata is historical and the push helper rejects
that retired entry point. No revised notebook has been uploaded to Kaggle.
The old two-notebook executor now executes only the unchanged EDA notebook.

Two private datasets support the historical pipeline: `tuannm3812/kiva-loans-hackathon-data`
and `tuannm3812/kiva-hackathon-src`. EDA retains its guarded VADER download;
the new local benchmark uses the vendored lexicon and runs offline.

```bash
scripts/push_kaggle_kernel.sh eda
kaggle kernels status tuannm3812/kiva-hackathon-full-dataset-eda
```

Publishing updated private datasets is a separate action; local source changes
do not update those remote copies. Preserve and inspect run artifacts before
starting another remote version.

**Regenerating the committed snapshot on Kaggle.** The ~2 h full-dataset `run_analysis` that produces `reports/generated_full_dataset/` (see "Run it on the real full dataset" above) also runs as a private *script* kernel, so it never has to occupy a laptop:

```bash
scripts/publish_kaggle_dataset.sh code version "src at <commit>"   # if src/ changed since the last publish
scripts/push_kaggle_kernel.sh pipeline                              # notebooks/kernels/full_dataset_pipeline/run_full_pipeline.py
kaggle kernels status tuannm3812/kiva-hackathon-full-dataset-pipeline   # poll until "complete"
kaggle kernels output tuannm3812/kiva-hackathon-full-dataset-pipeline -p /tmp/pipeline_out
mkdir -p reports/full_dataset_NEW_RUN_ID
cp /tmp/pipeline_out/generated_full_dataset/*.{json,txt} reports/full_dataset_NEW_RUN_ID/
```

Review the new run and its provenance before selecting it as a committed snapshot. The runner rebuilds the `src/` + `resources/` layout under `/kaggle/working` (so the vendored VADER lexicon resolves), then calls `run_analysis` with exactly the documented flags. One caveat to record honestly when committing a Kaggle-generated snapshot: its audit-trail line will show Kaggle's software versions (newer Python/pandas/statsmodels than the laptop venv recorded in earlier snapshots), so trailing digits may differ slightly from a local run - conclusions should not.

The historical self-contained modelling notebook used a simpler specification.
The current notebook uses `src/run_text_benchmark.py` and validates an explicit
reviewed bundle. The primary `python3 -m src.run_analysis` snapshot and expanded
explanatory sensitivity remain separate specifications; see the
[evidence map](docs/2_evidence_and_corrections.md).

## Chronological Validation and Leakage Protections

The historical primary evaluation uses a **posting-date chronological split**: models train on loans posted before a cutoff and are scored on later postings. This alone does not enforce availability of completed outcomes at training time (`src/validation.py::chronological_holdout`). `src/modeling.py`'s Ridge/baseline evaluation, `src/advanced_modeling.py`'s nonlinear regressor, and `src/binary_modeling.py`'s 24-hour classifier (reporting ROC AUC, average precision, and Brier score) all share this exact same split and preprocessing, not three separately derived ones. A dedicated `InsufficientDataError` distinguishes "this split has too little usable data" from unrelated bugs, so a too-small split degrades gracefully into a labeled diagnostic instead of a misleading number or a crash.

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

**Primary-pipeline predictors available at or before posting** (the fields its allowlist permits):

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

The [primary saved report](reports/generated_full_dataset/analysis_summary.json)
was generated on **2026-08-31**, with its [source provenance](reports/generated_full_dataset/provenance.json)
and [human-readable inference report](reports/generated_full_dataset/association_summary.txt)
retained together. It loaded **1,453,846** loans (2016–2025) and analysed
**1,453,840** valid completed durations after excluding six negative durations.
These include 1,452,203 funded and 1,637 refunded records. This is evidence
about time to completed platform funding, not the probability that any listing
will eventually fund.

- **Chronological predictive evaluation:** 1,174,953 training loans and
  278,887 holdout loans (2024–2025). Ridge MAE was 6.6323 days; the nonlinear
  HistGradientBoosting benchmark achieved MAE 5.2031 days and R² 0.5420.
  The 24-hour classifier achieved ROC AUC 0.8997 and average precision 0.8301.
  These evaluate prediction; they do not establish causal narrative effects.
- **Uncertainty changes the interpretation:** urgency coefficients were
  significant under HC3 but not under country clustering (duration p = 0.4943;
  24-hour p = 0.2233). This weakens a claim of association; it does not establish
  a zero effect. Sentiment remained associated with slower funding in the
  primary clustered models. Expanded sensitivity uses different controls and
  multiplicity adjustments; do not generalise that primary coefficient across
  specifications.
- **Regional family-framing patterns are descriptive:** primary average
  duration slopes were −0.0729 in the Middle East and −0.0742 in Central
  America per additional family mention per 100 words. Each region has only
  two country clusters. Their heuristic few-cluster intervals span zero;
  the analysis does not justify region-specific writing advice. The
  [correction notice](docs/2_evidence_and_corrections.md) explains why an
  interaction coefficient is not a within-region slope.
- **Expanded sensitivity is separate research:** the recovered
  [September snapshot](reports/expanded_feature_sensitivity/README.md) preserves
  history; the [reviewed inference extension](reports/expanded_feature_sensitivity_reviewed/README.md)
  documents current controls, numerical checks, uncertainty and provenance.
  It does not replace the primary models or rerun prediction. A
  [rejected diagnostic run](reports/expanded_feature_sensitivity_diagnostic/README.md)
  records an additional absorption defect caught during review.

Use the tested `src/` pipeline for primary claims. The self-contained notebooks
use simpler specifications; expanded sensitivity uses richer controls and a
linear-probability 24-hour model. Their coefficients and metrics are not
interchangeable. See [the evidence map](docs/2_evidence_and_corrections.md) and
[report guidance](reports/README.md) before reusing numbers.

## Post-competition research maintenance

The [reviewed October extension](reports/expanded_feature_sensitivity_reviewed/README.md)
reran expanded inference and added programme-text controls on the same
1,453,840 eligible records. The programme audit found 642 observed categories
and 40,012 missing labels; these are not verified partner identifiers.
Third-person duration estimates remain similar, but their individual BH-adjusted
p-value changes from 0.01236 to 0.06062 after programme adjustment. Business
framing is associated with lower 24-hour funding probability in that specification
(−0.258 percentage points per additional mention per 100 words; adjusted
p = 0.00635). Joint family tests provide a broader, specification-dependent
picture; neither finding supports a causal writing recommendation.

The fresh run records matching populations, exact categorical absorption,
country-clustered uncertainty, multiplicity adjustments, source/data hashes,
versions and execution logs. A rejected first attempt is preserved with its
failure diagnosis. Primary prediction metrics and submitted artifacts remain
unchanged. [Next evidence needed](docs/2_evidence_and_corrections.md#next-evidence-needed)
sets out the remaining research priorities.

The [November research review](docs/4_research_review.md) audits the notebook and
presentation claims against saved results and primary literature. Its
[ML refinement plan](docs/5_ml_refinement_plan.md) prioritises as-of outcome
availability, matched structure/text comparisons, temporal stability and text
measurement. The [revised deck and slide briefing](docs/presentation/research_refresh/README.md)
connect the evidence to a consulting decision framework. These are proposed
research improvements, not a fresh predictive run.

## Proposal (Submitted)

`proposal/proposal.md` (source, 1,421 words excluding references - see `tests/test_proposal.py` for the authoritative count) and `proposal/proposal.pdf` (styled render) were submitted for the proposal round and led to the team's finalist selection. Kept unchanged as the historical submission record. Presentation materials are in [docs/presentation](docs/presentation/); the [current correction notice](docs/2_evidence_and_corrections.md) qualifies older preparation claims without rewriting submitted files or generated PDF/PPTX artifacts.

## Known Limitations

- `notebooks/0_starter_eda.ipynb` and `proposal/proposal.md` were both built against `data/Kiva_Loans_Sample.pkl`, a **100-row illustrative sample** - treat every number in either as a pipeline demonstration, not final evidence. The real findings are in [Full-Dataset Results](#full-dataset-results) above.
- Every result in this project is an **association**, never a causal claim - borrowers were not randomly assigned a narrative framing, loan amount, or gender composition.
- `refunded`-status loans are included in the funding-speed analysis on the same footing as `funded` ones (they have valid completed funding timestamps; this analysis does not model repayment or explain the subsequent refund) - see `reports/generated_full_dataset/association_summary.txt`'s audit trail for the exact counts this affects.

- Platform fundraising duration is not borrower waiting time: the data dictionary records widespread pre-disbursal. Partner capital replenishment is a plausible interpretation for those records, not a measured causal or cash-flow outcome.
- Missing partner identifiers, programme differences, selective inclusion of completed funding records, observational text features, and sparse country clusters limit interpretation. Non-significant findings do not prove that narrative choices have no effect.
