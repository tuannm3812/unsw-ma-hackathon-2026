# Hackathon Project Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the exploratory Kiva repository into a tested, leakage-safe, temporally validated hackathon project with a submission-ready proposal under 1,500 words.

**Architecture:** Separate immutable data preparation, deterministic row features, learned text transformations, chronological validation, explanatory statistics, predictive benchmarking, and reporting. All learned preprocessing fits on training observations only; the notebook and CLI consume shared source functions rather than duplicating modeling logic.

**Tech Stack:** Python 3.9+, pandas, NumPy, scikit-learn, statsmodels, NLTK VADER when locally available, pytest, Markdown, Jupyter

**Spec:** `docs/superpowers/specs/2026-08-17-hackathon-project-upgrade-design.md`

## Global Constraints

- Proposal maximum: 1,500 words including tables, figures, and appendices; references excluded.
- Treat findings as loan-level associations, not causal effects or individual lender choices.
- Never impute a missing outcome.
- Never use post-outcome fields as predictors.
- Fit imputation, scaling, encoding, TF-IDF, and NMF on training observations only.
- Use chronological evaluation as the primary validation design.
- Keep raw organizer-provided files unchanged.
- Tests must run without the competition dataset and without network access.
- Do not download NLTK resources during module import.
- Use fixed random seeds for randomized estimators.

## File Map

- `src/data_loader.py`: schema validation, date parsing, targets, validity flags, periods.
- `src/features.py`: deterministic row-level narrative, borrower, structural, and contextual features.
- `src/text_transformer.py`: training-fitted TF-IDF and NMF transformer.
- `src/validation.py`: chronological splits and split validation.
- `src/modeling.py`: leakage-safe preprocessing, baselines, regularized models, metrics.
- `src/statistical_analysis.py`: robust explanatory duration and 24-hour models.
- `src/advanced_modeling.py`: one boosted-tree benchmark with held-out interpretation.
- `src/run_analysis.py`: root-level CLI orchestration and report creation.
- `notebooks/starter_eda.py` and `notebooks/starter_eda.ipynb`: concise consumer of shared analysis functions.
- `tests/conftest.py`: synthetic Kiva fixtures.
- `tests/test_data_loader.py`: schema, outcomes, invalid rows, periods.
- `tests/test_features.py`: deterministic narrative and borrower features.
- `tests/test_text_transformer.py`: training-only vocabulary and stable output.
- `tests/test_validation.py`: chronological splitting and guardrails.
- `tests/test_modeling.py`: predictor exclusions, time split, and smoke evaluation.
- `tests/test_statistical_analysis.py`: robust model smoke checks and association labels.
- `tests/test_run_analysis.py`: end-to-end report creation on synthetic data.
- `proposal/proposal.md`: organizer-aligned proposal draft.
- `README.md`: accurate setup, commands, design, caveats, and schedule.
- `requirements.txt`: add test dependency and retain only required runtime packages.

---

### Task 1: Establish Offline Test Fixtures and Validated Outcomes

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_data_loader.py`
- Modify: `src/data_loader.py`
- Modify: `requirements.txt`

**Interfaces:**
- Produces: `validate_schema(df: pd.DataFrame, required_columns: Sequence[str]) -> None`
- Produces: `prepare_analysis_data(df: pd.DataFrame) -> pd.DataFrame`
- Preserves: `load_kiva_pickle(file_path: str) -> pd.DataFrame`
- Preserves: `load_and_prepare_data(file_path: str) -> pd.DataFrame`

- [ ] **Step 1: Add the test dependency and synthetic fixture**

Add `pytest>=8.0.0` to `requirements.txt`. Create a `synthetic_kiva_df` fixture in `tests/conftest.py` with at least eight rows spanning 2018, 2020, 2021, 2023, 2024, and 2025. Include all required raw columns, valid and missing `raisedDate` values, one negative duration, female/male/mixed/missing gender strings, and distinct narrative text.

```python
import pandas as pd
import pytest


@pytest.fixture
def synthetic_kiva_df():
    rows = []
    years = [2018, 2020, 2021, 2023, 2024, 2024, 2025, 2025]
    for idx, year in enumerate(years):
        posted = pd.Timestamp(year=year, month=1 + idx % 6, day=10, tz="UTC")
        rows.append({
            "id": idx + 1,
            "status": "funded",
            "borrowerCount": 2 if idx == 2 else 1,
            "name": f"Borrower {idx}",
            "gender": ["female", "male", "female, male", None][idx % 4],
            "loanAmount": 100.0 + 50 * idx,
            "lenderRepaymentTerm": 6 + idx,
            "repaymentInterval": ["monthly", "irregularly", "at_end"][idx % 3],
            "sector": ["Agriculture", "Retail"][idx % 2],
            "activity": "Farming",
            "use": "to buy seeds and tools",
            "city": "Test City",
            "latitude": 0.0,
            "longitude": 0.0,
            "country_iso": ["KE", "PH"][idx % 2],
            "country_name": ["Kenya", "Philippines"][idx % 2],
            "region": ["Africa", "Asia"][idx % 2],
            "country_ppp": 2000.0 + idx,
            "fundsLentInCountry": 100000 + idx,
            "country_latitude": 0.0,
            "country_longitude": 0.0,
            "description": f"She has operated her family business for {idx + 2} years and needs support.",
            "whySpecial": "It serves an underserved community.",
            "image_url": "https://example.test/image.webp",
            "disbursalDate": (posted - pd.Timedelta(days=7)).isoformat(),
            "fundraisingDate": posted.isoformat(),
            "raisedDate": (posted + pd.Timedelta(hours=12 + idx * 8)).isoformat(),
        })
    return pd.DataFrame(rows)
