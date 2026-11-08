import pytest

from src.loan_detail_summary import ROW_ORDER, summarise


def _row(term, pct, low, high, unit='u'):
    return {'term': term, 'unit': unit, 'pct_change_in_1_plus_days': pct, 'pct_ci95': [low, high]}


def _data():
    framing = [_row(t, 1.0, -1, 2) for t in ROW_ORDER['framing']]
    numeric = [_row('log_loan_amount', 44.0, 30, 58), _row('lenderRepaymentTerm', 8.0, 2, 15),
               _row('borrowerCount', -1.0, -2, 1), _row('is_group_loan', 5.0, -18, 35)]
    categories = [_row('gender_classification__male', 60.0, 40, 80), _row('loan_size_band_small', 9.0, 1, 2)]
    return {'outcomes': {'log_funding_speed': {'framing': framing, 'numeric': numeric, 'categories': categories}}}


def test_summary_keeps_only_the_named_rows_and_leaves_out_size_bands():
    out = summarise(_data())
    assert [r['term'] for r in out['loan_details']] == ['log_loan_amount', 'lenderRepaymentTerm',
                                                        'gender_classification__male', 'borrowerCount']
    assert len(out['framing']) == 9
    assert not any('size_band' in r['term'] for r in out['loan_details'])


def test_summary_reports_largest_mention_rate_estimate_and_no_ratio():
    data = _data()
    data['outcomes']['log_funding_speed']['framing'][1]['pct_change_in_1_plus_days'] = -1.4
    out = summarise(data)
    assert out['largest_mention_rate_estimate'] == pytest.approx(1.4)
    assert 'ratio' not in str(out).lower()
