#!/usr/bin/env python3
"""Regenerate docs/presentation/slides_draft.pptx from the deck brief content.

Single source of truth for the editable draft deck: slide content, big-number
callouts, chart placeholders (named after the notebook section to screenshot)
and the timed speaker scripts (as presenter notes). Design mirrors the deck
brief page: warm paper ground, deep teal + amber accent, Georgia display type.
Re-run after any wording change: python3 scripts/build_slides_draft.py
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pathlib import Path
import os

# Slide -> chart image (extracted from the Kaggle-executed notebooks; the
# few-cluster table is typeset from the verified v15 SS7.2 output). Override
# with CHART_DIR env var; missing files fall back to the labelled placeholder.
CHART_DIR = os.environ.get("CHART_DIR", "docs/presentation/charts")
CHARTS = {
    3: "mod_21.png",            # predicted vs actual, chronological holdout
    4: "eda_17_right.png",      # 24h-funded share by period (cropped panel)
    5: "eda_22.png",            # average funding speed by sector
    6: "few_cluster_table.png", # SS7.2 within-region few-cluster screen
    7: "eda_32.png",            # funding speed by dominant topic
    12: "eda_23.png",           # appendix: region + repayment speed panels
    13: "mod_39.png",           # appendix: SHAP top-15
    14: "eda_36.png",           # appendix: speed by loan-amount decile
}

PAPER = RGBColor(0xFA, 0xF7, 0xF0); INK = RGBColor(0x1E, 0x2A, 0x2F)
TEAL = RGBColor(0x1F, 0x4E, 0x5F); CREAM = RGBColor(0xFA, 0xF7, 0xF0)
AMBER = RGBColor(0xC9, 0x7B, 0x3D); MUTED = RGBColor(0x6E, 0x6A, 0x5E)
PANEL = RGBColor(0xF1, 0xEB, 0xDF); LINE = RGBColor(0xDC, 0xD3, 0xC0)
DISPLAY = "Georgia"; BODY = "Avenir Next"; MONO = "Courier New"

SLIDES = [
 ("Beyond a Good Story",
  "When — and for whom — does persuasive loan language actually speed up funding?",
  None, ["Team Cultural Blend  ·  Kiva loan data  ·  1.45 million real loans (2016–2025)"], None,
  "Good morning — we're Cultural Blend. Kiva is built on stories: every loan page leads with one. So we asked a simple question of 1.45 million real loans: does the story actually move the money?",
  "UNSW MARKETING ANALYTICS HACKATHON · FINAL"),
 ("The question", None, None,
  ["When a loan's story leans on family, competence, or urgency — does it fund faster?",
   "Does the answer depend on WHO is asking and WHEN?",
   "Why it matters: framing is the one thing a platform can coach — loan size, sector and geography can't be rewritten after the fact."],
  None,
  "Specifically: when a borrower's story leans on family, on competence, on urgency — does the loan fund faster? And does the answer depend on who's asking, and when? We care because language is the one thing a platform can coach. You can't rewrite a loan's size, sector, or country after the fact — but you could suggest better words. IF words work. That's the claim we set out to test, not assume.",
  "MOTIVATION"),
 ("How we stress-tested our findings", None, None,
  ["Predictive claims: trained only on the past, tested only on loans posted 2024–2025 — no peeking at the future.",
   "Framing claims: every 'significant' result re-tested with country-clustered standard errors, then a harsher few-cluster reference where a result rests on a handful of countries.",
   "Most headline-looking results did NOT survive — that is the point of the method.",
   "SHAP importance shown as complementary predictive evidence only — it cannot confirm or refute a statistical finding."],
  "modeling notebook §4 data split · §7.1 cluster-robust check",
  "Two disciplines before any findings. For prediction, we train only on the past and test only on loans posted in 2024–25 — no peeking at the future. For the framing claims, every 'significant' result had to survive re-testing: first with standard errors clustered by country, so ten thousand loans from one country can't masquerade as ten thousand independent pieces of evidence — and where a result rested on just a couple of countries, a deliberately harsher few-cluster reference on top. Most headline-looking results did not survive. That's the point: we'd rather lose a finding than present a fluke.",
  "METHOD"),
 ("A marketplace that hasn't recovered", None,
  "46% → 30% → 30%|funded within 24 hours",
  ["Pre-pandemic, almost half of all loans funded within a day.",
   "Since 2020: under a third — and through the end of the data (2025) it has NOT recovered. Persistence to date, not proof it never will.",
   "589,823 loans before vs. 565,474 after — not a small, noisy sample."],
  "EDA notebook §4 categorical trends (period chart)",
  "Before the pandemic, almost half of Kiva loans — 46% — funded within 24 hours. Since 2020, it's been under a third — and through the end of our data in 2025 it has not recovered. That's more than half a million loans on each side of the divide, so this isn't noise. Every result we show next lives inside this slower, tighter marketplace — lenders are more selective now, which makes knowing what actually drives speed more valuable, not less.",
  "FINDING 1 · THE MARKET"),
 ("Structure beats story", None,
  "2.3 vs 7.7 days|median funding speed — female- vs male-posted loans",
  ["Loan amount + repayment terms: linked to funding speed ~10x more strongly than any single narrative choice.",
   "Sector alone spans well over an order of magnitude in speed; region shows similarly large gaps.",
   "None of this is causal — but it dwarfs anything the words do."],
  "EDA notebook §5 categorical features · §9 feature correlations",
  "So what does drive speed? Structure. Loan amount and repayment terms are associated with funding speed roughly ten times more strongly than any single narrative choice. Sector alone spans more than an order of magnitude. And the starkest gap in the data: loans posted by women fund in a median of 2.3 days; by men, 7.7 — more than three times longer. None of this is causal — but the pattern is enormous, it's stable, and it dwarfs anything the words do.",
  "FINDING 2 · STRUCTURE"),
 ("What survives scrutiny", None,
  "No narrative result|is robust enough to support a recommendation",
  ["Urgency: looked universal (p<0.001) — collapses under country clustering (p≈0.44). Not recommended.",
   "Family: corrected test → Middle East (Palestine+Yemen) & Central America (Honduras+Nicaragua) same direction in every fit — but 2 countries each; few-cluster t(1) screen bar is 12.7, not 1.96: p≈0.06–0.21. A hypothesis, not a finding.",
   "Sentiment: positive tone <-> slower funding, but significance flips between specifications — genuinely open.",
   "SHAP: no family / agency / urgency feature in the model's top 15 — complementary evidence, not confirmation."],
  "modeling notebook §7.2 within-region slopes · §7.1 check",
  "Now the question we came to answer — and the honest answer is that nothing about the narrative survives our own scrutiny. Urgency language looked like a clean, universal win: significant at p<0.001. Cluster by country, and it collapses to p≈0.44. Gone. Family framing — here our own first version got it wrong: we tested whether regions differ from Africa, which is not the same as whether family framing helps WITHIN a region. Corrected, two pooled categories — Palestine+Yemen, and Honduras+Nicaragua — do show faster funding in every fit we ran. But each rests on exactly two countries, and against a deliberately harsh few-cluster screen — a t distribution with one degree of freedom, where the critical value is 12.7, not 1.96 — neither is significant: p between 0.06 and 0.21. So we report it as a hypothesis worth testing, not a finding. Sentiment tone: more positive language associates with SLOWER funding, but its significance flips between our two specifications — we call it open. We'd rather report no robust evidence than one exciting result we can't defend.",
  "FINDING 3 · THE HEADLINE"),
 ("Beyond keywords", None,
  "1.5 → 13.5 days|across story topics — a >9x swing",
  ["Topic modeling (NMF, 5 topics — not keyword counts) surfaces coherent themes: livestock, health & sanitation, clean water, farming, retail.",
   "The largest single gap anywhere in the analysis — but a topic mostly encodes what the loan is FOR. Structure again, not persuasion."],
  "EDA notebook §8 topic modeling",
  "We also went beyond keyword counting. Topic modeling finds coherent themes in the stories — livestock, health and sanitation, clean water, farming, retail — and funding speed swings ninefold across them, from a day and a half to nearly two weeks. But notice what a topic mostly encodes: what the loan is FOR. Which is structure again — not persuasion.",
  "FINDING 4 · TOPICS"),
 ("What this means in practice", None, None,
  ["DON'T ship writing tips — a platform-wide 'add urgency' nudge would be built on a result that doesn't survive testing.",
   "DO run a country-stratified A/B test of family framing in exactly those 4 markets — that's how a hypothesis becomes a decision.",
   "DO review the structural gaps (sector / region / gender) — they are ~10x the size of any wording effect.",
   "PROTOTYPE, then re-validate: the 24h classifier ranks well among eventually-funded loans (AUC ≈ 0.90, strictly future data) — but expired/withdrawn listings aren't in the data, so an early-warning flag first needs all posted listings, a defined target, and retraining on that population."],
  None,
  "So what should Kiva actually do? Three things. First — don't ship writing tips. A platform-wide 'add urgency' nudge would be built on a result that doesn't survive testing. The family-framing pattern deserves a country-stratified A/B test in exactly those four markets: that's how a hypothesis becomes a decision, and it's cheap to run. Second — the structural gaps are where the real levers are: review how the consistently slower sectors and regions are surfaced, bundled, and supported, because those gaps are ten times the size of any wording effect. Third — speed is predictable in retrospect: among loans that eventually funded, our classifier ranks same-day funding at AUC 0.90 on strictly future data, without any framing features. One honest boundary: expired or withdrawn listings never enter this data, so that is a ranking prototype among eventual funders — not yet an early-warning system. To build one, Kiva should pull all posted listings including expired and withdrawn outcomes, define the operational target, and retrain and validate on that population — before any pilot.",
  "RECOMMENDATIONS"),
 ("What this can't tell us", None, None,
  ["Association, never causation — no borrower was randomly assigned a writing style.",
   "Measures how fast a FUNDED loan funds — not whether a loan gets funded at all (expired/withdrawn listings never enter the data).",
   "Framing measured with transparent, simple rules — not every nuance of persuasive writing."],
  None,
  "Three honest limits. This is association, never causation — no borrower was randomly assigned a writing style. We measure how fast funded loans fund — not whether a loan funds at all. And our framing measures are transparent, simple rules — they don't capture every nuance of persuasion. We'd rather you know exactly what this analysis can and cannot say — that's what makes the parts we do claim worth trusting.",
  "LIMITS"),
 ("", None, None, [], None,
  "In this data, the story barely registers — the structure carries the signal. And testing hard enough to KNOW that is worth more to a platform than a good-sounding tip. Thank you — we're happy to take questions.",
  "CLOSING"),
 # ---- Appendix: Q&A backup, never presented in the 10 minutes ----
 ("Appendix", "Q&A backup — not part of the 10-minute presentation.", None, [], None,
  "Divider only. Everything after this slide exists to be pulled up during Q&A if a question calls for it.",
  "APPENDIX"),
 ("The two-country problem, in full", None, None,
  ["Pooled categories: Middle East = Palestine + Yemen (14,946 loans); Central America = Honduras + Nicaragua (59,391); North America = Haiti alone.",
   "Few-cluster screen p (duration / 24h / notebook fit): ME 0.12 / 0.21 / 0.08 · CA 0.06 / 0.14 / 0.07 — same direction in every fit, none significant; t(1) critical value 12.7.",
   "North America: single country — between-country uncertainty not estimable at all.",
   "The screen is a conservative heuristic: it can downgrade a claim, never certify one. Next step: country-stratified A/B test in those four markets."],
  "EDA notebook §5 · regional speed context for the pooled categories",
  "Backup for Slide 6 probes: exact pooled definitions, all p-values, the single-country boundary, and the honest status of the screen.",
  "APPENDIX · A1"),
 ("Predictive weight ≠ statistical robustness", None, None,
  ["SHAP importance from the boosted forecasting model: structure fills the top ranks (amount, term, period, size band, sector, gender).",
   "No family, agency, or urgency feature reaches the top 15; sentiment is 11th despite its disputed significance.",
   "Complementary predictive evidence only — a different model, no region interactions; it cannot confirm or refute any coefficient's sign or uncertainty."],
  "modeling notebook §8 · SHAP top-15",
  "Backup for SHAP questions: what the ranking shows, and exactly what it cannot corroborate.",
  "APPENDIX · A2"),
 ("Structure, dose-response", None, None,
  ["Funding speed rises almost monotonically across loan-amount deciles — small asks fund in ~2 days, the largest in ~18.",
   "Gender: female-posted median 2.3 days vs male 7.7 (the duration-model male coefficient +0.430 survives HC3 AND country clustering, p < 0.0001 — still associational).",
   "This dose-response pattern is what the '~10x stronger than narrative' comparison rests on."],
  "EDA notebook §9 · speed by loan-amount decile",
  "Backup for Slide 5 probes: the amount gradient and the gender gap's robustness status.",
  "APPENDIX · A3"),
 ("24h classifier — operating detail", None, None,
  ["Holdout (posted 2024-01-01 onward): 278,887 loans; 87,466 funded within 24h vs 191,421 not.",
   "ROC AUC 0.8997 · average precision 0.8301 · Brier 0.1156 · accuracy 0.840 — no narrative features needed.",
   "Boundary: negative class = 'eventually funded, but not within 24h'. Expired/withdrawn listings never enter the data — a retrospective ranking prototype among eventual funders.",
   "Path to deployment: all posted listings incl. expired/withdrawn outcomes -> define operational target + censoring window -> retrain, validate -> threshold, calibration, fairness, prospective test."],
  None,
  "Backup for classifier questions: exact metrics, class balance, and the population boundary stated before anyone asks.",
  "APPENDIX · A4"),
]


def build(out_path: str) -> None:
    prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    def bg(slide, color):
        slide.background.fill.solid(); slide.background.fill.fore_color.rgb = color

    def box(slide, x, y, w, h):
        b = slide.shapes.add_textbox(x, y, w, h); b.text_frame.word_wrap = True
        return b.text_frame

    def style(p, size, color, font=BODY, bold=False, italic=False, align=None):
        p.font.size = Pt(size); p.font.color.rgb = color; p.font.name = font
        p.font.bold = bold; p.font.italic = italic
        if align: p.alignment = align

    def rect(slide, x, y, w, h, fill, line=None, rounded=False):
        sh = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, x, y, w, h)
        sh.fill.solid(); sh.fill.fore_color.rgb = fill
        if line: sh.line.color.rgb = line; sh.line.width = Pt(0.75)
        else: sh.line.fill.background()
        sh.shadow.inherit = False
        return sh

    for i, (title, sub_, big, bullets, chart, script, eyebrow) in enumerate(SLIDES, 1):
        sl = prs.slides.add_slide(blank)
        bg(sl, TEAL if i in (1, 10, 11) else PAPER)
        if i == 11:
            rect(sl, Inches(0.9), Inches(3.0), Inches(1.6), Pt(4), AMBER)
            tf = box(sl, Inches(0.9), Inches(3.25), Inches(11.5), Inches(1.2))
            tf.text = title; style(tf.paragraphs[0], 54, CREAM, DISPLAY, bold=True)
            tf = box(sl, Inches(0.9), Inches(4.5), Inches(11.5), Inches(0.6))
            tf.text = sub_; style(tf.paragraphs[0], 18, RGBColor(0xB8, 0xCE, 0xD6), BODY, italic=True)
        elif i == 1:
            rect(sl, Inches(0.9), Inches(2.05), Inches(1.6), Pt(4), AMBER)
            tf = box(sl, Inches(0.9), Inches(1.35), Inches(11.5), Inches(0.5))
            tf.text = eyebrow; style(tf.paragraphs[0], 13, AMBER, MONO)
            tf = box(sl, Inches(0.85), Inches(2.3), Inches(11.8), Inches(2.2))
            tf.text = title; style(tf.paragraphs[0], 66, CREAM, DISPLAY, bold=True)
            tf = box(sl, Inches(0.9), Inches(4.35), Inches(9.8), Inches(1.2))
            tf.text = sub_; style(tf.paragraphs[0], 22, RGBColor(0xB8, 0xCE, 0xD6), BODY, italic=True)
            tf = box(sl, Inches(0.9), Inches(6.3), Inches(11.5), Inches(0.6))
            tf.text = bullets[0]; style(tf.paragraphs[0], 15, RGBColor(0x8F, 0xB0, 0xBB), MONO)
        elif i == 10:
            rect(sl, Inches(5.87), Inches(1.7), Inches(1.6), Pt(4), AMBER)
            tf = box(sl, Inches(1.2), Inches(2.5), Inches(10.9), Inches(2.6))
            for j, line in enumerate(["“The story barely registers.", "The structure carries the signal.”"]):
                p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
                p.text = line; style(p, 42, CREAM, DISPLAY, bold=True, align=PP_ALIGN.CENTER)
            tf = box(sl, Inches(1.2), Inches(5.3), Inches(10.9), Inches(0.7))
            tf.text = "Thank you — questions."
            style(tf.paragraphs[0], 20, RGBColor(0xB8, 0xCE, 0xD6), BODY, align=PP_ALIGN.CENTER)
            tf = box(sl, Inches(1.2), Inches(6.9), Inches(10.9), Inches(0.4))
            tf.text = "Team Cultural Blend · UNSW Marketing Analytics Hackathon 2026"
            style(tf.paragraphs[0], 12, RGBColor(0x8F, 0xB0, 0xBB), MONO, align=PP_ALIGN.CENTER)
        else:
            tf = box(sl, Inches(0.75), Inches(0.42), Inches(9.0), Inches(0.35))
            tf.text = eyebrow; style(tf.paragraphs[0], 11.5, AMBER, MONO)
            chip = rect(sl, Inches(12.15), Inches(0.4), Inches(0.72), Inches(0.38), TEAL, rounded=True)
            ctf = chip.text_frame; ctf.text = f"{i}/10" if i <= 10 else f"A{i - 11}"
            ctf.margin_top = Emu(0); ctf.margin_bottom = Emu(0)
            style(ctf.paragraphs[0], 12, CREAM, MONO, align=PP_ALIGN.CENTER)
            ctf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = box(sl, Inches(0.7), Inches(0.78), Inches(11.3), Inches(1.0))
            tf.text = title; style(tf.paragraphs[0], 36, INK, DISPLAY, bold=True)
            rect(sl, Inches(0.75), Inches(1.62), Inches(1.35), Pt(3.5), AMBER)
            y = 1.95
            if big:
                num, label = big.split("|")
                tf = box(sl, Inches(0.75), Inches(y), Inches(12.1), Inches(1.0))
                p = tf.paragraphs[0]; p.text = num.strip() + "  "
                style(p, 40, AMBER, DISPLAY, bold=True)
                r = p.add_run(); r.text = label.strip()
                r.font.size = Pt(16); r.font.color.rgb = MUTED; r.font.name = BODY; r.font.bold = False
                y += 1.15
            img = None
            if chart and CHART_DIR and i in CHARTS:
                cand = Path(CHART_DIR) / CHARTS[i]
                if cand.is_file():
                    img = cand
            bw = 12.1 if not chart else 7.35
            tf = box(sl, Inches(0.75), Inches(y), Inches(bw), Inches(6.9 - y))
            for j, item in enumerate(bullets):
                p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
                r1 = p.add_run(); r1.text = "▪  "; r1.font.color.rgb = AMBER; r1.font.size = Pt(16); r1.font.name = BODY
                r2 = p.add_run(); r2.text = item; r2.font.size = Pt(16.5); r2.font.color.rgb = INK; r2.font.name = BODY
                p.space_after = Pt(12); p.line_spacing = 1.15
            if chart and img is not None:
                # right-column exhibit: fit to 4.45in wide, cap height, centre
                pic = sl.shapes.add_picture(str(img), Inches(8.2), Inches(y), width=Inches(4.45))
                max_h = Inches(6.7 - y)
                if pic.height > max_h:
                    ratio = max_h / pic.height
                    pic.height = int(max_h)
                    pic.width = int(pic.width * ratio)
                    pic.left = Inches(8.2) + (Inches(4.45) - pic.width) // 2
                cap = box(sl, Inches(8.2), Inches(6.75), Inches(4.6), Inches(0.3))
                cap.text = chart
                style(cap.paragraphs[0], 8.5, MUTED, MONO)
            elif chart:
                ph = rect(sl, Inches(9.2), Inches(y), Inches(3.5), Inches(6.55 - y), PANEL, line=LINE, rounded=True)
                ptf = ph.text_frame; ptf.word_wrap = True; ptf.vertical_anchor = MSO_ANCHOR.MIDDLE
                ptf.text = "CHART GOES HERE"
                style(ptf.paragraphs[0], 13, TEAL, MONO, bold=True, align=PP_ALIGN.CENTER)
                p2 = ptf.add_paragraph(); p2.text = "\nscreenshot from:\n" + chart
                style(p2, 11, MUTED, BODY, align=PP_ALIGN.CENTER)
            tf = box(sl, Inches(0.75), Inches(7.05), Inches(9.0), Inches(0.35))
            tf.text = "Cultural Blend · Kiva 2016–2025 · 1.45M loans"
            style(tf.paragraphs[0], 10, MUTED, MONO)
        sl.notes_slide.notes_text_frame.text = script
    prs.save(out_path)
    print("wrote", out_path, Path(out_path).stat().st_size, "bytes")


if __name__ == "__main__":
    build("docs/presentation/slides_draft.pptx")
