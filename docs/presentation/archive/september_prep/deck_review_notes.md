# Deck review notes

Reviewed `Team Cultural Blend - UNSW Hackathon 2026.pdf` (14 pages, exported from Google Slides, 2026-09-03 17:03) against the verified numbers in `reports/generated_full_dataset/` and `docs/1_data_dictionary.md`.

**The design is strong and the numbers are almost all right.** Every statistic I could check reproduces: the correlations (0.429 / 0.285 / 0.058 / 0.019 / 0.010), the regional means (3.7 to 15.6 days), the topic range (1.5 to 13.5 days), the classifier metrics (AUC 0.8997, AP 0.8301, Brier 0.1156, 87,466 + 191,421 = 278,887), and the few-cluster p-values (ME 0.12 / 0.21 / 0.08, CA 0.06 / 0.14 / 0.07). Slide numbering below uses the **PDF page**, with the deck's own step number in brackets.

---

## 1. Fix before presenting — these are wrong, not just awkward

**p4 [03] · "Borrowers now wait longer for capital"** and the headline **"A slower market where longer borrowers wait is the operating reality."**

96.4% of loans are disbursed to the borrower *before* the page goes live, a median of 24 days earlier. The borrower is not waiting — the field partner's capital is. This is the one thing on the deck that a judge could use to say we misunderstood the platform, and it is armed in Q&A **D6**. The headline is also ungrammatical ("where longer borrowers wait").

> Suggested: **"A slower market is the operating reality — and it is partner capital that waits."**

**p5 [04] · "region shows similarly large gaps"**

Not true, and it is the one direction the claim can't go. Region spans 3.7 to 15.6 days — about 4× — which is the *narrowest* structural field, because grouping countries into regions compresses country's 100× spread. Sector spans 13×. Country spans 0.2 (Nepal) to 20.5 (Senegal).

> Suggested: **"country spreads are wider still — 0.2 to 20.5 days."** That strengthens the slide instead of weakening it.

**p6 [05] · Headline "Storytelling coaching won't move the needle."**

This asserts no effect. Everything we've defended for thirteen review rounds says the opposite discipline: *absence of robust evidence is not evidence of absence*. It is written into Q&A A1's trap line and into the limitations slide. If a judge quotes this headline back, the honest answer contradicts our own slide.

> Suggested: **"We can't find robust evidence that coaching moves the needle."** The yellow sub-line underneath it is already exactly right — it just needs to be the claim, not the footnote.

**p9 [07] · Borrower table, "Profile: Female can represent household to submit loans"**

This tells households to put the woman forward to get funded faster. Three problems, any one of which is enough:

- It is an **association, not a cause** — our own limitations slide (p10) says no borrower was randomly assigned anything, and the gender gap is unexplained (Q&A **E2**).
- It advises **gaming a demographic field**, which is not something the evidence supports and not something a judge will read kindly.
- It contradicts the position we take everywhere else, that the gender gap is **a structural gap for Kiva to investigate**, not a tactic for borrowers.

> Suggested: cut the row, or move the finding to the platform side — "the 2.3 vs 7.7 day gap is a structural gap for Kiva to explain, not advice for borrowers."

**p9 [07] · "Sector: Clothing, Transportation, Services, Construction, Agriculture & Retail"**

If this reads as *recommended* sectors, it points at the wrong end: **Clothing is the slowest sector in the data at 12.1 days**, against Sanitation at 0.9. A borrower also can't pick a sector — it follows from what the loan is for.

**p9 [07] · "Focus on Loan Amount Range & Repayment terms: Top 1 & 2 strongest correlation"**

Reads as "ask for less". We explicitly decline to give that advice (Q&A **A4**) because the association is confounded with what borrowers need the money for. Either state the honest version — a bigger ask sits on the platform longer, which is a partner planning fact — or cut it.

---

## 2. Worth changing if there's time

- **p4 [03] · "46% >> 30% >> 30%"** — the two 30%s hide the actual finding. The exact shares are 46.0% / 30.3% / 30.0%: the "recovery" is **minus 0.3 points**. Showing `46% → 30.3% → 30.0%` makes the point the bullet is already making. (The `>>` glyph also reads as "much greater than" in a statistics room.)
- **p5 [04] · Figure 3 shows its title twice** — once as the slide's bold caption, once baked into the chart image.
- **p8 / p9 · both slides show step 07** in the progress rail.
- **Appendix labels run A1, A2, A4** — there is no A3. Nothing is missing: our A3 was the correlation detail, and its chart was promoted onto p5. Just relabel.
- **p1 · "University of Technology Sydney"** — worth a deliberate check that this is the affiliation we want on a UNSW-run competition. Fine if it's accurate; just make it a decision rather than a leftover.
- **p1 · the "1.45 million real loans" line is gone** from the title slide, though the script still says it aloud.
- **p8 [07] · no borrower item and no capital-cycle point.** Both now live only in the spoken script and in Q&A D6. With p9 existing as a separate borrower slide, the two should agree.

---

## 3. Typos

| Page | Reads | Should read |
|----|----|----|
| p2 [01] | "they posted ?" | "they posted?" |
| p3 [02] | "Most significant results results did NOT survive ." | "Most significant results did not survive." |
| p3 [02] | "a stricter few cluster reference" | "a stricter few-cluster reference" |
| p4 [03] | "Since 2020: under a third, and after 4 years though not yet recovered." | "Since 2020: under a third — and four years on, still not recovered." |
| p5 [04] | "Structural loan factors beats storytelling by a magnitude" | "Structural loan factors beat storytelling by an order of magnitude" |
| p5 [04] | "Female vs male-posted loans median funding speed are 2.3 vs 7.7 days" | "Loans posted by women fund in a median 2.3 days; by men, 7.7" |
| p8 [07] | "for Kiva team" | "for the Kiva team" |
| p10 [08] | "Association, never causation .No borrower was..." | "Association, never causation. No borrower was..." |

---

## 4. What is right and should not be touched

- The chronological train/test exhibit and its note — this is the slide that earns the method credibility.
- The within-region slope table on p6, including the `norm-ref only` verdicts and the t(1) = 12.7 note. That table is the honest core of the whole deck.
- The A1 appendix — pooled category sizes, the "single country, not estimable" row for North America, and "the screen can downgrade a claim, never certify one".
- The A2 SHAP framing: "complementary predictive evidence only — it cannot confirm or refute a coefficient."
- The A4 classifier boundary: "retrospective ranking prototype among eventual funders", not an early-warning system.
- The closing quote.
