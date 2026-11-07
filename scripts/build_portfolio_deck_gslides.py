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
# Photo frames (x, y, width, height), bleeding off the right and bottom edges.
COVER_FRAME = (528, 72, 432, 468)
CLOSE_FRAME = (672, 196, 288, 344)
FOOTER = 'Cultural Blend   Kiva funding speed, 1.45 million loans, 2016–2025'

NAVY, YELLOW, TEAL, PAPER = '#1C2333', '#FFDD04', '#31688E', '#FBFAF6'
GREY, SLATE, RED, RULE, WHITE = '#59636E', '#46576C', '#C64040', '#999999', '#FFFFFF'
TINT, HAIR = '#FFF6B8', '#D9D7CE'
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
        return self.badge(str(n), x, y, (12, 12), RED)

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
        self.text(label, L, 29.5, 600, 14, size=10, color=TEAL, bold=True, spans=spans)
        self.text(slide['title'], L, 48.4, FULL - L, 34, size=24, bold=True)
        if slide.get('subtitle'):
            self.text(slide['subtitle'], L, 90.9, FULL - L, 18, size=12, color=GREY)

    def takeaways(self, items, positions):
        """One unified column; markers sit beside each heading's measured first line."""
        self.line(658, TOP, 658, END, RULE, .75)
        text, paragraphs, spans, cursor = '', [], [], 0
        for i, item in enumerate(items):
            heading, body = item['heading'], item['text']
            spans.append((cursor, cursor + len(heading), {'bold': True, 'color': NAVY}))
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

    def caption(self, label, text, y, x=L, w=R - L):
        full = f'{label} {text}'
        self.text(full, x, y, w, 12, size=8, color=GREY, spans=[(0, len(label), {'bold': True})])


def marker_positions(slide, layout):
    stored = layout.get(str(slide['n']))
    count = len(slide.get('takeaways', []))
    return stored if stored and len(stored) == count else [137 + 80 * i for i in range(count)]


def card(page, x, y, w, h, bar=TEAL):
    page.rect(x, y, w, h, PAPER)
    page.rect(x, y, w, 2.5, bar)


def key_card(page, figure, x, y, w, h, bar=TEAL, size=26):
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
    """White ground; photo frame (inserted after this batch) bleeds off the right and bottom."""
    page.ops.append({'op': 'set-background', 'slide': page.id, 'color': WHITE})
    photo_accent(page, *COVER_FRAME[:2], 128)
    page.rect(L, 156, 28, 3, YELLOW)
    page.text('UNSW MARKETING ANALYTICS HACKATHON 2026', L, 166, 460, 14, size=10, color=TEAL, bold=True)
    page.text(slide['title'], L, 186, 470, 56, size=44, bold=True)
    page.text(slide['subtitle'], L, 252, 440, 50, size=16, color=SLATE, spacing=115)
    page.text(slide['names'], L, 394, 440, 16, size=12, bold=True)
    page.text(slide['team'], L, 413, 440, 16, size=12, color=GREY)


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
              spans=[(0, len(first), {'bold': True}), (start, len(text), {'link': slide['link'], 'color': TEAL})])


def summary(page, slide, pos):
    """Three findings across the full width, then the decision; no takeaway column."""
    page.chrome(slide)
    width, gap, top, h = 279, 19, TOP, 232
    for i, body in enumerate(slide['body']):
        x = L + i * (width + gap)
        card(page, x, top, width, h, [TEAL, SLATE, NAVY][i])
        page.text(body['figure'], x + 16, top + 20, width - 32, 40, size=28, bold=True)
        page.block(body['heading'], body['text'], x + 16, top + 76, width - 32, 110)
        page.line(x + 16, top + h - 34, x + width - 16, top + h - 34, HAIR, .75)
        page.text(body['layer'], x + 16, top + h - 26, width - 32, 14, size=10, color=GREY, bold=True)
    page.rect(L, 388, FULL - L - .5, 48, NAVY)
    page.rect(L, 388, 6, 48, YELLOW)
    label = 'Next decision:'
    page.text(slide['decision'], L + 22, 388, FULL - L - 40, 48, size=12, color=WHITE, middle=True,
              spans=[(0, len(label), {'bold': True})])


