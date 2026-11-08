import json

from src import gain_intervals


def _row(year, family, candidate, unit, low, high, gain=0.3):
    return {'year': year, 'family': family, 'baseline': 'S', 'candidate': candidate, 'metric': 'mae_days',
            'resampling_unit': unit, 'gain': gain, 'interval_95': [low, high]}


def test_paired_intervals_keeps_full_text_arm_only():
    rows = [_row(2021, 'linear', 'S+M+L+R', 'calendar_month', 0.2, 0.4),
            _row(2021, 'linear', 'S+M+L+R', 'country', -0.1, 0.5),
            _row(2021, 'linear', 'S+M', 'country', 0.0, 0.1),
            _row(2021, 'histogram_boosting', 'S+M+L', 'calendar_month', -0.07, 0.14, gain=0.035)]
    result = gain_intervals.paired_intervals(rows)
    assert result['linear'][2021] == {'gain': 0.3, 'month': [0.2, 0.4], 'country': [-0.1, 0.5]}
    assert result['histogram_boosting'][2021]['month'] == [-0.07, 0.14]


def test_includes_zero_is_inclusive():
    assert gain_intervals.includes_zero([-0.1, 0.2])
    assert gain_intervals.includes_zero([0.0, 0.2])
    assert not gain_intervals.includes_zero([0.01, 0.2])


def test_build_counts_zero_crossings(tmp_path):
    bench = tmp_path / 'benchmark.json'
    bench.write_text(json.dumps({'paired_comparisons': [
        _row(2021, 'linear', 'S+M+L+R', 'calendar_month', 0.2, 0.4),
        _row(2021, 'linear', 'S+M+L+R', 'country', -0.1, 0.5),
        _row(2021, 'histogram_boosting', 'S+M+L', 'calendar_month', -0.07, 0.14),
        _row(2021, 'histogram_boosting', 'S+M+L', 'country', 0.005, 0.09)]}))
    capped = {'year': 2021, 'estimators': {'log1p_capped': {
        'text_gain': {'mae_days': 0.32},
        'text_gain_mae_intervals': {'country': {'interval_95': [0.08, 0.54]}}}}}
    (tmp_path / 'loss_alignment_2021.json').write_text(json.dumps(capped))
    result = gain_intervals.build(bench, tmp_path)
    assert result['country_includes_zero'] == {'linear': 1, 'linear_capped': 0, 'tree': 0}
    assert result['month_includes_zero'] == {'linear': 0}
    assert result['linear_capped']['2021']['gain'] == 0.32
