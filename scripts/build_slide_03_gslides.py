#!/usr/bin/env python3
"""Build Slide 3 (Portfolio Blueprint / Table of Contents) natively in Google Slides.

Follows docs/presentation/DESIGN.md strictly:
- Google Sans for titles, card headings, and body
- Courier New for section chips, kickers, and monospace tags
- Exact signature theme palette (#FFDD04, #1C2333, #31688E, #6E7278, #F3F2ED)
"""
import json
import subprocess
from pathlib import Path

PRES_ID = "17rHwKFXiqN4GBo8TT5xnBWk33bN7niIodw9K9APNwDk"
SLIDE_ID = "SLIDES_API349037430_0"

# Fetch current elements on slide 3 to delete them
res = subprocess.check_output(["gslides", "readonly", "get-page", PRES_ID, SLIDE_ID, "--json"])
data = json.loads(res)
del_ops = [{"op": "delete-element", "element": el["objectId"]} for el in data.get("pageElements", [])]

ops = []
ops.extend(del_ops)

# 1. Background
ops.append({
    "op": "set-background",
    "slide": SLIDE_ID,
    "color": "#FBFAF6"
})

# 2. Eyebrow
ops.append({
    "op": "add-textbox",
    "slide": SLIDE_ID,
    "text": "TABLE OF CONTENTS · PROJECT BLUEPRINT",
    "x": 54,
    "y": 28,
    "width": 500,
    "height": 22,
    "font_size": 11,
    "font_family": "Courier New",
    "bold": True,
    "color": "#31688E"
})

# 3. Active Section Chip: OVERVIEW
ops.append({
    "op": "add-textbox",
    "slide": SLIDE_ID,
    "text": "OVERVIEW",
    "x": 810,
    "y": 26,
    "width": 96,
    "height": 24,
    "font_size": 10.5,
    "font_family": "Courier New",
    "bold": True,
    "color": "#1C2333",
    "background_color": "#FFDD04",
    "alignment": "center"
})

# 4. Slide Title
ops.append({
    "op": "add-textbox",
    "slide": SLIDE_ID,
    "text": "How the 1.45M loan investigation is structured",
    "x": 54,
    "y": 52,
    "width": 750,
    "height": 38,
    "font_size": 26,
    "font_family": "Google Sans",
    "bold": True,
    "color": "#1C2333"
})

# 5. Title Accent Bar
ops.append({
    "op": "add-shape",
    "slide": SLIDE_ID,
    "shape_type": "RECTANGLE",
    "x": 54,
    "y": 95,
    "width": 65,
    "height": 4,
    "background_color": "#FFDD04"
})

# 6. Four Column Cards
sections = [
    {
        "tag": "ACT I · CONTEXT",
        "slides": "SLIDES 4–5",
        "title": "The Operating Reality",
        "sub": "Why narrative advice is pitched, and what really happens on the ground.",
        "bullets": [
            "▪ The Platform Dilemma: Text is the only unsealed lever at listing; platforms want to coach it.",
            "▪ Market Slowdown: Same-day funding collapsed from 46% to 30% post-pandemic.",
            "▪ Capital Reality: 96.4% pre-disbursed; partner working capital waits, not borrowers."
        ]
    },
    {
        "tag": "ACT II · INFERENCE",
        "slides": "SLIDES 6–9",
        "title": "Empirical Stress-Test",
        "sub": "Testing narrative claims against 1.45M loans with econometric rigor.",
        "bullets": [
            "▪ Methodological Screen: 64 of 120 coefficients collapse under country-clustering.",
            "▪ Structural Dominance: Amount, terms, and sector beat storytelling by ~10×.",
            "▪ Narrative Scrutiny: Urgency dissolves (p ≈ 0.49); family rests on 2-country screen.",
            "▪ Topic Modeling: Topics track loan purpose (water vs farming; 9× swing)."
        ]
    },
    {
        "tag": "ACT III · STRATEGY",
        "slides": "SLIDES 10–12",
        "title": "The Strategic Playbook",
        "sub": "High-ROI platform decisions, borrower realism, and epistemic bounds.",
        "bullets": [
            "▪ 4-Quadrant Playbook: Kill generic tips, A/B test family framing, fix structural lag.",
            "▪ Borrower Realism: Set cash-flow expectations; do NOT game gender or story.",
            "▪ Scientific Bounds: Observational associations, completed-loans survival truncation."
        ]
    },
    {
        "tag": "APPENDIX · AUDITS",
        "slides": "SLIDES 14–17",
        "title": "Methodological Audits",
        "sub": "Full numerical proofs and statistical architecture for defense.",
        "bullets": [
            "▪ Two-Country Problem: The conservative t(1) = 12.7 heuristic screen in full.",
            "▪ Predictive vs Causal: Why SHAP importance cannot certify policy rules.",
            "▪ The ~10× Comparison: Decile monotonicities and correlation breakdown.",
            "▪ 24h Early Warning: LightGBM classifier architecture (ROC AUC 0.8997)."
        ]
    }
]

card_w = 198
card_gap = 20
card_y = 110
card_h = 295