def agenda(page, slide, urls):
    page.chrome(slide)
    colours = [(NAVY, WHITE), (TEAL, WHITE), (SLATE, WHITE), (YELLOW, NAVY)]
    contents = [[('Editable fields', 4), ('The outcome', 5), ('A slower market', 6)],
                [('Three evidence layers', 7)],
                [('Country uncertainty', 8), ('Small or unknown', 9), ('Regional patterns', 10),
                 ('Programme controls', 11), ('Forecast gain', 12), ('Limits of the gain', 13)],
                [('What is supported', 14), ('Three gates', 15)]]
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


def lever(page, slide, pos):
    page.chrome(slide)
    exhibit = slide['exhibit']
    panels = [('Fixed by the time a loan is listed', exhibit['fixed'], L, 293, SLATE),
              ('Still editable', exhibit['editable'], 356.5, 293.5, YELLOW)]
    for heading, items, x, w, bar in panels:
        card(page, x, TOP, w, 44 + 4 * 62, bar)
        page.text(heading, x + 12, TOP + 14, w - 24, 18, size=12, bold=True)
        pitch = 62
        for i, item in enumerate(items):
            y = TOP + 44 + i * pitch
            page.line(x + 12, y, x + w - 12, y, HAIR, .75)
            page.text(item, x + 12, y, w - 24, pitch, size=12 if bar == YELLOW and i == 0 else 10,
                      bold=bar == YELLOW and i == 0, middle=True)
    page.marker(1, 356.5 + 293.5 - 24, TOP + 14)
    page.marker(2, 356.5 + 293.5 - 24, TOP + 44 + 25)
    page.takeaways(slide['takeaways'], pos)


def outcome(page, slide, pos):
    page.chrome(slide)
    first, second = slide['key_figures']
    key_card(page, first, L, TOP, 296, 96, NAVY)
    key_card(page, second, 353.5, TOP, 296.5, 96, TEAL)
    page.marker(2, L + 296 - 22, TOP + 10)
    y = 330
    x1, x2, x3 = 105, 335, 585
    page.text('Typical sequence for a loan disbursed before listing', L, 246, 500, 18, size=12, bold=True)
    page.line(x1, y, x2, y, SLATE, 2)
    page.line(x2, y, x3, y, NAVY, 4)
    for x, fill in [(x1, SLATE), (x2, NAVY), (x3, NAVY)]:
        page.rect(x - 7, y - 7, 14, 14, fill, 'ELLIPSE')
    for x, label in [(x1, 'Partner disburses to the borrower'), (x2, 'Loan is listed on Kiva'),
                     (x3, 'Loan is fully funded')]:
        page.text(label, x - 60, y + 14, 120, 30, size=10, align='center', spacing=110)
    page.text('median 24.2 days', (x1 + x2) / 2 - 60, y - 26, 120, 16, size=10, color=GREY, align='center')
    page.text('our outcome: funding time', (x2 + x3) / 2 - 80, y - 26, 160, 16, size=10, bold=True, align='center')
    page.marker(1, x1 - 6, y - 26)
    page.caption('Scope:', slide['body'][0]['text'], 452)
    page.takeaways(slide['takeaways'], pos)


