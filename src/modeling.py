"""
Leakage-safe modeling pipeline for predicting Kiva loan funding speed.

The evaluation design here is chronological, not random: the model is
trained on loans posted before `holdout_start` and evaluated on loans
posted on or after it, mirroring how the model would actually be used
(scoring newly-posted loans using only information knowable at posting
time). All learned transformations - median/most-frequent imputation,
standard scaling, one-hot encoding, and the TF-IDF/NMF topic model - are
fit on the training partition only and merely *applied* (never re-fit) to
the holdout partition.

Predictors are chosen via an explicit allowlist (not by taking "every
numeric column" and hoping nothing sensitive slipped in). Any field that
records or derives from the funding outcome - `raisedDate`,
`funding_speed_days`, `log_funding_speed`, `funded_within_24h`,
`valid_completed_outcome`, `outcome_issue`, `status` - is excluded by
construction because it is never in the allowlist, not by being blocked
after the fact.
"""

import os
import warnings

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, median_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from src.data_loader import load_kiva_pickle, prepare_analysis_data
    from src.features import extract_deterministic_features
    from src.text_transformer import KivaTopicTransformer
    from src.validation import InsufficientDataError, chronological_holdout
except ModuleNotFoundError:
    from data_loader import load_kiva_pickle, prepare_analysis_data
    from features import extract_deterministic_features
    from text_transformer import KivaTopicTransformer
    from validation import InsufficientDataError, chronological_holdout


# Explicit predictor allowlist, built from the project's data contract for
# fields available at-or-before loan posting time. See the module docstring
# and the task report for the reasoning behind deliberate omissions
# (`country_name` as redundant with `country_iso`; `fundsLentInCountry` as
# an unverified-timestamp field; raw `description`/`use`/`whySpecial`/
# `gender`/`loanAmount` used only via their derived features below).
NUMERIC_PREDICTOR_COLUMNS = [
    "borrowerCount",
    "log_loan_amount",
    "desc_word_count",
    "desc_char_count",
    "desc_sentence_count",
    "desc_avg_word_length",
    "desc_avg_sentence_length",
    "description_missing",
    "use_missing",
    "whySpecial_missing",
    "number_token_count",
    "age_pattern_count",
    "years_in_business_count",
    "family_mentions_per_100_words",
    "basic_needs_mentions_per_100_words",
    "business_mentions_per_100_words",
    "agency_mentions_per_100_words",
    "gratitude_mentions_per_100_words",
    "urgency_mentions_per_100_words",
    "first_person_mentions_per_100_words",
    "third_person_mentions_per_100_words",
    "desc_sentiment_compound",
    "desc_sentiment_pos",
    "desc_sentiment_neg",
    "desc_sentiment_neu",
    "sentiment_available",
    "is_group_loan",
    "lenderRepaymentTerm",
    "country_ppp",
    "fundraising_year",
    "fundraising_month",
]

CATEGORICAL_PREDICTOR_COLUMNS = [
    "gender_classification",
    "loan_size_band",
    "repaymentInterval",
    "sector",
    "activity",
    "country_iso",
    "region",
    "analysis_period",
]

MIN_SPLIT_OBSERVATIONS = 5


def build_predictor_frame(df: pd.DataFrame) -> "tuple[pd.DataFrame, list, list]":
    """
    Build the modeling predictor matrix from an allowlist, not a blocklist.

    Computes deterministic row-level features (safe to call on any subset
    of rows - it fits nothing across rows) and then selects only the
    columns in `NUMERIC_PREDICTOR_COLUMNS` / `CATEGORICAL_PREDICTOR_COLUMNS`.
    Every other column present in `df` - including IDs, names, statuses,
    outcome dates, and derived outcome/leakage fields - is left out simply
    because it was never added to the allowlist.

    Returns (predictors, numeric_columns, categorical_columns).
    """
    featured = extract_deterministic_features(df)

    missing = [
        col for col in NUMERIC_PREDICTOR_COLUMNS + CATEGORICAL_PREDICTOR_COLUMNS
        if col not in featured.columns
    ]
    if missing:
        raise ValueError(
            "build_predictor_frame allowlist references columns that do not "
            f"exist after feature extraction: {sorted(missing)}"
        )

    numeric_columns = list(NUMERIC_PREDICTOR_COLUMNS)
    categorical_columns = list(CATEGORICAL_PREDICTOR_COLUMNS)

    predictors = featured[numeric_columns + categorical_columns].copy()

    for column in numeric_columns:
        predictors[column] = pd.to_numeric(predictors[column], errors="coerce")
    for column in categorical_columns:
        # Categorical/nullable dtypes convert missing entries to np.nan on
        # cast to object, which SimpleImputer(strategy="most_frequent")
        # recognizes as missing.
        predictors[column] = predictors[column].astype(object)

    return predictors, numeric_columns, categorical_columns


