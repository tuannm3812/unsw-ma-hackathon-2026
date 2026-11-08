import pytest

from src.appendix_summary import (flag_margin, larger_tree_with_text, model_rows, purpose_contrasts, sector_same_day,
                                  theme_rows, tuned_summary)


def _m(year, family, arm, mae, auc):
    return {'year': year, 'family': family, 'arm': arm, 'metrics': {'mae_days': mae, 'roc_auc': auc}}


def test_model_rows_keeps_order_and_auc_range():
    bench = {'models': [_m(y, 'baseline', 'B0', 10 - i, .5) for i, y in enumerate((2021, 2022))] +
                       [_m(y, 'baseline', 'B1', 9, .6 + i / 10) for i, y in enumerate((2021, 2022))]}
    large = {'windows': [{'year': 2021, 'arm': 'S', 'mae_days': 7.0, 'roc_auc': .8}, {'year': 2022, 'arm': 'S', 'mae_days': 6.0, 'roc_auc': .9}]}
    rows = model_rows(bench, large, (('Median', 'baseline', 'B0'), ('Lookup', 'baseline', 'B1')))
    assert [r['name'] for r in rows] == ['Median', 'Lookup', 'Larger boosted tree']
    assert rows[0]['mae'] == {'2021': 10, '2022': 9}
    assert rows[1]['auc_range'] == pytest.approx([.6, .7])
    assert rows[2]['mae']['2022'] == 6.0


def _c(level, n, pct):
    return {'group': 'activity', 'level': level, 'records': n, 'pct_change_in_1_plus_days': pct, 'pct_ci95': [pct - 1, pct + 1], 'p_t47': .01}


def test_purpose_contrasts_ranks_large_activities_and_keeps_sanitation():
    outcome = {'categories': [_c('Tiny', 5, -90), _c('Toilets & Sanitation Systems', 6000, -5), _c('School', 2000, -70), _c('Shop', 3000, 40),
                              {'group': 'gender_classification', 'level': 'male', 'records': 9, 'pct_change_in_1_plus_days': 1, 'pct_ci95': [0, 2], 'p_t47': .1}],
               'sector_contrasts': [{'sector': 'B', 'records': 9, 'pct_change_in_1_plus_days': 5, 'pct_ci95': [1, 9]},
                                    {'sector': 'A', 'records': 8, 'pct_change_in_1_plus_days': -5, 'pct_ci95': [-9, -1]}]}
    out = purpose_contrasts(outcome, keep=1, min_records=1000)
    assert [s['sector'] for s in out['sectors']] == ['A', 'B']
    assert out['fastest'][0]['level'] == 'School' and out['slowest'][0]['level'] == 'Shop'
    assert out['sanitation']['level'] == 'Toilets & Sanitation Systems' and out['activities_ranked'] == 3


def test_sector_outcome_reads_same_day_points():
    outcome = {'sector_contrasts': [{'sector': 'Sanitation & Hygiene', 'records': 9, 'estimate': 0.088, 'ci95': [0.063, 0.112]}]}
    out = sector_same_day(outcome, 'Sanitation & Hygiene')
    assert out['pp'] == pytest.approx(8.8) and out['ci95_pp'] == pytest.approx([6.3, 11.2]) and out['records'] == 9


def test_model_rows_appends_extra_models_after_the_larger_tree():
    bench = {'models': [_m(2021, 'baseline', 'B0', 10, .5), _m(2021, 'linear', 'T', 9, .7)]}
    large = {'windows': [{'year': 2021, 'arm': 'S', 'mae_days': 7.0, 'roc_auc': .8}]}
    rows = model_rows(bench, large, (('Median', 'baseline', 'B0'),), (('Text only', 'linear', 'T'),))
    assert [r['name'] for r in rows] == ['Median', 'Larger boosted tree', 'Text only']


def _year(year, compact, large, hgb, xgb):
    mae = {'compact_fixed_S': compact, 'large_fixed_S': large, 'hgb_tuned_S': hgb, 'xgb_tuned_S': xgb,
           'hgb_tuned_S+M+L+D': hgb - .1, 'xgb_tuned_S+M+L+D': xgb - .2}
    gains = [{'family': f, 'candidate': c, 'unit': u, 'gain': g, 'interval_95': [g - .1, g + .1]}
             for f, g in (('hgb', .1), ('xgb', .2)) for c in ('S+M+L', 'S+M+L+D') for u in ('month', 'country')]
    margin = {'compact_fixed_S': {'lift': [.2, 1.1], 'within': [.1, .3]}}
    return {'year': year, 'mae': mae, 'text_gain': gains, 'test_rows': 10,
            'tuning': {'hgb': {'params': {'a': 1}}, 'xgb': {'params': {'b': 2}}, 'hgb_trials': [{}, {}], 'xgb_trials': [{}, {}]},
            'triage': {'models': {'compact_fixed_S': {'top_10': {'lift': 2.6, 'precision': .5},
                                                      'within_country_median_precision_top_10': .52}},
                       'minus_lookup_95': {'month_block': margin,
                                           'country_block_lift_only': {'compact_fixed_S': {'lift': [.08, 1.2], 'within': [9, 9]}}}}}


def test_tuned_summary_compares_best_fixed_with_best_tuned():
    out = tuned_summary({'xgboost_version': '3', 'years': [_year(2021, 7.5, 8.0, 8.1, 8.2), _year(2022, 6.0, 6.1, 5.9, 5.8)]})
    assert [r['name'] for r in out['rows']][0] == 'Tuned tree, loan details'
    assert out['rows'][3]['mae'] == pytest.approx({'2021': 8.0, '2022': 5.6})
    assert [v['tuned_lower_by'] for v in out['versus_fixed']] == pytest.approx([-.6, .2])
    assert [v['xgb_below_tuned_tree'] for v in out['versus_fixed']] == [False, True]
    assert len(out['text_gains']) == 4 and out['text_gains'][1]['family'] == 'xgb'
    assert out['text_gains'][1]['country_95'] == pytest.approx([.1, .3])
    assert out['trials_per_family'] == 2


def test_flag_margin_keeps_month_and_country_ranges_apart():
    row = flag_margin({'years': [_year(2021, 7.5, 8.0, 8.1, 8.2)]})[0]
    assert row['lift'] == 2.6 and row['within'] == .52
    assert row['lift_margin_month_95'] == [.2, 1.1] and row['lift_margin_country_95'] == [.08, 1.2]
    assert 'within_margin_country_95' not in row


def test_larger_tree_with_text_uses_full_text_arm():
    row = larger_tree_with_text({'windows': [{'year': 2021, 'arm': 'S', 'mae_days': 8, 'roc_auc': .8},
                                             {'year': 2021, 'arm': 'S+M+L+D', 'mae_days': 7.9, 'roc_auc': .85}]})
    assert row['mae'] == {'2021': 7.9} and row['auc_range'] == [.85, .85]


def test_theme_rows_label_and_sort_by_raw_speed():
    def theme(words, days, pct):
        adj = {'pct_change_in_1_plus_days': pct, 'pct_ci95': [pct - 1, pct + 1], 'p': .5}
        return {'top_words': words, 'n': 5, 'mean_days': days, 'median_days': days, 'adjusted_loan_details': adj,
                'adjusted_plus_activity': adj}
    rows = theme_rows({'themes': [theme(['business', 'nwtf', 'philippines'], 8, 6), theme(['sanitary', 'toilet'], 1.5, -17)]})
    assert [r['label'] for r in rows] == ['Sanitary and toilets', 'Philippines business']
    assert rows[0]['adjusted']['ci95'] == [-18, -16]
