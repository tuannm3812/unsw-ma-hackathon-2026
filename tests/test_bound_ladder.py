import csv
import json

import pytest

from src import bound_ladder


def test_tightest_bound_prefers_smallest_held():
    assert bound_ladder.tightest_bound(True, {'0.02': True, '0.1': True}) == 0.02
    assert bound_ladder.tightest_bound(True, {'0.02': False, '0.1': True}) == 0.05
    assert bound_ladder.tightest_bound(False, {'0.02': False, '0.1': True}) == 0.10
    assert bound_ladder.tightest_bound(False, {'0.02': False, '0.1': False}) is None


def test_hours_at_median_is_asymmetric_and_scaled():
    shorter, longer = bound_ladder.hours_at_median(0.05, median_days=2.85)
    assert shorter == pytest.approx(3.85 * (1 - 2.718281828 ** -0.05) * 24, rel=1e-6)
    assert longer == pytest.approx(3.85 * (2.718281828 ** 0.05 - 1) * 24, rel=1e-6)
    assert shorter < longer


def test_build_reads_duration_rows_only(tmp_path):
    fields = ['specification', 'outcome', 'feature', 'equivalent', 'equivalent_at_sensitivity_bounds']
    rows = [
        ['expanded', 'log_funding_speed', 'family_mentions_per_100_words', 'True', '{"0.02": true, "0.1": true}'],
        ['expanded', 'log_funding_speed', 'urgency_mentions_per_100_words', 'False', '{"0.02": false, "0.1": false}'],
        ['expanded', 'log_funding_speed', 'desc_sentiment_compound', 'False', '{"0.02": false, "0.1": true}'],
        ['expanded', 'funded_within_24h', 'family_mentions_per_100_words', 'False', '{"0.02": false, "0.1": false}'],
    ]
    with (tmp_path / 'equivalence_screen.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        writer.writerows(rows)
    (tmp_path / 'feature_distribution.json').write_text(json.dumps(
        {'features': {'urgency_mentions_per_100_words': {'share_zero': 0.98697},
                      'desc_sentiment_compound': {'share_zero': 0.0336}}}))
    result = bound_ladder.build(tmp_path)
    assert result['tightest_bound'] == {'expanded': {'family': 0.02, 'urgency': None, 'sentiment': 0.10}}
    assert result['terms_equivalent_by_bound'] == {'expanded': {'0.02': 1, '0.05': 1, '0.1': 2}}
    assert result['share_no_mention'] == {'urgency': 0.987, 'sentiment': 0.0336}
    assert result['bound_percent_of_one_plus_days']['0.05'] == pytest.approx(5.13)
