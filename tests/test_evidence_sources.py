import pandas as pd
import pytest

from src.evidence_sources import (
    TERMS, clusters_for_share, effective_clusters, few_cluster_screen, leave_one_out, slice_gains,
    term_concentration,
)


def test_effective_clusters_equal_shares_and_concentration():
    assert effective_clusters([5, 5, 5, 5]) == pytest.approx(4)
    assert effective_clusters([97, 1, 1, 1]) < 1.1


def test_clusters_for_share_counts_largest_first():
    assert clusters_for_share([10, 70, 20], .8) == 2


def test_slice_gains_pairs_groups_and_skips_suppressed():
    base = [{'dimension': 'country', 'group': 'A', 'rows': 10, 'suppressed': False, 'mae_days': 5.0},
            {'dimension': 'country', 'group': 'B', 'rows': 2, 'suppressed': True}]
    new = [{'dimension': 'country', 'group': 'A', 'rows': 10, 'suppressed': False, 'mae_days': 4.0},
           {'dimension': 'country', 'group': 'B', 'rows': 2, 'suppressed': True}]
    rows = slice_gains(base, new, 'country')
    assert rows == [{'group': 'A', 'rows': 10, 'gain_days': 1.0, 'gain_total_days': 10.0}]


def test_leave_one_out_removes_a_group_from_the_mean():
    rows = [{'group': 'A', 'rows': 10, 'gain_total_days': 10.0}]
    assert leave_one_out(rows, 12.0, 20)[0]['gain_without'] == pytest.approx(.2)


def test_term_concentration_ignores_ineligible_records():
    data = {term: [1.0, 0.0, 1.0] for term in TERMS}
    frame = pd.DataFrame({'valid_completed_outcome': [True, True, False],
                          'country_iso': ['A', 'B', 'C'], **data})
    result = term_concentration(frame)
    assert result['countries'] == 2
    assert result['terms'][TERMS[0]]['countries_using_term'] == 1


def test_few_cluster_screen_widens_intervals_and_can_lose_a_verdict():
    rows = [{'specification': 'expanded', 'outcome': 'log_funding_speed', 'feature': 'a',
             'estimate': '0.0', 'standard_error': '0.025', 'bound': '0.05', 'equivalent': 'True'}]
    wide, narrow = few_cluster_screen(rows, 4)[0], few_cluster_screen(rows, 47)[0]
    assert wide['ci90_high'] > narrow['ci90_high']
    assert narrow['bounded']
    assert not wide['bounded']
