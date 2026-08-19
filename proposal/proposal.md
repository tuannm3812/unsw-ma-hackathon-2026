# Beyond a Good Story: When and for Whom Loan Narratives Are Linked to Faster Prosocial Funding

**Team members:** Manh Tuan Nguyen

**Affiliations:** University of Technology Sydney

*UNSW Marketing Analytics Hackathon 2026 — Kiva prosocial-lending funding-speed challenge*

## Project Aim and Research Questions

Kiva lenders do not observe one another's decisions directly, so no dataset records an individual lender choosing one loan over another. What the data do record is *when* a loan finishes funding relative to when it was posted. We treat loan-level funding speed — and a binary indicator of funding within 24 hours — as an **observable behavioral proxy for aggregate lender decision-making**: the outcome the organizer's brief and judging rubric name directly, aggregated across many independent lenders rather than attributed to any one of them. Both outcomes are defined only among loans that were **eventually funded**; our development sample has no rejected/expired rows, so results describe how quickly funded loans complete, not whether a loan gets funded at all. If the full dataset includes unfunded/right-censored loans, we will add a separate funding-success or survival-analysis outcome rather than extend this claim to funding probability. This project asks which **controllable** narrative choices in a borrower's story are linked to faster funding, once **structural** loan constraints borrowers cannot easily change are held fixed — and whether that link is stable or shifts across time and segment.

**Central question.** Which narrative choices are associated with faster funding, for whom, and when, after separating presentation from structural constraint?

**Supporting questions.**

- Which narrative characteristics — specificity, tone, beneficiary focus, agency, and thematic framing — are associated with funding speed after controlling for loan amount, term, sector, region, and borrower structure?
- Does that association differ across pre-specified segments — analysis period, region group, and loan-size band by default, with a sector interaction as an explicitly scoped extension (restricted to adequately represented sectors)?
- Did the narrative–speed association shift across the **pre-pandemic, pandemic-disruption, and post-pandemic** periods — the project's central **evolutionary-perspective** test?
- How well do patterns learned on earlier loans predict later-period outcomes, and which controllable features carry the most practical opportunity?

We study aggregate patterns, not individual lender psychology, and we report **associations, never causal effects**.

## Proposed Analytical Approaches

### Descriptive Layer

We report target validity, missingness, and funding-speed distribution by period and segment, without treating unadjusted differences as effects.

### Interpretable Explanatory Models

A robust OLS model regresses log(1 + funding-speed-days) on pre-specified narrative, structural, and contextual predictors, with **heteroskedasticity-robust (HC3) standard errors**; a parallel binomial GLM models funding within 24 hours on the log-odds scale. Both report every pre-specified coefficient with a 95% CI, never selected post hoc, using association language throughout. Both degrade gracefully: an unidentifiable model reports a labeled diagnostic instead of an unstable coefficient, while any other well-identified model in the same run is still reported in full. This is not hypothetical: our 24-hour binary model hits exactly this failure mode (**quasi-complete separation** at n=100) and reports a diagnostic; the duration model fits without issue.

Three theoretically distinct framing measures anchor the narrative predictors, normalized per 100 words for comparability across description lengths:

- **Communal/family** framing — help-oriented cues (Allison et al., 2015; Moss et al., 2015)
- **Agentic/competence** framing — business-oriented cues (Allison et al., 2015)
- **Urgency** appeals — a pre-specified time-pressure dictionary, exploratory rather than drawn from the framing literature above

The default model fits three **pre-specified interactions** — family framing × analysis period, × region group, and × loan-size band — each independently dropped if a sample cannot support it; all three survive on the development sample. Region group uses a fixed observation-count threshold, not a hardcoded region list, so it automatically re-derives adequately represented regions from whatever data is passed in — the same principle sector needs before moving from opt-in to default. On this sample, neither loan amount nor sector reaches conventional significance (n=100, illustrative of feasibility only) — several sector estimates carry wide intervals at this size, and any predictor lacking variation is automatically dropped.

### Predictive Benchmarks

A gradient-boosted regressor (`HistGradientBoostingRegressor`) benchmarks nonlinear predictive performance against a training-median baseline and a regularized linear model, using **permutation importance** on held-out data, scored in day-space so rankings match the units a reader interprets. A parallel leakage-safe chronological classifier (`HistGradientBoostingClassifier`) predicts funding within 24 hours, reporting **ROC AUC, average precision, and Brier score** on the untouched holdout, fulfilling the binary outcome's predictive-validation requirement. On the development sample it discriminates well (holdout ROC AUC 0.88, average precision 0.79) despite a 20-row holdout.

### Leakage-Safe Validation

::: {.keep-together}
All evaluation is **chronological, not random**: models train on loans posted before a cutoff and are scored on loans posted after it, mirroring deployment. Every learned transformation — imputation, scaling, one-hot encoding, and the **TF-IDF/NMF topic model** — is fit on the training partition only and merely applied to the holdout; a dedicated exception type distinguishes "too little data" from unrelated bugs.
:::