```

- [ ] **Step 2: Write failing target and schema tests**

```python
import numpy as np
import pandas as pd
import pytest

from src.data_loader import prepare_analysis_data, validate_schema


def test_prepare_analysis_data_creates_fractional_duration_and_binary_target(synthetic_kiva_df):
    result = prepare_analysis_data(synthetic_kiva_df)
    assert result.loc[0, "funding_speed_days"] == pytest.approx(0.5)
    assert result.loc[0, "funded_within_24h"] == 1
    assert result.loc[0, "log_funding_speed"] == pytest.approx(np.log1p(0.5))
    assert result.loc[0, "valid_completed_outcome"]


def test_prepare_analysis_data_flags_missing_and_negative_outcomes(synthetic_kiva_df):
    frame = synthetic_kiva_df.copy()
    frame.loc[0, "raisedDate"] = None
    frame.loc[1, "raisedDate"] = "2019-12-01T00:00:00Z"
    result = prepare_analysis_data(frame)
    assert not result.loc[0, "valid_completed_outcome"]
    assert pd.isna(result.loc[0, "funding_speed_days"])
    assert not result.loc[1, "valid_completed_outcome"]
    assert result.loc[1, "outcome_issue"] == "negative_duration"


def test_validate_schema_lists_missing_required_columns(synthetic_kiva_df):
    with pytest.raises(ValueError, match="raisedDate, use"):
        validate_schema(synthetic_kiva_df.drop(columns=["raisedDate", "use"]), ["use", "raisedDate"])
```

- [ ] **Step 3: Run tests and verify RED**

Run: `python3 -m pytest tests/test_data_loader.py -v`

Expected: collection fails because `prepare_analysis_data` and `validate_schema` do not exist.

- [ ] **Step 4: Implement schema validation and outcome preparation**

Implement constants for required outcome fields and these behaviors in `src/data_loader.py`:

```python
from collections.abc import Sequence


