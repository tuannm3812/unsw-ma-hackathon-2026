#!/usr/bin/env python3
"""Build the refined, authoritative presentation deck for UNSW Marketing Analytics Hackathon 2026.

Adheres strictly to docs/presentation/DESIGN.md:
- 960 x 540 pt widescreen canvas (16:9).
- Institutional Blue (#0F4BEB) & Amber (#E6A23C) palette with Navy (#17243B) ink and Cream (#FAF7F0) canvas.
- Exact grid layout:
  - Header: Section label at y=29.5, Title at y=48.4 (24pt bold blue), Subtitle at y=90.9 (12pt grey).
  - Left Evidence Rail (x=43.5, y=130, width=600pt).
  - Vertical Divider at x=658 (y=130 to y=476).
  - Takeaway Column at x=684 (y=136, width=235pt).
  - Paired Red Badges (#C64040, 12pt circle, 8pt bold white number) on evidence rail and takeaway column.
  - Footnote / Method Note at y=482 (8.5pt grey with bold prefix).
- Full structured speaker notes on every single slide.
"""

import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# -----------------------------------------------------------------------------
# Color Definitions (DESIGN.md)
# -----------------------------------------------------------------------------
C_BLUE = RGBColor.from_string("0F4BEB")       # Primary Blue
C_AMBER = RGBColor.from_string("E6A23C")      # Accent Amber
C_NAVY = RGBColor.from_string("17243B")       # Navy Ink (Headings & Body)
C_CREAM = RGBColor.from_string("FAF7F0")      # Cream Canvas
C_GREY = RGBColor.from_string("59636E")       # Muted Grey (Subtitles & Notes)
C_SLATE = RGBColor.from_string("46576C")      # Neutral Comparison
C_RED = RGBColor.from_string("C64040")        # Red Marker Badge
C_WHITE = RGBColor.from_string("FFFFFF")      # Surface White
C_RULE = RGBColor.from_string("D8DCE3")       # Divider Rule
C_PALE_BLUE = RGBColor.from_string("E7EDFD")  # Highlight Card Fill
C_PALE_AMBER = RGBColor.from_string("FBEFD9") # Caveat Callout Fill

FONT_NAME = "Google Sans"
FALLBACK_FONT = "Arial"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "docs" / "presentation" / "archive" / "november_old_decks" / "output"
OUTPUT_PPTX = OUTPUT_DIR / "cultural-blend-beyond-a-good-story-refined.pptx"
CHARTS_DIR = PROJECT_ROOT / "docs" / "presentation" / "charts"


def create_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width = Pt(960)
    prs.slide_height = Pt(540)
    return prs


def apply_background(slide, color=C_CREAM):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_header(slide, section: str, title: str, subtitle: str):
    """Render the standard top header."""
    # Section Label
    box_sec = slide.shapes.add_textbox(Pt(43.5), Pt(24), Pt(870), Pt(18))
    tf_sec = box_sec.text_frame
    tf_sec.word_wrap = True
    tf_sec.margin_left = tf_sec.margin_right = tf_sec.margin_top = tf_sec.margin_bottom = 0
    p_sec = tf_sec.paragraphs[0]
    p_sec.font.name = FONT_NAME
    p_sec.font.size = Pt(10)
    p_sec.font.bold = True
    p_sec.font.color.rgb = C_NAVY
    run1 = p_sec.add_run()
    run1.text = section.upper()
    run2 = p_sec.add_run()
    run2.text = "  |  UNSW MARKETING ANALYTICS HACKATHON 2026"
    run2.font.bold = False
    run2.font.color.rgb = C_GREY

    # Slide Title
    box_title = slide.shapes.add_textbox(Pt(43.5), Pt(46), Pt(870), Pt(40))
    tf_title = box_title.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    p_title.font.name = FONT_NAME
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = C_BLUE
    p_title.text = title

    # Scope Subtitle
    box_sub = slide.shapes.add_textbox(Pt(43.5), Pt(89), Pt(870), Pt(22))
    tf_sub = box_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    p_sub.font.name = FONT_NAME
    p_sub.font.size = Pt(11.5)
    p_sub.font.color.rgb = C_GREY
    p_sub.text = subtitle


def add_divider(slide):
    """Render the standard vertical divider at x=658."""
    connector = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Pt(658), Pt(126), Pt(658), Pt(472)
    )
    connector.line.color.rgb = C_RULE
    connector.line.width = Pt(1)


def add_marker(slide, x: float, y: float, number: str):
    """Add a red takeaway / evidence marker badge (12pt diameter circle)."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, Pt(x), Pt(y), Pt(14), Pt(14)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = C_RED
    shape.line.fill.background()
    shape.line.width = Pt(0)
    tf = shape.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.font.name = FONT_NAME
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = C_WHITE
    p.text = number
    return shape


def add_card(slide, x: float, y: float, w: float, h: float, bg_color=C_WHITE, border_color=C_RULE):
    """Add a rounded container card."""
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Pt(x), Pt(y), Pt(w), Pt(h)
    )
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(0.75)
    else:
        card.line.fill.background()
    return card


def add_takeaways(slide, items):
    """Render the standard takeaway rail at x=684, y=130."""
    cur_y = 130
    for idx, (heading, body) in enumerate(items, start=1):
        # Red numbered marker at x=668
        add_marker(slide, 666, cur_y + 2, str(idx))

        # Text box at x=686
        box = slide.shapes.add_textbox(Pt(686), Pt(cur_y), Pt(230), Pt(100))
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        # Heading
        p_head = tf.paragraphs[0]
        p_head.font.name = FONT_NAME
        p_head.font.size = Pt(11.5)
        p_head.font.bold = True
        p_head.font.color.rgb = C_NAVY
        p_head.text = heading
        p_head.space_after = Pt(3)

        # Body
        p_body = tf.add_paragraph()
        p_body.font.name = FONT_NAME
        p_body.font.size = Pt(10)
        p_body.font.color.rgb = C_NAVY
        p_body.line_spacing = 1.15
        p_body.text = body

        cur_y += 105


def add_footnote(slide, note: str, scope: str = ""):
    """Render the standard footnote at y=482."""
    box = slide.shapes.add_textbox(Pt(43.5), Pt(482), Pt(870), Pt(24))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.font.name = FONT_NAME
    p.font.size = Pt(8.5)
    p.font.color.rgb = C_GREY
    
    if scope:
        r_sc = p.add_run()
        r_sc.text = "Scope: "
        r_sc.font.bold = True
        r_sc_t = p.add_run()
        r_sc_t.text = f"{scope}  |  "
        
    r_n = p.add_run()
    r_n.text = "Note: "
    r_n.font.bold = True
    r_t = p.add_run()
    r_t.text = note


def set_speaker_notes(slide, notes: str):
    """Attach formatted speaker notes to the slide."""
    slide.notes_slide.notes_text_frame.text = notes


# =============================================================================
# Slide Builders
# =============================================================================

def build_slide_1_cover(prs):
    """Slide 1: Cover."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)

    # Sub-header tag
    tag_box = slide.shapes.add_textbox(Pt(50), Pt(45), Pt(860), Pt(20))
    p_tag = tag_box.text_frame.paragraphs[0]
    p_tag.font.name = FONT_NAME
    p_tag.font.size = Pt(11)
    p_tag.font.bold = True
    p_tag.font.color.rgb = C_AMBER
    p_tag.text = "UNSW MARKETING ANALYTICS HACKATHON 2026  |  FINALIST RESEARCH CASE STUDY"

    # Main Title
    title_box = slide.shapes.add_textbox(Pt(50), Pt(75), Pt(860), Pt(90))
    p_t = title_box.text_frame.paragraphs[0]
    p_t.font.name = FONT_NAME
    p_t.font.size = Pt(36)
    p_t.font.bold = True
    p_t.font.color.rgb = C_BLUE
    p_t.text = "Beyond a Good Story"

    # Subtitle
    sub_box = slide.shapes.add_textbox(Pt(50), Pt(140), Pt(860), Pt(50))
    p_s = sub_box.text_frame.paragraphs[0]
    p_s.font.name = FONT_NAME
    p_s.font.size = Pt(17)
    p_s.font.color.rgb = C_NAVY
    p_s.text = "When and for Whom Loan Narratives Are Linked to Faster Prosocial Funding"

    # Hero card on canvas
    add_card(slide, 50, 210, 860, 230, bg_color=C_WHITE, border_color=C_RULE)

    # 4 Key Stat Badges inside card
    stat_cols = [
        ("1,453,840", "Eligible Completed Loans", "Full 10-year platform dataset (2016-2025)", C_BLUE),
        ("96.4%", "Pre-Disbursed Loans", "Capital replenishment, not borrower waiting", C_AMBER),
        ("49.0%", "Variance Explained (R²)", "Hard structural context drives funding speed", C_NAVY),
        ("5 Annual Cohorts", "Retrospective Benchmark", "As-of matched evaluation across 728k records", C_SLATE),
    ]
    card_w = 195
    start_x = 70
    for val, lbl, desc, col in stat_cols:
        stat_box = slide.shapes.add_textbox(Pt(start_x), Pt(230), Pt(card_w), Pt(180))
        tf = stat_box.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.font.name = FONT_NAME
        p1.font.size = Pt(28)
        p1.font.bold = True
        p1.font.color.rgb = col
        p1.text = val
        
        p2 = tf.add_paragraph()
        p2.font.name = FONT_NAME
        p2.font.size = Pt(12)
        p2.font.bold = True
        p2.font.color.rgb = C_NAVY
        p2.text = lbl
        p2.space_before = Pt(4)
        
        p3 = tf.add_paragraph()
        p3.font.name = FONT_NAME
        p3.font.size = Pt(9.5)
        p3.font.color.rgb = C_GREY
        p3.text = desc
        p3.space_before = Pt(4)
        
        start_x += 205

    # Footer metadata
    foot_box = slide.shapes.add_textbox(Pt(50), Pt(465), Pt(860), Pt(30))
    p_f = foot_box.text_frame.paragraphs[0]
    p_f.font.name = FONT_NAME
    p_f.font.size = Pt(10)
    p_f.font.color.rgb = C_GREY
    p_f.text = "Team Cultural Blend (Manh Tuan Nguyen, Sophia Nguyen, Mike Nguyen)  |  University of Technology Sydney (UTS)  |  November 2026"

    set_speaker_notes(slide, """PURPOSE: Welcome the audience and position the research project as a rigorous, post-competition decision case study.

[Point 1: Research Question] We are Team Cultural Blend from the University of Technology Sydney. We set out to investigate a central marketing challenge on microfinance platform Kiva: which narrative choices in a borrower's loan description associate with faster funding, for whom, and when?
[Point 2: Population Scope] Unlike sample-based pitch decks, our entire investigation is grounded in the complete, verified 1.45-million-row Kiva dataset spanning 2016 to 2025.
[Point 3: Key Paradox] While microfinance storytelling is widely celebrated, our empirical findings reveal that hard structural realities—loan size, terms, and geography—drive funding speed, while popular narrative levers largely collapse under rigorous statistical scrutiny.

TRANSITION: Let's begin with our executive summary and recommended research roadmap.""")


