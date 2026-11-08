import math

import pytest

from src.robustness_summary import ORDER, adjusted_passes, bootstrap_summary, evidence_funnel, framing_in_real_units, subgroup_summary
def test_bootstrap_counts_changes_against_screen():
    wild = {'results': {'expanded/log_funding_speed': {'draws': 9999, 'n_clusters': 48, 'weights': 'Webb', 'rows': [
        {'feature': 'family_mentions_per_100_words', 'equivalent_wcr': True, 'wcr_p_zero_bh': 0.4},
        {'feature': 'urgency_mentions_per_100_words', 'equivalent_wcr': False, 'wcr_p_zero_bh': 0.9},
        {'feature': 'basic_needs_mentions_per_100_words', 'equivalent_wcr': False, 'wcr_p_zero_bh': 0.2}]}}}
    screen = {('expanded', 'log_funding_speed', 'family_mentions_per_100_words'): True,
              ('expanded', 'log_funding_speed', 'urgency_mentions_per_100_words'): False,
              ('expanded', 'log_funding_speed', 'basic_needs_mentions_per_100_words'): True}
    out = bootstrap_summary(wild, screen)
    assert (out['verdicts'], out['unchanged'], out['bounded_in_screen'], out['bounded_survive']) == (3, 2, 2, 1)
    assert out['changed'][0]['term'] == 'basic_needs' and out['min_p_zero_bh'] == 0.2


def test_subgroup_grid_follows_fixed_order_and_flags_hypotheses():
    results = []
    for k, (group, level) in enumerate(ORDER):
        for outcome in ('log_funding_speed', 'funded_within_24h'):
            results.append({'group': group, 'level': level, 'outcome': outcome, 'terms': [
                {'feature': 'urgency_mentions_per_100_words', 'equivalent': k == 0, 'estimate': -0.09,
                 'p_zero': 0.002 if level == 'Asia' else 0.5}]})
    out = subgroup_summary({'results': results})
    duration = out['log_funding_speed']
    assert duration['subgroups'][0] == 'pre_pandemic' and duration['subgroups'][-1] == 'Africa'
    assert duration['grid']['urgency'] == [True] + [False] * 9
    assert duration['bounded_count'] == {'urgency': 1}
    assert [h['level'] for h in duration['hypotheses_unadjusted']] == ['Asia']
    assert out['tests'] == 20


def _row(feature, estimate, clustered, wild, adjusted):
    return {'feature': feature, 'estimate': estimate, 'p_t47': clustered, 'wcr_p_zero': wild, 'wcr_p_zero_bh': adjusted}


def test_evidence_funnel_counts_each_stage_below_the_threshold():
    wild = {'results': {'a/log_funding_speed': {'rows': [_row('x', 0, .01, .02, .2), _row('y', 0, .03, .07, .3)]},
                        'b/funded_within_24h': {'rows': [_row('x', 0, .5, .5, .9)]}}}
    assert evidence_funnel(wild) == {'tests': 3, 'clustered': 2, 'bootstrap': 1, 'adjusted': 0}


def test_framing_in_real_units_converts_and_measures_the_shrink():
    third = 'third_person_mentions_per_100_words'
    business = 'business_mentions_per_100_words'
    wild = {'results': {'expanded/log_funding_speed': {'rows': [_row(third, -0.01, 0, 0, 0)]},
                        'programme_adjusted/log_funding_speed': {'rows': [_row(third, -0.008, 0, 0, 0)]},
                        'expanded/funded_within_24h': {'rows': [_row(business, -0.004, 0, 0, 0)]},
                        'programme_adjusted/funded_within_24h': {'rows': [_row(business, -0.003, 0, 0, 0)]}}}
    shares = {third: {'share_zero': 0.1}, business: {'share_zero': 0.25}}
    out = framing_in_real_units(wild, shares, median_days=3.0)
    assert out['third_person']['minutes_expanded'] == pytest.approx(4 * (1 - math.exp(-0.01)) * 1440)
    assert out['third_person']['shrink_share'] == pytest.approx(0.2)
    assert out['third_person']['share_with_mention'] == pytest.approx(0.9)
    assert out['business']['pp_expanded'] == pytest.approx(-0.4)
    assert out['business']['pp_programme_adjusted'] == pytest.approx(-0.3)
    assert out['business']['shrink_share'] == pytest.approx(0.25)


def test_adjusted_passes_reports_each_pass_with_its_programme_adjusted_result_and_the_next_lowest():
    third = 'third_person_mentions_per_100_words'
    wild = {'results': {'expanded/log_funding_speed': {'rows': [_row(third, -0.009, 0.001, 0.0009, 0.008), _row('x', 0, .5, .5, .156)]},
                        'programme_adjusted/log_funding_speed': {'rows': [_row(third, -0.008, 0.003, 0.128, 0.426), _row('x', 0, .5, .5, .9)]}}}
    out = adjusted_passes(wild)
    assert [(p['specification'], p['outcome'], p['term']) for p in out['passes']] == [('expanded', 'log_funding_speed', 'third_person')]
    assert out['passes'][0]['pct_change_in_1_plus_days'] == pytest.approx((math.exp(-0.009) - 1) * 100)
    assert out['passes'][0]['p_zero_bh'] == 0.008 and out['passes'][0]['programme_adjusted_p_zero_bh'] == 0.426
    assert out['passes'][0]['programme_adjusted_p_zero'] == 0.128 and out['lowest_other_p_zero_bh'] == 0.156
