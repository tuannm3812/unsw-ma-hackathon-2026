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
    page.text('UNSW MARKETING ANALYTICS HACKATHON 2026', L, 166, 440, 14, size=10, color=VIOLET, bold=True)
    page.text(slide['title'], L, 186, 450, 56, size=44, bold=True)
    page.text(slide['subtitle'], L, 252, 430, 50, size=16, color=SLATE, spacing=115)
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


SUMMARY_ICONS = ['query_stats-violet.png', 'target-violet.png', 'trending_up-violet.png']
STEP_ICONS = ['fact_check-white.png', 'table_rows-white.png', 'science-white.png']
SUMMARY_CARDS = [(L + i * 298, TOP, 279, 244) for i in range(3)]
BAND = (L, 390, FULL - L - .5, 66)
STEP_X = [548, 670, 792]


def summary(page, slide, pos):
    """Three mini-exhibits, each with an icon, key figure and a native chart, then the decision."""
    page.chrome(slide)
    exhibits = [waffle_mini, bound_mini, gain_mini]
    for (x, y, w, h), body, draw, colour in zip(SUMMARY_CARDS, slide['body'], exhibits, [VIOLET, SLATE, NAVY]):
        card(page, x, y, w, h, colour)
        page.text(body['layer'].upper(), x + 46, y + 18, w - 62, 14, size=10, color=GREY, bold=True)
        page.text(body['figure'], x + 16, y + 42, w - 32, 40, size=32, bold=True)
        draw(page, x + 16, y + 94, w - 32, slide)
        page.block(body['heading'], body['text'], x + 16, y + 180, w - 32, 60)
    bx, by, bw, bh = BAND
    page.rect(bx, by, bw, bh, NAVY)
    page.rect(bx, by, 6, bh, YELLOW)
    label = 'Next decision:'
    page.text(slide['decision'], bx + 22, by, 470, bh, size=12, color=WHITE, middle=True, spacing=110,
              spans=[(0, len(label), {'bold': True})])
    for x, step in zip(STEP_X, slide['steps']):
        page.text(step, x + 26, by, 96, bh, size=10, color=WHITE, middle=True, spacing=110)


def waffle_mini(page, x, y, w, slide):
    """120 terms, the first 64 in yellow: significant under HC3, lost under country clustering."""
    cell, gap = 10, 2.3
    for i in range(120):
        row, col = divmod(i, 20)
        page.rect(x + col * (cell + gap), y + row * (cell + gap), cell, cell, YELLOW if i < 64 else HAIR)


def bound_mini(page, x, y, w, slide):
    """Five bounded framings and urgency against the ±0.05 band; values from the equivalence test."""
    rows = {r['term']: r for r in [s for s in slide_by_id('equivalence')['exhibit']['rows']]}
    lo, hi = -.15, .15
    px = lambda value: x + (value - lo) * w / (hi - lo)
    page.rect(px(-.05), y - 2, px(.05) - px(-.05), 76, TINT)
    page.line(px(0), y - 2, px(0), y + 74, NAVY, .75)
    for i, term in enumerate(['family', 'basic needs', 'business', 'agency', 'third person', 'urgency']):
        r, cy = rows[term], y + 6 + i * 12.5
        colour = VIOLET if term == 'urgency' else NAVY
        page.line(px(r['ci90_low']), cy, px(r['ci90_high']), cy, colour, 1.5)
        page.rect(px(r['estimate']) - 2.5, cy - 2.5, 5, 5, colour, 'ELLIPSE')
    page.text('urgency', px(.0295) + 4, y + 6 + 5 * 12.5 - 7, 60, 12, size=8, color=VIOLET, bold=True)


def gain_mini(page, x, y, w, slide):
    """Linear MAE gain by year, bars from zero with direct labels."""
    years = [row[:2] for row in slide_by_id('gain_uncertainty')['exhibit']['series'][0]['rows']]
    bar, step, base, per = 30, 54, y + 62, 120
    for i, (year, gain) in enumerate(years):
        bx = x + 2 + i * step
        page.rect(bx, base - gain * per, bar, gain * per, NAVY)
        page.text(f'{gain:.3f}', bx - 8, base - gain * per - 14, bar + 16, 12, size=8, color=NAVY, bold=True, align='center')
        page.text(str(year), bx - 8, base + 2, bar + 16, 12, size=8, color=GREY, align='center')
    page.line(x, base, x + w, base, NAVY, .75)


def slide_data():
    return {str(s['n']): s for s in json.loads((DECK / 'storyline.json').read_text())['slides']}


