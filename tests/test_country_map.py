"""Pure helpers of the slide 8 country map; rendering needs the separate .venv-maps."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    'build_country_map', Path(__file__).resolve().parents[1] / 'scripts/build_country_map.py')
MAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MAP)


def test_import_does_not_need_geopandas_or_write_files():
    assert MAP.OUTPUT.name == 'country_share_map.png'


@pytest.mark.parametrize('share, colour', [(0.0, '#E2DCF0'), (0.0099, '#E2DCF0'), (0.01, '#B4A9D2'),
                                           (0.029, '#B4A9D2'), (0.05, '#7262A3'), (0.10, '#43356F'),
                                           (1.0, '#43356F')])
def test_share_colour_bins(share, colour):
    assert MAP.share_colour(share) == colour


def test_share_colour_rejects_out_of_range():
    with pytest.raises(ValueError):
        MAP.share_colour(1.2)


def test_match_codes_reports_missing_in_order():
    assert MAP.match_codes(['PH', 'XK', 'KE', 'ZZ'], {'PH', 'KE'}) == ['XK', 'ZZ']


def test_aspect_matches_extent():
    assert MAP.aspect() == pytest.approx(270 / 86)


def _luminance(hex_colour):
    channels = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def test_every_bin_carries_navy_or_white_text():
    for _, fill in MAP.BINS:
        best = max((max(_luminance(fill), _luminance(ink)) + 0.05) / (min(_luminance(fill), _luminance(ink)) + 0.05)
                   for ink in ('#1C2333', '#FFFFFF'))
        assert best >= 4.5, fill
