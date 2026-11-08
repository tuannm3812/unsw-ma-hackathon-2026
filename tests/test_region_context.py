import json

import pytest

from src import region_context


def test_percent_change_converts_log_points():
    assert region_context.percent_change(0) == 0
    assert region_context.percent_change(-0.0729) == pytest.approx(-7.03, abs=0.01)


def test_region_context_counts_countries_and_shares(tmp_path):
    shares = [{'country': 'PS', 'region': 'Middle East', 'loans': 97},
              {'country': 'YE', 'region': 'Middle East', 'loans': 3},
              {'country': 'KE', 'region': 'Africa', 'loans': 50},
              {'country': 'UG', 'region': 'Africa', 'loans': 30},
              {'country': 'TG', 'region': 'Africa', 'loans': 20}]
    path = tmp_path / 'country_shares.json'
    path.write_text(json.dumps({'shares': shares}))
    result = region_context.build(path)['regions']
    assert list(result) == ['Africa', 'Middle East']
    assert result['Middle East']['countries'] == 2 and result['Middle East']['loans'] == 100
    assert result['Middle East']['country_shares'][0] == {'country': 'PS', 'loans': 97, 'share_of_region': 0.97}