def slide_by_id(slide_id: str) -> dict:
    """Storyline slide by its stable id, so renumbering never breaks cross-slide lookups."""
    return next(s for s in slide_data().values() if s['id'] == slide_id)


def agenda(page, slide, urls):
    page.chrome(slide)
    colours = [(NAVY, WHITE), (VIOLET, WHITE), (SLATE, WHITE), (YELLOW, NAVY)]
    contents = [[('Editable fields', 4), ('The outcome', 5), ('A slower market', 6)],
                [('Four analyses', 7)],
                [('Country uncertainty', 8), ('Programme controls', 9), ('Small or unknown', 10),
                 ('Forecast gain', 11), ('Limits of the gain', 12)],
                [('What is supported', 13), ('Three gates', 14)]]
    for i, part in enumerate(slide['parts']):
        x = [43.5, 267.5, 491.5, 715.5][i]
        fill, ink = colours[i]
        page.badge(part['n'], x, TOP, (36, 36), fill, ink, 12)
        page.text(part['name'], x, 176, 200, 24, size=16, bold=True)
        page.text(part['question'], x, 204, 196, 36, size=12, color=GREY, spacing=110)
        page.line(x, 252, x + 200, 252, RULE, .75)
        for j, (label, number) in enumerate(contents[i]):
            y = 262 + j * 28
            page.text(label, x, y + 1, 168, 16, size=10)
            chip = page.badge(str(number), x + 176, y, (24, 18), fill, ink, 8, 'ROUND_RECTANGLE')
            page.ops.append({'op': 'style-text', 'element': chip, 'start': 0, 'end': len(str(number)),
                             'link': urls[number], 'color': ink, 'underline': False})


# Slide 4 photo frame inside the 316 pt card (x, y, width, height); icons sit beside the two headings.
LEVER_PHOTO = (L + 16, TOP + 14, 170, 288)
HIGHLIGHT = {'family': '#FFF0A8', 'business': '#E2DCF0', 'urgency': '#D5DCE5'}


