import numpy as np
import pytest

from src.advanced_modeling import evaluate_boosted_model
from src.validation import InsufficientDataError


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


def test_permutation_importance_is_scored_in_day_space_not_log_space(large_synthetic_kiva_df):
    # Every other metric this function reports (mae_days, medae_days,
    # rmse_days, r2) is in day space. Permutation importance must use the
    # same evaluation frame, not the model's internal log-space target -
    # log_predictions_to_days is a convex transform, so scoring in log
    # space can change which features rank as most important, not merely
    # rescale the numbers.
    from sklearn.inspection import permutation_importance
    from sklearn.metrics import mean_absolute_error

    from src.modeling import log_predictions_to_days

    result = evaluate_boosted_model(
        large_synthetic_kiva_df,
        holdout_start="2024-01-01",
        n_topics=2,
        random_state=42,
    )
    model = result["_artifacts"]["boosted_model"]
    X_holdout = result["_artifacts"]["X_holdout"]
    y_holdout_days = result["_artifacts"]["y_holdout_days"]
    y_holdout_log = result["_artifacts"]["y_holdout"]

    def day_space_neg_mae(estimator, X, y_days):
        return -mean_absolute_error(y_days, log_predictions_to_days(estimator.predict(X)))

    expected = permutation_importance(
        model, X_holdout, y_holdout_days, scoring=day_space_neg_mae, random_state=42,
    ).importances_mean
    log_space = permutation_importance(
        model, X_holdout, y_holdout_log, scoring="neg_mean_absolute_error", random_state=42,
    ).importances_mean

    reported = result["importance"].set_index("feature").loc[result["feature_names"], "permutation_importance"].to_numpy()
    assert reported == pytest.approx(expected)
    assert reported != pytest.approx(log_space)


def test_evaluate_boosted_model_raises_when_holdout_predictions_convert_to_infinity(
    large_synthetic_kiva_df, monkeypatch,
):
    # `evaluate_boosted_model` passes its holdout predictions through the
    # same shared `log_predictions_to_days` conversion boundary Ridge uses
    # (src/modeling.py) - a Codex review found this nonlinear path was
    # previously unprotected: a finite log-space prediction (e.g. 1000.0)
    # converts to a non-finite `inf` day-space value with no warning
    # surfaced, and neither `mean_absolute_error`/`r2_score` here nor the
    # permutation-importance scorer checked for it. Force exactly that by
    # making the boosted model's `.predict()` return a constant, finite-
    # but-extreme value, and confirm the pipeline now raises a clear
    # diagnostic instead of silently returning `inf`/`nan` metrics.
    from sklearn.ensemble import HistGradientBoostingRegressor

    def _extreme_predict(self, X):
        return np.full(X.shape[0], 1000.0)

    monkeypatch.setattr(HistGradientBoostingRegressor, "predict", _extreme_predict)

    with pytest.raises(InsufficientDataError, match="non-finite"):
        evaluate_boosted_model(large_synthetic_kiva_df, holdout_start="2024-01-01", n_topics=2)
