import math
import warnings

import numpy as np
import pandas as pd
import pytest

from src.data_loader import prepare_analysis_data
from src.modeling import (
    _check_ridge_well_identified,
    build_predictor_frame,
    evaluate_chronological_models,
    log_predictions_to_days,
)
from src.validation import InsufficientDataError


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


# --- Step 6: smoke test fixture -------------------------------------------
#
# Needs >=12 pre-2024 rows and >=6 2024-2025 rows, with description text
# that is lexically distinct between the two splits so we can assert the
# holdout-only token never leaks into the topic vocabulary fitted on train.

TRAIN_DESCRIPTIONS = [
    "She uses the loan to buy seeds and fertilizer for her farm.",
    "He invests in seeds and tools to expand his farm business.",
    "She purchases stock and supplies for her small retail shop.",
    "He restocks his shop with new supplies and tools for customers.",
    "She raises chickens and buys feed to grow her poultry farm.",
    "He raises goats and buys feed to expand his livestock business.",
    "She sells vegetables and buys seeds for her market stall.",
    "He sells tools and buys stock for his hardware shop.",
    "She bakes bread and buys flour and supplies for her bakery.",
    "He repairs bicycles and buys spare parts and tools for his shop.",
    "She weaves baskets and buys materials and supplies for her craft business.",
    "He tailors clothes and buys fabric and thread for his tailoring shop.",
]

HOLDOUT_DESCRIPTIONS = [
    "She started a futureonlytoken venture selling handmade soap.",
    "He launched a futureonlytoken project repairing solar panels.",
    "She opened a futureonlytoken stall selling fresh juice.",
    "He began a futureonlytoken workshop building furniture.",
    "She created a futureonlytoken studio selling pottery.",
    "He founded a futureonlytoken garage fixing motorbikes.",
]

TRAIN_YEARS = [2018, 2019, 2019, 2020, 2020, 2021, 2021, 2022, 2022, 2023, 2023, 2023]
HOLDOUT_YEARS = [2024, 2024, 2024, 2025, 2025, 2025]


@pytest.fixture
def chronological_kiva_df():
    rows = []
    all_descriptions = TRAIN_DESCRIPTIONS + HOLDOUT_DESCRIPTIONS
    all_years = TRAIN_YEARS + HOLDOUT_YEARS
    for idx, (year, description) in enumerate(zip(all_years, all_descriptions)):
        posted = pd.Timestamp(year=year, month=1 + idx % 6, day=10, tz="UTC")
        rows.append({
            "id": idx + 1,
            "status": "funded",
            "borrowerCount": 2 if idx % 5 == 0 else 1,
            "name": f"Borrower {idx}",
            "gender": ["female", "male", "female, male", None][idx % 4],
            "loanAmount": 100.0 + 25 * idx,
            "lenderRepaymentTerm": 6 + idx % 12,
            "repaymentInterval": ["monthly", "irregularly", "at_end"][idx % 3],
            "sector": ["Agriculture", "Retail", "Food"][idx % 3],
            "activity": ["Farming", "Retail", "Food Production"][idx % 3],
            "use": "to buy materials and tools",
            "city": "Test City",
            "latitude": 0.0,
            "longitude": 0.0,
            "country_iso": ["KE", "PH", "UG"][idx % 3],
            "country_name": ["Kenya", "Philippines", "Uganda"][idx % 3],
            "region": ["Africa", "Asia"][idx % 2],
            "country_ppp": 2000.0 + idx,
            "fundsLentInCountry": 100000 + idx,
            "country_latitude": 0.0,
            "country_longitude": 0.0,
            "description": description,
            "whySpecial": "It serves an underserved community.",
            "image_url": "https://example.test/image.webp",
            "disbursalDate": (posted - pd.Timedelta(days=7)).isoformat(),
            "fundraisingDate": posted.isoformat(),
            "raisedDate": (posted + pd.Timedelta(hours=12 + idx * 6)).isoformat(),
        })
    return pd.DataFrame(rows)


def test_evaluate_chronological_models_is_leakage_safe_and_finite(chronological_kiva_df):
    results = evaluate_chronological_models(chronological_kiva_df, holdout_start="2024-01-01", n_topics=2)

    assert results["train_rows"] == len(TRAIN_DESCRIPTIONS)
    assert results["holdout_rows"] == len(HOLDOUT_DESCRIPTIONS)

    baseline = results["metrics"]["baseline"]
    ridge = results["metrics"]["ridge"]
    metric_keys = (
        "train_mae_days", "holdout_mae_days",
        "train_medae_days", "holdout_medae_days",
        "train_r2", "holdout_r2",
    )
    for metrics in (baseline, ridge):
        for key in metric_keys:
            assert math.isfinite(metrics[key])

    topic_transformer = results["_artifacts"]["topic_transformer"]
    assert "futureonlytoken" not in topic_transformer.vectorizer_.vocabulary_


def test_log_predictions_to_days_clips_negative_log_predictions_to_zero():
    log_predictions = np.array([-1.0, 0.0, np.log1p(5.0)])
    days = log_predictions_to_days(log_predictions)
    assert days[0] == pytest.approx(0.0)
    assert days[1] == pytest.approx(0.0)
    assert days[2] == pytest.approx(5.0)