def build_slide_2_executive_summary(prs):
    """Slide 2: Executive Summary & Roadmap."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)
    add_header(
        slide,
        "Executive Summary",
        "Prioritise a fair text comparison and a targeted partner pilot",
        "Synthesizing findings across 1.45M loans, inferential sensitivity, and matched predictive benchmarks"
    )
    add_divider(slide)

    # Evidence Rail: 3 sequential action cards
    cards = [
        ("1", "AUDIT", "Validate data definitions & partner timeline",
         "96.4% of Kiva loans are disbursed before platform listing (median 24 days earlier). Funding duration reflects field partner working capital cycles, not borrower waiting time.",
         C_PALE_BLUE, C_BLUE),
        ("2", "COMPARE", "Measure what text adds beyond structure",
         "Adding vocabulary to linear models yields a modest median duration gain of +0.29 days across 5 annual cohorts (2021-2025). Compact text in boosted trees adds almost zero (+0.03d).",
         C_WHITE, C_NAVY),
        ("3", "TEST", "Design one pre-registered field pilot",
         "Do not mandate platform-wide copywriting guidelines. Partner with participating microfinance institutions to test factual clarity interventions in randomized field A/B pilots.",
         C_PALE_AMBER, C_AMBER)
    ]
    cur_y = 130
    for num, tag, title, body, bg_col, border_col in cards:
        add_card(slide, 43.5, cur_y, 600, 102, bg_color=bg_col, border_color=border_col)
        add_marker(slide, 58, cur_y + 14, num)
        
        box = slide.shapes.add_textbox(Pt(84), Pt(cur_y + 8), Pt(545), Pt(88))
        tf = box.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.font.name = FONT_NAME
        p1.font.size = Pt(11.5)
        p1.font.bold = True
        p1.font.color.rgb = C_NAVY
        p1.text = f"{tag}: {title}"
        
        p2 = tf.add_paragraph()
        p2.font.name = FONT_NAME
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = C_NAVY
        p2.line_spacing = 1.15
        p2.text = body
        p2.space_before = Pt(3)
        
        cur_y += 114

    # Takeaways
    add_takeaways(slide, [
        ("Partner Capital Cycle", "Listing duration measures partner liquidity replenishment, not borrower relief. Communications must address partner operations."),
        ("Modest Predictive Gain", "Narrative text adds a minor linear signal (~0.29d MAE), but gradient boosted trees already capture non-linear structural signals without text."),
        ("No Universal Writing Rule", "Popular beliefs like 'urgent language speeds up funding' are statistical artifacts that disappear under country clustering.")
    ])

    add_footnote(
        slide,
        "Authoritative full-dataset reports (reports/generated_full_dataset/ and reports/text_benchmark_reviewed/).",
        "1,453,840 eligible records (2016-2025); 728,640 retrospective benchmark evaluations."
    )

    set_speaker_notes(slide, """PURPOSE: Deliver the top-line executive recommendations before diving into detailed data and model evidence.

[Point 1: Audit] First, our audit reveals that 96.4% of loans are pre-disbursed. Funding speed is fundamentally a partner liquidity problem, not a borrower waiting period.
[Point 2: Compare] Second, our November matched benchmark proved that while rich text shaves about 0.29 days off linear forecast error, gradient boosted trees gain almost nothing from text features because loan amount and terms already explain 49% of the variance.
[Point 3: Test] Third, we strongly advise platform managers against issuing universal writing rules. Instead, execute stratified partner pilots to test factual clarity.

TRANSITION: Let's inspect the underlying operational mechanics of the Kiva funding process.""")


def build_slide_3_context_timeline(prs):
    """Slide 3: Context & The Funding Cycle."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)
    add_header(
        slide,
        "Operational Reality",
        "The observed outcome is field partner capital replenishment",
        "Kiva's microfinance architecture decouples field disbursal from platform fundraising"
    )
    add_divider(slide)

    # Left Evidence: Hero stat card + 4-stage process card
    add_card(slide, 43.5, 130, 600, 110, bg_color=C_WHITE, border_color=C_RULE)
    add_marker(slide, 58, 142, "1")
    
    stat_box = slide.shapes.add_textbox(Pt(80), Pt(138), Pt(550), Pt(95))
    tf_stat = stat_box.text_frame
    tf_stat.word_wrap = True
    p1 = tf_stat.paragraphs[0]
    p1.font.name = FONT_NAME
    p1.font.size = Pt(24)
    p1.font.bold = True
    p1.font.color.rgb = C_AMBER
    p1.text = "96.4% of Loans Disbursed Prior to Listing"
    p2 = tf_stat.add_paragraph()
    p2.font.name = FONT_NAME
    p2.font.size = Pt(10)
    p2.font.color.rgb = C_NAVY
    p2.line_spacing = 1.15
    p2.text = "Across 1.45M loans, the borrower receives their funds a median of 24 days BEFORE the loan is posted on Kiva.org. Platform funding speed is the replenishment cycle of the local microfinance partner, not borrower wait time."
    p2.space_before = Pt(3)

    # Timeline card
    add_card(slide, 43.5, 252, 600, 218, bg_color=C_WHITE, border_color=C_RULE)
    add_marker(slide, 58, 264, "2")
    
    time_box = slide.shapes.add_textbox(Pt(80), Pt(260), Pt(550), Pt(200))
    tf_time = time_box.text_frame
    tf_time.word_wrap = True
    
    pt0 = tf_time.paragraphs[0]
    pt0.font.name = FONT_NAME
    pt0.font.size = Pt(13)
    pt0.font.bold = True
    pt0.font.color.rgb = C_BLUE
    pt0.text = "Kiva 4-Stage Working Capital Timeline"
    
    stages = [
        ("Stage 1: Field Disbursal", "Partner vets borrower and disburses cash locally (Day -24 median)."),
        ("Stage 2: Listing & Translation", "Partner uploads borrower story, translates to English, applies templates."),
        ("Stage 3: Platform Fundraising", "Loan active on Kiva; duration variable (Median 2.88 days; mean 8.6 days)."),
        ("Stage 4: Capital Settlement", "Crowdfunded lenders replenish partner's liquidity pool to fund new loans.")
    ]
    for st_title, st_desc in stages:
        p_st = tf_time.add_paragraph()
        p_st.font.name = FONT_NAME
        p_st.font.size = Pt(9.5)
        p_st.line_spacing = 1.15
        p_st.space_before = Pt(4)
        r_t = p_st.add_run()
        r_t.text = f"{st_title} — "
        r_t.font.bold = True
        r_t.font.color.rgb = C_NAVY
        r_d = p_st.add_run()
        r_d.text = st_desc
        r_d.font.color.rgb = C_GREY

    # Takeaways
    add_takeaways(slide, [
        ("Partner Liquidity Velocity", "Speeding up funding allows microfinance partners to re-lend capital faster. It does not shorten the borrower's wait for emergency funds."),
        ("Template Confounding", "Because partner field staff translate and write descriptions, narrative features reflect partner administrative habits as much as borrower voice.")
    ])

    add_footnote(
        slide,
        "Field data audit confirms disbursalDate precedes fundraisingDate in 1,401,988 of 1,453,840 loans.",
        "Kiva.org API data dictionary; Allison et al. (2022)."
    )

    set_speaker_notes(slide, """PURPOSE: Clarify the fundamental business process underlying the dataset and correct a common misinterpretation.

