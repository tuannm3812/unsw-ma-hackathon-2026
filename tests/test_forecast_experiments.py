import pytest

from src.forecast_experiments import placebo_summary, tree_summary


def _paired(year, candidate, metric, unit, gain, low, high):
    return {'year': year, 'baseline': 'S', 'candidate': candidate, 'metric': metric, 'resampling_unit': unit,
            'gain': gain, 'interval_95': [low, high]}


def _window(year, mae):
    return {'year': year, 'arm': 'S', 'mae_days': mae}


def test_tree_summary_reads_full_text_arm_and_counts_intervals_excluding_zero():
    large = {'windows': [_window(2021, 8.0), _window(2022, 6.0)],
             'paired': [_paired(2021, 'S+M+L+D', 'mae_days', 'calendar_month', .15, .1, .2),
                        _paired(2021, 'S+M+L+D', 'mae_days', 'country', .15, .05, .3),
                        _paired(2021, 'S+M+L+D', 'brier', 'calendar_month', .005, -.001, .01),
                        _paired(2021, 'S+M+L', 'mae_days', 'calendar_month', .9, .8, 1.0),
                        _paired(2022, 'S+M+L+D', 'mae_days', 'calendar_month', -.01, -.06, .03),
                        _paired(2022, 'S+M+L+D', 'mae_days', 'country', -.01, -.09, .03),
                        _paired(2022, 'S+M+L+D', 'brier', 'calendar_month', .001, .0005, .002)]}
    benchmark = {'windows': [_window(2021, 7.5), _window(2022, 6.5)], 'paired': []}
    out = tree_summary(large, benchmark)
    assert out['years']['2021']['mae_gain'] == .15 and out['years']['2021']['brier_gain'] == .005
    assert out['years']['2022']['country'] == [-.09, .03]
    assert out['month_excludes_zero'] == 1 and out['country_excludes_zero'] == 1
    assert out['structure_lower_error_years'] == 1 and out['years_compared'] == 2
    assert out['brier_positive_years'] == 2


def test_placebo_summary_splits_gain_into_context_and_loan_specific():
    def block(gain, low, high):
        return {'gain': gain, 'interval_95': [low, high]}
    data = {'share_rows_moved': .98, 'years': [
        {'year': 2021, 'gain_real': block(.3, .2, .4), 'gain_shuffled': block(.12, .05, .2),
         'real_minus_shuffled': block(.18, .1, .25), 'real_minus_shuffled_country': block(.18, -.03, .4)},
        {'year': 2022, 'gain_real': block(.4, .2, .5), 'gain_shuffled': block(.24, .1, .3),
         'real_minus_shuffled': block(.16, .02, .3), 'real_minus_shuffled_country': block(.16, .01, .5)}]}
    out = placebo_summary(data)
    assert out['years']['2021']['context'] == .12 and out['years']['2021']['loan_specific'] == .18
    assert out['years']['2022']['context_share'] == pytest.approx(.6)
    assert out['context_share_range'] == pytest.approx([.4, .6])
    assert out['loan_specific_range'] == [.16, .18]
    assert out['month_excludes_zero'] == 2 and out['country_excludes_zero'] == 1
