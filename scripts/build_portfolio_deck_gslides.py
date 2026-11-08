#!/usr/bin/env python3
"""Build the portfolio deck as a NEW native Google Slides presentation.

Reads docs/presentation/portfolio_deck/storyline.json and follows
docs/presentation/DESIGN.md plus the parent slide standard. All charts and tables
are native shapes drawn from the storyline data.

`gslides mutate create` always gives a 720 x 405 pt page, and the CLI cannot change
page size. The new deck is therefore a `gslides mutate copy` of a blank 960 x 540 pt
base converted from scripts/build_portfolio_deck_base.py, then filled here.

  build_portfolio_deck_gslides.py --base BASE_ID      create a new deck (default use)
  build_portfolio_deck_gslides.py --reuse DECK_ID     refill a working deck during QA

After the first import the live deck is authoritative; do not rerun over owner edits.
Refuses to touch the historical live deck. Marker heights come from
docs/presentation/portfolio_deck/marker_layout.json, measured by
scripts/qa_portfolio_deck.py from the Google-rendered PDF.
"""
from __future__ import annotations

import argparse
import json
import importlib.util
import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / 'docs/presentation/portfolio_deck'
TITLE = 'Cultural Blend — Beyond a good story (portfolio, Nov 2026)'
PROTECTED = {'17rHwKFXiqN4GBo8TT5xnBWk33bN7niIodw9K9APNwDk'}
PHOTO = ROOT / 'docs/presentation/poster/assets/kiva-tatiana-farmer.jpg'
# Official UNSW logo (competition host mark), provenance in docs/presentation/poster/README.md.
# Full colour on transparency with no reversed version, so it sits on a white tile, never recoloured.
LOGO = ROOT / 'docs/presentation/poster/assets/unsw-official-logo.png'
ASSETS = DECK / 'assets'
MARKET = ASSETS / 'photos/unsplash-market-muhammad-taha-ibrahim.jpg'
TAILOR = ASSETS / 'photos/unsplash-tailor-david-geneugelijk.jpg'
HARVEST = ASSETS / 'photos/unsplash-harvest-richard-nyoni.jpg'
VENDOR = ASSETS / 'photos/unsplash-vendor-ali-mkumbwa.jpg'
# Photo frames (x, y, width, height). The large frames bleed off the right and bottom edges
# and round only their visible top-left corner; the small cover frames round all four.
COVER_FRAME = (652, 96, 308, 444)
COVER_SMALL = [(MARKET, (504, 140, 132, 176)), (TAILOR, (504, 330, 132, 176))]
CLOSE_FRAME = (672, 196, 288, 344)
CREDIT = 'Photos: Kiva; Muhammad-Taha Ibrahim and David Geneugelijk on Unsplash'
FOOTER = 'Cultural Blend   Kiva funding speed, 1.45 million loans, 2016–2025'

# Violet replaced teal on 2026-11-08 (Mike's decision); see DESIGN.md.
NAVY, YELLOW, VIOLET, PAPER = '#1C2333', '#FFDD04', '#5B4B8A', '#FBFAF6'
GREY, SLATE, RED, RULE, WHITE = '#59636E', '#46576C', '#C64040', '#999999', '#FFFFFF'
TINT, HAIR = '#FFF6B8', '#D9D7CE'
TINT_BAND = '#FFF0A8'  # DESIGN.md yellow tint: the slide 9 "too small to matter" band
BAND_OUTER = '#FFF8D6'  # lighter yellow: slide 9's 5-10% area
FONT = 'Google Sans'
INSET = 7.2  # native text box inset; the API cannot change it, so frames compensate
LEGEND_MID = 4.9  # x-height centre of 8 pt text below its box top, measured at 400 dpi; scales with size
NARROW, WIDE = set("iljt.,:;’'()¹ "), set('mwW')


def label_width(text: str, size: float = 8) -> float:
    """Approximate Google Sans width in points, close enough to space legend items evenly."""
    width = sum(2.4 if c in NARROW else 6.6 if c in WIDE else 5.5 if c.isupper() else 4.5 for c in text)
    return width * size / 8
L, R, FULL, TOP, END = 43.5, 650, 919, 130, 476


def gslides() -> str:
    found = shutil.which('gslides')
    fallback = Path.home() / '.gemini/antigravity/bin/gslides'
    if found or fallback.exists():
        return found or str(fallback)
    raise SystemExit('gslides CLI not found')


def run(*args: str) -> str:
    return subprocess.run([gslides(), *args], check=True, capture_output=True, text=True).stdout


class Page:
    """Collect batch ops for one slide; coordinates are the visual text position."""

    def __init__(self, slide_id: str):
        self.id, self.ops, self.count = slide_id, [], 0

    def _new(self, prefix: str) -> str:
        self.count += 1
        return f'{prefix}{self.count}'

    def text(self, text, x, y, w, h=None, size=10, color=NAVY, bold=False, align=None,
             middle=False, spacing=None, after=None, paragraphs=None, spans=None):
        """Add a text box. ``spans`` is [(start, end, style)]; paragraphs is [(start, end, style)]."""
        element = self._new('t')
        h = h if h is not None else size * 1.6
        op = {'op': 'add-textbox', 'slide': self.id, 'id': element, 'text': text,
              'x': x - INSET, 'y': y - INSET, 'width': w + 2 * INSET, 'height': h + 2 * INSET,
              'font_size': size, 'font_family': FONT, 'color': color, 'bold': bold}
        if align:
            op['alignment'] = align
        if middle:
            op['content_alignment'] = 'MIDDLE'
        self.ops.append(op)
        if spacing or after is not None:
            style = {'op': 'style-paragraph', 'element': element, 'start': 0, 'end': len(text)}
            if spacing:
                style['line_spacing'] = spacing
            if after is not None:
                style['space_below'] = after
            self.ops.append(style)
        for start, end, style in paragraphs or []:
            self.ops.append({'op': 'style-paragraph', 'element': element, 'start': start,
                             'end': end, **style})
        for start, end, style in spans or []:
            self.ops.append({'op': 'style-text', 'element': element, 'start': start,
                             'end': end, **style})
        return element

    def block(self, heading, body, x, y, w, h=None, body_size=10, head_size=12, color=GREY):
        """Heading and explanation in one rich-text component."""
        text = f'{heading}\n{body}'
        return self.text(text, x, y, w, h or 60, size=body_size, color=color, spacing=110,
                         paragraphs=[(0, len(heading), {'space_below': 3})],
                         spans=[(0, len(heading), {'bold': True, 'color': NAVY, 'font_size': head_size})])

    def rect(self, x, y, w, h, fill, shape='RECTANGLE'):
        element = self._new('r')
        self.ops.append({'op': 'add-shape', 'slide': self.id, 'id': element, 'shape_type': shape,
                         'x': x, 'y': y, 'width': w, 'height': h, 'background_color': fill})
        return element

    def badge(self, label, x, y, size, fill, color=WHITE, font=8, shape='ELLIPSE'):
        element = self._new('b')
        self.ops.append({'op': 'add-shape', 'slide': self.id, 'id': element, 'shape_type': shape,
                         'x': x, 'y': y, 'width': size[0], 'height': size[1], 'background_color': fill,
                         'content_alignment': 'MIDDLE'})
        if len(label) > 1 and size[0] < 60:
            # Native insets would wrap two digits inside a small shape, so a wider
            # text box sits on top, centred on the shape.
            return self.text(label, x - 20, y, size[0] + 40, size[1], size=font, color=color, bold=True,
                             align='center', middle=True)
        # add-shape ignores text, so it is inserted and styled as separate ops.
        self.ops.append({'op': 'insert-text', 'element': element, 'text': label})
        self.ops.append({'op': 'style-text', 'element': element, 'start': 0, 'end': len(label),
                         'font_size': font, 'font_family': FONT, 'bold': True, 'color': color})
        self.ops.append({'op': 'style-paragraph', 'element': element, 'start': 0, 'end': len(label),
                         'alignment': 'center'})
        return element

    def marker(self, n, x, y):
        """Red 12 pt ellipse with a centred 8 pt white number in its own frame.

        A number inside a 12 pt shape inherits the native 7.2 pt insets the CLI cannot remove,
        so the circle stays empty and a text box, compensated for those insets, sits on top.
        """
        self.rect(x, y, 12, 12, RED, 'ELLIPSE')
        return self.text(str(n), x, y, 12, 12, size=8, color=WHITE, bold=True, align='center', middle=True)

    def line(self, x1, y1, x2, y2, color=RULE, weight=.75):
        self.ops.append({'op': 'add-line', 'slide': self.id, 'id': self._new('l'), 'x': min(x1, x2),
                         'y': min(y1, y2), 'width': abs(x2 - x1), 'height': abs(y2 - y1),
                         'color': color, 'line_weight': weight})

    def chrome(self, slide):
        section = (slide['section'] or '').upper()
        sub = (slide.get('sublabel') or '').upper()
        label = f'{section}  |  {sub}' if sub else section
        spans = [(len(section), len(section) + 5, {'color': RULE}),
                 (len(section) + 5, len(label), {'color': GREY})] if sub else []
        # Sublabel uses body grey, not the parent's #999999, so it meets WCAG AA (DESIGN.md).
        if not slide.get('hide_label'):  # Mike removed the agenda's label in the live deck
            self.text(label, L, 29.5, 600, 14, size=10, color=VIOLET, bold=True, spans=spans)
        self.text(slide['title'], L, 48.4, FULL - L, 34, size=24, bold=True)
        if slide.get('subtitle'):
            self.text(slide['subtitle'], L, 90.9, FULL - L, 18, size=12, color=GREY)

    def takeaways(self, items, positions):
        """One unified column; markers sit beside each heading's measured first line."""
        self.line(658, TOP, 658, END, RULE, .75)
        text, paragraphs, spans, cursor = '', [], [], 0
        for i, item in enumerate(items):
            heading, raw = item['heading'], item['text']
            body, emphasis = '', []
            for j, part in enumerate(raw.split('**')):
                if j % 2:  # **phrase** marks an evidence-bearing phrase
                    emphasis.append((len(body), len(body) + len(part)))
                body += part
            spans.append((cursor, cursor + len(heading), {'bold': True, 'color': VIOLET}))
            start = cursor + len(heading) + 1
            spans += [(start + a, start + b, {'bold': True, 'color': NAVY}) for a, b in emphasis]
            above = {'space_above': 14} if i else {}
            paragraphs.append((cursor, cursor + len(heading), {'space_below': 6, **above}))
            paragraphs.append((cursor + len(heading) + 1, cursor + len(heading) + 1 + len(body),
                               {'space_below': 6}))
            text += f'{heading}\n{body}\n'
            cursor = len(text)
        self.text(text.rstrip('\n'), 684, 136, 235, 324, size=12, color=GREY, spacing=110,
                  paragraphs=paragraphs, spans=spans)
        for i, item in enumerate(items):
            self.marker(item['marker'], 668, positions[i])

    def sup(self, text, x, y, w, h=14, size=10, color=NAVY, bold=False, align=None):
        """Text ending in a superscript note mark (¹, ²) that is drawn in slate."""
        mark = len(text.rstrip('¹²³'))
        spans = [(mark, len(text), {'color': SLATE, 'bold': True})] if mark < len(text) else []
        return self.text(text, x, y, w, h, size=size, color=color, bold=bold, align=align, spans=spans)

    def swatch(self, x, y, w, h, fill, shape='RECTANGLE', size=8):
        """A legend mark centred on the x-height of a label whose text box top is at y."""
        return self.rect(x, y + LEGEND_MID * size / 8 - h / 2, w, h, fill, shape)

    def legend(self, items, y, x, span=None, gap=20, size=8):
        """Swatches centred on their labels' x-height, evenly spaced, optionally centred within span.

        Each item is (label, fill) or (label, fill, shape) or (label, fill, shape, marker number).
        """
        mid, scale = LEGEND_MID * size / 8, size / 8
        def parts(item):
            label, fill, shape, marker = (*item, 'RECTANGLE', None)[:4] if len(item) == 2 else (*item, None)[:4]
            return label, fill, shape, marker, (7 * scale if shape in ('ELLIPSE', 'HOLLOW') else 12 * scale)
        widths = [p[4] + 4 + label_width(p[0], size) + (16 if p[3] else 0) for p in map(parts, items)]
        lx = x + (span - sum(widths) - gap * (len(items) - 1)) / 2 if span else x
        for item, width in zip(items, widths):
            label, fill, shape, marker, swatch = parts(item)
            tall = swatch if shape in ('ELLIPSE', 'HOLLOW') else {'BAR': 3.5, 'RULE': .75}.get(shape, 8 * scale)
            self.swatch(lx, y, swatch, tall, fill, {'BAR': 'RECTANGLE', 'RULE': 'RECTANGLE', 'HOLLOW': 'ELLIPSE'}.get(shape, shape), size)
            if shape == 'HOLLOW':
                self.swatch(lx + 1.25, y, swatch - 2.5, tall - 2.5, PAPER, 'ELLIPSE', size)
            self.sup(label, lx + swatch + 4, y, label_width(label, size) + 10, 12 * scale, size=size, color=GREY)
            if marker:
                self.marker(marker, lx + width - 12, y + mid - 6)
            lx += width + gap

    def caption(self, label, text, y, x=L, w=R - L):
        full = f'{label} {text}'
        self.text(full, x, y, w, 12, size=8, color=GREY, spans=[(0, len(label), {'bold': True})])


def marker_positions(slide, layout):
    stored = layout.get(str(slide['n']))
    count = len(slide.get('takeaways', []))
    return stored if stored and len(stored) == count else [137 + 80 * i for i in range(count)]


def card(page, x, y, w, h, bar=VIOLET):
    page.rect(x, y, w, h, PAPER)
    page.rect(x, y, w, 2.5, bar)


def key_card(page, figure, x, y, w, h, bar=VIOLET, size=26):
    card(page, x, y, w, h, bar)
    page.text(figure['value'], x + 12, y + 12, w - 24, 34, size=size, bold=True)
    page.text(figure['label'], x + 12, y + 12 + size * 1.5, w - 24, h - 50, size=10, color=GREY, spacing=110)


def table(page, columns, rows, x, y, w, row_h=30, size=10):
    """Native table. The CLI cannot fill cells, so a rectangle sits behind the header row."""
    page.rect(x, y, w, row_h, NAVY)
    element = page._new('tb')
    page.ops.append({'op': 'add-table', 'slide': page.id, 'id': element, 'rows': len(rows) + 1,
                     'cols': len(columns), 'x': x, 'y': y, 'width': w, 'height': row_h * (len(rows) + 1)})
    for c, label in enumerate(columns):
        page.ops.append({'op': 'set-table-cell', 'table': element, 'row': 0, 'col': c, 'text': label,
                         'bold': True, 'color': WHITE, 'font_family': FONT, 'font_size': size})
    for r, row in enumerate(rows, 1):
        for c, value in enumerate(row):
            page.ops.append({'op': 'set-table-cell', 'table': element, 'row': r, 'col': c, 'text': value,
                             'color': NAVY, 'font_family': FONT, 'font_size': size})


# --- slides ---------------------------------------------------------------------------------

def photo_accent(page, x, y, size):
    """The cover's one decorative shape: a yellow block behind the photo's rounded corner."""
    page.rect(x - 16, y - 16, size, size, YELLOW, 'ROUND_RECTANGLE')