[Point 1: 96.4% Disbursed] Almost all loans—96.4%—are already disbursed by the local microfinance institution weeks before lenders ever see them online.
[Point 2: Working Capital Cycle] Therefore, when a loan funds in 24 hours versus 15 days, it affects the partner's balance sheet velocity, not the borrower's immediate survival.
[Point 3: Implication] Any intervention designed to speed up funding should be marketed to lending partners to improve their liquidity management.

TRANSITION: Next, let's decompose the funding process into an issue tree to see which levers actually matter.""")


def build_slide_4_issue_tree(prs):
    """Slide 4: Problem Decomposition & Issue Tree."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)
    add_header(
        slide,
        "Problem Decomposition",
        "Investigate four connected mechanisms before proposing changes",
        "A structured diagnostic framework separating observed loan factors from unobserved confounders"
    )
    add_divider(slide)

    # 4 columns on the evidence rail
    cols = [
        ("1. Borrower Context", "Observed", C_BLUE, [
            "Loan amount requested",
            "Repayment term (months)",
            "Gender (female preference)",
            "Sector & activity type",
            "Geographic country/region"
        ]),
        ("2. Partner Operational", "Partially Observed", C_AMBER, [
            "Partner risk rating (1-5)",
            "Disbursal lead time",
            "Narrative framing style",
            "English translation quality",
            "Programme type (whySpecial)"
        ]),
        ("3. Platform Exposure", "Unobserved", C_SLATE, [
            "Homepage spotlighting",
            "Corporate matching funds",
            "Search ranking & sort order",
            "Category browsing placement",
            "Lender email newsletters"
        ]),
        ("4. Lender Behavior", "Partially Observed", C_NAVY, [
            "Prosocial altruism",
            "Portfolio diversification",
            "Repeat lender relationships",
            "Loss aversion & risk",
            "Herd behavior / momentum"
        ])
    ]
    cur_x = 43.5
    w_col = 142
    for title, status, col_color, bullets in cols:
        add_card(slide, cur_x, 130, w_col, 340, bg_color=C_WHITE, border_color=C_RULE)
        
        box = slide.shapes.add_textbox(Pt(cur_x + 8), Pt(138), Pt(w_col - 16), Pt(320))
        tf = box.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.font.name = FONT_NAME
        p1.font.size = Pt(10.5)
        p1.font.bold = True
        p1.font.color.rgb = col_color
        p1.text = title
        
        p2 = tf.add_paragraph()
        p2.font.name = FONT_NAME
        p2.font.size = Pt(8.5)
        p2.font.bold = True
        p2.font.color.rgb = C_GREY
        p2.text = f"[{status.upper()}]"
        p2.space_before = Pt(2)
        p2.space_after = Pt(8)
        
        for b in bullets:
            pb = tf.add_paragraph()
            pb.font.name = FONT_NAME
            pb.font.size = Pt(8.5)
            pb.font.color.rgb = C_NAVY
            pb.line_spacing = 1.15
            pb.space_before = Pt(4)
            pb.text = f"• {b}"
            
        cur_x += 152

    # Takeaways
    add_takeaways(slide, [
        ("Structural Factors Rule", "Borrower context (Branch 1) accounts for virtually all explained variance in funding velocity."),
        ("Missing Exposure Logs", "Platform exposure (Branch 3) creates massive velocity shocks that cannot be controlled via narrative analysis."),
        ("Confounded Partner Text", "Partner translation and writing templates (Branch 2) bundle narrative text with operational sophistication.")
    ])

    add_footnote(
        slide,
        "Diagnostic framework adapted from McKinsey 7-step problem solving & microfinance literature.",
        "Identifies what observational regression can and cannot control."
    )

    set_speaker_notes(slide, """PURPOSE: Lay out the comprehensive issue tree and distinguish what our data observes from what remains unmeasured.

[Point 1: 4 Branches] We decompose platform funding speed into four distinct branches: borrower context, partner operations, platform exposure, and lender behavior.
[Point 2: Observational Boundaries] While borrower structure is fully observed, platform exposure—like homepage features and matching campaigns—is entirely unrecorded in Kiva's public data.
[Point 3: Implication] Analysts who attribute speed solely to text are confounding narrative framing with unobserved platform promotion.

TRANSITION: Let us look at what happens when we model the fully observed structural branch.""")


def build_slide_5_structural_dominance(prs):
    """Slide 5: Structural Dominance."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)
    add_header(
        slide,
        "Structural Findings",
        "Hard structural constraints dominate platform funding speed",
        "Loan size, repayment terms, sector, and geography account for ~49% of forecast variance"
    )
    add_divider(slide)

    # Evidence Rail: 2 cards (Correlation Card & Sector Card)
    add_card(slide, 43.5, 130, 600, 160, bg_color=C_WHITE, border_color=C_RULE)
    add_marker(slide, 58, 142, "1")
    
    box1 = slide.shapes.add_textbox(Pt(80), Pt(138), Pt(550), Pt(145))
    tf1 = box1.text_frame
    tf1.word_wrap = True
    
    p1 = tf1.paragraphs[0]
    p1.font.name = FONT_NAME
    p1.font.size = Pt(13)
    p1.font.bold = True
    p1.font.color.rgb = C_BLUE
    p1.text = "Correlation with Log Funding Duration (Days)"
    
    corrs = [
        ("Loan Amount (log)", "+0.429 (Spearman 0.559)", "Large loans face heavy funding friction", C_BLUE),
        ("Lender Repayment Term", "+0.282", "Longer capital lockups deter lenders", C_BLUE),
        ("Family Framing Mentions", "-0.052", "Minor negative correlation with duration", C_SLATE),
        ("Urgency Mentions", "-0.012", "Virtually zero direct linear correlation", C_SLATE),
        ("Sentiment Tone (VADER)", "+0.018", "Virtually zero direct linear correlation", C_SLATE)
    ]
    for var, val, desc, col in corrs:
        pc = tf1.add_paragraph()
        pc.font.name = FONT_NAME
        pc.font.size = Pt(9.5)
        pc.space_before = Pt(3)
        r1 = pc.add_run()
        r1.text = f"• {var}: "
        r1.font.bold = True
        r1.font.color.rgb = C_NAVY
        r2 = pc.add_run()
        r2.text = f"{val}  "
        r2.font.bold = True
        r2.font.color.rgb = col
        r3 = pc.add_run()
        r3.text = f"({desc})"
        r3.font.color.rgb = C_GREY

    # Sector & Model Card
    add_card(slide, 43.5, 302, 600, 168, bg_color=C_WHITE, border_color=C_RULE)
    add_marker(slide, 58, 314, "2")
    
    box2 = slide.shapes.add_textbox(Pt(80), Pt(310), Pt(550), Pt(150))
    tf2 = box2.text_frame
    tf2.word_wrap = True
    
    p2 = tf2.paragraphs[0]
    p2.font.name = FONT_NAME
    p2.font.size = Pt(13)
    p2.font.bold = True
    p2.font.color.rgb = C_NAVY
    p2.text = "Sector Gaps & Predictive Power on Holdout (2024–2025)"
    
    p2_b1 = tf2.add_paragraph()
    p2_b1.font.name = FONT_NAME
    p2_b1.font.size = Pt(9.5)
    p2_b1.space_before = Pt(4)
    p2_b1.text = "• Sector Disparities: Education (coef -1.07), Water (-1.12), and Clean Energy (-0.80) fund 2-4x faster than Retail (+0.20) and Clothing (+0.26), holding loan size constant."
    
    p2_b2 = tf2.add_paragraph()
    p2_b2.font.name = FONT_NAME
    p2_b2.font.size = Pt(9.5)
    p2_b2.space_before = Pt(4)
    p2_b2.text = "• GBDT Model Performance: On 278,887 holdout loans, boosted trees achieve MAE = 5.56 days and R² = 0.490 using only structural and baseline variables."
    
    p2_b3 = tf2.add_paragraph()
    p2_b3.font.name = FONT_NAME
    p2_b3.font.size = Pt(9.5)
    p2_b3.space_before = Pt(4)
    p2_b3.text = "• Linear Ridge Baseline: Achieves MAE = 6.76 days. The 1.20-day gain in boosted trees proves that structural factors interact non-linearly."

    # Takeaways
    add_takeaways(slide, [
        ("Scale Over Story", "Loan amount is the single strongest predictor of funding friction (r = +0.43). No narrative choice can overcome a large funding hurdle."),
        ("Predictable Baseline", "Half of all duration variance (R² = 0.490) is explained before a single word of text is read by the model."),
        ("Structural Synergies", "Non-linear models outperform additive linear models by 1.20 days MAE by exploiting size, sector, and term combinations.")
    ])

    add_footnote(
        slide,
        "Evaluated on 278,887 holdout loans (2024-2025) strictly following training on 1,174,953 loans (2016-2023).",
        "Authoritative full-dataset regression and GBDT models."
    )

    set_speaker_notes(slide, """PURPOSE: Prove that structural characteristics of the loan account for the vast majority of predictable funding variation.

[Point 1: Correlation] Loan amount has a massive correlation with duration—Spearman rank correlation of 0.559. In contrast, narrative measures show correlations below 0.06.
[Point 2: Sector Spreads] Mission-driven sectors like Water and Clean Energy fund four times faster than commerce sectors like Clothing and Retail.
[Point 3: Model Power] Our gradient boosted trees achieve an R² of 0.490 and an MAE of 5.56 days on the 2024–2025 holdout without needing text.

TRANSITION: Next, let's examine platform-wide trends across time and borrower demographics.""")