def slowdown(page, slide, pos):
    page.chrome(slide)
    base, per = 418, 5.4
    bars = slide['exhibit']['bars']
    centres = [150, 345, 540]
    for bar, cx, fill in zip(bars, centres, [NAVY, SLATE, SLATE]):
        h = bar['value'] * per
        page.rect(cx - 62, base - h, 124, h, fill)
        page.text(f"{bar['value']:.1f}%", cx - 62, base - h - 22, 124, 18, size=12, bold=True, align='center')
        page.text(bar['label'], cx - 80, base + 6, 160, 16, size=10, bold=True, align='center')
        page.text(f"{bar['n']:,} loans", cx - 80, base + 22, 160, 16, size=10, color=GREY, align='center')
    page.line(L, base, R - 10, base, NAVY, 1)
    page.marker(1, 540 + 70, base - bars[2]['value'] * per - 18)
    page.marker(2, 150 + 70, base - bars[0]['value'] * per - 18)
    page.caption('Figure 1.', 'Share of completed loans funded within 24 hours. Bars start at zero.', 460)
    page.takeaways(slide['takeaways'], pos)


def approach(page, slide):
    page.chrome(slide)
    fills = [NAVY, TEAL, SLATE]
    width, gap = 277, 22
    for i, layer in enumerate(slide['exhibit']['layers']):
        x = L + i * (width + gap)
        page.rect(x, TOP, width, 270, PAPER)
        page.badge(layer['name'], x, TOP, (width, 36), fills[i], WHITE, 12, 'RECTANGLE')
        page.text('Question', x + 12, TOP + 50, width - 24, 14, size=10, color=GREY, bold=True)
        page.text(layer['question'], x + 12, TOP + 66, width - 24, 56, size=12, bold=True, spacing=110)
        page.text('Method', x + 12, TOP + 146, width - 24, 14, size=10, color=GREY, bold=True)
        page.text(layer['method'], x + 12, TOP + 162, width - 24, 90, size=10, color=GREY, spacing=115)
    page.rect(L, 414, FULL - L - .5, 42, PAPER)
    page.rect(L, 414, 6, 42, YELLOW)
    page.text(slide['exhibit']['footer'], L + 18, 427, 800, 16, size=10, bold=True)


def clustering(page, slide, pos):
    page.chrome(slide)
    first, second = slide['key_figures']
    key_card(page, first, L, TOP, 296, 100, YELLOW)
    key_card(page, second, 353.5, TOP, 296.5, 100, TEAL)
    page.marker(2, 353.5 + 296.5 - 22, TOP + 10)
    cell, gap, x0, y0 = 20, 5, L, 250
    for i in range(120):
        row, col = divmod(i, 20)
        page.rect(x0 + col * (cell + gap), y0 + row * (cell + gap), cell, cell, YELLOW if i < 64 else NAVY)
    page.marker(1, x0 + 20 * (cell + gap) + 6, y0)
    legend = y0 + 6 * (cell + gap) + 6
    page.rect(L, legend + 2, 11, 11, YELLOW)
    page.text('Lost significance under country clustering', L + 17, legend, 260, 14, size=10)
    page.rect(320, legend + 2, 11, 11, NAVY)
    page.text('Kept significance', 337, legend, 200, 14, size=10)
    page.caption('Figure 2.', 'Each square is one term significant under HC3, across both August models.', legend + 22)
    page.takeaways(slide['takeaways'], pos)


