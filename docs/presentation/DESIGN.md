# Slide Deck Design Standard

**Project:** UNSW Marketing Analytics Hackathon Challenge 2026  
**Team:** Cultural Blend (1 of 8 Finalist Teams)  
**Status:** Official living design standard, reconciled with the signature presentation deck (`Team Cultural Blend - UNSW Hackathon 2026.v3`) and Project 15 / `aipa-text-to-sql-agent` principles.

---

## 1. Authority and Visual Identity

This document defines the visual grammar, spatial layout, typography, and color palette of the official presentation deck for the Kiva loan funding speed investigation (*Beyond a Good Story: When and for Whom Loan Narratives Are Linked to Faster Prosocial Funding*).

- The visual identity is anchored in the team's signature **Bright Yellow & Deep Navy/Teal** Google Slides theme.
- The standard slide canvas is **16:9 widescreen** (Inches 13.333 × 7.5, or **960 × 540 pt**).
- Evidence must strictly distinguish the **primary August snapshot** (1,453,840 eligible records), the **reviewed October inference extension** (country-clustered standard errors and within-region contrasts), and the **November matched predictive benchmark** (728,640 records across 2021–2025 annual cohorts).

---

## 2. Signature Theme Palette

The palette combines high-contrast dark ink typography with a vibrant team yellow accent and deep viridis teal for charts:

| Token | Hex Code | RGB | Usage |
|---|---|---|---|
| **Signature Yellow (Accent Primary)** | `#FFDD04` | `(255, 221, 4)` | Title accent bar, bullet markers (`▪`), active step indicators, full-width footer bar, cover arrow |
| **Dark Ink (Navy / Charcoal)** | `#1C2333` | `(28, 35, 51)` | Main titles, card headings, primary body copy, footer text |
| **Viridis Blue / Deep Teal** | `#31688E` | `(49, 104, 142)` | Category eyebrow labels, step chips, primary chart bars (e.g. pre-pandemic baseline, training split) |
| **Paper Canvas** | `#FBFAF6` | `(251, 250, 246)` | Slide background (soft warm paper ground) |
| **Surface White** | `#FFFFFF` | `(255, 255, 255)` | Content card surfaces, exhibit containers |
| **Panel / Well** | `#EFEDE6` | `(239, 237, 230)` | Neutral table headers, callout card backgrounds |
| **Divider Line** | `#D9D6CC` | `(217, 214, 204)` | Container borders, structural separators |
| **Muted Grey** | `#6E7278` | `(110, 114, 120)` | Captions, secondary notes, inactive step numbers, axis labels |
| **Red Marker** | `#C64040` | `(198, 64, 64)` | Numbered takeaway badges (12pt circles with 8pt white numerals) |

> [!IMPORTANT]
> **Yellow Text Rule:** Yellow (`#FFDD04`) is strictly an accent, badge, shape, or chip color. It must **never** be used for body text on a light background. On the signature yellow footer bar, all text is printed in Dark Ink (`#1C2333`).

---

## 3. Spatial Grid & Layout Architecture

Each body slide follows a disciplined split-rail layout:

```
+-------------------------------------------------------------------------------------------------+
| [CATEGORY EYEBROW] (x=0.75", y=0.42") 11.5pt Bold Viridis Blue       [01  (02)  03 ... 08 < ^ >]  |
| [SLIDE TITLE]      (x=0.70", y=0.78") 36pt Bold Dark Ink                                        |
| [ACCENT BAR]       (x=0.75", y=1.62") 1.35" wide x 3.5pt height (#FFDD04 Yellow)               |
+---------------------------------------------------------+---------------------------------------+
| Left Rail: Narrative & Big Numbers (w=7.35" or 12.1")   | Right Rail: Academic Figure (w=4.55") |
| - Big Callout Number (40pt bold + 16pt label)           | - Native resolution chart (300 dpi)   |
| - Bullet list with Yellow markers (▪ #FFDD04)           | - Figure N. Caption (10pt bold ink)   |
| - Strong bold lead-ins for each bullet                  | - Notes: (9pt muted grey)             |
+---------------------------------------------------------+---------------------------------------+
| Full-Width Signature Footer Bar (y=7.15", height=0.35", Fill: #FFDD04 Yellow)                  |
| Text: "UNSW Marketing Analytics Hackathon 2026" (10pt Dark Ink #1C2333, left aligned x=0.75")   |
+-------------------------------------------------------------------------------------------------+
```

### Coordinates and Spatial Specifications

