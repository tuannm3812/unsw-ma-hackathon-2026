# Cultural Blend — Kiva funding-speed research

Updated 2026-11-08. One story across the competition work and the October and
November research extensions. Every number here is traced in the
[claims register](presentation/claims_register.md).

**Finalist, UNSW Marketing Analytics Hackathon Challenge 2026.** Cultural
Blend (Sophia and Tuan) was one of eight finalist teams selected from 44
registered teams involving 133 students at 19 universities across eight
countries. The final took place on 4 September 2026.
[Official UNSW results](https://www.unsw.edu.au/business/our-schools/marketing/news-events/student-events/MA-hackathon).

## Bottom line

Loan descriptions carry measurable information about how fast a Kiva loan
funds: adding text to a structure-only forecast lowered error in every one of
five test years. Most individual framing associations are also small enough to
bound. What the data cannot show is that rewriting a description makes a loan
fund faster, so the next step is measurement and a small truthful pilot, not
platform-wide writing advice.

## Problem and data

Which narrative choices in Kiva loan descriptions are associated with faster
funding, and how do those patterns differ across contexts and periods? The
project analysed **1,453,846 loan records from 2016–2025**; six negative
durations were excluded, leaving **1,453,840 valid completed durations**,
including 1,637 refunded records. Outcomes were time from listing to completed
funding and completion within 24 hours.

Two facts shape every claim. First, the share of loans funded within a day fell
from 46.0% before the pandemic to 30.3% during it and 30.0% after, a
descriptive shift that never recovered. Second, 96.4% of loans were disbursed
to borrowers before listing, so platform funding time often reflects a partner
replenishing capital rather than a borrower waiting. The data contain only
loans that eventually funded, so they cannot say whether a loan funds at all.

## Approach: three layers of evidence

| Layer | Question | Method |
| --- | --- | --- |
| August primary run | Which narrative features are associated with speed, and how certain is that? | OLS on log(1 + days) and a binomial GLM, HC3 versus country-clustered uncertainty, within-region contrasts; chronological 2024–2025 holdout for prediction |
| October extension | Do the associations survive richer controls, including programme text? | Country-clustered OLS/LPM with and without an unvalidated programme-text proxy, BH-adjusted |
| November benchmark | How much does text add to a forecast built on loan structure alone? | Matched feature blocks on identical rows, as-of training cohorts, five annual windows 2021–2025, paired month and country resampling |

A fourth, exploratory check (8 November) asks which associations are small
enough to rule out a practically large effect, using equivalence tests on the
October coefficients.

## Findings

**1. Large row counts did not remove country-level uncertainty.** Of 120 terms
significant under HC3, 64 lost significance once errors were clustered by
country. Urgency language went from p < 0.001 to p = 0.49 for duration. The two
regional family-framing patterns each rest on two countries, so their wider
heuristic intervals cross zero.

**2. Most framing associations are small, and two are unresolved.** With a
practical bound of about ±5% of funding time and ±1 percentage point of
same-day completion per extra mention per 100 words, family, basic-needs,
business, agency and third-person framing are bounded in both October
specifications. Urgency and first-person framing are not: their intervals
still allow associations of roughly 6–14%. "Not significant" for urgency meant
"too uncertain", not "no effect". The bound was set after seeing the
estimates, so this is exploratory.

**3. Some associations persist under richer controls.** Third-person framing
stays associated with faster funding with programme controls (−0.0081
log points per mention per 100 words; BH p moves from 0.012 to 0.061), and
business framing is linked to a 0.26 percentage-point lower same-day rate
per extra mention per 100 words (programme-adjusted, BH p = 0.006).
These are associations, not effects of writing.

**4. Text adds forecast information.** On 728,640 evaluation records, adding
description form, lexical measures and TF-IDF lowered the linear model's error
in 5 of 5 years, by 0.26–0.39 days (median 0.29). A compact tree model gained
only 0.001–0.042 days, and country resampling included zero in 4 of 5 linear
comparisons. In 2025, text improved error and probability scores but slightly
lowered ranking (AUC 0.893 to 0.888). Richer text may encode purpose,
location or programme templates as well as framing.

**5. Structure still predicts most of the variation.** The primary
HistGradientBoosting benchmark reached MAE 5.20 days and R² 0.542 on 278,887
holdout loans; the 24-hour classifier reached ROC AUC 0.900. These are
retrospective predictions on completed loans, not deployment estimates.

## What this means

For Kiva and its partners, the evidence supports two things: treat
description text as useful context in research and forecasting, and stop
treating any single framing tip as proven. It does not support country-level
writing rules or a claim that editing speeds funding. The three next steps are:

1. **Validate the measures.** Dual-code a sample of narratives for clarity,
   specificity, need and agency, then freeze definitions.
2. **Close the data gaps.** Partner identifiers, all listings including expired
   ones, and original text versions.
3. **Design one truthful pilot** with partners: a clarity prompt, a control, a
   practical-effect threshold agreed in advance, and enough power to detect it.

## Limits

Observational associations; 48 country clusters with sparse regions; a
programme proxy that does not identify partners; completed-funding records only;
snapshot rather than listing-time field values; retrospective prediction windows.
Historical slide claims such as "the story barely registers" are superseded; see
[evidence and corrections](2_evidence_and_corrections.md). The submitted proposal
and competition deck are preserved as historical records.

## LinkedIn achievement entry

**Title:** Finalist — UNSW Marketing Analytics Hackathon Challenge 2026

**Organisation:** UNSW Business School

**Date:** September 2026

Selected as one of eight finalist teams from 44 registered teams in the UNSW
Marketing Analytics Hackathon Challenge 2026. As part of Cultural Blend with
Sophia, analysed 1.45 million Kiva loan records to investigate associations
between loan narratives and funding speed. Our work combined text analysis,
statistical inference, chronological predictive validation and sensitivity
checks, with an emphasis on reproducibility and responsible interpretation.

This is an achievement description for Tuan's profile; it does not assign an
unverified individual contribution split or describe finalist recognition as
a prize win. [Official recognition](https://www.unsw.edu.au/business/our-schools/marketing/news-events/student-events/MA-hackathon).
