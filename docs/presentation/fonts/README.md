# Deck typeface: DM Sans

The PPTX names "DM Sans" for slide text but PowerPoint does NOT embed
fonts from these files - it looks the name up on the machine opening the
deck. **On every machine that edits or presents the deck: double-click
both `.ttf` files here and click Install Font.** Without that, PowerPoint
silently substitutes another face and line-wrapping may shift.

The final PDF export sent to the organizer embeds fonts regardless of the
recipient's machine, so only editing/presenting machines need the install.
Chart PNGs are immune either way (their type is rasterized).

DM Sans is the open (SIL-OFL, `OFL.txt`) Google-commissioned substitute
for Google Sans, which is not freely redistributable. Dropping a real
`GoogleSans*.ttf` here makes `scripts/build_charts.py` prefer it
automatically (keep it uncommitted).