def forest(page, slide, pos):
    page.chrome(slide)
    rows = slide['exhibit']['rows']
    x0, x1, lo, hi, top, pitch = 160, 548, -.15, .15, 148, 31
    scale = (x1 - x0) / (hi - lo)
    px = lambda value: x0 + (value - lo) * scale
    bottom = top + pitch * len(rows)
    page.rect(px(-.05), top - 6, px(.05) - px(-.05), bottom - top + 6, TINT)
    page.text('±0.05 bound', px(-.05), top - 20, px(.05) - px(-.05), 13, size=8, color=NAVY, bold=True, align='center')
    page.line(px(0), top - 6, px(0), bottom, NAVY, .75)
    status = {'bounded': ('Bounded', NAVY), 'mixed': ('Mixed', SLATE), 'unresolved': ('Unresolved', TEAL)}
    for i, row in enumerate(rows):
        y = top + i * pitch + pitch / 2 - 3
        label, colour = status[row['status_both_specs']]
        page.text(row['term'].capitalize(), L, y - 7, 112, 14, size=10)
        page.line(px(row['ci90_low']), y, px(row['ci90_high']), y, colour, 2)
        page.rect(px(row['estimate']) - 4, y - 4, 8, 8, colour, 'ELLIPSE')
        page.text(label, 572, y - 7, 72, 14, size=10, color=colour, bold=True)
    for value, name in [(-.1, '−0.10'), (-.05, '−0.05'), (0, '0'), (.05, '+0.05'), (.1, '+0.10')]:
        page.text(name, px(value) - 20, bottom + 2, 40, 12, size=8, color=GREY, align='center')
    page.marker(1, 552, top + 1 * pitch + 6)
    page.marker(2, 552, top + 8 * pitch + 6)
    page.marker(3, px(.05) + 4, top - 21)
    page.caption('Figure 3.', 'Change in log(1 + days) per extra mention per 100 words (sentiment per +0.5 score), '
                              '90% interval, expanded specification. Status covers both specifications.', bottom + 18)
    page.takeaways(slide['takeaways'], pos)


def regions(page, slide, pos):
    page.chrome(slide)
    x0, x1, lo, hi = 170, 630, -.30, .15
    scale = (x1 - x0) / (hi - lo)
    px = lambda value: x0 + (value - lo) * scale
    top, bottom = 140, 420
    page.line(px(0), top, px(0), bottom, NAVY, .75)
    fmt = lambda pair: f'[{pair[0]:.4f}, {pair[1]:.4f}]'.replace('-', '−')
    for i, row in enumerate(slide['exhibit']['rows']):
        y = top + 14 + i * 136
        page.block(row['region'], f"{row['countries']} countries\n{row['loans']:,} loans", L, y + 8, 116, 60)
        normal, heuristic = row['normal_ci'], row['heuristic_ci']
        page.text(f'Country-clustered, normal reference {fmt(normal)}', x0, y, 450, 14, size=10)
        page.line(px(normal[0]), y + 26, px(normal[1]), y + 26, NAVY, 3)
        page.rect(px(row['estimate']) - 4.5, y + 21.5, 9, 9, NAVY, 'ELLIPSE')
        page.text(f't(1) heuristic screen {fmt(heuristic)}', x0, y + 50, 450, 14, size=10, color=TEAL, bold=True)
        page.line(px(heuristic[0]), y + 76, px(heuristic[1]), y + 76, TEAL, 3)
        page.rect(px(row['estimate']) - 4.5, y + 71.5, 9, 9, TEAL, 'ELLIPSE')
    for value, name in [(-.2, '−0.20'), (-.1, '−0.10'), (0, '0'), (.1, '+0.10')]:
        page.text(name, px(value) - 20, bottom + 3, 40, 12, size=8, color=GREY, align='center')
    y = top + 14
    page.marker(1, px(.1043) + 6, y + 70)
    page.marker(2, L + 90, y + 8)
    page.caption('Figure 4.', 'Change in log(1 + days) per extra family mention per 100 words. Dots are the slope estimates.', 442)
    page.takeaways(slide['takeaways'], pos)


def persist(page, slide, pos):
    page.chrome(slide)
    exhibit = slide['exhibit']
    table(page, exhibit['columns'], exhibit['rows'], L, TOP, R - L - 6, 40)
    first, second = slide['key_figures']
    key_card(page, first, L, 268, 296, 110, TEAL, 24)
    key_card(page, second, 353.5, 268, 296.5, 110, NAVY, 24)
    page.marker(1, L + 296 - 22, 278)
    page.marker(2, 353.5 + 296.5 - 22, 278)
    page.caption('Note:', exhibit['note'], 392)
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
    key_card(page, {'value': '5 of 5', 'label': 'years with lower error'}, 498, 246, 152, 92, TEAL, 24)
    key_card(page, {'value': '728,640', 'label': 'evaluation records'}, 498, 350, 152, 92, SLATE, 24)
    page.marker(1, 498 + 152 - 22, TOP + 10)
    page.marker(2, 290, legend_y + 1)
    page.caption('Figure 5.', 'MAE in days, lower is better. Linear model on identical evaluation rows. Bars start at zero.', 450)
    page.takeaways(slide['takeaways'], pos)


