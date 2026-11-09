# Cultural Blend — Kiva funding-speed research

Updated 2026-11-09. One story across the competition work and the October and
November research extensions. Every number here is traced in the
[claims register](presentation/claims_register.md).

**Finalist, UNSW Marketing Analytics Hackathon Challenge 2026.** Cultural
Blend (Sophia and Tuan) was one of eight finalist teams selected from 44
registered teams involving 133 students at 19 universities across eight
countries. The final took place on 4 September 2026.
[Official UNSW results](https://www.unsw.edu.au/business/our-schools/marketing/news-events/student-events/MA-hackathon).

## Bottom line

Kiva loans that will fund slowly can largely be spotted from loan details at
posting, so the useful response has three steps: **predict** slow loans,
**prioritise** lender-side support for them, and **test** before giving any
writing advice. In a retrospective check, a boosted tree on loan details flags
slow loans 2.63–4.04 times better than chance and beats a simple historical
lookup in every test year. Most individual framing associations are small
enough to bound, and text adds only a small, inconsistent forecast gain. What
the data cannot show is that rewriting a description makes a loan fund faster,
so writing advice waits for a small truthful pilot.

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

A fourth, exploratory set of checks (8–9 November) asks which associations are
small enough to rule out a practically large effect, using equivalence tests on
the October coefficients, a corrected wild cluster bootstrap, subgroup refits, a
historical lookup baseline and tuned forecasters.

## Findings

**1. Large row counts did not remove country-level uncertainty.** Of 120 terms
significant under HC3, 64 lost significance once errors were clustered by
country. Urgency language went from p < 0.001 to p = 0.49 for duration. The two
regional family-framing patterns each rest on two countries, so their wider
heuristic intervals cross zero.

**2. Most framing associations are small, and two are unresolved.** With a
practical bound of about ±5% of funding time (±0.05 on log(1 + days), about
4.5–4.7 hours at the 2.85-day median) and ±1 percentage point of
same-day completion per extra mention per 100 words, family, basic-needs,
business, agency and third-person framing are bounded in both October
specifications. Urgency and first-person framing are not: their intervals
still allow associations of roughly 6–14%. "Not significant" for urgency meant
"too uncertain", not "no effect". The bound was set after seeing the
estimates, so this is exploratory. Within 10 subgroups of period, loan size,
gender and region, a wild cluster bootstrap on the programme-adjusted model
confirms family and third-person framing within ±5% of funding time
(±0.05 on log(1 + days)) in all 10.
Business and agency each hold in 9 of 10. Basic needs, gratitude and sentiment
hold in 5, 5 and 7 of 10, so they cannot be confirmed in every group; that does
not make them large. Of 360 subgroup tests, 6 pass adjustment and none is urgency
or agency, so no group shows a confirmed large framing effect.

**3. Almost nothing passes the strictest test.** Nine measures, two outcomes and
two models make 36 tests: 5 pass the country-clustered test, 4 a wild cluster
bootstrap, and 1 after adjusting for multiple testing. That one is third-person
framing for funding time in the expanded model (−0.9% in 1 + days per extra
mention per 100 words; bootstrap p 0.0009, BH p 0.008), or 49.7 minutes on a
typical 2.85-day loan. With programme controls it does not pass (bootstrap
p 0.128, BH p 0.426). Loan details sit on another scale: a doubled loan amount
goes with +44.6% and a month of term with +8.6% in 1 + days. These are
associations, not effects of writing.

**4. Text adds a small, inconsistent forecast gain.** On 728,640 evaluation
records, adding description form, lexical measures and TF-IDF lowered the linear
model's error in 5 of 5 years, by 0.26–0.39 days (median 0.29), and shuffled text
keeps 42–61% of that gain, so about half is context. A compact tree model gained
only 0.001–0.042 days. Fixed trees gain up to about 0.15 days from text; in an
exploratory run, tuned trees reach 0.16–0.22 in 2021. Country resampling included
zero in 4 of 5 linear comparisons. In 2025, text improved error and probability
scores but slightly lowered ranking (AUC 0.893 to 0.888). Richer text may encode
purpose, location or programme templates as well as framing.

**5. Loan details predict most of the variation, and the flag beats a lookup.**
The primary boosted tree reached MAE 5.20 days and R² 0.542 on 278,887 holdout
loans; the 24-hour classifier reached ROC AUC 0.900. Flagging the top 10% of
predicted-slow loans gives 2.63–4.04× lift on each year's slowest 20%, against
1.97–2.74× for a training-only lookup by country, sector and month. The 95%
range of that gap is above zero in every year, with a lowest bound of +0.08 in
2021 when resampling by country. Median within-country precision is 0.49–0.56,
against 0.22–0.29 for the lookup. An exploratory run tuned a boosted tree and
XGBoost on the year before each test year. On loan details, tuned trees were
lowest in 3 of 5 years, by at most 0.06 days, and fixed settings won 2021 and 2022, so tuning did
not clearly help; XGBoost beat the tuned boosted tree in 2 of 5 years. These are
retrospective predictions on completed loans, not deployment estimates.

**6. Loan purpose tracks funding speed, but purpose is not a lever.** Against the
average loan, Education runs −68.7% and Clothing +30.2% in 1 + days. In an
exploratory 20,000-description sample, sanitary and water themes average 1.5 and
1.8 days; they fund fast, but that speed largely reflects which countries and
loan types they are, and their adjusted ranges include zero. On all completed
loans, the Sanitation & Hygiene sector is modestly faster (−13.4%) and the toilets
activity is not distinct from farming (−5.7%, range −19.7% to +10.7%). These are
associations among completed loans.

## What this means

For Kiva and its partners, the evidence supports a three-step approach. It does
not support country-level writing rules or a claim that editing speeds funding.

**Predict.** Score each listing's risk of slow funding at posting, from loan
details. The flag has only been checked on past loans, so it must be recalibrated
and validated by country before use.

**Prioritise.** Send lender-side support to flagged loans: feature them, offer
matching funds, alert lenders who follow the sector, and ask the partner to check
the listing. 96.4% of loans reach the borrower before listing, so the wait ties up
partner capital. What these levers do to funding speed is unmeasured, so each needs
a controlled pilot.

**Test.** Writing advice has to pass three gates, in order:

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
Loan photos were not analysed, because fetching them at scale needs Kiva's
permission. Historical slide claims are superseded; see
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
