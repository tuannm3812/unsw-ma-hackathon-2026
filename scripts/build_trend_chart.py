#!/usr/bin/env python3
"""Render slide 4's yearly trend: same-day share (violet area) and share waiting over two weeks (navy line).

  .venv/bin/python scripts/build_trend_chart.py

Reads reports/period_trend/yearly_same_day_share.json (src/period_trend.py) and writes a
transparent PNG with no text: the deck draws every label, tick and band natively in Google Sans,
so the PNG must cover exactly EXTENT (years on x, share on y). Rising line segments cannot be
drawn by the Slides CLI, which is why this chart is an image.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'reports/period_trend/yearly_same_day_share.json'
OUTPUT = ROOT / 'docs/presentation/portfolio_deck/assets/charts/yearly_trend.png'
EXTENT = (2015.6, 2025.4, 0.0, 0.6)  # x from, x to, y from, y to
VIOLET, VIOLET_FILL, NAVY = '#5B4B8A', '#C4BBDF', '#1C2333'
INCOMPLETE_YEAR = 2025


def series(rows: list[dict]) -> dict:
    """Years with the same-day share, the share waiting over 14 days, and which year is incomplete."""
    rows = sorted(rows, key=lambda r: r['year'])
    return {'years': [r['year'] for r in rows],
            'same_day': [r['share_within_24h'] for r in rows],
            'over_14': [r['share_over_14_days'] for r in rows],
            'incomplete': [r['year'] == INCOMPLETE_YEAR for r in rows]}


def to_frame(value_x: float, value_y: float, frame: tuple) -> tuple:
    """Map a (year, share) point to slide coordinates inside frame = (x, y, w, h)."""
    x0, x1, y0, y1 = EXTENT
    fx, fy, fw, fh = frame
    return fx + (value_x - x0) / (x1 - x0) * fw, fy + fh - (value_y - y0) / (y1 - y0) * fh


def render(output: Path = OUTPUT, width_in: float = 8.0, height_in: float = 2.4, dpi: int = 300) -> None:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    data = series(json.loads(SOURCE.read_text())['years'])
    fig = plt.figure(figsize=(width_in, height_in), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    years, same, over = data['years'], data['same_day'], data['over_14']
    ax.fill_between(years, same, 0, color=VIOLET_FILL, linewidth=0)
    ax.plot(years, same, color=VIOLET, linewidth=2.2)
    ax.plot(years[:-1], over[:-1], color=NAVY, linewidth=2.2)
    ax.plot(years[-2:], over[-2:], color=NAVY, linewidth=2.2, linestyle=(0, (2, 2)))
    for x, y, done in zip(years, over, data['incomplete']):
        ax.plot([x], [y], marker='o', markersize=5, color=NAVY, markerfacecolor='white' if done else NAVY)
    for x, y, done in zip(years, same, data['incomplete']):
        ax.plot([x], [y], marker='o', markersize=5, color=VIOLET, markerfacecolor='white' if done else VIOLET)
    x0, x1, y0, y1 = EXTENT
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_axis_off()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=dpi, transparent=True)
    plt.close(fig)


if __name__ == '__main__':
    render()
    print(OUTPUT.relative_to(ROOT))
