# Matched text benchmark implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task by task. Track the execution ledger and preserve prior evidence.

**Goal:** Quantify outcome availability and the incremental predictive information in narrative text on the full Kiva dataset, then connect accepted results to the notebook and revised deck.

**Architecture:** Add a separate research runner without changing the primary analysis pipeline. Shared helpers own as-of splits, feature blocks and diagnostics. An immutable aggregate bundle plus ignored private predictions supports an output-free notebook and a separately versioned deck.

**Tech Stack:** Existing Python/pandas/scikit-learn/SciPy, pytest, Jupytext, Matplotlib; existing artifact-tool deck builder.

**Spec:** `docs/5_ml_refinement_plan.md`, with interpretation in `docs/4_research_review.md`.

## Global constraints and frozen protocol

- Full input: 1,453,846 records; primary saved reports, proposal and submitted artifacts stay unchanged.
- Five expanding annual windows: 2021, 2022, 2023, 2024, 2025. All are retrospective; 2024–25 have already informed project interpretation.
- Train only on valid durations posted and completed strictly before the evaluation year's January 1. Evaluate valid completed records posted during that calendar year; record observed coverage and eventual-completion selection.
- Preserve refunded records in the main comparison; report separate funded-only diagnostics.
- Fixed seed 42. No tuning against evaluation windows. Fixed configurations are benchmarks, not optimised winners.
- B0: training median / prevalence. B1: past-only country × sector × calendar-month baseline, shrunk with 50 training observations toward global median/prevalence.
- S: borrower count/group/gender, amount and fixed size bands, repayment term/interval, country/region, sector/activity, posting year/month. Exclude `country_ppp` and `fundsLentInCountry` because historical availability is unverified; no identifiers or outcomes.
- M: description presence, word/character/sentence length and average word/sentence length. L: existing deterministic framing, specificity and VADER measures. R: training-only description TF-IDF, word 1–2 grams, max 5,000 features, min_df=5, sublinear_tf=True, float32. P: trimmed `whySpecial` category, unvalidated proxy, training-fitted encoder.
- Sparse linear arms: S, T=M+L+R, S+M, S+M+L, S+M+L+R, S+P, S+P+M+L+R. Ridge on log1p duration (alpha=10, lsqr, tol=1e-5, max_iter=1000); SGD logistic (alpha=1e-5, max_iter=100, tol=1e-4, average=True, early_stopping=False).
- Compact histogram-boosting arms: S, S+M+L, S+P, S+P+M+L. Both targets use 100 iterations, 15 leaves, learning_rate=.1, l2=1, early_stopping=False. Training-only ordinal categories capped at 127 levels; unknown values handled explicitly. No claim about richer TF-IDF in the tree family.
- Model comparisons share exact rows and targets within a window. Preprocessing fits on training rows only. The sparse text matrix is never densified.
- Duration: day MAE/MedAE/RMSE/R²/bias and log MAE. Classification: prevalence, AUC/AP/Brier/log loss and reliability bins with counts.
- Paired uncertainty for mean losses: 1,000 resamples of calendar months and country clusters, weighted by record count, separately. These are conditional fixed-model sensitivity intervals, not causal or retraining uncertainty; annual month counts are small.
- Group diagnostics report count/base rate/MAE/Brier and suppress groups below 200 records. Exact and digit-normalised text novelty are diagnostics; they are not proof of semantic near-duplication.
- No human construct-validation, deployment, new data acquisition or prospective pilot is claimed. These remain external prerequisites.
- No push, publication or blanket staging. Preserve all prior uncommitted poster/research work. Work on the existing `codex/research-maintenance` feature branch because the approved specification and new deck are uncommitted here.

## Review focus

1. Boundary-crossing completions and missing dates cannot enter as-of training.
2. All comparisons retain identical row order, including empty text and unseen categories.
3. Outcome/identifier changes cannot alter predictors; evaluation vocabulary cannot enter training.
4. Degenerate classes, empty vocabulary, nonfinite predictions and convergence problems must be visible.
5. Reports cannot export raw text/identifiers or mislabel incomplete execution as accepted evidence.

### Task 1: Availability contract and audit

