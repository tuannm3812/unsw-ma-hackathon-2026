import pytest

from src.triage_lookup_summary import summarise


def _model(lift, median):
    return {'top_10': {'lift': lift}, 'within_country_precision_top_10': {'median': median}}


def _year(year, lookup, tree):
    return {'year': year, 'models': {'lookup_B1': _model(*lookup), 'tree_structure': _model(*tree), 'linear_structure': _model(9, 9)}}


def test_summary_reports_each_year_and_ranges():
    data = {'years': [_year(2021, (2.0, .25), (2.6, .5)), _year(2022, (2.5, .22), (3.4, .56))]}
    out = summarise(data)
    assert out['years']['2021']['tree_lift'] == 2.6 and out['years']['2022']['lookup_within'] == .22
    assert out['lookup_lift_range'] == [2.0, 2.5] and out['tree_within_range'] == [.5, .56]


def test_summary_counts_years_the_tree_beats_the_lookup():
    data = {'years': [_year(2021, (2.0, .25), (2.6, .5)), _year(2022, (3.5, .6), (3.4, .56))]}
    out = summarise(data)
    assert out['tree_beats_lift_years'] == 1 and out['tree_beats_within_years'] == 1
    assert out['years_compared'] == pytest.approx(2)
