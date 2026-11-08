import numpy as np

from src.triage_value import calibration_deciles, flag_top, slow_target, triage_metrics


def test_perfect_ranker_has_full_precision_and_lift_five():
    days = np.arange(100, dtype=float)
    m = triage_metrics(days, slow_target(days), 0.10)
    assert m["flagged"] == 10 and m["precision"] == 1.0
    assert abs(m["lift"] - 1 / 0.2) < 0.01
    assert abs(m["recall"] - 10 / 20) < 1e-9


def test_flag_top_counts_and_calibration_bins():
    score = np.random.default_rng(0).normal(size=1000)
    assert flag_top(score, 0.2).sum() == 200
    bins = calibration_deciles(np.zeros(1000), np.linspace(0, 1, 1000))
    assert sum(b["rows"] for b in bins) == 1000 and len(bins) == 10


def test_month_bootstrap_reselects_capacity_each_draw():
    from src.triage_value import month_bootstrap
    days = np.arange(200, dtype=float)
    months = np.array(["a", "b"] * 100)
    low, high = month_bootstrap(days, days, days, months, draws=50)
    assert low == 0.0 and high == 0.0