def gains(page, slide, pos):
    page.chrome(slide)
    panels = slide['exhibit']['series']
    lo, hi, width, top, pitch = -.1, .55, 244, 168, 49
    for p, panel in enumerate(panels):
        px0 = L + p * 310
        plot = px0 + 40
        px = lambda value: plot + (value - lo) * width / (hi - lo)
        colour = [NAVY, TEAL][p]
        page.text(panel['name'], px0, TOP + 2, 290, 16, size=10, bold=True, color=colour)
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
    page.marker(2, L, 449)
    page.text('Country resampling, not shown: intervals include zero in 4 of 5 linear and 3 of 5 tree years.',
              L + 18, 448, 570, 14, size=10)
    page.caption('Figure 6.', 'MAE gain in days with month-resampled 95% intervals; positive is better. Both panels share one scale.', 464)
    page.takeaways(slide['takeaways'], pos)


def supports(page, slide):
    page.chrome(slide)
    width = 426
    for i, column in enumerate(slide['columns']):
        x = L + i * (width + 22.5)
        fill = [NAVY, TEAL][i]
        page.rect(x, TOP, width, 320, PAPER)
        page.badge(column['heading'], x, TOP, (width, 36), fill, WHITE, 12, 'RECTANGLE')
        pitch = 280 / len(column['items'])
        for j, item in enumerate(column['items']):
            y = TOP + 36 + j * pitch
            if j:
                page.line(x + 14, y, x + width - 14, y, HAIR, .75)
            page.text(item, x + 14, y, width - 28, pitch, size=12, middle=True)


def gates(page, slide):
    page.chrome(slide)
    width, gap = 262, 44
    fills = [(NAVY, WHITE), (TEAL, WHITE), (YELLOW, NAVY)]
    for i, step in enumerate(slide['steps']):
        x = L + i * (width + gap)
        card(page, x, 160, width, 176, fills[i][0])
        page.badge(step['n'], x + 14, 176, (36, 36), *fills[i], 12)
        page.text(step['name'], x + 14, 224, width - 28, 18, size=12, bold=True)
        page.text(step['text'], x + 14, 246, width - 28, 70, size=10, color=GREY, spacing=115)
        if i < 2:
            page.rect(x + width + 12, 238, 20, 20, SLATE, 'RIGHT_ARROW')


def a_table(page, slide):
    page.chrome(slide)
    exhibit = slide['exhibit']
    table(page, exhibit['columns'], exhibit['rows'], L, TOP, FULL - L, 40 if len(exhibit['rows']) < 3 else 42)
    y = TOP + (40 if len(exhibit['rows']) < 3 else 42) * (len(exhibit['rows']) + 1) + 34
    for i, body in enumerate(slide.get('body', [])):
        page.block(body['heading'], body['text'], L + i * 450, y, 425, 90)
    if slide.get('note'):
        page.caption('Note:', slide['note'].removeprefix('Note: '), y, w=FULL - L)


def a_metrics(page, slide):
    page.chrome(slide)
    figures = slide['key_figures']
    width = 275
    for i, figure in enumerate(figures[:2]):
        key_card(page, figure, L + i * (width + 25), TOP, width, 104, NAVY)
    for i, figure in enumerate(figures[2:]):
        key_card(page, figure, L + i * (width + 25), 250, width, 104, TEAL)
    page.caption('Scope:', slide['note'].removeprefix('Scope: '), 372, w=FULL - L)