def lever(page, slide, pos):
    """An illustrative listing card: fixed fields above, the editable description highlighted by framing."""
    page.chrome(slide)
    ex = slide['exhibit']
    x, y, w, h = L, TOP, R - 16 - L, 316
    page.rect(x, y, w, h, PAPER)
    page.rect(x, y, w, 2.5, YELLOW)
    page.caption('Figure 1.', ex['caption'], y + h + 8, w=w)
    y -= 16  # card content starts higher now that the label sits in the caption
    rx, rw = x + 202, w - 218
    page.text('FIXED AT LISTING', rx + 26, y + 32, 240, 14, size=10, color=SLATE, bold=True)
    cw = rw / 3
    for i, (label, value) in enumerate(ex['fixed_fields']):
        cx, cy = rx + (i % 3) * cw, y + 54 + (i // 3) * 36
        page.text(label, cx, cy, cw - 8, 12, size=8, color=GREY)
        page.text(value, cx, cy + 12, cw - 8, 14, size=10, bold=True)
    page.line(rx, y + 132, rx + rw, y + 132, HAIR, .75)
    page.text('EDITABLE DESCRIPTION', rx + 26, y + 142, 240, 14, size=10, color=VIOLET, bold=True)
    page.rect(rx, y + 164, rw, 100, WHITE)
    page.rect(rx, y + 164, 4, 100, YELLOW)
    text = ex['description']
    spans = []
    for kind, words in ex['highlights'].items():
        for word in words:
            for m in re.finditer(r'\b' + re.escape(word) + r'\b', text):
                if kind in HIGHLIGHT:
                    spans.append((m.start(), m.end(), {'background_color': HIGHLIGHT[kind]}))
                elif kind == 'gratitude':
                    spans.append((m.start(), m.end(), {'underline': True, 'color': VIOLET, 'bold': True}))
    page.text(text, rx + 16, y + 174, rw - 28, 92, size=12, color=NAVY, spacing=135, spans=spans)
    page.text('Highlights mark framing terms counted per 100 words', rx, y + 276, rw, 12, size=8, color=GREY, bold=True)
    chips = [('Family', 'family'), ('Business', 'business'), ('Urgency', 'urgency'), ('Gratitude', 'gratitude')]
    cx = rx
    for label, kind in chips:
        width = 8 + len(label) * 5.6
        if kind in HIGHLIGHT:
            page.rect(cx, y + 294, width, 18, HIGHLIGHT[kind])
            page.text(label, cx, y + 294, width, 18, size=10, align='center', middle=True)
        else:
            style = {'underline': True, 'color': VIOLET, 'bold': True} if kind == 'gratitude' else {'bold': True}
            page.text(label, cx, y + 294, width, 18, size=10, align='center', middle=True,
                      spans=[(0, len(label), style)])
        cx += width + 8
    page.marker(3, rx + rw - 14, y + 33)
    page.marker(1, rx + rw - 14, y + 143)
    page.marker(4, rx + rw - 14, y + 170)
    page.marker(2, rx + rw - 14, y + 277)
    page.takeaways(slide['takeaways'], pos)


JOURNEY_X = [112, 256, 400, 544]  # icon centres for the four journey steps on slide 5
JOURNEY_ICONS = ['payments-violet.png', 'storefront-navy.png', 'groups-navy.png', 'account_balance-violet.png']


def outcome(page, slide, pos):
    """A pre-disbursed loan's journey with what we measure bracketed, then who is in the data."""
    page.chrome(slide)
    ex = slide['exhibit']
    xs, line_y = JOURNEY_X, 186
    for i, (label, note) in enumerate(ex['steps']):
        if i < 3:
            page.line(xs[i] + 18, line_y, xs[i + 1] - 18, line_y, HAIR if i != 1 else NAVY, 2 if i == 1 else 1.25)
        page.sup(label, xs[i] - 64, 208, 128, 16, size=10, bold=True, align='center')
    for (a, b), fill, text, mark in [((0, 1), SLATE, ex['before'], 3), ((1, 2), YELLOW, ex['measure'], 1)]:
        page.rect(xs[a], 158, xs[b] - xs[a], 3, fill)
        page.rect(xs[a], 158, 2, 10, fill)
        page.rect(xs[b] - 2, 158, 2, 10, fill)
        page.sup(text, xs[a] - 6, 128, xs[b] - xs[a] + 12, 28, size=10, bold=True, align='center')
    page.marker(1, xs[0] - 18, 157)
    page.marker(3, xs[2] + 6, 157)
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
    page.marker(2, sx + sw - 16, top + 77)
    page.caption('Figure 2.', ex['caption'], 400)
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


def approach(page, slide, urls):
    """Four analyses fed by one dataset, each previewing its result, then the years each one uses."""
    page.chrome(slide)
    ex = slide['exhibit']
    page.rect(L, TOP, FULL - L - .5, 28, PAPER)
    page.rect(L, TOP, 6, 28, YELLOW)
    page.text(ex['source'], L + 40, TOP, 760, 28, size=12, bold=True, middle=True)
    width, top, h = PIPE_W, 172, 174
    fills = [(NAVY, WHITE), (VIOLET, WHITE), (YELLOW, NAVY), (SLATE, WHITE)]
    previews = [preview_waffle, preview_table, preview_bound, preview_bars]
    for i, step in enumerate(ex['steps']):
        x = pipe_x(i)
        fill, ink = fills[i]
        page.line(x + width / 2, TOP + 28, x + width / 2, top - 1, SLATE, .75)
        page.ops[-1]['end_arrow'] = 'FILL_ARROW'
        page.rect(x, top, width, h, PAPER)
        page.rect(x, top, width, 30, fill)
        page.text(step['name'], x + 34, top, width - 76, 30, size=11, color=ink, bold=True, middle=True)
        chip = page.rect(x + width - 38, top + 7, 30, 16, WHITE, 'ROUND_RECTANGLE')
        label = f"→ {step['slide']}"
        page.text(label, x + width - 38, top + 7, 30, 16, size=8, bold=True, align='center', middle=True,
                  spans=[(0, len(label), {'link': urls[step['slide']], 'color': NAVY})])
        page.text(step['question'], x + 10, top + 36, width - 20, 28, size=10, bold=True, spacing=105)
        page.text(step['method'], x + 10, top + 66, width - 20, 22, size=8, color=GREY, spacing=105)
        previews[i](page, x + 10, top + 90, width - 20, 46, slide)
        page.text(step['headline'], x + 10, top + 142, width - 20, 28, size=10, bold=True, spacing=105)
        if i < 2:
            page.line(x + width + 2, top + 15, x + width + 20, top + 15, SLATE, .75)
            page.ops[-1]['end_arrow'] = 'FILL_ARROW'
    page.line(pipe_x(3) - 20, top, pipe_x(3) - 20, top + h, RULE, .75)
    timeline(page, ex['timeline'])
    claims(page, ex['claims'])


def claims(page, chips):
    """What each analysis can claim, ending with the causal caveat."""
    y = 454
    page.text('What each can claim', L, y, 150, 14, size=8, bold=True, middle=True)
    fills = [NAVY, VIOLET, YELLOW, SLATE]
    x = 236
    for (name, claim), fill in zip(chips, fills):
        label = f'{name}: {claim}'
        width = 12 + len(label) * 4.25
        page.rect(x, y, width, 14, PAPER)
        page.rect(x, y, 3, 14, fill)
        page.text(label, x + 6, y, width - 6, 14, size=8, middle=True, spans=[(0, len(name) + 1, {'bold': True})])
        x += width + 6
    page.text('None of these is a causal claim.', x + 4, y, FULL - x - 4, 14, size=8, color=SLATE, bold=True, middle=True)


def preview_waffle(page, x, y, w, h, slide):
    """Mini of the 120-term waffle: 64 terms lost significance."""
    cell, gap = 5.6, 1.5
    for i in range(120):
        row, col = divmod(i, 20)
        page.rect(x + col * (cell + gap), y + 2 + row * (cell + gap), cell, cell, YELLOW if i < 64 else HAIR)


def preview_table(page, x, y, w, h, slide):
    """Mini of the robustness table: a header row and two term rows."""
    for r in range(3):
        page.rect(x, y + 2 + r * 14, w * .8, 12, NAVY if r == 0 else WHITE)
        if r:
            page.line(x, y + 2 + r * 14 + 12, x + w * .8, y + 2 + r * 14 + 12, HAIR, .5)
    for c in (1, 2):
        page.line(x + w * .8 * c / 3, y + 14, x + w * .8 * c / 3, y + 44, HAIR, .5)


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
    gains = [row[1] for row in slide_by_id('gain_uncertainty')['exhibit']['series'][0]['rows']]
    for i, gain in enumerate(gains):
        height = gain * 110
        page.rect(x + i * 26, y + 46 - height, 18, height, NAVY)
    page.line(x, y + 46, x + 126, y + 46, NAVY, .75)


def timeline(page, tl):
    """Years each analysis uses: all loans, the holdout split, five expanding windows; notes at right."""
    x0, per, top = 236, 41.3, 356
    note_x = x0 + 10 * per + 14
    page.text(tl['title'], L, top, 190, 12, size=10, bold=True)
    for i, year in enumerate(range(2016, 2026)):
        page.text(str(year), x0 + i * per - 6, top, per + 12, 12, size=8, color=GREY, align='center')
    page.rect(note_x, top + 2, 8, 8, SLATE)
    page.text('train', note_x + 11, top, 30, 12, size=8, color=GREY)
    page.rect(note_x + 44, top + 2, 8, 8, YELLOW)
    page.text('test', note_x + 55, top, 30, 12, size=8, color=GREY)
    def span(first, last, y, h, fill):
        page.rect(x0 + (first - 2016) * per + 1, y, (last - first + 1) * per - 2, h, fill)
    rows = tl['rows']
    y = top + 16
    page.text(rows[0]['label'], L, y, 190, 13, size=8, bold=True, middle=True)
    span(2016, 2025, y, 13, NAVY)
    page.text('all 1,453,840 loans', x0 + 6, y, 200, 13, size=8, color=WHITE, bold=True, middle=True)
    page.text(rows[0]['note'], note_x, y, FULL - note_x, 13, size=8, color=GREY, middle=True)
    y += 17
    page.text(rows[1]['label'], L, y, 190, 13, size=8, bold=True, middle=True)
    span(2016, 2023, y, 13, SLATE)
    span(2024, 2025, y, 13, YELLOW)
    page.text('train: 1,174,953 loans', x0 + 6, y, 220, 13, size=8, color=WHITE, bold=True, middle=True)
    page.text('test: 278,887', x0 + 8 * per + 4, y, 2 * per - 6, 13, size=8, bold=True, middle=True)
    page.text(rows[1]['note'], note_x, y, FULL - note_x, 13, size=8, color=GREY, middle=True)
    y += 17
    page.text(rows[2]['label'], L, y + 6, 190, 30, size=8, bold=True, spacing=105)
    page.text(rows[2]['note'], note_x, y + 6, FULL - note_x, 30, size=8, color=GREY, spacing=105)
    for test in range(2021, 2026):
        span(2016, test - 1, y, 6.5, SLATE)
        span(test, test, y, 6.5, YELLOW)
        y += 8.5


PIPE_W = 196


def pipe_x(i):
    """Card x: three chained cards 22 pt apart, then the separate benchmark after a 40 pt gap."""
    return L + i * (PIPE_W + 22) + (18 if i == 3 else 0)


# Slide 8 panel (c): map frame matches scripts/build_country_map.py's 270:86 crop, and the table's
# share cells reuse that script's bins so one legend explains both.
MAP_PANEL = (L, TOP + 166, R - 16 - L, 148)
MAP_FRAME = (L + 10, TOP + 166 + 42, 250, 250 * 86 / 270)
MAP_PNG = ASSETS / 'maps/country_share_map.png'
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
    page.text(guide, x + 10, y + 23, w - 20, 22, size=8, color=GREY, spacing=105)


def clustering(page, slide, pos):
    """Three blocks: (a) which terms lost significance, (b) urgency before and after, (c) where loans are."""
    page.chrome(slide)
    ex = slide['exhibit']
    ax, ay, aw, ah = L, TOP, 290, 158
    panel(page, ax, ay, aw, ah, ex['panels'][0]['title'], ex['panels'][0]['guide'])
    cell, gap = 8.4, 2.1
    for g, group in enumerate(ex['groups']):
        x0 = ax + 10 + g * 104
        page.text(f"{group['name']}: {group['lost']} of {group['significant']}", x0, ay + 46, 100, 12,
                  size=8, bold=True)
        for i in range(group['significant']):
            row, col = divmod(i, 8)
            page.rect(x0 + col * (cell + gap), ay + 62 + row * (cell + gap), cell, cell,
                      YELLOW if i < group['lost'] else NAVY)
    lx = ax + 220
    page.rect(lx, ay + 64, 8, 8, YELLOW)
    page.text('lost', lx + 12, ay + 62, 50, 12, size=8, color=GREY)
    page.rect(lx, ay + 80, 8, 8, NAVY)
    page.text('kept', lx + 12, ay + 78, 50, 12, size=8, color=GREY)
    # (b)
    bx, by, bw, bh = L + 300, TOP, R - 16 - L - 300, 158
    panel(page, bx, by, bw, bh, ex['panels'][1]['title'], ex['panels'][1]['guide'])
    x0, x1 = bx + 20, bx + bw - 20
    px = lambda p_value: x0 + (math.log10(p_value) + 4) / 4 * (x1 - x0)  # 0.0001 .. 1
    page.line(px(.05), by + 54, px(.05), by + 126, VIOLET, .75)
    page.ops[-1]['dash_style'] = 'DASH'
    page.text('0.05', px(.05) - 14, by + 128, 28, 12, size=8, color=VIOLET, bold=True, align='center')
    for value, name in [(0.001, '0.001'), (0.01, '0.01'), (1, '1')]:
        page.text(name, px(value) - 16, by + 128, 32, 12, size=8, color=GREY, align='center')
    for r, row in enumerate(ex['urgency']):
        y = by + 72 + r * 32
        page.text(row['model'], bx + 10, y - 16, 200, 12, size=8, bold=True)
        page.line(px(.0004) + 4, y, px(row['clustered']) - 5, y, SLATE, .75)
        page.ops[-1]['end_arrow'] = 'FILL_ARROW'
        page.rect(px(.0004) - 4, y - 4, 8, 8, NAVY, 'ELLIPSE')
        page.rect(px(row['clustered']) - 4, y - 4, 8, 8, VIOLET, 'ELLIPSE')
        page.sup('<0.001¹', px(.0004) - 24, y + 4, 48, 12, size=8, align='center')
        page.text(f"{row['clustered']:.2f}", px(row['clustered']) - 20, y + 4, 40, 12, size=8, bold=True,
                  color=VIOLET, align='center')
    page.rect(bx + 10, by + 144, 8, 8, NAVY, 'ELLIPSE')
    page.text('HC3', bx + 22, by + 142, 40, 12, size=8, color=GREY)
    page.rect(bx + 54, by + 144, 8, 8, VIOLET, 'ELLIPSE')
    page.text('country-clustered', bx + 66, by + 142, 120, 12, size=8, color=GREY)
    # (c) map on the left, top-10 table on the right
    cx, cy, cw, ch = MAP_PANEL
    panel(page, cx, cy, cw, ch, ex['panels'][2]['title'], ex['panels'][2]['guide'])
    # Map (image inserted later at MAP_FRAME) with a compact vertical legend to its right.
    mx, my, mw, mh = MAP_FRAME
    lx = mx + mw + 10
    page.text('Loan share', lx, my, 56, 12, size=8, color=GREY, bold=True)
    legend = [(colour, label) for (_, colour), label in zip(COUNTRY_MAP.BINS, COUNTRY_MAP.BIN_LABELS)]
    for i, (fill, label) in enumerate(legend + [(NO_LOANS, 'no loans'), (None, 'top 10')]):
        y = my + 12 * (i + 1)
        if fill is None:  # navy outline swatch, as drawn on the map
            page.rect(lx, y + 0.5, 8, 8, NAVY)
            page.rect(lx + 1.2, y + 1.7, 5.6, 5.6, PAPER)
        else:
            page.rect(lx, y + 0.5, 8, 8, fill)  # centred on the label's cap height
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
    page.marker(1, ax + aw - 22, ay + 8)
    page.marker(2, ax + 210, ay + 46)
    page.marker(3, bx + bw - 22, by + 8)
    page.marker(4, cx + cw - 22, cy + 8)
    page.caption('Figure 4.', ex['caption'], cy + ch + 8, w=cw)
    page.caption('¹', ex['note'], cy + ch + 22, w=cw)
    page.takeaways(slide['takeaways'], pos)


STATUS_COLOURS = {'bounded': NAVY, 'mixed': SLATE, 'unresolved': VIOLET}


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
        rows = [row for row in ex['rows'] if row['status_both_specs'] == group['status']]
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
            page.text(name, L, ry + 1, 96, 14, size=9)
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
    # Legend under the plot, aligned with its left edge; the bands are labelled by the axis itself.
    ly, lx = ay + 15, px(-.10)  # the plot's visible left edge: the −10% band edge and tick
    page.line(lx, ly + 5.1, lx + 20, ly + 5.1, NAVY, 2)
    page.rect(lx + 6.5, ly + 1.6, 7, 7, NAVY, "ELLIPSE")
    page.text('Estimate, 90% range', lx + 24, ly, 90, 12, size=8, color=GREY)
    page.marker(2, px(.05) + 4, TOP + 2.5)
    page.marker(1, *header['bounded'])
    page.marker(3, *header['unresolved'])
    page.marker(4, rx + 3.3 * len(ex['t4_tag']) + 8, header['bounded'][1] + 0.5)
    page.caption('Figure 6.', ex['caption'], ly + 16)
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
    page.chrome(slide)
    exhibit = slide['exhibit']
    table(page, exhibit['columns'], exhibit['rows'], L, TOP, R - L - 6, 40)
    page.caption('Figure 5.', exhibit['note'], TOP + 120 + 8)
    first, second = slide['key_figures']
    key_card(page, first, L, 286, 296, 110, VIOLET, 24)
    key_card(page, second, 353.5, 286, 296.5, 110, NAVY, 24)
    page.marker(1, L + 296 - 22, 296)
    page.marker(3, L + 296 - 40, 296)
    page.marker(2, 353.5 + 296.5 - 22, 296)
    page.takeaways(slide['takeaways'], pos)


def forecast(page, slide, pos):
    page.chrome(slide)
    exhibit = slide['exhibit']
    base, per, x0, group, bar = 424, 26, L + 4, 90, 36
    legend_y = TOP + 2
    page.rect(L, legend_y + 2, 11, 11, SLATE)
    page.text(exhibit['series'][0], L + 17, legend_y, 110, 14, size=10)
    page.rect(160, legend_y + 2, 11, 11, NAVY)
    page.text(exhibit['series'][1], 177, legend_y, 120, 14, size=10)
    for i, row in enumerate(exhibit['data']):
        x = x0 + i * group
        for j, (value, fill) in enumerate(zip(row['values'], [SLATE, NAVY])):
            h = value * per
            bx = x + j * (bar + 2)
            page.rect(bx, base - h, bar, h, fill)
            page.text(f'{value:.3f}', bx - 5, base - h - 17 - j * 0, bar + 10, 14, size=10, color=GREY if j == 0 else NAVY,
                      bold=j == 1, align='center')
        page.text(str(row['year']), x, base + 4, bar * 2 + 2, 14, size=10, align='center')
    page.line(L, base, L + 5 * group - 8, base, NAVY, 1)
    figure = slide['key_figures'][0]
    key_card(page, figure, 498, TOP, 152, 104, YELLOW, 24)
    key_card(page, {'value': '5 of 5', 'label': 'years with lower error'}, 498, 246, 152, 92, VIOLET, 24)
    key_card(page, {'value': '728,640', 'label': 'evaluation records'}, 498, 350, 152, 92, SLATE, 24)
    page.marker(1, 498 + 152 - 22, TOP + 10)
    page.marker(2, 290, legend_y + 1)
    page.marker(3, 452, 215)
    page.caption('Figure 7.', 'Linear-model MAE in days on identical evaluation rows; lower is better.', 450)
    page.takeaways(slide['takeaways'], pos)


def gains(page, slide, pos):
    page.chrome(slide)
    panels = slide['exhibit']['series']
    lo, hi, width, top, pitch = -.1, .55, 244, 168, 49
    for p, panel in enumerate(panels):
        px0 = L + p * 310
        plot = px0 + 40
        px = lambda value: plot + (value - lo) * width / (hi - lo)
        colour = [NAVY, VIOLET][p]
        page.sup(panel['name'] + '¹', px0, TOP + 2, 290, 16, size=10, bold=True, color=colour)
        page.line(px(0), top - 12, px(0), top + 5 * pitch - 12, GREY, .75)
        for i, (year, gain, low, high) in enumerate(panel['rows']):
            y = top + i * pitch
            page.text(str(year), px0, y + 6, 36, 14, size=10)
            text = f'{gain:.3f} [{low:.3f}, {high:.3f}]'.replace('-', '−')
            page.text(text, px(0) + 5, y - 9, width - 40, 14, size=10, color=GREY)
            page.line(px(low), y + 14, px(high), y + 14, colour, 2)
            page.rect(px(gain) - 3.5, y + 10.5, 7, 7, colour, 'ELLIPSE')
        for value, name in [(0, '0'), (.25, '0.25'), (.5, '0.50')]:
            page.text(name, px(value) - 20, top + 5 * pitch - 10, 40, 12, size=8, color=GREY, align='center')
    page.marker(1, L + 310 + 270, TOP + 3)
    page.marker(3, L + 31, top + 4 * pitch + 7)
    axis = top + 5 * pitch - 10 + 12
    page.caption('Figure 8.', 'Annual MAE gain in days with month-resampled 95% intervals; positive is better.', axis + 8)
    page.marker(2, L, axis + 22)
    page.caption('¹', 'Country resampling, not shown: intervals include zero in 4 of 5 linear and 3 of 5 tree years.',
                 axis + 22, x=L + 18)
    page.takeaways(slide['takeaways'], pos)


def supports(page, slide):
    page.chrome(slide)
    width = 426
    for i, column in enumerate(slide['columns']):
        x = L + i * (width + 22.5)
        fill = [NAVY, VIOLET][i]
        page.rect(x, TOP, width, 320, PAPER)
        page.badge(column['heading'], x, TOP, (width, 36), fill, WHITE, 12, 'RECTANGLE')
        pitch = 280 / len(column['items'])
        for j, item in enumerate(column['items']):
            y = TOP + 36 + j * pitch
            if j:
                page.line(x + 14, y, x + width - 14, y, HAIR, .75)
            page.text(item, x + 14, y, width - 28, pitch, size=12, middle=True)


GATE_X = [L + i * 306 for i in range(3)]
GATE_ICONS = ['fact_check-navy.png', 'table_rows-navy.png', 'science-navy.png']


def gates(page, slide, urls):
    """Three gates as full cards, then the claim each gate would unlock and the stop rule."""
    page.chrome(slide)
    width, top, h = 262, 136, 226
    fills = [(NAVY, WHITE), (VIOLET, WHITE), (YELLOW, NAVY)]
    for i, (step, x) in enumerate(zip(slide['steps'], GATE_X)):
        card(page, x, top, width, h, fills[i][0])
        page.badge(step['n'], x + 14, top + 14, (30, 30), *fills[i], 11)
        label = f"→ {step['slide']}"
        page.rect(x + width - 44, top + 20, 30, 16, WHITE, 'ROUND_RECTANGLE')
        page.text(label, x + width - 44, top + 20, 30, 16, size=8, bold=True, align='center', middle=True,
                  spans=[(0, len(label), {'link': urls[step['slide']], 'color': NAVY})])
        page.text(step['name'], x + 14, top + 52, width - 28, 16, size=12, bold=True)
        for j, (key, size, colour, bold) in enumerate([('question', 10, NAVY, True), ('do', 10, GREY, False),
                                                       ('done', 10, GREY, False)]):
            y = top + 76 + j * 50
            page.text({'question': 'Question', 'do': 'Do', 'done': 'Done when'}[key], x + 14, y, 120, 12,
                      size=8, color=GREY, bold=True)
            page.text(step[key], x + 14, y + 12, width - 28, 36, size=size, color=colour, bold=bold, spacing=105)
        if i < 2:
            page.line(x + width + 8, top + h / 2, x + width + 36, top + h / 2, SLATE, .75)
            page.ops[-1]['end_arrow'] = 'FILL_ARROW'
    ladder = slide['ladder']
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


def a_table(page, slide):
    page.chrome(slide)
    exhibit = slide['exhibit']
    row = 40 if len(exhibit['rows']) < 3 else 42
    table(page, exhibit['columns'], exhibit['rows'], L, TOP, FULL - L, row)
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
    builders = {'summary': summary, 'lever': lever, 'outcome': outcome, 'slowdown': slowdown,
                'clustering': clustering, 'equivalence': forest, 'regions': regions, 'a_screen': regions, 'persist': persist,
                'forecast': forecast, 'gain_uncertainty': gains}
    plain = {'approach': approach, 'supports': supports, 'gates': gates,
             'a_asof': a_table, 'a_primary': a_metrics, 'a_topics': a_topics, 'cover': cover, 'close': close}
    for index, (slide, item) in enumerate(zip(story, slides)):
        if only is not None and index not in only:
            continue
        page = Page(item['objectId'])
        for element in item.get('pageElements', []):
            if 'placeholder' in element.get('shape', {}):
                page.ops.append({'op': 'update-shape', 'element': element['objectId'], 'content_alignment': 'TOP'})
        if slide['id'] in builders:
            builders[slide['id']](page, slide, marker_positions(slide, layout))
        elif slide['id'] == 'agenda':
            agenda(page, slide, urls)
        elif slide['id'] == 'approach':
            approach(page, slide, urls)
        elif slide['id'] == 'gates':
            gates(page, slide, urls)
        else:
            plain[slide['id']](page, slide)
        notes_id = next(e['objectId'] for e in item['slideProperties']['notesPage']['pageElements']
                        if e.get('shape', {}).get('placeholder', {}).get('type') == 'BODY')
        add_notes(page, slide, notes_id)
        submit(pres, page.ops)
        print(f"slide {slide['n']}: {len(page.ops)} ops", flush=True)
    # Images last so they sit above the accent blocks.
    with tempfile.TemporaryDirectory() as work:
        images = [(0, framed_photo(Path(work), PHOTO, COVER_FRAME, 'cover.png'), COVER_FRAME),
                  (14, framed_photo(Path(work), MARKET, CLOSE_FRAME, 'close.png'), CLOSE_FRAME)]
        images += [(0, framed_photo(Path(work), path, frame, f'small-{i}.png', all_corners=True), frame)
                   for i, (path, frame) in enumerate(COVER_SMALL)]
        # Logo: UNSW host mark on white, 330 x 140 px source at its own proportions.
        images.append((0, LOGO, (L, 446, 84.9, 36)))
        images.append((3, framed_photo(Path(work), MARKET, LEVER_PHOTO, 'lever.png', all_corners=True), LEVER_PHOTO))
        images.append((3, ASSETS / 'icons/table_rows-slate.png', (L + 202, TOP + 14, 18, 18)))
        images.append((3, ASSETS / 'icons/description-violet.png', (L + 202, TOP + 124, 18, 18)))
        for i, step in enumerate(slide_by_id('approach')['exhibit']['steps']):
            x = pipe_x(i)
            images.append((6, ASSETS / 'icons' / step['icon'], (x + 8, 172 + 5, 20, 20)))
        images.append((6, ASSETS / 'icons/table_rows-navy.png', (L + 14, TOP + 5, 18, 18)))
        images.append((7, MAP_PNG, MAP_FRAME))
        for x, icon in zip(JOURNEY_X, JOURNEY_ICONS):
            images.append((4, ASSETS / 'icons' / icon, (x - 15, 171, 30, 30)))
        images.append((4, ASSETS / 'icons/check_circle-navy.png', (356 + 12, 284 + 31, 18, 18)))
        images.append((4, ASSETS / 'icons/block-slate.png', (356 + 12, 284 + 74, 18, 18)))
        for x, icon in zip(GATE_X, GATE_ICONS):
            images.append((13, ASSETS / 'icons' / icon, (x + 262 - 72, 136 + 18, 20, 20)))
        for icon, (x, y, _, _) in zip(SUMMARY_ICONS, SUMMARY_CARDS):
            images.append((1, ASSETS / 'icons' / icon, (x + 16, y + 14, 22, 22)))
        for icon, x in zip(STEP_ICONS, STEP_X):
            images.append((1, ASSETS / 'icons' / icon, (x, BAND[1] + BAND[3] / 2 - 10, 20, 20)))
        for index, path, (x, y, w, h) in images:
            if only is not None and index not in only:
                continue
            run('mutate', 'insert-image-from-file', pres, '--slide', slides[index]['objectId'],
                '--file', str(path), '--x', str(x), '--y', str(y), '--width', str(w), '--height', str(h))
    print(f'https://docs.google.com/presentation/d/{pres}/edit')


if __name__ == '__main__':
    main()