def _build_column_transformer(numeric_columns, categorical_columns) -> ColumnTransformer:
    numeric_pipeline = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical_pipeline = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer([
        ("numeric", numeric_pipeline, numeric_columns),
        ("categorical", categorical_pipeline, categorical_columns),
    ])


def prepare_chronological_matrices(
    df: pd.DataFrame,
    holdout_start: str = "2024-01-01",
    n_topics: int = 5,
) -> dict:
    """
    Build a leakage-safe chronological train/holdout split with fitted
    preprocessing artifacts, ready for any downstream estimator (linear or
    nonlinear) to consume identically.

    Pipeline, in order:
      1. `prepare_analysis_data` parses dates and derives the target.
      2. Rows without a `valid_completed_outcome` are dropped - never
         imputed, since a missing/invalid outcome is not a value to guess.
      3. `chronological_holdout` splits the remaining rows on
         `fundraisingDate` at `holdout_start`.
      4. Deterministic features are computed separately on each partition
         (harmless either way since they fit nothing across rows, but done
         post-split to keep the pipeline unambiguous).
      5. A `KivaTopicTransformer` is fit on training descriptions only and
         used to transform both partitions.
      6. A `ColumnTransformer` (median/most-frequent imputation, scaling,
         one-hot encoding) is fit on the training predictor matrix only and
         used to transform both partitions.

    Returns a dict with row counts, feature name lists, and a private
    `_artifacts` key holding the fitted transformers, transformed matrices,
    both targets (continuous: log space and days; binary: `funded_within_24h`),
    and untransformed predictor frames.
    """
    prepared = prepare_analysis_data(df)
    valid = prepared.loc[prepared["valid_completed_outcome"]].copy()

    train_raw, holdout_raw = chronological_holdout(
        valid, date_col="fundraisingDate", holdout_start=holdout_start
    )

    if len(train_raw) < MIN_SPLIT_OBSERVATIONS or len(holdout_raw) < MIN_SPLIT_OBSERVATIONS:
        raise InsufficientDataError(
            "prepare_chronological_matrices requires at least "
            f"{MIN_SPLIT_OBSERVATIONS} valid observations in both the training and "
            f"holdout splits; got {len(train_raw)} training and {len(holdout_raw)} "
            f"holdout rows for holdout_start={holdout_start!r}"
        )

    train_predictors, numeric_columns, categorical_columns = build_predictor_frame(train_raw)
    holdout_predictors, _, _ = build_predictor_frame(holdout_raw)

    topic_transformer = KivaTopicTransformer(n_topics=n_topics, random_state=42)
    topic_transformer.fit(train_raw["description"])
    train_topics = topic_transformer.transform(train_raw["description"])
    holdout_topics = topic_transformer.transform(holdout_raw["description"])
    topic_columns = [str(name) for name in topic_transformer.get_feature_names_out()]

    train_full = pd.concat([train_predictors, train_topics], axis=1)
    holdout_full = pd.concat([holdout_predictors, holdout_topics], axis=1)

    all_numeric_columns = numeric_columns + topic_columns

    column_transformer = _build_column_transformer(all_numeric_columns, categorical_columns)
    X_train = column_transformer.fit_transform(train_full)
    X_holdout = column_transformer.transform(holdout_full)
    feature_names = list(column_transformer.get_feature_names_out())

    y_train = train_raw["log_funding_speed"].to_numpy(dtype=float)
    y_holdout = holdout_raw["log_funding_speed"].to_numpy(dtype=float)
    y_train_days = train_raw["funding_speed_days"].to_numpy(dtype=float)
    y_holdout_days = holdout_raw["funding_speed_days"].to_numpy(dtype=float)
    # `funded_within_24h` is always determinable (never <NA>) within rows
    # that already passed the `valid_completed_outcome` filter above (see
    # `prepare_analysis_data`), so this is safe to cast straight to int -
    # exposed here, not just the continuous target, so any binary-outcome
    # classifier (see `src/binary_modeling.py`) can reuse this exact same
    # leakage-safe split/encoding instead of rebuilding it.
    y_train_binary = train_raw["funded_within_24h"].to_numpy(dtype=int)
    y_holdout_binary = holdout_raw["funded_within_24h"].to_numpy(dtype=int)

    return {
        "holdout_start": holdout_start,
        "train_rows": int(len(train_raw)),
        "holdout_rows": int(len(holdout_raw)),
        "numeric_features": all_numeric_columns,
        "categorical_features": categorical_columns,
        "feature_names": feature_names,
        "_artifacts": {
            "column_transformer": column_transformer,
            "topic_transformer": topic_transformer,
            "X_train": X_train,
            "X_holdout": X_holdout,
            "y_train": y_train,
            "y_holdout": y_holdout,
            "y_train_days": y_train_days,
            "y_holdout_days": y_holdout_days,
            "y_train_binary": y_train_binary,
            "y_holdout_binary": y_holdout_binary,
            "train_df": train_full,
            "holdout_df": holdout_full,
        },
    }


