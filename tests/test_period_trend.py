import pandas as pd

from src.period_trend import yearly_share


def test_yearly_share_counts_only_eligible_records():
    frame = pd.DataFrame({'valid_completed_outcome': [True, True, True, False],
                          'fundraising_year': [2016, 2016, 2017, 2017],
                          'funded_within_24h': [1, 0, 1, 1]})
    rows = yearly_share(frame)
    assert rows == [{'year': 2016, 'records': 2, 'funded_within_24h': 1, 'share_within_24h': .5},
                    {'year': 2017, 'records': 1, 'funded_within_24h': 1, 'share_within_24h': 1.0}]


def test_yearly_share_adds_median_and_long_waits_when_days_present():
    frame = pd.DataFrame({'valid_completed_outcome': [True, True, True, True],
                          'fundraising_year': [2016, 2016, 2016, 2017],
                          'funded_within_24h': [1, 0, 0, 0],
                          'funding_speed_days': [0.5, 3.0, 20.0, 15.0]})
    rows = yearly_share(frame)
    assert rows[0]['median_days'] == 3.0
    assert rows[0]['share_over_14_days'] == 1 / 3 and rows[0]['records_over_14_days'] == 1
    assert rows[1]['share_over_14_days'] == 1.0
