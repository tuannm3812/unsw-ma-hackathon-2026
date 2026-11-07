> **Superseded 2026-11-08.** This 17-slide brief reuses claims retired in `docs/2_evidence_and_corrections.md`. Kept as history. Use `docs/presentation/portfolio_deck/` and `claims_register.md` instead.

# Authoritative Slide Content Briefing · Executive 3-Act Hybrid
**Team Cultural Blend · UNSW Marketing Analytics Hackathon Challenge 2026**  
*Investigation: 1,453,846 real Kiva loans (2016–2025) · 10-Minute Presentation & Q&A*  
*Standard: Governed strictly by [`docs/presentation/DESIGN.md`](file:///Users/tuannm3812/Documents/GitHub/4.%20Training/unsw-ma-hackathon-2026/docs/presentation/DESIGN.md)*

---

## 1. Architectural Strategy: The Executive 3-Act Hybrid

This briefing establishes the single source of truth for the presentation deck. It reconciles two powerful presentation philosophies:
1. **The McKinsey Executive BLUF (Bottom-Line Up Front):** Give the judging panel (80% weight) the definitive empirical verdict in the first 45 seconds so they never have to guess the outcome.
2. **The 3-Act Narrative Arc (High Drama for Audience Vote):** Keep the audience (20% weight) engaged through a structured emotional journey:
   - **Act I: The Platform Promise & Operating Reality** (Why copy is coached $\to$ but the market has slowed and partner capital is waiting).
   - **Act II: The Empirical Stress-Test (The Reveal)** (Why big data lies without clustering $\to$ structure beats story $\sim 10\times$ $\to$ narrative advice collapses).
   - **Act III: The High-ROI Strategic Playbook** (Stop wasteful nudges $\to$ launch 4-market stratified A/B tests $\to$ deploy predictive early warnings).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  EXECUTIVE 3-ACT HYBRID MAP (17-SLIDE MASTER PORTFOLIO DECK)                           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  PROLOGUE & BLUEPRINT: THE EXECUTIVE VERDICT (BLUF)                                    │
│  Slide 1: Cover · Beyond a Good Story (1.45M real loans scale)                         │
│  Slide 2: Step 01 · The Executive Verdict (What Platforms Believe vs 1.45M Reveal)     │
│  Slide 3: OVERVIEW · Project Architecture & Executive Table of Contents                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  ACT I: THE PLATFORM PROMISE & OPERATING REALITY (Sophia)                              │
│  Slide 4: Step 02 · The Motivation (Why platforms coach story: the only unsealed lever)│
│  Slide 5: Step 03 · Finding 1: The Slower Market & Partner Capital (46% → 30%, 96.4%)  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  ACT II: THE EMPIRICAL STRESS-TEST (Sophia ➔ Tuan hand-off at Slide 7)                 │
│  Slide 6: Step 04 · Methodology (Why big data lies: 64/120 drop, chronological holdout)│
│  Slide 7: Step 05 · Finding 2: Structural Dominance (Structure beats story ~10×)       │
│  Slide 8: Step 06 · Finding 3: The Narrative Scrutiny (Urgency p=0.49, 2-country screen)│
│  Slide 9: Step 07 · Finding 4: Topics Encode Cause (Clean water vs farming; 9× swing)  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  ACT III: THE HIGH-ROI STRATEGIC PLAYBOOK (Tuan)                                       │
│  Slide 10: Step 08 · Platform Playbook for Kiva (The 4-Action Executive Matrix)        │
│  Slide 11: Step 08 · Setting Expectations for Borrowers & Partners (What NOT to game)  │
│  Slide 12: Step 08 · Limits & Scientific Rigor (Three boundaries on the evidence)      │
│  Slide 13: Epilogue · The Core Thesis Statement & Call to Q&A                          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  APPENDIX: TECHNICAL DEFENSE & PROOF PACK (FOR DEEP-DIVE REVIEW)                       │
│  Slide 14 (A1): The Two-Country Screen Problem in Full (t(1) = 12.7 critical barrier)  │
│  Slide 15 (A2): Predictive Weight ≠ Statistical Robustness (SHAP Top 15 Analysis)     │
│  Slide 16 (A3): The ~10× Structural Comparison Exactly (Deciles & correlation table)  │
│  Slide 17 (A4): 24h Early Warning Classifier Architecture (ROC AUC 0.8997)             │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Visual & Format Governance (`DESIGN.md` Alignment)

Every slide generated or edited must obey these programmatic rules:
- **Canvas:** 16:9 Widescreen (Width: `13.333"` / `960pt`, Height: `7.50"` / `540pt`).
- **Signature Palette:**
  - `Vivid Signature Yellow` (`#FFDD04`): Eyebrow accents, accent bar, bullet markers (`▪`), active step chip, full-width footer.
  - `Dark Ink Navy` (`#1C2333`): Background for Cover & Closing; all title and body typography on light slides.
  - `Viridis Blue / Teal` (`#31688E`): Category kickers, secondary card headers, baseline chart fills.
  - `Warm Paper Canvas` (`#FBFAF6`): Clean light ground for content slides.
  - `Surface White` (`#FFFFFF`): Card backgrounds.
  - `Panel Fill` (`#F3F2ED`): Callout and timeline containers.
  - `Divider Line` (`#D9D6CC`): Card borders.
  - `Muted Slate Grey` (`#6E7278`): Exhibit notes, inactive step numbers, captions.
  - `Alert Red` (`#C53030`): 'DON'T SHIP' warning badges.
- **Top-Right 8-Step Progress Rail:**
  - Coordinates: `x = 9.05"`, `y = 0.36"`, width `3.55"`, height `0.34"`.
  - Eight distinct rounded chips (`01` through `08`).
  - Active step: filled in `#FFDD04` with bold `#1C2333` text; inactive steps in white/neutral with grey text.
- **Header Block:**
  - Category Eyebrow: `x = 0.75"`, `y = 0.38"`, `Courier New` Bold Viridis Blue.
  - Main Title: `x = 0.70"`, `y = 0.72"`, `Georgia` Bold Dark Ink (`Pt(30)` or `Pt(26)` for 2-line wraps).
  - Accent Bar: `x = 0.75"`, `w = 1.35"`, `h = 3.5pt`, filled in `#FFDD04`, dynamically placed below title line 2.
- **Full-Width Yellow Footer Bar:**
  - `y = 7.15"`, `h = 0.35"`, `w = 13.333"`. Fill: `#FFDD04`.
  - Text at `x = 0.75"`: `UNSW Marketing Analytics Hackathon 2026` in 10pt Bold `#1C2333`.

---

## 3. Detailed Slide-by-Slide Briefing & Audited Evidence

---

### PROLOGUE: THE EXECUTIVE VERDICT (BLUF)

#### Slide 1 · Title & Hook
- **Eyebrow:** `UNSW MARKETING ANALYTICS HACKATHON 2026`
- **Title:** `Beyond a Good Story`
- **Subtitle:** `When and for whom does persuasive loan language actually speed up funding?`
- **Team Block:** `Team Cultural Blend · University of Technology Sydney`
- **Data Scale Line:** `Kiva loan data · 1.45 million real loans · 2016–2025`
- **Audited Evidence:** Exactly 1,453,846 completed loans over 10 full calendar years across 80+ countries.
- **Visual Style:** High-contrast Dark Ink Navy canvas with yellow arrow and accents.
- **Speaker:** Sophia (~30s). Establishes institutional gravity immediately.

#### Slide 2 · Step 01 · The Executive Verdict (BLUF Upfront)
- **Eyebrow:** `EXECUTIVE SUMMARY · THE VERDICT` | **Active Step:** `01`
- **Headline:** `In 1.45M loans, the story barely registers. The structure carries the signal.`
- **Audited Evidence & Narrative Structure:**
  - *Left Card (What Platforms Believe):* Platforms assume copy is the only active conversion lever because size and geography are locked at listing. Naive unclustered regressions support this ($p < 0.001$).
  - *Right Card (What 1.45M Loans Reveal):* Under country clustering, urgency language dissolves ($p \approx 0.49$); family framing rests on a 2-country screen illusion ($t(1)=12.7$); structural loan factors beat storytelling by $\sim 10\times$. 96.4% of loans are pre-disbursed—partner capital waits, not borrowers.
  - *Bottom Strategic Banner:* Do not waste engineering resources on generic copywriting nudges. Shift platform investment toward structural bottlenecks, partner liquidity cycles, and country-stratified A/B experiments.
- **Speaker:** Sophia (~55s). Delivers the core conclusion up front.

#### Slide 3 · OVERVIEW · Project Architecture & Executive Table of Contents
- **Eyebrow:** `TABLE OF CONTENTS · PROJECT BLUEPRINT` | **Active Tag:** `OVERVIEW`
- **Headline:** `How the 1.45M loan investigation is structured`
- **Audited Architecture & 4-Pillar Layout:**
  - *Card 1 (Act I · Operating Reality, Slides 4–5):* Platform dilemma at listing; 16-point post-pandemic slowdown ($46\% \to 30\%$); 96.4% pre-disbursed partner working capital cycle.
  - *Card 2 (Act II · The Empirical Stress-Test, Slides 6–9):* 64 of 120 coefficients collapse under country clustering; ~10× structural dominance over words; urgency dissolves ($p \approx 0.49$); topic models track loan purpose (water vs farming; 9× swing).
  - *Card 3 (Act III · Strategic Playbook, Slides 10–12):* 4-quadrant action matrix for Kiva product & marketing; borrower realism (what NOT to game); transparent academic boundaries.
  - *Card 4 (Appendix · Methodological Audits, Slides 14–17):* The conservative $t(1)=12.7$ few-cluster screen; why SHAP importance cannot certify policy rules; exact ~10× correlation table; 24h LightGBM classifier architecture (ROC AUC 0.8997).
  - *Bottom Methodology Stack Banner:* Econometric OLS Duration Modeling · Binomial GLM · Country-Clustered SEs · Few-Cluster $t(1)$ Heuristic · NMF Topic Extraction · LightGBM Holdout Benchmark (Strict Chronological Split, Zero Future Leakage).
- **Purpose for Portfolio Review:** Gives hiring managers and technical directors an immediate roadmap of econometric rigor and platform strategy.

---

### ACT I: THE PLATFORM PROMISE & OPERATING REALITY

#### Slide 4 · Step 02 · Motivation: The Platform Dilemma
- **Eyebrow:** `ACT I · OPERATING REALITY` | **Active Step:** `02`
- **Headline:** `Why platforms coach story: the only lever unsealed at listing`
- **Audited Evidence & Content:**
  - *Card 1 (The Narrative Question):* When a loan's story leans on family, competence, or urgency, does it fund faster?
  - *Card 2 (The Moderation Question):* Does the result shift by WHO the borrower is (gender, geography) and WHERE & WHEN they posted?
  - *Card 3 (Why It Matters):* On Kiva, the loan page is the product page. Loan amount, sector, country, and partner terms cannot be rewritten after posting—copywriting is the only coachable lever.
- **Speaker:** Sophia (~50s). Frames the marketing dilemma.

#### Slide 5 · Step 03 · Finding 1: The Slower Market & Partner Capital
- **Eyebrow:** `ACT I · OPERATING REALITY` | **Active Step:** `03`
- **Headline:** `A slower market is the operating reality — and it is partner capital that waits.`
- **Audited Evidence:**
  - Same-day conversion: Pre-pandemic `46.0%` ($589,823$ loans) $\to$ Pandemic `30.3%` ($298,549$ loans) $\to$ Post-pandemic `30.0%` ($565,474$ loans).
  - Four years on, conversion has not recovered (net shift: $-0.3$ percentage points).
  - **The 96.4% Pre-Disbursal Reality (The D6 Defense):** 96.4% of loans are disbursed to the borrower *before* listing on Kiva (median 24 days prior). Borrowers do *not* wait; field partner working capital waits to replenish.
- **Visual Exhibit:** Right rail: Figure 2 (share of loans funded within 24h). Left rail: Embedded Field Partner Capital Cycle diagram (`Day 0 Cash Disbursed ➔ Day 24 Listing ➔ Day 27+ Reimbursed`).
- **Speaker:** Sophia (~65s). Disarms the judge's biggest potential trap (Q&A D6).

---

### ACT II: THE EMPIRICAL STRESS-TEST (THE SHOCKING REVEAL)

#### Slide 6 · Step 04 · Methodology: Why Big Data Lies Without Clustering
- **Eyebrow:** `ACT II · THE STRESS-TEST` | **Active Step:** `04`
- **Headline:** `Why big data lies without clustering: how we stress-tested our claims`
- **Audited Evidence:**
  - **The Chronological Holdout:** Trained strictly on loans up to 2023; `278,887` loans from 2024–2025 sealed until evaluation.
  - **The Country-Clustered Re-Test:** In big data, standard errors shrink mechanically. When clustered by country, **64 of 120 significant coefficients collapsed**.
  - **The Few-Cluster Screen:** For regions with only 1–2 countries, required the conservative critical value $t(1) = 12.7$ (not normal $1.96$).
  - **Role of Machine Learning:** SHAP importance is complementary predictive validation only; cannot certify causal or econometric signs.
- **Visual Exhibit:** Right rail: Figure 1 (Chronological train/test split timeline). Left rail: Hero Big Number `64 of 120 significant coefficients lost significance`.
- **Speaker:** Sophia (~60s). Demonstrates econometric muscle.

#### Slide 7 · Step 05 · Finding 2: Structural Dominance
- **Eyebrow:** `ACT II · THE STRESS-TEST` | **Active Step:** `05`
- **Headline:** `Structural loan factors beat storytelling by an order of magnitude`
- **Audited Evidence:**
  - **Hero Metric:** `2.3 vs 7.7 days` median funding speed for female-posted vs male-posted loans (3x faster).
  - **Correlation Ratio:** Loan amount and repayment terms correlate $\sim 10\times$ more strongly with funding speed than any narrative signal ($r \approx 0.43 - 0.56$ vs $r \le 0.058$). Bigger ask, longer on the platform.
  - **Geographic Spread:** Sector spans 0.9 to 12.1 days; country gaps span 0.2 to 20.5 days; programme labels (`whySpecial`) span 0.2 to 30.9 days.
- **Visual Exhibit:** Right rail: Figure 3 (Correlation bar chart: structure vs narrative).
- **Speaker:** Sophia (~65s). Delivers the structural evidence and hands off to Tuan.

#### Slide 8 · Step 06 · Finding 3: The Narrative Scrutiny (Myth Busted)
- **Eyebrow:** `ACT II · THE STRESS-TEST` | **Active Step:** `06`
- **Headline:** `Storytelling coaching: no robust evidence it moves the needle.`
- **Audited Evidence:**
  - **Urgency Framing:** Appeared universal ($p < 0.001$), but under country clustering collapses to **$p \approx 0.49$** (authoritative duration model). Gone.
  - **Family Framing (The Two-Country Problem):** Middle East ($n = 14,946$) = Palestine + Yemen; Central America ($n = 59,391$) = Honduras + Nicaragua. Under the few-cluster screen bar ($t(1) = 12.7$), neither passes ($p \approx 0.06 - 0.12$). A hypothesis, not an established rule.
  - **Sentiment:** Positive tone associated with slower funding, but flips between specifications.
  - **SHAP Confirmation:** Zero narrative features in the model's top 15.
- **Visual Exhibit:** Right rail: Figure 4 (Within-region family framing slope table). Left rail: Yellow sub-card: *“No narrative result is robust enough to support a writing recommendation.”*
- **Speaker:** Tuan (~1m50s). The central intellectual defense.

#### Slide 9 · Step 07 · Finding 4: Topics Encode Cause, Not Prose
- **Eyebrow:** `ACT II · THE STRESS-TEST` | **Active Step:** `07`
- **Headline:** `The themes come down to loan purpose, not persuasion.`
- **Audited Evidence:**
  - **Hero Callout:** `1.5 → 13.5 days` across story themes (a ninefold swing).
  - 8 NMF topics surface coherent themes: clean water & sanitation fund in under 2 days; group farming loans take ~2 weeks.
  - **The Core Attribution Takeaway:** Lenders fund clean water because it is clean water, not because the borrower wrote better adjectives. Story themes encode **what the loan is FOR (structure)**, not persuasive copywriting.
- **Visual Exhibit:** Right rail: Figure 5 (Mean funding speed by story theme bar chart).
- **Speaker:** Tuan (~50s). Prepares the ground for the strategic recommendations.

---

### ACT III: THE HIGH-ROI STRATEGIC PLAYBOOK

#### Slide 10 · Step 08 · Platform Strategy for Kiva: The 4-Action Playbook
- **Eyebrow:** `ACT III · STRATEGIC PLAYBOOK` | **Active Step:** `08`
- **Headline:** `What this means in practice for the Kiva team: a 4-action playbook`
- **Audited Evidence & 4-Quadrant Actions:**
  1. `[DON'T SHIP · Generic Writing Tips]` (Red Accent): Withhold platform-wide "add urgency" tips. Built on statistical noise ($p \approx 0.49$). Spares engineering overhead and prevents borrower confusion.
  2. `[A/B TEST · Targeted Family Framing]` (Blue Accent): Run stratified A/B experiments strictly in the 4 candidate markets: Palestine, Yemen, Honduras, Nicaragua. Randomize prompts at listing; evaluate causal speed country-by-country.
  3. `[REVIEW STRUCTURE · The ~10x Levers]` (Dark Ink): Optimize where speed variance actually lives: Programme labels (`whySpecial`, 0.2–30.9d), sector friction, and partner replenishment cycles.
  4. `[PROTOTYPE & AUDIT · 24h Classifier]` (Blue Accent): The 24h LightGBM classifier achieves $AUC \approx 0.90$ (accuracy 0.840) on funded loans. Before operational deployment, retrain on all listings (including expired and withdrawn).
  - *Bottom Banner:* `⚡ Operational Reality: 96% of loans are disbursed before listing — speed is the partner's capital cycle, not borrower waiting.`
- **Speaker:** Tuan (~1m25s). Practical product roadmap for Kiva leadership.

#### Slide 11 · Step 08 · Setting Expectations for Borrowers & Field Partners
- **Eyebrow:** `ACT III · STRATEGIC PLAYBOOK` | **Active Step:** `08`
- **Headline:** `What to expect when listing: setting expectations, not gaming levers`
- **Audited Evidence & 3 Structured Rows:**
  - *Banner:* `FOR BORROWERS & FIELD PARTNERS: WHAT TO EXPECT — NOT WHAT TO GAME`
  - *Row 1 (Profile & Gender):* Women fund in median 2.3d vs 7.7d for men. A gap for Kiva to investigate internally; **DO NOT** manipulate who represents the household.
  - *Row 2 (Loan Size & Terms):* The two strongest speed predictors. Amounts reflect real business capital need; plan cash flow around them; **DO NOT** shrink the ask.
  - *Row 3 (Sector & Cause):* Speed varies ~13x (water <2d vs farming ~2wks). Purpose dictates category; **DO NOT** misclassify category to chase speed.
  - *Footnote:* Bigger asks sit on platform longer (~2 vs ~19 days). Affects partner liquidity, not borrower survival.
- **Speaker:** Tuan (~40s). Protects vulnerable borrowers from exploitative or counterproductive advice.

#### Slide 12 · Step 08 · Academic Limits & Scientific Integrity
- **Eyebrow:** `ACT III · STRATEGIC PLAYBOOK` | **Active Step:** `08`
- **Headline:** `What this can't tell us: three boundaries on the evidence`
- **Audited Evidence & 3 Academic Shield Cards:**
  1. `01 · ASSOCIATION, NEVER CAUSATION:` Observational data; no borrower was randomly assigned narrative phrasing.
  2. `02 · COMPLETED FUNDRAISES ONLY:` Measures how fast a funded loan funds, not whether it gets funded at all (survival truncation).
  3. `03 · TRANSPARENT LEXICAL BOUNDS:` Transparent dictionary counts and sentiment compound scores, not every nuance of storytelling craft.
- **Speaker:** Tuan (~35s). Intellectual honesty that disarms tough academic judge probes.

#### Slide 13 · Epilogue: Conclusion & Call to Q&A
- **Visual Style:** Dark Ink Navy canvas with signature yellow quote accents and full-width yellow footer bar.
- **The Core Thesis Quote:**
  > *“In this data, the story barely registers.  
  > The structure carries the signal.”*
- **Closing Callout:** `Thank you — questions.`
- **Speaker:** Both Tuan & Sophia (~20s). Decisive hand-off to question time.

---

### APPENDIX: TECHNICAL DEFENSE & PROOF PACK (FOR DEEP-DIVE REVIEW)

- **Slide 14 (A1) · The Two-Country Problem in Full:**  
  Exact pooled counts (ME: 14,946; CA: 59,391; Haiti: 7,559). Explanation of degrees of freedom and why $t(1)=12.7$ critical barrier is mathematically required.
- **Slide 15 (A2) · Predictive Weight $\neq$ Statistical Robustness:**  
  LightGBM SHAP top 15 ranking exhibit. Ten structural features lead; sentiment is 11th; zero family/urgency features in top 15. Explains why SHAP cannot validate econometric signs.
- **Slide 16 (A3) · The ~10× Comparison Exactly:**  
  Correlation table ($r = 0.43$ amount vs $0.058$ competence) and decile gradient (~2 days to ~18 days). Male coefficient $+0.430$ survives HC3 and clustering ($p < 0.0001$).
- **Slide 17 (A4) · 24h Classifier Architecture & Censoring Protocol:**  
  Holdout evaluation on 278,887 loans (ROC AUC 0.8997, AP 0.8301, Brier 0.1156, accuracy 0.840). Detailed retraining blueprint for expired/withdrawn populations.
