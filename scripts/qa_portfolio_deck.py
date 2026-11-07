#!/usr/bin/env python3
"""Export and check the portfolio deck from Google's own rendering.

  qa_portfolio_deck.py DECK_ID [--write-markers]

Exports the PDF and per-slide PNG previews to docs/presentation/portfolio_deck/output/,
then reports text outside the content frame, fonts that are not Google Sans, and any
number shown on a slide that the claims register does not contain. With --write-markers
it stores each takeaway heading's rendered height in marker_layout.json for the builder.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / 'docs/presentation/portfolio_deck'
OUT = DECK / 'output'
REGISTER = ROOT / 'docs/presentation/claims_register.md'
PDF = OUT / 'cultural-blend-portfolio-deck.pdf'
GSLIDES = shutil.which('gslides') or str(Path.home() / '.gemini/antigravity/bin/gslides')
# Structural numbers that are not claims: agenda and step numbers, figure labels, axis ticks,
# and the digits in the GitHub username on the close slide.
ALLOWED = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17',
           '18', '19', '20', '3812', '01', '02', '03', '04', '100', '24', '2026', '0.10', '0.05', '0.25', '0.50', '0.20'}


def lines(page: int) -> list[dict]:
    raw = subprocess.run(['pdftotext', '-bbox-layout', '-f', str(page), '-l', str(page), str(PDF), '-'],
                         check=True, capture_output=True, text=True).stdout
    result = []
    for match in re.finditer(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>',
                             raw, re.S):
        words = re.findall(r'<word [^>]*>(.*?)</word>', match.group(5))
        x0, y0, x1, y1 = map(float, match.groups()[:4])
        result.append({'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'text': html.unescape(' '.join(words))})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('deck')
    parser.add_argument('--write-markers', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run([GSLIDES, 'readonly', 'export', args.deck, str(PDF), '--format', 'pdf'], check=True,
                   capture_output=True)
    for old in OUT.glob('slide-*.png'):
        old.unlink()
    subprocess.run(['pdftoppm', '-r', '120', '-png', str(PDF), str(OUT / 'slide')], check=True)
    story = json.loads((DECK / 'storyline.json').read_text())['slides']
    register = REGISTER.read_text().replace('−', '-').replace(',', '')
    problems, markers = [], {}
    for index, slide in enumerate(story, 1):
        found = lines(index)
        for line in found:
            is_number = line['y0'] > 490  # footer zone: page number and footer text
            if slide['layout' if 'layout' in slide else 'id'] in ('cover', 'close') or is_number:
                continue
            if line['y1'] > 477:
                problems.append(f"slide {slide['n']}: text ends at y{line['y1']:.0f}: {line['text'][:50]}")
            if line['x1'] > 920 or line['x0'] < 43:
                problems.append(f"slide {slide['n']}: text x {line['x0']:.0f}-{line['x1']:.0f}: {line['text'][:50]}")
        titles = [l for l in found if 45 < l['y0'] < 90 and l['x0'] < 60]
        if len(titles) > 1:
            problems.append(f"slide {slide['n']}: title wraps")
        text = ' '.join(l['text'] for l in found).replace('−', '-').replace(',', '')
        for token in re.findall(r'\d+(?:\.\d+)?', text):
            if token not in ALLOWED and token not in register:
                problems.append(f"slide {slide['n']}: number not in register: {token}")
        if slide.get('takeaways'):
            column = [l for l in found if l['x0'] >= 680]
            positions = []
            for item in slide['takeaways']:
                hit = next((l for l in column if l['text'].startswith(item['heading'][:18])), None)
                if hit is None:
                    problems.append(f"slide {slide['n']}: heading not found: {item['heading']}")
                    continue
                positions.append(round((hit['y0'] + hit['y1']) / 2 - 6, 1))
            markers[str(slide['n'])] = positions
    fonts = subprocess.run(['pdffonts', str(PDF)], check=True, capture_output=True, text=True).stdout
    names = {row.split()[0] for row in fonts.splitlines()[2:] if row.strip()}
    problems += [f'font: {name}' for name in sorted(names) if 'GoogleSans' not in name.replace(' ', '')]
    if args.write_markers:
        (DECK / 'marker_layout.json').write_text(json.dumps(markers, indent=2) + '\n')
    print('\n'.join(problems) or 'no automated problems')
    print(f'{len(story)} slides; fonts: {sorted(names)}')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