**Files:** create `src/benchmark_data.py`, `tests/test_benchmark_data.py`.
**Interfaces:** `calendar_split(prepared, year) -> (train_index, test_index)`; `audit_availability(df, years) -> dict`; `build_benchmark_frame(df, chunk_size=25000) -> DataFrame`; `feature_registry() -> dict`.

- [x] Write synthetic tests for crossing completions, missing/negative duration, exact cutoff, duplicate indexes/IDs, empty descriptions and predictor exclusions.
- [x] Run tests; verify missing implementation fails.
- [x] Implement the audit and shared feature registry; reuse deterministic extraction in bounded chunks, export only aggregate audit.
- [x] Run the task tests; expected all pass.

### Task 2: Matched models and diagnostics

**Files:** create `src/benchmark_models.py`, `src/benchmark_metrics.py`, `tests/test_benchmark_models.py`, `tests/test_benchmark_metrics.py`.
**Interfaces:** `fit_predict_window(frame, train_index, test_index, config) -> iterator[(family, arm, predictions, fit_metadata)]`; `score_predictions(y_days, y_binary, days, probability) -> dict`; `paired_loss_intervals(...) -> dict`.

- [x] Write tests proving block isolation, training-only vocabulary/category fitting, same-row predictions, unseen/missing inputs, deterministic fixed configurations, paired constant-difference intervals and empty/single-class diagnostics.
- [x] Observe failures, implement sparse linear and compact tree branches with fixed budgets, then run all task tests.
- [x] Record library configuration, fit times, warnings and feature dimensions. Fail on nonfinite predictions.

### Task 3: Immutable full-data runner

**Files:** create `src/run_text_benchmark.py`, `tests/test_text_benchmark_runner.py`.
**Interfaces:** `run_benchmark(data_path, output_dir, config, feature_cache=None) -> dict`; CLI `python -m src.run_text_benchmark --data PATH --output-dir NEW_DIR`.

- [x] Test a synthetic end-to-end bundle, source/data/config identity, rejected overwrite, report privacy and completed-run status.
- [x] Implement auditable progress and per-window checkpoints, aggregate results, private ignored row predictions, calibration and group diagnostics. Cache deterministic features only with exact data/source identity.
- [x] Run task tests and the full offline suite, then run the fixed full-data protocol. Inspect every completion/warning and preserve execution logs.
- [x] Review results and provenance before marking any run accepted. Failed runs remain diagnostic evidence.

### Task 4: Executable insight notebook

**Files:** replace maintained `notebooks/2_full_dataset_modeling.py` and synchronise its `.ipynb`; adjust kernel documentation as needed; add notebook contract tests.
**Interfaces:** loads and validates a selected completed benchmark bundle; optional explicit new-run mode calls shared runner. Default reviewed-report mode is offline and does not silently retrain.

- [x] Add tests for shared-source use, result provenance, removed false claims and output policy.
- [x] Implement the 12-section insight structure, dynamic metrics/plots and honest pending measurement/external-data sections.
- [x] Execute the notebook against the accepted full-data bundle; keep the verified execution copy private and committed pair output-free.

### Task 5: Research interpretation, deck and final review

**Files:** add `docs/6_matched_text_results.md`, reviewed aggregate snapshot/readme; update current readmes, evidence notice and a new deck version/brief; append collaboration log.

- [x] Interpret matched gains, uncertainty, calibration and transfer limitations without causal or deployment claims.
- [x] Update slides 5/6/10 and evidence register in a new version; preserve the prior research-design deck.
- [x] Run relevant contracts, full suite, notebook source/output checks, privacy/source checks and deck visual/package validation.
- [x] Obtain an independent review of the integrated changes and result evidence; address material findings, rerunning affected work if needed.
- [x] Leave a reviewable diff and append verified outcomes and unresolved limitations; no automatic commit or push.

## Verified completion

Full benchmark completed and independently checked: 65 model/arm windows,
120 paired intervals and 5,681 subgroup slices. The accepted aggregate snapshot
is `reports/text_benchmark_reviewed/`. Notebook 2 executed all 13 report/plot
code cells with five embedded figures and no errors; the source pair stays
output-free. The new 16-slide deck passed package, geometry and re-import
validation, and its two native chart series match the report. Full offline
suite: 160 passed; subsequent notebook contracts: 9 passed. Original competition
evidence is preserved. Human annotation, new histories and a real pilot remain
external research prerequisites. No commit or push was performed.
