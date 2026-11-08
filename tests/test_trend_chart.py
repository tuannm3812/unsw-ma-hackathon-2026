import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    'build_trend_chart', Path(__file__).resolve().parents[1] / 'scripts/build_trend_chart.py')
CHART = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHART)


def test_series_sorts_years_and_flags_incomplete_year():
    rows = [{'year': 2025, 'share_within_24h': .35, 'share_over_14_days': .23},
            {'year': 2016, 'share_within_24h': .43, 'share_over_14_days': .23}]
    out = CHART.series(rows)
    assert out['years'] == [2016, 2025] and out['incomplete'] == [False, True]
    assert out['same_day'] == [.43, .35]


def test_to_frame_maps_extent_corners():
    frame = (100, 200, 400, 120)
    x0, x1, y0, y1 = CHART.EXTENT
    assert CHART.to_frame(x0, y0, frame) == pytest.approx((100, 320))
    assert CHART.to_frame(x1, y1, frame) == pytest.approx((500, 200))
