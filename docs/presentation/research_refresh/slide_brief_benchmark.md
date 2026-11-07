# Slide-by-slide briefing: matched benchmark update

Post-competition update, 2026-11-02. Twelve core slides plus four appendix slides. The previous research-design deck remains preserved.

## 1. What narrative text adds to funding-speed forecasts

**Message:** Measure what narratives add, then test whether a truthful change helps.

**Reader decision:** Understand the project as a decision case with an explicit next test.

**Evidence status:** Reviewed post-competition predictive extension. 1,453,846 input records; 1,453,840 valid completed durations; 65 model/arm windows.

**Exhibit:** Minimal editorial cover, team names and recognition; no model-performance claim.

**Speaker briefing:** We are Mike Nguyen and Sophia Nguyen from Cultural Blend. This case began with a marketing question: which loan narratives are associated with faster funding? The maintained research now asks a more useful next question: what information does text add, and what evidence would justify changing how a loan is presented? We distinguish what the competition work established from later research. The new matched study is separate from the original competition results. The retrospective evaluation does not become an untouched test because we changed the protocol.

**Sources:** [www.unsw.edu.au](https://www.unsw.edu.au/business/our-schools/marketing/news-events/student-events/MA-hackathon); `docs/2_evidence_and_corrections.md`; `reports/text_benchmark_reviewed/benchmark.json`.

## 2. Use the matched evidence to choose the next test

**Message:** The next decision concerns measurement and intervention, informed by a completed comparison.

**Reader decision:** Approve the research sequence before commissioning additional model complexity.

**Evidence status:** Recommendation after the matched benchmark. Availability audit and fixed-config comparisons completed; no measured editing benefit.

**Exhibit:** Three large numbered statements on a flat canvas; no invented impact scores.

**Speaker briefing:** The first two research steps are now completed. This does not remove completed-record selection, snapshot-field uncertainty or construct validity questions. Decide what the remaining information gaps justify before choosing a writing or allocation policy.

**Sources:** `reports/text_benchmark_reviewed/benchmark.json`; `reports/text_benchmark_reviewed/availability_audit.json`; `docs/6_matched_text_results.md`.

## 3. The outcome is completed funding on the platform

**Message:** The observed sample and timing determine what the project can claim.

**Reader decision:** Interpret later results within completed records and distinguish borrower disbursal.

**Evidence status:** Primary population and descriptive audit. 1,453,846 input rows; six negative durations excluded; 1,453,840 eligible, including 1,637 refunded records. Dictionary reports 96.4% pre-disbursal.

**Exhibit:** Large eligible count at left, listing-to-completion timeline in text at right, precise population footnote.

**Speaker briefing:** The full input contains 1,453,846 records from 2016 to 2025. Six negative durations are excluded. The analysis includes 1,637 refunded records with valid completed durations. The dictionary's full-data descriptive audit reports 96.4% pre-disbursal, so listing-to-completion time often begins after money has already been disbursed. It does not directly measure borrower waiting, partner liquidity or welfare. Unfunded and expired listings are needed to study all-listing success. The new as-of training audit removes pre-cutoff postings whose completed membership was not yet known; the primary August snapshot is preserved.

**Sources:** `reports/generated_full_dataset/analysis_summary.json`; `docs/1_data_dictionary.md`; `docs/2_evidence_and_corrections.md`; [www.kiva.org](https://www.kiva.org/blog/qa-expiring-loans-credit-limits-and-the-evolution-of-kiva); `reports/text_benchmark_reviewed/availability_audit.json`.

## 4. Investigate four connected parts of the funding process

**Message:** Choose a mechanism to investigate before choosing a lever to change.

**Reader decision:** Prioritise the missing data required by the intended intervention.

**Evidence status:** Working issue tree. Repository schema and Kiva process documentation; missing fields are data requests, not established causes.

**Exhibit:** Native editable issue-tree matrix with observed versus missing evidence.

**Speaker briefing:** This issue tree is a working decomposition. Its branches interact: a partner's process may affect both wording and exposure. Literature gives reasons to consider prosocial framing and lender preferences, while Kiva describes editing and translation in the posting process. None of these mechanisms is identified by a predictive importance chart. We should request data that can distinguish them.

**Sources:** `docs/1_data_dictionary.md`; [www.kiva.org](https://www.kiva.org/blog/how-kiva-works-faqs); [www.thallison.com](https://www.thallison.com/wp-content/uploads/2022/03/etap.12108.pdf); [www.mckinsey.com](https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/how-to-master-the-seven-step-problem-solving-process).

## 5. Text improves linear forecasts in all five years

**Message:** Matched gains quantify additional predictive information; they are not the effects of editing.

**Reader decision:** Assess the size and temporal stability of added predictive information.

**Evidence status:** New full-data retrospective benchmark. Sparse Ridge/logistic family, fixed configurations, as-of training cohorts. Annual rows and exact metrics are in the reviewed bundle.

**Exhibit:** Native grouped MAE chart for all five years, with matched structure/text inputs.

**Speaker briefing:** Compare structure-only and structure-plus-text within the same sparse linear family, using the same rows, outcomes and cutoffs. TF-IDF is fitted on each training window only. The side callout is the median of annual MAE gains, not a loan-weighted pooled estimate. The AUC change is text-added minus structure-only in the latest observed year: a negative value means ranking declined even though duration MAE improved. These fixed models are not tuned winners. Description contents may encode context as well as framing.

**Sources:** `reports/text_benchmark_reviewed/benchmark.json`; `docs/6_matched_text_results.md`.

## 6. Read the added-text gain with its uncertainty

**Message:** Country-resampling intervals include zero in 4 of 5 linear comparisons; read both sensitivity checks.

**Reader decision:** Choose a practical threshold with decision owners; do not infer an intervention return.

**Evidence status:** New matched comparisons; pointwise fixed-model sensitivity intervals. Linear adds M+L+R; trees add M+L only. Positive gain means lower MAE in days. Month-cluster bootstrap uses 1,000 draws.

**Exhibit:** Native table of paired gains and month-block sensitivity intervals, with units.

**Speaker briefing:** Each gain subtracts candidate absolute error from the structure-only error on the same records. Whole calendar-month blocks are resampled, preserving paired losses and weighting by record count. These are fixed-model sensitivity intervals, not causal intervals or retraining uncertainty. Annual windows have few independent month blocks. The notebook also shows country sensitivities, paired Brier gains and S+P versus S+P+text comparisons. P remains an unvalidated programme-text proxy.

**Sources:** `reports/text_benchmark_reviewed/benchmark.json`; `docs/5_ml_refinement_plan.md`.

## 7. Large row counts do not remove contextual uncertainty

**Message:** Regional narrative patterns require careful treatment of the number of independent countries.

**Reader decision:** Treat regional patterns as exploratory hypotheses, not country-specific writing advice.

**Evidence status:** Primary August estimates. Middle East slope −.0729, normal interval [−.1003,−.0456], heuristic [−.2502,.1043], 2 countries; Central America −.0742, normal [−.0879,−.0605], heuristic [−.1629,.0145], 2 countries. Slope units: change in log(1+days) per additional family mention per 100 words.

**Exhibit:** Two-region native table with point estimates, normal intervals and heuristic intervals. Clearly label the latter as uncalibrated sensitivity.

**Speaker briefing:** The two regional point estimates suggest faster completed funding with more family mentions, conditional on the primary model. Each pooled region contains only two countries. The normal-reference country-clustered intervals and the much wider t(1) screen show why the uncertainty deserves attention. The screen is heuristic and is not a calibrated correction. In the same primary analysis, urgency has country-clustered p=.4943 for duration and .2233 for 24-hour completion. Failure to reject does not establish a negligible effect.

**Sources:** `docs/2_evidence_and_corrections.md`; `reports/generated_full_dataset/analysis_summary.json`; [cameron.econ.ucdavis.edu](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015.pdf).

## 8. Later checks retain some narrative associations

**Message:** Statistical support changes with specification; a universal editing benefit remains unestablished.

**Reader decision:** Retire the blanket null story while retaining the intervention boundary.

**Evidence status:** Reviewed October research extension. Same 1,453,840 eligible rows and 48 countries across four fits. Joint framing families remain associated. Primary predictive models were not rerun.

**Exhibit:** Compact specification comparison plus one clearly unit-labelled 24-hour result. Keep the two outcomes separate.

**Speaker briefing:** The October extension is later research, separate from the competition submission. The third-person duration estimate changes modestly, while its adjusted p-value crosses .05. This is not proof that the association disappeared. Business framing is associated with a lower 24-hour completion probability under the programme specification. Several joint families remain associated. The programme variable is a text-derived proxy, not a verified partner ID. Coefficients are per extra mention per 100 words, and the duration outcome is log(1+days). Multiplicity is handled within each outcome/specification, not across the entire research history. Duration pointwise 95% intervals are [−0.013833, −0.004183] for expanded controls and [−0.013210, −0.002965] for programme adjustment. Business framing has a pointwise interval [−0.390, −0.126] percentage points. Intervals are pointwise; the displayed p-values are BH-adjusted within each outcome/specification.

**Sources:** `reports/expanded_feature_sensitivity_reviewed/README.md`; `reports/programme_proxy_audit/README.md`.

## 9. Choose actions by evidence and readiness

**Message:** Prioritise learning value without inventing intervention returns.

**Reader decision:** Prioritise construct validation and the feasibility of a defined pilot.

**Evidence status:** Proposed prioritisation. Synthesises current evidence boundaries. No cost or benefit estimates were collected.

**Exhibit:** Native options matrix using verbal judgments, no artificial impact scores.

**Speaker briefing:** The audit and matched comparison are completed. They support a decision about further measurement and feasibility work, not a claim that changing text will improve funding. All-listing validation and an agreed operational purpose are still required for allocation tools. A model identifying slow loans does not identify who benefits from attention.

**Sources:** `docs/4_research_review.md`; `docs/5_ml_refinement_plan.md`.

## 10. Ranking and probability quality need separate checks

**Message:** A ranking score cannot establish reliable probabilities for all new listings.

**Reader decision:** Inspect reliability, coverage and the population before considering an operational queue.

**Evidence status:** 2025 observed completed records; sparse linear S+M+L+R. Equal-width probability bins; empty bins omitted. Brier/log loss, counts, tail errors and group diagnostics are in the notebook.

**Exhibit:** Native line chart comparing predicted and observed probability within fixed bins.

**Speaker briefing:** This diagnostic uses the latest observed year and the prespecified text-added sparse linear model. Predictions are compared with observed completion within 24 hours in the same probability bins, with counts shown below. Empty bins are omitted. The notebook compares both model families and shows duration-tail and novelty diagnostics. No calibration model has been fitted and no all-listing deployment evaluation has been performed.

**Sources:** `reports/text_benchmark_reviewed/benchmark.json`; [scikit-learn.org](https://scikit-learn.org/stable/modules/calibration.html).

## 11. Test one truthful presentation change

**Message:** A prospective experiment should estimate a defined intervention on all eligible listings.

**Reader decision:** Agree the intervention and observation contract with participating partners.

**Evidence status:** Proposed pilot, no measured benefit. Candidate factual clarity/specificity prompt, usual-content control. Assignment, horizon, practical threshold and power are not yet fixed.

**Exhibit:** Four numbered steps with endpoint and guardrails in a separate short statement.

**Speaker briefing:** One candidate is a prompt that makes the existing purpose and use of funds clearer while preserving facts. Compare the offer of that prompt with usual practice and include all eligible listings in analysis. Decide the assignment unit to limit staff/template contamination and marketplace spillovers. Choose one primary completion horizon, a practical effect threshold and sufficient independent units before launch. Do not compare duration only among loans that fund after treatment. Measure accuracy, editing burden, representation and displacement as guardrails. No sample size or duration is justified yet.

**Sources:** `docs/4_research_review.md`; [digitaleconomy.stanford.edu](https://digitaleconomy.stanford.edu/publication/interference-bias-and-variance-in-two-sided-marketplace-experimentation-guidance-for-platforms/).

## 12. Validate the proposed lever before running a pilot

**Message:** The retrospective comparison is complete; intervention benefit remains the next evidence gap.

**Reader decision:** Validate narrative constructs and agree a feasible intervention design.

**Evidence status:** Recommended delivery sequence. Research plan with dependency-based gates; no committed delivery dates.

**Exhibit:** Four horizontal work stages, owners and concrete exit tests.

**Speaker briefing:** The as-of audit and matched full-data comparison are completed. Next validate the constructs, request historical field/exposure information and assess whether a factual presentation pilot is feasible. Agree its endpoint, assignment, practical threshold and guardrails before launch. The existing observational results do not establish the outcome of that experiment.

**Sources:** `docs/5_ml_refinement_plan.md`; `docs/4_research_review.md`.

## 13. Appendix: evidence register

**Message:** Every claim belongs to a specific result set and population.

**Reader decision:** Use the right run when reusing any number.

**Evidence status:** Evidence provenance. Existing report manifests and correction notice.

**Exhibit:** Native evidence ledger.

**Speaker briefing:** The local historical PPTX has 15 slides. Other notes refer to separate 14-page and 13-page exports. We cannot assume they are identical. This revised deck preserves those historical files and uses an explicit evidence ledger. The 100-row proposal example is not comparable to the full-data run. New paired notebooks remain output-free/source-validated unless actual execution is recorded. This update adds the reviewed November predictive extension and preserves the earlier research-design deck as a separate artifact.

**Sources:** `docs/2_evidence_and_corrections.md`; `docs/presentation/README.md`; `reports/text_benchmark_reviewed/benchmark.json`.

## 14. Appendix: primary predictive benchmark

**Message:** Keep metrics, target units and population together.

**Reader decision:** Read complementary metrics and audit the prediction task before deployment.

**Evidence status:** Primary August snapshot. Exact JSON report values; no rerun.

**Exhibit:** Native benchmark table with negative R² retained.

**Speaker briefing:** Primary numeric values are read from the saved report. Ridge trains on log duration and is scored in days after exponentiation. This target/loss choice warrants inspection of tail predictions; a negative R² can coexist with a lower MAE than the baseline. The classifier's negative class is completed funding after 24 hours, not expired or never-funded listings. The historical holdout has already been examined and informed later research, so it is not a fresh untouched evaluation.

**Sources:** `reports/generated_full_dataset/analysis_summary.json`; [scikit-learn.org](https://scikit-learn.org/stable/modules/calibration.html).

## 15. Appendix: replace claims that exceed the evidence

**Message:** Accurate language is part of analytical quality.

**Reader decision:** Apply these replacements consistently in notebook prose and future slides.

**Evidence status:** Corrections for current use. Notebook/deck audit and current evidence map.

**Exhibit:** Two-column replacement table; historical materials remain preserved.

**Speaker briefing:** Several old sentences are stronger than the data allow. The correction should be systematic rather than leaving a careful caveat at the end while overclaiming earlier. Also retire cross-unit coefficient rankings, the unsupported selectivity explanation for period trends, the 20,000-loan topic sample presented as full-data evidence, and claims that a heuristic few-cluster screen is calibrated inference. The missing comparison has now been run; its estimates remain predictive information gains.

**Sources:** `docs/4_research_review.md`; `docs/2_evidence_and_corrections.md`; [shap.readthedocs.io](https://shap.readthedocs.io/en/latest/example_notebooks/overviews/Be%20careful%20when%20interpreting%20predictive%20models%20in%20search%20of%20causal%20insights.html).

## 16. Appendix: prioritised research experiments

**Message:** Complexity follows a demonstrated research need.

**Reader decision:** Run the inexpensive information and validity checks first.

**Evidence status:** Proposed experiments. Next experiments after the matched study; no new annotations, survival data or pilot results exist.

**Exhibit:** Ranked work table with concrete gates.

**Speaker briefing:** Further model complexity should answer a documented need. The full matched study does not validate the psychological meaning of text features, produce a calibrated deployment tool or identify a writing intervention. Human measurement and missing process data are the next priorities.

**Sources:** `docs/5_ml_refinement_plan.md`; [scikit-survival.readthedocs.io](https://scikit-survival.readthedocs.io/en/stable/user_guide/evaluating-survival-models.html); [collaborate.princeton.edu](https://collaborate.princeton.edu/en/publications/how-to-make-causal-inferences-using-texts/).

