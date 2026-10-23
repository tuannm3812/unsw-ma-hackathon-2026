"""Expanded feature-coverage sensitivity analysis for the Kiva project.

The project's existing explanatory model remains the pre-specified primary
specification.  This module answers the narrower audit question raised after
that model was reviewed: do its narrative conclusions survive when every
currently engineered text-feature family is examined, and when country,
activity, and fine-grained time controls replace their coarser nested forms?

Two complementary checks are provided:

* chronological Ridge comparisons isolate the incremental out-of-time value
  of the primary and expanded narrative blocks using the existing leakage-safe
  predictor matrix; and
* sparse Frisch-Waugh-Lovell regressions estimate narrative associations after
  partialling out richer controls, with country-clustered standard errors,
  family-level Wald tests, and Benjamini-Hochberg adjusted p-values.

The binary sensitivity is deliberately a linear-probability model.  That keeps
the full 1.45-million-row, high-dimensional fixed-effect check tractable and
does not replace the project's primary binomial GLM.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import linalg, sparse, stats
from scipy.sparse.linalg import lsmr
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from statsmodels.stats.multitest import multipletests

from src.data_loader import load_kiva_pickle, prepare_analysis_data
from src.features import extract_deterministic_features
from src.modeling import log_predictions_to_days
from src.text_transformer import KivaTopicTransformer
from src.validation import chronological_holdout


PRIMARY_NARRATIVE_FEATURES = [
    "desc_word_count",
    "family_mentions_per_100_words",
    "agency_mentions_per_100_words",
    "urgency_mentions_per_100_words",
    "desc_sentiment_compound",
]

NARRATIVE_FEATURE_FAMILIES = {
    "description_form": [
        "desc_word_count",
        "desc_char_count",
        "desc_sentence_count",
        "desc_avg_word_length",
        "desc_avg_sentence_length",
    ],
    "auxiliary_text": [
        "description_missing",
        "use_missing",
        "whySpecial_missing",
        "use_char_count",
        "use_word_count",
        "whySpecial_char_count",
        "whySpecial_word_count",
    ],
    "specificity": [
        "number_token_count",
        "age_pattern_count",
        "years_in_business_count",
    ],
    "framing": [
        "family_mentions_per_100_words",
        "basic_needs_mentions_per_100_words",
        "business_mentions_per_100_words",
        "agency_mentions_per_100_words",
        "gratitude_mentions_per_100_words",
        "urgency_mentions_per_100_words",
        "first_person_mentions_per_100_words",
        "third_person_mentions_per_100_words",
    ],
    # Neutral is the explicit reference share when all three shares are
    # requested. VADER rounding and empty descriptions mean their sum need
    # not be exactly one; this is a specification choice, not an exact rank claim.
    "sentiment": [
        "desc_sentiment_compound",
        "desc_sentiment_pos",
        "desc_sentiment_neg",
        "desc_sentiment_neu",
    ],
}

EXPANDED_NARRATIVE_FEATURES = list(
    dict.fromkeys(
        feature
        for family in NARRATIVE_FEATURE_FAMILIES.values()
        for feature in family
    )
)

RICH_NUMERIC_CONTROLS = [
    "log_loan_amount",
    "lenderRepaymentTerm",
    "borrowerCount",
    "is_group_loan",
]

RICH_CATEGORICAL_CONTROLS = [
    "gender_classification",
    "loan_size_band",
    "repaymentInterval",
    # Activity replaces sector, and country replaces region.  The coarser
    # variables are deterministic nestings of these and cannot coexist with
    # them in a full-rank fixed-effect design.
    "activity",
    "country_iso",
    "fundraising_year",
    "fundraising_month",
]

PREDICTION_STRUCTURAL_NUMERIC = [
    "borrowerCount",
    "log_loan_amount",
    "lenderRepaymentTerm",
    "country_ppp",
    "fundraising_year",
    "fundraising_month",
    "is_group_loan",
]

PREDICTION_STRUCTURAL_CATEGORICAL = [
    "gender_classification",
    "loan_size_band",
    "repaymentInterval",
    "sector",
    "activity",
    "country_iso",
    "region",
    "analysis_period",
]


def build_sensitivity_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare outcomes and every deterministic feature used by the audit."""
    prepared = prepare_analysis_data(df)
    return extract_deterministic_features(prepared)


