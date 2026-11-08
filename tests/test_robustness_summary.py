from src.robustness_summary import ORDER, bootstrap_summary, subgroup_summary


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
