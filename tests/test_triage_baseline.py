import numpy as np

from src.triage_baseline import break_ties


def test_break_ties_keeps_score_order_and_is_a_permutation():
    score = np.array([1.0, 3.0, 3.0, 2.0, 1.0])
    ranks = break_ties(score, np.random.default_rng(0))
    assert sorted(ranks) == [0, 1, 2, 3, 4]
    assert max(ranks[[0, 4]]) < ranks[3] < min(ranks[[1, 2]])