def log_predictions_to_days(log_predictions: np.ndarray) -> np.ndarray:
    """
    Convert log1p-space duration predictions back to days.

    `log_funding_speed` targets are always >= 0 (they come from
    `log1p(funding_speed_days)` with `funding_speed_days >= 0`), but an
    unconstrained model (Ridge, or the nonlinear benchmark) can still
    predict a negative log value. `np.expm1` of a negative log prediction
    yields a negative "duration", which is outside the target's domain.
    Clip at zero in log space before converting, so every model's
    predictions stay within the domain of actual elapsed time.

    A model badly overfit on this project's small real sample (e.g. Ridge
    on an ~80-row training split) can pass in extreme log-space values;
    `np.expm1`/`np.clip` on those can themselves emit a benign
    RuntimeWarning without producing a non-finite result (verified against
    `data/Kiva_Loans_Sample.pkl` - see the report). Scoped to just this
    conversion so any other RuntimeWarning in this module still surfaces
    normally.

    This is the single shared boundary every caller in this project uses to
    turn a model's raw log-space prediction into a day-space one - Ridge,
    the training-median baseline, and (via `src/advanced_modeling.py`) the
    nonlinear benchmark's holdout predictions and its permutation-importance
    scorer. Two distinct failure modes are checked, not just one:

    1. The raw prediction itself is already non-finite (`nan`, `+inf`, or
       `-inf`) - a badly broken model, not a conversion artifact. This must
       be checked *before* clipping: `np.clip(-inf, a_min=0.0, ...)`
       evaluates to a plain `0.0` (clipping treats `-inf` as "below the
       floor"), which would otherwise silently launder a `-inf` prediction
       into a plausible-looking "funded in 0 days" instead of raising a
       diagnostic - the more dangerous failure mode of the two, since it
       produces a convincing wrong answer rather than an obviously invalid
       one.
    2. The raw prediction is finite but sufficiently extreme (e.g. ~1000)
       that it overflows `np.expm1` into a non-finite `inf` day-space value,
       with the RuntimeWarning above suppressed - checked *after*
       conversion, since the input itself was valid.

    Both are checked here, once, so every caller is protected without
    duplicating the check at each call site - and each raises a distinct,
    accurate message rather than describing an overflow that did not
    happen.
    """
    if not np.all(np.isfinite(log_predictions)):
        raise InsufficientDataError(
            "log_predictions_to_days received non-finite log-space "
            "prediction(s) (nan, +inf, or -inf) - the underlying model "
            "itself produced an invalid value; this is not a conversion "
            "artifact. This usually means the model is not well identified "
            "on this sample. Provide more rows or fewer/coarser predictor "
            "columns, and try again."
        )
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        days = np.expm1(np.clip(log_predictions, a_min=0.0, a_max=None))
    if not np.all(np.isfinite(days)):
        raise InsufficientDataError(
            "log_predictions_to_days produced non-finite day-space value(s) "
            "from finite log-space prediction(s) - an extreme prediction "
            "overflowed through np.expm1. This usually means the underlying "
            "model is not well identified on this sample (e.g. severe "
            "overfitting on too few training rows relative to features). "
            "Provide more rows or fewer/coarser predictor columns, and try "
            "again."
        )
    return days


