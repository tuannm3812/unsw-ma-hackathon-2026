# Deck edit list — for the resubmission to Dr Dong

Page-by-page **find → replace** list for `Team Cultural Blend - UNSW Hackathon 2026` (the 14-page Google Slides deck). Search for the FIND text with Edit → Find and replace; the strings are copied verbatim from the rendered slides. Work Section A first — every item there is factually wrong or contradicts our own prepared answers. Sections B and C are improvements; Section D is what to leave alone.

Provenance: 15 independent review passes (5 lenses × 3 page groups) over the page images, deduped to 84 candidate edits; each surviving item was then fact-checked against `reports/generated_full_dataset/association_summary.txt`, `docs/1_data_dictionary.md` and the Q&A pack — the key numbers (64/120, the within-region slopes, urgency p, the classifier feature matrix) recomputed or re-read from source, not trusted from any reviewer.

---

## A · Must fix — wrong, or contradicts our own answers

### p4 [step 03] · the market slide

**Headline**
- FIND: `A slower market where longer borrowers wait is the operating reality.`
- REPLACE: `A slower market is the operating reality — and it is partner capital that waits.`
- Why: 96.4% of loans are disbursed **before** the page goes live (median 24 days). The borrower is not waiting; the field partner's capital is. This is the one claim a judge could use to say we misread the platform (Q&A **D6**). The original is also ungrammatical.

**Bullet 2 (replace the whole bullet — both sentences are defective)**
- FIND: `Since 2020: under a third, and after 4 years though not yet recovered. Borrowers now wait longer for capital in the markets where waiting costs most.`
- REPLACE: `Since 2020: under a third — and four years on, still not recovered. Partner capital now waits longer, not the borrower: 96% of loans are already disbursed before the page goes live.`
- Why: the first clause is garbled; the second sentence repeats the D6 contradiction, and "markets where waiting costs most" has no supporting analysis anywhere in the repo. (Bullet 3 already carries the "persistence to date" hedge — keep it there.)

**Number strip**
- FIND: `46% >> 30% >> 30%`
- REPLACE: `46.0% → 30.3% → 30.0%`
- Why: the two identical 30%s hide the finding the bullet states — the "recovery" is **minus 0.3 points**. The chart's own notes line already carries the exact shares. (`>>` also reads as "much greater than" to a statistics audience.)

### p5 [step 04] · structure beats story

**Headline**
- FIND: `Structural loan factors beats storytelling by a magnitude`
- REPLACE: `Structural loan factors beat storytelling by an order of magnitude`
- Why: subject–verb agreement in the largest type on the page; "by a magnitude" is not the idiom.

**Bullet 2, closing bold phrase**
- FIND: `Bigger ask, longer wait.`
- REPLACE: `Bigger ask, longer on the platform.`
- Why: "wait" re-imports the borrower-waiting frame (D6), and the phrase nudges toward "ask for less", which Q&A **A4** explicitly declines to advise.

**Bullet 3, second clause**
- FIND: `region shows similarly large gaps`
- REPLACE: `country gaps are wider still — 0.2 to 20.5 days`
- Why: backwards as written. Region (6 levels, 3.7–15.6 d, ~4×) is the **narrowest** structural field because it compresses country's ~100× spread. Citing country makes the slide stronger, not weaker.

### p6 [step 05] · the headline finding

**Headline**
- FIND: `Storytelling coaching won't move the needle.`
- REPLACE: `Storytelling coaching: no robust evidence it moves the needle.`
- Why: the original asserts **no effect** — the exact overclaim the whole verification arc exists to avoid, and it contradicts p10's own limitations. Absence of robust evidence ≠ evidence of absence (the trap line in Q&A **A1**). The yellow sub-line beneath is already correct; the headline must match it.

**Figure 4 table — replace the six data rows with the authoritative fit**

The table currently prints the *notebook* duration fit, but the deck's own appendix (p12) quotes the authoritative pipeline's screen values, and the deck brief's standing rule is "use the authoritative numbers on slides." As printed, p6 and p12 disagree with each other. New cell values (loan counts stay as they are — they already match):