def build_slide_6_demographic_shifts(prs):
    """Slide 6: Structural Shifts & Gender Disparities."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)
    add_header(
        slide,
        "Structural Findings",
        "Fast funding dropped during the pandemic and never recovered",
        "Platform-wide conversion within 24 hours experienced a permanent downward structural break"
    )
    add_divider(slide)

    # Evidence Rail: 2 cards (Pandemic Shift & Gender Gap)
    add_card(slide, 43.5, 130, 600, 160, bg_color=C_WHITE, border_color=C_RULE)
    add_marker(slide, 58, 142, "1")
    
    box1 = slide.shapes.add_textbox(Pt(80), Pt(138), Pt(550), Pt(145))
    tf1 = box1.text_frame
    tf1.word_wrap = True
    
    p1 = tf1.paragraphs[0]
    p1.font.name = FONT_NAME
    p1.font.size = Pt(13)
    p1.font.bold = True
    p1.font.color.rgb = C_BLUE
    p1.text = "Permanent Drop in Fast-Funding Velocity (Within 24h)"
    
    shifts = [
        ("Pre-Pandemic (2016–2019)", "46.0% funded in 24h", "Median funding duration: 1.25 days", C_BLUE),
        ("Pandemic Shock (2020–2021)", "30.3% funded in 24h", "Median duration stretched to 3.52 days", C_AMBER),
        ("Post-Pandemic (2022–2025)", "30.0% funded in 24h", "Zero recovery; median duration: 3.48 days", C_RED)
    ]
    for per, rate, dur, col in shifts:
        pc = tf1.add_paragraph()
        pc.font.name = FONT_NAME
        pc.font.size = Pt(9.5)
        pc.space_before = Pt(4)
        r1 = pc.add_run()
        r1.text = f"• {per}: "
        r1.font.bold = True
        r1.font.color.rgb = C_NAVY
        r2 = pc.add_run()
        r2.text = f"{rate}  "
        r2.font.bold = True
        r2.font.color.rgb = col
        r3 = pc.add_run()
        r3.text = f"({dur})"
        r3.font.color.rgb = C_GREY

    # Gender Card
    add_card(slide, 43.5, 302, 600, 168, bg_color=C_WHITE, border_color=C_RULE)
    add_marker(slide, 58, 314, "2")
    
    box2 = slide.shapes.add_textbox(Pt(80), Pt(310), Pt(550), Pt(150))
    tf2 = box2.text_frame
    tf2.word_wrap = True
    
    p2 = tf2.paragraphs[0]
    p2.font.name = FONT_NAME
    p2.font.size = Pt(13)
    p2.font.bold = True
    p2.font.color.rgb = C_NAVY
    p2.text = "Gender Disparities & Fast-Funding Classification"
    
    p2_b1 = tf2.add_paragraph()
    p2_b1.font.name = FONT_NAME
    p2_b1.font.size = Pt(9.5)
    p2_b1.space_before = Pt(4)
    p2_b1.text = "• Female Borrowing Advantage: Female entrepreneurs fund in a median of 2.33 days compared to 7.71 days for male borrowers (3.3x slower). Male dummy OLS coefficient: +0.434 (p < 0.0001)."
    
    p2_b2 = tf2.add_paragraph()
    p2_b2.font.name = FONT_NAME
    p2_b2.font.size = Pt(9.5)
    p2_b2.space_before = Pt(4)
    p2_b2.text = "• 24-Hour Classifier Accuracy: HistGradientBoostingClassifier predicts fast completion with 0.9053 ROC AUC and 0.8374 Average Precision on the independent holdout set."
    
    p2_b3 = tf2.add_paragraph()
    p2_b3.font.name = FONT_NAME
    p2_b3.font.size = Pt(9.5)
    p2_b3.space_before = Pt(4)
    p2_b3.text = "• Operational Early Warning: This provides Kiva with a production-ready risk scoring engine to flag listings at risk of stalling at publication time."

    # Takeaways
    add_takeaways(slide, [
        ("Permanent Shift", "The pandemic induced a permanent -16 percentage point drop in fast-funding share that has not recovered post-2021."),
        ("Female Preference", "Prosocial lenders exhibit a massive, durable preference for female-led microenterprises across all continents."),
        ("Actionable Screening", "A 0.905 ROC AUC classifier provides field partners with reliable early alerts for listings that require promotional support.")
    ])

    add_footnote(
        slide,
        "Classification evaluated on 278,887 holdout loans (2024-2025).",
        "Authoritative full-dataset descriptive statistics and binary classifier."
    )

    set_speaker_notes(slide, """PURPOSE: Demonstrate how macro-level shocks and demographic preferences shape platform outcomes.

[Point 1: 24h Drop] Prior to 2020, nearly half of all loans funded within 24 hours. During the pandemic, that plummeted to 30.3%—and has remained flat at 30.0% through 2025.
[Point 2: Gender Disparity] Male borrowers take 7.7 days to fund compared to just 2.3 days for female borrowers. Kiva lenders have a deep structural preference for female microborrowers.
[Point 3: 24h Classifier] Our binary model predicts whether a loan will fund in 24 hours with an outstanding 0.905 AUC, creating a turnkey early-warning tool.

TRANSITION: Now, let's submit popular narrative claims to rigorous econometrics.""")


def build_slide_7_clustered_sensitivity(prs):
    """Slide 7: Inferential Scrutiny: Country Clustering."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)
    add_header(
        slide,
        "Inferential Scrutiny",
        "Clustered standard errors overturn apparent narrative significance",
        "Accounting for within-country correlation eliminates 20 of 45 OLS statistical claims"
    )
    add_divider(slide)

    # Evidence Rail: Detailed Comparison Table Card
    add_card(slide, 43.5, 130, 600, 340, bg_color=C_WHITE, border_color=C_RULE)
    add_marker(slide, 58, 142, "1")
    
    t_box = slide.shapes.add_textbox(Pt(80), Pt(138), Pt(550), Pt(325))
    tf = t_box.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.font.name = FONT_NAME
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = C_BLUE
    p0.text = "Robust SE (HC3) vs. Country-Clustered SE on 1.45M Loans"
    
    rows = [
        ("Urgency Mentions", "-0.0795", "p < 0.0001", "p = 0.4442", "SIGNIFICANCE OVERTURNED", C_RED),
        ("Family Framing Main", "+0.0031", "p < 0.0001", "p = 0.7638", "SIGNIFICANCE OVERTURNED", C_RED),
        ("Family × Post-Pandemic", "-0.0152", "p < 0.0001", "p = 0.5298", "SIGNIFICANCE OVERTURNED", C_RED),
        ("Sentiment Compound", "+0.1116", "p < 0.0001", "p = 0.2544", "SIGNIFICANCE OVERTURNED", C_RED),
        ("Agency Mentions", "+0.0007", "p = 0.4601", "p = 0.9412", "CONSISTENTLY NULL", C_SLATE),
        ("Log Loan Amount", "+0.4285", "p < 0.0001", "p < 0.0001", "ROBUSTLY SIGNIFICANT", C_BLUE),
        ("Repayment Term", "+0.0676", "p < 0.0001", "p < 0.0001", "ROBUSTLY SIGNIFICANT", C_BLUE),
        ("Male Gender Dummy", "+0.4336", "p < 0.0001", "p < 0.0001", "ROBUSTLY SIGNIFICANT", C_BLUE)
    ]
    
    # Table header
    p_th = tf.add_paragraph()
    p_th.font.name = FONT_NAME
    p_th.font.size = Pt(9.5)
    p_th.font.bold = True
    p_th.font.color.rgb = C_NAVY
    p_th.space_before = Pt(8)
    p_th.text = f"{'Variable':<24}{'Coef':<10}{'HC3 p':<12}{'Clustered p':<14}{'Conclusion'}"
    
    for var, coef, p_hc3, p_cl, conc, col in rows:
        pr = tf.add_paragraph()
        pr.font.name = FONT_NAME
        pr.font.size = Pt(8.5)
        pr.space_before = Pt(3)
        r1 = pr.add_run()
        r1.text = f"{var:<24}{coef:<10}{p_hc3:<12}{p_cl:<14}"
        r1.font.color.rgb = C_NAVY
        r2 = pr.add_run()
        r2.text = conc
        r2.font.bold = True
        r2.font.color.rgb = col

    # Summary callout at bottom
    p_sum = tf.add_paragraph()
    p_sum.font.name = FONT_NAME
    p_sum.font.size = Pt(9.5)
    p_sum.font.bold = True
    p_sum.font.color.rgb = C_NAVY
    p_sum.space_before = Pt(12)
    p_sum.text = "Result: 20 of 45 model coefficients (44.4%) lose statistical significance when clustering by country! Every single overturned coefficient is a narrative or sentiment term."

    # Takeaways
    add_takeaways(slide, [
        ("The Urgency Illusion", "Naive OLS assumes 1.45M independent observations. Clustered SE reveals that apparent urgency effects were partner-country artifacts (p=0.44)."),
        ("Narrative Vulnerability", "Every single variable that lost significance was a text measure. Narrative signals are highly correlated within local partner practices."),
        ("Structural Resilience", "Hard loan dimensions (amount, term, sector, gender) remain unconditionally significant at p < 0.0001 under all clustering regimes.")
    ])

    add_footnote(
        slide,
        "OLS model on 1,453,840 eligible loans. Clustered standard errors grouped by country_name (80+ country clusters).",
        "Authoritative full-dataset regression and reviewed sensitivity extension."
    )

    set_speaker_notes(slide, """PURPOSE: Deliver the central methodological contribution of the research: why clustered standard errors change everything.

