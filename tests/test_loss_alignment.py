import numpy as np
import pytest

from src.loss_alignment import (
    duan_smearing_factor, duration_scores, error_anatomy, smeared_days,
)


def test_smearing_factor_is_mean_exponentiated_residual():
    y = np.array([1.0, 2.0, 3.0])
    pred = np.array([1.0, 1.0, 4.0])
    assert duan_smearing_factor(y, pred) == pytest.approx((1 + np.e + np.exp(-1)) / 3)


def test_smearing_recovers_lognormal_mean_where_expm1_undershoots():
    rng = np.random.default_rng(42)
    log_target = rng.normal(2.0, 1.0, 200_000)
    pred = np.full_like(log_target, 2.0)
    true_mean = np.expm1(log_target).mean()
    factor = duan_smearing_factor(log_target, pred)
    assert smeared_days(pred, factor).mean() == pytest.approx(true_mean, rel=.02)
    assert np.expm1(pred).mean() < .7 * true_mean


def test_smeared_days_clip_at_zero():
    assert smeared_days(np.array([-5.0]), 1.0)[0] == 0


def test_smearing_factor_rejects_mismatched_arrays():
    with pytest.raises(ValueError):
        duan_smearing_factor([1.0], [1.0, 2.0])


def test_duration_scores_match_hand_values():
    scores = duration_scores([0.0, 2.0], [1.0, 2.0])
    assert scores['mae_days'] == .5
    assert scores['bias_days'] == .5
    assert scores['r2_days'] == pytest.approx(.5)


def test_error_anatomy_attributes_squared_error_to_overprediction():
    anatomy = error_anatomy([1.0, 1.0, 1.0, 4.0], [1.0, 1.0, 11.0, 3.0])
    assert anatomy['share_squared_error_overprediction'] == pytest.approx(100 / 101)
    assert anatomy['predictions_above_observed_max'] == 1