for i, sec in enumerate(sections):
    cx = 54 + i * (card_w + card_gap)

    # Card background container
    ops.append({
        "op": "add-shape",
        "slide": SLIDE_ID,
        "shape_type": "ROUND_RECTANGLE",
        "x": cx,
        "y": card_y,
        "width": card_w,
        "height": card_h,
        "background_color": "#FFFFFF"
    })

    # 1) Tag
    ops.append({
        "op": "add-textbox",
        "slide": SLIDE_ID,
        "text": sec["tag"],
        "x": cx + 10,
        "y": card_y + 10,
        "width": card_w - 20,
        "height": 14,
        "font_size": 8.5,
        "font_family": "Courier New",
        "bold": True,
        "color": "#31688E"
    })

    # 2) Slide range
    ops.append({
        "op": "add-textbox",
        "slide": SLIDE_ID,
        "text": sec["slides"],
        "x": cx + 10,
        "y": card_y + 24,
        "width": card_w - 20,
        "height": 14,
        "font_size": 8,
        "font_family": "Courier New",
        "bold": True,
        "color": "#6E7278"
    })

    # 3) Card Title
    ops.append({
        "op": "add-textbox",
        "slide": SLIDE_ID,
        "text": sec["title"],
        "x": cx + 10,
        "y": card_y + 40,
        "width": card_w - 20,
        "height": 22,
        "font_size": 13,
        "font_family": "Google Sans",
        "bold": True,
        "color": "#1C2333"
    })

    # 4) Card Subtitle
    ops.append({
        "op": "add-textbox",
        "slide": SLIDE_ID,
        "text": sec["sub"],
        "x": cx + 10,
        "y": card_y + 64,
        "width": card_w - 20,
        "height": 34,
        "font_size": 9,
        "font_family": "Google Sans",
        "italic": True,
        "color": "#6E7278"
    })

    # 5) Thin accent divider
    ops.append({
        "op": "add-shape",
        "slide": SLIDE_ID,
        "shape_type": "RECTANGLE",
        "x": cx + 10,
        "y": card_y + 100,
        "width": card_w - 20,
        "height": 1,
        "background_color": "#E2E0D6"
    })

    # 6) Bullets block
    body_text = "\n\n".join(sec["bullets"])
    ops.append({
        "op": "add-textbox",
        "slide": SLIDE_ID,
        "text": body_text,
        "x": cx + 10,
        "y": card_y + 108,
        "width": card_w - 20,
        "height": 182,
        "font_size": 9,
        "font_family": "Google Sans",
        "color": "#1C2333"
    })

# 7. Bottom Methodology Stack Banner
ops.append({
    "op": "add-shape",
    "slide": SLIDE_ID,
    "shape_type": "ROUND_RECTANGLE",
    "x": 54,
    "y": 420,
    "width": 852,
    "height": 78,
    "background_color": "#F3F2ED"
})

ops.append({
    "op": "add-textbox",
    "slide": SLIDE_ID,
    "text": "PORTFOLIO METHODOLOGY & REPRODUCIBILITY STACK · 1,453,846 REAL LOANS (2016–2025)",
    "x": 68,
    "y": 426,
    "width": 824,
    "height": 18,
    "font_size": 9.5,
    "font_family": "Courier New",
    "bold": True,
    "color": "#1C2333"
})

ops.append({
    "op": "add-textbox",
    "slide": SLIDE_ID,
    "text": "Econometric OLS Duration Modeling · Binomial GLM · Country-Clustered Standard Errors · Conservative Few-Cluster t(1)=12.7 Screen · NMF Topic Extraction (8 Components) · LightGBM Predictive Benchmark (Strict Chronological Split, Zero Future Leakage)",
    "x": 68,
    "y": 448,
    "width": 824,
    "height": 42,
    "font_size": 9.5,
    "font_family": "Google Sans",
    "color": "#1C2333"
})

# 8. Bottom Full-width Yellow Footer Bar
ops.append({
    "op": "add-shape",
    "slide": SLIDE_ID,
    "shape_type": "RECTANGLE",
    "x": 0,
    "y": 515,
    "width": 960,
    "height": 25,
    "background_color": "#FFDD04"
})

ops.append({
    "op": "add-textbox",
    "slide": SLIDE_ID,
    "text": "UNSW Marketing Analytics Hackathon 2026",
    "x": 54,
    "y": 518,
    "width": 600,
    "height": 18,
    "font_size": 9.5,
    "font_family": "Courier New",
    "bold": True,
    "color": "#1C2333"
})

# 9. Presenter Notes
ops.append({
    "op": "set-notes",
    "slide": SLIDE_ID,
    "text": (
        "(Portfolio Blueprint) This executive architecture maps the full 1.45 million loan investigation. "
        "Readers can navigate the sequence across three core phases: from the initial platform dilemma (Act I) "
        "through our econometric stress-testing and statistical falsification (Act II), into Kiva's high-ROI platform strategy (Act III), "
        "supported by complete methodological proofs in the Technical Appendix.\n\n"
        "[Navigation] Slides 4–5 (Act I), Slides 6–9 (Act II), Slides 10–12 (Act III), Slides 14–17 (Technical Appendix)."
    )
})

out_json = Path("/tmp/slide3_native_ops.json")
with open(out_json, "w") as f:
    json.dump(ops, f, indent=2)

print(f"Generated {len(ops)} operations ({len(del_ops)} deletes + {len(ops) - len(del_ops)} creates)")
