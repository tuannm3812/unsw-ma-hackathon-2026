import pandas as pd
import pytest

from src.country_shares import country_shares


def test_country_shares_sorted_and_eligible_only():
    frame = pd.DataFrame({'valid_completed_outcome': [True, True, True, False],
                          'country_iso': ['A', 'A', 'B', 'B'], 'funded_within_24h': [1, 0, 1, 1]})
    result = country_shares(frame)
    assert result['records'] == 3
    first = result['shares'][0]
    assert first['country'] == 'A' and first['loans'] == 2
    assert first['share'] == pytest.approx(2 / 3) and first['same_day_share'] == pytest.approx(.5)
