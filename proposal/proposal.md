# Beyond a Good Story: When and for Whom Persuasive Loan Narratives Accelerate Prosocial Funding

**Team members:** Manh Tuan Nguyen

**Affiliations:** University of Technology Sydney

*UNSW Marketing Analytics Hackathon 2026 — Kiva prosocial-lending funding-speed challenge*

## Project Aim and Research Questions

Kiva lenders do not observe one another's decisions directly, so no dataset records an individual lender choosing one loan over another. What the data do record is *when* a loan finishes funding relative to when it was posted. We treat loan-level funding speed — and a binary indicator of funding within 24 hours — as an **observable behavioral proxy for aggregate lender decision-making**: the outcome the organizer's brief and judging rubric name directly, aggregated across many independent lenders rather than attributed to any one of them. This project asks which **controllable** narrative choices in a borrower's story are associated with faster funding, once **structural** loan constraints borrowers cannot easily change are held fixed — and whether that association is stable or shifts across time and segment.

**Central question.** Which narrative choices accelerate funding, for whom, and when, after separating presentation from structural constraint?

**Supporting questions.**

- Which narrative characteristics — specificity, tone, beneficiary focus, agency, and thematic framing — are associated with funding speed after controlling for loan amount, term, sector, region, and borrower structure?
- Do these associations differ by region, sector, gender classification, group status, or loan size?
- Did the narrative–speed association shift across the **pre-pandemic, pandemic-disruption, and post-pandemic** periods — the project's central **evolutionary-perspective** test?
- How well do patterns learned on earlier loans predict later-period outcomes, and which controllable features carry the most practical opportunity?

We study aggregate patterns, not individual lender psychology, and we report **associations, never causal effects**.

## Proposed Analytical Approaches

### Descriptive Layer

We report target validity, missingness, and funding-speed distribution by period and segment, without treating unadjusted differences as effects.

### Interpretable Explanatory Models

A robust OLS model regresses log(1 + funding-speed-days) on pre-specified narrative, structural, and contextual predictors, with **heteroskedasticity-robust (HC3) standard errors**; a parallel binomial GLM models funding within 24 hours on the log-odds scale. Both report every pre-specified coefficient with a 95% confidence interval — never selected post hoc by significance — using association language throughout. Both also degrade gracefully rather than misleadingly: if a specific model cannot be reliably identified on a given sample, it reports a labeled diagnostic instead of an unstable coefficient, while any other, well-identified model in the same run is still reported in full. This is not hypothetical: on our development sample, the 24-hour binary model already hits exactly this failure mode (**quasi-complete separation**, since some sector/region cells share one outcome at only 100 rows) and correctly reports a diagnostic rather than an unstable estimate, while the duration model fits without issue on the same data.

Three theoretically distinct framing measures anchor the narrative predictors, following established crowdfunding-narrative research and normalized per 100 words for comparability across description lengths:

- **Communal/family** framing
- **Agentic/competence** framing
- **Urgency** appeals

The default model now fits three **pre-specified interactions** — family framing × analysis period, × region, and × loan-size band — each independently dropped if a given sample cannot support it. Region is grouped into major regions plus "Other" under the same "adequately represented" logic applied to sector below (one raw region has a single observation); all three interactions survive on the development sample. Narrative × sector remains deliberately opt-in, since restricting it to "adequately represented sectors" is a sample-specific judgment the default formula cannot safely make.

On the same development sample, loan amount is significantly associated with slower funding (coefficient 0.84 in this log-log specification, 95% CI [0.44, 1.24], p<0.001), and the Education sector is associated with faster funding relative to the reference sector (p=0.032) — illustrative of feasibility, not a full-data conclusion; several other sector estimates carry wide confidence intervals at this sample size, and any predictor lacking variation in a given sample is automatically dropped.

### Predictive Benchmark

A gradient-boosted regressor (`HistGradientBoostingRegressor`) benchmarks nonlinear predictive performance against a training-median baseline and a regularized linear model, using **permutation importance** on held-out data, scored in day-space so feature-importance rankings match the units a reader actually interprets.

### Leakage-Safe Validation

::: {.keep-together}
All evaluation is **chronological, not random**: models train on loans posted before a cutoff and are scored on loans posted after it, mirroring how a model would actually be used to score newly posted loans. Every learned transformation — missing-value imputation, feature scaling, one-hot encoding, and the **TF-IDF/NMF topic model** fit on narrative text — is fit on the training partition only and merely applied, never refit, to the holdout; a dedicated exception type distinguishes "this split has too little data" from unrelated bugs, so a too-small split degrades gracefully into a labeled diagnostic instead of a misleading number.
:::