[Point 1: The Table] Under standard HC3 robust errors, almost every variable looks highly significant due to our huge sample of 1.45 million rows.
[Point 2: Urgency Collapses] But when we cluster by country to account for the fact that loans within the same country share partner writing habits and economic context, urgency p-value jumps from 0.0001 to 0.44!
[Point 3: 44% Overturned] Fully 20 of 45 coefficients lose significance—and every single one is a narrative term. Hard structural features never waver.

TRANSITION: Let's examine whether regional narrative effects survive closer scrutiny.""")


def build_slide_8_regional_nuance(prs):
    """Slide 8: Regional Slopes & Few-Cluster Uncertainty."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)
    add_header(
        slide,
        "Regional Nuance",
        "Regional narrative associations rest on sparse country clusters",
        "Within-region contrasts in Middle East and Central America fail small-cluster robustness checks"
    )
    add_divider(slide)

    # Evidence Rail: Regional slope table card
    add_card(slide, 43.5, 130, 600, 340, bg_color=C_WHITE, border_color=C_RULE)
    add_marker(slide, 58, 142, "1")
    
    box = slide.shapes.add_textbox(Pt(80), Pt(138), Pt(550), Pt(325))
    tf = box.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.font.name = FONT_NAME
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = C_BLUE
    p0.text = "Average Within-Region Duration Slopes for Family Framing"
    
    reg_rows = [
        ("Africa", "27", "610,368", "-0.0101", "p = 0.5536", "t(26) p = 0.5587", "No robust effect", C_SLATE),
        ("Asia", "12", "738,191", "+0.0338", "p = 0.0535", "t(11) p = 0.0797", "No robust effect", C_SLATE),
        ("Central America", "2", "59,391", "-0.0742", "p = 0.0000", "t(1) p = 0.0597", "Spans zero in t(1)", C_AMBER),
        ("Middle East", "2", "14,946", "-0.0729", "p = 0.0000", "t(1) p = 0.1203", "Spans zero in t(1)", C_AMBER),
        ("North America", "1", "7,559", "+0.0109", "p = 0.0621", "Unestimable (1 cluster)", "No robust effect", C_SLATE),
        ("Oceania", "4", "23,385", "+0.0162", "p = 0.6305", "t(3) p = 0.6634", "No robust effect", C_SLATE)
    ]
    
    p_th = tf.add_paragraph()
    p_th.font.name = FONT_NAME
    p_th.font.size = Pt(9)
    p_th.font.bold = True
    p_th.font.color.rgb = C_NAVY
    p_th.space_before = Pt(8)
    p_th.text = f"{'Region':<16}{'Countries':<10}{'Loans':<10}{'Slope':<10}{'Clustered':<12}{'Few-Cluster t':<15}"
    
    for reg, cnt, lns, slp, p_cl, p_few, note, col in reg_rows:
        pr = tf.add_paragraph()
        pr.font.name = FONT_NAME
        pr.font.size = Pt(8.5)
        pr.space_before = Pt(3)
        r1 = pr.add_run()
        r1.text = f"{reg:<16}{cnt:<10}{lns:<10}{slp:<10}{p_cl:<12}"
        r1.font.color.rgb = C_NAVY
        r2 = pr.add_run()
        r2.text = f"{p_few:<15}"
        r2.font.bold = True
        r2.font.color.rgb = col

    # Explanation card
    p_note = tf.add_paragraph()
    p_note.font.name = FONT_NAME
    p_note.font.size = Pt(9.5)
    p_note.line_spacing = 1.15
    p_note.space_before = Pt(12)
    p_note.text = "• The Two-Country Trap: Middle East comprises ONLY Palestine & Yemen; Central America comprises ONLY Honduras & Nicaragua. Accumulating thousands of loans across 2 countries creates pseudoreplication."
    
    p_note2 = tf.add_paragraph()
    p_note2.font.name = FONT_NAME
    p_note2.font.size = Pt(9.5)
    p_note2.line_spacing = 1.15
    p_note2.space_before = Pt(3)
    p_note2.text = "• Heuristic t(1) Screen: With G=2 clusters (d.f. = 1), the 95% critical value jumps from 1.96 to 12.71. Both regional intervals expand to cross zero: Middle East [-0.25, +0.10], Central America [-0.16, +0.01]."

    # Takeaways
    add_takeaways(slide, [
        ("Descriptive, Not Causal", "Apparent speedups in Middle East and Central America cannot support universal regional guidelines because each region contains only 2 countries."),
        ("Pseudoreplication", "Thousands of loans within 2 countries share the same partner models and economic crises; they do not represent independent evidence."),
        ("Hypothesis for A/B Tests", "These regional nuances should be treated as exploratory hypotheses for stratified partner trials, not established rules.")
    ])

    add_footnote(
        slide,
        "Average within-region slopes estimated via linear contrasts weighting over observed sector/period shares.",
        "Primary model reports/generated_full_dataset/ and portfolio uncertainty exhibit."
    )

    set_speaker_notes(slide, """PURPOSE: Address regional heterogeneity and explain why family framing cannot be recommended even in seemingly responsive regions.

[Point 1: The Regional Slopes] At first glance, family framing shows significant speedups in Middle East (-0.073) and Central America (-0.074).
[Point 2: The Two-Country Problem] But look at the cluster counts: Middle East has only 2 countries—Palestine and Yemen. Central America has only Honduras and Nicaragua.
[Point 3: Few-Cluster Correction] When we test against a t-distribution with 1 degree of freedom, the 95% confidence interval spans zero in both regions.
[Point 4: Takeaway] These patterns are descriptive artifacts of local partner operations, not universal cultural rules.

TRANSITION: Next, let's explore our November machine learning extension: what happens when we give predictive models full text?""")


def build_slide_9_predictive_benchmark(prs):
    """Slide 9: November Matched Predictive Benchmark."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)
    add_header(
        slide,
        "Predictive Benchmark",
        "Richer text modestly reduces linear error, but tree gains are negligible",
        "Retrospective evaluation across 5 annual cohorts (2021–2025, 728,640 records)"
    )
    add_divider(slide)

    # Evidence Rail: Annual benchmark results card
    add_card(slide, 43.5, 130, 600, 340, bg_color=C_WHITE, border_color=C_RULE)
    add_marker(slide, 58, 142, "1")
    
    box = slide.shapes.add_textbox(Pt(80), Pt(138), Pt(550), Pt(325))
    tf = box.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.font.name = FONT_NAME
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = C_BLUE
    p0.text = "Duration Forecast Error (MAE in Days) Across 5 Annual Cohorts"
    
    bench_rows = [
        ("2021", "8.250", "7.957", "+0.293d [0.20, 0.38]", "+0.035d [-0.07, 0.14]", C_BLUE),
        ("2022", "8.570", "8.197", "+0.372d [0.21, 0.52]", "+0.028d [-0.04, 0.08]", C_BLUE),
        ("2023", "8.185", "7.926", "+0.259d [0.09, 0.41]", "+0.006d [-0.02, 0.04]", C_BLUE),
        ("2024", "7.515", "7.126", "+0.389d [0.29, 0.50]", "+0.001d [-0.02, 0.03]", C_BLUE),
        ("2025", "6.406", "6.147", "+0.260d [0.14, 0.40]", "+0.042d [0.01, 0.07]", C_BLUE)
    ]
    
    p_th = tf.add_paragraph()
    p_th.font.name = FONT_NAME
    p_th.font.size = Pt(9)
    p_th.font.bold = True
    p_th.font.color.rgb = C_NAVY
    p_th.space_before = Pt(8)
    p_th.text = f"{'Cohort':<8}{'Linear S':<12}{'Linear +Text':<14}{'Linear Gain (Days)':<22}{'Tree Gain (Days)'}"
    
    for yr, s_mae, full_mae, lin_g, tree_g, col in bench_rows:
        pr = tf.add_paragraph()
        pr.font.name = FONT_NAME
        pr.font.size = Pt(8.5)
        pr.space_before = Pt(3)
        r1 = pr.add_run()
        r1.text = f"{yr:<8}{s_mae:<12}{full_mae:<14}{lin_g:<22}"
        r1.font.color.rgb = C_NAVY
        r2 = pr.add_run()
        r2.text = f"{tree_g}"
        r2.font.bold = True
        r2.font.color.rgb = col

    # Summary notes
    p_s1 = tf.add_paragraph()
    p_s1.font.name = FONT_NAME
    p_s1.font.size = Pt(9.5)
    p_s1.line_spacing = 1.15
    p_s1.space_before = Pt(12)
    p_s1.text = "• Linear Models Benefit from TF-IDF: Adding 500-term TF-IDF, form, and lexicon measures consistently reduces linear MAE by 0.26 to 0.39 days (median 0.293 days)."
    
    p_s2 = tf.add_paragraph()
    p_s2.font.name = FONT_NAME
    p_s2.font.size = Pt(9.5)
    p_s2.line_spacing = 1.15
    p_s2.space_before = Pt(4)
    p_s2.text = "• Tree Models Show Negligible Text Gains: Boosted trees gain only 0.001 to 0.042 days from compact text features. Non-linear trees already extract optimal context from structural fields."

    p_s3 = tf.add_paragraph()
    p_s3.font.name = FONT_NAME
    p_s3.font.size = Pt(9.5)
    p_s3.line_spacing = 1.15
    p_s3.space_before = Pt(4)
    p_s3.text = "• Geographic Uncertainty: When resampling complete country clusters, 95% bootstrap intervals cross zero in 4 of 5 linear years and 3 of 5 tree years."

    # Takeaways
    add_takeaways(slide, [
        ("Modest Linear Lift", "Text features help sparse linear models recover ~0.29 days of duration error, likely encoding missing location or programme cues."),
        ("Tree Invariance", "Modern gradient boosted trees derive almost no benefit from compact text features (+0.03d), rendering text feature engineering redundant."),
        ("Not a Causal Benefit", "A 0.29-day forecast reduction among completed loans does not mean that rewriting a loan description speeds up funding.")
    ])

    add_footnote(
        slide,
        "As-of training cohorts evaluate 728,640 records across 65 model/arm windows. S=Structure, M=Form, L=Lexicons, R=TF-IDF.",
        "Reviewed November matched benchmark (reports/text_benchmark_reviewed/)."
    )

    set_speaker_notes(slide, """PURPOSE: Present the results of our November research extension: the matched predictive text benchmark.