def _check_ridge_well_identified(coefficients: np.ndarray, n_obs: int, n_cols: int) -> None:
    """
    Mirrors `statistical_analysis._check_well_identified`: a design can stay
    technically full rank while still being too close to rank-deficient to
    support a stable fit. On this project's small real sample, Ridge's SVD
    solver can emit a benign RuntimeWarning (suppressed in `.fit()`'s call
    site) without the resulting coefficients ever going non-finite -
    verified against `data/Kiva_Loans_Sample.pkl` and a synthetic fixture
    (see tests/test_modeling.py). This check turns the case where that
    stops holding into a clear diagnostic instead of a silently-NaN metric.

    Only checks `coefficients`: prediction finiteness (including the
    post-`log_predictions_to_days` day-space case) is guaranteed by
    `log_predictions_to_days` itself, the shared conversion boundary every
    caller goes through - duplicating that check here would be dead code.
    """
    if not np.all(np.isfinite(coefficients)):
        raise InsufficientDataError(
            f"Ridge produced non-finite coefficients for "
            f"{n_obs} training observations vs {n_cols} design columns - the "
            "design is likely too rank-deficient for a stable fit. Provide "
            "more rows or fewer/coarser predictor columns, and try again."
        )


def _days_metrics(y_true_days: np.ndarray, y_pred_days: np.ndarray) -> dict:
    return {
        "mae_days": float(mean_absolute_error(y_true_days, y_pred_days)),
        "medae_days": float(median_absolute_error(y_true_days, y_pred_days)),
        "r2": float(r2_score(y_true_days, y_pred_days)),
    }


def evaluate_chronological_models(
    df: pd.DataFrame,
    holdout_start: str = "2024-01-01",
    n_topics: int = 5,
) -> dict:
    """
    Fit and evaluate two leakage-safe baselines on the shared chronological
    split produced by `prepare_chronological_matrices`:

      - `baseline`: predicts the training-set median `log_funding_speed`
        for every row (a naive but leakage-safe reference point).
      - `ridge`: `Ridge(alpha=1.0)` fit on the transformed training matrix.

    Both are trained on `log_funding_speed` and converted back to days via
    `log_predictions_to_days` (clip at zero, then `np.expm1`) before MAE,
    median-AE, and R2 are computed, so the reported metrics are in the same
    units analysts think in (days), not log-days, and never negative.

    Returns a JSON-serializable dict (row counts, split boundary, feature
    names, metrics) plus a private `_artifacts` key holding fitted objects,
    transformed matrices, and untransformed split frames - callers that
    serialize this dict to a report should drop `_artifacts` first.
    """
    matrices = prepare_chronological_matrices(df, holdout_start=holdout_start, n_topics=n_topics)
    artifacts = matrices["_artifacts"]

    X_train, X_holdout = artifacts["X_train"], artifacts["X_holdout"]
    y_train, y_holdout = artifacts["y_train"], artifacts["y_holdout"]
    y_train_days, y_holdout_days = artifacts["y_train_days"], artifacts["y_holdout_days"]

    # Baseline: training-median log-speed, applied as a constant prediction.
    # (Guaranteed >= 0 since it's the median of non-negative training
    # targets, but converted through the same clipped helper as every other
    # model for a single, consistently-tested log-to-days conversion path.)
    train_median_log = float(np.median(y_train))
    baseline_train_pred_days = np.full_like(y_train_days, log_predictions_to_days(np.array(train_median_log)))
    baseline_holdout_pred_days = np.full_like(y_holdout_days, log_predictions_to_days(np.array(train_median_log)))

    train_metrics = _days_metrics(y_train_days, baseline_train_pred_days)
    holdout_metrics = _days_metrics(y_holdout_days, baseline_holdout_pred_days)
    baseline_metrics = {
        "train_mae_days": train_metrics["mae_days"],
        "holdout_mae_days": holdout_metrics["mae_days"],
        "train_medae_days": train_metrics["medae_days"],
        "holdout_medae_days": holdout_metrics["medae_days"],
        "train_r2": train_metrics["r2"],
        "holdout_r2": holdout_metrics["r2"],
    }

    # Ridge, fit only on the training partition.
    #
    # On this project's small real sample (~80 training rows vs. many
    # one-hot/topic columns), the design is close to rank-deficient, which
    # can make both `Ridge.fit()`'s internal SVD-based solver and
    # `Ridge.predict()`'s `X @ coef_ + intercept_` emit a benign
    # divide-by-zero/overflow/invalid-value RuntimeWarning without the
    # resulting coefficients/predictions actually being non-finite
    # (verified directly against `data/Kiva_Loans_Sample.pkl` - see the
    # report). Scoped to just these three calls.
    ridge = Ridge(alpha=1.0, random_state=42)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        ridge.fit(X_train, y_train)
        ridge_train_pred = ridge.predict(X_train)
        ridge_holdout_pred = ridge.predict(X_holdout)
    # `log_predictions_to_days` itself raises InsufficientDataError if the
    # conversion produces a non-finite day-space value (see its docstring),
    # so prediction finiteness is already guaranteed by the time these
    # return. Only the coefficients need a separate check below.
    ridge_train_pred_days = log_predictions_to_days(ridge_train_pred)
    ridge_holdout_pred_days = log_predictions_to_days(ridge_holdout_pred)
    _check_ridge_well_identified(ridge.coef_, *X_train.shape)

    train_metrics = _days_metrics(y_train_days, ridge_train_pred_days)
    holdout_metrics = _days_metrics(y_holdout_days, ridge_holdout_pred_days)
    ridge_metrics = {
        "train_mae_days": train_metrics["mae_days"],
        "holdout_mae_days": holdout_metrics["mae_days"],
        "train_medae_days": train_metrics["medae_days"],
        "holdout_medae_days": holdout_metrics["medae_days"],
        "train_r2": train_metrics["r2"],
        "holdout_r2": holdout_metrics["r2"],
    }

    artifacts["ridge_model"] = ridge

    return {
        "holdout_start": matrices["holdout_start"],
        "train_rows": matrices["train_rows"],
        "holdout_rows": matrices["holdout_rows"],
        "numeric_features": matrices["numeric_features"],
        "categorical_features": matrices["categorical_features"],
        "feature_names": matrices["feature_names"],
        "metrics": {
            "baseline": baseline_metrics,
            "ridge": ridge_metrics,
        },
        "_artifacts": artifacts,
    }


