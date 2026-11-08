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
                                           (0.029, '#B4A9D2'), (0.05, '#8677B4'), (0.10, '#5B4B8A'),
                                           (1.0, '#5B4B8A')])
def test_share_colour_bins(share, colour):
    assert MAP.share_colour(share) == colour


def test_share_colour_rejects_out_of_range():
    with pytest.raises(ValueError):
        MAP.share_colour(1.2)


def test_match_codes_reports_missing_in_order():
    assert MAP.match_codes(['PH', 'XK', 'KE', 'ZZ'], {'PH', 'KE'}) == ['XK', 'ZZ']


def test_aspect_matches_extent():
    assert MAP.aspect() == pytest.approx(270 / 86)