- **Slide Dimensions:** 13.333" × 7.50" (960 × 540 pt in standard 16:9 widescreen).
- **Top Eyebrow:** `left = 0.75"`, `top = 0.42"`, uppercase letter-spaced font in `#31688E` (e.g., `FINDING 1 · THE MARKET`, `METHOD`, `RECOMMENDATIONS`).
- **Step Indicator Rail (top-right):** `top = 0.40"`, `right = 12.8"`. Contains circular step pills `01` to `08`. Active step is highlighted in Yellow (`#FFDD04`) with dark bold number.
- **Title Block:** `left = 0.70"`, `top = 0.78"`, `width = 11.3"`, 36 pt bold `#1C2333` (`Georgia` or `DM Sans` / `Google Sans`).
- **Accent Line:** `left = 0.75"`, `top = 1.62"`, `width = 1.35"`, `height = 3.5 pt`, solid `#FFDD04`.
- **Hero Number Callout:** `left = 0.75"`, `top = 1.95"`, 40 pt bold Dark Ink + 16 pt muted grey label (e.g., `46.0% → 30.3% → 30.0%`).
- **Bullet Content:** Starts at `y = 1.95"` (or `y = 3.10"` below callout), `width = 7.35"` (beside chart) or `12.1"` (full width). Yellow bullet square `▪` in 16 pt `#FFDD04`, body in 16.5 pt `#1C2333` with 12 pt paragraph spacing.
- **Figure Container (right):** `left = 8.2"`, `top = 1.95"`, max width `4.55"`, max height `4.6"`.
- **Figure Caption:** `left = 8.2"`, `top = 6.62"`, 10 pt bold ink caption + 9 pt muted grey methodology note.
- **Footer Bar:** `top = 7.15"`, `height = 0.35"`, spanning full slide width (`13.333"`). Filled with `#FFDD04`. Text at `left = 0.75"`: `UNSW Marketing Analytics Hackathon 2026` in 10 pt bold `#1C2333`.

---

## 4. Typography Standards

| Element | Typeface | Size | Weight | Color |
|---|---|---|---|---|
| **Cover Title** | Georgia / Modern Sans | 66 pt | Bold | `#FBFAF6` (on dark teal cover) |
| **Cover Subtitle** | DM Sans / Google Sans | 22 pt | Italic | `#B8CED6` |
| **Cover Kicker** | Courier New / Mono | 13 pt | Bold | `#FFDD04` (Yellow) |
| **Section Eyebrow** | Courier New / Mono | 11.5 pt | Bold | `#31688E` (Viridis Blue) |
| **Slide Title** | Georgia / Modern Sans | 36 pt | Bold | `#1C2333` (Dark Ink) |
| **Hero Big Number** | Georgia / Modern Sans | 40 pt | Bold | `#1C2333` (Dark Ink) |
| **Hero Label** | DM Sans / Google Sans | 16 pt | Regular | `#6E7278` (Muted Grey) |
| **Body Bullets** | DM Sans / Google Sans | 16.5 pt | Regular (Bold lead-in) | `#1C2333` (Dark Ink) |
| **Bullet Marker (`▪`)** | Arial / DM Sans | 16 pt | Bold | `#FFDD04` (Yellow) |
| **Figure Number** | DM Sans / Google Sans | 10 pt | Bold | `#1C2333` (Dark Ink) |
| **Figure Note** | DM Sans / Google Sans | 9 pt | Regular | `#6E7278` (Muted Grey) |
| **Footer Text** | Courier New / Mono | 10 pt | Bold | `#1C2333` (on Yellow Bar) |

---

## 5. Editorial and Statistical Governance (The `v3` Fix List)

Every slide must strictly adhere to the audited facts established in `docs/presentation/deck_edit_list.md`:

1. **Borrower vs. Partner Capital Framing (D6):**
   - 96.4% of loans are disbursed *before* platform listing (median 24 days prior).
   - Funding speed is the *field partner's working capital cycle*, not the borrower's wait.
   - Never say "helps borrowers get money faster" or suggest borrowers "ask for less."
2. **Permanent Pandemic Slowdown:**
   - Pre-pandemic 24h completion rate was **46.0%**.
   - Dropped to **30.3%** in pandemic and remained flat at **30.0%** post-pandemic.
   - Quote exact arrow notation: `46.0% → 30.3% → 30.0%` (never `46% >> 30% >> 30%`).
3. **Clustered Standard Errors & The Urgency Illusion:**
   - Under country clustering, urgency p-value collapses to **$p \approx 0.49$** (authoritative pipeline) or **$p \approx 0.44$** (notebook fit).
   - State clearly: 64 of 120 significant coefficients (53.3%) do not survive country clustering.
4. **Regional Within-Slope Screening:**
   - Middle East (-0.073) and Central America (-0.074) rest on only 2 countries each.
   - Under heuristic few-cluster $t(1)$ critical value (12.71), confidence intervals cross zero: Middle East $[-0.25, +0.10]$, Central America $[-0.16, +0.01]$.
   - Report as a *hypothesis for stratified A/B testing*, never as an established finding.
5. **Borrower Strategy Reframed as Expectations:**
   - Borrowers cannot choose gender or sector to game funding speed.
   - Frame advice as *setting realistic expectations by category and amount*.
6. **Classifier Capability Boundaries:**
   - 24h classifier achieves **0.8997 ROC AUC** and **0.8301 Average Precision** on 278,887 holdout loans.
   - State clearly: "Structure does the work: no framing feature in the SHAP top 10."
   - The classifier is a retrospective ranking prototype among funded loans; deployment requires retraining on all posted listings (including expired/withdrawn).
7. **Closing Scope:**
   - Always conclude: `“In this data, the story barely registers. The structure carries the signal.”`

---

## 6. Speaker Notes Architecture

Every slide carries an exact, rehearsal-tested spoken script in presenter notes:
- Speaker designation (Sophia vs. Tuan).
- Measured timing target (e.g. `(Sophia, ~65s)`).
- Word-for-word delivery text matching the exact numbers shown on the slide.
- Explicit `[Sources]` block documenting data provenance.