def _complete_case_frame(
    frame: pd.DataFrame,
    outcome: str,
    narrative_features: Iterable[str],
    numeric_controls: Iterable[str],
    categorical_controls: Iterable[str],
    cluster_col: str,
) -> pd.DataFrame:
    columns = list(
        dict.fromkeys(
            [outcome, cluster_col]
            + list(narrative_features)
            + list(numeric_controls)
            + list(categorical_controls)
        )
    )
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"Sensitivity specification references missing columns: {missing}")
    result = frame.loc[:, columns].replace([np.inf, -np.inf], np.nan).dropna().copy()
    if result.empty:
        raise ValueError("Sensitivity specification has no complete rows")
    return result


def _control_matrix(
    data: pd.DataFrame,
    numeric_controls: list[str],
    categorical_controls: list[str],
) -> tuple[sparse.csr_matrix, list[str]]:
    parts: list[sparse.spmatrix] = [sparse.csr_matrix(np.ones((len(data), 1)))]
    names = ["intercept"]

    if numeric_controls:
        numeric = data[numeric_controls].to_numpy(dtype=float)
        means = numeric.mean(axis=0)
        scales = numeric.std(axis=0)
        scales[scales == 0] = 1.0
        numeric = (numeric - means) / scales
        parts.append(sparse.csr_matrix(numeric))
        names.extend(numeric_controls)

    if categorical_controls:
        encoder = OneHotEncoder(
            drop="first",
            handle_unknown="ignore",
            sparse_output=True,
            dtype=float,
        )
        encoded = encoder.fit_transform(data[categorical_controls].astype(str))
        parts.append(encoded)
        names.extend(encoder.get_feature_names_out(categorical_controls).tolist())

    matrix = sparse.hstack(parts, format="csr")
    # Unit column norms improve iterative convergence with rare fixed effects.
    norms = np.sqrt(np.asarray(matrix.power(2).sum(axis=0)).ravel())
    norms[norms == 0] = 1.0
    return matrix.multiply(1.0 / norms).tocsr(), names


