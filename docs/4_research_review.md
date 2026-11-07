# Research review and strategic direction

Date: 2026-11-02. Audience assumption: portfolio and industry readers, with a
Kiva/platform-partner decision as the case. This is a post-competition review.
Cultural Blend, Mike Nguyen and Sophia Nguyen, was one of eight finalist teams.

This is the pre-implementation diagnosis of the source at revision `7afea5f`.
Notebook line references describe that historical version. The approved audit,
matched benchmark and maintained notebook changes are reported separately in
the [November findings](6_matched_text_results.md); the remaining measurement
and intervention proposals below retain their prospective status.

## 1. The recommendation

Refine the project around **whether narrative information adds reliable,
decision-relevant evidence beyond the loan and marketplace context**. The
stronger contribution is a transparent research process that connects a business
question, defensible measurement, comparative models, uncertainty and a proposed
experiment. A longer list of models would not resolve the present weaknesses.

Three directions are plausible:

| Direction | Benefit | Limitation | Recommendation |
| --- | --- | --- | --- |
| Repair and polish the existing story | Fastest route to an accurate portfolio | Leaves the incremental value of text unresolved | Necessary first step |
| Rebuild the analytical comparison and decision story | Directly answers the project's core question | Requires a new full-data predictive study | Recommended next research phase |
| Develop a live prioritisation tool | Could support operational decisions | Needs all listings, exposure data, verified identifiers and prospective evaluation | Conditional later phase |

The recommended narrative is: **funding speed is predictable within the observed
completed-loan population; narrative associations depend on context and
specification; a fair incremental-value study and a prospective test are needed
before turning them into a writing or allocation policy.**

This review inspected source and saved results and consulted primary literature
and official method documentation. It did not rerun the ML models, execute the
notebooks, collect new borrower data or estimate intervention benefits.

## 2. What is already worth keeping

- The authoritative pipeline uses an explicit posting-time predictor allowlist
  and fits preprocessing and learned text transformations on training data.
- A chronological evaluation is materially better suited to future loans than
  a shuffled random split.
- The project separates predictive models from explanatory models and already
  records country-clustered sensitivity, exclusions and provenance.
- The reviewed October extension corrected an absorbed-predictor defect and
  retained rejected outputs with an audit trail. This is useful research practice.
- Transparent text features are a good baseline. They make it possible to inspect
  what the algorithm counted before introducing semantic complexity.

Sources: [pipeline](../src/modeling.py), [current evidence map](2_evidence_and_corrections.md),
[reviewed extension](../reports/expanded_feature_sensitivity_reviewed/README.md).

## 3. The consequential weaknesses

| Priority | Finding from the repository | Why it matters | Required response |
| --- | --- | --- | --- |
| P0 | Notebook 2 §9.2 says AUC 0.91 uses no narrative-framing features, but lines 270–274 include family, agency, urgency and sentiment, and lines 370–373 fit that matrix | The reported ablation does not exist | Remove the claim and run explicit feature-block comparisons |
| P0 | Notebook 2 §6 describes a reliable at-risk tool, while §9.2 correctly limits it to completed loans | The deployed population would include outcomes missing from evaluation | Use retrospective language and define a future all-listing target |
| P0 | The old deck says “robust null”, “won't move the needle” and “the story barely registers” | Non-significance and low attribution do not demonstrate no useful effect | Replace with a bounded conclusion about unestablished intervention benefits |
| P1 | A single 2024–2025 aggregate holdout is repeatedly discussed | A good pooled score can hide temporal drift and has already influenced interpretation | Add rolling calendar backtests and call later 2024–2025 comparisons retrospective |
| P1 | The shared split selects training rows by posting date without an explicit outcome-availability cutoff | A pre-cutoff loan funded after the cutoff would have an unavailable duration label at training time | Audit boundary-crossing outcomes before a fresh predictive run; magnitude is currently unknown |
| P1 | Notebook 2 and `src/` differ in feature definitions, controls and formula | Conflicting results may reflect different constructs as well as different specifications | Publish a specification crosswalk and use shared functions for the maintained walkthrough |
| P1 | SHAP and simple importance ranks are used to motivate structural dominance | Rankings cannot quantify the benefit of removing a correlated feature family or editing text | Prioritise paired ablation, then use explanations diagnostically |
| P1 | Programme categories are derived from `whySpecial` | They may capture templates and context but do not identify partners or authors | Keep the proxy label and seek validated identifiers |
| P1 | Narrative constructs have little documented human validation | A precise coefficient for a weak measure can still answer the wrong question | Validate clarity, family orientation, need and agency with reviewed annotations |
| P2 | The topic exhibit mixes a 20,000-record exploratory fit with the full-data story | Readers can confuse exploratory themes with full-population predictive evidence | Move to the appendix, label the sample, and assess topic stability |

