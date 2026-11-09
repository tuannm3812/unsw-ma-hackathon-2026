#!/usr/bin/env python3
"""Build Team Cultural Blend - UNSW Hackathon 2026 v3 (Executive 3-Act Hybrid).

Strictly controlled by:
- docs/presentation/archive/november_old_decks/SLIDE_CONTENT_BRIEF.md (The single source of truth for narrative & evidence)
- docs/presentation/DESIGN.md (Visual identity, spatial grid, typography, colors)

Deck Architecture (17-Slide Portfolio Master Deck):
- Prologue & Blueprint:
  Slide 1: Cover · Beyond a Good Story (1.45M real loans)
  Slide 2: Step 01 · The Executive Verdict (BLUF: Belief vs 1.45M Loans Reveal)
  Slide 3: OVERVIEW · Project Architecture & Executive Table of Contents
- Act I: The Platform Promise & Operating Reality (Sophia)
  Slide 4: Step 02 · The Motivation (Why platforms coach story: the only unsealed lever)
  Slide 5: Step 03 · Finding 1: The Slower Market & Partner Capital (46% → 30%, 96.4% pre-disbursed)
- Act II: The Empirical Stress-Test (Sophia -> Tuan hand-off at Slide 7)
  Slide 6: Step 04 · Methodology (Why big data lies: 64/120 drop, chronological holdout)
  Slide 7: Step 05 · Finding 2: Structural Dominance (Structure beats story ~10×)
  Slide 8: Step 06 · Finding 3: The Narrative Scrutiny (Urgency p=0.49, 2-country screen t(1)=12.7)
  Slide 9: Step 07 · Finding 4: Topics Encode Cause (Water vs farming; 9× swing)
- Act III: The High-ROI Strategic Playbook (Tuan)
  Slide 10: Step 08 · Platform Playbook for Kiva (4-Action Executive Matrix)
  Slide 11: Step 08 · Setting Expectations for Borrowers & Partners (What NOT to game)
  Slide 12: Step 08 · Limits & Scientific Rigor (Three boundaries on the evidence)
  Slide 13: Epilogue · The Core Thesis Statement & Call to Q&A
- Appendix: Technical Defense & Proof Pack
  Slide 14 (A1): The Two-Country Screen Problem in Full (t(1) = 12.7 critical barrier)
  Slide 15 (A2): Predictive Weight ≠ Statistical Robustness (SHAP Top 15 Analysis)
  Slide 16 (A3): The ~10× Structural Comparison Exactly (Deciles & correlation table)
  Slide 17 (A4): 24h Early Warning Classifier Architecture (ROC AUC 0.8997)
"""

import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHART_DIR = PROJECT_ROOT / "docs" / "presentation" / "charts"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "presentation" / "archive" / "november_old_decks" / "output"
OUTPUT_PPTX = OUTPUT_DIR / "Team-Cultural-Blend-UNSW-Hackathon-2026-v3.pptx"

# -----------------------------------------------------------------------------
# Signature Theme Palette (DESIGN.md)
# -----------------------------------------------------------------------------
PAPER = RGBColor(0xFB, 0xFA, 0xF6)      # Soft warm paper ground
INK = RGBColor(0x1C, 0x23, 0x33)        # Deep navy/charcoal ink
TEAL = RGBColor(0x1C, 0x23, 0x33)       # Dark Ink Navy for Cover & Closing
AMBER = RGBColor(0xFF, 0xDD, 0x04)      # Signature Yellow #FFDD04
MUTED = RGBColor(0x6E, 0x72, 0x78)      # Meta & Captions slate grey
PANEL = RGBColor(0xF3, 0xF2, 0xED)      # Card Well Fill
LINE = RGBColor(0xD9, 0xD6, 0xCC)       # Subtle border
BLUE = RGBColor(0x31, 0x68, 0x8E)       # Category eyebrow viridis blue
WHITE = RGBColor(0xFF, 0xFF, 0xFF)      # Surface white
CARD_BORDER = RGBColor(0xE2, 0xE0, 0xD6)

DISPLAY = "Google Sans"
BODY = "Google Sans"
MONO = "Courier New"

# Chart image mapping
CHARTS = {
    5: "period_24h.png",
    6: "data_split.png",
    7: "sector.png",
    8: "few_cluster_table.png",
    9: "topics.png",
    14: "region.png",
    15: "shap_top15.png",
    16: "correlations.png",
}

FIGS = {
    5: (2, "Share of loans funded within 24 hours, by analysis period.",
        "The drop is 16 points; the 'recovery' is -0.3. Exact shares 46.0% → 30.3% → 30.0% (589,823 / 298,549 / 565,474 loans)."),
    6: (1, "Chronological train/test split.",
        "The 278,887 test loans stayed sealed during training — the models never see the future they are scored on."),
    7: (3, "Mean funding speed by sector.",
        "Sanitation loans fund ~13x faster than Clothing (0.9 vs 12.1 days). Counts verified vs executed notebook."),
    8: (4, "Average within-region family-framing slope (duration model).",
        "Against the few-cluster screen (t(1) critical value 12.7), nothing clears it. Authoritative values in analysis_summary.json."),
    9: (5, "Mean funding speed by story theme.",
        "Water and sanitation stories fund in under 2 days; group farming loans take ~2 weeks — themes track what the loan is FOR."),
    14: (6, "Mean funding speed by region.",
         "North America is Haiti alone (n = 7,559) — fastest region, and exactly why single-cluster inference is off the table."),
    15: (7, "Top 15 features by mean |SHAP| value, boosted model.",
         "Ten structural features outrank the first narrative one. Rebuilt from modeling §8 printed values."),
    16: (8, "Correlation with funding speed: structural vs narrative features.",
         "Loan amount correlates ~7x stronger with speed than the best narrative signal (0.429 vs 0.058)."),
}

DEFAULT_SOURCE = "reports/generated_full_dataset/association_summary.txt (authoritative numbers); docs/presentation/archive/september_prep/deck_content.md"

