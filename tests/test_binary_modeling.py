import numpy as np
import pytest
from sklearn.metrics import average_precision_score

from src.binary_modeling import evaluate_chronological_binary_classifier
from src.validation import InsufficientDataError


def test_binary_classifier_returns_holdout_metrics(large_synthetic_kiva_df):
    result = evaluate_chronological_binary_classifier(
        large_synthetic_kiva_df, holdout_start="2024-01-01", n_topics=2,
    )
    metrics = result["metrics"]
    assert result["train_rows"] > 0
    assert result["holdout_rows"] > 0
    assert set(metrics) == {
        "roc_auc", "average_precision", "brier_score", "holdout_accuracy",
        "single_class_holdout", "holdout_class_balance",
    }
    assert 0.0 <= metrics["brier_score"] <= 1.0
    assert 0.0 <= metrics["holdout_accuracy"] <= 1.0


def test_binary_classifier_reports_roc_and_average_precision_when_holdout_has_both_classes(large_synthetic_kiva_df):
    result = evaluate_chronological_binary_classifier(
        large_synthetic_kiva_df, holdout_start="2024-01-01", n_topics=2,
    )
    metrics = result["metrics"]
    assert metrics["single_class_holdout"] is False
    assert metrics["roc_auc"] is not None
    assert metrics["average_precision"] is not None
    assert 0.0 <= metrics["roc_auc"] <= 1.0
    assert 0.0 <= metrics["average_precision"] <= 1.0


def test_binary_classifier_average_precision_matches_sklearns_definition_exactly(large_synthetic_kiva_df):
    # Regression test for a real mislabeling bug: this project's
    # `average_precision` field must be exactly
    # `sklearn.metrics.average_precision_score`, not the trapezoidal area
    # under the precision-recall curve (`sklearn.metrics.auc(recall,
    # precision)`) - the two are related but numerically different
    # (confirmed on the real Kiva sample: 0.7882 vs. 0.7689). Recomputes
    # average precision directly from the fitted classifier's own holdout
    # predictions and asserts an exact match, so a future swap to a
    # different precision-recall summary would fail this test rather than
    # silently drift from what the field name promises.
    result = evaluate_chronological_binary_classifier(
        large_synthetic_kiva_df, holdout_start="2024-01-01", n_topics=2,
    )
    classifier = result["_artifacts"]["binary_classifier"]
    X_holdout = result["_artifacts"]["X_holdout"]
    y_holdout = result["_artifacts"]["y_holdout_binary"]
    holdout_pred_proba = classifier.predict_proba(X_holdout)[:, 1]
    expected = float(average_precision_score(y_holdout, holdout_pred_proba))
    assert result["metrics"]["average_precision"] == pytest.approx(expected)


def test_binary_classifier_degrades_gracefully_on_single_class_holdout(large_synthetic_kiva_df, monkeypatch):
    # With only one class in y_true, ROC AUC is mathematically undefined
    # (roc_auc_score itself returns nan), but average_precision_score is
    # not undefined in the same sense - it returns a real, technically
    # valid number (1.0/0.0) that is trivial, determined only by the
    # class balance rather than the classifier. Force exactly this (an
    # all-1s holdout target) and confirm both are still omitted as a
    # labeled diagnostic - ROC AUC because it is undefined, average
    # precision because it would be uninformative - rather than letting
    # roc_auc_score raise an opaque ValueError or reporting the
    # meaningless average-precision number as if it were real. Brier
    # score and accuracy remain well-defined and informative regardless,
    # so they must still be reported.
    import src.binary_modeling as binary_modeling_module

    real_prepare = binary_modeling_module.prepare_chronological_matrices

    def _single_class_holdout(*args, **kwargs):
        matrices = real_prepare(*args, **kwargs)
        matrices["_artifacts"]["y_holdout_binary"] = np.ones_like(
            matrices["_artifacts"]["y_holdout_binary"]
        )
        return matrices

    monkeypatch.setattr(binary_modeling_module, "prepare_chronological_matrices", _single_class_holdout)

    result = evaluate_chronological_binary_classifier(
        large_synthetic_kiva_df, holdout_start="2024-01-01", n_topics=2,
    )
    metrics = result["metrics"]
    assert metrics["single_class_holdout"] is True
    assert metrics["roc_auc"] is None
    assert metrics["average_precision"] is None
    assert metrics["brier_score"] is not None
    assert 0.0 <= metrics["holdout_accuracy"] <= 1.0


def test_binary_classifier_raises_insufficient_data_on_single_class_training(large_synthetic_kiva_df, monkeypatch):
    # A classifier cannot be fit at all on a training partition with only
    # one class present - this must raise a clear diagnostic, not an
    # opaque sklearn error, mirroring how prepare_chronological_matrices
    # itself raises InsufficientDataError for an unusably small split.
    import src.binary_modeling as binary_modeling_module

    real_prepare = binary_modeling_module.prepare_chronological_matrices

    def _single_class_training(*args, **kwargs):
        matrices = real_prepare(*args, **kwargs)
        matrices["_artifacts"]["y_train_binary"] = np.zeros_like(
            matrices["_artifacts"]["y_train_binary"]
        )
        return matrices

    monkeypatch.setattr(binary_modeling_module, "prepare_chronological_matrices", _single_class_training)

    with pytest.raises(InsufficientDataError, match="both funded_within_24h classes"):
        evaluate_chronological_binary_classifier(
            large_synthetic_kiva_df, holdout_start="2024-01-01", n_topics=2,
        )


def test_binary_classifier_shares_the_same_split_as_the_continuous_benchmarks(large_synthetic_kiva_df):
    # This module must reuse prepare_chronological_matrices, not re-derive
    # its own split - confirmed here by checking its reported train/holdout
    # row counts exactly match evaluate_chronological_models's (the linear
    # baseline) on the same inputs.
    from src.modeling import evaluate_chronological_models

    binary_result = evaluate_chronological_binary_classifier(
        large_synthetic_kiva_df, holdout_start="2024-01-01", n_topics=2,
    )
    continuous_result = evaluate_chronological_models(
        large_synthetic_kiva_df, holdout_start="2024-01-01", n_topics=2,
    )
    assert binary_result["train_rows"] == continuous_result["train_rows"]
    assert binary_result["holdout_rows"] == continuous_result["holdout_rows"]