def a_topics(page, slide):
    page.chrome(slide)
    for i, figure in enumerate(slide['key_figures']):
        key_card(page, figure, L + i * 449, TOP, 426, 104, [TEAL, SLATE][i])
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


def cover_image(work: Path, frame: tuple, name: str) -> Path:
    """Crop the photograph to a frame and round its one visible (top-left) corner, 24 pt."""
    scale = 2.5
    width, height, radius = int(frame[2] * scale), int(frame[3] * scale), int(24 * scale)
    source = Image.open(PHOTO).convert('RGB')
    ratio = width / height
    w, h = source.size
    crop = (int((w - h * ratio) / 2), 0, int((w + h * ratio) / 2), h) if w / h > ratio else \
           (0, int((h - w / ratio) / 2), w, int((h + w / ratio) / 2))
    image = source.crop(crop).resize((width, height), Image.LANCZOS).convert('RGBA')
    mask = Image.new('L', (width, height), 255)
    corner = Image.new('L', (radius * 2, radius * 2), 0)
    ImageDraw.Draw(corner).pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=255)
    mask.paste(corner.crop((0, 0, radius, radius)), (0, 0))
    image.putalpha(mask)
    target = work / name
    image.save(target)
    return target


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


def prepare_slides(pres: str, reuse: bool, count: int) -> list[dict]:
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
        ops = [{'op': 'delete-element', 'element': element['objectId']} for slide in slides
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
    slides = prepare_slides(pres, bool(args.reuse), len(story))
    ensure_footer(pres)
    urls = {i + 1: f'https://docs.google.com/presentation/d/{pres}/edit#slide=id.{s["objectId"]}'
            for i, s in enumerate(slides)}
    builders = {'summary': summary, 'lever': lever, 'outcome': outcome, 'slowdown': slowdown,
                'clustering': clustering, 'equivalence': forest, 'regions': regions, 'persist': persist,
                'forecast': forecast, 'gain_uncertainty': gains}
    plain = {'approach': approach, 'supports': supports, 'gates': gates, 'a_screen': a_table,
             'a_asof': a_table, 'a_primary': a_metrics, 'a_topics': a_topics, 'cover': cover, 'close': close}
    for slide, item in zip(story, slides):
        page = Page(item['objectId'])
        for element in item.get('pageElements', []):
            if 'placeholder' in element.get('shape', {}):
                page.ops.append({'op': 'update-shape', 'element': element['objectId'], 'content_alignment': 'TOP'})
        if slide['id'] in builders:
            builders[slide['id']](page, slide, marker_positions(slide, layout))
        elif slide['id'] == 'agenda':
            agenda(page, slide, urls)
        else:
            plain[slide['id']](page, slide)
        notes_id = next(e['objectId'] for e in item['slideProperties']['notesPage']['pageElements']
                        if e.get('shape', {}).get('placeholder', {}).get('type') == 'BODY')
        add_notes(page, slide, notes_id)
        submit(pres, page.ops)
        print(f"slide {slide['n']}: {len(page.ops)} ops", flush=True)
    # Images last so they sit above the yellow accent blocks.
    with tempfile.TemporaryDirectory() as work:
        for index, frame in [(0, COVER_FRAME), (15, CLOSE_FRAME)]:
            x, y, w, h = frame
            run('mutate', 'insert-image-from-file', pres, '--slide', slides[index]['objectId'],
                '--file', str(cover_image(Path(work), frame, f'frame-{index}.png')),
                '--x', str(x), '--y', str(y), '--width', str(w), '--height', str(h))
    # UNSW host mark directly on white, 330 x 140 px source at its own proportions.
    run('mutate', 'insert-image-from-file', pres, '--slide', slides[0]['objectId'],
        '--file', str(LOGO), '--x', str(L), '--y', '446', '--width', '84.9', '--height', '36')
    print(f'https://docs.google.com/presentation/d/{pres}/edit')


if __name__ == '__main__':
    main()