def cover(page, slide):
    """White ground; three photo frames (inserted after this batch) with one yellow and one violet accent."""
    page.ops.append({'op': 'set-background', 'slide': page.id, 'color': WHITE})
    photo_accent(page, *COVER_FRAME[:2], 112)
    x, y, w, h = COVER_SMALL[0][1]
    page.rect(x + 8, y + 8, w, h, VIOLET, 'ROUND_RECTANGLE')
    page.rect(L, 156, 28, 3, YELLOW)
    page.text(slide.get('kicker', 'UNSW Marketing Analytics Hackathon 2026').upper(), L, 166, 440, 14, size=10, color=VIOLET, bold=True)
    page.text(slide['title'], L, 186, 450, 112, size=44, bold=True, spacing=95)
    page.text(slide['subtitle'], L, 304, 430, 50, size=16, color=SLATE, spacing=115)
    page.text(slide['names'], L, 394, 420, 16, size=12, bold=True)
    page.text(slide['team'], L, 413, 420, 16, size=12, color=GREY)


def close(page, slide):
    page.ops.append({'op': 'set-background', 'slide': page.id, 'color': WHITE})
    photo_accent(page, *CLOSE_FRAME[:2], 104)
    page.rect(L, 196, 28, 3, YELLOW)
    page.text(slide['title'], L, 210, 520, 56, size=44, bold=True)
    first, second = slide['lines']
    prefix = 'Code and evidence: '
    start = len(first) + 1 + len(prefix)
    text = f'{first}\n{second}'
    page.text(text, L, 284, 560, 50, size=12, color=NAVY, spacing=120,
              spans=[(0, len(first), {'bold': True}), (start, len(text), {'link': slide['link'], 'color': VIOLET})])


SUMMARY_ICONS = [None, 'target-violet.png', 'description-violet.png']  # Mike removed the first icon in the live deck
STEP_ICONS = ['query_stats-white.png', 'trending_up-white.png', 'science-white.png']
SUMMARY_CARDS = [(L + i * 298, TOP, 279, 244) for i in range(3)]
BAND = (L, 390, FULL - L - .5, 66)
STEP_X = [548, 670, 792]


def summary(page, slide, pos):
    """Three mini-exhibits, each with an icon, key figure and a native chart, then the decision."""
    page.chrome(slide)
    minis = {'periods': period_mini, 'lift': lift_mini, 'bound': bound_mini, 'waffle': waffle_mini, 'gain': gain_mini,
             'waits': waits_mini}
    for (x, y, w, h), body, colour in zip(SUMMARY_CARDS, slide['body'], [SLATE, NAVY, VIOLET]):
        draw = minis[body.get('mini', 'gain')]
        card(page, x, y, w, h, colour)
        page.text(body['layer'].upper(), x + 46, y + 18, w - 62, 14, size=10, color=GREY, bold=True)
        page.text(body['figure'], x + 16, y + 42, w - 32, 40, size=32, bold=True)
        draw(page, x + 16, y + 94, w - 32, slide)
        page.block(body['heading'], body['text'], x + 16, y + 180, w - 32, 60)
    bx, by, bw, bh = BAND
    page.rect(bx, by, bw, bh, NAVY)
    page.rect(bx, by, 6, bh, YELLOW)
    label_end = slide['decision'].index(':') + 1
    page.text(slide['decision'], bx + 22, by, 470, bh, size=12, color=WHITE, middle=True, spacing=110,
              spans=[(0, label_end, {'bold': True})])
    for (x, y, w, h), (nx, _, _, _) in zip(SUMMARY_CARDS, SUMMARY_CARDS[1:]):
        page.line(x + w + 3, y + h / 2, nx - 3, y + h / 2, SLATE, .75)
        page.ops[-1]['end_arrow'] = 'FILL_ARROW'
    for x, step in zip(STEP_X, slide['steps']):
        page.text(step, x + 26, by, 96, bh, size=10, color=WHITE, middle=True, spacing=110)
    if slide.get('pending'):
        page.text(slide['pending'], L, by + bh + 8, FULL - L, 12, size=8, color=GREY)


def wait_scale(x, w, lo=0.1, hi=100):
    """Log-scale position for a funding time in days."""
    return lambda days: x + (math.log10(days) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)) * w


MINI_BASE = 62  # every summary mini chart puts its axis line at y + MINI_BASE and labels 3 pt below


def waits_mini(page, x, y, w, slide):
    """Funding-time quartiles on a log scale: the middle half as a band, the median as a bar."""
    q = slide_by_id('problem')['exhibit']['quartiles']
    px = wait_scale(x, w)
    base = y + MINI_BASE
    page.line(x, base, x + w, base, NAVY, .75)
    page.rect(px(q['q1']), base - 24, px(q['q3']) - px(q['q1']), 24, '#E2DCF0')
    page.rect(px(q['median']) - 1.5, base - 34, 3, 34, NAVY)
    page.text(f"{q['median']} days", px(q['median']) - 30, base - 48, 60, 12, size=8, bold=True, align='center')
    page.text(f"over {q['q3']} days", px(q['q3']) - 36, base - 38, 72, 12, size=8, color=VIOLET, bold=True,
              align='center')
    for days, name in [(0.1, '0.1'), (1, '1'), (10, '10'), (100, '100 days')]:
        page.text(name, px(days) - 22, base + 3, 44, 12, size=8, color=GREY, align='center')


def period_mini(page, x, y, w, slide):
    """Same-day share by period, bars from zero with direct labels."""
    periods = slide_by_id('problem')['exhibit']['periods']
    bar, step, base, per = 56, 82, y + 72, 1.3
    for i, (name, value) in enumerate(periods):
        bx = x + 4 + i * step
        page.rect(bx, base - value * per, bar, value * per, SLATE if i == 0 else NAVY)
        page.text(f'{value:.1f}%', bx - 8, base - value * per - 14, bar + 16, 12, size=8, color=NAVY, bold=True,
                  align='center')
        page.text(name, bx - 14, base + 2, bar + 28, 12, size=8, color=GREY, align='center')
    page.line(x, base, x + w, base, NAVY, .75)


def lift_mini(page, x, y, w, slide):
    """Triage lift by test year against random (1x), on the shared summary baseline."""
    lift = slide_by_id('triage')['exhibit']['lift']
    bar, step, base, per = 30, 50, y + MINI_BASE, 11
    page.line(x, base - per, x + w, base - per, RULE, .75)
    page.ops[-1]['dash_style'] = 'DASH'
    for i, (year, value) in enumerate(lift):
        bx = x + 4 + i * step
        page.rect(bx, base - value * per, bar, value * per, NAVY)
        page.text(f'{value:.2f}', bx - 8, base - value * per - 13, bar + 16, 12, size=8, color=NAVY, bold=True,
                  align='center')
        page.text(str(year), bx - 8, base + 3, bar + 16, 12, size=8, color=GREY, align='center')
    page.line(x, base, x + w, base, NAVY, .75)


def waffle_mini(page, x, y, w, slide):
    """120 terms, the first 64 in yellow: significant under HC3, lost under country clustering."""
    cell, gap = 10, 2.3
    for i in range(120):
        row, col = divmod(i, 20)
        page.rect(x + col * (cell + gap), y + row * (cell + gap), cell, cell, YELLOW if i < 64 else HAIR)


def bound_mini(page, x, y, w, slide):
    """Five bounded framings and urgency against the ±5% band, on the shared summary baseline."""
    rows = {r['term']: r for r in slide_by_id('equivalence')['exhibit']['rows']}
    lo, hi = -.15, .15
    px = lambda value: x + (value - lo) * w / (hi - lo)
    base = y + MINI_BASE
    page.rect(px(-.05), y, px(.05) - px(-.05), MINI_BASE, TINT)
    page.line(px(0), y, px(0), base, NAVY, .75)
    for i, term in enumerate(['family', 'basic needs', 'business', 'agency', 'third person', 'urgency']):
        r, cy = rows[term], y + 6 + i * 10
        colour = VIOLET if term == 'urgency' else NAVY
        page.line(px(r['ci90_low']), cy, px(r['ci90_high']), cy, colour, 1.5)
        page.rect(px(r['estimate']) - 2.5, cy - 2.5, 5, 5, colour, 'ELLIPSE')
    page.text('urgency', px(.0295) + 4, y + 6 + 5 * 10 - 7, 60, 12, size=8, color=VIOLET, bold=True)
    page.line(x, base, x + w, base, NAVY, .75)
    for value, name in [(-.05, '−5%'), (0, '0'), (.05, '+5%')]:
        page.text(name, px(value) - 20, base + 3, 40, 12, size=8, color=GREY, align='center')


def gain_mini(page, x, y, w, slide):
    """Linear MAE gain by year, bars from zero with direct labels."""
    years = [(int(y), v['gain']) for y, v in sorted(slide_by_id('gain_uncertainty')['exhibit']['linear'].items())]
    bar, step, base, per = 30, 54, y + 62, 120
    for i, (year, gain) in enumerate(years):
        bx = x + 2 + i * step
        page.rect(bx, base - gain * per, bar, gain * per, NAVY)
        page.text(f'{gain:.3f}', bx - 8, base - gain * per - 14, bar + 16, 12, size=8, color=NAVY, bold=True, align='center')
        page.text(str(year), bx - 8, base + 2, bar + 16, 12, size=8, color=GREY, align='center')
    page.line(x, base, x + w, base, NAVY, .75)


EXTRA_IMAGES: list = []  # (slide id, path, frame) appended by builders whose image positions depend on layout


def slide_data():
    return {str(s['n']): s for s in json.loads((DECK / 'storyline.json').read_text())['slides']}


def slide_by_id(slide_id: str) -> dict:
    """Storyline slide by its stable id, so renumbering never breaks cross-slide lookups."""
    return next(s for s in slide_data().values() if s['id'] == slide_id)


def agenda(page, slide, urls):
    page.chrome(slide)
    colours = [(NAVY, WHITE), (VIOLET, WHITE), (SLATE, WHITE), (YELLOW, NAVY)]
    xs = [43.5, 267.5, 491.5, 715.5]
    for x0, x1 in zip(xs, xs[1:]):
        page.line(x0 + 42, TOP + 18, x1 - 6, TOP + 18, SLATE, .75)
        page.ops[-1]['end_arrow'] = 'FILL_ARROW'
    for i, (teaser, x) in enumerate(zip(slide.get('teasers', []), xs)):
        card(page, x, 400, 200, 62, colours[i][0])
        page.text(teaser['value'], x + 12, 408, 176, 26, size=20, bold=True)
        page.text(teaser['label'], x + 12, 436, 176, 14, size=9, color=GREY)
    for i, part in enumerate(slide['parts']):
        x = [43.5, 267.5, 491.5, 715.5][i]
        fill, ink = colours[i]
        page.badge(part['n'], x, TOP, (36, 36), fill, ink, 12)
        page.text(part['name'], x, 176, 200, 24, size=16, bold=True)
        page.text(part['question'], x, 204, 196, 36, size=12, color=GREY, spacing=110)
        page.line(x, 252, x + 200, 252, RULE, .75)
        pitch = 22
        for j, (label, number) in enumerate(part['items']):
            y = 262 + j * pitch
            page.text(label, x, y + 1, 168, 16, size=10)
            chip = page.badge(str(number), x + 176, y + 1, (24, 15), fill, ink, 8, 'ROUND_RECTANGLE')
            page.ops.append({'op': 'style-text', 'element': chip, 'start': 0, 'end': len(str(number)),
                             'link': urls[number], 'color': ink, 'underline': False})


# Slide 4 photo frame inside the 316 pt card (x, y, width, height); icons sit beside the two headings.
LEVER_PHOTO = (L + 12, TOP + 12, 130, 162)
HIGHLIGHT = {'family': '#FFF0A8', 'business': '#E2DCF0', 'urgency': '#D5DCE5'}


LEVER_KEY_ROWS = 2


