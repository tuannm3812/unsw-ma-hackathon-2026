import pytest

from src.triage_summary import summarise


def _arm(precision, lift, median, low, high):
    return {'top_10': {'precision': precision, 'lift': lift},
            'top10_countries_within_country_precision_top_10': {'median': median, 'min': low, 'max': high}}


def _year(year, structure, text, diff, interval):
    return {'year': year, 'models': {'tree/duration': {
        'structure': structure, 'structure_text': text,
        'text_minus_structure_precision_top_10': {'difference': diff, 'month_block_95': interval}}}}


def test_summarise_ranges_and_zero_crossings():
    data = {'target': 'slowest 20%', 'population': 'completed loans', 'years': [
        _year(2021, _arm(0.5, 2.5, 0.48, 0.30, 0.80), _arm(0.52, 2.6, 0.49, 0.31, 0.81), 0.02, [-0.01, 0.04]),
        _year(2022, _arm(0.8, 4.0, 0.56, 0.18, 0.90), _arm(0.79, 3.9, 0.55, 0.20, 0.88), -0.01, [0.01, 0.03]),
    ]}
    tree = summarise(data)['models']['tree/duration']
    assert tree['structure']['precision_range'] == [0.5, 0.8]
    assert tree['structure']['lift_range'] == [2.5, 4.0]
    assert tree['structure']['country_median_range'] == [0.48, 0.56]
    assert tree['structure']['country_range'] == [0.18, 0.90]
    assert tree['structure']['lift_by_year'] == {2021: 2.5, 2022: 4.0}
    assert tree['text_gain']['difference_range'] == pytest.approx([-0.01, 0.02])
    assert tree['text_gain']['years_interval_includes_zero'] == 1
