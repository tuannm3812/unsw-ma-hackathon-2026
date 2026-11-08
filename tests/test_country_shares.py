import pandas as pd
import pytest

from src.country_shares import country_shares


def test_country_shares_sorted_and_eligible_only():
    frame = pd.DataFrame({'valid_completed_outcome': [True, True, True, False],
                          'country_iso': ['A', 'A', 'B', 'B']})
    result = country_shares(frame)
    assert result['records'] == 3
    assert result['shares'][0] == {'country': 'A', 'share': pytest.approx(2 / 3)}