def lever(page, slide, pos):
    """Illustrative listing (photo, fixed fields, highlighted description) above a key of all eight measures."""
    page.chrome(slide)
    ex = slide['exhibit']
    x, y, w, h = L, TOP, R - 16 - L, 316
    page.rect(x, y, w, h, PAPER)
    page.rect(x, y, w, 2.5, YELLOW)
    rx, rw = x + 154, w - 166
    page.text('FIXED AT LISTING', rx + 24, y + 12, 200, 14, size=10, color=SLATE, bold=True)
    cw = rw / 3
    for i, (label, value) in enumerate(ex['fixed_fields']):
        cx, cy = rx + (i % 3) * cw, y + 30 + (i // 3) * 27
        page.text(label, cx, cy, cw - 8, 11, size=8, color=GREY)
        page.text(value, cx, cy + 11, cw - 8, 13, size=9, bold=True)
    page.line(rx, y + 86, rx + rw, y + 86, HAIR, .75)
    page.text('EDITABLE DESCRIPTION', rx + 24, y + 92, 200, 14, size=10, color=VIOLET, bold=True)
    page.rect(rx, y + 110, rw, 64, WHITE)
    page.rect(rx, y + 110, 4, 64, YELLOW)
    text = ex['description']
    spans = []
    for kind, words in ex['highlights'].items():
        for word in words:
            for m in re.finditer(r'\b' + re.escape(word) + r'\b', text):
                if kind in HIGHLIGHT:
                    spans.append((m.start(), m.end(), {'background_color': HIGHLIGHT[kind]}))
                elif kind == 'gratitude':
                    spans.append((m.start(), m.end(), {'underline': True, 'color': VIOLET, 'bold': True}))
    page.text(text, rx + 14, y + 115, rw - 34, 56, size=10, color=NAVY, spacing=120, spans=spans)
    page.marker(1, rx + rw - 14, y + 12)
    page.marker(4, rx + rw - 14, y + 92)
    # Key of the eight measures: same names, order and icons as the evidence slides.
    ky = y + 182
    page.line(x + 12, ky - 3, x + w - 12, ky - 3, HAIR, .75)
    page.text(ex['key_title'], x + 12, ky, w - 60, 12, size=8, color=GREY, bold=True)
    page.marker(2, x + w - 24, ky - 1)
    cell, row_h = (w - 24) / 4, 57
    for k, item in enumerate(ex['key']):
        cx, cy = x + 12 + (k % 4) * cell, ky + 16 + (k // 4) * row_h
        if item['highlight'] in HIGHLIGHT:
            page.rect(cx + 18, cy + 1, 8 + 5.2 * len(item['name']), 15, HIGHLIGHT[item['highlight']])
        spans = [(0, len(item['name']), {'underline': True, 'color': VIOLET})] if item['highlight'] == 'gratitude' else None
        page.text(item['name'], cx + 20, cy + 2, cell - 24, 13, size=9, bold=True, spans=spans)
        page.text(item['definition'], cx + 20, cy + 16, cell - 24, 11, size=8, color=GREY)
        page.text(f"e.g. {item['example']} · in {item['mention']}%", cx + 20, cy + 28, cell - 24, 11, size=8, color=GREY)
        EXTRA_IMAGES.append(('lever', ASSETS / 'icons' / item['icon'], (cx + 2, cy + 1.5, 14, 14)))
        if item['id'] == 'urgency':
            page.marker(3, cx + cell - 22, cy + 2)
    page.caption(slide['figure'], ex['caption'], y + h + 8, w=w)
    page.takeaways(slide['takeaways'], pos)


JOURNEY_X = [100, 224, 348, 472, 596]  # icon centres for the five journey stages on the process slide
JOURNEY_ICONS = ['payments-violet.png', 'storefront-navy.png', 'groups-navy.png', 'account_balance-violet.png']


def outcome(page, slide, pos):
    """A pre-disbursed loan's journey with what we measure bracketed, then who is in the data."""
    page.chrome(slide)
    ex = slide['exhibit']
    xs, line_y = JOURNEY_X, 186
    actor_fill = {'violet': (VIOLET, WHITE), 'navy': (NAVY, WHITE), 'yellow': (YELLOW, NAVY), 'slate': (SLATE, WHITE)}
    for i, (label, note) in enumerate(ex['steps']):
        if i < len(ex['steps']) - 1:
            page.line(xs[i] + 18, line_y, xs[i + 1] - 18, line_y, HAIR if i != 1 else NAVY, 2 if i == 1 else 1.25)
            page.ops[-1]['end_arrow'] = 'FILL_ARROW'
        page.sup(label, xs[i] - 54, 206, 108, 28, size=9, bold=True, align="center")
        if ex.get('actors'):
            name, colour = ex['actors'][i]
            fill, ink = actor_fill[colour]
            tw = 5.2 * len(name) + 14
            page.badge(name, xs[i] - tw / 2, 240, (tw, 16), fill, ink, 8, 'ROUND_RECTANGLE')
    for (a, b), fill, text, mark in [((0, 1), SLATE, ex['before'], 3), ((1, 2), YELLOW, ex['measure'], 1)]:
        page.rect(xs[a], 158, xs[b] - xs[a], 3, fill)
        page.rect(xs[a], 158, 2, 10, fill)
        page.rect(xs[b] - 2, 158, 2, 10, fill)
        page.sup(text, xs[a] + 2, 128, xs[b] - xs[a] - 4, 28, size=9, bold=True, align='center')
    page.marker(2, xs[0] - 18, 157)
    page.marker(1, xs[2] + 6, 157)
    # 96.4% stacked bar
    top = 284
    page.text(ex['bar_title'], L, top, 280, 14, size=10, bold=True)
    width, share = 280, ex['before_share']
    page.rect(L, top + 20, width * share / 100, 26, VIOLET)
    page.rect(L + width * share / 100, top + 20, width * (100 - share) / 100, 26, HAIR)
    page.text(f'{share:.1f}% before listing', L + 8, top + 20, 200, 26, size=10, color=WHITE, bold=True, middle=True)
    page.text(f'{100 - share:.1f}% after', L + width - 60, top + 50, 60, 14, size=10, align='right')
    # who is in the data
    sx, sw = 356, 294
    page.text('Who is in the data', sx, top, sw, 14, size=10, bold=True)
    page.rect(sx, top + 20, sw, 40, PAPER)
    page.rect(sx, top + 20, 4, 40, NAVY)
    page.text(ex['in_data'], sx + 36, top + 20, sw - 44, 40, size=10, middle=True, spacing=105,
              spans=[(0, ex['in_data'].index(':') + 1, {'bold': True})])
    page.rect(sx, top + 66, sw, 34, '#EEF0F3')
    page.text(ex['not_in_data'], sx + 36, top + 66, sw - 44, 34, size=10, color=GREY, middle=True,
              spans=[(0, ex['not_in_data'].index(':') + 1, {'bold': True})])
    page.marker(4, sx + sw - 16, top + 77)
    page.marker(3, L + width + 6, top + 50)
    page.caption(slide['figure'], ex['caption'], 400)
    page.caption('¹', ex['note'], 414)
    page.caption('²', ex['note2'], 428)
    page.caption('Scope:', slide['body'][0]['text'], 442)
    page.takeaways(slide['takeaways'], pos)


def slowdown(page, slide, pos):
    """Yearly same-day share as bars from zero, with period bands and dashed period averages.

    Native lines cannot be flipped through the CLI, so rising segments of a line chart would draw
    backwards; bars avoid that and keep the zero baseline.
    """
    page.chrome(slide)
    ex = slide['exhibit']
    years = ex['years']
    x0, x1, base, per, bar = 82, 616, 412, 4.6, 34  # 4.6 pt per percentage point, 0% at the baseline
    step = (x1 - x0) / (len(years) - 1)
    px = lambda i: x0 + i * step
    py = lambda share: base - share * per
    top = py(60)
    for band in ex['periods']:
        first, last = band['from'] - years[0]['year'], band['to'] - years[0]['year']
        left, right = px(first) - step / 2, px(last) + step / 2
        page.rect(left, top, right - left, base - top, band_fill(band['shade']))
        page.text(band['label'], left + 6, top + 6, right - left - 12, 14, size=10, bold=True)
        page.text(f"Average {band['average']:.1f}%", left + 6, top + 21, right - left - 12, 14, size=10, color=GREY)
        page.line(left + 4, py(band['average']), right - 4, py(band['average']), VIOLET, 1.25)
        page.ops[-1]['dash_style'] = 'DASH'
    for share in (20, 40):
        page.line(x0 - step / 2, py(share), x1 + step / 2, py(share), HAIR, .5)
        page.text(f'{share}%', L, py(share) - 6, 28, 12, size=8, color=GREY)
    page.text('0%', L, base - 6, 28, 12, size=8, color=GREY)
    for i, row in enumerate(years):
        value = row['share'] * 100
        x, y = px(i), py(value)
        light = row.get('incomplete')
        page.rect(x - bar / 2, y, bar, base - y, '#B9C1CC' if light else NAVY)
        # Labels sit inside the bar top so the dashed averages, drawn first, never cross them.
        page.text(f"{value:.1f}", x - 24, y + 4, 48, 14, size=10, bold=True, align='center',
                  color=NAVY if light else WHITE)
        page.sup(f"{row['year']}¹" if light else str(row['year']), x - 22, base + 4, 44, 14, size=10, align='center')
    page.line(x0 - step / 2, base, x1 + step / 2, base, NAVY, 1)
    page.marker(1, px(4) - 6, py(years[4]['share'] * 100) - 18)
    page.marker(2, px(9) + step / 2 - 20, top + 6)
    page.marker(3, px(3) + step / 2 - 20, top + 6)
    page.marker(4, px(5) + step / 2 - 20, top + 6)
    page.caption('Figure 3.', ex['caption'], base + 26)
    page.caption('¹', ex['note'], base + 40)
    page.takeaways(slide['takeaways'], pos)


def band_fill(shade):
    return {'paper': PAPER, 'violet': '#EEEBF5'}[shade]


def approach(page, slide, pos):
    """Four analyses fed by one dataset, each with a result preview and the solution step it feeds."""
    page.chrome(slide)
    ex = slide['exhibit']
    pw = R - L
    page.rect(L, TOP, pw, 24, PAPER)
    page.rect(L, TOP, 5, 24, YELLOW)
    page.text(ex['source'], L + 32, TOP, pw - 60, 24, size=10, bold=True, middle=True)
    page.marker(1, L + pw - 20, TOP + 6)
    width, top, h = PIPE_W, 166, 178
    fills = [(NAVY, WHITE), (VIOLET, WHITE), (YELLOW, NAVY), (SLATE, WHITE)]
    previews = [preview_waffle, preview_table, preview_bound, preview_bars]
    card_markers = {0: 2, 1: 3, 3: 4}
    for i, step in enumerate(ex['steps']):
        x = pipe_x(i)
        fill, ink = fills[i]
        page.line(x + width / 2, TOP + 24, x + width / 2, top - 1, SLATE, .75)
        page.ops[-1]['end_arrow'] = 'FILL_ARROW'
        page.rect(x, top, width, h, PAPER)
        page.rect(x, top, width, 26, fill)
        page.text(step['name'], x + 24, top, width - 30, 26, size=9, color=ink, bold=True, middle=True)
        page.text(step['question'], x + 8, top + 31, width - 16, 36, size=9, bold=True, spacing=100)
        previews[i](page, x + 8, top + 72, width - 16, 46, slide)
        page.text(step['headline'], x + 8, top + 124, width - 16, 26, size=9, bold=True, spacing=100)
        page.text(f"Feeds {step['feeds']}", x + 8, top + 157, width - 34, 13, size=9, color=SLATE, bold=True, middle=True)
        if i in card_markers:
            page.marker(card_markers[i], x + width - 20, top + 157)
        if i < 2:
            page.line(x + width + 1, top + 13, x + width + 10.5, top + 13, SLATE, .75)
            page.ops[-1]['end_arrow'] = 'FILL_ARROW'
    timeline(page, ex['timeline'], top + h + 22)
    page.takeaways(slide['takeaways'], pos)


def preview_waffle(page, x, y, w, h, slide):
    """Mini of the 120-term waffle: 64 terms lost significance."""
    gap = 1.4
    cell = (w - 19 * gap) / 20
    for i in range(120):
        row, col = divmod(i, 20)
        page.rect(x + col * (cell + gap), y + 2 + row * (cell + gap), cell, cell, YELLOW if i < 64 else HAIR)


def preview_table(page, x, y, w, h, slide):
    """Lowest adjusted bootstrap p against the 0.05 line: the closest any term gets to passing."""
    limit = .2
    px = lambda v: x + v / limit * w
    base = y + 32
    page.rect(px(0), base - 14, px(.05) - px(0), 14, '#FFF0A8')
    page.line(x, base, x + w, base, NAVY, .75)
    page.line(px(.05), base - 14, px(.05), base + 3, NAVY, .75)
    page.rect(px(.136) - 3.5, base - 10, 7, 7, VIOLET, 'ELLIPSE')
    page.text('Lowest p 0.136', px(.136) - 45, base - 27, 90, 12, size=8, bold=True, color=VIOLET, align='center')
    page.text('0.05', px(.05) - 15, base + 3, 30, 11, size=8, color=GREY, align='center')


def preview_bound(page, x, y, w, h, slide):
    """Mini of the bound chart: five short intervals inside the band, urgency running out of it."""
    rows = {r['term']: r for r in slide_by_id('equivalence')['exhibit']['rows']}
    lo, hi = -.15, .15
    px = lambda v: x + (v - lo) * w * .8 / (hi - lo)
    page.rect(px(-.05), y, px(.05) - px(-.05), 46, '#FFF0A8')
    page.line(px(0), y, px(0), y + 46, NAVY, .5)
    for i, term in enumerate(['family', 'basic needs', 'business', 'agency', 'third person', 'urgency']):
        r, cy = rows[term], y + 5 + i * 7.4
        page.line(px(r['ci90_low']), cy, px(r['ci90_high']), cy, VIOLET if term == 'urgency' else NAVY, 1.25)


def preview_bars(page, x, y, w, h, slide):
    """Mini of the five annual linear gains, bars from zero."""
    gains = [v['gain'] for _, v in sorted(slide_by_id('gain_uncertainty')['exhibit']['linear'].items())]
    for i, gain in enumerate(gains):
        height = gain * 110
        page.rect(x + i * 25, y + 46 - height, 18, height, NAVY)
    page.line(x, y + 46, x + w, y + 46, NAVY, .75)


def timeline(page, tl, top):
    """Years each analysis uses, on the same left and right edges as the cards."""
    label_w, x0 = 122, L + 126
    per = (R - x0) / 10
    page.text(tl['title'], L, top, label_w, 12, size=9, bold=True)
    for i, year in enumerate(range(2016, 2026)):
        page.text(str(year), x0 + i * per - 6, top, per + 12, 12, size=8, color=GREY, align='center')

    def span(first, last, y, h, fill):
        page.rect(x0 + (first - 2016) * per + 1, y, (last - first + 1) * per - 2, h, fill)
    rows = tl['rows']
    y = top + 14
    page.text(rows[0]['label'], L, y - 1, label_w, 22, size=8, bold=True, spacing=95)
    span(2016, 2025, y, 13, NAVY)
    page.text('all 1,453,840 loans', x0 + 6, y, 200, 13, size=8, color=WHITE, bold=True, middle=True)
    y += 22
    page.text(rows[1]['label'], L, y, label_w, 13, size=8, bold=True, middle=True)
    span(2016, 2023, y, 13, SLATE)
    span(2024, 2025, y, 13, YELLOW)
    page.text('train: 1,174,953 loans', x0 + 6, y, 220, 13, size=8, color=WHITE, bold=True, middle=True)
    page.text('test: 278,887', x0 + 8 * per + 4, y, 2 * per - 6, 13, size=8, bold=True, middle=True)
    y += 17
    page.text(rows[2]['label'], L, y, label_w, 22, size=8, bold=True, spacing=95)
    page.legend([('train', SLATE), ('test', YELLOW)], y + 24, L, gap=12)
    for test in range(2021, 2026):
        span(2016, test - 1, y, 6, SLATE)
        span(test, test, y, 6, YELLOW)
        y += 7.5


PIPE_W = 143


def pipe_x(i):
    """Card x: four equal cards across the content width."""
    return L + i * (PIPE_W + 11.5)


# Slide 8 panel (c): map frame matches scripts/build_country_map.py's 270:86 crop, and the table's
# share cells reuse that script's bins so one legend explains both.
MAP_PANEL = (L, TOP + 166, R - 16 - L, 148)
MAP_FRAME = (L + 10, TOP + 166 + 42, 250, 250 * 86 / 270)


def map_frame(cy: float) -> tuple:
    """Map image frame inside a country panel whose top is at cy."""
    return (L + 10, cy + 42, 250, 250 * 86 / 270)

MAP_PNG = ASSETS / 'maps/country_share_map.png'
TREND_EXTENT = (2015.6, 2025.4, 0.0, 0.6)  # must equal scripts/build_trend_chart.py EXTENT
_MAP_SPEC = importlib.util.spec_from_file_location('build_country_map', ROOT / 'scripts/build_country_map.py')
COUNTRY_MAP = importlib.util.module_from_spec(_MAP_SPEC)
_MAP_SPEC.loader.exec_module(COUNTRY_MAP)
NO_LOANS = COUNTRY_MAP.NO_LOANS


# Same-day cells: yellow tints by level, navy text, no legend (values are printed). Yellow keeps this
# column apart from the violet loan-share scale the shared legend explains.
SAME_DAY_FILLS = [(0.20, '#FFF7D1'), (0.35, '#FFEE94'), (0.50, '#FFE557'), (1.01, YELLOW)]


def same_day_fill(share: float) -> str:
    """Yellow step for a same-day share: under 20%, 20-35%, 35-50%, 50% or more."""
    return next(fill for limit, fill in SAME_DAY_FILLS if share < limit)


def share_style(share: float) -> tuple[str, str]:
    """Share-cell fill (the map's bin) and its text colour: white on the two dark steps."""
    fill = COUNTRY_MAP.share_colour(share)
    dark = [colour for _, colour in COUNTRY_MAP.BINS][2:]
    return fill, WHITE if fill in dark else NAVY


def panel(page, x, y, w, h, title, guide):
    """A light block with a bold header and a one-line reading guide."""
    page.rect(x, y, w, h, PAPER)
    page.rect(x, y, w, 2, HAIR)
    page.text(title, x + 10, y + 8, w - 20, 14, size=10, bold=True)
    if guide:
        page.text(guide, x + 10, y + 23, w - 20, 22, size=8, color=GREY, spacing=105)


def clustering(page, slide, pos):
    """Why the errors widen (illustrative dots), then which terms lost significance and the urgency example."""
    page.chrome(slide)
    ex = slide['exhibit']
    pw = R - L
    why = ex['why']
    panel(page, L, TOP, pw, 104, why['title'], why['guide'])
    dot, pitch, dy = 5, 8, TOP + 56
    for row in range(5):
        for col in range(16):
            page.rect(L + 14 + col * pitch, dy + row * pitch, dot, dot, NAVY, 'ELLIPSE')
    page.text(f"{why['hc3'][0]}\n{why['hc3'][1]}", L + 150, dy, 136, 38, size=9, color=GREY, spacing=105,
              spans=[(0, len(why['hc3'][0]), {'bold': True, 'color': NAVY})])
    page.line(L + 288, dy + 18, L + 312, dy + 18, SLATE, .75)
    page.ops[-1]['end_arrow'] = 'FILL_ARROW'
    x = L + 322
    for size in (5, 3, 2, 1, 1, 1):
        for row in range(5):
            for col in range(size):
                page.rect(x + col * pitch, dy + row * pitch, dot, dot, VIOLET, 'ELLIPSE')
        x += size * pitch + 10
    text = why['clustered']
    page.text(f'{text[0]}\n{text[1]}', L + 482, dy, pw - 490, 38, size=9, color=GREY, spacing=105,
              spans=[(0, len(text[0]), {'bold': True, 'color': VIOLET})])
    page.marker(1, L + pw - 22, TOP + 8)
    # Which terms lost significance
    ax, ay, aw, ah = L, TOP + 114, 290, 182
    panel(page, ax, ay, aw, ah, ex['terms']['title'], ex['terms']['guide'])
    cell, gap = 9, 2.6
    for g, group in enumerate(ex['groups']):
        x0 = ax + 12 + g * 140
        page.text(f"{group['name']}: {group['lost']} of {group['significant']} lost", x0, ay + 40, 130, 12, size=9, bold=True)
        for i in range(group['significant']):
            row, col = divmod(i, 8)
            page.rect(x0 + col * (cell + gap), ay + 56 + row * (cell + gap), cell, cell,
                      YELLOW if i < group['lost'] else NAVY)
    ly = ay + ah - 18
    page.legend([('lost', YELLOW), ('kept', NAVY, 'RECTANGLE', 3)], ly, ax + 12, gap=20)
    page.marker(2, ax + aw - 22, ay + 8)
    # Urgency
    bx, by, bw, bh = L + 300, ay, pw - 300, ah
    panel(page, bx, by, bw, bh, ex['urgency_panel']['title'], ex['urgency_panel']['guide'])
    x0, x1 = bx + 78, bx + bw - 18
    px = lambda p_value: x0 + (math.log10(p_value) + 3) / 3 * (x1 - x0)  # 0.001 .. 1; HC3 p sits at the floor
    axis = by + 150
    page.line(x0, axis, x1, axis, SLATE, .75)
    page.line(x0, by + 60, x0, axis, SLATE, .75)
    page.line(px(.05), by + 56, px(.05), axis, VIOLET, .75)
    page.ops[-1]['dash_style'] = 'DASH'
    page.text('significant', px(.05) - 74, by + 46, 70, 12, size=8, color=GREY, align='right')
    page.text('not significant', px(.05) + 4, by + 46, 74, 12, size=8, color=GREY)
    for value, name in [(.001, '<0.001'), (.01, '0.01'), (.05, '0.05'), (.1, '0.1'), (.5, '0.5'), (1, '1')]:
        page.line(px(value), axis, px(value), axis + 3, SLATE, .75)
        page.text(name, px(value) - 16, axis + 3, 32, 12, size=8, color=VIOLET if value == .05 else GREY,
                  bold=value == .05, align='center')
    page.text('p-value (log scale)', x0, axis + 15, x1 - x0, 12, size=8, color=GREY, align='center')
    for r, row in enumerate(ex['urgency']):
        y = by + 80 + r * 42
        page.text(row['model'].replace(' model', ''), bx + 10, y - 13, 62, 26, size=8, bold=True, middle=True,
                  spacing=100)
        page.line(px(.001) + 4, y, px(row['clustered']) - 5, y, SLATE, .75)
        page.ops[-1]['end_arrow'] = 'FILL_ARROW'
        page.rect(px(.001) - 4, y - 4, 8, 8, NAVY, 'ELLIPSE')
        page.rect(px(row['clustered']) - 4, y - 4, 8, 8, VIOLET, 'ELLIPSE')
        page.sup('Before: HC3 <0.001¹', x0 + 6, y + 5, 100, 12, size=8)
        page.text(f"After: clustered {row['clustered']:.2f}", px(.05) + 6, y + 5, 90, 12, size=8, bold=True,
                  color=VIOLET)
    page.marker(4, bx + bw - 22, by + 8)
    page.caption(slide['figure'], ex['caption'], ay + ah + 8, w=pw)
    page.caption('¹', ex['note'], ay + ah + 22, w=pw)
    page.takeaways(slide['takeaways'], pos)


def country_panel(page, ex, cx, cy, cw, ch, title, guide):
    """Map (image inserted later at map_frame(cy)) with a vertical legend, then the top-10 table."""
    panel(page, cx, cy, cw, ch, title, guide)
    # Map (image inserted later at MAP_FRAME) with a compact vertical legend to its right.
    mx, my, mw, mh = map_frame(cy)
    lx = mx + mw + 10
    page.text('Loan share', lx, my, 56, 12, size=8, color=GREY, bold=True)
    legend = [(colour, label) for (_, colour), label in zip(COUNTRY_MAP.BINS, COUNTRY_MAP.BIN_LABELS)]
    for i, (fill, label) in enumerate(legend + [(NO_LOANS, 'no loans'), (None, 'top 10')]):
        y = my + 12 * (i + 1)
        if fill is None:  # navy outline swatch, as drawn on the map
            page.swatch(lx, y, 8, 8, NAVY)
            page.swatch(lx + 1.2, y, 5.6, 5.6, PAPER)
        else:
            page.swatch(lx, y, 8, 8, fill)
        page.text(label, lx + 12, y, 44, 12, size=8, color=GREY)
    # Table: top 10 in one column; share cells use the map's colours, same-day is plain text.
    names = ex['country_names']
    rows = ex['country_shares'][:10]
    tx = cx + 336
    for label, off, w, align in [('Country', 12, 54, None), ('Region', 66, 56, None), ('Loans', 124, 38, 'right'),
                                 ('Share', 166, 36, 'center'), ('Same-day', 202, 40, 'center')]:
        page.text(label, tx + off, my, w, 12, size=8, color=GREY, bold=True, align=align)
    for k, item in enumerate(rows):
        y = my + 12 + k * 9
        page.text(str(k + 1), tx, y, 10, 12, size=8, color=GREY)
        page.text(names[item['country']], tx + 12, y, 54, 12, size=8, bold=True)
        page.text(item['region'], tx + 66, y, 58, 12, size=8, color=GREY)
        page.text(f"{item['loans']:,}", tx + 124, y, 38, 12, size=8, align='right')
        fill, ink = share_style(item['share'])
        page.rect(tx + 168, y + 1.2, 32, 8, fill)
        page.text(f"{item['share'] * 100:.1f}%", tx + 168, y + 0.4, 32, 12, size=8, color=ink,
                  bold=ink == WHITE, align='center')
        page.rect(tx + 206, y + 1.2, 32, 8, same_day_fill(item['same_day_share']))
        page.text(f"{item['same_day_share'] * 100:.0f}%", tx + 206, y + 0.4, 32, 12, size=8, align='center')


TERM_LABELS = {'third_person': 'Third person', 'basic_needs': 'Basic needs', 'first_person': 'First person'}


def subgroups(page, slide, pos):
    """Heat grid of equivalence verdicts by framing and subgroup, with counts for each model and outcome."""
    page.chrome(slide)
    ex = slide['exhibit']
    x0, cw, ch, gap, top = L + 92, 32, 20, 10, TOP + 34
    small, unknown = TINT_BAND, STAGE_FILLS[0]
    xs, k = [], 0
    for g, (group, levels) in enumerate(ex['groups']):
        gx = x0 + k * cw + g * gap
        page.text(group, gx, TOP + 2, cw * len(levels), 12, size=8, color=GREY, bold=True, align='center')
        page.line(gx + 2, TOP + 15, gx + cw * len(levels) - 4, TOP + 15, HAIR, .75)
        for level in levels:
            page.text(level, x0 + k * cw + g * gap - 6, TOP + 18, cw + 12, 12, size=8, color=GREY, align='center')
            xs.append(x0 + k * cw + g * gap)
            k += 1
    count_x, count_w = xs[-1] + cw + 12, 50
    page.text('Small in, of 10', count_x, TOP + 2, count_w * 3, 12, size=8, color=GREY, bold=True, align='center')
    page.line(count_x + 2, TOP + 15, count_x + count_w * 3 - 4, TOP + 15, HAIR, .75)
    for c, label in enumerate(ex['count_columns']):
        page.text(label, count_x + c * count_w, TOP + 18, count_w, 12, size=8, color=GREY, align='center')
    page.marker(4, count_x + count_w * 3 - 22, TOP + 1)
    hyp = {(t, c) for t, c in ex['hypotheses']}
    for r, row in enumerate(sorted(ex['rows'], key=lambda row: MEASURE_ORDER.index(measure_key(row['term'])))):
        y = top + r * (ch + 6)
        page.text(TERM_LABELS.get(row['term'], row['term'].capitalize()), L + 16, y + 3, 76, 14, size=9)
        EXTRA_IMAGES.append(('subgroups', measure_icon(row['term']), (L, y + 3.5, 12, 12)))
        for c, (cx, ok) in enumerate(zip(xs, row['cells'])):
            page.rect(cx + 1, y, cw - 2, ch, small if ok else unknown)
            if (row['term'], c) in hyp:
                page.rect(cx + cw / 2 - 3.5, y + ch / 2 - 3.5, 7, 7, NAVY, 'ELLIPSE')
        for c, value in enumerate((row['count'], row['expanded'], row['same_day'])):
            full = value == len(xs)
            page.text(str(value), count_x + c * count_w, y + 3, count_w, 14, size=9, bold=full,
                      color=NAVY if full else VIOLET, align='center')
        if row['term'] == 'urgency':
            page.marker(2, L + 62, y + 4)
    ly = top + len(ex['rows']) * (ch + 6) + 6
    names = ex['legend']
    page.legend([(names[0], small, 'RECTANGLE', 1), (names[1], unknown), (names[2], NAVY, 'ELLIPSE', 3)],
                ly, x0, span=xs[-1] + cw - x0, gap=26)
    page.caption(slide['figure'], ex['caption'], ly + 18, w=R - L)
    page.caption('¹', ex['note_sup'], ly + 31, w=R - L)
    page.takeaways(slide['takeaways'], pos)


def where(page, slide, pos):
    """(a) the country panel (map and top-10 table); (b) where the long waits are, as bars by country."""
    page.chrome(slide)
    ex = slide['exhibit']
    cx, cy, cw, ch = L, TOP, R - 16 - L, 148
    country_panel(page, ex, cx, cy, cw, ch, ex['panel']['title'], ex['panel']['guide'])
    page.marker(1, cx + cw - 22, cy + 8)
    page.marker(2, cx + cw - 12, cy + 54)
    lw = ex['long']
    by, bh = cy + ch + 8, 142
    panel(page, cx, by, cw, bh, lw['title'], lw['guide'])
    page.marker(3, cx + cw - 22, by + 8)
    # Stacked bars on one loan scale: within 24 hours, 1 day to 2 weeks, over 2 weeks (top three in navy).
    bands = ['#E2DCF0', '#B4A9D2']
    top = max(r['loans'] for r in lw['rows'])
    scale = 300 / top
    for k, row in enumerate(lw['rows']):
        y = by + 42 + 14 * k
        page.text(row['country'], cx + 10, y, 80, 12, size=9, bold=row['top3'])
        left = cx + 92
        for value, fill in [(row['within_24h'], bands[0]), (row['one_to_14'], bands[1]),
                            (row['count'], NAVY if row['top3'] else SLATE)]:
            page.rect(left, y + 1.5, value * scale, 10, fill)
            left += value * scale
        label = f"{row['count']:,} over 2 weeks · {row['own_share'] * 100:.1f}%"
        page.text(label, left + 4, y, 200, 12, size=8, color=NAVY if row['top3'] else GREY, bold=row['top3'])
        if row['country'] == 'Tajikistan':
            page.marker(4, left + 4 + 4.3 * len(label) + 8, y)
    page.legend(list(zip(lw['legend'], bands + [NAVY])), by + 42 + 14 * 6 + 2, cx + 92, gap=18)
    page.caption(slide['figure'], ex['caption'], by + bh + 8, w=cw)
    page.takeaways(slide['takeaways'], pos)


STATUS_COLOURS = {'bounded': NAVY, 'mixed': SLATE, 'unresolved': VIOLET}
# Slide 7's measure key sets the names, order and icons reused on every slide that lists the measures.
MEASURE_ORDER = ['family', 'business', 'basic_needs', 'agency', 'gratitude', 'urgency', 'first_person', 'third_person',
                 'sentiment']
MEASURE_ICONS = {'family': 'family_restroom', 'business': 'storefront', 'basic_needs': 'water_drop', 'agency': 'bolt',
                 'gratitude': 'favorite', 'urgency': 'schedule', 'first_person': 'person',
                 'third_person': 'record_voice_over', 'sentiment': 'sentiment_satisfied'}


def measure_key(term: str) -> str:
    """Canonical measure id for a storyline term such as 'basic needs' or 'sentiment (+0.5 score)'."""
    return 'sentiment' if term.startswith('sentiment') else term.replace(' ', '_')


def measure_icon(term: str) -> Path:
    return ASSETS / 'icons' / f'{MEASURE_ICONS[measure_key(term)]}-navy.png'


def forest(page, slide, pos):
    """Two yellow areas (within ±5%, 5-10%), verdict groups, direction arrows and a legend under the plot."""
    page.chrome(slide)
    ex = slide['exhibit']
    x0, x1, lo, hi = L + 66, 420, -.15, .11
    scale = (x1 - x0) / (hi - lo)
    px = lambda value: x0 + (value - lo) * scale
    rx, track = 440, 150
    page.text('No difference', px(0) - 40, TOP + 2, 80, 12, size=8, color=NAVY, bold=True, align='center')
    page.text('Records with no mention', rx, TOP + 2, track + 40, 12, size=8, color=GREY, bold=True)
    y = TOP + 20
    header = {}
    for group in ex['groups']:
        rows = sorted((row for row in ex['rows'] if row['status_both_specs'] == group['status']),
                      key=lambda row: MEASURE_ORDER.index(measure_key(row['term'])))
        colour = STATUS_COLOURS[group['status']]
        page.line(L, y - 3, R - 6, y - 3, HAIR, .5)
        page.sup(group['label'], L, y, 330, 13, size=9, color=colour, bold=True)
        header[group['status']] = (L + 4.2 * len(group['label']) + 8, y)
        if group['status'] == 'bounded':
            page.text(ex['t4_tag'], rx, y + 1, track + 40, 12, size=8, color=SLATE)
        top = y + 16
        bottom = top + 20 * len(rows)
        page.rect(px(-.10), top - 2, px(.10) - px(-.10), bottom - top + 2, BAND_OUTER)
        page.rect(px(-.05), top - 2, px(.05) - px(-.05), bottom - top + 2, TINT_BAND)
        page.line(px(0), top - 2, px(0), bottom, NAVY, .75)
        for k, row in enumerate(rows):
            ry = top + 20 * k
            centre = ry + 7.5
            name = 'Sentiment' if row['term'].startswith('sentiment') else row['term'].capitalize()
            page.text(name, L + 16, ry + 1, 84, 14, size=9)
            EXTRA_IMAGES.append(('equivalence', measure_icon(row['term']), (L, ry + 1.5, 12, 12)))
            page.line(px(row['ci90_low']), centre, px(row['ci90_high']), centre, colour, 2)
            page.rect(px(row['estimate']) - 3.5, centre - 3.5, 7, 7, colour, 'ELLIPSE')
            page.rect(rx, centre - 3.5, track, 7, '#ECEAE4')
            page.rect(rx, centre - 3.5, track * row['no_mention'], 7, colour)
            page.text(f"{row['no_mention'] * 100:.1f}%", rx + track + 5, ry + 2, 36, 12, size=8,
                      color=colour, bold=group['status'] == 'unresolved')
        y = bottom + 8
    end = y - 8
    for value, name in [(-.1, '−10%'), (-.05, '−5%'), (0, '0'), (.05, '+5%'), (.1, '+10%')]:
        page.line(px(value), end, px(value), end + 3, RULE, .75)
        page.text(name, px(value) - 20, end + 4, 40, 12, size=8, color=GREY, align='center')
    for value, name in [(0, '0%'), (1, '100%')]:
        page.text(name, rx + value * track - 15, end + 4, 30, 12, size=8, color=GREY, align='center')
    # Direction: a positive coefficient on log(1 + days) means a longer wait (src/data_loader.py).
    ay = end + 18
    page.text('Faster funding', px(0) - 66, ay, 60, 12, size=8, color=SLATE, bold=True, align='right')
    page.line(px(0) - 98, ay + 5.1, px(0) - 70, ay + 5.1, SLATE, .75)  # on the label x-height centre (measured)
    page.ops[-1]['start_arrow'] = 'FILL_ARROW'
    page.text('Slower funding', px(0) + 6, ay, 60, 12, size=8, color=SLATE, bold=True)
    page.line(px(0) + 70, ay + 5.1, px(0) + 98, ay + 5.1, SLATE, .75)
    page.ops[-1]['end_arrow'] = 'FILL_ARROW'
    # Axis title, then the legend to its right; the bands are labelled by the axis itself.
    ly, lx = ay + 15, px(0) + 60
    page.text('Change in funding time, %', px(0) - 55, ly, 110, 12, size=8, color=GREY, align='center')
    page.line(lx, ly + 5.1, lx + 20, ly + 5.1, NAVY, 2)
    page.rect(lx + 6.5, ly + 1.6, 7, 7, NAVY, "ELLIPSE")
    page.text('Estimate, 90% range', lx + 24, ly, 90, 12, size=8, color=GREY)
    page.marker(2, px(.05) + 4, TOP + 2.5)
    page.marker(1, *header['bounded'])
    page.marker(3, *header['unresolved'])
    page.marker(4, rx + 3.3 * len(ex['t4_tag']) + 8, header['bounded'][1] + 0.5)
    page.caption(slide['figure'], ex['caption'], ly + 16)
    page.caption('¹', ex['note_sup'], ly + 29)
    page.takeaways(slide['takeaways'], pos)


def regions(page, slide, pos):
    """One panel per two-country region (its country mix, two ranges) and a strip of countries per region."""
    page.chrome(slide)
    ex = slide['exhibit']
    pw = R - 16 - L
    x0, x1, lo, hi = L + 140, 610, -.27, .13
    scale = (x1 - x0) / (hi - lo)
    px = lambda value: x0 + (value - lo) * scale
    page.text('No difference', px(0) - 40, TOP + 2, 80, 12, size=8, color=NAVY, bold=True, align='center')
    py, ph = TOP + 18, 92
    for i, row in enumerate(ex['rows']):
        page.rect(L, py, pw, ph, PAPER)
        page.rect(L, py, pw, 2, HAIR)
        page.text(row['region'], L + 10, py + 8, 200, 14, size=10, bold=True)
        page.text(f"{row['countries']} countries · {row['loans']:,} loans", L + 10, py + 23, 200, 12, size=8, color=GREY)
        if i == 1:
            page.marker(4, L + 10 + 6.1 * len(row['region']) + 6, py + 8.5)
        # Country mix bar, top right of the panel.
        bx, bw, bx_end = 470, 140, 610
        page.text('Loan mix', bx - 46, py + 9, 42, 12, size=8, color=GREY, bold=True, align='right')
        left = bx
        for k, part in enumerate(row['mix']):
            width = bw * part['share']
            page.rect(left, py + 10, width, 10, NAVY if k == 0 else SLATE)
            left += width
        first, second = row['mix'][0], row['mix'][1]
        page.text(f"{first['country']} {first['share'] * 100:.1f}%", bx, py + 22, 90, 12, size=8, bold=True)
        page.text(f"{second['country']} {second['share'] * 100:.1f}%", bx_end - 90, py + 22, 90, 12, size=8,
                  color=SLATE, bold=True, align='right')
        page.line(px(0), py + 40, px(0), py + ph - 6, NAVY, .75)
        for k, (key, colour) in enumerate([('normal', NAVY), ('heuristic', VIOLET)]):
            centre = py + 52 + 22 * k
            low, high = row['normal_ci'] if key == 'normal' else row['heuristic_ci']
            page.sup(ex['row_labels'][key], L + 10, centre - 6.5, 130, 13, size=8, color=colour, bold=key == 'heuristic')
            page.line(px(low), centre, px(high), centre, colour, 3)
            page.rect(px(row['estimate']) - 4, centre - 4, 8, 8, colour, 'ELLIPSE')
            if i == 0 and key == 'normal':
                page.marker(1, L + 10 + 3.9 * len(ex['row_labels'][key]) + 6, centre - 6)
            if i == 0 and key == 'heuristic':
                page.marker(2, px(high) + 6, centre - 6)
        py += ph + 6
    end = py - 6
    for value, name in [(-.2, '−20%'), (-.1, '−10%'), (0, '0'), (.1, '+10%')]:
        page.line(px(value), end, px(value), end + 3, RULE, .75)
        page.text(name, px(value) - 20, end + 4, 40, 12, size=8, color=GREY, align='center')
    ay = end + 18
    page.text('Faster funding', px(0) - 66, ay, 60, 12, size=8, color=SLATE, bold=True, align='right')
    page.line(px(0) - 98, ay + 5.1, px(0) - 70, ay + 5.1, SLATE, .75)
    page.ops[-1]['start_arrow'] = 'FILL_ARROW'
    page.text('Slower funding', px(0) + 6, ay, 60, 12, size=8, color=SLATE, bold=True)
    page.line(px(0) + 70, ay + 5.1, px(0) + 98, ay + 5.1, SLATE, .75)
    page.ops[-1]['end_arrow'] = 'FILL_ARROW'
    # Countries behind each region: one dot per country, the two thin regions in violet.
    sy = ay + 20
    page.text(ex['strip_title'], L, sy, 160, 12, size=8, color=GREY, bold=True)
    page.marker(3, L + 4.3 * len(ex['strip_title']) + 6, sy + 0.5)
    thin = {row['region'] for row in ex['rows']}
    for k, item in enumerate(ex['region_counts']):
        col, line = divmod(k, 3)
        x, y = L + col * 300, sy + 14 + 11 * line
        colour = VIOLET if item['region'] in thin else SLATE
        page.text(item['region'], x, y, 86, 12, size=8, color=colour, bold=item['region'] in thin)
        for d in range(item['countries']):
            page.rect(x + 90 + 7 * d, y + 2.6, 5, 5, colour, 'ELLIPSE')
        page.text(str(item['countries']), x + 90 + 7 * item['countries'] + 3, y, 24, 12, size=8, color=colour, bold=True)
    page.caption(ex.get('figure', 'Figure A1.'), ex['caption'], sy + 14 + 33 + 8)
    page.caption('¹', ex['note_sup'], sy + 14 + 33 + 21)
    page.takeaways(slide['takeaways'], pos)


def persist(page, slide, pos):
    """Tests passing at each stage, framings against loan details on one scale, and two real-unit cards."""
    page.chrome(slide)
    ex = slide['exhibit']
    pw, fun = R - L, ex['funnel']
    panel(page, L, TOP, pw, 94, fun['title'], fun['guide'])
    cell, gap, cols = 8, 2, 12
    block_w = cols * cell + (cols - 1) * gap
    step = (pw - 24 - block_w - 64) / 2
    for s, stage in enumerate(fun['stages']):
        x, y = L + 12 + s * step, TOP + 56
        page.text(stage['label'], x, y - 15, step - 8, 12, size=9, bold=True)
        for i in range(fun['tests']):
            row, col = divmod(i, cols)
            page.rect(x + col * (cell + gap), y + row * (cell + gap), cell, cell,
                      VIOLET if i < stage['passes'] else HAIR)
        page.text(f"{stage['passes']} of {fun['tests']} pass", x + block_w + 8, y - 1, 56, 13, size=9, bold=True, color=VIOLET)
        if s < 2:
            page.line(x + block_w + 8, y + 22, x + step - 8, y + 22, SLATE, .75)
            page.ops[-1]['end_arrow'] = 'FILL_ARROW'
    page.marker(1, L + pw - 22, TOP + 8)
    # Framings against loan details
    top, h, aw = TOP + 102, 200, 396
    scale = ex['scale']
    panel(page, L, top, aw, h, scale['title'], '')
    rows = scale['loan'] + scale['framing']
    x0, x1, lo = L + 136, L + aw - 44, -12
    hi = max(r['ci'][1] for r in rows) * 1.02
    px = lambda value: x0 + (value - lo) / (hi - lo) * (x1 - x0)
    first, pitch, split = top + 38, 10.4, 5
    axis = first + pitch * len(rows) + split
    page.rect(px(-5), first - 3, px(5) - px(-5), axis - first + 3, TINT_BAND)
    page.line(px(0), first - 3, px(0), axis, NAVY, .75)
    page.line(x0, axis, x1, axis, SLATE, .75)
    page.text('Faster', px(0) - 34, top + 24, 30, 11, size=8, color=SLATE, bold=True, align='right')
    page.text('Slower', px(0) + 4, top + 24, 40, 11, size=8, color=SLATE, bold=True)
    for value, name in [(0, '0'), (20, '+20'), (40, '+40'), (60, '+60')]:
        page.line(px(value), axis, px(value), axis + 3, SLATE, .75)
        page.text(name, px(value) - 16, axis + 3, 32, 11, size=8, color=GREY, align='center')
    page.text('% change in (1 + days)', L + 10, axis + 3, x0 - L - 16, 11, size=8, color=GREY)
    for k, row in enumerate(rows):
        loan = k < len(scale['loan'])
        y = first + k * pitch + (0 if loan else split)
        colour = NAVY if loan else VIOLET
        if not loan:
            EXTRA_IMAGES.append(('persist', measure_icon(row['key']), (L + 10, y - .5, 9.5, 9.5)))
        page.text(row['label'], L + 23 if not loan else L + 10, y - 1.5, x0 - L - 26, 11, size=8, bold=loan, color=NAVY if loan else GREY)
        page.line(px(row['ci'][0]), y + 4, px(row['ci'][1]), y + 4, colour, 1.25)
        page.rect(px(row['pct']) - 2.5, y + 1.5, 5, 5, colour, 'ELLIPSE')
        page.text(f"{row['pct']:+.1f}%".replace('-', '−'), L + aw - 42, y - 1.5, 36, 11, size=8, bold=loan, color=colour, align='right')
    divider = first + pitch * len(scale['loan']) + split / 2 - 1.5
    page.line(L + 10, divider, L + aw - 8, divider, HAIR, .5)
    page.marker(3, L + aw - 22, top + 8)
    # Real-unit cards
    cx, cw, card_h = L + aw + 10, pw - aw - 10, 96
    for k, item in enumerate(ex['cards']):
        y = top + k * (card_h + 8)
        page.rect(cx, y, cw, card_h, PAPER)
        page.rect(cx, y, cw, 2, [NAVY, VIOLET][k])
        page.text(item['name'], cx + 10, y + 8, cw - 50, 13, size=10, bold=True)
        page.text(item['value'], cx + 10, y + 24, cw - 20, 24, size=18, bold=True)
        page.text(item['label'], cx + 10, y + 50, cw - 20, 22, size=8, color=GREY, spacing=100)
        page.rect(cx + 10, y + 74, cw - 20, 4, HAIR)
        page.rect(cx + 10, y + 74, (cw - 20) * item['share'], 4, NAVY)
        page.text(item['share_label'], cx + 10, y + 80, cw - 20, 11, size=8, color=GREY)
    page.marker(2, cx + cw - 22, top + 8)
    page.marker(4, cx + cw - 38, top + 8)
    page.caption(slide['figure'], ex['note'], top + h + 8, w=pw)
    page.caption('Scale.', ex['note2'], top + h + 21, w=pw)
    page.takeaways(slide['takeaways'], pos)


STAGE_FILLS = ['#C4BBDF', VIOLET, NAVY]  # text form, lexicon and sentiment, TF-IDF


def forecast(page, slide, pos):
    """MAE pairs per year (top) and the gain split by text feature group (bottom)."""
    page.chrome(slide)
    exhibit = slide['exhibit']
    base, per, x0, group, bar = 300, 13, L + 4, 90, 36
    legend_y = TOP + 2
    page.legend([(exhibit['series'][0], SLATE), (exhibit['series'][1], NAVY, 'RECTANGLE', 2)], legend_y, L, gap=24, size=10)
    for i, row in enumerate(exhibit['data']):
        x = x0 + i * group
        for j, (value, fill) in enumerate(zip(row['values'], [SLATE, NAVY])):
            h = value * per
            bx = x + j * (bar + 2)
            page.rect(bx, base - h, bar, h, fill)
            page.text(f'{value:.3f}', bx - 5, base - h - 15, bar + 10, 13, size=9, color=GREY if j == 0 else NAVY,
                      bold=j == 1, align='center')
        page.text(str(row['year']), x, base + 3, bar * 2 + 2, 13, size=9, align='center')
    page.line(L, base, L + 5 * group - 8, base, NAVY, 1)
    # Gain by text feature group, one stacked bar per year, in nesting order.
    ty = base + 22
    page.sup(exhibit['breakdown_title'], L, ty, 200, 13, size=9, bold=True)
    page.marker(4, L + 4.6 * len(exhibit['breakdown_title']) + 8, ty + 0.5)
    scale, bx0 = 900, L + 40
    for k, row in enumerate(exhibit['breakdown']):
        y = ty + 17 + 15 * k
        page.text(str(row['year']), L, y, 34, 12, size=8, color=GREY)
        left = bx0
        for value, fill in zip(row['stages'], STAGE_FILLS):
            page.rect(left, y + 1.5, value * scale, 9, fill)
            left += value * scale
        page.text(f"{row['total']:.3f}", left + 4, y, 40, 12, size=8, color=NAVY, bold=True)
    ly = ty + 17 + 15 * 5 + 2
    lx = bx0
    for label, fill in zip(exhibit['stage_labels'], STAGE_FILLS):
        page.rect(lx, ly + 1.6, 9, 7, fill)
        page.text(label, lx + 13, ly, 4.2 * len(label) + 6, 12, size=8, color=GREY)
        lx += 13 + 4.2 * len(label) + 16
    figure = slide['key_figures'][0]
    key_card(page, figure, 498, TOP, 152, 104, YELLOW, 24)
    key_card(page, {'value': '5 of 5', 'label': 'years with lower error'}, 498, 246, 152, 92, VIOLET, 24)
    key_card(page, {'value': '728,640', 'label': 'evaluation records'}, 498, 350, 152, 92, SLATE, 24)
    page.marker(1, 498 + 152 - 22, TOP + 10)
    page.marker(3, 498 + 152 - 22, 246 + 10)  # gain stays positive every year
    page.caption(slide['figure'], exhibit['caption'], ly + 16)
    page.caption('¹', exhibit['note_sup'], ly + 29)
    page.takeaways(slide['takeaways'], pos)


def gains(page, slide, pos):
    """One chart: per year, the linear model and the larger tree, each with month (thick) and country (thin) ranges."""
    page.chrome(slide)
    ex = slide['exhibit']
    years, pw, h, aw = sorted(ex['linear']), R - L, 296, 396
    panel(page, L, TOP, aw, h, ex['title'], ex['guide'])
    x0, x1, lo, hi = L + 46, L + aw - 48, -.22, 1.0
    px = lambda value: x0 + (value - lo) / (hi - lo) * (x1 - x0)
    first, pitch, tier = TOP + 56, 48, 16
    axis = first + pitch * 5 - 12
    page.line(px(0), TOP + 44, px(0), axis, NAVY, .75)
    page.line(x0, axis, x1, axis, SLATE, .75)
    for value, name in [(0, '0'), (.25, '0.25'), (.5, '0.5'), (.75, '0.75')]:
        page.line(px(value), axis, px(value), axis + 3, SLATE, .75)
        page.text(name, px(value) - 16, axis + 3, 32, 11, size=8, color=GREY, align='center')
    page.text('Days', L + 10, axis + 3, 34, 11, size=8, color=GREY)
    for k, year in enumerate(years):
        y = first + k * pitch
        page.text(year, L + 10, y + tier / 2 - 7, 36, 14, size=9, color=GREY, middle=True)
        if k:
            page.line(L + 10, y - 15, L + aw - 10, y - 15, HAIR, .5)
        for row, colour, source in ((0, NAVY, ex['linear'][year]), (1, VIOLET, ex['large_tree'][year])):
            cy = y + row * tier
            page.line(px(source['country'][0]), cy, px(source['country'][1]), cy, colour, .75)
            page.line(px(source['month'][0]), cy, px(source['month'][1]), cy, colour, 3.5)
            page.rect(px(source['gain']) - 3.5, cy - 3.5, 7, 7, colour, 'ELLIPSE')
            page.rect(px(source['gain']) - 2, cy - 2, 4, 4, WHITE, 'ELLIPSE')
            page.text(f"{source['gain']:.3f}".replace('-', '−'), x1 + 2, cy - 6, 38, 12, size=8, bold=True, color=colour, align='right')
    names = ex['legend']
    page.legend([(names[0], NAVY), (names[1], SLATE, 'BAR', 1), (names[2], VIOLET, 'RECTANGLE', 2), (names[3], SLATE, 'RULE', 3)],
                TOP + h + 6, L, gap=14)
    card = ex['scorecard']
    cx, cw = L + aw + 10, pw - aw - 10
    panel(page, cx, TOP, cw, h, card['title'], card['guide'])
    left, right = cx + 12, cx + cw / 2 + 12
    icons = ('calendar_month-navy.png', 'public-violet.png')
    for c, label, icon in zip((left, right), card['columns'], icons):
        EXTRA_IMAGES.append(('gain_uncertainty', ASSETS / 'icons' / icon, (c, TOP + 49, 12, 12)))
        page.text(label, c + 15, TOP + 50, 70, 12, size=8, color=GREY, bold=True)
    dot, step = 6.5, 9
    for r, (name, month, country, meaning, month_years, country_years) in enumerate(card['rows']):
        y, colour = TOP + 68 + r * 76, VIOLET if r == 1 else NAVY
        page.line(cx + 10, y - 3, cx + cw - 10, y - 3, HAIR, .5)
        page.text(name, cx + 12, y + 1, cw - 22, 12, size=9, bold=True)
        page.text(meaning, cx + 12, y + 14, cw - 22, 12, size=8, color=GREY)
        mid = y + 44
        for c, count, flags in ((left, month, month_years), (right, country, country_years)):
            page.text(str(count), c, mid - 10, 13, 20, size=14, bold=True, color=colour, middle=True)
            for n, cleared in enumerate(flags):
                dx = c + 16 + n * step
                page.rect(dx, mid - dot / 2, dot, dot, colour if cleared else SLATE, 'ELLIPSE')
                if not cleared:
                    page.rect(dx + 1.25, mid - dot / 2 + 1.25, dot - 2.5, dot - 2.5, PAPER, 'ELLIPSE')
        page.line(left + 66, mid, right - 6, mid, SLATE, .75)
        page.ops[-1]['end_arrow'] = 'FILL_ARROW'
    page.legend([(card['reading'][0], SLATE, 'ELLIPSE'), (card['reading'][1], SLATE, 'HOLLOW')], TOP + h - 17, cx + 12, gap=10)
    page.caption(slide['figure'], ex['caption'], TOP + h + 24, w=pw)
    page.caption('¹', ex['note_sup'], TOP + h + 37, w=pw)
    page.marker(4, L + label_width(ex['note_sup']) - 8, TOP + h + 36)
    page.takeaways(slide['takeaways'], pos)


VERDICT_FILLS = {'yes': NAVY, 'unclear': SLATE, 'not_yet': VIOLET}

def supports(page, slide):
    """2x2 board: per block a question, verdict tag, key figure, evidence and a 'so what' line; then a strip."""
    page.chrome(slide)
    gap, bw, bh = 16, (FULL - L - 16) / 2, 142
    for k, block in enumerate(slide['blocks']):
        x, y = L + (k % 2) * (bw + gap), TOP + (k // 2) * (bh + gap)
        fill = VERDICT_FILLS[block['tone']]
        page.rect(x, y, bw, bh, PAPER)
        page.rect(x, y, bw, 3, fill)
        tag_w = 6.2 * len(block['verdict']) + 20
        page.text(block['question'], x + 18, y + 16, bw - 54 - tag_w, 16, size=11, color=GREY, bold=True)
        page.badge(block['verdict'], x + bw - 18 - tag_w, y + 14, (tag_w, 20), fill, WHITE, 9, 'ROUND_RECTANGLE')
        page.text(block['figure'], x + 18, y + 38, bw - 36, 36, size=28, bold=True)
        page.text(block['evidence'], x + 18, y + 78, bw - 36, 30, size=10, color=GREY, spacing=110)
        if block.get('so_what'):
            page.text(block['so_what'], x + 18, y + bh - 26, bw - 36, 16, size=10, bold=True, color=fill)
    sy = TOP + 2 * bh + gap + 12
    page.rect(L, sy, 2 * bw + gap, 28, PAPER)
    page.rect(L, sy, 4, 28, YELLOW)
    page.text(slide['next']['text'], L + 16, sy, 2 * bw + gap - 32, 28, size=11, bold=True, middle=True)


GATE_X = [L + i * 306 for i in range(3)]


GATE_ICONS = ['fact_check-navy.png', 'table_rows-navy.png', 'science-navy.png']
SOLUTION_ICONS = ['target-navy.png', 'groups-navy.png', 'science-navy.png']


SOLUTION_W, SOLUTION_GAP = 187, 22.75
SOLUTION_WHEN = ['post_add-navy.png', 'hourglass_top-navy.png', 'science-navy.png']
SOLUTION_WHO = ['desktop_windows-navy.png', 'handshake-navy.png', 'manage_search-navy.png']


def solution(page, slide, pos):
    """Predict, Prioritise and Test as three linked cards, each with what, how and its evidence."""
    page.chrome(slide)
    top, h, pitch = TOP, 316, 48
    fills = [(NAVY, WHITE), (VIOLET, WHITE), (YELLOW, NAVY)]
    for i, step in enumerate(slide['steps']):
        x = L + i * (SOLUTION_W + SOLUTION_GAP)
        card(page, x, top, SOLUTION_W, h, fills[i][0])
        page.badge(step['n'], x + 12, top + 14, (26, 26), *fills[i], 10)
        page.text(step['name'], x + 12, top + 48, SOLUTION_W - 44, 16, size=12, bold=True)
        page.marker(i + 1, x + SOLUTION_W - 22, top + 50)
        page.text('What', x + 12, top + 72, 120, 12, size=8, color=GREY, bold=True)
        page.text(step['action'], x + 12, top + 84, SOLUTION_W - 24, 44, size=10, bold=True, spacing=105)
        for k, (label, value, colour) in enumerate((('Who', step['who'], GREY), ('When', step['when'], GREY), ('Status', step['status'], VIOLET))):
            y = top + 134 + k * pitch
            page.text(label, x + 32, y, 120, 12, size=8, color=GREY, bold=True)
            page.text(value, x + 32, y + 12, SOLUTION_W - 44, 28, size=10, color=colour, bold=label == 'Status', spacing=105)
            if label == 'Status':
                page.rect(x + 16, y + 14, 8, 8, VIOLET, 'ELLIPSE')
            else:
                icon = SOLUTION_WHO[i] if label == 'Who' else SOLUTION_WHEN[i]
                EXTRA_IMAGES.append(('solution', ASSETS / 'icons' / icon, (x + 12, y + 10, 16, 16)))
        page.line(x + 12, top + h - 30, x + SOLUTION_W - 12, top + h - 30, HAIR, .75)
        page.text(f"Evidence: {step['evidence']}", x + 12, top + h - 25, SOLUTION_W - 24, 12, size=8, color=GREY)
        if i == 0:
            page.marker(4, x + SOLUTION_W - 22, top + 134 + 2 * pitch - 1)
        if i < 2:
            page.line(x + SOLUTION_W + 3, top + h / 2, x + SOLUTION_W + SOLUTION_GAP - 3, top + h / 2, SLATE, .75)
            page.ops[-1]['end_arrow'] = 'FILL_ARROW'
    page.takeaways(slide['takeaways'], pos)


def gates(page, slide):
    """Three steps as full cards with labelled rows; then either a ladder of claims or a stop line."""
    page.chrome(slide)
    ladder = slide.get('ladder')
    width, top = 262, 136
    h = 226 if ladder else 270
    fills = [(NAVY, WHITE), (VIOLET, WHITE), (YELLOW, NAVY)]
    for i, (step, x) in enumerate(zip(slide['steps'], GATE_X)):
        card(page, x, top, width, h, fills[i][0])
        page.badge(step['n'], x + 14, top + 14, (30, 30), *fills[i], 11)
        page.text(step['name'], x + 14, top + 52, width - 28, 16, size=12, bold=True)
        rows = step.get('rows') or [['Question', step['question']], ['Do', step['do']], ['Done when', step['done']]]
        pitch = 50 if ladder else 62
        for j, (name, value) in enumerate(rows):
            y = top + 76 + j * pitch
            page.text(name, x + 14, y, 120, 12, size=8, color=GREY, bold=True)
            page.text(value, x + 14, y + 12, width - 28, pitch - 14, size=10, color=NAVY if j == 0 else GREY,
                      bold=j == 0, spacing=105)
        if i < 2:
            page.line(x + width + 8, top + h / 2, x + width + 36, top + h / 2, SLATE, .75)
            page.ops[-1]['end_arrow'] = 'FILL_ARROW'
    if not ladder:
        page.text(slide['stop'], L, top + h + 18, FULL - L, 14, size=11, color=SLATE, bold=True)
        return
    y = 376
    page.text(ladder['title'], L, y, 600, 14, size=10, bold=True, color=VIOLET)
    chip_w, gap = (FULL - L - 3 * 24) / 4, 24
    for i, (stage, claim) in enumerate(ladder['steps']):
        x = L + i * (chip_w + gap)
        page.rect(x, y + 20, chip_w, 40, PAPER)
        page.rect(x, y + 20, 4, 40, [SLATE, NAVY, VIOLET, YELLOW][i])
        page.text(f'{stage}\n{claim}', x + 12, y + 20, chip_w - 18, 40, size=10, middle=True, spacing=105,
                  spans=[(0, len(stage), {'bold': True, 'color': GREY, 'font_size': 8})])
        if i < 3:
            page.line(x + chip_w + 3, y + 40, x + chip_w + gap - 3, y + 40, SLATE, .75)
            page.ops[-1]['end_arrow'] = 'FILL_ARROW'
    page.text(ladder['stop'], L, y + 68, FULL - L, 14, size=10, color=SLATE, bold=True)


def chip_link(page, label, x, y, fill, urls, ink=WHITE):
    """Small rounded "→N" chip linking to slide N (a number or an appendix label)."""
    text = f'→{label}'
    chip = page.badge(text, x, y, (28, 16), fill, ink, 8, 'ROUND_RECTANGLE')
    page.ops.append({'op': 'style-text', 'element': chip, 'start': 0, 'end': len(text),
                     'link': urls[label], 'color': ink, 'underline': False})


TREND_FRAME = (L + 34, TOP + 20, 560, 168)  # matches scripts/build_trend_chart.py's 8 x 2.4 in figure
TREND_PNG = ASSETS / 'charts/yearly_trend.png'


def problem(page, slide, pos):
    """Hero: yearly same-day share and long waits (PNG, native labels); below, the funding-time strip."""
    page.chrome(slide)
    ex = slide['exhibit']
    fx, fy, fw, fh = TREND_FRAME
    x0, x1, y0, y1 = TREND_EXTENT
    X = lambda year: fx + (year - x0) / (x1 - x0) * fw
    Y = lambda share: fy + fh - (share - y0) / (y1 - y0) * fh
    # Legend, period bands and gridlines sit behind the transparent chart image.
    # Legend under the plot, drawn with the chart's own symbols and centred on the labels' x-height.
    ly = fy + fh + 18
    mid = ly + 5.1
    lx = fx
    page.rect(lx, mid - 4, 20, 8, '#C4BBDF')
    page.line(lx, mid - 4, lx + 20, mid - 4, VIOLET, 2)
    page.text(ex['trend_legend'][0], lx + 25, ly, 110, 12, size=8, color=GREY)
    lx += 135
    page.line(lx, mid, lx + 20, mid, NAVY, 2)
    page.rect(lx + 7, mid - 3, 6, 6, NAVY, 'ELLIPSE')
    page.text(ex['trend_legend'][1], lx + 25, ly, 110, 12, size=8, color=GREY)
    lx += 135
    page.line(lx, mid, lx + 20, mid, NAVY, 2)
    page.ops[-1]['dash_style'] = 'DOT'
    page.rect(lx + 7, mid - 3, 6, 6, NAVY, 'ELLIPSE')
    page.rect(lx + 8.2, mid - 1.8, 3.6, 3.6, WHITE, 'ELLIPSE')
    page.text(ex['trend_legend'][2], lx + 25, ly, 120, 12, size=8, color=GREY)
    for name, start, end in ex['periods_band']:
        if name == 'Pandemic':
            page.rect(X(start - .5), fy, X(end + .5) - X(start - .5), fh, '#EEEBF5')
        page.text(name, X(start - .5), fy - 14, X(end + .5) - X(start - .5), 12, size=8, color=VIOLET if name == 'Pandemic' else GREY,
                  bold=True, align='center')
    for share in (0, .2, .4, .6):
        page.line(fx, Y(share), fx + fw, Y(share), HAIR, .5)
        page.text(f'{share * 100:.0f}%', L - 4, Y(share) - 6, 34, 12, size=8, color=GREY, align='right')
    for row in ex['trend']:
        page.text(str(row['year']), X(row['year']) - 18, fy + fh + 3, 36, 12, size=8, color=GREY, align='center')
    page.text(ex['drop_label'], X(2018.5), Y(.53), 130, 12, size=9, color=VIOLET, bold=True)
    page.marker(3, X(2018.5) + 124, Y(.53))
    page.marker(4, X(2021) + 10, Y(.34) - 20)
    # Funding-time strip, all years.
    q = ex['quartiles']
    sy, sw = fy + fh + 36, 380
    panel(page, L, sy, sw, 92, ex['strip_title'], 'Violet band: the middle half of loans; navy bar: the median.')
    px = wait_scale(L + 16, sw - 104)
    base = sy + 74
    page.line(L + 16, base, L + sw - 88, base, NAVY, .75)
    for days, name in [(0.1, '0.1'), (1, '1 day'), (10, '10'), (100, '100')]:
        page.text(name, px(days) - 20, base + 2, 40, 11, size=8, color=GREY, align='center')
    page.rect(px(q['q1']), base - 18, px(q['q3']) - px(q['q1']), 18, '#E2DCF0')
    page.rect(px(q['median']) - 1.5, base - 26, 3, 26, NAVY)
    page.text(f"Median {q['median']} days", px(q['median']) - 50, base - 40, 100, 12, size=8, bold=True, align='center')
    page.marker(1, px(q['median']) + 44, base - 40)
    page.text(f"A quarter wait\nover {q['q3']} days", L + sw - 84, base - 30, 82, 26, size=8, color=VIOLET, bold=True,
              spacing=100)
    page.marker(2, L + sw - 22, sy + 8)
    page.caption(slide['figure'], ex['caption'], sy + 100, w=R - 6 - L)
    page.takeaways(slide['takeaways'], pos)


INSIGHT_CARDS = [(L + i * 245, TOP, 233, 236) for i in range(3)]
INSIGHT_PHOTO = (L + 735, TOP, FULL - L - 735, 236)
PROBLEM_PHOTO = (L + 392, TOP + 20 + 168 + 36, R - 6 - L - 392, 92)
PRIORITISE_PHOTO = (L + 400, TOP + 178, 98, 124)
PRIORITISE_PHOTO2 = (L + 508.5, TOP + 178, 98, 124)


INSIGHT_ROWS = [(L, TOP + k * 106, 440, 100) for k in range(3)]
STEP_FILLS = {'navy': (NAVY, WHITE), 'violet': (VIOLET, WHITE), 'yellow': (YELLOW, NAVY)}


def insight_glyph(page, kind, x, y, w):
    """Tiny preview of the proof: the disbursal bar, lift by year, or framings against the ±5% band."""
    if kind == 'share':
        page.rect(x, y + 24, w * .964, 20, VIOLET)
        page.rect(x + w * .964, y + 24, w * .036, 20, HAIR)
        page.text('before listing', x, y + 48, 100, 12, size=8, color=GREY)
        page.text('3.6% after', x + w - 60, y + 48, 60, 12, size=8, color=GREY, align='right')
    elif kind == 'lift':
        lift = slide_by_id('triage')['exhibit']['lift']
        base, per, bar, step = y + 62, 13, 20, (w - 20) / 4
        page.line(x, base - per, x + w, base - per, RULE, .75)
        page.ops[-1]['dash_style'] = 'DASH'
        page.text('chance', x + w + 3, base - per - 6, 34, 11, size=8, color=GREY)
        page.text('by test year, 2021–2025', x, base + 2, w, 11, size=8, color=GREY)
        for k, (year, value) in enumerate(lift):
            bx = x + k * step
            page.rect(bx, base - value * per, bar, value * per, NAVY)
        page.line(x, base, x + w, base, NAVY, .75)
    else:
        rows = {r['term']: r for r in slide_by_id('equivalence')['exhibit']['rows']}
        lo, hi = -.15, .15
        px = lambda value: x + (value - lo) * w / (hi - lo)
        page.rect(px(-.05), y + 4, px(.05) - px(-.05), 60, TINT_BAND)
        page.line(px(0), y + 4, px(0), y + 64, NAVY, .75)
        for k, term in enumerate(['family', 'basic needs', 'business', 'agency', 'third person', 'urgency']):
            r, cy = rows[term], y + 10 + k * 9.6
            colour = VIOLET if term == 'urgency' else NAVY
            page.line(px(r['ci90_low']), cy, px(r['ci90_high']), cy, colour, 1.5)
            page.rect(px(r['estimate']) - 2.5, cy - 2.5, 5, 5, colour, 'ELLIPSE')


def insight(page, slide, urls, pos):
    """Three rows: finding and key figure, a tiny proof glyph, then an arrow to the solution step."""
    page.chrome(slide)
    for k, ((x, y, w, h), item) in enumerate(zip(INSIGHT_ROWS, slide['cards'])):
        page.rect(x, y, w, h, PAPER)
        page.rect(x, y, w, 2.5, [NAVY, SLATE, VIOLET][k])
        page.text(item['heading'], x + 36, y + 11, 200, 16, size=11, bold=True)
        page.text(item['figure'], x + 12, y + 34, 190, 36, size=28, bold=True)
        page.text(item['text'], x + 12, y + 72, 190, 24, size=9, color=GREY, spacing=105)
        insight_glyph(page, item['glyph'], x + 216, y + 16, 170)
        page.marker(k + 1, x + w - 22, y + 8)
        cx = x + w - 34
        for label in reversed(item['slides']):
            chip_link(page, label, cx, y + h - 22, [NAVY, SLATE, VIOLET][k], urls)
            cx -= 32
        if k == 2:
            page.marker(4, cx - 8, y + h - 24)
        step = item['step']
        fill, ink = STEP_FILLS[step['colour']]
        page.line(x + w + 4, y + h / 2, x + w + 30, y + h / 2, SLATE, .75)
        page.ops[-1]['end_arrow'] = 'FILL_ARROW'
        bx, bw = x + w + 34, R - 6 - (x + w + 34)
        page.rect(bx, y + 20, bw, 60, fill)
        page.text(step['sub'], bx, y + 26, bw, 12, size=8, color=ink, align='center')
        page.text(step['label'], bx, y + 40, bw, 22, size=12, color=ink, bold=True, align='center',
                  spans=[(0, len(step['label']), {'link': urls[step['slide']], 'color': ink})])
    page.takeaways(slide['takeaways'], pos)


def triage(page, slide, pos):
    """Concept card for the flag beside its lift and within-country precision against a simple lookup."""
    page.chrome(slide)
    ex = slide['exhibit']
    x, y, w, h = L, TOP, 222, 300
    card(page, x, y, w, h, VIOLET)
    tag_w = 6.2 * len(ex['tag']) + 20
    page.badge(ex['tag'], x + 14, y + 12, (tag_w, 18), YELLOW, NAVY, 8, 'ROUND_RECTANGLE')
    page.marker(4, x + w - 22, y + 14)
    page.text('Listing at posting time', x + 14, y + 40, w - 28, 12, size=8, color=GREY, bold=True)
    page.text(ex['listing'], x + 14, y + 53, w - 28, 14, size=10, bold=True)
    page.text(ex['listing_note'], x + 14, y + 68, w - 28, 12, size=8, color=GREY)
    page.text('Predicted risk of slow funding', x + 14, y + 90, w - 28, 12, size=8, color=GREY, bold=True)
    seg, gap = 17.4, 2
    for k in range(10):
        page.rect(x + 14 + k * (seg + gap), y + 104, seg, 11, VIOLET if k == 9 else '#E2DCF0')
    page.text('top 10%', x + w - 54, y + 116, 40, 12, size=8, color=VIOLET, bold=True, align='right')
    page.text(ex['flag'], x + 14, y + 130, w - 28, 15, size=11, color=VIOLET, bold=True)
    page.text(ex['same_day'], x + 14, y + 147, w - 28, 13, size=9, color=GREY)
    page.text(ex['support_title'], x + 14, y + 172, w - 28, 13, size=9, bold=True)
    for k, item in enumerate(ex['support']):
        page.text(item, x + 34, y + 192 + 25 * k, w - 46, 13, size=9)
    # Lookup against the flag
    px0, pw = x + w + 10, R - (x + w + 10)
    panel(page, px0, y, pw, h, ex['chart_title'], '')
    page.marker(1, px0 + pw - 22, y + 8)
    rows = ex['compare']
    left, step, bar = px0 + 18, (pw - 32) / 5, 26
    def bars(base, per, keys, fmt, chance):
        for k, row in enumerate(rows):
            for j, (key, fill) in enumerate(zip(keys, (SLATE, NAVY))):
                bx, value = left + k * step + j * (bar + 3), row[key]
                page.rect(bx, base - value * per, bar, value * per, fill)
                page.text(fmt(value), bx - 6, base - value * per - 12, bar + 12, 11, size=8, bold=j == 1, align='center',
                          color=NAVY if j else GREY)
        page.line(px0 + 10, base - chance * per, px0 + pw - 10, base - chance * per, SLATE, .75)
        page.ops[-1]['dash_style'] = 'DASH'
        page.line(px0 + 10, base, px0 + pw - 10, base, NAVY, .75)
    page.text(ex['lift_label'], px0 + 10, y + 27, pw - 20, 12, size=8, color=GREY, bold=True)
    bars(y + 144, 23, ('lookup_lift', 'tree_lift'), lambda v: f'{v:.2f}×', 1)
    page.text(ex['within_label'], px0 + 10, y + 158, pw - 40, 12, size=8, color=GREY, bold=True)
    page.marker(2, px0 + pw - 22, y + 157)
    bars(y + 272, 145, ('lookup_within', 'tree_within'), lambda v: f'{v:.2f}', .2)
    for k, row in enumerate(rows):
        page.text(row['year'], left + k * step - 4, y + 276, 2 * bar + 11, 12, size=8, color=GREY, align='center')
    page.legend([(ex['legend'][0], SLATE), (ex['legend'][1], NAVY, 'RECTANGLE', 3)], y + h + 6, px0, gap=16)
    page.caption(slide['figure'], ex['caption'], y + h + 24, w=R - L)
    page.takeaways(slide['takeaways'], pos)


LEVER_BOXES = [(L + (k % 2) * 195, TOP + (k // 2) * 156, 185, 146) for k in range(4)]


def prioritise(page, slide, pos):
    """Four lender-side levers to pilot, who acts and what to watch, and where not to spend effort."""
    page.chrome(slide)
    for k, ((x, y, w, h), lever) in enumerate(zip(LEVER_BOXES, slide['levers'])):
        card(page, x, y, w, h, NAVY)
        page.text(lever['name'], x + 36, y + 12, w - 50, 16, size=12, bold=True)
        page.text(lever['text'], x + 12, y + 38, w - 24, 44, size=10, color=GREY, spacing=105)
        for r, (label, value) in enumerate((('Who', lever['who']), ('Watch for', lever['watch']))):
            text = f'{label}: {value}'
            page.text(text, x + 12, y + 96 + r * 18, w - 24, 14, size=9, color=GREY, spans=[(0, len(label) + 1, {'bold': True, 'color': NAVY})])
    page.marker(1, L + 185 - 22, TOP + 12)
    page.marker(2, L + 185 - 22, TOP + 112)
    dx, dw, dh = L + 400, R - (L + 400), 168
    dont = slide['dont']
    card(page, dx, TOP, dw, dh, VIOLET)
    page.text(dont['heading'], dx + 12, TOP + 14, dw - 44, 34, size=12, color=VIOLET, bold=True, spacing=105)
    page.text(dont['text'], dx + 12, TOP + 44, dw - 24, 100, size=10, color=GREY, spacing=110)
    page.marker(4, dx + dw - 22, TOP + 14)
    sy = TOP + 312
    page.rect(L, sy, R - L, 24, PAPER)
    page.rect(L, sy, 4, 24, YELLOW)
    page.text(slide['note'], L + 14, sy, R - L - 50, 24, size=10, bold=True, middle=True, spans=[(0, len('Scope:'), {'bold': True})])
    page.marker(3, R - 22, sy + 6)
    page.takeaways(slide['takeaways'], pos)


def text_adds(page, slide, pos):
    """Linear gain per year split into context and loan-specific parts, with the larger-tree gain as a dot."""
    page.chrome(slide)
    ex = slide['exhibit']
    pw, h = R - L, 276
    panel(page, L, TOP, pw, h, ex['title'], ex['guide'])
    x0, x1, lo, hi = L + 52, R - 20, -.05, .42
    px = lambda value: x0 + (value - lo) / (hi - lo) * (x1 - x0)
    pitch, first, axis = 38, TOP + 48, TOP + 240
    page.line(px(0), TOP + 42, px(0), axis, NAVY, .75)
    page.line(x0, axis, x1, axis, SLATE, .75)
    for value, name in [(0, '0'), (.1, '0.1'), (.2, '0.2'), (.3, '0.3'), (.4, '0.4')]:
        page.line(px(value), axis, px(value), axis + 3, SLATE, .75)
        page.text(name, px(value) - 16, axis + 3, 32, 11, size=8, color=GREY, align='center')
    page.text('MAE gain, days', x0, axis + 14, x1 - x0, 12, size=8, color=GREY, align='center')
    context_fill = STAGE_FILLS[0]
    for k, row in enumerate(ex['rows']):
        y = first + k * pitch
        page.text(row['year'], L + 10, y, 36, 15, size=9, color=GREY, middle=True)
        split = px(row['context'])
        page.rect(px(0), y, split - px(0), 15, context_fill)
        page.text(f"{row['context']:.3f}", px(0), y, split - px(0), 15, size=8, bold=True, align='center', middle=True)
        end = px(row['context'] + row['loan_specific'])
        page.rect(split, y, end - split, 15, VIOLET)
        page.text(f"{row['loan_specific']:.3f}", split, y, end - split, 15, size=8, bold=True, color=WHITE,
                  align='center', middle=True)
        page.text(f"{row['context'] + row['loan_specific']:.2f}", end + 5, y, 34, 15, size=9, bold=True, middle=True)
        tree, dot = row['tree'], y + 23
        page.line(px(0), dot, px(tree), dot, SLATE, .75)
        page.rect(px(tree) - 3.5, dot - 3.5, 7, 7, NAVY, 'ELLIPSE')
        label = f'{tree:.3f}'.replace('-', '−')
        page.text(label, px(max(tree, 0)) + 7, dot - 6, 40, 12, size=8, bold=True, middle=True)
    page.marker(1, L + pw - 22, TOP + 8)
    # Legend under the figure
    ly, names = TOP + h + 6, ex['legend']
    page.legend([(names[0], context_fill, 'RECTANGLE', 2), (names[1], VIOLET), (names[2], NAVY, 'ELLIPSE', 3)],
                ly, L, span=pw, gap=24)
    # Text alone
    sy = ly + 18
    page.rect(L, sy, pw, 22, PAPER)
    page.rect(L, sy, 4, 22, YELLOW)
    page.text(ex['strip'], L + 14, sy, pw - 50, 22, size=10, bold=True, middle=True)
    page.marker(4, L + pw - 22, sy + 5)
    page.caption(slide['figure'], ex['caption'], sy + 28, w=pw)
    page.takeaways(slide['takeaways'], pos)


def roadmap(page, slide):
    """Now, next and later as three columns joined by thin arrows, then the stop rule."""
    page.chrome(slide)
    fills = {'navy': (NAVY, WHITE), 'violet': (VIOLET, WHITE), 'yellow': (YELLOW, NAVY)}
    width, top, h = 262, TOP + 6, 250
    for i, (column, x) in enumerate(zip(slide['columns'], GATE_X)):
        fill, ink = fills[column['colour']]
        page.rect(x, top, width, h, PAPER)
        page.badge(column['stage'], x, top, (width, 34), fill, ink, 13, 'RECTANGLE')
        for j, item in enumerate(column['items']):
            y = top + 50 + j * 64
            if j:
                page.line(x + 14, y - 8, x + width - 14, y - 8, HAIR, .75)
            page.badge(str(j + 1), x + 14, y + 2, (18, 18), fill, ink, 8)
            page.text(item, x + 42, y, width - 56, 52, size=11, spacing=115)
        if i < 2:
            page.line(x + width + 8, top + h / 2, x + width + 36, top + h / 2, SLATE, .75)
            page.ops[-1]['end_arrow'] = 'FILL_ARROW'
    page.text(slide['stop'], L, top + h + 18, FULL - L, 14, size=11, color=SLATE, bold=True)


def a_table(page, slide):
    page.chrome(slide)
    exhibit = slide['exhibit']
    row = 40 if len(exhibit['rows']) < 3 else 42
    table(page, exhibit['columns'], exhibit['rows'], L, TOP, FULL - L, row, exhibit.get('font', 10))
    y = TOP + row * (len(exhibit['rows']) + 1) + 8
    page.caption(exhibit['figure'], exhibit['caption'], y, w=FULL - L)
    if slide.get('note'):
        page.caption('¹', slide['note'], y + 14, w=FULL - L)
    for i, body in enumerate(slide.get('body', [])):
        page.block(body['heading'], body['text'], L + i * 450, y + 40, 425, 90)


def a_metrics(page, slide):
    page.chrome(slide)
    figures = slide['key_figures']
    width = 275
    for i, figure in enumerate(figures[:2]):
        key_card(page, figure, L + i * (width + 25), TOP, width, 104, NAVY)
    for i, figure in enumerate(figures[2:]):
        key_card(page, figure, L + i * (width + 25), 250, width, 104, VIOLET)
    page.caption('Scope:', slide['note'].removeprefix('Scope: '), 362, w=FULL - L)


def a_topics(page, slide):
    page.chrome(slide)
    for i, figure in enumerate(slide['key_figures']):
        key_card(page, figure, L + i * 449, TOP, 426, 104, [VIOLET, SLATE][i])
    for i, body in enumerate(slide['body']):
        page.block(body['heading'], body['text'], L + i * 449, 262, 426, 90)


def notes_text(slide):
    """Return notes text and styles in the Project 15 pattern."""
    notes = slide['notes']
    purpose = notes['purpose']
    parts, cursor = [purpose], len(purpose) + 1
    spans = [(0, len(purpose), {'bold': True, 'color': '#174EA6', 'background_color': '#E8F0FE', 'font_size': 14})]
    script = notes['script']
    pieces, rest = [], script
    while '[Point:' in rest:
        before, after = rest.split('[Point:', 1)
        label, rest = after.split(']', 1)
        pieces += [before.strip(), f'[Point:{label}]']
        rest = rest.strip()
    pieces.append(rest.strip())
    for piece in filter(None, pieces):
        style = ({'italic': True, 'color': '#5F6368', 'background_color': '#F1F3F4', 'font_size': 11}
                 if piece.startswith('[Point:') else {'color': '#202124', 'font_size': 14})
        spans.append((cursor, cursor + len(piece), style))
        parts.append(piece)
        cursor += len(piece) + 1
    if notes.get('reference'):
        heading = 'Reference — not read aloud'
        spans.append((cursor, cursor + len(heading), {'bold': True, 'color': '#5F6368', 'font_size': 11}))
        parts.append(heading)
        cursor += len(heading) + 1
        spans.append((cursor, cursor + len(notes['reference']), {'color': '#5F6368', 'font_size': 11}))
        parts.append(notes['reference'])
    return '\n'.join(parts), spans


def add_notes(page, slide, notes_id):
    text, spans = notes_text(slide)
    page.ops.append({'op': 'set-notes', 'slide': page.id, 'text': text})
    page.ops.append({'op': 'style-text', 'element': notes_id, 'start': 0, 'end': len(text), 'font_family': FONT})
    page.ops.append({'op': 'style-paragraph', 'element': notes_id, 'start': 0, 'end': len(text),
                     'line_spacing': 115, 'space_below': 8})
    for start, end, style in spans:
        page.ops.append({'op': 'style-text', 'element': notes_id, 'start': start, 'end': end, **style})


def framed_photo(work: Path, source_path: Path, frame: tuple, name: str, all_corners: bool = False) -> Path:
    """Crop a photograph to a frame and round its visible corners with a 24 pt radius."""
    scale = 2.5
    width, height, radius = int(frame[2] * scale), int(frame[3] * scale), int(24 * scale)
    source = Image.open(source_path).convert('RGB')
    ratio = width / height
    w, h = source.size
    crop = (int((w - h * ratio) / 2), 0, int((w + h * ratio) / 2), h) if w / h > ratio else \
           (0, int((h - w / ratio) / 2), w, int((h + w / ratio) / 2))
    image = source.crop(crop).resize((width, height), Image.LANCZOS).convert('RGBA')
    mask = Image.new('L', (width, height), 0)
    if all_corners:
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, height - 1), radius, fill=255)
    else:
        mask.paste(255, (0, 0, width, height))
        corner = Image.new('L', (radius * 2, radius * 2), 0)
        ImageDraw.Draw(corner).pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=255)
        mask.paste(corner.crop((0, 0, radius, radius)), (0, 0))
    image.putalpha(mask)
    target = work / name
    image.save(target)
    return target


def fix_markers(pres: str) -> None:
    """Rebuild every red 12 pt marker in place: empty ellipse plus a centred overlay number."""
    info = json.loads(run('readonly', 'info', pres, '--json'))
    for slide in info['slides']:
        page = Page(slide['objectId'])
        for element in slide.get('pageElements', []):
            shape = element.get('shape', {})
            fill = shape.get('shapeProperties', {}).get('shapeBackgroundFill', {}).get('solidFill', {})
            rgb = fill.get('color', {}).get('rgbColor', {})
            text = ''.join(t.get('textRun', {}).get('content', '') for t in shape.get('text', {}).get('textElements', []))
            if shape.get('shapeType') != 'ELLIPSE' or not text.strip().isdigit():
                continue
            if abs(rgb.get('red', 0) - 0.776) > .02 or abs(rgb.get('green', 0) - 0.251) > .02:
                continue
            t = element['transform']
            page.ops.append({'op': 'delete-element', 'element': element['objectId']})
            page.marker(int(text), t.get('translateX', 0) / EMU_PT, t.get('translateY', 0) / EMU_PT)
        if page.ops:
            submit(pres, page.ops)
            print(f"fixed {sum(o['op'] == 'delete-element' for o in page.ops)} markers on {slide['objectId']}")


EMU_PT = 12700


def ensure_footer(pres: str) -> None:
    """Add the work-specific footer text and a short yellow accent to the content layout once."""
    info = json.loads(run('readonly', 'info', pres, '--json'))
    layout = next(l for l in info['layouts'] if l['layoutProperties'].get('displayName') == 'Content')
    texts = [''.join(t.get('textRun', {}).get('content', '') for t in
                     e.get('shape', {}).get('text', {}).get('textElements', []))
             for e in layout.get('pageElements', [])]
    if any(FOOTER.split()[0] in t for t in texts):
        return
    page = Page(layout['objectId'])
    page.rect(0, 488.5, 43.5, 3.5, YELLOW)
    page.text(FOOTER, L, 498, 600, 12, size=8, color=GREY, spans=[(0, len('Cultural Blend'), {'bold': True, 'color': NAVY})])
    submit(pres, page.ops)


def prepare_slides(pres: str, reuse: bool, count: int, only: set | None = None) -> list[dict]:
    """Return slide objects in deck order, duplicating base slides as needed."""
    slides = json.loads(run('readonly', 'list-slides', pres, '--json'))
    if len(slides) == 2:
        first, content = slides[0]['objectId'], slides[1]['objectId']
        for _ in range(count - 3):
            run('mutate', 'duplicate', pres, content)
        run('mutate', 'duplicate', pres, first)  # lands at index 1
        slides = json.loads(run('readonly', 'list-slides', pres, '--json'))
        close_id = slides[1]['objectId']
        # Position is evaluated before removal, so index 15 needs 16.
        run('mutate', 'reorder-slide', pres, '--slide', close_id, '--position', '16')
        slides = json.loads(run('readonly', 'list-slides', pres, '--json'))
    if len(slides) != count:
        raise SystemExit(f'expected {count} slides, found {len(slides)}')
    if reuse:
        ops = [{'op': 'delete-element', 'element': element['objectId']}
               for index, slide in enumerate(slides) if only is None or index in only
               for element in slide.get('pageElements', [])
               if 'placeholder' not in element.get('shape', {})]
        if ops:
            submit(pres, ops)
    return slides


def submit(pres: str, ops: list[dict]) -> None:
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as handle:
        json.dump(ops, handle)
    try:
        run('mutate', 'batch', pres, '-f', handle.name)
    except subprocess.CalledProcessError as error:
        raise SystemExit(f'batch failed: {error.stderr}\n{error.stdout}') from error
    finally:
        os.unlink(handle.name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--base', help='blank 960 x 540 base presentation to copy into a NEW deck')
    target.add_argument('--reuse', help='working deck to clear and refill during QA, never an owner-edited deck')
    parser.add_argument('--only', help='with --reuse: comma-separated storyline slide numbers to refill (others untouched)')
    parser.add_argument('--fix-markers', action='store_true',
                        help='with --reuse: rebuild existing red markers in place as circle plus overlay number')
    args = parser.parse_args()
    if {args.base, args.reuse} & PROTECTED:
        raise SystemExit('refusing to touch the historical live deck')
    story = json.loads((DECK / 'storyline.json').read_text())['slides']
    layout_path = DECK / 'marker_layout.json'
    layout = json.loads(layout_path.read_text()) if layout_path.exists() else {}
    if args.base:
        pres = re.search(r'\(ID: ([\w-]+)\)', run('mutate', 'copy', args.base, TITLE)).group(1)
    else:
        pres = args.reuse
    keys = [str(slide['n']) for slide in story]
    only = {keys.index(k) for k in args.only.split(',')} if args.only else None
    if args.fix_markers:
        fix_markers(pres)
        return
    slides = prepare_slides(pres, bool(args.reuse), len(story), only)
    ensure_footer(pres)
    urls = {i + 1: f'https://docs.google.com/presentation/d/{pres}/edit#slide=id.{s["objectId"]}'
            for i, s in enumerate(slides)}
    # Link targets accept a storyline number as int or text, including appendix labels such as 'A2'.
    urls.update({str(slide['n']): urls[i + 1] for i, slide in enumerate(story)})
    builders = {'summary': summary, 'problem': problem, 'text_adds': text_adds, 'where': where, 'subgroups': subgroups,
                'lever': lever, 'outcome': outcome,
                'clustering': clustering, 'equivalence': forest, 'regions': regions, 'a_screen': regions,
                'persist': persist, 'forecast': forecast, 'gain_uncertainty': gains, 'approach': approach, 'solution': solution, 'triage': triage, 'prioritise': prioritise}
    linked = {'agenda': agenda}
    plain = {'gates': gates, 'supports': supports, 'roadmap': roadmap,
             'a_asof': a_table, 'a_text_methods': a_table, 'a_primary': a_metrics, 'a_topics': a_topics, 'cover': cover, 'close': close}
    for index, (slide, item) in enumerate(zip(story, slides)):
        if only is not None and index not in only:
            continue
        page = Page(item['objectId'])
        for element in item.get('pageElements', []):
            if 'placeholder' in element.get('shape', {}):
                page.ops.append({'op': 'update-shape', 'element': element['objectId'], 'content_alignment': 'TOP'})
        if slide['id'] in builders:
            builders[slide['id']](page, slide, marker_positions(slide, layout))
        elif slide['id'] == 'insight':
            insight(page, slide, urls, marker_positions(slide, layout))
        elif slide['id'] in linked:
            linked[slide['id']](page, slide, urls)
        else:
            plain[slide['id']](page, slide)
        if slide.get('solution_link'):
            page.text(slide['solution_link'], 684, 452, 235, 22, size=10, color=VIOLET, bold=True, spacing=105)
        notes_id = next(e['objectId'] for e in item['slideProperties']['notesPage']['pageElements']
                        if e.get('shape', {}).get('placeholder', {}).get('type') == 'BODY')
        add_notes(page, slide, notes_id)
        submit(pres, page.ops)
        print(f"slide {slide['n']}: {len(page.ops)} ops", flush=True)
    # Images last so they sit above the accent blocks.
    with tempfile.TemporaryDirectory() as work:
        at = {slide['id']: k for k, slide in enumerate(story)}
        images = [(at['cover'], framed_photo(Path(work), HARVEST, COVER_FRAME, 'cover.png'), COVER_FRAME),
                  (at['close'], framed_photo(Path(work), VENDOR, CLOSE_FRAME, 'close.png'), CLOSE_FRAME)]
        for sid, frame in [('problem', PROBLEM_PHOTO), ('prioritise', PRIORITISE_PHOTO)]:
            images.append((at[sid], framed_photo(Path(work), ASSETS / 'photos' / slide_by_id(sid)['photo'], frame,
                                                 f'{sid}.png', all_corners=True), frame))
        images.append((at['problem'], TREND_PNG, TREND_FRAME))
        images.append((at['prioritise'], framed_photo(Path(work), ASSETS / 'photos' / slide_by_id('prioritise')['photo2'],
                                                      PRIORITISE_PHOTO2, 'prioritise2.png', all_corners=True),
                       PRIORITISE_PHOTO2))
        images += [(at[sid], path, frame) for sid, path, frame in EXTRA_IMAGES]
        if 'lever' in at:
            images.append((at['lever'], framed_photo(Path(work), ASSETS / 'photos' / slide_by_id('lever')['photo'],
                                                     LEVER_PHOTO, 'lever.png', all_corners=True), LEVER_PHOTO))
            images.append((at['lever'], ASSETS / 'icons/table_rows-slate.png', (L + 154, TOP + 9.4, 18, 18)))
            images.append((at['lever'], ASSETS / 'icons/description-violet.png', (L + 154, TOP + 89.4, 18, 18)))
        if 'outcome' in at:
            for x, icon in zip(JOURNEY_X, slide_by_id('outcome')['exhibit']['icons']):
                images.append((at['outcome'], ASSETS / 'icons' / icon, (x - 15, 171, 30, 30)))
            images.append((at['outcome'], ASSETS / 'icons/check_circle-navy.png', (356 + 12, 284 + 31, 18, 18)))
            images.append((at['outcome'], ASSETS / 'icons/block-slate.png', (356 + 12, 284 + 74, 18, 18)))
        if 'where' in at:
            images.append((at['where'], MAP_PNG, map_frame(TOP)))
        images += [(at['cover'], framed_photo(Path(work), path, frame, f'small-{i}.png', all_corners=True), frame)
                   for i, (path, frame) in enumerate(COVER_SMALL)]
        # Logo: UNSW host mark on white, 330 x 140 px source at its own proportions.
        images.append((at['cover'], LOGO, (L, 446, 84.9, 36)))
        for i, step in enumerate(slide_by_id('approach')['exhibit']['steps']):
            images.append((at['approach'], ASSETS / 'icons' / step['icon'], (pipe_x(i) + 6, 166 + 5, 16, 16)))
        images.append((at['approach'], ASSETS / 'icons/table_rows-navy.png', (L + 11, TOP + 4, 16, 16)))
        for x, icon in zip(GATE_X, GATE_ICONS):
            images.append((at['gates'], ASSETS / 'icons' / icon, (x + 262 - 72, 136 + 18, 20, 20)))
        for i, icon in enumerate(SOLUTION_ICONS):
            images.append((at['solution'], ASSETS / 'icons' / icon, (L + i * (SOLUTION_W + SOLUTION_GAP) + SOLUTION_W - 32, TOP + 17, 20, 20)))
        for icon, x in zip(slide_by_id('agenda').get('icons', []), [43.5, 267.5, 491.5, 715.5]):
            images.append((at['agenda'], ASSETS / 'icons' / icon, (x + 178, 177, 20, 20)))
        for icon, (x, y, _, _) in zip(SUMMARY_ICONS, SUMMARY_CARDS):
            if icon:
                images.append((at['summary'], ASSETS / 'icons' / icon, (x + 16, y + 14, 22, 22)))
        for icon, x in zip(STEP_ICONS, STEP_X):
            images.append((at['summary'], ASSETS / 'icons' / icon, (x, BAND[1] + BAND[3] / 2 - 10, 20, 20)))
        for item, (x, y, _, _) in zip(slide_by_id('insight')['cards'], INSIGHT_ROWS):
            images.append((at['insight'], ASSETS / 'icons' / item['icon'], (x + 12, y + 10, 18, 18)))
        for item, (x, y, _, _) in zip(slide_by_id('prioritise')['levers'], LEVER_BOXES):
            images.append((at['prioritise'], ASSETS / 'icons' / item['icon'], (x + 12, y + 12, 18, 18)))
        for k in range(len(slide_by_id('triage')['exhibit']['support'])):
            images.append((at['triage'], ASSETS / 'icons/check_circle-navy.png', (L + 14, TOP + 190 + 25 * k, 15, 15)))
        for index, path, (x, y, w, h) in images:
            if only is not None and index not in only:
                continue
            run('mutate', 'insert-image-from-file', pres, '--slide', slides[index]['objectId'],
                '--file', str(path), '--x', str(x), '--y', str(y), '--width', str(w), '--height', str(h))
    print(f'https://docs.google.com/presentation/d/{pres}/edit')


if __name__ == '__main__':
    main()