On the 100-loan development sample, an 80/20 chronological split already demonstrates this discipline end to end:

- A naive baseline reaches a holdout MAE of 9.0 days
- The boosted benchmark improves on it (MAE 6.1 days, R²=0.39)
- The regularized linear model still overfits sharply despite its L2 penalty (holdout R² −12.2, versus a training R² of 0.87) — an honest, expected finding at this sample size, showing that regularization alone does not substitute for more data, and one that motivates weighting the nonlinear benchmark more heavily once the full dataset is available

Text-derived features (framing counts, sentiment, latent topics) are always compared against structural controls (loan amount, term, sector) in the same model, so a narrative association is never reported without the structural comparison that lets a reader judge whether it is a genuinely controllable lever.

## Data Items to Be Used

We use borrower narrative text only through derived features, never as raw text predictors. The primary `description` field supplies word/sentence counts, readability proxies, per-100-word framing counts, VADER sentiment, concrete-detail indicators, and training-fitted topic proportions; the shorter `use` and `whySpecial` fields currently contribute only missingness indicators, with the same derived-feature treatment a natural, already-supported extension for the full dataset.

Structural, borrower, and contextual predictors:

- **Structural:** loan amount (log-transformed), repayment term, and repayment interval
- **Borrower:** group size and a **gender classification** (female, male, mixed, or unknown) that preserves missingness as its own category rather than imposing an assumed gender
- **Contextual:** sector, region, country purchasing-power parity, and posting year/month, collapsed into three pre-specified analysis periods (2016–2019, 2020–2021, 2022–2025) spanning the dataset's full range; `country_name` is represented only through `country_iso` to avoid duplicating the same geographic signal

We exclude, enforced by an **explicit predictor allowlist, not a blocklist**, so a leakage-sensitive field cannot be silently reintroduced by a future edit:

- Any field whose posting-time availability is unverified (`fundsLentInCountry`)
- All post-outcome fields (raised date, funded status)
- Identifiers, image URLs, and borrower names
- Geographic coordinates (already summarized by country and region)

## Expected Outcomes and Managerial Relevance

We expect to identify a small set of **controllable narrative levers** — plausibly specificity, agency framing, and concrete detail — whose association with funding speed is distinguishable from **structural constraints** like requested amount, and to characterize when that association strengthens or weakens across periods, region, sector, and loan-size segments.

Our working hypothesis is that communal/family framing carried more weight during the 2020–2021 disruption period, when prosocial motivations plausibly intensified, than in the calmer surrounding periods — a testable, pre-specified expectation. On the 100-loan sample this interaction is not distinguishable from zero, expected at this size and reported as such: the full dataset tests the same hypothesis with far more precision, whichever direction it moves.

The two outcomes should tell complementary stories: the duration model estimates how each predictor relates to average, log-transformed funding pace, while the 24-hour indicator isolates what predicts the fastest-funding loans specifically. The chronological validation yields an honest estimate of how well patterns learned on historical loans transfer to newly posted ones, and the nonlinear benchmark's feature-importance ranking offers a second, model-agnostic check on which levers the coefficients single out.

For Kiva field partners and borrower-support staff, the managerial payoff is segment-specific, uncertainty-aware guidance on which narrative choices are worth the writing effort — not a universal template. Because recommendations are **associations with confidence intervals, not causal claims**, they are testable hypotheses for field partners to validate, not settled prescriptions. We frame ethical boundaries explicitly: guidance should improve clarity, specificity, and relevant detail — and must **not**:

- Coach exaggerated hardship claims
- Manufacture urgency that is not real
- Suppress relevant borrower information

The same growth in funding speed pursued through manipulation would undermine the trust prosocial lending depends on. Every limitation — sample size, non-identified segments, the associational nature of every estimate — is reported alongside the findings themselves.

The core pipeline — all three default segment interactions included — is already implemented, tested, and running end to end; the full dataset needs only re-running that same code, plus the sector interaction's category grouping as a small, already-scoped second pass, comfortably within the one-week window.

## References

Moss, T. W., Neubaum, D. O., & Meyskens, M. (2015). The effect of virtuous and entrepreneurial orientations on microfinance lending and repayment: A signaling theory perspective. *Entrepreneurship Theory and Practice*, 39(1), 27–52.