def build_deck(out_path):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.50)
    blank_layout = prs.slide_layouts[6]

    def bg(slide, color):
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = color

    def box(slide, x, y, w, h):
        b = slide.shapes.add_textbox(x, y, w, h)
        tf = b.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        return tf

    def rect(slide, x, y, w, h, fill, line=None, rounded=False):
        sh = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, x, y, w, h
        )
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
        if line:
            sh.line.color.rgb = line
            sh.line.width = Pt(0.75)
        else:
            sh.line.fill.background()
        sh.shadow.inherit = False
        return sh

    def add_progress_rail(sl, active_step):
        # 8-step horizontal rail in top right (x ~ 9.0" to 12.6")
        start_x = 9.05
        chip_w = 0.38
        gap = 0.06
        for step_i in range(1, 9):
            x = Inches(start_x + (step_i - 1) * (chip_w + gap))
            is_active = (step_i == active_step)
            fill_c = AMBER if is_active else WHITE
            line_c = None if is_active else LINE
            ch = rect(sl, x, Inches(0.36), Inches(chip_w), Inches(0.34), fill_c, line=line_c, rounded=True)
            ctf = ch.text_frame
            ctf.margin_left = ctf.margin_right = ctf.margin_top = ctf.margin_bottom = Emu(0)
            p = ctf.paragraphs[0]
            p.text = f"{step_i:02d}"
            p.font.size = Pt(10.5)
            p.font.bold = True
            p.font.color.rgb = INK if is_active else MUTED
            p.font.name = MONO
            p.alignment = PP_ALIGN.CENTER
            ctf.vertical_anchor = MSO_ANCHOR.MIDDLE

    def add_chrome(sl, eyebrow_text, active_step, title_text):
        # Category Eyebrow
        tf = box(sl, Inches(0.75), Inches(0.38), Inches(8.0), Inches(0.32))
        tf.text = eyebrow_text
        p_eye = tf.paragraphs[0]
        p_eye.font.size = Pt(11.5)
        p_eye.font.color.rgb = BLUE
        p_eye.font.name = MONO
        p_eye.font.bold = True

        # Progress Rail (01..08) or Appendix / Overview Tag
        if isinstance(active_step, int) and 1 <= active_step <= 8:
            add_progress_rail(sl, active_step)
        elif active_step:
            step_str = str(active_step)
            chip_w = Inches(1.30) if len(step_str) > 3 else Inches(0.90)
            chip_x = Inches(12.80) - chip_w
            chip = rect(sl, chip_x, Inches(0.36), chip_w, Inches(0.34), AMBER, rounded=True)
            ctf = chip.text_frame
            ctf.margin_top = ctf.margin_bottom = Emu(0)
            p_chip = ctf.paragraphs[0]
            p_chip.text = step_str
            p_chip.font.size = Pt(10.5) if len(step_str) > 3 else Pt(11)
            p_chip.font.bold = True
            p_chip.font.color.rgb = INK
            p_chip.font.name = MONO
            p_chip.alignment = PP_ALIGN.CENTER
            ctf.vertical_anchor = MSO_ANCHOR.MIDDLE

        # Determine title length & wrapping
        is_long = len(title_text) > 42 and title_text not in ("The questions", "What this can't tell us")
        title_font_size = Pt(26) if is_long else Pt(30)
        title_h = Inches(0.95) if is_long else Inches(0.55)
        y_bar = Inches(1.78) if is_long else Inches(1.42)

        # Slide Title
        tf = box(sl, Inches(0.70), Inches(0.72), Inches(11.8), title_h)
        tf.text = title_text
        p_tit = tf.paragraphs[0]
        p_tit.font.size = title_font_size
        p_tit.font.bold = True
        p_tit.font.color.rgb = INK
        p_tit.font.name = DISPLAY

        # Signature Yellow Accent Bar
        rect(sl, Inches(0.75), y_bar, Inches(1.35), Pt(3.5), AMBER)

        # Full-Width Yellow Footer Bar
        rect(sl, Inches(0), Inches(7.15), Inches(13.333), Inches(0.35), AMBER)
        tf_foot = box(sl, Inches(0.75), Inches(7.17), Inches(11.5), Inches(0.30))
        p_f = tf_foot.paragraphs[0]
        p_f.text = "UNSW Marketing Analytics Hackathon 2026"
        p_f.font.size = Pt(10)
        p_f.font.bold = True
        p_f.font.color.rgb = INK
        p_f.font.name = MONO

        return y_bar + Inches(0.20)

    def add_chart_exhibit(sl, chart_id, chart_top=1.95):
        if chart_id in CHARTS:
            cand = CHART_DIR / CHARTS[chart_id]
            if cand.is_file():
                pic = sl.shapes.add_picture(str(cand), Inches(8.15), Inches(chart_top))
                max_w = Inches(4.60)
                max_h = Inches(6.55 - chart_top)
                if pic.width > max_w * 1.05 or pic.height > max_h * 1.05:
                    ratio = min(max_w / pic.width, max_h / pic.height)
                    pic.width = int(pic.width * ratio)
                    pic.height = int(pic.height * ratio)
                pic.left = Inches(8.15) + max(0, (Inches(4.60) - pic.width) // 2)

                if chart_id in FIGS and FIGS[chart_id]:
                    fig_no, fig_name, fig_notes = FIGS[chart_id]
                    cap = box(sl, Inches(8.15), Inches(6.45), Inches(4.7), Inches(0.65))
                    cp = cap.paragraphs[0]
                    r1 = cp.add_run()
                    r1.text = f"Figure {fig_no}. "
                    r1.font.size = Pt(9.5)
                    r1.font.bold = True
                    r1.font.color.rgb = INK
                    r1.font.name = BODY

                    r2 = cp.add_run()
                    r2.text = fig_name
                    r2.font.size = Pt(9.5)
                    r2.font.color.rgb = INK
                    r2.font.name = BODY

                    cp2 = cap.add_paragraph()
                    r3 = cp2.add_run()
                    r3.text = "Notes: " + fig_notes
                    r3.font.size = Pt(8.5)
                    r3.font.color.rgb = MUTED
                    r3.font.name = BODY

    # =========================================================================
    # SLIDE 1: COVER (Prologue)
    # =========================================================================
    sl1 = prs.slides.add_slide(blank_layout)
    bg(sl1, TEAL)
    arrow_box = box(sl1, Inches(12.0), Inches(0.6), Inches(0.8), Inches(0.8))
    p_arr = arrow_box.paragraphs[0]
    p_arr.text = "↗"
    p_arr.font.size = Pt(56)
    p_arr.font.bold = True
    p_arr.font.color.rgb = AMBER
    p_arr.alignment = PP_ALIGN.RIGHT

    rect(sl1, Inches(0.9), Inches(1.85), Inches(1.6), Pt(4), AMBER)
    tf = box(sl1, Inches(0.9), Inches(1.2), Inches(11.5), Inches(0.5))
    tf.text = "UNSW MARKETING ANALYTICS HACKATHON 2026"
    p = tf.paragraphs[0]
    p.font.size = Pt(13)
    p.font.color.rgb = AMBER
    p.font.name = MONO
    p.font.bold = True

    tf = box(sl1, Inches(0.85), Inches(2.1), Inches(11.8), Inches(2.0))
    tf.text = "Beyond a Good Story"
    p = tf.paragraphs[0]
    p.font.size = Pt(64)
    p.font.bold = True
    p.font.color.rgb = PAPER
    p.font.name = DISPLAY

    tf = box(sl1, Inches(0.9), Inches(4.1), Inches(10.5), Inches(1.2))
    tf.text = "When and for whom does persuasive loan language actually speed up funding?"
    p = tf.paragraphs[0]
    p.font.size = Pt(22)
    p.font.italic = True
    p.font.color.rgb = RGBColor(0xB8, 0xCE, 0xD6)
    p.font.name = BODY

    tf = box(sl1, Inches(0.9), Inches(5.6), Inches(11.5), Inches(1.2))
    p1 = tf.paragraphs[0]
    p1.text = "Team Cultural Blend"
    p1.font.size = Pt(16)
    p1.font.bold = True
    p1.font.color.rgb = AMBER
    p1.font.name = DISPLAY

    p2 = tf.add_paragraph()
    p2.text = "University of Technology Sydney"
    p2.font.size = Pt(14)
    p2.font.color.rgb = RGBColor(0xDF, 0xE7, 0xEB)
    p2.font.name = BODY

    p3 = tf.add_paragraph()
    p3.text = "Kiva loan data · 1.45 million real loans · 2016–2025"
    p3.font.size = Pt(13)
    p3.font.color.rgb = RGBColor(0x8F, 0xB0, 0xBB)
    p3.font.name = MONO

    rect(sl1, Inches(0), Inches(7.15), Inches(13.333), Inches(0.35), AMBER)
    tf_foot = box(sl1, Inches(0.75), Inches(7.17), Inches(11.5), Inches(0.30))
    p_f = tf_foot.paragraphs[0]
    p_f.text = "UNSW Marketing Analytics Hackathon 2026"
    p_f.font.size = Pt(10)
    p_f.font.bold = True
    p_f.font.color.rgb = INK
    p_f.font.name = MONO
    sl1.notes_slide.notes_text_frame.text = (
        "(Sophia, ~30s) Good morning — we're Cultural Blend: I'm Sophia, and my teammate Tuan "
        "will take you through what survives when we test it hard. Kiva is built on stories — "
        "every loan page leads with one. We asked 1.45 million real loans a single question: "
        "does the story actually move the money?\n\n[Sources] reports/generated_full_dataset/association_summary.txt"
    )

    # =========================================================================
    # SLIDE 2: THE EXECUTIVE VERDICT (Step 01 · BLUF Upfront)
    # =========================================================================
    sl2 = prs.slides.add_slide(blank_layout)
    bg(sl2, PAPER)
    start_y = add_chrome(sl2, "EXECUTIVE SUMMARY · THE VERDICT", 1, "In 1.45M loans, the story barely registers. The structure carries the signal.")

    # Two Comparative Split Cards
    c_left = rect(sl2, Inches(0.75), Inches(2.05), Inches(5.75), Inches(3.30), WHITE, CARD_BORDER, rounded=True)
    tf_l = c_left.text_frame
    tf_l.margin_left = tf_l.margin_right = Inches(0.30)
    tf_l.margin_top = Inches(0.20)
    p = tf_l.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = "WHAT PLATFORMS BELIEVE\n"
    r.font.bold = True
    r.font.size = Pt(13)
    r.font.color.rgb = MUTED
    r.font.name = MONO

    p2 = tf_l.add_paragraph()
    p2.space_before = Pt(4)
    r2 = p2.add_run()
    r2.text = "“Storytelling is the only lever a platform can coach.”\n"
    r2.font.bold = True
    r2.font.size = Pt(15.5)
    r2.font.color.rgb = INK
    r2.font.name = DISPLAY

    p3 = tf_l.add_paragraph()
    p3.space_before = Pt(4)
    r3 = p3.add_run()
    r3.text = "• Loan amount, sector, and country are fixed at listing.\n• Conventional marketing advice suggests adding urgency, mentioning family, or perfecting copy to speed up conversion.\n• Naive regressions seem to back this up (p < 0.001)."
    r3.font.size = Pt(12.5)
    r3.font.color.rgb = INK
    r3.font.name = BODY

    c_right = rect(sl2, Inches(6.80), Inches(2.05), Inches(5.75), Inches(3.30), WHITE, CARD_BORDER, rounded=True)
    tf_r = c_right.text_frame
    tf_r.margin_left = tf_r.margin_right = Inches(0.30)
    tf_r.margin_top = Inches(0.20)
    p = tf_r.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = "WHAT 1.45M LOANS REVEAL\n"
    r.font.bold = True
    r.font.size = Pt(13)
    r.font.color.rgb = BLUE
    r.font.name = MONO

    p2 = tf_r.add_paragraph()
    p2.space_before = Pt(4)
    r2 = p2.add_run()
    r2.text = "“Structural loan factors beat storytelling by ~10×.”\n"
    r2.font.bold = True
    r2.font.size = Pt(15.5)
    r2.font.color.rgb = INK
    r2.font.name = DISPLAY

    p3 = tf_r.add_paragraph()
    p3.space_before = Pt(4)
    r3 = p3.add_run()
    r3.text = "• Urgency dissolves under country-clustering (p ≈ 0.49).\n• Family framing rests on a 2-country screen illusion (t(1)=12.7).\n• Loan size, terms, sector, and gender dwarf narrative choices.\n• 96.4% of loans pre-disbursed: partner capital waits, not borrower."
    r3.font.size = Pt(12.5)
    r3.font.color.rgb = INK
    r3.font.name = BODY

    # Bottom Callout: Strategic Pivot Banner
    c_bot = rect(sl2, Inches(0.75), Inches(5.50), Inches(11.8), Inches(1.35), PANEL, line=AMBER, rounded=True)
    tf_b = c_bot.text_frame
    tf_b.margin_left = tf_b.margin_right = Inches(0.30)
    tf_b.margin_top = Inches(0.18)
    p = tf_b.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = "THE STRATEGIC TAKEAWAY FOR KIVA\n"
    r.font.bold = True
    r.font.size = Pt(12)
    r.font.color.rgb = INK
    r.font.name = MONO
    p2 = tf_b.add_paragraph()
    p2.space_before = Pt(4)
    r2 = p2.add_run()
    r2.text = "Do not waste product and marketing resources shipping generic copywriting nudges. Shift platform investment toward structural bottlenecks, partner liquidity cycles, and country-stratified A/B experiments."
    r2.font.size = Pt(13.5)
    r2.font.color.rgb = INK
    r2.font.name = BODY
    sl2.notes_slide.notes_text_frame.text = (
        "(Sophia, ~55s) Why are we here? Kiva is built on the belief that loan copy is the coachable lever. "
        "Loan size, country, sector — fixed at listing. So the platform wants to coach borrowers to tell better stories. "
        "We tested that premise across 1.45 million loans. Our verdict right up front: in this data, the story barely registers; "
        "the structure carries the signal. Storytelling advice does not survive rigorous testing. "
        "Today, we show you why that happens, and where Kiva should actually invest its product energy.\n\n[Sources] EDA §1–§5, modeling §7."
    )

    # =========================================================================
    # SLIDE 3: PROJECT ARCHITECTURE & EXECUTIVE TABLE OF CONTENTS (OVERVIEW)
    # =========================================================================
    sl3 = prs.slides.add_slide(blank_layout)
    bg(sl3, PAPER)
    start_y = add_chrome(sl3, "TABLE OF CONTENTS · PROJECT BLUEPRINT", "OVERVIEW", "How the 1.45M loan investigation is structured")

    col_w = Inches(2.78)
    col_gap = Inches(0.237)
    left_margin = Inches(0.75)
    top_cards = Inches(2.05)
    card_h = Inches(3.85)

    sections = [
        {
            "tag": "ACT I · CONTEXT",
            "title": "The Operating Reality",
            "slides": "Slides 4–5",
            "sub": "Why narrative advice is pitched, and what really happens on the ground.",
            "points": [
                ("The Platform Dilemma", "Text is the only unsealed lever at listing; platforms want to coach it."),
                ("Market Slowdown", "Same-day funding collapsed from 46% to 30% post-pandemic."),
                ("Capital Reality", "96.4% pre-disbursed; partner working capital waits, not borrowers.")
            ]
        },
        {
            "tag": "ACT II · INFERENCE",
            "title": "Empirical Stress-Test",
            "slides": "Slides 6–9",
            "sub": "Testing narrative claims against 1.45M loans with econometric rigor.",
            "points": [
                ("Methodological Screen", "64 of 120 coefficients collapse under country-clustering."),
                ("Structural Dominance", "Amount, terms, and sector beat storytelling by ~10×."),
                ("Narrative Scrutiny", "Urgency dissolves (p ≈ 0.49); family rests on 2-country screen."),
                ("Topic Modeling", "Topics track loan purpose (water vs farming; 9× swing).")
            ]
        },
        {
            "tag": "ACT III · STRATEGY",
            "title": "The Strategic Playbook",
            "slides": "Slides 10–12",
            "sub": "High-ROI platform decisions, borrower realism, and epistemic bounds.",
            "points": [
                ("4-Quadrant Playbook", "Kill generic tips, A/B test family framing, fix structural lag."),
                ("Borrower Realism", "Set cash-flow expectations; do NOT game gender or story."),
                ("Scientific Bounds", "Observational associations, completed-loans survival truncation.")
            ]
        },
        {
            "tag": "APPENDIX · AUDITS",
            "title": "Methodological Audits",
            "slides": "Slides 14–17",
            "sub": "Full numerical proofs and statistical architecture for defense.",
            "points": [
                ("Two-Country Problem", "The conservative t(1) = 12.7 heuristic screen in full."),
                ("Predictive vs Causal", "Why SHAP importance cannot certify policy rules."),
                ("The ~10× Comparison", "Decile monotonicities and correlation breakdown."),
                ("24h Early Warning", "LightGBM classifier architecture (ROC AUC 0.8997).")
            ]
        }
    ]

    for idx, sec in enumerate(sections):
        card_x = left_margin + idx * (col_w + col_gap)
        card = rect(sl3, card_x, top_cards, col_w, card_h, WHITE, CARD_BORDER, rounded=True)
        tf_c = card.text_frame
        tf_c.margin_left = tf_c.margin_right = Inches(0.20)
        tf_c.margin_top = Inches(0.18)

        # Header tag
        p0 = tf_c.paragraphs[0]
        p0.alignment = PP_ALIGN.LEFT
        r_tag = p0.add_run()
        r_tag.text = sec["tag"]
        r_tag.font.bold = True
        r_tag.font.size = Pt(9.5)
        r_tag.font.color.rgb = BLUE
        r_tag.font.name = MONO

        # Slide range
        p_sl = tf_c.add_paragraph()
        p_sl.space_before = Pt(1)
        p_sl.alignment = PP_ALIGN.LEFT
        r_sl = p_sl.add_run()
        r_sl.text = sec["slides"].upper()
        r_sl.font.bold = True
        r_sl.font.size = Pt(8.5)
        r_sl.font.color.rgb = MUTED
        r_sl.font.name = MONO

        # Title
        p_t = tf_c.add_paragraph()
        p_t.space_before = Pt(3)
        p_t.alignment = PP_ALIGN.LEFT
        r_t = p_t.add_run()
        r_t.text = sec["title"]
        r_t.font.bold = True
        r_t.font.size = Pt(13.5)
        r_t.font.color.rgb = INK
        r_t.font.name = DISPLAY

        # Subtitle
        p_sub = tf_c.add_paragraph()
        p_sub.space_before = Pt(2)
        p_sub.alignment = PP_ALIGN.LEFT
        r_sub = p_sub.add_run()
        r_sub.text = sec["sub"]
        r_sub.font.italic = True
        r_sub.font.size = Pt(9.5)
        r_sub.font.color.rgb = MUTED
        r_sub.font.name = BODY

        # Points
        for p_idx, (head, desc) in enumerate(sec["points"]):
            p_pt = tf_c.add_paragraph()
            p_pt.space_before = Pt(6)
            p_pt.alignment = PP_ALIGN.LEFT

            r_sq = p_pt.add_run()
            r_sq.text = "▪ "
            r_sq.font.color.rgb = AMBER
            r_sq.font.bold = True
            r_sq.font.size = Pt(10)

            r_h = p_pt.add_run()
            r_h.text = f"{head}: "
            r_h.font.bold = True
            r_h.font.size = Pt(10)
            r_h.font.color.rgb = INK
            r_h.font.name = BODY

            r_d = p_pt.add_run()
            r_d.text = desc
            r_d.font.size = Pt(9.5)
            r_d.font.color.rgb = INK
            r_d.font.name = BODY

    # Bottom Methodology Stack Banner
    b_bot = rect(sl3, Inches(0.75), Inches(6.02), Inches(11.833), Inches(0.92), PANEL, line=AMBER, rounded=True)
    tf_bb = b_bot.text_frame
    tf_bb.margin_left = tf_bb.margin_right = Inches(0.25)
    tf_bb.margin_top = Inches(0.12)

    p_bb0 = tf_bb.paragraphs[0]
    p_bb0.alignment = PP_ALIGN.LEFT
    r_bb0 = p_bb0.add_run()
    r_bb0.text = "PORTFOLIO METHODOLOGY & REPRODUCIBILITY STACK · 1,453,846 REAL LOANS (2016–2025)\n"
    r_bb0.font.bold = True
    r_bb0.font.size = Pt(10)
    r_bb0.font.color.rgb = INK
    r_bb0.font.name = MONO

    p_bb1 = tf_bb.add_paragraph()
    p_bb1.space_before = Pt(2)
    p_bb1.alignment = PP_ALIGN.LEFT
    r_bb1 = p_bb1.add_run()
    r_bb1.text = "Econometric OLS Duration Modeling · Binomial GLM · Country-Clustered Standard Errors · Conservative Few-Cluster t(1)=12.7 Screen · NMF Topic Extraction (8 Components) · LightGBM Predictive Benchmark (Strict Chronological Split, Zero Future Leakage)"
    r_bb1.font.size = Pt(10)
    r_bb1.font.color.rgb = INK
    r_bb1.font.name = BODY

    sl3.notes_slide.notes_text_frame.text = (
        "(Portfolio Blueprint) This executive architecture maps the full 1.45 million loan investigation. "
        "Readers can navigate the sequence across three core phases: from the initial platform dilemma (Act I) "
        "through our econometric stress-testing and statistical falsification (Act II), into Kiva's high-ROI platform strategy (Act III), "
        "supported by complete methodological proofs in the Technical Appendix.\n\n"
        "[Navigation] Slides 4–5 (Act I), Slides 6–9 (Act II), Slides 10–12 (Act III), Slides 14–17 (Technical Appendix)."
    )

    # =========================================================================
    # SLIDE 4: MOTIVATION (Act I · Step 02)
    # =========================================================================
    sl4 = prs.slides.add_slide(blank_layout)
    bg(sl4, PAPER)
    start_y = add_chrome(sl4, "ACT I · OPERATING REALITY", 2, "Why platforms coach story: the only lever unsealed at listing")

    card1 = rect(sl4, Inches(0.75), Inches(1.90), Inches(11.8), Inches(1.40), WHITE, CARD_BORDER, rounded=True)
    tf1 = card1.text_frame
    tf1.margin_left = tf1.margin_right = Inches(0.35)
    tf1.margin_top = Inches(0.22)
    p = tf1.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = "1. THE NARRATIVE QUESTION\n"
    r.font.bold = True
    r.font.size = Pt(14)
    r.font.color.rgb = BLUE
    r.font.name = DISPLAY
    r2 = p.add_run()
    r2.text = "When a loan's story leans on family, competence, or urgency, does it get funded faster?"
    r2.font.size = Pt(16)
    r2.font.color.rgb = INK
    r2.font.name = BODY

    card2 = rect(sl4, Inches(0.75), Inches(3.50), Inches(11.8), Inches(1.40), WHITE, CARD_BORDER, rounded=True)
    tf2 = card2.text_frame
    tf2.margin_left = tf2.margin_right = Inches(0.35)
    tf2.margin_top = Inches(0.22)
    p = tf2.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = "2. THE MODERATION QUESTION\n"
    r.font.bold = True
    r.font.size = Pt(14)
    r.font.color.rgb = BLUE
    r.font.name = DISPLAY
    r2 = p.add_run()
    r2.text = "Does the result shift by WHO the borrower is (gender, geography) and WHERE & WHEN they posted?"
    r2.font.size = Pt(16)
    r2.font.color.rgb = INK
    r2.font.name = BODY

    card3 = rect(sl4, Inches(0.75), Inches(5.10), Inches(11.8), Inches(1.65), PANEL, line=AMBER, rounded=True)
    tf3 = card3.text_frame
    tf3.margin_left = tf3.margin_right = Inches(0.35)
    tf3.margin_top = Inches(0.22)
    p = tf3.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = "WHY IT MATTERS TO PLATFORM MARKETING\n"
    r.font.bold = True
    r.font.size = Pt(13)
    r.font.color.rgb = INK
    r.font.name = DISPLAY
    p2 = tf3.add_paragraph()
    p2.alignment = PP_ALIGN.LEFT
    p2.text = "Loan story framing is the one lever a platform can actually coach. Loan size, sector, country, and partner terms are fixed at listing — narrative choices are the only active conversion lever."
    p2.font.size = Pt(14.5)
    p2.font.color.rgb = INK
    p2.font.name = BODY
    p2.space_before = Pt(4)
    sl4.notes_slide.notes_text_frame.text = (
        "(Sophia, ~50s) Why should a marketing audience care? Because on Kiva, the lender is the customer "
        "and the loan page is the product page. Loan size, sector, geography — fixed at listing. "
        "The story is the one element a platform can coach, test, and optimise. So: when a story leans on "
        "family, competence, or urgency, does the loan fund faster? And does that depend on who's asking, "
        "and when? That's a testable claim — so we tested it, hard.\n\n[Sources] EDA notebook §1–§3."
    )

    # =========================================================================
    # SLIDE 5: THE MARKET & PARTNER CAPITAL (Act I · Step 03)
    # =========================================================================
    sl5 = prs.slides.add_slide(blank_layout)
    bg(sl5, PAPER)
    start_y = add_chrome(sl5, "ACT I · OPERATING REALITY", 3, "A slower market is the operating reality — and it is partner capital that waits.")
    add_chart_exhibit(sl5, 5, chart_top=2.0)

    tf = box(sl5, Inches(0.75), Inches(2.05), Inches(7.1), Inches(0.70))
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = "46.0% → 30.3% → 30.0%  "
    r.font.size = Pt(26)
    r.font.bold = True
    r.font.color.rgb = INK
    r.font.name = DISPLAY
    r2 = p.add_run()
    r2.text = "funded within 24 hours"
    r2.font.size = Pt(14)
    r2.font.color.rgb = MUTED
    r2.font.name = BODY

    tf = box(sl5, Inches(0.75), Inches(2.80), Inches(7.1), Inches(1.85))
    b4 = [
        "Pre-pandemic, almost half of all loans funded within a day.",
        "Since 2020: under a third — and four years on, still not recovered (-0.3 points recovery).",
        "589,823 loans before vs 565,474 after — not a thin sample, and the slowdown persists to date."
    ]
    for j, item in enumerate(b4):
        p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
        r1 = p.add_run()
        r1.text = "▪  "
        r1.font.color.rgb = AMBER
        r1.font.bold = True
        r2 = p.add_run()
        r2.text = item
        r2.font.size = Pt(13)
        r2.font.color.rgb = INK
        r2.font.name = BODY
        p.space_after = Pt(4)

    timeline_card = rect(sl5, Inches(0.75), Inches(4.75), Inches(7.1), Inches(1.95), PANEL, CARD_BORDER, rounded=True)
    tf_tc = timeline_card.text_frame
    tf_tc.margin_left = tf_tc.margin_right = Inches(0.25)
    tf_tc.margin_top = Inches(0.18)
    p_hdr = tf_tc.paragraphs[0]
    p_hdr.alignment = PP_ALIGN.LEFT
    r = p_hdr.add_run()
    r.text = "THE OPERATIONAL REALITY · 96.4% PRE-DISBURSED\n"
    r.font.size = Pt(11.5)
    r.font.bold = True
    r.font.color.rgb = BLUE
    r.font.name = MONO

    p_flow = tf_tc.add_paragraph()
    p_flow.alignment = PP_ALIGN.LEFT
    p_flow.space_before = Pt(2)
    r_f = p_flow.add_run()
    r_f.text = "Day 0: Cash Disbursed  ➔  Day 24: Kiva Listing  ➔  Day 27+: Reimbursed\n"
    r_f.font.size = Pt(12)
    r_f.font.bold = True
    r_f.font.color.rgb = INK
    r_f.font.name = DISPLAY

    r_desc = p_flow.add_run()
    r_desc.text = "Borrowers do NOT wait for crowdfunding — field partners disburse upfront. A slower market means field partner working capital waits longer to replenish."
    r_desc.font.size = Pt(11.5)
    r_desc.font.color.rgb = INK
    r_desc.font.name = BODY
    sl5.notes_slide.notes_text_frame.text = (
        "(Sophia, ~65s) Start with the market, because every other number lives inside it. "
        "Before the pandemic, 46.0% of loans funded within 24 hours — nearly half converting same-day. "
        "Since 2020 it's been under a third — and through 2025, the 'recovery' is minus 0.3 points. "
        "Partner capital now waits longer, not the borrower, because 96% of loans are already disbursed "
        "before the page goes live. With over half a million loans on each side of that divide, "
        "this isn't noise: it's a structurally slower, more selective marketplace.\n\n[Sources] EDA notebook §4."
    )

    # =========================================================================
    # SLIDE 6: METHODOLOGY (Act II · Step 04)
    # =========================================================================
    sl6 = prs.slides.add_slide(blank_layout)
    bg(sl6, PAPER)
    start_y = add_chrome(sl6, "ACT II · THE STRESS-TEST", 4, "Why big data lies without clustering: how we stress-tested our claims")
    add_chart_exhibit(sl6, 6, chart_top=2.0)

    tf = box(sl6, Inches(0.75), Inches(2.05), Inches(7.1), Inches(0.75))
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = "64 of 120  "
    r.font.size = Pt(30)
    r.font.bold = True
    r.font.color.rgb = INK
    r.font.name = DISPLAY
    r2 = p.add_run()
    r2.text = "significant coefficients lost significance"
    r2.font.size = Pt(14)
    r2.font.color.rgb = MUTED
    r2.font.name = BODY

    tf = box(sl6, Inches(0.75), Inches(2.95), Inches(7.1), Inches(3.9))
    bullets_s5 = [
        "Chronological Holdout: Trained strictly on loans up to 2023; 278,887 loans from 2024–2025 sealed until evaluation. Zero future leakage.",
        "Country-Clustered Standard Errors: Standard errors clustered across 80+ countries to remove artificial significance inflation from massive sample sizes.",
        "Stricter Few-Cluster Screen: Where regional claims rested on only 1–2 countries, required the conservative t(1) critical value of 12.7 (not 1.96).",
        "Role of Machine Learning: SHAP importance used as complementary predictive validation only; cannot certify causal signs or policy rules."
    ]
    for j, item in enumerate(bullets_s5):
        p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
        r1 = p.add_run()
        r1.text = "▪  "
        r1.font.color.rgb = AMBER
        r1.font.size = Pt(13)
        r1.font.bold = True
        r2 = p.add_run()
        r2.text = item
        r2.font.size = Pt(13.5)
        r2.font.color.rgb = INK
        r2.font.name = BODY
        p.space_after = Pt(8)
        p.line_spacing = 1.15
    sl6.notes_slide.notes_text_frame.text = (
        "(Sophia, ~60s) Two tests separated what is real from what is statistical noise. "
        "First, chronological holdout: 278,887 loans from 2024–2025 stayed sealed. "
        "Second, country-clustered standard errors: in a 1.45 million row dataset, standard errors shrink "
        "mechanically, making noise look 'highly significant.' Across both explanatory models, 64 of 120 "
        "significant coefficients did not survive country-clustering. That is the point of the method.\n\n[Sources] analysis_summary.json"
    )

    # =========================================================================
    # SLIDE 7: STRUCTURAL DOMINANCE (Act II · Step 05)
    # =========================================================================
    sl7 = prs.slides.add_slide(blank_layout)
    bg(sl7, PAPER)
    start_y = add_chrome(sl7, "ACT II · THE STRESS-TEST", 5, "Structural loan factors beat storytelling by an order of magnitude")
    add_chart_exhibit(sl7, 7, chart_top=2.0)

    tf = box(sl7, Inches(0.75), Inches(2.05), Inches(7.1), Inches(0.85))
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = "2.3 vs 7.7 days  "
    r.font.size = Pt(30)
    r.font.bold = True
    r.font.color.rgb = INK
    r.font.name = DISPLAY
    r2 = p.add_run()
    r2.text = "median speed — female vs male loans"
    r2.font.size = Pt(14)
    r2.font.color.rgb = MUTED
    r2.font.name = BODY

    tf = box(sl7, Inches(0.75), Inches(3.05), Inches(7.1), Inches(3.8))
    b6 = [
        "Loan amount + repayment terms: linked to funding speed ~10× more strongly than any single narrative choice. Bigger ask, longer on the platform.",
        "Sector alone spans well over an order of magnitude in speed (0.9–12.1 days); country gaps are wider still — 0.2 to 20.5 days.",
        "Loans posted by women fund in a median 2.3 days; by men, 7.7. None of this is causal — but it dwarfs anything the words do.",
        "Programme label (whySpecial) spans 0.2 to 30.9 days across 141 well-populated levels — institutional design dominates."
    ]
    for j, item in enumerate(b6):
        p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
        r1 = p.add_run()
        r1.text = "▪  "
        r1.font.color.rgb = AMBER
        r1.font.bold = True
        r2 = p.add_run()
        r2.text = item
        r2.font.size = Pt(13)
        r2.font.color.rgb = INK
        r2.font.name = BODY
        p.space_after = Pt(8)
        p.line_spacing = 1.15
    sl7.notes_slide.notes_text_frame.text = (
        "(Sophia, ~65s) And what drives it is structure. Loan amount and repayment terms correlate "
        "with funding speed roughly ten times more strongly than any narrative signal. Bigger ask, "
        "longer on the platform. Sector alone spans an order of magnitude — sanitation in under a day, "
        "clothing takes twelve. And loans posted by women fund in a median of 2.3 days, by men 7.7 — "
        "three times longer. None of this is causal, but it dwarfs anything the words do. "
        "Tuan will now take you through what happened when we put storytelling to the test.\n\n[Sources] EDA notebook §5, §9."
    )

    # =========================================================================
    # SLIDE 8: THE NARRATIVE SCRUTINY (Act II · Step 06)
    # =========================================================================
    sl8 = prs.slides.add_slide(blank_layout)
    bg(sl8, PAPER)
    start_y = add_chrome(sl8, "ACT II · THE STRESS-TEST", 6, "Storytelling coaching: no robust evidence it moves the needle.")
    add_chart_exhibit(sl8, 8, chart_top=2.0)

    sub_card = rect(sl8, Inches(0.75), Inches(2.05), Inches(7.1), Inches(0.70), AMBER, rounded=True)
    tf = sub_card.text_frame
    tf.margin_left = tf.margin_right = Inches(0.25)
    tf.margin_top = Inches(0.12)
    p = tf.paragraphs[0]
    p.text = "No narrative result is robust enough to support a writing recommendation"
    p.font.size = Pt(13.5)
    p.font.bold = True
    p.font.color.rgb = INK
    p.font.name = DISPLAY

    tf = box(sl8, Inches(0.75), Inches(2.88), Inches(7.1), Inches(4.0))
    b7 = [
        "Urgency: looked universal (p<0.001) — collapses under country clustering (p≈0.49). Not recommended.",
        "Family: corrected within-region tests in Middle East (Palestine+Yemen) & Central America (Honduras+Nicaragua) same direction in every fit — but 2 countries each; few-cluster t(1) screen bar is 12.7, not 1.96: p≈0.06–0.12. A hypothesis, not a finding.",
        "Sentiment: positive tone <-> slower funding, but significance flips between specifications — genuinely open.",
        "SHAP: no family / agency / urgency feature in the model's top 15 — complementary evidence."
    ]
    for j, item in enumerate(b7):
        p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
        r1 = p.add_run()
        r1.text = "▪  "
        r1.font.color.rgb = AMBER
        r1.font.bold = True
        r2 = p.add_run()
        r2.text = item
        r2.font.size = Pt(13)
        r2.font.color.rgb = INK
        r2.font.name = BODY
        p.space_after = Pt(8)
        p.line_spacing = 1.15
    sl8.notes_slide.notes_text_frame.text = (
        "(Tuan, ~1m50s) Thanks, Sophia. So: does the story matter? Our honest answer: no narrative result "
        "is robust enough across specifications to support a recommendation. Urgency language looked like a "
        "universal win — significant at p below 0.001. Cluster by country, and it collapses to 0.49. Gone. "
        "Family framing — Middle East and Central America do show faster funding in every fit we ran. "
        "But each rests on exactly two countries, and against a deliberately harsh few-cluster screen — "
        "critical value 12.7, not 1.96 — neither is significant: p between 0.06 and 0.12. "
        "So we report a hypothesis worth testing, not an established rule.\n\n[Sources] modeling notebook §7.2"
    )

    # =========================================================================
    # SLIDE 9: TOPICS ENCODE CAUSE (Act II · Step 07)
    # =========================================================================
    sl9 = prs.slides.add_slide(blank_layout)
    bg(sl9, PAPER)
    start_y = add_chrome(sl9, "ACT II · THE STRESS-TEST", 7, "The themes come down to loan purpose, not persuasion.")
    add_chart_exhibit(sl9, 9, chart_top=2.0)

    tf = box(sl9, Inches(0.75), Inches(2.05), Inches(7.1), Inches(0.85))
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = "1.5 → 13.5 days  "
    r.font.size = Pt(30)
    r.font.bold = True
    r.font.color.rgb = INK
    r.font.name = DISPLAY
    r2 = p.add_run()
    r2.text = "mean speed across topics — ninefold swing"
    r2.font.size = Pt(14)
    r2.font.color.rgb = MUTED
    r2.font.name = BODY

    tf = box(sl9, Inches(0.75), Inches(3.00), Inches(7.1), Inches(3.8))
    b8 = [
        "Topic modeling on descriptions (TF-IDF + NMF, 8 topics — not keyword counts) surfaces coherent themes: sanitation, clean water, pig raising, family business, smallholder farming.",
        "The largest single gap anywhere in the analysis: clean water funds in under 2 days; group farming loans take ~2 weeks.",
        "A theme mostly encodes what the loan is FOR. Lenders prioritize clean water cause, not because the borrower wrote better prose. Structure again, not persuasion."
    ]
    for j, item in enumerate(b8):
        p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
        r1 = p.add_run()
        r1.text = "▪  "
        r1.font.color.rgb = AMBER
        r1.font.bold = True
        r2 = p.add_run()
        r2.text = item
        r2.font.size = Pt(13.5)
        r2.font.color.rgb = INK
        r2.font.name = BODY
        p.space_after = Pt(10)
        p.line_spacing = 1.15
    sl9.notes_slide.notes_text_frame.text = (
        "(Tuan, ~50s) Topic modelling finds eight coherent story themes, and mean funding speed swings "
        "ninefold across them — sanitation and clean-water in under two days, group farming loans take ~2 weeks. "
        "But notice what a theme mostly encodes: what the loan is FOR. Structure again — not persuasion — "
        "and it's why the structural review should cover what loans are FOR, not just which sector they sit in.\n\n[Sources] EDA notebook §8"
    )

    # =========================================================================
    # SLIDE 10: PLATFORM STRATEGY · KIVA (Act III · Step 08)
    # =========================================================================
    sl10 = prs.slides.add_slide(blank_layout)
    bg(sl10, PAPER)
    add_chrome(sl10, "ACT III · STRATEGIC PLAYBOOK", 8, "What this means in practice for the Kiva team: a 4-action playbook")

    c1 = rect(sl10, Inches(0.75), Inches(1.95), Inches(5.75), Inches(2.15), WHITE, CARD_BORDER, rounded=True)
    tf1 = c1.text_frame
    tf1.margin_left = tf1.margin_right = Inches(0.30)
    tf1.margin_top = Inches(0.20)
    p = tf1.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = "DON'T SHIP  ·  Generic Writing Tips\n"
    r.font.bold = True
    r.font.size = Pt(14)
    r.font.color.rgb = RGBColor(0xC5, 0x30, 0x30)
    r.font.name = DISPLAY
    r_b = p.add_run()
    r_b.text = "A platform-wide 'add urgency' nudge would be built on unclustered statistical noise (p ≈ 0.49). Withhold writing coaching to save engineering resources and avoid confusing borrowers."
    r_b.font.size = Pt(12.5)
    r_b.font.color.rgb = INK
    r_b.font.name = BODY

    c2 = rect(sl10, Inches(6.80), Inches(1.95), Inches(5.75), Inches(2.15), WHITE, CARD_BORDER, rounded=True)
    tf2 = c2.text_frame
    tf2.margin_left = tf2.margin_right = Inches(0.30)
    tf2.margin_top = Inches(0.20)
    p = tf2.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = "A/B TEST  ·  Targeted Family Framing\n"
    r.font.bold = True
    r.font.size = Pt(14)
    r.font.color.rgb = BLUE
    r.font.name = DISPLAY
    r_b = p.add_run()
    r_b.text = "Run a country-stratified A/B test strictly in the 4 candidate markets: Palestine, Yemen, Honduras, Nicaragua. Randomize prompts at listing; evaluate causal funding speed country-by-country."
    r_b.font.size = Pt(12.5)
    r_b.font.color.rgb = INK
    r_b.font.name = BODY

    c3 = rect(sl10, Inches(0.75), Inches(4.30), Inches(5.75), Inches(2.15), WHITE, CARD_BORDER, rounded=True)
    tf3 = c3.text_frame
    tf3.margin_left = tf3.margin_right = Inches(0.30)
    tf3.margin_top = Inches(0.20)
    p = tf3.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = "REVIEW STRUCTURE  ·  The ~10× Levers\n"
    r.font.bold = True
    r.font.size = Pt(14)
    r.font.color.rgb = INK
    r.font.name = DISPLAY
    r_b = p.add_run()
    r_b.text = "Review structural friction: Programme label (whySpecial, 0.2–30.9 days), sector, region, and gender. These structural factors drive ten times the variance of any wording effect."
    r_b.font.size = Pt(12.5)
    r_b.font.color.rgb = INK
    r_b.font.name = BODY

    c4 = rect(sl10, Inches(6.80), Inches(4.30), Inches(5.75), Inches(2.15), WHITE, CARD_BORDER, rounded=True)
    tf4 = c4.text_frame
    tf4.margin_left = tf4.margin_right = Inches(0.30)
    tf4.margin_top = Inches(0.20)
    p = tf4.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = "PROTOTYPE & AUDIT  ·  24h Classifier\n"
    r.font.bold = True
    r.font.size = Pt(14)
    r.font.color.rgb = BLUE
    r.font.name = DISPLAY
    r_b = p.add_run()
    r_b.text = "The 24h LightGBM classifier achieves AUC ≈ 0.90 (accuracy 0.840) among funded loans. Before operational deployment, retrain on all listings (including expired and withdrawn)."
    r_b.font.size = Pt(12.5)
    r_b.font.color.rgb = INK
    r_b.font.name = BODY

    bot_b = rect(sl10, Inches(0.75), Inches(6.58), Inches(11.8), Inches(0.42), PANEL, CARD_BORDER, rounded=True)
    tf_b = bot_b.text_frame
    tf_b.margin_top = Inches(0.08)
    p_b = tf_b.paragraphs[0]
    p_b.text = "⚡ OPERATIONAL REALITY: 96% of loans are disbursed before listing — funding speed is the partner's capital cycle, not borrower waiting."
    p_b.font.size = Pt(10.5)
    p_b.font.bold = True
    p_b.font.color.rgb = INK
    p_b.font.name = MONO
    p_b.alignment = PP_ALIGN.CENTER
    sl10.notes_slide.notes_text_frame.text = (
        "(Tuan, ~1m25s) Three moves for the platform. One: don't ship writing tips — a firm don't, "
        "because a robust null is what we found. Two: run the country-stratified A/B test in Palestine, "
        "Yemen, Honduras, Nicaragua — test before you ship. Three: review the structural gaps — programme, "
        "sector, region, and gender. And the classifier stays a prototype among funded loans until "
        "retrained on all listings including expired ones.\n\n[Sources] analysis_summary.json"
    )

    # =========================================================================
    # SLIDE 11: BORROWER EXPECTATIONS (Act III · Step 08)
    # =========================================================================
    sl11 = prs.slides.add_slide(blank_layout)
    bg(sl11, PAPER)
    start_y = add_chrome(sl11, "ACT III · STRATEGIC PLAYBOOK", 8, "What to expect when listing: setting expectations, not gaming levers")

    banner = rect(sl11, Inches(0.75), Inches(2.05), Inches(11.8), Inches(0.55), AMBER, rounded=True)
    tf_ban = banner.text_frame
    tf_ban.margin_left = tf_ban.margin_right = Inches(0.25)
    tf_ban.margin_top = Inches(0.12)
    p_ban = tf_ban.paragraphs[0]
    p_ban.text = "FOR BORROWERS & FIELD PARTNERS: WHAT TO EXPECT — NOT WHAT TO GAME"
    p_ban.font.size = Pt(13)
    p_ban.font.bold = True
    p_ban.font.color.rgb = INK
    p_ban.font.name = DISPLAY
    p_ban.alignment = PP_ALIGN.CENTER

    rows_data = [
        ("Profile & Gender",
         "Loans posted by women fund in a median 2.3 days vs 7.7 male-posted.",
         "A gap for Kiva to investigate, not a lever for borrowers. DO NOT manipulate who represents the household."),
        ("Loan Size & Terms",
         "The two strongest speed predictors (linked ~10x more strongly than words).",
         "Amounts are partner-set against real business capital need. Plan cash flow around them; DO NOT shrink the ask."),
        ("Sector & Cause",
         "Speed varies ~13x by sector (0.9 to 12.1 days; water <2d vs farming ~2wks).",
         "Category is dictated by loan purpose. Set realistic expectations by sector; DO NOT misclassify category to chase speed.")
    ]
    for idx, (factor, reality, rule) in enumerate(rows_data):
        y_pos = Inches(2.75 + idx * 1.30)
        card = rect(sl11, Inches(0.75), y_pos, Inches(11.8), Inches(1.18), WHITE, CARD_BORDER, rounded=True)
        tf_c = card.text_frame
        tf_c.margin_left = tf_c.margin_right = Inches(0.30)
        tf_c.margin_top = Inches(0.14)
        p = tf_c.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        r1 = p.add_run()
        r1.text = factor.upper() + "  ·  "
        r1.font.bold = True
        r1.font.size = Pt(13.5)
        r1.font.color.rgb = BLUE
        r1.font.name = DISPLAY

        r2 = p.add_run()
        r2.text = reality + "\n"
        r2.font.size = Pt(13)
        r2.font.color.rgb = INK
        r2.font.name = BODY

        r3 = p.add_run()
        r3.text = rule
        r3.font.size = Pt(12.5)
        r3.font.bold = True
        r3.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
        r3.font.name = BODY

    tf_fn = box(sl11, Inches(0.75), Inches(6.75), Inches(11.8), Inches(0.35))
    p_fn = tf_fn.paragraphs[0]
    p_fn.text = "Note: A bigger ask sits on the platform longer (~2 vs ~19 days). Because 96% of loans are pre-disbursed, this affects partner liquidity cycles, not borrower survival."
    p_fn.font.size = Pt(10.5)
    p_fn.font.color.rgb = MUTED
    p_fn.font.name = BODY
    sl11.notes_slide.notes_text_frame.text = (
        "(Tuan, ~40s) And for borrowers — expectations, not tactics. We are not advising anyone "
        "to game demographic fields, switch sectors, or shrink their loan request. "
        "The timing story belongs to field partners: a bigger ask sits on the platform longer, "
        "and since 96% of these loans are already disbursed before the page goes live, that is a "
        "partner capital-cycle fact, not a borrower's waiting time.\n\n[Sources] EDA notebook §4, §5, §7."
    )

    # =========================================================================
    # SLIDE 12: LIMITS & RIGOR (Act III · Step 08)
    # =========================================================================
    sl12 = prs.slides.add_slide(blank_layout)
    bg(sl12, PAPER)
    start_y = add_chrome(sl12, "ACT III · STRATEGIC PLAYBOOK", 8, "What this can't tell us: three boundaries on the evidence")

    limits_data = [
        ("01 · ASSOCIATION, NEVER CAUSATION",
         "No borrower was randomly assigned a writing style.",
         "All results are observational associations. Narrative features correlate with geographic, economic, and institutional realities that cannot be causally attributed to the borrower's text alone."),
        ("02 · COMPLETED FUNDRAISES ONLY",
         "Measures how fast a FUNDED loan funds — not whether it gets funded at all.",
         "The dataset contains completed fundraisers (1,452,203 funded loans). Expired or withdrawn campaigns never enter the platform data, creating survival truncation."),
        ("03 · TRANSPARENT LEXICAL BOUNDS",
         "Framing measured with transparent, simple rules — not every nuance of persuasion.",
         "Lexicon word-rate frequencies and sentiment compound scores capture broad stylistic patterns, but cannot capture deep storytelling craft, emotional subtlety, or cultural context.")
    ]
    for idx, (tag, headline, desc) in enumerate(limits_data):
        y_pos = Inches(1.95 + idx * 1.65)
        card = rect(sl12, Inches(0.75), y_pos, Inches(11.8), Inches(1.45), WHITE, CARD_BORDER, rounded=True)
        tf_c = card.text_frame
        tf_c.margin_left = tf_c.margin_right = Inches(0.35)
        tf_c.margin_top = Inches(0.18)
        p = tf_c.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        r1 = p.add_run()
        r1.text = tag + "\n"
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = BLUE
        r1.font.name = MONO

        r2 = p.add_run()
        r2.text = headline + "  "
        r2.font.bold = True
        r2.font.size = Pt(14)
        r2.font.color.rgb = INK
        r2.font.name = DISPLAY

        r3 = p.add_run()
        r3.text = desc
        r3.font.size = Pt(12.5)
        r3.font.color.rgb = MUTED
        r3.font.name = BODY
    sl12.notes_slide.notes_text_frame.text = (
        "(Tuan, ~35s) Three honest limits. Association, never causation — nobody randomly assigned writing styles. "
        "We measure how fast funded loans fund — not whether a loan funds at all. And our framing measures are "
        "transparent, simple rules — not every nuance of persuasion. We'd rather you know exactly what this "
        "can and cannot say — that's what makes the parts we do claim worth trusting.\n\n[Sources] association_summary.txt"
    )

    # =========================================================================
    # SLIDE 13: CLOSING (Epilogue)
    # =========================================================================
    sl13 = prs.slides.add_slide(blank_layout)
    bg(sl13, TEAL)
    rect(sl13, Inches(5.87), Inches(1.7), Inches(1.6), Pt(4), AMBER)

    tf = box(sl13, Inches(1.2), Inches(2.3), Inches(10.9), Inches(2.6))
    p1 = tf.paragraphs[0]
    p1.text = "“In this data, the story barely registers."
    p1.font.size = Pt(38)
    p1.font.bold = True
    p1.font.color.rgb = PAPER
    p1.font.name = DISPLAY
    p1.alignment = PP_ALIGN.CENTER

    p2 = tf.add_paragraph()
    p2.text = "The structure carries the signal.”"
    p2.font.size = Pt(38)
    p2.font.bold = True
    p2.font.color.rgb = PAPER
    p2.font.name = DISPLAY
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(8)

    tf = box(sl13, Inches(1.2), Inches(5.1), Inches(10.9), Inches(0.7))
    tf.text = "Thank you — questions."
    p_q = tf.paragraphs[0]
    p_q.font.size = Pt(22)
    p_q.font.color.rgb = AMBER
    p_q.font.name = DISPLAY
    p_q.font.bold = True
    p_q.alignment = PP_ALIGN.CENTER

    tf = box(sl13, Inches(1.2), Inches(6.5), Inches(10.9), Inches(0.4))
    tf.text = "Team Cultural Blend · UNSW Marketing Analytics Hackathon 2026"
    p_team = tf.paragraphs[0]
    p_team.font.size = Pt(12)
    p_team.font.color.rgb = RGBColor(0x8F, 0xB0, 0xBB)
    p_team.font.name = MONO
    p_team.alignment = PP_ALIGN.CENTER

    rect(sl13, Inches(0), Inches(7.15), Inches(13.333), Inches(0.35), AMBER)
    tf_foot = box(sl13, Inches(0.75), Inches(7.17), Inches(11.5), Inches(0.30))
    p_f = tf_foot.paragraphs[0]
    p_f.text = "UNSW Marketing Analytics Hackathon 2026"
    p_f.font.size = Pt(10)
    p_f.font.bold = True
    p_f.font.color.rgb = INK
    p_f.font.name = MONO
    sl13.notes_slide.notes_text_frame.text = (
        "(Both, ~20s) (Tuan) In this data, the story barely registers — the structure carries the signal. "
        "(Sophia) And testing hard enough to say, honestly, that there is no robust evidence for the story — "
        "that's worth more to a platform than a good-sounding tip. Thank you — we're happy to take your questions.\n\n[Sources] docs/presentation/archive/september_prep/deck_content.md"
    )

    # =========================================================================
    # SLIDES 14–17: APPENDIX SLIDES (A1–A4)
    # =========================================================================
    appendix_data = [
        (14, "APPENDIX · A1", "A1", "The two-country problem, in full",
         [
             "Pooled categories: Middle East = Palestine + Yemen (14,946 loans); Central America = Honduras + Nicaragua (59,391); North America = Haiti alone.",
             "Few-cluster screen p (duration / 24h / notebook fit): ME 0.12 / 0.21 / 0.08 · CA 0.06 / 0.14 / 0.07 — same direction in every fit, none significant; t(1) critical value 12.7.",
             "North America: single country — between-country uncertainty not estimable at all.",
             "The screen is a conservative heuristic: it can downgrade a claim, never certify one. Next step: country-stratified A/B test in those four markets."
         ],
         "Backup for Slide 8 probes: exact pooled definitions, all p-values, the single-country boundary, and the honest status of the screen."),
        (15, "APPENDIX · A2", "A2", "Predictive weight ≠ statistical robustness",
         [
             "SHAP importance from the boosted forecasting model: structure fills the top ranks (amount, term, period, size band, sector, gender).",
             "No family, agency, or urgency feature reaches the top 15; sentiment is 11th despite its disputed significance.",
             "Complementary predictive evidence only — a different model, no region interactions; it cannot confirm or refute any coefficient's sign or uncertainty."
         ],
         "Backup for SHAP questions: what the ranking shows, and exactly what it cannot corroborate."),
        (16, "APPENDIX · A3", "A3", "The '~10x' comparison, exactly",
         [
             "Correlation with funding speed: loan amount (log) r = 0.43, repayment term r = 0.28 — vs competence 0.058, family 0.019, urgency 0.010.",
             "Loan-amount deciles also rise almost monotonically (~2 days for the smallest asks, ~18 for the largest) — monotonicity, not the 10x basis itself.",
             "Gender: female-posted median 2.3 days vs male 7.7 (male coefficient +0.430 survives HC3 AND country clustering, p < 0.0001 — still associational)."
         ],
         "Backup for Slide 7 probes: the amount gradient and the gender gap's robustness status."),
        (17, "APPENDIX · A4", "A4", "24h classifier — operating detail",
         [
             "Holdout (posted 2024-01-01 onward): 278,887 loans; 87,466 funded within 24h vs 191,421 not.",
             "ROC AUC 0.8997 · average precision 0.8301 · Brier 0.1156 · accuracy 0.840 — structure does the work: no framing feature in the SHAP top 10 (sentiment is 11th).",
             "Boundary: negative class = 'eventually funded, but not within 24h'. Expired/withdrawn listings never enter the data — a retrospective ranking prototype among eventual funders.",
             "Path to deployment: all posted listings incl. expired/withdrawn outcomes -> define operational target + censoring window -> retrain, validate -> threshold, calibration, fairness, prospective test."
         ],
         "Backup for classifier questions: holdout metrics, censoring boundary, and the retraining path before operational deployment.")
    ]

    for app_idx, eyebrow, step, title, bullets, note in appendix_data:
        sl = prs.slides.add_slide(blank_layout)
        bg(sl, PAPER)
        add_chrome(sl, eyebrow, step, title)
        add_chart_exhibit(sl, app_idx, chart_top=2.0)

        bw = 7.1 if app_idx in CHARTS else 11.8
        tf = box(sl, Inches(0.75), Inches(2.0), Inches(bw), Inches(4.8))
        for j, item in enumerate(bullets):
            p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            r1 = p.add_run()
            r1.text = "▪  "
            r1.font.color.rgb = AMBER
            r1.font.bold = True
            r2 = p.add_run()
            r2.text = item
            r2.font.size = Pt(13)
            r2.font.color.rgb = INK
            r2.font.name = BODY
            p.space_after = Pt(8)
            p.line_spacing = 1.15
        sl.notes_slide.notes_text_frame.text = f"{note}\n\n[Sources] analysis_summary.json"

    prs.save(str(out_path))
    print(f"Successfully generated {len(prs.slides)} slides in {out_path}!")

def main():
    print(f"Building polished v3 presentation deck: {OUTPUT_PPTX}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    build_deck(OUTPUT_PPTX)

if __name__ == "__main__":
    main()