Exact pointers are expanded in the [ML plan](5_ml_refinement_plan.md) and
[slide briefing](presentation/research_refresh/slide_brief.md). These are
diagnoses of the current record, not a claim that every saved number is wrong.

## 4. Define the decision before the model

**Proposed client question:** Where should Kiva and participating lending partners
invest their next unit of research and content-support effort to understand
funding delays while preserving access for underserved borrowers?

The current data support comparisons among records with valid completed funding
durations. They do not identify the probability that an arbitrary new listing
will fund. Slow funding is also not a repayment-default outcome.

The dictionary's full-data descriptive audit reports 96.4% pre-disbursal. This
means the interval from listing to completed funding often follows an earlier
disbursal. It is an observable platform interval. Partner cash recycling is a
plausible business mechanism, but partner liquidity, wire-transfer timing and
borrower welfare are not measured by that interval alone. Kiva's historical
[process explanation](https://www.kiva.org/blog/qa-expiring-loans-credit-limits-and-the-evolution-of-kiva)
supports this distinction; its 2012 operational rules must not be assumed current.

Use three explicit research questions:

1. **Description:** how do observed funding durations vary with time, loan
   characteristics and narrative measures?
2. **Prediction:** how much does text improve forecasting on later eligible
   loans, beyond information already in structured fields?
3. **Intervention:** would a specific factual change in presentation improve
   funding outcomes, and for whom? This requires a separate design.

## 5. What prior research contributes

The literature gives reasons to investigate narratives, not a warrant to copy
an old coefficient into the current recommendation.

| Evidence reviewed | Relevant idea | Implication for Cultural Blend | Boundary |
| --- | --- | --- | --- |
| [Allison, McKenny & Short, 2013](https://www.thallison.com/wp-content/uploads/2022/03/CrowdfundingJBV.pdf), 6,051 Kiva narratives | Different rhetorical constructs were associated with funding time | Define and validate constructs, rather than treating all emotional words as one score | Earlier observational setting; language and context differ |
| [Allison et al., 2015](https://www.thallison.com/wp-content/uploads/2022/03/etap.12108.pdf), over 36,000 loans | Prosocial and business-opportunity framing were associated differently with funding outcomes | Compare theoretically motivated framing measures and context interactions | Does not establish that the current business-mention coefficient is the same construct |
| [Galak, Small & Stephen, 2011](https://faculty.wharton.upenn.edu/wp-content/uploads/2012/02/Galak,-Small,---Stephen-2011.pdf) | Borrower identity and social proximity matter to lender decisions | Treat narrative, borrower context and lender demand as related mechanisms | Does not justify exploiting protected characteristics to rank access |
| [Ly & Mason, 2012](https://www.sciencedirect.com/science/article/abs/pii/S0305750X11002312), abstract reviewed | Competition among projects relates to funding speed | Request contemporaneous marketplace supply and exposure measures | Full article was not accessible in this review; no detailed identification claim is made |
| [Egami et al., 2022](https://collaborate.princeton.edu/en/publications/how-to-make-causal-inferences-using-texts/) | Discovering a text representation can introduce identification and overfitting problems | Separate construct development from later evaluation and predefine the intervention | Better representation or sample splitting alone does not remove confounding |
| [SHAP's causal interpretation guidance](https://shap.readthedocs.io/en/latest/example_notebooks/overviews/Be%20careful%20when%20interpreting%20predictive%20models%20in%20search%20of%20causal%20insights.html) | Attribution explains predictive associations | Use SHAP for model diagnosis and example explanations | It cannot show the effect of rewriting a loan description |

Kiva also describes partners uploading loan details and volunteers editing and
translating them in its [process FAQ](https://www.kiva.org/blog/how-kiva-works-faqs).
Accordingly, call the object a **loan narrative**, not automatically the borrower's
own writing. Template, translation and editorial provenance belong in the data
request. Do not infer authorship from first- or third-person counts.

A newer [image–text study](https://www.sciencedirect.com/science/article/abs/pii/S0167923625001976)
was found at abstract level only. It motivates a possible later multimodal
research question, but supplies no validated result for this project. Image
modelling should wait behind the much cheaper text-value and measurement audits.

## 6. A consulting framework that fits the evidence

Use a **decision question, issue tree, evidence matrix and stage-gated pilot**.
This adapts the problem definition, decomposition and synthesis principles in
[McKinsey's structured problem-solving discussion](https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/how-to-master-the-seven-step-problem-solving-process).
The choices below are our project proposal, not a McKinsey endorsement.

### Situation, complication, question, answer

- **Situation:** loan pages combine a financing request, a narrative and a
  marketplace position. Funding speed varies substantially across records.
- **Complication:** the available data cover completed funding, and narrative
  content is entangled with purpose, geography, programmes and editing processes.
- **Question:** which additional evidence would support an effective and fair
  content or operational intervention?
- **Proposed answer:** audit the outcome and measurement, quantify text's added
  information, then test one factual presentation change with participating
  partners before considering scale.

### Working issue tree

| Branch | Mechanisms to investigate | Available evidence | Missing evidence |
| --- | --- | --- | --- |
| Financing request | Amount, term, purpose, borrower/group composition | Many structured fields | Changes over the life of a listing, operational constraints |
| Narrative and presentation | Clarity, specificity, need, agency, translation | Description and auxiliary text | Reviewed constructs, authorship, listing-time versions |
| Marketplace exposure and demand | Visibility, competing loans, campaigns, lender availability | Calendar and geographic proxies | Impressions, ranking position, lender sessions, competing inventory |
| Partner and programme process | Templates, posting schedules, disbursal and settlement | Pre-disbursal fields and programme-text proxy | Validated partner ID, process history and cash-flow measures |

This is a working decomposition, not a claim of independent causal mechanisms.
For example, programme operations can affect both narrative and exposure.

### Options and recommended order

| Option | Evidence now | Cost/dependency | Decision |
| --- | --- | --- | --- |
| Narrative quality audit and fair text-value benchmark | Strong need identified by source review | Existing data plus annotation effort | Start here |
| Segment diagnostic for partner discussions | Descriptive evidence exists | Comparable populations, uncertainty, partner participation | Develop as a diagnostic |
| Factual clarity/specificity editing pilot | Plausible mechanism, no measured benefit here | Validated constructs and operational experiment | Design after audit |
| Automated visibility or at-risk allocation | Current model population is insufficient | All listings, exposure logs, calibrated policies and safeguards | Defer deployment |
| Universal family/urgency tips | No established editing benefit | Could induce stereotyped or inaccurate content | Do not adopt from this study |

Avoid a decorative SWOT or Porter analysis. They do not resolve this project's
specific measurement, incremental-value and intervention questions. Use
qualitative priorities until effort and benefit estimates are supplied; an
invented ROI or numerical impact score would add false precision.

## 7. What a useful pilot would test

Candidate: a partner-reviewed prompt that makes a loan's existing purpose and
use of funds clearer while preserving all factual content. This is a proposal,
not a result. Test the prompt's actual adoption and fidelity as well as outcomes.

Define eligibility, assignment unit, treatment, standard-content control,
observation window, estimand, practical effect threshold and analysis before
launch. Include every eligible listing, not just eventual funders. A sensible
primary endpoint is completion by a stakeholder-selected deadline. Use a
time-to-event endpoint with valid censoring as a secondary view; do not compare
duration only among treatment and control loans that eventually fund.

Select the randomisation unit with the platform. Loan-level assignment may
contaminate templates across staff or redistribute fixed lender attention.
Marketplace experiments can have spillovers, as discussed by
[marketplace-interference research](https://digitaleconomy.stanford.edu/publication/interference-bias-and-variance-in-two-sided-marketplace-experimentation-guidance-for-platforms/).
Use cluster or time-based designs only after
examining interference and carry-over, not as an automatic correction.

Guardrails should include factual accuracy, editing workload, coverage of
underserved groups and displacement of funding from other loans. A faster
treated loan alone does not demonstrate additional total funding or welfare.
Power depends on the baseline rate, practical improvement, independent assignment
units and intracluster correlation. None is estimated sufficiently here to promise
a sample size or duration.

## 8. Decisions and delivery sequence

1. **Correct communication:** retire unsupported claims, reconcile the notebook
   and pipeline, and use the new deck's evidence boundaries.
2. **Audit and benchmark:** implement the reproducible comparison in the
   [ML refinement plan](5_ml_refinement_plan.md), then run it on the full input.
3. **Interpret:** choose what to retain based on stable incremental performance,
   measurement quality, costs and stakeholder use; an honest small or uncertain
   gain is still useful evidence.
4. **Refresh the deck:** replace the proposed-experiment exhibit with verified
   paired estimates and uncertainty. Keep all unsuccessful comparisons visible
   in the research record.
5. **Request external data and partnership:** proceed to an all-listing model
   or pilot only when the missing data and operational decision are specified.

The immediate output is a revised evidence-based story and an executable
research specification. It is not a newly validated model or proven solution.