[Point 1: 5 Annual Cohorts] We evaluated 728,640 loans across five independent annual test cohorts from 2021 through 2025, enforcing strict as-of historical training.
[Point 2: Linear vs Tree] For sparse linear models, adding 500 TF-IDF terms reduces duration error by a modest 0.29 days. But for gradient boosted trees, text features add virtually zero gain—between 0.001 and 0.042 days.
[Point 3: Country Uncertainty] Furthermore, when we resample by country, the confidence interval spans zero in 4 out of 5 years.
[Point 4: Takeaway] Text predictive power is modest and unstable. It does not justify building complex text-rewriting systems.

TRANSITION: Let's confirm this by looking into the tree model's decision engine via SHAP values.""")


def build_slide_10_shap_importance(prs):
    """Slide 10: Feature Importance & Attribution."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)
    add_header(
        slide,
        "Predictive Attribution",
        "Gradient boosted trees rely almost exclusively on structural fields",
        "SHAP TreeExplainer attribution across 2,000 holdout loans confirms text's secondary role"
    )
    add_divider(slide)

    # Evidence Rail: Top SHAP table card
    add_card(slide, 43.5, 130, 600, 340, bg_color=C_WHITE, border_color=C_RULE)
    add_marker(slide, 58, 142, "1")
    
    box = slide.shapes.add_textbox(Pt(80), Pt(138), Pt(550), Pt(325))
    tf = box.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.font.name = FONT_NAME
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = C_BLUE
    p0.text = "Top 12 Predictive Features by Mean |SHAP Value|"
    
    shap_rows = [
        ("1. log_loan_amount", "0.4462", "Dominant driver: large loans face high friction", C_BLUE),
        ("2. lenderRepaymentTerm", "0.3373", "Capital lockup duration heavily deters lenders", C_BLUE),
        ("3. analysis_period_pre_pandemic", "0.2201", "Macro speed baseline prior to 2020", C_BLUE),
        ("4. loan_size_band_small", "0.1490", "Micro-loans (<$250) fund exceptionally fast", C_BLUE),
        ("5. sector_Retail", "0.0777", "Commerce sector penalty", C_SLATE),
        ("6. gender_female", "0.0646", "Strong platform preference for women", C_SLATE),
        ("7. period_pandemic_disruption", "0.0535", "Macro platform-wide deceleration", C_SLATE),
        ("8. region_Asia", "0.0445", "Regional volume & lender attention", C_SLATE),
        ("9. sector_Food", "0.0436", "Essential livelihood preference", C_SLATE),
        ("10. sector_Education", "0.0393", "High-priority mission sector speedup", C_SLATE),
        ("11. desc_sentiment_compound", "0.0368", "Only text feature in top ranks (weak)", C_AMBER),
        ("12. gender_male", "0.0362", "Slower funding velocity penalty", C_SLATE)
    ]
    
    p_th = tf.add_paragraph()
    p_th.font.name = FONT_NAME
    p_th.font.size = Pt(9)
    p_th.font.bold = True
    p_th.font.color.rgb = C_NAVY
    p_th.space_before = Pt(8)
    p_th.text = f"{'Rank & Feature Name':<32}{'Mean |SHAP|':<14}{'Operational Interpretation'}"
    
    for feat, val, desc, col in shap_rows:
        pr = tf.add_paragraph()
        pr.font.name = FONT_NAME
        pr.font.size = Pt(8.5)
        pr.space_before = Pt(2)
        r1 = pr.add_run()
        r1.text = f"{feat:<32}{val:<14}"
        r1.font.color.rgb = C_NAVY
        r2 = pr.add_run()
        r2.text = desc
        r2.font.bold = (col == C_AMBER)
        r2.font.color.rgb = col

    p_absent = tf.add_paragraph()
    p_absent.font.name = FONT_NAME
    p_absent.font.size = Pt(9.5)
    p_absent.font.bold = True
    p_absent.font.color.rgb = C_RED
    p_absent.space_before = Pt(10)
    p_absent.text = "Absent from Top 15: Family mentions (rank 18), Urgency (rank 24), Agency (rank 27). Narrative framing has negligible attribution in non-linear tree models."

    # Takeaways
    add_takeaways(slide, [
        ("Financial Physics", "Loan amount and repayment schedule completely dominate tree splits. How much you ask for matters far more than how you ask."),
        ("Text Absent from Top 10", "Not a single thematic narrative feature cracked the Top 10. Only generic sentiment appeared at rank 11 with weak impact."),
        ("Reconciled Evidence", "Both explanatory regression and predictive machine learning independently reach the same conclusion: structure dominates story.")
    ])

    add_footnote(
        slide,
        "TreeExplainer Shapley values computed on 2,000 holdout loan samples from 2024-2025.",
        "Authoritative GBDT model artifact (reports/generated_full_dataset/)."
    )

    set_speaker_notes(slide, """PURPOSE: Demonstrate through game-theoretic feature attribution (SHAP) that narrative features do not drive modern machine learning predictions.

[Point 1: Top Features] The top four features are all structural: loan amount, repayment term, pre-pandemic timing, and small loan tier.
[Point 2: Text Missing] All three core narrative categories—family, urgency, and agency—rank completely outside the top 15.
[Point 3: Independent Convergence] Econometric regression and machine learning attribution arrive at the exact same conclusion: structural context dominates narrative framing.

TRANSITION: Based on these unified empirical findings, what should microfinance leaders actually do?""")


def build_slide_11_strategic_recommendations(prs):
    """Slide 11: Strategic Recommendations."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)
    add_header(
        slide,
        "Strategic Implications",
        "Focus on partner operational efficiency rather than borrower copywriting",
        "Evidence-backed guidelines for Kiva management and participating microfinance institutions"
    )
    add_divider(slide)

    # 3 Strategic Action Cards on Evidence Rail
    recs = [
        ("1", "DO NOT MANDATE NARRATIVE GUIDELINES",
         "Never instruct borrowers to use 'urgent' pleas or force family references. Urgency is statistically non-significant, and forcing personal hardship narratives harms borrower dignity without improving funding velocity.",
         C_WHITE, C_RED),
        ("2", "OPTIMIZE LISTING FLOW & REDUCE CONGESTION",
         "Field partners should stagger loan submissions rather than bulk-uploading hundreds of listings simultaneously. Platform congestion during peak hours dramatically inflates funding duration.",
         C_WHITE, C_BLUE),
        ("3", "TRANCHE LARGE LOANS TO ACCELERATE VELOCITY",
         "Because funding friction scales exponentially with loan size, restructuring a $2,000 capital request into two staggered $1,000 tranches can cut total funding cycle time by more than 50%.",
         C_WHITE, C_AMBER)
    ]
    cur_y = 130
    for num, title, body, bg_col, col in recs:
        add_card(slide, 43.5, cur_y, 600, 102, bg_color=bg_col, border_color=col)
        add_marker(slide, 58, cur_y + 14, num)
        
        box = slide.shapes.add_textbox(Pt(84), Pt(cur_y + 8), Pt(545), Pt(88))
        tf = box.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.font.name = FONT_NAME
        p1.font.size = Pt(11.5)
        p1.font.bold = True
        p1.font.color.rgb = col
        p1.text = title
        
        p2 = tf.add_paragraph()
        p2.font.name = FONT_NAME
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = C_NAVY
        p2.line_spacing = 1.15
        p2.text = body
        p2.space_before = Pt(3)
        
        cur_y += 114

    # Takeaways
    add_takeaways(slide, [
        ("Protect Borrower Dignity", "Forcing borrowers to perform poverty or manufacture urgency generates zero measurable funding advantage."),
        ("Balance Sheet Velocity", "Tranching large loan requests aligns with non-linear duration elasticity, freeing up field partner liquidity far faster."),
        ("Predictive Screening", "Deploy the 24-hour classification model to identify loans at risk of stalling and route them to matching funds.")
    ])

    add_footnote(
        slide,
        "Recommendations grounded in 1,453,840 loans and verified duration elasticity.",
        "UNSW Marketing Analytics Hackathon Challenge 2026."
    )

    set_speaker_notes(slide, """PURPOSE: Translate empirical results into actionable, high-impact managerial recommendations for Kiva and microfinance partners.

