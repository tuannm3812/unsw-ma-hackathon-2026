#!/usr/bin/env python3
"""Write a self-contained HTML preview of the portfolio deck from the Google-rendered PNGs.

Run scripts/qa_portfolio_deck.py DECK_ID first to refresh the PNGs. Output:
docs/presentation/portfolio_deck/output/deck-preview.html (JPEG previews embedded as data URIs).
"""
import base64
import html
import io
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / 'docs/presentation/portfolio_deck'
DECK_ID = '1Q7n_sOn_4HL68_Mk-GogDOtS9P_pfPVXLNUeinV7pFM'
DARK = '--bg: #12161F; --surface: #1C2333; --fg: #EEF0F3; --muted: #A9B1BC; --rule: #2E3646; --teal: #7FB3D5; color-scheme: dark;'

STYLE = """
/* Layout: one reading column of full-width slide renders, a sticky slide index above. */
:root { --bg: #F4F3EE; --surface: #FFFFFF; --fg: #1C2333; --muted: #59636E; --rule: #D9D7CE; --accent: #FFDD04; --teal: #31688E;
  --font: "Google Sans", "Product Sans", system-ui, -apple-system, "Segoe UI", sans-serif; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { DARK } }
:root[data-theme="dark"] { DARK }
body { background: var(--bg); color: var(--fg); font-family: var(--font); font-size: 15px; line-height: 1.5; }
.wrap { max-width: 1040px; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 32px 64px; }
header { display: grid; gap: 10px; padding-bottom: 20px; border-bottom: 1px solid var(--rule); }
.eyebrow { font-size: 12px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--teal);
  display: flex; align-items: center; gap: 10px; }
.eyebrow::before { content: ""; width: 28px; height: 3px; background: var(--accent); }
h1 { margin: 0; font-size: clamp(26px, 4vw, 36px); line-height: 1.15; text-wrap: balance; }
.meta { margin: 0; color: var(--muted); max-width: 65ch; }
.open { justify-self: start; display: inline-flex; padding: 9px 14px; border-radius: 6px; background: var(--fg);
  color: var(--bg); font-weight: 700; text-decoration: none; }
.open:focus-visible, nav a:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 10; background: var(--bg); }
nav { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5; background: var(--bg); padding-block: 12px;
  display: flex; flex-wrap: wrap; gap: 6px; border-bottom: 1px solid var(--rule); }
nav a { min-width: 34px; text-align: center; padding: 4px 8px; border: 1px solid var(--rule); border-radius: 4px;
  color: var(--fg); text-decoration: none; font-size: 13px; font-variant-numeric: tabular-nums; }
nav a:hover { border-color: var(--teal); }
main { display: grid; gap: 36px; padding-top: 24px; }
.slide { margin: 0; display: grid; gap: 10px; scroll-margin-top: 72px; }
.slide img { display: block; width: 100%; height: auto; aspect-ratio: 16 / 9; border: 1px solid var(--rule); border-radius: 4px; background: #fff; }
figcaption { display: flex; flex-wrap: wrap; gap: 4px 12px; align-items: baseline; }
.num { font-weight: 700; font-variant-numeric: tabular-nums; }
.ttl { min-width: 0; }
.sec { color: var(--muted); font-size: 13px; text-transform: uppercase; letter-spacing: .05em; margin-left: auto; }
footer { margin-top: 40px; color: var(--muted); font-size: 13px; }
@media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }
""".replace('DARK', DARK)


def main() -> None:
    story = json.loads((DECK / 'storyline.json').read_text())['slides']
    figures = []
    for i, slide in enumerate(story, 1):
        image = Image.open(DECK / f'output/slide-{i:02d}.png').convert('RGB')
        buffer = io.BytesIO()
        image.save(buffer, 'JPEG', quality=85, optimize=True)
        data = base64.b64encode(buffer.getvalue()).decode()
        label = f"Slide {slide['n']}" if isinstance(slide['n'], int) else f"Appendix {slide['n']}"
        section = slide.get('section') or ('Cover' if slide['n'] == 1 else 'Close')
        sub = f" · {html.escape(slide['sublabel'])}" if slide.get('sublabel') else ''
        figures.append(
            f'<figure class="slide" id="s{i}"><img src="data:image/jpeg;base64,{data}" width="1600" height="900" '
            f'alt="{html.escape(label)}: {html.escape(slide["title"])}" loading="lazy"><figcaption>'
            f'<span class="num">{html.escape(label)}</span><span class="ttl">{html.escape(slide["title"])}</span>'
            f'<span class="sec">{html.escape(section)}{sub}</span></figcaption></figure>')
    nav = ''.join(f'<a href="#s{i}">{s["n"]}</a>' for i, s in enumerate(story, 1))
    page = f'''<title>Cultural Blend deck preview</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>{STYLE}</style>
<div class="wrap">
<header>
  <div class="eyebrow">Portfolio deck · November 2026</div>
  <h1>Beyond a good story</h1>
  <p class="meta">Cultural Blend's portfolio deck on Kiva funding speed: 22 core slides and 8 appendix slides, rendered by Google Slides. The live deck is the editable source.</p>
  <a class="open" href="https://docs.google.com/presentation/d/{DECK_ID}/edit">Open in Google Slides</a>
</header>
<nav aria-label="Slides">{nav}</nav>
<main>
{chr(10).join(figures)}
</main>
<footer>Previews are static renders; speaker notes and links live in the Google Slides deck.</footer>
</div>
'''
    target = DECK / 'output/deck-preview.html'
    target.write_text(page)
    print(f'{target} {target.stat().st_size / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
