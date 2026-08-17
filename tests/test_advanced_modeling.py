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
