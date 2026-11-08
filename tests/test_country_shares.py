import pandas as pd
import pytest

from src.country_shares import country_shares


def test_country_shares_sorted_and_eligible_only():
    frame = pd.DataFrame({'valid_completed_outcome': [True, True, True, False],
                          'country_iso': ['A', 'A', 'B', 'B'], 'funded_within_24h': [1, 0, 1, 1],
                          'region': ['Asia', 'Asia', 'Africa', 'Africa']})
    result = country_shares(frame)
    assert result['records'] == 3
    first = result['shares'][0]
    assert first['country'] == 'A' and first['loans'] == 2
    assert first['share'] == pytest.approx(2 / 3) and first['same_day_share'] == pytest.approx(.5)


def test_country_shares_reports_region_and_region_shares():
    frame = pd.DataFrame({'valid_completed_outcome': [True, True, True],
                          'country_iso': ['A', 'A', 'B'], 'funded_within_24h': [1, 0, 1],
                          'region': ['Asia', 'Asia', 'Africa']})
    result = country_shares(frame)
    assert [row['region'] for row in result['shares']] == ['Asia', 'Africa']
    assert result['region_shares'] == pytest.approx({'Asia': 2 / 3, 'Africa': 1 / 3})


def test_country_in_two_regions_is_rejected():
    frame = pd.DataFrame({'valid_completed_outcome': [True, True], 'country_iso': ['A', 'A'],
                          'funded_within_24h': [1, 0], 'region': ['Asia', 'Africa']})
    with pytest.raises(ValueError):
        country_shares(frame)


def test_country_shares_adds_long_waits_when_days_present():
    frame = pd.DataFrame({'valid_completed_outcome': [True] * 4, 'country_iso': ['A', 'A', 'A', 'B'],
                          'funded_within_24h': [1, 0, 0, 0], 'region': ['Asia'] * 3 + ['Africa'],
                          'funding_speed_days': [0.5, 20.0, 30.0, 15.0]})
    result = country_shares(frame)
    first, second = result['shares']
    assert first['records_over_14_days'] == 2 and first['share_over_14_days'] == pytest.approx(2 / 3)
    assert first['median_days'] == 20.0
    assert (first['records_within_24h'], first['records_1_to_14_days'], first['records_over_14_days']) == (1, 0, 2)
    assert result['records_over_14_days'] == 3
    assert first['share_of_all_long_waits'] == pytest.approx(2 / 3)
    assert second['share_of_all_long_waits'] == pytest.approx(1 / 3)
