"""Render the portfolio deck's extra Material Symbols Rounded icons in deck colours.

Same method and pinned version as the parent standard's build_icons.py:

    uv run --no-project --with "playwright==1.60.0" python scripts/build_deck_icons.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / 'docs/presentation/portfolio_deck/assets/icons'
ICONS = {'payments': ['violet', 'navy'], 'storefront': ['violet', 'navy'], 'groups': ['violet', 'navy'],
         'account_balance': ['violet', 'navy'], 'check_circle': ['navy'], 'block': ['slate'],
         # framing-measure key (slide 7) and the slides that reuse it
         'family_restroom': ['navy'], 'water_drop': ['navy'], 'bolt': ['navy'], 'favorite': ['navy'],
         'schedule': ['navy'], 'person': ['navy'], 'record_voice_over': ['navy'], 'sentiment_satisfied': ['navy'],
         # slide 15 scorecard columns
         'calendar_month': ['navy'], 'public': ['violet'],
         # slide 16 who row
         'desktop_windows': ['navy'], 'handshake': ['navy'], 'manage_search': ['navy']}
COLOURS = {'violet': '#5B4B8A', 'navy': '#1C2333', 'slate': '#46576C', 'white': '#FFFFFF'}
FONT = ('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD'
        '@24,400,0,0')

with sync_playwright() as p:
    browser = p.chromium.launch()
    tab = browser.new_page(viewport={'width': 96, 'height': 96}, device_scale_factor=2)
    for icon, colours in ICONS.items():
        for name in colours:
            if (OUT / f'{icon}-{name}.png').exists():
                continue
            style = ("font-family:'Material Symbols Rounded';font-size:96px;line-height:96px;"
                     f"display:block;color:{COLOURS[name]}")
            tab.set_content(f'<link rel="stylesheet" href="{FONT}"><style>html,body{{margin:0;'
                            f'background:transparent}}</style><span style="{style}">{icon}</span>')
            tab.evaluate('document.fonts.ready')
            tab.wait_for_timeout(300)
            tab.locator('span').screenshot(path=str(OUT / f'{icon}-{name}.png'), omit_background=True)
            print(icon, name)
    browser.close()
