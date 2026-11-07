import pandas as pd

from src.period_trend import yearly_share


def test_yearly_share_counts_only_eligible_records():
    frame = pd.DataFrame({'valid_completed_outcome': [True, True, True, False],
                          'fundraising_year': [2016, 2016, 2017, 2017],
                          'funded_within_24h': [1, 0, 1, 1]})
    rows = yearly_share(frame)
    assert rows == [{'year': 2016, 'records': 2, 'funded_within_24h': 1, 'share_within_24h': .5},
                    {'year': 2017, 'records': 1, 'funded_within_24h': 1, 'share_within_24h': 1.0}]
