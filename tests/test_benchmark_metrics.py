import numpy as np
import pytest


def test_metrics_and_reliability_keep_single_class_visible():
    from src.benchmark_metrics import score_predictions, reliability_bins
    y = np.ones(8)
    scores = score_predictions(y, y, y, np.full(8,.75))
    assert scores['mae_days'] == 0
    assert scores['roc_auc'] is None
    assert scores['average_precision'] is None
    assert scores['brier'] == .0625
    bins = reliability_bins(y, np.full(8,.75))
    assert sum(b['count'] for b in bins) == 8
    assert next(b['observed_rate'] for b in bins if b['count']) == 1


def test_paired_cluster_interval_uses_paired_weighted_losses():
    from src.benchmark_metrics import paired_loss_intervals
    base = np.array([2.,4.,8.,2.,6.])
    new = base - 1.5
    result = paired_loss_intervals(base,new,np.array(['a','a','b','c','c']),resamples=100)
    assert result['gain'] == 1.5
    assert result['interval_95'] == pytest.approx([1.5,1.5])
    assert result['clusters'] == 3
    with pytest.raises(ValueError,match='same length'):
        paired_loss_intervals(base,new[:-1],np.array(['a']*5))


def test_nonfinite_predictions_are_rejected():
    from src.benchmark_metrics import score_predictions
    with pytest.raises(ValueError,match='finite'):
        score_predictions(np.ones(2),np.ones(2),np.array([1.,np.inf]),np.ones(2))