| region (ctys) | slope | cl. p | few-cl. p | verdict |
|---|---|---|---|---|
| Africa (27) | −0.016 | 0.323 | t(26) 0.332 | n.s. |
| Asia (12) | +0.023 | 0.085 | t(11) 0.113 | n.s. |
| C. America (2) | −0.074 | <0.001 | t(1) 0.060 | norm-ref only |
| Middle East (2) | −0.073 | <0.001 | t(1) 0.120 | norm-ref only |
| N. America (1) | +0.013 | 0.009 | not estimable | 1 country |
| Oceania (4) | +0.005 | 0.895 | t(3) 0.903 | n.s. |

**Urgency bullet (must move together with the table swap)**
- FIND: `collapses under country clustering (p≈0.44)`
- REPLACE: `collapses under country clustering (p≈0.49)`
- Why: 0.4943 is the authoritative duration model's clustered p; 0.4442 is the notebook's. One slide must not mix fits.
- *Fallback if there is no time for the table:* leave every number as is and change the table header to `Within-region family-framing slope (notebook duration fit): none pass the screen` — then 0.44 stays. Do one or the other, not neither.
- **Tell me which way you go** — I will sync the spoken scripts (currently "collapses to 0.44") and the pptx notes to match.

### p9 [step 07] · the borrower slide

The safest option remains deleting this slide. If it stays, all three rows and both headings need the rewrite below — as printed, the slide advises gaming a demographic field, points at the slowest sector, and implies "ask for less", each contradicting a prepared answer (E2, A4) or the limitations slide one page later.

**Yellow banner**
- FIND: `For Borrowers`
- REPLACE: `For borrowers: what to expect — not what to game`

**Heading**
- FIND: `Recommended Loan Strategy`
- REPLACE: `What to expect when listing`

**Row 1 (Profile), value cell**
- FIND: `Female can represent household to submit loans`
- REPLACE: `Female-posted loans fund in a median 2.3 days vs 7.7 male-posted — a gap for Kiva to investigate, not a lever for borrowers`
- Why: unexplained association (about half is composition, the rest undecomposed — Q&A **E2**); presenting it as strategy contradicts p10 ("no borrower was randomly assigned…").

**Row 2, label + value cells**
- FIND: `Focus on Loan Amount Range & Repayment terms` / `Top 1 & 2 strongest correlation`
- REPLACE: `Loan amount & repayment terms` / `The two strongest speed predictors — but partner-set against a real need. Plan timing around them; don't shrink the ask`
- Why: Q&A **A4** is a prepared HARD question whose entire answer is "no, don't ask for less."

**Row 3 (Sector), value cell**
- FIND: `Clothing, Transportation, Services, Construction, Agriculture & Retail`
- REPLACE: `Speed varies ~13× by sector (0.9–12.1 days) — set expectations by category; don't switch categories to chase speed`
- Why: as printed the list leads with Clothing — the **slowest** sector in the data — and a borrower cannot choose a sector anyway; it follows from the loan's purpose.

### p14 [appendix] · classifier detail

**Kicker**
- FIND: `APPENDIX · A4`
- REPLACE: `APPENDIX · A3`
- Why: labels run A1, A2, A4 — there is no A3 in the deck. Nothing is missing; relabel.

**Bullet 2, closing phrase**
- FIND: `accuracy 0.840 — no narrative features needed.`
- REPLACE: `accuracy 0.840 — structure does the work: no framing feature in the SHAP top 10 (sentiment is 11th).`
- Why: **factually wrong as printed.** The classifier's feature matrix *includes* the framing, sentiment and topic features (`src/modeling.py::prepare_chronological_matrices` — verified in code). No narrative-free ablation was ever run, so "not needed" is an untested claim; what the evidence supports is the SHAP ranking on p13.

---

## B · Should fix — misleading or self-inconsistent, not fatal