def run_baseline_model(pkl_path: str, holdout_start: str = "2024-01-01", n_topics: int = 5) -> dict:
    """
    Notebook-facing entry point. Loads the raw pickle, runs the leakage-safe
    chronological evaluation, prints a summary, and returns the full results
    dict (metrics plus fitted artifacts under `_artifacts`) so notebooks and
    other callers can keep using the fitted `Ridge`/`ColumnTransformer`/
    `KivaTopicTransformer` objects without refitting.
    """
    print("Loading and preprocessing data...")
    df = load_kiva_pickle(pkl_path)

    print(f"Running chronological evaluation (holdout_start={holdout_start})...")
    results = evaluate_chronological_models(df, holdout_start=holdout_start, n_topics=n_topics)

    print(f"\nTraining rows: {results['train_rows']}")
    print(f"Holdout rows:  {results['holdout_rows']}")
    print(f"Number of features (post-encoding): {len(results['feature_names'])}")

    for model_name, metrics in results["metrics"].items():
        print(f"\n--- {model_name} ---")
        print(f"Train MAE (days):     {metrics['train_mae_days']:.4f}")
        print(f"Holdout MAE (days):   {metrics['holdout_mae_days']:.4f}")
        print(f"Train median AE:      {metrics['train_medae_days']:.4f}")
        print(f"Holdout median AE:    {metrics['holdout_medae_days']:.4f}")
        print(f"Train R2:             {metrics['train_r2']:.4f}")
        print(f"Holdout R2:           {metrics['holdout_r2']:.4f}")

    ridge = results["_artifacts"]["ridge_model"]
    coef_df = pd.DataFrame({
        "Feature": results["feature_names"],
        "Coefficient": ridge.coef_,
    })
    coef_df["Abs_Coefficient"] = coef_df["Coefficient"].abs()
    coef_df = coef_df.sort_values(by="Abs_Coefficient", ascending=False)
    print("\nTop 10 Ridge Regression Coefficients (Influence on log funding speed):")
    print(coef_df[["Feature", "Coefficient"]].head(10).to_string(index=False))

    return results


if __name__ == "__main__":
    default_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Kiva_Loans_Sample.pkl")
    run_baseline_model(default_path)