def validate_schema(df: pd.DataFrame, required_columns: Sequence[str]) -> None:
    missing = sorted(set(required_columns) - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def prepare_analysis_data(df: pd.DataFrame) -> pd.DataFrame:
    validate_schema(df, ["fundraisingDate", "raisedDate"])
    result = df.copy()
    for column in ["disbursalDate", "fundraisingDate", "raisedDate"]:
        if column in result:
            result[column] = pd.to_datetime(result[column], errors="coerce", utc=True)
    duration = (result["raisedDate"] - result["fundraisingDate"]).dt.total_seconds() / 86400
    result["funding_speed_days"] = duration.where(duration >= 0)
    result["valid_completed_outcome"] = duration.notna() & duration.ge(0)
    result["outcome_issue"] = np.select(
        [result["raisedDate"].isna(), result["fundraisingDate"].isna(), duration.lt(0)],
        ["missing_raised_date", "missing_fundraising_date", "negative_duration"],
        default="",
    )
    result["log_funding_speed"] = np.log1p(result["funding_speed_days"])
    result["funded_within_24h"] = result["funding_speed_days"].le(1).astype("Int64")
    result.loc[~result["valid_completed_outcome"], "funded_within_24h"] = pd.NA
    year = result["fundraisingDate"].dt.year
    result["fundraising_year"] = year.astype("Int64")
    result["fundraising_month"] = result["fundraisingDate"].dt.month.astype("Int64")
    result["analysis_period"] = pd.cut(
        year,
        bins=[2015, 2019, 2021, 2025],
        labels=["pre_pandemic", "pandemic_disruption", "post_pandemic"],
    )
    return result
```

Make `preprocess_dates_and_target` delegate to `prepare_analysis_data` for backward compatibility. Make `load_and_prepare_data` load, then call `prepare_analysis_data`.

- [ ] **Step 5: Run Task 1 tests and the full suite**

Run: `python3 -m pytest tests/test_data_loader.py -v`

Expected: all Task 1 tests pass.

Run: `python3 -m pytest -q`

Expected: all collected tests pass.

- [ ] **Step 6: Commit Task 1**

```bash
git add requirements.txt src/data_loader.py tests/conftest.py tests/test_data_loader.py
git commit -m "feat: validate Kiva outcomes and analysis periods"
```

---

### Task 2: Replace Unsupported Features With Deterministic Narrative and Borrower Measures

**Files:**
- Create: `tests/test_features.py`
- Modify: `src/features.py`

**Interfaces:**
- Produces: `classify_gender(value: object) -> str`
- Produces: `extract_deterministic_features(df: pd.DataFrame) -> pd.DataFrame`
- Preserves: `clean_html(text: object) -> str`
- Changes: `build_features(df)` becomes a backward-compatible alias for deterministic features only.

- [ ] **Step 1: Write failing gender and narrative tests**

```python
import pandas as pd
import pytest

from src.features import classify_gender, extract_deterministic_features


@pytest.mark.parametrize(("raw", "expected"), [
    ("female", "female"),
    ("male", "male"),
    ("female, male", "mixed"),
    (None, "unknown"),
    ("", "unknown"),
])
def test_classify_gender_does_not_assume_missing_is_female(raw, expected):
    assert classify_gender(raw) == expected


def test_narrative_counts_are_normalized_per_100_words(synthetic_kiva_df):
    frame = synthetic_kiva_df.iloc[[0]].copy()
    frame.loc[frame.index[0], "description"] = "family business needs support"
    result = extract_deterministic_features(frame)
    assert result.iloc[0]["family_mentions"] == 1
    assert result.iloc[0]["family_mentions_per_100_words"] == pytest.approx(25.0)


def test_deterministic_features_do_not_create_unverified_female_ratio(synthetic_kiva_df):
    result = extract_deterministic_features(synthetic_kiva_df)
    assert "female_ratio" not in result.columns
    assert set(result["gender_classification"]) == {"female", "male", "mixed", "unknown"}
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m pytest tests/test_features.py -v`

Expected: import fails because the new public functions do not exist.

- [ ] **Step 3: Implement deterministic feature extraction**

Refactor `src/features.py` so importing it performs no downloads and fitting across observations is absent. Implement:

```python
def classify_gender(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        return "unknown"
    tokens = {token.strip().lower() for token in value.split(",") if token.strip()}
    has_female = "female" in tokens
    has_male = "male" in tokens
    if has_female and has_male:
        return "mixed"
    if has_female:
        return "female"
    if has_male:
        return "male"
    return "unknown"


def _count_pattern(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def _per_100(counts: pd.Series, words: pd.Series) -> pd.Series:
    return np.where(words.gt(0), counts / words * 100, 0.0)
```

`extract_deterministic_features` must:

- Validate the required deterministic columns.
- Clean `description`, `use`, and `whySpecial`.
- Add missing-text flags, character/word/sentence counts, average word length, average sentence length, number-token count, age-pattern count, and years-in-business count.
- Add raw and per-100-word counts for family/beneficiary, basic needs, business investment, agency, gratitude, urgency, first person, and third person.
- Add VADER scores only when the lexicon is already installed; otherwise add neutral fallback values and `sentiment_available = 0` without network access.
- Add `gender_classification`, `is_group_loan`, `log_loan_amount`, and `loan_size_band` based on fixed transparent thresholds: `<= 250`, `251–750`, and `> 750`.
- Preserve raw categorical and time columns for downstream pipelines.
- Exclude `female_ratio`.

Keep `extract_text_features`, `extract_borrower_features`, and `extract_financial_and_geography_features` as compatibility wrappers that call focused deterministic helpers. Make `build_features` call only deterministic helpers; remove NMF fitting from it.

- [ ] **Step 4: Run feature tests and full suite**

Run: `python3 -m pytest tests/test_features.py -v`

Expected: all Task 2 tests pass.

Run: `python3 -m pytest -q`

Expected: all tests pass with no NLTK download output.

- [ ] **Step 5: Commit Task 2**

```bash
git add src/features.py tests/test_features.py
git commit -m "feat: add ethical deterministic narrative features"
```

---

### Task 3: Add a Training-Fitted Text Topic Transformer

**Files:**
- Create: `src/text_transformer.py`
- Create: `tests/test_text_transformer.py`
- Modify: `src/topics.py`

**Interfaces:**
- Produces: `KivaTopicTransformer(n_topics: int = 5, min_df: int = 2, random_state: int = 42)`
- Produces methods: `fit(X, y=None)`, `transform(X) -> pd.DataFrame`, `get_feature_names_out()`, `get_topic_terms(n_top_words=10)`
- `X` accepts a `pd.Series`, a one-column `pd.DataFrame`, or an iterable of strings.

- [ ] **Step 1: Write failing leakage and output-shape tests**

```python
import pandas as pd

from src.text_transformer import KivaTopicTransformer


def test_topic_transformer_does_not_learn_holdout_vocabulary():
    train = pd.Series([
        "farmer buys seeds for harvest",
        "farmer needs seeds and tools",
        "retailer buys stock for shop",
        "retailer expands local shop stock",
    ])
    holdout = pd.Series(["futureonlytoken appears nowhere else"])
    transformer = KivaTopicTransformer(n_topics=2, min_df=1, random_state=42)
    transformer.fit(train)
    assert "futureonlytoken" not in transformer.vectorizer_.vocabulary_
    transformed = transformer.transform(holdout)
    assert list(transformed.columns) == ["topic_0", "topic_1"]
    assert transformed.shape == (1, 2)


def test_topic_transformer_preserves_input_index():
    text = pd.Series(["seed farm", "shop stock"], index=[10, 20])
    transformer = KivaTopicTransformer(n_topics=2, min_df=1).fit(text)
    assert transformer.transform(text).index.tolist() == [10, 20]
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m pytest tests/test_text_transformer.py -v`

Expected: import fails because `src.text_transformer` does not exist.

- [ ] **Step 3: Implement the scikit-learn-compatible transformer**

Use `BaseEstimator` and `TransformerMixin`. Convert input to cleaned strings, fit `TfidfVectorizer` and then NMF. Reject `n_topics < 1`, empty training corpora, and topic counts greater than the TF-IDF matrix dimensions with clear `ValueError` messages. Store fitted attributes with trailing underscores.

```python
class KivaTopicTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, n_topics=5, min_df=2, random_state=42):
        self.n_topics = n_topics
        self.min_df = min_df
        self.random_state = random_state

    def fit(self, X, y=None):
        text, _ = self._coerce_text(X)
        self.vectorizer_ = TfidfVectorizer(
            max_df=0.95, min_df=self.min_df, stop_words="english", ngram_range=(1, 2)
        )
        matrix = self.vectorizer_.fit_transform(text)
        if self.n_topics > min(matrix.shape):
            raise ValueError("n_topics exceeds the fitted text matrix dimensions")
        self.nmf_ = NMF(
            n_components=self.n_topics, random_state=self.random_state,
            init="nndsvda", max_iter=1000,
        ).fit(matrix)
        return self

    def transform(self, X):
        check_is_fitted(self, ["vectorizer_", "nmf_"])
        text, index = self._coerce_text(X)
        weights = self.nmf_.transform(self.vectorizer_.transform(text))
        totals = weights.sum(axis=1, keepdims=True)
        probabilities = np.divide(weights, totals, out=np.zeros_like(weights), where=totals != 0)
        return pd.DataFrame(probabilities, index=index, columns=self.get_feature_names_out())
```

Update `src/topics.py` to use this transformer and clearly label its convenience function as full-sample exploratory analysis, not evaluation code.

- [ ] **Step 4: Run transformer tests and full suite**

Run: `python3 -m pytest tests/test_text_transformer.py -v`

Expected: all Task 3 tests pass.

Run: `python3 -m pytest -q`

Expected: all tests pass.

- [ ] **Step 5: Commit Task 3**

```bash
git add src/text_transformer.py src/topics.py tests/test_text_transformer.py
git commit -m "feat: fit text topics on training data only"
```

---

### Task 4: Introduce Chronological Splits and Leakage-Safe Prediction

**Files:**
- Create: `src/validation.py`
- Create: `tests/test_validation.py`
- Create: `tests/test_modeling.py`
- Modify: `src/modeling.py`

**Interfaces:**
- Produces: `chronological_holdout(df, date_col="fundraisingDate", holdout_start="2024-01-01") -> tuple[pd.DataFrame, pd.DataFrame]`
- Produces: `build_predictor_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]`
- Produces: `prepare_chronological_matrices(df: pd.DataFrame, holdout_start="2024-01-01", n_topics=5) -> dict`
- Produces: `evaluate_chronological_models(df: pd.DataFrame, holdout_start="2024-01-01", n_topics=5) -> dict`

- [ ] **Step 1: Write failing chronological split tests**

```python
import pandas as pd
import pytest

from src.validation import chronological_holdout


def test_chronological_holdout_separates_earlier_and_later_rows(synthetic_kiva_df):
    train, holdout = chronological_holdout(synthetic_kiva_df, holdout_start="2024-01-01")
    assert pd.to_datetime(train["fundraisingDate"], utc=True).max() < pd.Timestamp("2024-01-01", tz="UTC")
    assert pd.to_datetime(holdout["fundraisingDate"], utc=True).min() >= pd.Timestamp("2024-01-01", tz="UTC")


def test_chronological_holdout_rejects_empty_side(synthetic_kiva_df):
    with pytest.raises(ValueError, match="empty training or holdout partition"):
        chronological_holdout(synthetic_kiva_df, holdout_start="2010-01-01")
```

- [ ] **Step 2: Write failing modeling safety test**

```python
from src.data_loader import prepare_analysis_data
from src.modeling import build_predictor_frame


def test_predictor_frame_excludes_outcomes_and_post_outcome_fields(synthetic_kiva_df):
    prepared = prepare_analysis_data(synthetic_kiva_df)
    predictors, numeric, categorical = build_predictor_frame(prepared)
    forbidden = {
        "id", "name", "status", "raisedDate", "funding_speed_days",
        "log_funding_speed", "funded_within_24h", "valid_completed_outcome",
        "outcome_issue", "fundsLentInCountry", "image_url",
    }
    assert forbidden.isdisjoint(predictors.columns)
    assert set(numeric + categorical).issubset(predictors.columns)
```

- [ ] **Step 3: Run tests and verify RED**

Run: `python3 -m pytest tests/test_validation.py tests/test_modeling.py -v`

Expected: imports fail because the chronological API and predictor builder do not exist.

- [ ] **Step 4: Implement chronological splitting**

In `src/validation.py`, parse dates with `utc=True`, reject missing dates, sort each partition, and reject empty sides. Add an assertion that `max(train_date) < min(holdout_date)`.

- [ ] **Step 5: Implement predictor selection and evaluation**

In `src/modeling.py`:

- Call `prepare_analysis_data`, retain only valid completed outcomes, and split before fitting features.
- Apply deterministic features separately without learning across rows.
- Define an explicit predictor allowlist rather than selecting every numeric column.
- Use a `ColumnTransformer` for median numeric imputation, standard scaling, most-frequent categorical imputation, and one-hot encoding with `handle_unknown="ignore"`.
- Fit one `KivaTopicTransformer` to training descriptions and append transformed topic columns to training and holdout deterministic features.
- Put the fitted preprocessing objects, transformed training/holdout matrices, untransformed split frames, targets, and feature names in the dictionary returned by `prepare_chronological_matrices`. Both linear and nonlinear evaluators must consume this shared function so they use identical splits and transformations.
- Compare training-median prediction and `Ridge(alpha=1.0)` on `log_funding_speed`; convert predictions back to days with `np.expm1` before calculating MAE and median absolute error.
- Return a serializable dictionary containing row counts, split boundaries, metrics, feature names, and fitted objects under a private `_artifacts` key that report writers omit from JSON.
- Raise a diagnostic if fewer than five valid observations exist on either split.

Retain `run_baseline_model` as a wrapper that prints the new chronological results and returns fitted artifacts for notebook compatibility.

- [ ] **Step 6: Add a smoke evaluation test**

Extend `tests/test_modeling.py` with a fixture containing at least twelve pre-2024 and six 2024–2025 observations and distinct train/holdout tokens. Assert finite baseline and Ridge MAE, correct row counts, and absence of the holdout-only token from the fitted topic vocabulary.

- [ ] **Step 7: Run Task 4 tests and full suite**

Run: `python3 -m pytest tests/test_validation.py tests/test_modeling.py -v`

Expected: all Task 4 tests pass.

Run: `python3 -m pytest -q`

Expected: all tests pass.

- [ ] **Step 8: Commit Task 4**

```bash
git add src/validation.py src/modeling.py tests/test_validation.py tests/test_modeling.py
git commit -m "feat: add leakage-safe chronological evaluation"
```

---

### Task 5: Add Robust Explanatory Duration and 24-Hour Models

**Files:**
- Create: `tests/test_statistical_analysis.py`
- Modify: `src/statistical_analysis.py`

**Interfaces:**
- Produces: `fit_explanatory_models(df: pd.DataFrame) -> dict[str, object]`
- Produces: `format_association_summary(results: dict[str, object]) -> str`
- Preserves: `run_ols_analysis(pkl_path: str, report_dir: str)` as a compatibility wrapper.

- [ ] **Step 1: Write failing statistical-model tests**

```python
from src.statistical_analysis import fit_explanatory_models, format_association_summary


def test_explanatory_models_use_valid_rows_and_robust_covariance(large_synthetic_kiva_df):
    result = fit_explanatory_models(large_synthetic_kiva_df)
    assert result["duration"].cov_type == "HC3"
    assert result["n_duration"] == len(large_synthetic_kiva_df)
    assert result["n_binary"] == len(large_synthetic_kiva_df)


def test_summary_uses_association_not_effect_language(large_synthetic_kiva_df):
    summary = format_association_summary(fit_explanatory_models(large_synthetic_kiva_df))
    assert "associated with" in summary
    assert "causes" not in summary.lower()
    assert "has a significant effect" not in summary.lower()
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m pytest tests/test_statistical_analysis.py -v`

Expected: imports fail because the new statistical interfaces do not exist.

- [ ] **Step 3: Implement pre-specified robust models**

Prepare valid completed outcomes and deterministic features. Use a compact, explicit formula containing:

- `log_loan_amount`
- `lenderRepaymentTerm`
- `is_group_loan`
- `C(gender_classification)`
- `desc_word_count`
- selected normalized framing measures
- sentiment compound score and availability indicator
- `C(repaymentInterval)`
- `C(sector)`
- `C(region)`
- `C(analysis_period)`

Fit OLS to `log_funding_speed` with `cov_type="HC3"`. Fit a binomial GLM to `funded_within_24h` with HC3 covariance. Add only pre-specified period interactions in the default sample model; expose a parameter for additional segment interaction formulas on the full dataset.

Detect rank-deficient or too-small designs and raise a message showing observations and design columns. Format coefficients as associations with 95% confidence intervals. Do not select variables solely by `p < 0.05`.

- [ ] **Step 4: Run Task 5 tests and full suite**

Run: `python3 -m pytest tests/test_statistical_analysis.py -v`

Expected: all Task 5 tests pass.

Run: `python3 -m pytest -q`

Expected: all tests pass.

- [ ] **Step 5: Commit Task 5**

```bash
git add src/statistical_analysis.py tests/test_statistical_analysis.py tests/conftest.py
git commit -m "feat: add robust explanatory funding models"
```

---

### Task 6: Consolidate the Nonlinear Benchmark

**Files:**
- Modify: `src/advanced_modeling.py`
- Create: `tests/test_advanced_modeling.py`

**Interfaces:**
- Produces: `evaluate_boosted_model(df: pd.DataFrame, holdout_start="2024-01-01", n_topics=5, random_state=42) -> dict`
- Consumes: `prepare_chronological_matrices(df, holdout_start, n_topics) -> dict` from `src/modeling.py`.

- [ ] **Step 1: Write the failing boosted benchmark test**

```python
import numpy as np

from src.advanced_modeling import evaluate_boosted_model


def test_boosted_model_returns_holdout_metrics_and_importance(large_synthetic_kiva_df):
    result = evaluate_boosted_model(
        large_synthetic_kiva_df,
        holdout_start="2024-01-01",
        n_topics=2,
        random_state=42,
    )
    assert np.isfinite(result["metrics"]["mae_days"])
    assert result["importance"].shape[1] == 2
    assert set(result["importance"].columns) == {"feature", "permutation_importance"}
```

- [ ] **Step 2: Run the test and verify RED**

Run: `python3 -m pytest tests/test_advanced_modeling.py -v`

Expected: import fails because the new benchmark interface does not exist.

- [ ] **Step 3: Implement one nonlinear benchmark**

Use `sklearn.ensemble.HistGradientBoostingRegressor` to avoid redundant XGBoost and LightGBM dependencies. Fit only on transformed training data, predict the untouched chronological holdout, convert log predictions to days, and calculate MAE, median absolute error, RMSE, and R-squared. Calculate permutation importance on the holdout with a fixed random seed and MAE scoring.

Remove full-dataset fitting and random K-fold evaluation from the primary function. Keep `run_advanced_cv_modeling` as a deprecated wrapper that directs callers to the chronological benchmark.

- [ ] **Step 4: Run Task 6 tests and full suite**

Run: `python3 -m pytest tests/test_advanced_modeling.py -v`

Expected: all Task 6 tests pass.

Run: `python3 -m pytest -q`

Expected: all tests pass.

- [ ] **Step 5: Remove redundant dependencies and commit**

Remove `xgboost` and `lightgbm` from `requirements.txt` after confirming no active imports remain:

Run: `rg -n 'xgboost|lightgbm|import xgb|import lgb' src tests`

Expected: no active matches outside migration comments.

```bash
git add src/advanced_modeling.py tests/test_advanced_modeling.py tests/conftest.py requirements.txt
git commit -m "feat: use one chronological nonlinear benchmark"
```

---

### Task 7: Add Reproducible CLI and Generated Reports

**Files:**
- Create: `src/run_analysis.py`
- Create: `tests/test_run_analysis.py`
- Modify: `reports/statistical_summary.txt`

**Interfaces:**
- Produces: `run_analysis(data_path: Path, output_dir: Path, holdout_start: str = "2024-01-01") -> dict`
- CLI: `python3 -m src.run_analysis --data data/Kiva_Loans_Sample.pkl --output-dir reports/generated`

- [ ] **Step 1: Write failing end-to-end report test**

```python
import json
import pickle

from src.run_analysis import run_analysis


def test_run_analysis_writes_auditable_reports(tmp_path, large_synthetic_kiva_df):
    data_path = tmp_path / "sample.pkl"
    with data_path.open("wb") as handle:
        pickle.dump(large_synthetic_kiva_df.to_dict("records"), handle)
    output_dir = tmp_path / "reports"
    summary = run_analysis(data_path, output_dir, holdout_start="2024-01-01")
    assert (output_dir / "analysis_summary.json").exists()
    assert (output_dir / "association_summary.txt").exists()
    saved = json.loads((output_dir / "analysis_summary.json").read_text())
    assert saved["data"]["n_rows"] == len(large_synthetic_kiva_df)
    assert saved["data"]["holdout_start"] == "2024-01-01"
    assert "_artifacts" not in saved
    assert summary["data"]["date_min"] <= summary["data"]["date_max"]
```

- [ ] **Step 2: Run the test and verify RED**

Run: `python3 -m pytest tests/test_run_analysis.py -v`

Expected: import fails because `src.run_analysis` does not exist.

- [ ] **Step 3: Implement CLI orchestration**

The CLI must:

- Resolve user-supplied paths without assuming the current working directory.
- Load and validate data.
- Record row count, valid outcome count, exclusion reasons, date range, period counts, and 24-hour share.
- Run chronological baseline and Ridge evaluation.
- Run robust explanatory models.
- Attempt the nonlinear benchmark, recording a clear diagnostic if the sample is too small.
- Strip fitted objects before JSON serialization.
- Write `analysis_summary.json` and `association_summary.txt` atomically into the requested output directory.
- Record Python, pandas, NumPy, scikit-learn, and statsmodels versions.

Use `argparse` with explicit `--data`, `--output-dir`, and `--holdout-start` arguments.

- [ ] **Step 4: Run Task 7 tests and the sample command**

Run: `python3 -m pytest tests/test_run_analysis.py -v`

Expected: all Task 7 tests pass.

Run: `python3 -m src.run_analysis --data data/Kiva_Loans_Sample.pkl --output-dir reports/generated`

Expected: command exits zero and writes both reports. If the 100-row sample is insufficient for a secondary model, the report contains the diagnostic and still completes core analysis.

- [ ] **Step 5: Replace the stale report and commit**

Replace `reports/statistical_summary.txt` with a short notice that the historical raw-OLS output is superseded, linking readers to `reports/generated/association_summary.txt`. Keep generated JSON ignored unless the team wants to version a specific competition snapshot.

```bash
git add src/run_analysis.py tests/test_run_analysis.py tests/conftest.py reports/statistical_summary.txt
git commit -m "feat: add reproducible analysis reporting"
```

---

### Task 8: Refocus the Notebook on Auditable Evidence

**Files:**
- Modify: `notebooks/starter_eda.py`
- Modify: `notebooks/starter_eda.ipynb`
- Create: `tests/test_notebook_contract.py`

**Interfaces:**
- Notebook/script imports shared functions from `src` and resolves the project root from the notebook or script location.

- [ ] **Step 1: Write a failing notebook contract test**

```python
from pathlib import Path


def test_notebook_script_has_portable_paths_and_no_duplicated_legacy_modeling():
    text = Path("notebooks/starter_eda.py").read_text(encoding="utf-8")
    assert "F:/" not in text
    assert 'pkl_path = "../data/' not in text
    assert "train_test_split" not in text
    assert "run_analysis" in text
    assert "analysis_period" in text
```

- [ ] **Step 2: Run the test and verify RED**

Run: `python3 -m pytest tests/test_notebook_contract.py -v`

Expected: assertions fail because the notebook script uses working-directory-relative paths and legacy modeling calls.

- [ ] **Step 3: Rewrite the notebook script as a thin consumer**

Use `Path(__file__).resolve().parents[1]` for script execution and a safe notebook fallback based on `Path.cwd()`. Include sections for:

1. Research question and association caveat.
2. Data validity and outcome distribution.
3. Funding behavior by period.
4. Controllable narrative versus structural predictors.
5. Pre-specified period and segment comparisons.
6. Chronological evaluation results.
7. Robust explanatory associations.
8. Ethical managerial interpretation and limitations.

Call shared source functions for preparation, features, evaluation, and reporting. Keep plots descriptive and label the 100-row file as a sample rather than final evidence.

- [ ] **Step 4: Synchronize and execute the notebook**

Regenerate `starter_eda.ipynb` from the percent-format script using Jupytext if available. If Jupytext is not installed, update the notebook cells with a small repository-owned conversion script added and tested within this task; do not hand-edit notebook JSON.

Run the notebook from the repository root with a noninteractive backend:

`MPLBACKEND=Agg jupyter nbconvert --to notebook --execute notebooks/starter_eda.ipynb --output starter_eda.executed.ipynb --output-dir /tmp`

Expected: execution succeeds with no traceback and all paths resolve.

- [ ] **Step 5: Run tests and commit Task 8**

Run: `python3 -m pytest tests/test_notebook_contract.py -v`

Expected: all Task 8 tests pass.

Run: `python3 -m pytest -q`

Expected: all tests pass.

```bash
git add notebooks/starter_eda.py notebooks/starter_eda.ipynb tests/test_notebook_contract.py
git commit -m "docs: refocus notebook on temporal funding evidence"
```

---

### Task 9: Draft the Organizer-Aligned Proposal

**Files:**
- Create: `proposal/proposal.md`
- Create: `tests/test_proposal.py`

**Interfaces:**
- Proposal contains exactly the required substantive sections and placeholders only for team identity fields.

- [ ] **Step 1: Write failing structure and word-limit tests**

```python
import re
from pathlib import Path


def _proposal_text():
    return Path("proposal/proposal.md").read_text(encoding="utf-8")


def test_proposal_contains_required_sections():
    text = _proposal_text()
    for heading in [
        "# Beyond a Good Story",
        "## Project Aim and Research Questions",
        "## Proposed Analytical Approaches",
        "## Data Items to Be Used",
        "## Expected Outcomes and Managerial Relevance",
        "## References",
    ]:
        assert heading in text


def test_proposal_is_within_1500_words_excluding_references():
    body = _proposal_text().split("## References", 1)[0]
    words = re.findall(r"\b[\w’'-]+\b", body)
    assert len(words) <= 1500


def test_proposal_does_not_make_causal_or_completed_analysis_claims():
    body = _proposal_text().lower()
    assert "will cause" not in body
    assert "proves that" not in body
    assert "our results show" not in body
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `python3 -m pytest tests/test_proposal.py -v`

Expected: file-not-found failures because the proposal does not exist.

- [ ] **Step 3: Write the proposal draft**

Write 1,250–1,400 words excluding references. Follow this allocation:

- Title, names, affiliations: 40 words.
- Aim and four research questions: 220–260 words.
- Analytical approaches: 550–650 words.
- Data items: 180–220 words.
- Expected outcomes and managerial relevance: 280–330 words.

Explicitly state:

- The outcome is loan-level funding duration, not individual lender choice.
- The primary distinction is controllable narrative levers versus structural constraints.
- Temporal periods and segment interactions are pre-specified.
- All learned text transformations fit on training data only.
- Chronological holdout is the primary validation.
- Estimates are associations, not causal effects.
- Recommendations include ethical safeguards against emotional exploitation.
- The complete plan is feasible in one week.

Use `[Team member names]` and `[University affiliations]` as the only unresolved placeholders.

- [ ] **Step 4: Run proposal tests and inspect the word count**

Run: `python3 -m pytest tests/test_proposal.py -v`

Expected: all proposal tests pass.

Run:

```bash
python3 -c 'import re, pathlib; t=pathlib.Path("proposal/proposal.md").read_text().split("## References",1)[0]; print(len(re.findall(r"\b[\w’\x27-]+\b", t)))'
```

Expected: an integer between 1,250 and 1,500.

- [ ] **Step 5: Request the only required manual content**

Ask the user for exact team-member names and university affiliations. Replace only the two placeholders after receiving them; do not alter analytical content without a separate review request.

- [ ] **Step 6: Commit Task 9**

```bash
git add proposal/proposal.md tests/test_proposal.py
git commit -m "docs: draft hackathon proposal"
```

---

### Task 10: Update Repository Documentation and Perform Final Verification

**Files:**
- Modify: `README.md`
- Modify: `data/README.md`
- Modify: `.gitignore`

**Interfaces:**
- README documents a single root-level setup and analysis workflow.

- [ ] **Step 1: Write a failing README contract test**

Add to `tests/test_notebook_contract.py`:

```python
def test_readme_documents_current_portable_workflow():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "python3 -m src.run_analysis" in text
    assert "chronological" in text.lower()
    assert "association" in text.lower()
    assert "F:/" not in text
    assert "file:///" not in text
    for module in ["text_transformer.py", "validation.py", "run_analysis.py"]:
        assert module in text
```

- [ ] **Step 2: Run the test and verify RED**

Run: `python3 -m pytest tests/test_notebook_contract.py::test_readme_documents_current_portable_workflow -v`

Expected: failure because the README contains Windows file links and does not document the new workflow.

- [ ] **Step 3: Rewrite the README**

Include:

- Deadline and proposal constraints.
- Central research question and four supporting questions.
- Clear statement that analysis is associational and loan-level.
- Actual repository tree.
- Python environment setup and `pip install -r requirements.txt`.
- `python3 -m pytest -q` verification command.
- Root-level analysis and notebook commands.
- Chronological validation and text-leakage protections.
- Data field groups and excluded/leakage-sensitive fields.
- One-week schedule with daily deliverables.
- Proposal location and manual identity placeholder instructions.
- Known limitation that the sample has 100 funded loans and is not final evidence.

Update `data/README.md` with exact expected filenames and raw-data immutability. Update `.gitignore` to ignore generated reports and executed notebook copies while retaining source proposal and curated report files.

- [ ] **Step 4: Run all automated verification**

Run: `python3 -m pytest -q`

Expected: all tests pass with no warnings caused by project code.

Run: `python3 -m src.run_analysis --data data/Kiva_Loans_Sample.pkl --output-dir reports/generated`

Expected: exit code zero and auditable outputs.

Run: `python3 -m compileall -q src tests`

Expected: exit code zero.

Run: `git diff --check`

Expected: no whitespace errors.

- [ ] **Step 5: Inspect final project state**

Run:

```bash
git status --short
git diff --stat HEAD
rg -n 'F:/|file:///|has a significant effect|Default to female|nltk\.download' README.md src notebooks proposal tests
```

Expected: only intentional changes; prohibited patterns absent except where a test explicitly asserts their absence.

- [ ] **Step 6: Use verification-before-completion and request code review**

Invoke `superpowers:verification-before-completion`, rerun its required fresh checks, then invoke `superpowers:requesting-code-review`. Address any correctness findings with a new failing test before changing production code.

- [ ] **Step 7: Commit final documentation**

```bash
git add README.md data/README.md .gitignore
git commit -m "docs: document submission-ready analysis workflow"
```

- [ ] **Step 8: Present integration options**

Invoke `superpowers:finishing-a-development-branch` only after all tests and reviews pass. Report the final proposal word count, verification commands, generated output paths, remaining identity placeholders, and any full-dataset limitations requiring manual team judgment.