[Point 1: Stop Writing Rules] First, do not burden borrowers or field officers with formulaic writing rules. Telling people to sound urgent or mention family does not work.
[Point 2: Manage Congestion] Second, field partners should smooth their listing uploads across the week rather than dumping batches that get buried.
[Point 3: Loan Tranching] Third, tranche large requests. Because duration scales non-linearly with loan size, two smaller loans fund much faster than one large loan.

TRANSITION: Before implementing any presentation changes, we establish three explicit decision gates.""")


def build_slide_12_decision_gates(prs):
    """Slide 12: Research Decision Gates & Pilot Design."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)
    add_header(
        slide,
        "Research Roadmap",
        "Three rigorous decision gates before implementing presentation interventions",
        "A disciplined research protocol to establish causal proof and prevent unintended harm"
    )
    add_divider(slide)

    gates = [
        ("1", "GATE 1: CONSTRUCT VALIDATION",
         "Dual-code narrative text against verified codebooks to confirm what TF-IDF and dictionaries actually measure. Separate partner writing templates from genuine borrower voice.",
         C_PALE_BLUE, C_BLUE),
        ("2", "GATE 2: PROCESS & EXPOSURE AUDIT",
         "Acquire true partner identifiers, homepage placement logs, and expired/unfunded listings to eliminate unobserved platform exposure confounding.",
         C_WHITE, C_NAVY),
        ("3", "GATE 3: PRE-REGISTERED A/B PILOT",
         "Partner with 3-5 willing microfinance institutions to run a randomized trial testing factual clarity changes, measuring lender attention displacement across all listings.",
         C_PALE_AMBER, C_AMBER)
    ]
    cur_y = 130
    for num, title, body, bg_col, col in gates:
        add_card(slide, 43.5, cur_y, 600, 102, bg_color=bg_col, border_color=col)
        add_marker(slide, 58, cur_y + 14, num)
        
        box = slide.shapes.add_textbox(Pt(84), Pt(cur_y + 8), Pt(545), Pt(88))
        tf = box.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.font.name = FONT_NAME
        p1.font.size = Pt(11.5)
        p1.font.bold = True
        p1.font.color.rgb = col
        p1.text = title
        
        p2 = tf.add_paragraph()
        p2.font.name = FONT_NAME
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = C_NAVY
        p2.line_spacing = 1.15
        p2.text = body
        p2.space_before = Pt(3)
        
        cur_y += 114

    # Takeaways
    add_takeaways(slide, [
        ("No Premature Rollout", "Never deploy automated text-generation or rewriting tools until Gate 3 proves causal efficacy in a live randomized trial."),
        ("Cannibalization Risk", "Evaluate whether making one loan fund faster merely steals lender dollars from an equally deserving borrower nearby."),
        ("Evidence-First Culture", "Advance from one gate to the next only when explicit uncertainty hurdles are successfully cleared.")
    ])

    add_footnote(
        slide,
        "Research sequence follows consulting problem solving and AEA pre-registration evaluation standards.",
        "docs/4_research_review.md and docs/5_ml_refinement_plan.md."
    )

    set_speaker_notes(slide, """PURPOSE: Conclude the main deck with a structured decision-gate framework to guide future investments.

[Point 1: Gate 1] Before building any AI text tools, validate what the text measures by independently coding descriptions.
[Point 2: Gate 2] Obtain exposure logs and unfunded listings to control for platform promotion.
[Point 3: Gate 3] Run a pre-registered randomized field trial with partner organizations, carefully measuring whether speeding up one loan cannibalizes funding from other borrowers.
[Point 4: Conclusion] By pairing rigorous econometrics with machine learning, we replace storytelling mythology with actionable operational science.

TRANSITION: The remaining slides provide our technical appendix, detailing data integrity, cohort accounting, and methodological boundaries.""")


def build_slide_13_appendix_population(prs):
    """Slide 13: Appendix: Dataset Provenance & Exclusions."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)
    add_header(
        slide,
        "Technical Appendix",
        "Data filtering preserves 99.999% of raw records with complete integrity",
        "Full audit trail from 1,453,846 raw records to 1,453,840 eligible completed durations"
    )

    # Full width table card
    add_card(slide, 43.5, 130, 873, 340, bg_color=C_WHITE, border_color=C_RULE)
    
    box = slide.shapes.add_textbox(Pt(60), Pt(140), Pt(840), Pt(320))
    tf = box.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.font.name = FONT_NAME
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = C_BLUE
    p0.text = "Data Pipeline Accounting & Population Summary"
    
    audit_rows = [
        ("Raw Input Records", "1,453,846", "Initial Kaggle / Kiva export across 2016-2025; 27 raw columns."),
        ("Excluded Negative Durations", "6", "Dropped because raisedDate preceded fundraisingDate (corrupted timestamps)."),
        ("Eligible Completed Durations", "1,453,840", "Primary analysis population. Retains 1,637 refunded records with valid durations."),
        ("Missing Descriptions", "39,088", "2.69% of records carry blank descriptions. They fund faster (median 1.81d vs 2.88d) due to group size."),
        ("Chronological Train Cohort", "1,174,953", "Loans posted from 2016-01-01 to 2023-12-31 used for model training."),
        ("Chronological Holdout Cohort", "278,887", "Loans posted from 2024-01-01 to 2025-06-30 strictly held out for final evaluation."),
        ("Duplicate Loan IDs", "0", "Verified unique primary key; no duplicate loans exist in the dataset.")
    ]
    
    p_th = tf.add_paragraph()
    p_th.font.name = FONT_NAME
    p_th.font.size = Pt(9.5)
    p_th.font.bold = True
    p_th.font.color.rgb = C_NAVY
    p_th.space_before = Pt(8)
    p_th.text = f"{'Pipeline Step':<32}{'Record Count':<16}{'Description & Methodological Rationale'}"
    
    for step, cnt, desc in audit_rows:
        pr = tf.add_paragraph()
        pr.font.name = FONT_NAME
        pr.font.size = Pt(9)
        pr.space_before = Pt(4)
        r1 = pr.add_run()
        r1.text = f"{step:<32}{cnt:<16}"
        r1.font.bold = True
        r1.font.color.rgb = C_NAVY
        r2 = pr.add_run()
        r2.text = desc
        r2.font.color.rgb = C_GREY

    add_footnote(
        slide,
        "Authoritative tested pipeline generated 2026-08-31 (reports/generated_full_dataset/analysis_summary.json).",
        "Exclusion of 6 corrupted records vetted under contract tests."
    )

    set_speaker_notes(slide, """PURPOSE: Document the full data provenance and exact record accounting for peer review.
