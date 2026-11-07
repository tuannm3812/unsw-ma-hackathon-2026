import numpy as np
import pytest

from src.feature_distribution import per_sd, summarise


def test_summarise_ignores_missing_and_counts_zeros():
    stats = summarise([0.0, 0.0, 2.0, 4.0, np.nan])
    assert stats['rows'] == 5 and stats['observed_rows'] == 4
    assert stats['mean'] == 1.5
    assert stats['share_zero'] == .5
    assert stats['mean_nonzero'] == 3
    assert stats['sd'] == pytest.approx(np.std([0, 0, 2, 4], ddof=1))


def test_per_sd_scales_a_rate_term_by_its_sd():
    row = {'specification': 'expanded', 'outcome': 'log_funding_speed',
           'feature': 'urgency_mentions_per_100_words', 'estimate': '-0.05',
           'ci90_low': '-0.13', 'ci90_high': '0.03'}
    result = per_sd(row, {'sd': .2})
    assert result['estimate_per_sd'] == pytest.approx(-.01)
    assert result['ci90_low_per_sd'] == pytest.approx(-.026)
    assert result['inside_primary_bound_per_sd'] is True
    assert result['bound_equivalent_per_sd'] == pytest.approx(.01)


def test_per_sd_uses_the_half_point_edit_unit_for_sentiment():
    row = {'specification': 'expanded', 'outcome': 'funded_within_24h',
           'feature': 'desc_sentiment_compound', 'estimate': '0.01',
           'ci90_low': '0.0', 'ci90_high': '0.02'}
    result = per_sd(row, {'sd': .25})
    assert result['sd_per_edit_unit'] == .5
    assert result['ci90_high_per_sd'] == pytest.approx(.01)
    assert result['primary_bound'] == .01