### p3 [step 02]
- FIND: `Most significant results results did NOT survive . That is the point of the method.`
- REPLACE: `Across both explanatory models, 64 of 120 significant coefficients did not survive the country-clustered re-test. That is the point of the method.`
- Why: fixes the doubled word and the stray space, and replaces "most" with the exact figure — recomputed directly from the sensitivity blocks in `association_summary.txt` (64 of 120 HC3-significant coefficients lost significance). A quantified claim lands harder on the methods slide.
- Also on this page: `a stricter few cluster reference` → `a stricter few-cluster screen` ("screen" is the word every prepared answer uses — it can downgrade a claim, never certify one).

### p8 [step 07]
- FIND: `What this means in practice for Kiva team` → REPLACE: `What this means in practice for the Kiva team`
- FIND: `DO review the structural gaps (sector / region / gender)` → REPLACE: `DO review the structural gaps (programme / sector / region / gender)`
  — the programme label (`whySpecial`) is the widest structural gap in the data (0.2–30.9 mean days); the structural review should start there (Q&A **C10**).
- FIND: `strictly future data),  but` → REPLACE: `strictly future data), but` (double space)
- If there is room, add one small line under the cards: `96% of these loans are disbursed before the page goes live — funding speed is the field partner's capital cycle.` The spoken script carries this; the slide currently doesn't.

### p7 [step 06]
- FIND: `across story topics >> a >9× swing` → REPLACE: `across story topics — a ninefold swing` (13.5 / 1.5 = 9.0 exactly; the `>>` glyph noise again)
- FIND: `group farming waits ~2 weeks` → REPLACE: `group farming loans take ~2 weeks to fund` ("waits" re-imports the borrower-waiting frame)

### p11 [closing]
- FIND: `The story barely registers.` → REPLACE: `In this data, the story barely registers.`
- Why: matches the spoken line word for word, and the scope hedge is the discipline. (This is the slide the audience will be looking at while voting.)

### p5 [step 04] · optional coherence fix
- The bullet says `~10×`, the chart notes line says `~7x stronger` — a judge can read both on one slide. If touching it: end the notes line with `…(0.429 vs 0.058); "~10×" is the order-of-magnitude summary across all narrative signals (7× the strongest, 20× the rest).`
- Figure 3's title is printed twice (bold slide caption + baked into the chart image). Crop or blank the in-image title if quick.

## C · Typos (one Find-and-replace pass)

| Page | FIND | REPLACE |
|---|---|---|
| p2 | `they posted ?` | `they posted?` |
| p4 | `589,823 loans before vs. 565,474 after, not a thin sample, and show persistence to date.` | `589,823 loans before vs 565,474 after — not a thin sample, and the slowdown persists to date.` |
| p5 | `Female vs male-posted loans median funding speed are 2.3 vs 7.7 days` | `Loans posted by women fund in a median 2.3 days; by men, 7.7` |
| p10 | `Association, never causation .No borrower` | `Association, never causation. No borrower` |
| footer (layout master, all pages) | `UNSW Marketing Hackathon 2026` | `UNSW Marketing Analytics Hackathon 2026` |

## D · Leave alone (checked, deliberate, or a fix would break something else)

- **Progress rail: p8 and p9 both show step 07.** Deliberate — the rail has 8 dots for 9 content slides and both pages sit under RECOMMENDATIONS. Renumbering p9 to 08 would collide with p10. Leave it.
- The chronological train/test exhibit (p3) and its notes line.
- The p12 appendix (A1) in full — pooled sizes, `not estimable` for North America, "the screen can downgrade a claim, never certify one." It already quotes the authoritative values; it is p6 that has to move to match it.
- The p13 SHAP framing ("complementary predictive evidence only").
- The closing photo-quote layout on p11 (text fix above only).
- Title slide affiliation "University of Technology Sydney" — correct (the team is UTS; the competition is UNSW-hosted). Optionally add a data line under the team block: `Kiva loan data · 1.45 million real loans · 2016–2025` — the opening script says it aloud and no slide shows it.

---

*After you apply p6, tell me which option you took (authoritative numbers vs notebook relabel) and I'll sync the spoken scripts, pptx notes and rehearsal copy to match — they currently say "collapses to 0.44".*