On the 100-loan sample, an 80/20 chronological split already demonstrates this end to end: a naive baseline reaches 9.0 days holdout MAE; the boosted benchmark improves on it (6.1 days, R²=0.39); the regularized linear model overfits sharply (holdout R² −12.2 vs. training R² 0.87) — an honest, expected small-sample finding motivating more weight on the nonlinear benchmark until more data arrives.

Text-derived features are always compared against structural controls in the same model, so a narrative association is never reported without the comparison that lets a reader judge whether it is a genuinely controllable lever.

## Data Items to Be Used

We use borrower narrative text only through derived features, never as raw text predictors. `description` supplies word/sentence counts, readability proxies, per-100-word framing counts, VADER sentiment, concrete-detail indicators, and training-fitted topic proportions; the shorter `use`/`whySpecial` fields currently contribute only missingness indicators, with the same derived-feature treatment a natural extension for the full dataset.

- **Structural:** loan amount (log-transformed), repayment term, and repayment interval
- **Borrower:** group size and a **gender classification** (female, male, mixed, or unknown) that preserves missingness as its own category rather than imposing an assumed gender
- **Contextual:** sector, region, country purchasing-power parity, and posting year/month, collapsed into three pre-specified analysis periods (2016–2019, 2020–2021, 2022–2025); `country_name` is represented only through `country_iso`

We exclude, enforced by an **explicit predictor allowlist, not a blocklist**, so a leakage-sensitive field cannot be silently reintroduced:

- Any field whose posting-time availability is unverified (`fundsLentInCountry`)
- All post-outcome fields (raised date, funded status)
- Identifiers, image URLs, and borrower names
- Geographic coordinates (already summarized by country and region)

## Expected Outcomes and Managerial Relevance

We expect a small set of **controllable narrative choices** — plausibly specificity, agency framing, and concrete detail — whose association with funding speed is distinguishable from **structural constraints**, and to characterize when that association strengthens or weakens across periods, region, sector, and loan-size segments.

Our working hypothesis is that communal/family framing carried more weight during the 2020–2021 disruption period, consistent with evidence that external shocks reshape prosocial-lending behavior (Ding et al., 2025) — a testable, pre-specified expectation. On the 100-loan sample this interaction is not distinguishable from zero, expected at this size: the full dataset tests the same hypothesis with far more precision.

The duration model estimates average log-transformed pace; the 24-hour outcomes isolate what predicts the fastest-funding loans. Chronological validation yields an honest transfer estimate; the nonlinear benchmark's feature ranking offers a complementary, held-out check on the coefficients' levers.

For Kiva field partners, the managerial deliverable is a **segment-by-framing opportunity matrix** — which narrative choice is worth the writing effort, for which segment, flagged by confidence — plus copy guidance to pilot and a field-test agenda for the highest-confidence associations. Because recommendations are **associations with confidence intervals, not causal claims**, they are testable hypotheses to validate, not settled prescriptions. Guidance should improve clarity, specificity, and relevant detail, and must **not** coach exaggerated hardship, manufacture unreal urgency, or suppress relevant information; the same gain pursued through manipulation would undermine the trust prosocial lending depends on. Every limitation — sample size, the funded-only outcome boundary, the associational nature of every estimate — is reported alongside the findings.

**One-week execution sequence:** (1) full-dataset schema/coverage audit; (2) freeze segment-grouping thresholds against the audited counts; (3) feature-extraction QA; (4) re-run the chronological, explanatory, and classifier fits; (5) diagnostics and sensitivity checks; (6) build the segment-by-framing opportunity matrix; (7) reproducibility check and final write-up. Steps 3–4 and 7 reuse the pipeline already implemented and tested unchanged; steps 1–2, 5, and 6 are manual analytical work — auditing coverage, freezing grouping decisions, building the matrix — not automated stages. Region/loan-size thresholds already degrade gracefully if the full data's categories or date range differ, reducing step 2 to confirmation rather than redesign.

## References

Allison, T. H., Davis, B. C., Short, J. C., & Webb, J. W. (2015). Crowdfunding in a prosocial microlending environment: Examining the role of intrinsic versus extrinsic cues. *Entrepreneurship Theory and Practice*, 39(1), 53–73.

Ding, Y., Xu, H., & Tan, B. C. Y. (2025). A natural disaster reshapes prosocial microlending. *Information Systems Research*, 36(3), 1760–1779.

Moss, T. W., Neubaum, D. O., & Meyskens, M. (2015). The effect of virtuous and entrepreneurial orientations on microfinance lending and repayment: A signaling theory perspective. *Entrepreneurship Theory and Practice*, 39(1), 27–52.