All data transformations are fully reproducible via tests/test_notebook_contract.py.""")


def build_slide_14_appendix_cohorts(prs):
    """Slide 14: Appendix: As-of Training & Annual Cohort Accounting."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)
    add_header(
        slide,
        "Technical Appendix",
        "Retrospective as-of training removes future completion leakage",
        "Accounting for 728,640 evaluation records across five annual cohorts (2021–2025)"
    )

    add_card(slide, 43.5, 130, 873, 340, bg_color=C_WHITE, border_color=C_RULE)
    
    box = slide.shapes.add_textbox(Pt(60), Pt(140), Pt(840), Pt(320))
    tf = box.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.font.name = FONT_NAME
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = C_BLUE
    p0.text = "Annual Cohort Availability Audit (reports/text_benchmark_reviewed/)"
    
    cohort_rows = [
        ("2021", "717,672", "7,528", "163,166", "+0.293d [0.20, 0.38]", "+0.035d [-0.07, 0.14]"),
        ("2022", "884,448", "3,918", "143,354", "+0.372d [0.21, 0.52]", "+0.028d [-0.04, 0.08]"),
        ("2023", "1,028,174", "3,546", "143,233", "+0.259d [0.09, 0.41]", "+0.006d [-0.02, 0.04]"),
        ("2024", "1,169,262", "5,691", "141,725", "+0.389d [0.29, 0.50]", "+0.001d [-0.02, 0.03]"),
        ("2025", "1,312,417", "4,261", "137,162", "+0.260d [0.14, 0.40]", "+0.042d [0.01, 0.07]"),
        ("Total / Median", "Expanding", "24,944 Excluded", "728,640 Evaluated", "+0.293d Median Gain", "+0.028d Median Gain")
    ]
    
    p_th = tf.add_paragraph()
    p_th.font.name = FONT_NAME
    p_th.font.size = Pt(9.5)
    p_th.font.bold = True
    p_th.font.color.rgb = C_NAVY
    p_th.space_before = Pt(8)
    p_th.text = f"{'Cohort':<8}{'Training Set':<16}{'Pre-Cutoff Excluded':<22}{'Evaluation Set':<16}{'Linear MAE Gain':<22}{'Tree MAE Gain'}"
    
    for yr, tr, exc, ev, lg, tg in cohort_rows:
        pr = tf.add_paragraph()
        pr.font.name = FONT_NAME
        pr.font.size = Pt(9)
        pr.space_before = Pt(4)
        r = pr.add_run()
        r.text = f"{yr:<8}{tr:<16}{exc:<22}{ev:<16}{lg:<22}{tg}"
        r.font.bold = (yr == "Total / Median")
        r.font.color.rgb = C_BLUE if yr == "Total / Median" else C_NAVY

    p_expl = tf.add_paragraph()
    p_expl.font.name = FONT_NAME
    p_expl.font.size = Pt(9.5)
    p_expl.line_spacing = 1.15
    p_expl.space_before = Pt(14)
    p_expl.text = "Methodological Safeguard: Loans posted before January 1 of each evaluation year that had not yet completed funding by that date are strictly excluded from the training set. This prevents future completion outcome leakage into historical training histories."

    add_footnote(
        slide,
        "Availability audit published in reports/text_benchmark_reviewed/availability_audit.json.",
        "65 model/arm windows evaluated across 2021-2025."
    )

    set_speaker_notes(slide, """PURPOSE: Document the as-of training availability audit and explain how completion leakage was eliminated.
In 2024, for example, 5,691 loans had been posted before the cutoff but completed after; excluding them guarantees strict historical integrity.""")


def build_slide_15_appendix_metrics(prs):
    """Slide 15: Appendix: Metric Divergence & Calibration."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)
    add_header(
        slide,
        "Technical Appendix",
        "Performance metrics diverge across linear and tree model families",
        "Day-space R², MAE, ROC AUC, and Brier score capture distinct predictive dimensions"
    )

    add_card(slide, 43.5, 130, 873, 340, bg_color=C_WHITE, border_color=C_RULE)
    
    box = slide.shapes.add_textbox(Pt(60), Pt(140), Pt(840), Pt(320))
    tf = box.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.font.name = FONT_NAME
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = C_BLUE
    p0.text = "Multi-Metric Model Comparison on 2025 Evaluation Cohort (137,162 Loans)"
    
    m_rows = [
        ("Linear S (Structure only)", "6.406 days", "-0.4189", "0.8931", "0.1598", "Baseline linear benchmark"),
        ("Linear S+M+L+R (Full text)", "6.147 days", "-0.3147", "0.8883", "0.1446", "MAE & Brier improve; AUC declines"),
        ("GBDT S (Structure only)", "4.875 days", "+0.4644", "0.9091", "0.1274", "Outperforms all linear text models"),
        ("GBDT S+M+L (Structure + Text)", "4.833 days", "+0.4765", "0.9083", "0.1270", "Negligible text gain (+0.04d MAE)")
    ]
    
    p_th = tf.add_paragraph()
    p_th.font.name = FONT_NAME
    p_th.font.size = Pt(9.5)
    p_th.font.bold = True
    p_th.font.color.rgb = C_NAVY
    p_th.space_before = Pt(8)
    p_th.text = f"{'Model Specification':<32}{'MAE (Days)':<14}{'Day-Space R²':<16}{'ROC AUC':<12}{'Brier Score'}"
    
    for spec, mae, r2, auc, br, desc in m_rows:
        pr = tf.add_paragraph()
        pr.font.name = FONT_NAME
        pr.font.size = Pt(9)
        pr.space_before = Pt(4)
        r = pr.add_run()
        r.text = f"{spec:<32}{mae:<14}{r2:<16}{auc:<12}{br:<14}"
        r.font.bold = ("GBDT" in spec)
        r.font.color.rgb = C_BLUE if "GBDT" in spec else C_NAVY

    p_disc = tf.add_paragraph()
    p_disc.font.name = FONT_NAME
    p_disc.font.size = Pt(9.5)
    p_disc.line_spacing = 1.15
    p_disc.space_before = Pt(14)
    p_disc.text = "Key Insight on Metric Divergence: In linear models, adding text features improves duration MAE by 0.26 days and improves probability calibration (Brier score from 0.1598 to 0.1446), yet ROC AUC ranking discrimination actually drops from 0.8931 to 0.8883. Optimizing for ranking does not guarantee calibrated duration forecasts."

    add_footnote(
        slide,
        "Evaluated on 137,162 completed loans in the 2025 retrospective cohort.",
        "reports/text_benchmark_reviewed/benchmark.json."
    )

    set_speaker_notes(slide, """PURPOSE: Show technical reviewers how different machine learning evaluation metrics interact and why AUC alone is misleading.""")


def build_slide_16_appendix_boundaries(prs):
    """Slide 16: Appendix: Limitations & Research Boundaries."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide, C_CREAM)
    add_header(
        slide,
        "Technical Appendix",
        "Transparent boundary conditions and methodological guardrails",
        "Explicit documentation of study limits to ensure responsible academic and industry reuse"
    )

    # 4 boundary cards in a 2x2 grid
    bounds = [
        ("1. Observational Inference Boundary",
         "The dataset records observational platform transactions, not an experimental intervention. Borrowers are not randomly assigned loan amounts, repayment terms, or narrative framing. Coefficients represent conditional associations, never causal effects.",
         C_PALE_BLUE, C_BLUE),
        ("2. Conditioning on Successful Completion",
         "The analytical population comprises listings that completed funding. Unfunded and expired listings (which Kiva historically purged or restricted) are absent. Findings describe funding velocity among funded loans, not overall listing survival probability.",
         C_WHITE, C_NAVY),
        ("3. Unvalidated Programme Text Proxy",
         "The whySpecial field reflects platform-generated tag text, not verified partner identities. Controlling for programme text introduces unvalidated proxies that must not be interpreted as field partner fixed effects.",
         C_WHITE, C_SLATE),
        ("4. Welfare & Liquidity Disconnection",
         "Because 96.4% of loans are pre-disbursed locally, platform funding velocity measures partner balance sheet liquidity replenishment. It does not measure borrower waiting time, poverty alleviation, or household economic welfare.",
         C_PALE_AMBER, C_AMBER)
    ]
    coords = [
        (43.5, 130, 426, 160),
        (490.5, 130, 426, 160),
        (43.5, 302, 426, 160),
        (490.5, 302, 426, 160)
    ]
    for (title, body, bg_col, col), (x, y, w, h) in zip(bounds, coords):
        add_card(slide, x, y, w, h, bg_color=bg_col, border_color=col)
        
        box = slide.shapes.add_textbox(Pt(x + 14), Pt(y + 12), Pt(w - 28), Pt(h - 24))
        tf = box.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.font.name = FONT_NAME
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = col
        p1.text = title
        
        p2 = tf.add_paragraph()
        p2.font.name = FONT_NAME
        p2.font.size = Pt(9)
        p2.font.color.rgb = C_NAVY
        p2.line_spacing = 1.15
        p2.text = body
        p2.space_before = Pt(4)

    add_footnote(
        slide,
        "Formal methodological bounds documented in docs/2_evidence_and_corrections.md and docs/6_matched_text_results.md.",
        "Ethical and scientific transparency standards."
    )

    set_speaker_notes(slide, """PURPOSE: Conclude the appendix by clearly stating all research boundaries, ensuring that future teams do not over-claim causal impact.""")


# =============================================================================
# Main Execution
# =============================================================================

def main():
    print(f"Building refined presentation deck: {OUTPUT_PPTX}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    prs = create_deck()
    
    # 12 Core Slides + 4 Technical Appendix Slides
    build_slide_1_cover(prs)
    build_slide_2_executive_summary(prs)
    build_slide_3_context_timeline(prs)
    build_slide_4_issue_tree(prs)
    build_slide_5_structural_dominance(prs)
    build_slide_6_demographic_shifts(prs)
    build_slide_7_clustered_sensitivity(prs)
    build_slide_8_regional_nuance(prs)
    build_slide_9_predictive_benchmark(prs)
    build_slide_10_shap_importance(prs)
    build_slide_11_strategic_recommendations(prs)
    build_slide_12_decision_gates(prs)
    build_slide_13_appendix_population(prs)
    build_slide_14_appendix_cohorts(prs)
    build_slide_15_appendix_metrics(prs)
    build_slide_16_appendix_boundaries(prs)
    
    prs.save(str(OUTPUT_PPTX))
    print(f"Successfully generated {len(prs.slides)} slides in {OUTPUT_PPTX}!")


if __name__ == "__main__":
    main()
