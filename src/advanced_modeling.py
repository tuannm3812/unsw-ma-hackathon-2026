"""
Nonlinear benchmark for predicting Kiva loan funding speed.

This module provides exactly one gradient-boosting benchmark,
`evaluate_boosted_model`, built on top of the shared leakage-safe
chronological data-prep pipeline in `src/modeling.py`
(`prepare_chronological_matrices`). It does not re-derive its own
train/holdout split or preprocessing: it calls
`prepare_chronological_matrices` once, fits `HistGradientBoostingRegressor`
on the training partition only, and evaluates on the untouched chronological
holdout - the same evaluation design `evaluate_chronological_models` uses
for the linear baselines, so the two benchmarks are directly comparable.

`sklearn.ensemble.HistGradientBoostingRegressor` is used instead of
`xgboost`/`lightgbm` to avoid two redundant third-party gradient-boosting
dependencies for a single nonlinear reference point; scikit-learn's built-in
implementation is sufficient for a benchmark and keeps `requirements.txt`
smaller.
"""

import os

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, median_absolute_error, mean_squared_error, r2_score

try:
    from src.data_loader import load_kiva_pickle
    from src.modeling import log_predictions_to_days, prepare_chronological_matrices
except ModuleNotFoundError:
    from data_loader import load_kiva_pickle
    from modeling import log_predictions_to_days, prepare_chronological_matrices


def _day_space_neg_mae(estimator, X, y_days) -> float:
    """
    Permutation-importance scorer that evaluates in day space, matching
    every other metric this module reports (`mae_days`, `medae_days`,
    `rmse_days`, `r2`). `estimator.predict` returns log-space predictions;
    `log_predictions_to_days` converts them the same way `mae_days` etc.
    are computed, so permutation importance measures the same thing a
    reader of the metrics dict would expect "importance" to mean.

    Scoring in the model's native log space instead would not just rescale
    the numbers: `log_predictions_to_days` (clip then `expm1`) is a convex
    transform, so it amplifies errors on long-duration predictions more
    than short ones. A feature that mostly affects long-duration loans can
    therefore rank differently by log-space MAE than by day-space MAE.
    """
    predicted_days = log_predictions_to_days(estimator.predict(X))
    return -mean_absolute_error(y_days, predicted_days)


def evaluate_boosted_model(
    df: pd.DataFrame,
    holdout_start: str = "2024-01-01",
    n_topics: int = 5,
    random_state: int = 42,
) -> dict:
    """
    Fit a `HistGradientBoostingRegressor` on the shared chronological
    training split and evaluate it on the untouched chronological holdout.

    Reuses `prepare_chronological_matrices` for the entire split/
    preprocessing pipeline (chronological train/holdout split, imputation,
    scaling, one-hot encoding, and topic modeling - all fit on the training
    partition only). This function fits nothing on the holdout or the full
    dataset; it only fits the boosted regressor on the already-encoded
    training matrix.

    Predictions are made in log space (matching the target the model is
    trained on) and converted back to days via `log_predictions_to_days`,
    which clips negative log predictions to zero before `expm1` so an
    unconstrained regressor can never yield a negative "duration".

    Permutation importance is computed on the holdout split (the data the
    model has not seen), using negative day-space MAE as the scoring
    function (see `_day_space_neg_mae`) and the same `random_state` used
    to fit the model, so results are reproducible and directly comparable
    to the day-space metrics reported alongside them.

    Returns a dict with row counts, feature names, a `"metrics"` dict
    (`mae_days`, `medae_days`, `rmse_days`, `r2`), an `"importance"`
    DataFrame with exactly the columns `{"feature", "permutation_importance"}`
    sorted by importance descending, and a private `_artifacts` key holding
    the fitted model and the matrices/transformers from
    `prepare_chronological_matrices`.
    """
    matrices = prepare_chronological_matrices(df, holdout_start=holdout_start, n_topics=n_topics)
    artifacts = matrices["_artifacts"]

    X_train, X_holdout = artifacts["X_train"], artifacts["X_holdout"]
    y_train = artifacts["y_train"]
    y_holdout_days = artifacts["y_holdout_days"]

    model = HistGradientBoostingRegressor(random_state=random_state)
    model.fit(X_train, y_train)

    holdout_pred_days = log_predictions_to_days(model.predict(X_holdout))

    metrics = {
        "mae_days": float(mean_absolute_error(y_holdout_days, holdout_pred_days)),
        "medae_days": float(median_absolute_error(y_holdout_days, holdout_pred_days)),
        "rmse_days": float(np.sqrt(mean_squared_error(y_holdout_days, holdout_pred_days))),
        "r2": float(r2_score(y_holdout_days, holdout_pred_days)),
    }

    perm_result = permutation_importance(
        model,
        X_holdout,
        y_holdout_days,
        scoring=_day_space_neg_mae,
        random_state=random_state,
    )
    importance = pd.DataFrame({
        "feature": matrices["feature_names"],
        "permutation_importance": perm_result.importances_mean,
    }).sort_values(by="permutation_importance", ascending=False).reset_index(drop=True)

    artifacts["boosted_model"] = model

    return {
        "holdout_start": matrices["holdout_start"],
        "train_rows": matrices["train_rows"],
        "holdout_rows": matrices["holdout_rows"],
        "feature_names": matrices["feature_names"],
        "metrics": metrics,
        "importance": importance,
        "_artifacts": artifacts,
    }


def run_advanced_cv_modeling(pkl_path: str) -> dict:
    """
    Deprecated. This used to run a random 5-fold cross-validation with
    XGBoost and LightGBM, fit on the full dataset (including the holdout it
    was "evaluated" on) with the missing target imputed by its own median -
    a leakage-unsafe design on every count. It has been replaced by
    `evaluate_boosted_model`, which trains a single
    `HistGradientBoostingRegressor` on a chronological train split and
    evaluates on an untouched chronological holdout, consistent with the
    rest of this project's leakage-safe evaluation design.

    This wrapper no longer performs the old evaluation; it loads the data
    and delegates to `evaluate_boosted_model` so existing callers keep
    working, but get the leakage-safe benchmark instead.
    """
    print(
        "run_advanced_cv_modeling is deprecated: it used a leakage-unsafe "
        "random 5-fold CV over XGBoost/LightGBM fit on the full dataset. "
        "Delegating to evaluate_boosted_model (chronological holdout, "
        "HistGradientBoostingRegressor) instead."
    )
    df = load_kiva_pickle(pkl_path)
    results = evaluate_boosted_model(df)

    print(f"\nTraining rows: {results['train_rows']}")
    print(f"Holdout rows:  {results['holdout_rows']}")
    print(f"Holdout MAE (days):    {results['metrics']['mae_days']:.4f}")
    print(f"Holdout median AE:     {results['metrics']['medae_days']:.4f}")
    print(f"Holdout RMSE (days):   {results['metrics']['rmse_days']:.4f}")
    print(f"Holdout R2:            {results['metrics']['r2']:.4f}")
    print("\nTop 10 permutation importances (holdout):")
    print(results["importance"].head(10).to_string(index=False))

    return results


if __name__ == "__main__":
    default_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Kiva_Loans_Sample.pkl")
    run_advanced_cv_modeling(default_path)
