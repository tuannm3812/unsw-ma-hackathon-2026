#!/usr/bin/env python3
"""Render slide 8's choropleth of Kiva loan share by country.

  .venv-maps/bin/python scripts/build_country_map.py

Reads reports/evidence_sources/country_shares.json and the Natural Earth 1:110m
admin-0 countries file in docs/presentation/portfolio_deck/assets/maps/ (see its
PROVENANCE.md), then writes assets/maps/country_share_map.png. Countries are joined
on ISO alpha-2 codes (Natural Earth's ISO_A2_EH); any code that fails to match is
printed and makes the script exit non-zero. geopandas lives only in the isolated
.venv-maps environment, so it is imported inside render().
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / 'docs/presentation/portfolio_deck/assets/maps'
WORLD = MAPS / 'ne_110m_admin_0_countries.zip'
SHARES = ROOT / 'reports/evidence_sources/country_shares.json'
OUTPUT = MAPS / 'country_share_map.png'

# Deck palette (docs/presentation/DESIGN.md): violet sequential scale on a transparent ground.
NAVY, NO_LOANS, BORDER = '#1C2333', '#E4E2DC', '#FFFFFF'
# Loan-share bins as fractions of all loans, with their fill, from low to high.
# The slide 8 table reuses these fills for its share cells, so each step must carry 8 pt text at
# 4.5:1 or better: navy text on the two light steps, white on the two dark ones.
BINS = [(0.01, '#E2DCF0'), (0.03, '#B4A9D2'), (0.10, '#7262A3'), (1.01, '#43356F')]
BIN_LABELS = ['under 1%', '1–3%', '3–10%', '10%+']
# Crop to the lending countries (longitude -96 to 174, latitude -36 to 50).
EXTENT = (-96.0, 174.0, -36.0, 50.0)
TOP_N = 10


def share_colour(share: float) -> str:
    """Fill for a country's share of all loans."""
    if not 0 <= share <= 1:
        raise ValueError(f'share outside [0, 1]: {share}')
    return next(colour for limit, colour in BINS if share < limit)


def match_codes(codes: list[str], available: set[str]) -> list[str]:
    """Return the Kiva country codes with no Natural Earth polygon, in input order."""
    return [code for code in codes if code not in available]


def aspect() -> float:
    """Width over height of the cropped plate carrée frame."""
    west, east, south, north = EXTENT
    return (east - west) / (north - south)


def render(output: Path = OUTPUT, width_in: float = 8.0, dpi: int = 300) -> list[str]:
    """Draw the map and return any unmatched codes (empty when every country joined)."""
    import geopandas
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    shares = json.loads(SHARES.read_text())['shares']
    world = geopandas.read_file(f'zip://{WORLD}')
    world = world[world['ISO_A2_EH'] != 'AQ']
    unmatched = match_codes([row['country'] for row in shares], set(world['ISO_A2_EH']))
    by_code = {row['country']: row for row in shares}
    top = {row['country'] for row in sorted(shares, key=lambda r: -r['loans'])[:TOP_N]}

    fig = plt.figure(figsize=(width_in, width_in / aspect()), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    lending = world['ISO_A2_EH'].isin(by_code)
    world[~lending].plot(ax=ax, color=NO_LOANS, edgecolor=BORDER, linewidth=0.3)
    fills = world.loc[lending, 'ISO_A2_EH'].map(lambda c: share_colour(by_code[c]['share']))
    world[lending].plot(ax=ax, color=list(fills), edgecolor=BORDER, linewidth=0.3)
    world[world['ISO_A2_EH'].isin(top)].plot(ax=ax, facecolor='none', edgecolor=NAVY, linewidth=0.9)
    west, east, south, north = EXTENT
    ax.set_xlim(west, east)
    ax.set_ylim(south, north)
    ax.set_axis_off()
    # Transparent ground: the slide panel's paper shows through, so no seam at the frame edge.
    fig.savefig(output, dpi=dpi, transparent=True)
    plt.close(fig)
    return unmatched


def main() -> int:
    unmatched = render()
    if unmatched:
        print('unmatched country codes: ' + ', '.join(unmatched))
        return 1
    print(f'{OUTPUT.relative_to(ROOT)}: all countries matched')
    return 0


if __name__ == '__main__':
    sys.exit(main())