def _residualize(controls: sparse.csr_matrix, values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.ndim == 1:
        values = values[:, None]
    residuals = np.empty_like(values, dtype=float)
    for column in range(values.shape[1]):
        solution = lsmr(
            controls,
            values[:, column],
            atol=1e-10,
            btol=1e-10,
            maxiter=max(1000, controls.shape[1] * 10),
        )
        if solution[1] not in {0, 1, 2, 4, 5}:
            raise ValueError(
                f"Control residualization did not converge for column {column}: "
                f"LSMR stop code {solution[1]}, iterations {solution[2]}"
            )
        residuals[:, column] = values[:, column] - controls @ solution[0]
        if not np.isfinite(residuals[:, column]).all():
            raise FloatingPointError("Control residualization produced non-finite values")
    return residuals


def _checked_matmul(left: np.ndarray, right: np.ndarray, label: str) -> np.ndarray:
    """Multiply through the known Apple-Accelerate warning and verify output.

    NumPy 2 on this project's Apple-Silicon environment can emit spurious
    divide/overflow/invalid RuntimeWarnings from small, finite matrix
    products (the same platform issue documented in ``src/modeling.py`` and
    ``src/text_transformer.py``).  Suppression is safe only at this narrow
    boundary because every result is immediately checked for finiteness.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        result = np.matmul(left, right)
    if not np.isfinite(result).all():
        raise FloatingPointError(f"{label} produced non-finite values")
    return result


def _independent_columns(
    matrix: np.ndarray, names: list[str], original_norms: np.ndarray,
) -> tuple[np.ndarray, list[str], list[str]]:
    norms = np.linalg.norm(matrix, axis=0)
    # Do not amplify iterative-solver residue from an absorbed feature into
    # an apparent independent direction. The threshold is relative to input
    # units, with a margin over the 1e-10 solver tolerance.
    nonzero = norms > 1e-8 * original_norms
    scaled = np.zeros_like(matrix)
    scaled[:, nonzero] = matrix[:, nonzero] / norms[nonzero]
    gram = _checked_matmul(scaled.T, scaled, "Narrative rank-check Gram matrix")
    if not np.isfinite(gram).all():
        raise ValueError("Residualized narrative design contains non-finite values")
    _, r, pivots = linalg.qr(gram, mode="economic", pivoting=True)
    diagonal = np.abs(np.diag(r))
    # A merely machine-epsilon threshold admits columns that are technically
    # distinct but numerically unusable (the VADER pos/neg/neutral shares are
    # the real-data example).  A relative 1e-8 threshold treats a direction
    # carrying less than roughly one hundred-millionth of the standardized
    # design's information as dependent and records the dropped column.
    tolerance = 1e-8 * (diagonal.max() if diagonal.size else 0.0)
    rank = int(np.sum(diagonal > tolerance))
    keep_set = set(int(index) for index in pivots[:rank])
    kept_indices = [index for index in range(len(names)) if index in keep_set]
    dropped = [name for index, name in enumerate(names) if index not in keep_set]
    if not kept_indices:
        raise ValueError("No independent narrative features remain after residualizing controls")
    return matrix[:, kept_indices], [names[index] for index in kept_indices], dropped


def fit_clustered_partial_regression(
    frame: pd.DataFrame,
    *,
    outcome: str,
    narrative_features: list[str],
    numeric_controls: list[str],
    categorical_controls: list[str],
    cluster_col: str,
    feature_families: dict[str, list[str]],
) -> dict[str, object]:
    """Fit a rich-control OLS/LPM sensitivity with clustered uncertainty.

    Controls are partialled out with sparse least squares.  The remaining
    narrative regression is algebraically equivalent to including the same
    controls directly in OLS (Frisch-Waugh-Lovell), while avoiding a dense
    1.45M-by-hundreds fixed-effect matrix.
    """
    requested_narrative_features = list(narrative_features)
    pre_dropped_features = []
    sentiment_composition = {
        "desc_sentiment_pos",
        "desc_sentiment_neg",
        "desc_sentiment_neu",
    }
    if sentiment_composition.issubset(narrative_features):
        # Choose neutral as the reference to avoid nearly compositional
        # dependence. Rounding and empty text prevent exact identity in all
        # rows, so this is an explicit restriction of the specification.
        narrative_features = [
            feature for feature in narrative_features if feature != "desc_sentiment_neu"
        ]
        pre_dropped_features.append("desc_sentiment_neu")
    data = _complete_case_frame(
        frame,
        outcome,
        requested_narrative_features,
        numeric_controls,
        categorical_controls,
        cluster_col,
    )
    # A feature constant within every level of one categorical control is
    # exactly in that control's dummy span. Detect this before iterative
    # projection: LSMR's backward-error stopping rule can leave residue above
    # the relative-norm cutoff for an intercept-minus-many-dummies contrast.
    categorically_absorbed = {}
    for control in categorical_controls:
        remaining = [name for name in narrative_features
                     if name not in categorically_absorbed]
        if not remaining:
            break
        grouped = data[remaining].groupby(data[control].astype(str), sort=False)
        constant_within_groups = grouped.min().eq(grouped.max()).all()
        for name in constant_within_groups.index[constant_within_groups]:
            categorically_absorbed[name] = control
    narrative_features = [name for name in narrative_features
                          if name not in categorically_absorbed]
    pre_dropped_features.extend(categorically_absorbed)
    if not narrative_features:
        raise ValueError("No independent narrative features remain after categorical absorption")
    controls, control_names = _control_matrix(data, numeric_controls, categorical_controls)
    # Only the small p-by-p cross-product is dense, never the n-by-p design.
    # Nested controls do not add degrees of freedom to the CR1 correction.
    control_gram = (controls.T @ controls).toarray()
    eigenvalues = linalg.eigvalsh(control_gram, check_finite=True)
    control_rank = int(np.sum(eigenvalues > 1e-10 * eigenvalues[-1]))
    y_residual = _residualize(controls, data[outcome].to_numpy(dtype=float)).ravel()
    x_residual = _residualize(controls, data[narrative_features].to_numpy(dtype=float))
    x_residual, kept_features, dropped_features = _independent_columns(
        x_residual, list(narrative_features),
        np.linalg.norm(data[narrative_features].to_numpy(dtype=float), axis=0),
    )
    dropped_features = pre_dropped_features + dropped_features

    feature_scales = np.linalg.norm(x_residual, axis=0)
    x_scaled = x_residual / feature_scales
    gram = _checked_matmul(x_scaled.T, x_scaled, "Narrative regression Gram matrix")
    try:
        factor = linalg.cho_factor(gram, lower=True, check_finite=True)
        bread = linalg.cho_solve(factor, np.eye(gram.shape[0]), check_finite=True)
    except linalg.LinAlgError as error:
        raise ValueError("Retained narrative design is still numerically singular") from error
    rhs = _checked_matmul(x_scaled.T, y_residual, "Narrative regression right-hand side")
    scaled_coefficients = _checked_matmul(bread, rhs, "Narrative regression coefficients")
    coefficients = scaled_coefficients / feature_scales
    residuals = y_residual - _checked_matmul(
        x_scaled, scaled_coefficients, "Narrative fitted values"
    )

    cluster_codes, cluster_labels = pd.factorize(data[cluster_col], sort=True)
    n_clusters = len(cluster_labels)
    if n_clusters < 2:
        raise ValueError("Clustered sensitivity requires at least two clusters")
    scores = np.zeros((n_clusters, len(kept_features)), dtype=float)
    np.add.at(scores, cluster_codes, x_scaled * residuals[:, None])
    meat = _checked_matmul(scores.T, scores, "Cluster sandwich meat")

    n_rows = len(data)
    full_parameter_count = control_rank + len(kept_features)
    if n_rows <= full_parameter_count:
        raise ValueError(
            f"Sensitivity design needs more rows than parameters; got {n_rows} rows "
            f"and {full_parameter_count} parameters"
        )
    correction = (n_clusters / (n_clusters - 1)) * ((n_rows - 1) / (n_rows - full_parameter_count))
    bread_meat = _checked_matmul(bread, meat, "Cluster sandwich left product")
    scaled_covariance = correction * _checked_matmul(
        bread_meat, bread, "Cluster sandwich covariance"
    )
    inverse_scales = 1.0 / feature_scales
    covariance = scaled_covariance * inverse_scales[:, None] * inverse_scales[None, :]
    standard_errors = np.sqrt(np.clip(np.diag(covariance), 0.0, None))
    t_values = np.divide(
        coefficients,
        standard_errors,
        out=np.full_like(coefficients, np.nan),
        where=standard_errors > 0,
    )
    p_values = 2 * stats.t.sf(np.abs(t_values), df=n_clusters - 1)
    fdr_values = multipletests(np.nan_to_num(p_values, nan=1.0), method="fdr_bh")[1]

    coefficient_table = pd.DataFrame(
        {
            "feature": kept_features,
            "coefficient": coefficients,
            "standard_error": standard_errors,
            "t_value": t_values,
            "p_value": p_values,
            "fdr_p_value": fdr_values,
            "ci_low": coefficients - stats.t.ppf(0.975, n_clusters - 1) * standard_errors,
            "ci_high": coefficients + stats.t.ppf(0.975, n_clusters - 1) * standard_errors,
        }
    )

    joint_rows = []
    feature_index = {name: index for index, name in enumerate(kept_features)}
    for family, requested in feature_families.items():
        members = [name for name in requested if name in feature_index]
        if not members:
            continue
        indices = [feature_index[name] for name in members]
        beta = coefficients[indices]
        family_covariance = covariance[np.ix_(indices, indices)]
        # Normalize to correlations before checking rank so units (counts
        # versus shares) do not determine which restriction is estimable.
        family_se = np.sqrt(np.clip(np.diag(family_covariance), 0.0, None))
        positive_se = family_se > 0
        correlation = np.zeros_like(family_covariance)
        denominator = family_se[:, None] * family_se[None, :]
        np.divide(family_covariance, denominator, out=correlation, where=denominator > 0)
        eigenvalues = linalg.eigvalsh(correlation, check_finite=True)
        covariance_rank = int(np.sum(eigenvalues > 1e-10 * max(eigenvalues[-1], 0)))
        available = covariance_rank == len(indices) and positive_se.all()
        if available:
            standardized_beta = beta / family_se
            weighted_beta = linalg.solve(correlation, standardized_beta, assume_a="pos")
            statistic = float(np.dot(standardized_beta, weighted_beta) / len(indices))
            p_value = float(stats.f.sf(statistic, len(indices), n_clusters - 1))
        else:
            # A pseudoinverse tests only a projected subspace, not the full
            # named family. Do not publish its p-value as the latter.
            statistic = p_value = float("nan")
        joint_rows.append(
            {
                "family": family,
                "n_features": len(indices),
                "covariance_rank": covariance_rank,
                "df_numerator": len(indices) if available else None,
                "df_denominator": n_clusters - 1,
                "test_status": "available" if available else "unavailable_singular_covariance",
                "statistic": statistic,
                "p_value": p_value,
            }
        )
    joint_table = pd.DataFrame(joint_rows)
    if not joint_table.empty:
        # Separate exploratory family from coefficient-level BH correction.
        joint_table["fdr_p_value"] = multipletests(
            joint_table["p_value"].fillna(1.0), method="fdr_bh"
        )[1]
        joint_table.loc[joint_table["p_value"].isna(), "fdr_p_value"] = np.nan

    return {
        "outcome": outcome,
        "model_type": "OLS" if outcome != "funded_within_24h" else "linear_probability_model",
        "n_rows": int(n_rows),
        "input_rows": int(len(frame)),
        "complete_case_excluded_rows": int(len(frame) - n_rows),
        "missing_by_column": {
            name: int(frame[name].replace([np.inf, -np.inf], np.nan).isna().sum())
            for name in data.columns
        },
        "control_rank": control_rank,
        "control_column_count": controls.shape[1],
        "full_parameter_count": full_parameter_count,
        "coefficient_fdr_family": "retained_narrative_terms_within_this_outcome",
        "joint_fdr_family": "reported_feature_families_within_this_outcome",
        "numerical_tolerances": {
            "lsmr_atol_btol": 1e-10,
            "absorbed_relative_norm": 1e-8,
            "narrative_gram_rank": 1e-8,
            "control_gram_rank": 1e-10,
            "joint_correlation_rank": 1e-10,
        },
        "n_clusters": int(n_clusters),
        "cluster_column": cluster_col,
        "numeric_controls": list(numeric_controls),
        "categorical_controls": list(categorical_controls),
        "control_columns": control_names,
        "requested_narrative_features": requested_narrative_features,
        "dropped_narrative_features": dropped_features,
        "categorically_absorbed_features": categorically_absorbed,
        "coefficients": coefficient_table,
        "joint_tests": joint_table,
    }


def _prediction_transformer(numeric_columns: list[str]) -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=True),
            ),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric_pipeline, numeric_columns),
            ("categorical", categorical_pipeline, PREDICTION_STRUCTURAL_CATEGORICAL),
        ],
        sparse_threshold=1.0,
    )


def evaluate_nested_ridge(
    df: pd.DataFrame,
    *,
    featured_frame: pd.DataFrame | None = None,
    holdout_start: str = "2024-01-01",
    n_topics: int = 5,
) -> dict[str, object]:
    """Compare nested feature blocks on the same chronological split."""
    if featured_frame is None:
        featured_frame = build_sensitivity_frame(df)
    elif len(featured_frame) != len(df) or not featured_frame.index.equals(df.index):
        raise ValueError("featured_frame must have the same rows and index as df")
    valid = featured_frame.loc[featured_frame["valid_completed_outcome"]].copy()
    train, holdout = chronological_holdout(
        valid, date_col="fundraisingDate", holdout_start=holdout_start
    )

    topic_transformer = KivaTopicTransformer(n_topics=n_topics, random_state=42)
    topic_transformer.fit(train["description"])
    train_topics = topic_transformer.transform(train["description"])
    holdout_topics = topic_transformer.transform(holdout["description"])
    topic_names = topic_transformer.get_feature_names_out().tolist()
    train = pd.concat([train, train_topics], axis=1)
    holdout = pd.concat([holdout, holdout_topics], axis=1)

    for column in PREDICTION_STRUCTURAL_CATEGORICAL:
        train[column] = train[column].astype(object).where(train[column].notna(), np.nan)
        holdout[column] = holdout[column].astype(object).where(holdout[column].notna(), np.nan)

    block_narrative_features = {
        "structural_only": [],
        "primary_narrative": list(PRIMARY_NARRATIVE_FEATURES),
        "expanded_narrative": list(EXPANDED_NARRATIVE_FEATURES) + topic_names,
    }
    y_train = train["log_funding_speed"].to_numpy(dtype=float)
    y_holdout_days = holdout["funding_speed_days"].to_numpy(dtype=float)

    blocks: dict[str, dict[str, float | int]] = {}
    for name, narrative_features in block_narrative_features.items():
        numeric_columns = PREDICTION_STRUCTURAL_NUMERIC + narrative_features
        transformer = _prediction_transformer(numeric_columns)
        x_train = transformer.fit_transform(
            train[numeric_columns + PREDICTION_STRUCTURAL_CATEGORICAL]
        )
        x_holdout = transformer.transform(
            holdout[numeric_columns + PREDICTION_STRUCTURAL_CATEGORICAL]
        )
        model = Ridge(alpha=1.0)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            model.fit(x_train, y_train)
            raw_predictions = model.predict(x_holdout)
        predictions = log_predictions_to_days(raw_predictions)
        blocks[name] = {
            "n_features": int(x_train.shape[1]),
            "included_narrative_features": narrative_features,
            "holdout_mae_days": float(mean_absolute_error(y_holdout_days, predictions)),
            "holdout_r2": float(r2_score(y_holdout_days, predictions)),
        }

    return {
        "holdout_start": holdout_start,
        "train_rows": int(len(train)),
        "holdout_rows": int(len(holdout)),
        "blocks": blocks,
    }


def _serializable(value):
    if isinstance(value, pd.DataFrame):
        return _serializable(value.to_dict(orient="records"))
    if isinstance(value, dict):
        return {key: _serializable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serializable(item) for item in value]
    if isinstance(value, (np.integer, np.floating)):
        return _serializable(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _report_text(payload: dict[str, object]) -> str:
    lines = [
        "Expanded Feature Sensitivity",
        "============================",
        "",
        "This is a sensitivity analysis, not a replacement for the pre-specified primary model.",
        "The 24-hour specification is a linear-probability model for tractable rich-control verification.",
        "",
        "Chronological Ridge block comparison",
        "-------------------------------------",
    ]
    prediction = payload.get("prediction", {})
    for name, result in prediction.get("blocks", {}).items():
        lines.append(
            f"- {name}: {result['n_features']} features; holdout MAE "
            f"{result['holdout_mae_days']:.4f} days; R2 {result['holdout_r2']:.6f}"
        )

    for outcome, result in payload.get("inference", {}).items():
        lines.extend(
            [
                "",
                f"Clustered sensitivity: {outcome}",
                "-" * (23 + len(outcome)),
                f"Rows: {result['n_rows']}; country clusters: {result['n_clusters']}",
                f"Control rank: {result.get('control_rank', 'not recorded')} / "
                f"{result.get('control_column_count', 'not recorded')} columns; "
                f"total parameter rank: {result.get('full_parameter_count', 'not recorded')}",
                f"Complete-case exclusions: {result.get('complete_case_excluded_rows', 'not recorded')}",
                "Dropped dependent/constant narrative columns: "
                f"{result.get('dropped_narrative_features', [])}",
                "",
                "Joint feature-family tests (BH within outcome; singular families unavailable):",
                result["joint_tests"].to_string(index=False),
                "",
                "Narrative coefficients (country-clustered; BH-FDR across retained terms):",
                result["coefficients"].to_string(index=False),
            ]
        )
    return "\n".join(lines) + "\n"


def write_sensitivity_outputs(payload: dict[str, object], output_dir: Path | str) -> dict[str, Path]:
    """Write a new snapshot with per-file atomic replacement.

    Existing result files are never overwritten. The three-file bundle is
    not a transaction; after an interrupted write choose a fresh directory.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    coefficient_frames = []
    for outcome, result in payload.get("inference", {}).items():
        table = result["coefficients"].copy()
        table.insert(0, "outcome", outcome)
        coefficient_frames.append(table)
    combined = pd.concat(coefficient_frames, ignore_index=True) if coefficient_frames else pd.DataFrame()

    paths = {
        "json": output_dir / "expanded_sensitivity.json",
        "coefficients": output_dir / "narrative_coefficients.csv",
        "report": output_dir / "expanded_sensitivity.txt",
    }
    existing = [path.name for path in paths.values() if path.exists()]
    if existing:
        raise FileExistsError(f"Refusing to overwrite an existing snapshot: {existing}")
    contents = {
        "json": json.dumps(_serializable(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        "coefficients": combined.to_csv(index=False),
        "report": _report_text(payload),
    }
    for key, final_path in paths.items():
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{final_path.name}.", dir=output_dir, text=True
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(contents[key])
            os.replace(temporary_name, final_path)
        except Exception:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise
    return paths


def run_expanded_sensitivity(
    df: pd.DataFrame,
    *,
    output_dir: Path | str,
    holdout_start: str = "2024-01-01",
    n_topics: int = 5,
) -> dict[str, object]:
    """Run all approved full-data checks and persist their results."""
    frame = build_sensitivity_frame(df)
    prediction = evaluate_nested_ridge(
        df,
        featured_frame=frame,
        holdout_start=holdout_start,
        n_topics=n_topics,
    )
    valid = frame.loc[frame["valid_completed_outcome"]].copy()
    inference = {}
    for outcome in ["log_funding_speed", "funded_within_24h"]:
        inference[outcome] = fit_clustered_partial_regression(
            valid,
            outcome=outcome,
            narrative_features=EXPANDED_NARRATIVE_FEATURES,
            numeric_controls=RICH_NUMERIC_CONTROLS,
            categorical_controls=RICH_CATEGORICAL_CONTROLS,
            cluster_col="country_name",
            feature_families=NARRATIVE_FEATURE_FAMILIES,
        )
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_scope": "expanded_feature_sensitivity_not_primary_specification",
        "prediction": prediction,
        "inference": inference,
    }
    write_sensitivity_outputs(payload, output_dir)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Path to Kiva pickle data")
    parser.add_argument("--output-dir", required=True, help="Directory for sensitivity results")
    parser.add_argument("--holdout-start", default="2024-01-01")
    parser.add_argument("--n-topics", type=int, default=5)
    args = parser.parse_args(argv)

    data = load_kiva_pickle(args.data)
    result = run_expanded_sensitivity(
        data,
        output_dir=args.output_dir,
        holdout_start=args.holdout_start,
        n_topics=args.n_topics,
    )
    print(_report_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