def test_ridge_predictions_never_convert_to_negative_days(chronological_kiva_df):
    results = evaluate_chronological_models(chronological_kiva_df, holdout_start="2024-01-01", n_topics=2)
    ridge = results["_artifacts"]["ridge_model"]
    X_train = results["_artifacts"]["X_train"]
    X_holdout = results["_artifacts"]["X_holdout"]
    train_days = log_predictions_to_days(ridge.predict(X_train))
    holdout_days = log_predictions_to_days(ridge.predict(X_holdout))
    assert (train_days >= 0).all()
    assert (holdout_days >= 0).all()


def test_ridge_and_log_conversion_stay_finite_on_a_sample_that_triggers_overfit_warnings(
    large_synthetic_kiva_df,
):
    # `large_synthetic_kiva_df` (120 rows, default 2024-01-01 holdout split
    # -> ~88 training rows against many one-hot/topic-encoded columns)
    # reliably reproduces the benign divide-by-zero/overflow/invalid-value
    # RuntimeWarning that a near-rank-deficient design can trigger inside
    # both `Ridge.fit()`'s internal SVD solver and `Ridge.predict()`'s
    # `X @ coef_ + intercept_` (see the `warnings.catch_warnings` block
    # around the Ridge fit/predict calls in `evaluate_chronological_models`)
    # - confirmed here with real numbers that the fitted coefficients, raw
    # predictions, and the day-space conversion all remain finite
    # regardless of that warning firing. This mirrors the finiteness
    # verified directly against the real `data/Kiva_Loans_Sample.pkl` (see
    # the report).
    results = evaluate_chronological_models(large_synthetic_kiva_df, holdout_start="2024-01-01", n_topics=5)
    ridge = results["_artifacts"]["ridge_model"]
    X_train = results["_artifacts"]["X_train"]
    X_holdout = results["_artifacts"]["X_holdout"]

    assert np.isfinite(ridge.coef_).all()

    # Re-predicting here (outside evaluate_chronological_models's own
    # scoped `warnings.catch_warnings` block) intentionally reproduces the
    # same known, already-diagnosed RuntimeWarning to directly assert
    # finiteness on the raw predictions - suppressed the same way and for
    # the same documented reason as the production call site, not an
    # unexplained leak.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        raw_train_pred = ridge.predict(X_train)
        raw_holdout_pred = ridge.predict(X_holdout)
    assert np.isfinite(raw_train_pred).all()
    assert np.isfinite(raw_holdout_pred).all()
    assert np.isfinite(log_predictions_to_days(raw_train_pred)).all()
    assert np.isfinite(log_predictions_to_days(raw_holdout_pred)).all()

    for metrics in results["metrics"].values():
        for value in metrics.values():
            assert math.isfinite(value)


def test_evaluate_chronological_models_raises_when_ridge_predictions_convert_to_infinity(
    chronological_kiva_df, monkeypatch,
):
    # `_check_ridge_well_identified` must run on the *day-space*
    # predictions (after `log_predictions_to_days`'s `np.expm1`), not just
    # the raw log-space `ridge.predict()` output: a finite log-space value
    # (e.g. 1000.0) converts to `inf` in day-space with no warning
    # surfaced. Force exactly that by making `Ridge.predict()` return a
    # constant, finite-but-extreme value, and confirm the pipeline raises
    # a clear diagnostic instead of silently returning `inf` metrics.
    from src.modeling import Ridge

    def _extreme_predict(self, X):
        return np.full(X.shape[0], 1000.0)

    monkeypatch.setattr(Ridge, "predict", _extreme_predict)

    with pytest.raises(InsufficientDataError, match="non-finite"):
        evaluate_chronological_models(chronological_kiva_df, holdout_start="2024-01-01", n_topics=2)


def test_check_ridge_well_identified_passes_through_finite_coefficients_and_predictions():
    coefficients = np.array([0.1, -0.2, 0.3])
    train_pred = np.array([0.5, 0.6])
    holdout_pred = np.array([0.4])
    # Should not raise.
    _check_ridge_well_identified(coefficients, train_pred, holdout_pred, n_obs=2, n_cols=3)


@pytest.mark.parametrize(
    "coefficients,train_pred,holdout_pred",
    [
        (np.array([0.1, np.nan]), np.array([0.5]), np.array([0.4])),
        (np.array([0.1, 0.2]), np.array([np.inf]), np.array([0.4])),
        (np.array([0.1, 0.2]), np.array([0.5]), np.array([-np.inf])),
    ],
)
def test_check_ridge_well_identified_raises_insufficient_data_error_on_non_finite_values(
    coefficients, train_pred, holdout_pred,
):
    # Mirrors `_check_well_identified`'s non-finite-standard-error check in
    # src/statistical_analysis.py: if Ridge's near-rank-deficient design
    # ever produces genuinely non-finite output (rather than the benign,
    # still-finite RuntimeWarning case verified above), this must surface
    # as a clear diagnostic instead of a silently-NaN metric.
    with pytest.raises(InsufficientDataError, match="non-finite"):
        _check_ridge_well_identified(coefficients, train_pred, holdout_pred, n_obs=2, n_cols=2)
