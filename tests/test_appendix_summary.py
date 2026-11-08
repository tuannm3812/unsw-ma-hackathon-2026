import pytest

from src.appendix_summary import model_rows, purpose_contrasts, sector_same_day


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
