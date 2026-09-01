<!-- Markdown rendering of docs/presentation/qa_pack.html (the "Question Time" artifact).
     The HTML file is the styled original; this file is the same content for reading on GitHub. -->

Final-round briefing · UNSW Marketing Analytics Hackathon 2026 · Team Cultural Blend

# Question Time

The full analysis report, and prepared answers for the 10-minute Q&A that follows the presentation — up to three audience questions first, then the judges. Every number here comes from a verified run; nothing is recalled from memory.

**Final** 2026-09-04, UNSW Business School **Slides due** 2026-09-03 5pm Sydney **Q&A** 10 min, audience then judges

[Part I · The report](#report) [Part II · Audience Qs](#qa-audience) [Headline finding](#qa-headline) [Robustness](#qa-robust) [Methods & data](#qa-methods) [Other findings](#qa-other) [Crib sheet](#crib)

## Part I · The report

### Executive summary

We asked whether the way a Kiva borrower's story is written — family appeals, competence language, urgency, tone — is associated with how fast the loan funds, across 1,453,846 real loans (2016–2025). The answer that survives serious testing: **structure dominates story.** What a loan is for, where it's from, how big it is, and how it's repaid are linked to funding speed roughly an order of magnitude more strongly than any writing choice. Narrative framing has **no robustly supported association — absence of robust evidence, not proof of no effect**. One descriptive pattern — family framing and faster funding in **two pooled two-country categories** (Middle East = Palestine + Yemen; Central America = Honduras + Nicaragua; together ~5% of loans) — is consistent in direction across all three of our model fits, but each rests on exactly two countries, and under a few-cluster reference (t with 1 degree of freedom) it is not significant in any fit. It is a hypothesis for a country-stratified test, not a finding.

The methodological arc is the differentiator: a standard analysis of this dataset would have confidently recommended urgency language platform-wide, and a slightly better one would have recommended family framing in two regions. We tested both, across multiple review rounds, and neither obtained robust support. What we present is what's left standing after we tried hard to kill it — and for narrative framing the finding is that the available evidence does not support a writing recommendation. The effects themselves remain uncertain; we are reporting a failure to obtain robust support, not proof of no effect.

### The question

When a borrower's story leans on family, competence, or urgency — does the loan fund faster? And does the answer depend on who's asking, where, and when? Framing matters because it's the one factor a platform can actually coach; loan size, sector, and geography can't be rewritten after the fact.

### Data and guardrails

- **1,453,840 of 1,453,846 loans usable** (99.9996%) — outcome is days from posting to full funding, log-transformed; plus a funded-within-24h yes/no version.
- **Leakage-safe chronological validation**: models train on 2016–2023 (1,174,953 loans), tested only on 2024–2025 (278,887 loans) they never saw. Imputers, encoders and text vectorizers fit on training data only.
- **Association-only language, enforced in code**: the pipeline's own report generator never writes "causes" or "proves". Borrowers weren't randomly assigned a writing style.
- **Two separately built implementations (same data)**: an authoritative tested pipeline (`authoritative`, `src/` + committed report snapshot) and self-contained Kaggle notebooks (`notebook`). Where they disagree, we report the disagreement.

### Predictive results (the uncontroversial half)

- Gradient-boosted model: **MAE 5.20 days, R² = 0.54** on the never-seen holdout (authoritative; notebook: 5.56 / 0.49). Ridge baseline: MAE 6.63 days.
- 24-hour funding classifier: **ROC AUC 0.90, average precision 0.83** — a strong retrospective ranking signal among eventually-funded loans (expired/withdrawn listings aren't in the data), no framing insight required; a live early-warning flag would first need all posted listings incl. expired/withdrawn outcomes, then retraining and validation on that population.
- SHAP on the boosted model: loan amount and repayment term dominate; no family/agency/urgency feature reaches the top 15. Only sentiment appears (11th).

### The verification arc — three rounds, each changing the answer

Round 1 · Standard analysis

#### Almost everything "significant"

OLS with HC3 robust errors on 1.45M rows: urgency framing a clean win (p \< 0.001), family framing conditional on period, region and size. The story most teams would present.

Round 2 · Cluster by country

#### Half of it evaporates

Loans from one country share partners, templates, conditions. Clustered standard errors: 44–50% of coefficients change significance conclusion. Urgency's p-value goes 0.000 → ~0.44. Not fabricated — fragile.

Round 3 · Test the right quantity

#### The question itself was wrong

An interaction coefficient tests difference-from-Africa, not "does framing do anything *here*". Computing each region's average within-region slope resolved a fake contradiction (Asia) and left two apparent survivors — each identified by only two countries.

### What survives — the findings table

| Claim | Evidence | Status |
|----|----|----|
| Structure dominates: sector, region, loan size, repayment, gender carry the largest associations | e.g. Water −1.12, ME region −1.07, male +0.43 (notebook, log-days); the largest terms survive clustering in both pipelines | `robust` |
| Pandemic-era slowdown persists through 2025: share funded in 24h fell 46.0% → 30.3% and stayed at 30.0% | 589,823 / 298,549 / 565,474 loans per era | `robust` |
| Gender gap: female-posted median 2.3 days vs male-posted 7.7 | +0.43 coefficient holding all else fixed; survives clustering | `robust` |
| Family framing ↔ faster funding in two pooled categories (Palestine+Yemen; Honduras+Nicaragua) — pooled, not per-country | Same direction in all 3 fits; conventional clustered p\<0.05, but few-cluster t(1) p = 0.06–0.21 — intervals span zero | `descriptive pattern — not statistically supported` |
| Urgency framing helps | HC3 p\<0.001 → clustered p≈0.44 (notebook) · 0.49 / 0.22 (authoritative) | `does not survive` |
| Family framing depends on timing / loan size | All period & size interactions fail clustering | `does not survive` |
| Agency/competence language helps | Null in notebook; fragile (HC3-only) in authoritative 24h model | `no reliable link` |
| Positive sentiment ↔ slower funding | Survives clustering in authoritative fits (p≈0.01/0.02), not in notebook (p≈0.25) | `genuinely open` |
| Family framing in Asia (opposite direction) | p = 0.0535 / 0.0846 / 0.2860 across the 3 fits | `not significant — our earlier claim was a computational artifact, corrected` |
| Family framing in North America (Haiti — 1 country) | Significant in 1 of 3 fits (p = 0.0094 authoritative duration only) | `reported, not claimed` |
| Family × Water / Construction sector interactions | Survive clustering in both authoritative models — but as difference-from-Agriculture only | `within-sector slopes not yet computed — not claimed` |

### Limitations we state before anyone asks

- **Association, never causation.** No borrower was randomly assigned a writing style.
- **Speed among funded loans**, not whether a loan funds at all — the dataset contains completed loans.
- **Two countries cannot carry an inference.** The one family-framing pattern pools two countries per category; a normal-reference clustered p-value overstates its precision, a few-cluster reference makes it non-significant, and nothing can separate "family framing works here" from "something else is different about Palestine and Yemen".
- **Framing measured by transparent dictionaries**, not a claim to capture all persuasion. Topic modeling and sentiment complement, not complete, the picture.
- **Magnitudes are specification-sensitive even where significance is not** (Middle East slope: −0.124 vs −0.073 across our two model families, ~1.7×).

### Recommendations

- **Treat the classifier as a prototype, not a product.** Holdout AUC 0.90 (Brier 0.116) is a retrospective ranking result among loans that eventually funded — the data contain no expired/withdrawn listings, so it is not validated for flagging loans that may never fund. Before any pilot: obtain all posted listings including expired/withdrawn outcomes, define the operational target and censoring window, retrain and validate on that population; only then threshold, calibration, fairness checks and a prospective test.
- **Don't ship writing rules from this data.** Urgency advice would have been wrong; family advice has no supporting evidence for ~95% of loans.
- **If anyone wants to chase the family-framing pattern, do it as a country-stratified A/B test** in the two pooled categories — designed to find out whether any real association exists at all and which countries, if any, carry it. A hypothesis, not a finding, and certainly not a rollout.
- **Investigate structure, not copy**: why Water and Education loans fund in a fraction of the time Agriculture does is a platform question worth more than any style guide.
- **Adopt the test-before-recommending discipline** — the process finding is itself the practical implication.

## Part II · Q&A preparation

Format: up to three audience questions first, then judges. Audience questions skew practical and non-technical; judge questions probe methods. Each card: the spoken answer (~30–45 seconds), backup numbers if pressed, and the trap to avoid. `[HARD]` marks the hostile versions.

### Likely audience questions

#### A1 · So… does storytelling matter or not?

**Answer:**

Far less than everyone assumes — and that's the finding. How a loan is structured — its size, sector, country, repayment plan — is linked to funding speed about ten times more strongly than any writing choice. Every writing-style effect that looked significant at first collapsed when we tested it properly — including the last one standing, a family-framing pattern in two small country-groups (Palestine with Yemen, Honduras with Nicaragua) that points the same way in every fit but rests on two countries each and isn't significant once that is accounted for. So: polish the structure conversation before the copywriting one.

**Backup:**

Raw correlations: loan amount r = +0.43, repayment term r = +0.28, vs family r = −0.02, urgency r = +0.01, agency r = +0.06 (the largest narrative correlation — and toward *slower*). So "about ten times" is 7× against the biggest narrative signal, 20× against the others. SHAP: no framing feature in the boosted model's top 15.

**Trap:** don't say "storytelling doesn't matter" — say the honest version: *we couldn't find reliable evidence it matters, and we looked hard*. Absence of robust evidence ≠ evidence of absence.

#### A2 · What should a borrower actually write, then?

**Answer:**

Our data can't hand a borrower a winning script — and we think saying so is more useful than pretending otherwise. A typical analysis of this dataset would tell every borrower to add urgent language; we tested that and it doesn't hold up. Our honest advice is boring: write a clear, complete description — not because our data shows it speeds funding, but because nothing we tested beats it — and let the platform work on what is actually linked to speed — how loans are sized, categorized and surfaced. The one family-framing pattern (Palestine+Yemen, Honduras+Nicaragua) is a pooled, descriptive average that doesn't survive a few-cluster test — worth a properly designed experiment, not advice for any borrower.

**Trap:** a questioner may want a tip they can tweet. Resist inventing one — "we tested the popular tip and it failed" is the memorable answer.

#### A3 · Why did funding get slower after 2020, and will it recover?

**Answer:**

Pre-pandemic, 46% of loans funded within a day. During the disruption that fell to 30% — and four years later it's still 30%. Whatever changed — lender attention, competition for capital, the mix of loans posted — it's structural, not a shock that faded. We can't say from this data *why*; we can say a "it'll bounce back on its own" assumption has already been wrong for four years, which makes it an operational question worth someone's time.

**Backup:**

46.0% → 30.3% → 30.0% across 589,823 / 298,549 / 565,474 loans. The era shift survives clustering in the authoritative duration model — both post-2019 period terms significant (clustered p = 0.0014 / 0.0031), direction: slower than pre-pandemic.

### The headline finding

#### B1 · Your key claim rests on two countries per region. Is that a finding at all? `[HARD]`

**Answer:**

You've named the exact limitation we'd point to ourselves, and it's why we call this exploratory. In our data "Middle East" is Palestine and Yemen; "Central America" is Honduras and Nicaragua. Because we cluster standard errors by country — treating same-country loans as related, not independent — a two-country group carries little independent evidence, and the estimate can't separate "family framing works here" from "these two countries are unusual." We went further than conceding: the conventional clustered p-value that made it look significant uses a normal approximation that's only trustworthy with many clusters, so we re-referred it to a t distribution with one degree of freedom — a deliberately harsh sensitivity screen, a conservative heuristic rather than calibrated inference — and it is not significant in any of our three fits (p ≈ 0.06 to 0.21). What's left is a descriptive pattern: same direction every time, pooled per pair so it can't even say whether Palestine or Yemen drives it. Our recommendation is scoped to exactly that: a country-stratified A/B test in those markets, presented as a hypothesis, not a claim about regions, countries, or significance.

**Backup:**

ME: −0.124 (notebook), −0.073 (authoritative duration), +0.175 (authoritative 24h log-odds — inverted sign, also faster), all clustered p ≤ 0.004. CA: −0.062 / −0.074 / +0.103, all p \< 0.0001. The clustered covariance uses all 48 country clusters — the SE isn't computed from two — but the contrast is *identified* only by those two.

**Trap:** don't defend it as a finding at all. Concede immediately, say we applied the few-cluster sensitivity screen to our own result, and pivot to the discipline — conceding fast is what makes the rest credible.

#### B2 · How big is the family-framing association in practice?

**Answer:**

Descriptively, in the two pooled categories: each additional family mention per hundred words goes with roughly 6–12% faster funding on average across each pair of countries — but with a few-cluster interval that comfortably spans zero, so treat the magnitude as illustrative — the range depends on which of our two model specifications you use, which is itself worth noting: the direction is stable across specifications (as was the conventional normal-reference significance, before the few-cluster screen rejected it), the magnitude less so. For scale, that's real but modest next to structure: in our notebook model a Water-sector loan is associated with funding in roughly a third of the time an Agriculture loan takes.

**Backup:**

Slope on log(1+days) per mention/100 words: Middle East −0.124 / −0.073 → ~12% / ~7% shorter; Central America −0.062 / −0.074 → ~6% / ~7%. Water sector −1.12 → ≈ ×0.33 (notebook). All approximate transformations of log-scale coefficients.

#### B3 · Couldn't the pooled-category result just be those countries being different — conflict zones, say? `[HARD]`

**Answer:**

Yes — and we can't rule that out, which is exactly why we won't call it causal. Worse for the country framing: the estimate pools each pair, so we can't even say which of the two countries drives it. Palestine and Yemen are conflict-affected; lenders may respond differently to family language in that context, or the field partners there may write differently, or something else entirely may travel with those countries. Clustering by country adjusts the uncertainty for within-country dependence, but no amount of statistics separates the framing from the country when the group only contains two of them. That's what the A/B test recommendation is for: it's the design that *would* separate them.

### The robustness story

#### C1 · Half your coefficients changed significance when you clustered. Doesn't that mean your model is wrong? `[HARD]`

**Answer:**

It means the standard *assumption* was wrong, and we corrected it — the model's coefficients don't change at all, only the honesty of the uncertainty around them. Every analysis of this dataset that treats 1.45 million loans as 1.45 million independent observations will produce those overconfident p-values; loans from the same country share field partners, templates, and local conditions, so the effective sample is much smaller than the row count. The change was also selective in an informative way: the largest structural findings — the big sector and region gaps, gender, loan amount, repayment structure — all held, while the flips concentrated in narrative-framing terms plus some of the smaller sector and region categories. The fragile results were overwhelmingly the framing ones.

**Backup:**

Notebook: 20/45 coefficients flip (44%). Authoritative, both models: 64/128 (50%), of which 40 (62.5%) are narrative/sentiment terms. 48 country clusters. Urgency: HC3 p\<0.001 → clustered 0.44 (notebook duration); 0.49 / 0.22 (authoritative duration / 24h).

**Trap:** don't let "your p-values changed" be framed as instability. The framing is: *we'd rather report 10 findings that are real than 30 that are artifacts.*

#### C2 · Why cluster by country rather than field partner, sector, or time?

**Answer:**

Country is the strongest grouping available in our data for the dependence we're worried about — field partners operate within countries, and they're the plausible source of shared writing templates and shared local conditions. The dataset has no partner identifier, so we clustered at the coarser level that contains partners: country. That's the conservative direction — coarser clusters allow *more* correlation between loans, so country-level clustering produces wider standard errors than partner-level clustering would. With a partner ID we'd cluster there instead for a sharper estimate of where the dependence really sits, but our results were tested against the coarser of the two corrections - the one that allows more dependence - not the finer one.

**Backup:**

48 country clusters, only 5 with \<30 loans. Standard practice: cluster at the coarsest level you believe dependence operates at — clustering coarser than the truth is conservative (wider SEs), clustering finer than the truth understates uncertainty.

#### C3 · Why HC3 standard errors in the first place?

**Answer:**

HC3 is the conservative default for unequal variance — funding speed is heavily skewed, so classical standard errors would understate uncertainty. But the honest answer is that at 1.45 million rows the choice among HC0–HC3 barely matters; they converge. The assumption that actually bound our results was independence, not heteroskedasticity — which is why the check that mattered was clustering, and it changed our headline findings where the HC-variant choice changed nothing.

**Trap:** this is a knowledge-check question. Answer it in one breath and steer to the assumption that mattered — that's where the analysis has something to say.

#### C4 · What's the difference between your interaction test and the within-region average — and why did it matter?

**Answer:**

An interaction coefficient answers "is this region's family-framing slope different from Africa's?" — which is not the question anyone actually cares about. The useful question is "within this region, is family framing associated with speed at all?" And because family framing is interacted with several factors at once in our model, answering that properly means averaging the slope over each region's own mix of loan sizes and time periods, not reading a single coefficient. Getting this wrong isn't hypothetical for us: our own first attempt evaluated the slope at one unrepresentative reference cell, which made Asia look significant in the opposite direction. Computed correctly, that result disappeared — it was an artifact of our calculation, and we've documented the correction rather than hidden it.

**Backup:**

Asia: artifact value p = 0.0070 (preserved in our committed correction log — the corrected run no longer prints it); corrected within-region average p = 0.0535 / 0.0846 / 0.2860 across the three fits — not significant anywhere. The withdrawn contrast's reference cell was pandemic-era × large loans — a few percent of the data.

#### C5 · You've said you got it wrong twice. Why should we trust round three? `[HARD]`

**Answer:**

Because round three is the only one that was independently verified three different ways rather than trusted. The corrected quantity was validated arithmetically against a brute-force calculation; it was computed through two separately-built implementations that agree; and the whole trail — including both mistakes and what caught them — is in our repository's review log, not cleaned up. But the deeper answer is: you shouldn't trust any single round, ours included. The reason we found our own errors is that we kept subjecting the headline result to new tests. An analysis that never revises its answer is one that was never really tested.

**Trap:** don't get defensive. This question is the presentation's thesis handed to you — self-correction under testing is the method working, not failing.

#### C6 · You tested well over a hundred coefficients. Aren't your survivors just multiple-comparison luck? `[HARD]`

**Answer:**

Fair concern, and three things answer it. First, the regression formula itself was pre-specified — one formula, no stepwise searching, every coefficient reported whether significant or not. We'll be candid that the within-region *averaging* analysis came later, developed through review rounds, so we treat it as post-estimation and exploratory rather than pretending the whole inferential path was fixed in advance. Second, the clustering correction itself removed the mass false-positive problem: it's what took us from "almost everything significant" to a handful. Third — and this is where we ended up conceding the point ourselves — multiplicity isn't even the binding problem. The pooled family-framing result clears conventional clustered p-values in all three fits and five of six headline tests clear an 18-test Bonferroni threshold; but those p-values rely on a normal approximation that fails with two clusters, and under a few-cluster t(1) reference the result is not significant in any fit. So we don't claim it. The within-region averaging itself is post-estimation and exploratory. And where a result *was* marginal — a single-fit p = 0.009 for Haiti — we didn't claim it, which is the multiple-comparisons discipline applied rather than described.

**Backup:**

6 regions × 3 fits = 18 slope tests; Bonferroni threshold ≈ 0.0028. ME/CA clear it in 5 of 6 tests: notebook and authoritative-duration p \< 0.0001 for both regions, CA 24h p \< 0.0001; the exception is ME's 24h fit, p = 0.0040 vs the adjusted threshold 0.0028 — significant unadjusted, just over the line after correction. Worth conceding if pushed.

#### C7 · Your own committed results show family×Water and family×Construction surviving clustering. Why aren't sectors in your headline? `[HARD]`

**Answer:**

Because those are interaction coefficients, and the central lesson of our own analysis is that a significant interaction is not a within-group association — it only says the slope differs from the Agriculture baseline. For regions we did the extra work: averaged each region's slope over its own composition and re-tested. For sectors we haven't run that computation yet, so we report the interactions as surviving and claim nothing about what family framing does *within* Water or Construction loans — the same discipline that caught our own Asia error. It's the first item on the analysis backlog, and the honest answer today is "not yet tested properly."

**Backup:**

Authoritative interaction terms surviving clustering in both models: family×Water (p = 0.0000 / 0.0258), family×Construction (p = 0.0413 / 0.0007); family×Clean Energy in the duration model only (0.0079 / 0.0818). All are difference-from-Agriculture, not within-sector slopes.

**Trap:** don't improvise a within-sector claim under pressure — "we haven't computed that quantity, and here's why we won't guess it" is the strong answer.

#### C8 · What about North America? Your snapshot shows it significant.

**Answer:**

Significant in exactly one of our three fits — the authoritative duration model, p = 0.009 — and not in the other two. And "North America" in this dataset is a single country: Haiti. One cluster can't support any within-region inference at all, so we report it for completeness and claim nothing. If a marginal single-fit result on a one-country base counted as a finding, our four-country caution would be theater — consistency is the point.

**Backup:**

Haiti: 7,559 loans. Within-region slope +0.0127 (toward slower), clustered p = 0.0094 authoritative duration; p = 0.0621 notebook; p = 0.6570 authoritative 24h.

### Methods & data

#### D1 · Why OLS on log-days instead of a survival model?

**Answer:**

A survival model earns its complexity when observations are censored — loans still unfunded when the data ends. Our dataset contains completed loans — every row has both a posting and a fully-funded date, so there's essentially no censoring for a hazard model to handle. (The six rows we drop, of 1.45 million, have a funded date recorded *before* the posting date — a data inconsistency, not censoring.) Log-transformed duration with OLS handles the heavy skew, keeps every coefficient directly interpretable for a non-technical audience, and we pair it with a 24-hour logistic model so the "fast vs slow" framing is covered too. With unfunded or expired loans in the data, survival analysis would be our first move — we'd genuinely like that data.

#### D2 · You only observe funded loans. Isn't that survivorship bias? `[HARD]`

**Answer:**

It's a real scope limit and we state it: our outcome is *how fast a loan that funded got funded*, not whether loans fund. If some loans expire unfunded and framing affects *that*, we can't see it, and our associations are conditional on reaching full funding. What we can say is that within our question the data is essentially complete — only six loans out of 1.45 million were dropped, for timestamp inconsistencies (funded date before posting), not missingness — and the practical outputs, like the at-risk-loan flag, are about speed among posted loans, where this scope is the right one. Extending to expiry outcomes is the top of our future-work list.

#### D3 · Dictionary word-counting for framing seems crude. Why not embeddings or an LLM?

**Answer:**

Deliberate trade-off: transparency over sophistication. A dictionary measure is auditable — anyone can check exactly which words counted, reproduce every number, and challenge the word lists themselves. An LLM score is neither reproducible nor explainable at that standard, and for an analysis whose whole contribution is rigor, an unauditable feature would undercut the point. We didn't stop at keywords, though: topic modeling found the description themes without any word lists, and VADER sentiment scores tone — and notably, the topic structure agrees with the structural story, not the framing one. LLM-scored narrative dimensions are the natural next iteration once there's a validation protocol for them.

**Backup:**

TF-IDF + NMF, 8 topics, coherent themes (livestock, sanitation, clean water, farming, retail); topic funding-speed means span 1.5 → 13.5 days (\>9×), though topics track sector/loan-type as much as style.

#### D4 · How do you know your predictive results aren't leakage?

**Answer:**

Three defenses, all structural. The split is chronological, not random — train on 2016–2023, test on 2024–2025, so the model literally cannot have seen the future. Every fitted transformation — imputation, encoding, the text vectorizer — is fit on training data only and applied to the holdout. And the feature set is restricted to information available at posting time; anything downstream of the outcome is excluded by an allowlist, not by judgment call. The holdout R² of 0.54 is credible partly *because* it's unglamorous — leakage usually announces itself with numbers too good to believe.

#### D5 · R² of 0.49–0.54 — is that good? What's in the missing half?

**Answer:**

For predicting human funding behavior from posting-time information alone, explaining half the variation is strong — and the missing half is informative about what we don't observe: lender-side dynamics. Where a loan appears in browse results, when it's posted relative to lender activity, photos, promotion, herding among lenders — none of that is in our data. The half we do explain is dominated by structure, which is the finding: the observable, coachable part of a loan's presentation contributes little on top.

### Other findings

#### E1 · Positive descriptions fund slower? Should borrowers write sadder stories? `[HARD]`

**Answer:**

No — and this result is a good example of why we report uncertainty honestly. The direction is consistent everywhere we tested: more positive tone, slower funding. But its statistical significance depends on which of our two model specifications you ask — it survives clustering in one and not the other, so we report it as open, not established. Even taking the direction at face value, we deliberately don't offer a mechanism, because the obvious one fails our own test: description *length* is separately controlled in the model and, if anything, points toward faster funding — so "positive pitches are just longer" doesn't explain it. What we can say: descriptions are almost uniformly upbeat already — median 0.89 on a −1 to +1 scale — so tone has little room to vary, whatever it proxies for is unresolved, and nothing here says "write negatively."

**Backup:**

Median compound 0.89, mean 0.78 (20k-sample). Clustered p ≈ 0.01/0.02 (authoritative duration/24h) vs ≈ 0.25 (notebook). Word-count coefficients: −0.0004 duration / +0.0011 24h-odds — both toward faster, both fail clustering. Ceiling effect limits coachability regardless.

#### E2 · The gender gap — what's driving it, and what should Kiva do?

**Answer:**

It's one of the most robust patterns in the data: female-posted loans fund in a median 2.3 days against 7.7 for male-posted. Controls matter here in both directions: adjusting for loan size, sector, region, timing and writing style simultaneously absorbs roughly half of that raw gap — so composition explains a lot — but a large adjusted gap remains, about 54% longer for male-posted loans, and it survives clustering. What drives the remainder our data can't decompose: candidates include lender behavior, field-partner posting practices, and loan differences we don't observe. What to do with it is genuinely a values question for the platform more than an analytics one — but knowing the gap is real, large, and not purely a composition artifact is the necessary first step, and setting realistic funding-time expectations by borrower profile is an immediate, neutral use.

**Backup:**

Raw median ratio ≈ 3.3×; adjusted coefficient +0.43 on log(1+days) ≈ ×1.54 — controls absorb roughly half the raw log-gap. Survives clustering (p \< 0.0001). Smaller than the biggest sector/region gaps, larger than every narrative term combined.

#### E3 · What's the difference between your two pipelines, and which one is right?

**Answer:**

One is the authoritative tested pipeline — versioned, unit-tested, source of the committed results. The other is a deliberately simpler, self-contained rebuild for Kaggle, so anyone can run the analysis without our internal code. They're not meant to produce identical numbers — different formula richness — and that turned out to be useful: where the two agree, as on the pooled-category result, the finding is at least robust to the modeling choices that differ between them — same data, so not independent replication; where they disagree, as on sentiment, that disagreement *is* the result — it tells us the finding is specification-sensitive and shouldn't be presented as settled.

#### E4 · What would you do next with more time or data?

**Answer:**

Four things, in order. Run the country-stratified A/B test in the two surviving pooled categories — it's the only way to locate which countries, if any, actually drive the pooled association and turn it into something actionable. Get expired and unfunded loans into the data, so we can model funding success, not just speed. Get a field-partner identifier, which would let us cluster at the true dependence level and probably explain part of what "country" currently absorbs. And add LLM-scored narrative dimensions alongside our transparent dictionaries — with a validation protocol, so they'd meet the same auditability bar as everything else here.

## Part III · Numbers crib sheet

One table to re-read before the session. Sign conventions: duration models predict log(1+days), **negative = faster**; the 24-hour model predicts log-odds, **positive = faster**.

| Number | Value | Source |
|----|----|----|
| Dataset / usable | 1,453,846 / 1,453,840 (99.9996%) | both pipelines |
| Train / holdout split | 1,174,953 (2016–23) / 278,887 (2024–25) | authoritative |
| Boosted model holdout | MAE 5.20 d · R² 0.54 (notebook: 5.56 / 0.49) | authoritative |
| 24h classifier | ROC AUC 0.90 · AP 0.83 | authoritative |
| Funded within 24h by era | 46.0% → 30.3% → 30.0% | notebook (EDA) |
| Gender medians | female 2.3 d · male 7.7 d; coef +0.43 ≈ 54% longer | notebook |
| Explanatory OLS R² | 0.426 on 1,453,840 loans | notebook |
| Cluster-check flips | 20/45 (44%) notebook · 64/128 (50%) authoritative, 62.5% of those narrative terms | both |
| Urgency collapse | HC3 p\<0.001 → clustered p≈0.44 notebook dur · 0.49 / 0.22 authoritative dur / 24h | both |
| Family within Middle East | −0.124 / −0.073 / +0.175 · conventional clustered p ≤ 0.004 · few-cluster t(1) p = 0.12 (dur) / 0.21 (24h) | 3 fits |
| Family within Central America | −0.062 / −0.074 / +0.103 · conventional clustered p \< 0.0001 · few-cluster t(1) p = 0.06 (dur) / 0.14 (24h) | 3 fits |
| Family within Asia (corrected) | p = 0.0535 / 0.0846 / 0.2860 — not significant | 3 fits |
| Family within North America (Haiti) | sig in 1 of 3 fits only (p = 0.0094 auth. duration) — 1 country, not claimed | 3 fits |
| Country counts per group | Africa 27 · Asia 12 · Oceania 4 · CA 2 · ME 2 · NA 1 (48 total) | raw data |
| Pooled ME + CA loan share | 74,337 loans ≈ 5.1% (ME 14,946 + CA 59,391) | raw data |
| Biggest structural coefs (dur) | Water −1.12 · ME region −1.07 · male +0.43 · log-amount +0.43 · term +0.068/mo | notebook |
| Sentiment | median 0.89 · clustered p 0.01/0.02 authoritative vs 0.25 notebook — open | both |
| Topic-modeling swing | 1.5 → 13.5 days across 8 topics (\>9×) | notebook (EDA) |
| Repayment term spread | 2–133 months, middle 50% between 8–14 | raw data |

**The one-sentence close, if a question goes sideways:** "The honest summary is that we tested our own best findings four times and killed every narrative one, including the last one standing; what's left — structure dominates, and no writing rule is supported — is what we'd stake the recommendation on."

Compiled 2026-08-29 from verified runs: Kaggle kernels v10 (EDA) and v13 (modeling), the committed `reports/generated_full_dataset/` snapshot, and the authoritative pipeline's within-region average recomputation. Companion to the deck-content brief "Beyond a Good Story".
