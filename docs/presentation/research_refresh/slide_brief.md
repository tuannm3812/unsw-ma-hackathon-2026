# Slide-by-slide briefing

Date: 2026-11-02. Proposed audience: portfolio and industry readers. Twelve core slides plus four technical appendix slides. This is a post-competition research refresh, with later findings labelled. Suggested narration is 10–12 minutes, subject to rehearsal; the deck is also intended to be read independently. Mike Nguyen and Sophia Nguyen are the presenters, with no unverified individual contribution split.

The narrative follows a situation–complication–question–answer opening, a working issue tree, an evidence review, an options matrix and decision gates. These are aids to reasoning, not proof of an intervention's impact. The full discussion is in [the research review](../../4_research_review.md) and [ML plan](../../5_ml_refinement_plan.md).

The old local draft has 15 pages. Notes about 14-page and 13-page exports refer to other versions. Do not reuse their numbering or presume the local PPTX is the submitted version. The historical no-background instruction applied to the competition event; this reader deck needs context.

## 1. Narratives, context and funding speed

**Message:** Measure what narratives add, then test whether a truthful change helps.

**Reader decision:** Understand the project as a decision case with an explicit next test.

**Evidence status:** Post-competition research refresh. Verified saved primary results and reviewed October sensitivity. Cultural Blend was one of eight finalists.

**Exhibit and layout:** Minimal editorial cover, team names and recognition; no model-performance claim.

**Speaker briefing:** We are Mike Nguyen and Sophia Nguyen from Cultural Blend. This case began with a marketing question: which loan narratives are associated with faster funding? The maintained research now asks a more useful next question: what information does text add, and what evidence would justify changing how a loan is presented? We distinguish what the competition work established from later research.

**Sources:** [UNSW finalist results](https://www.unsw.edu.au/business/our-schools/marketing/news-events/student-events/MA-hackathon); `docs/2_evidence_and_corrections.md`.

## 2. Prioritise a fair text comparison and a targeted pilot

**Message:** The immediate recommendation is a sequence of evidence-building decisions.

**Reader decision:** Approve the research sequence before commissioning additional model complexity.

**Evidence status:** Recommendation. Source audit found an unsupported narrative-free claim; existing inference is observational and context-sensitive.

**Exhibit and layout:** Three large numbered statements on a flat canvas; no invented impact scores.

**Speaker briefing:** The first investment should address the biggest uncertainty: whether narrative information adds stable value once the loan context is known. Then we can ask whether a particular factual presentation change improves outcomes. These are recommendations for research actions. We have not measured a return on investment or an intervention effect.

**Sources:** `docs/4_research_review.md`; `docs/5_ml_refinement_plan.md`.

## 3. The outcome is completed funding on the platform

**Message:** The observed sample and timing determine what the project can claim.

**Reader decision:** Interpret later results within completed records and distinguish borrower disbursal.

**Evidence status:** Primary population and descriptive audit. 1,453,846 input rows; six negative durations excluded; 1,453,840 eligible, including 1,637 refunded records. Dictionary reports 96.4% pre-disbursal.

**Exhibit and layout:** Large eligible count at left, listing-to-completion timeline in text at right, precise population footnote.

**Speaker briefing:** The full input contains 1,453,846 records from 2016 to 2025. Six negative durations are excluded. The analysis includes 1,637 refunded records with valid completed durations. The dictionary's full-data descriptive audit reports 96.4% pre-disbursal, so listing-to-completion time often begins after money has already been disbursed. It does not directly measure borrower waiting, partner liquidity or welfare. Unfunded and expired listings are needed to study all-listing success.

**Sources:** `reports/generated_full_dataset/analysis_summary.json`; `docs/1_data_dictionary.md`; `docs/2_evidence_and_corrections.md`; [Kiva historical process explanation](https://www.kiva.org/blog/qa-expiring-loans-credit-limits-and-the-evolution-of-kiva).

## 4. Investigate four connected parts of the funding process

**Message:** Choose a mechanism to investigate before choosing a lever to change.

**Reader decision:** Prioritise the missing data required by the intended intervention.

**Evidence status:** Working issue tree. Repository schema and Kiva process documentation; missing fields are data requests, not established causes.

**Exhibit and layout:** Native editable issue-tree matrix with observed versus missing evidence.

**Speaker briefing:** This issue tree is a working decomposition. Its branches interact: a partner's process may affect both wording and exposure. Literature gives reasons to consider prosocial framing and lender preferences, while Kiva describes editing and translation in the posting process. None of these mechanisms is identified by a predictive importance chart. We should request data that can distinguish them.

**Sources:** `docs/1_data_dictionary.md`; [Kiva process FAQ](https://www.kiva.org/blog/how-kiva-works-faqs); [Allison et al. (2015)](https://www.thallison.com/wp-content/uploads/2022/03/etap.12108.pdf); [Seven-step problem solving](https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/how-to-master-the-seven-step-problem-solving-process).

## 5. Saved forecasts show signal among completed loans

**Message:** Prediction is useful evidence of information content, but does not isolate the contribution of text.

**Reader decision:** Accept the historical benchmark and request the missing controlled comparison.

**Evidence status:** Primary August snapshot. Median MAE 8.72339662505516, Ridge 6.632280583545429, HGB 5.203114192747133. Classifier AUC .8997080625176485, AP .8301490806510436. Holdout 278,887.

**Exhibit and layout:** Native editable MAE bar chart with zero baseline and three models. Classifier AUC/AP at right. Explicit completed-record population.

**Speaker briefing:** The saved August pipeline outperformed its training-median baseline on later completed loans. The nonlinear duration model reduced MAE from 8.72 to 5.20 days, and the 24-hour classifier had AUC 0.900 and average precision 0.830. This compares model configurations, not a structural-only model with an otherwise identical text-added model. It therefore cannot quantify text's added value. These are saved metrics, not a new run. The posting-date split also needs a label-availability audit before a stronger historical-deployment claim.

**Sources:** `reports/generated_full_dataset/analysis_summary.json`; `reports/generated_full_dataset/provenance.json`; `docs/5_ml_refinement_plan.md`.

## 6. The missing experiment is the incremental value of text

**Message:** Same rows, model family, chronology and tuning budget make the comparison interpretable.

**Reader decision:** Run the matched comparison before saying that structure dominates or text adds little.

**Evidence status:** Proposed experiment, no new results. Notebook 2 uses narrative features in every predictive fit. Historical Ridge ablation is narrower and not a fresh October prediction run.

**Exhibit and layout:** Comparison design table, not simulated performance bars.

**Speaker briefing:** The notebook's claim that the classifier needs no narrative features contradicts its input matrix. We should correct that claim immediately in the next notebook revision. The primary research experiment uses matched feature blocks within the same model family. Text-only performance is diagnostic because text can encode country, purpose and programme. The key quantity is the paired difference between structure plus text and structure alone, with uncertainty and a practical threshold. Compare S versus S+text and S+P versus S+P+text on the same rows. P is an unvalidated programme-text proxy; these contrasts do not identify confounding removed or partner effects.

**Sources:** `notebooks/2_full_dataset_modeling.py:270`; `notebooks/2_full_dataset_modeling.py:987`; `src/feature_sensitivity.py:532`; `docs/5_ml_refinement_plan.md`.

## 7. Large row counts do not remove contextual uncertainty

**Message:** Regional narrative patterns require careful treatment of the number of independent countries.

**Reader decision:** Treat regional patterns as exploratory hypotheses, not country-specific writing advice.

**Evidence status:** Primary August estimates. Middle East slope −.0729, normal interval [−.1003,−.0456], heuristic [−.2502,.1043], 2 countries; Central America −.0742, normal [−.0879,−.0605], heuristic [−.1629,.0145], 2 countries. Slope units: change in log(1+days) per additional family mention per 100 words.

**Exhibit and layout:** Two-region native table with point estimates, normal intervals and heuristic intervals. Clearly label the latter as uncalibrated sensitivity.

**Speaker briefing:** The two regional point estimates suggest faster completed funding with more family mentions, conditional on the primary model. Each pooled region contains only two countries. The normal-reference country-clustered intervals and the much wider t(1) screen show why the uncertainty deserves attention. The screen is heuristic and is not a calibrated correction. In the same primary analysis, urgency has country-clustered p=.4943 for duration and .2233 for 24-hour completion. Failure to reject does not establish a negligible effect.

**Sources:** `docs/2_evidence_and_corrections.md`; `reports/generated_full_dataset/analysis_summary.json`; [Cluster-robust inference guidance](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015.pdf).

## 8. Later checks retain some narrative associations

**Message:** Statistical support changes with specification; a universal editing benefit remains unestablished.

**Reader decision:** Retire the blanket null story while retaining the intervention boundary.

**Evidence status:** Reviewed October research extension. Same 1,453,840 eligible rows and 48 countries across four fits. Joint framing families remain associated. Primary predictive models were not rerun.

**Exhibit and layout:** Compact specification comparison plus one clearly unit-labelled 24-hour result. Keep the two outcomes separate.

**Speaker briefing:** The October extension is later research, separate from the competition submission. The third-person duration estimate changes modestly, while its adjusted p-value crosses .05. This is not proof that the association disappeared. Business framing is associated with a lower 24-hour completion probability under the programme specification. Several joint families remain associated. The programme variable is a text-derived proxy, not a verified partner ID. Coefficients are per extra mention per 100 words, and the duration outcome is log(1+days). Multiplicity is handled within each outcome/specification, not across the entire research history. Duration pointwise 95% intervals are [−0.013833, −0.004183] for expanded controls and [−0.013210, −0.002965] for programme adjustment. Business framing has a pointwise interval [−0.390, −0.126] percentage points. Intervals are pointwise; the displayed p-values are BH-adjusted within each outcome/specification.

**Sources:** `reports/expanded_feature_sensitivity_reviewed/README.md`; `reports/programme_proxy_audit/README.md`.

## 9. Choose actions by evidence and readiness

**Message:** Prioritise learning value without inventing intervention returns.

**Reader decision:** Choose the first two research tasks and define the gate for a pilot.

**Evidence status:** Proposed prioritisation. Synthesises current evidence boundaries. No cost or benefit estimates were collected.

**Exhibit and layout:** Native options matrix using verbal judgments, no artificial impact scores.

**Speaker briefing:** This is the consulting decision. We can confidently recommend a diagnostic and fair comparison because they close specific evidence gaps. The editing pilot is a candidate, not a proven solution. Automated visibility allocation needs a suitable population, calibration, capacity rules and evaluation of who gains or loses. A ranking of slow loans does not tell us which loans would benefit most from extra attention.

**Sources:** `docs/4_research_review.md`; `docs/5_ml_refinement_plan.md`.

## 10. Make the notebook an argument readers can verify

**Message:** Each exhibit should answer a question and lead to a bounded interpretation.

**Reader decision:** Refactor around shared src functions and a versioned result manifest.

**Evidence status:** Proposed notebook redesign. Current walkthrough has specification drift, repeated hardcoded claims and conflicting interpretation.

**Exhibit and layout:** Three spacious sections with analytical outputs beneath each heading.

**Speaker briefing:** The next notebook should use the authoritative implementation and put insight next to evidence. Every major exhibit should state what we observe, why it matters and what remains unresolved. We should not repeat hardcoded metrics or describe a later source-validation pass as a complete notebook run. A full-data execution and accepted report bundle will be required before the revised empirical findings are promoted.

**Sources:** `docs/5_ml_refinement_plan.md`; `src/modeling.py`; `notebooks/2_full_dataset_modeling.py`.

## 11. Test one truthful presentation change

**Message:** A prospective experiment should estimate a defined intervention on all eligible listings.

**Reader decision:** Agree the intervention and observation contract with participating partners.

**Evidence status:** Proposed pilot, no measured benefit. Candidate factual clarity/specificity prompt, usual-content control. Assignment, horizon, practical threshold and power are not yet fixed.

**Exhibit and layout:** Four numbered steps with endpoint and guardrails in a separate short statement.

**Speaker briefing:** One candidate is a prompt that makes the existing purpose and use of funds clearer while preserving facts. Compare the offer of that prompt with usual practice and include all eligible listings in analysis. Decide the assignment unit to limit staff/template contamination and marketplace spillovers. Choose one primary completion horizon, a practical effect threshold and sufficient independent units before launch. Do not compare duration only among loans that fund after treatment. Measure accuracy, editing burden, representation and displacement as guardrails. No sample size or duration is justified yet.

**Sources:** `docs/4_research_review.md`; [Marketplace experimentation guidance](https://digitaleconomy.stanford.edu/publication/interference-bias-and-variance-in-two-sided-marketplace-experimentation-guidance-for-platforms/).

## 12. Advance when each decision has enough evidence

**Message:** The next milestone is a credible comparison, followed by a decision on whether to pilot.

**Reader decision:** Start with claim correction, outcome availability and the feature-block comparison.

**Evidence status:** Recommended delivery sequence. Research plan with dependency-based gates; no committed delivery dates.

**Exhibit and layout:** Four horizontal work stages, owners and concrete exit tests.

**Speaker briefing:** The immediate work is to correct the analytical story and establish a data contract. Next, run the matched full-data benchmark and inspect stability. Then decide whether the remaining uncertainty warrants a pilot, additional data or stopping a proposed feature. Scale only if a prospective practical benefit and acceptable guardrails support it. These are functional owner suggestions, not claims about individual work by Mike or Sophia. The project's contribution is the evidence and the disciplined next decision.

**Sources:** `docs/5_ml_refinement_plan.md`; `docs/4_research_review.md`.

## 13. Appendix: evidence register

**Message:** Every claim belongs to a specific result set and population.

**Reader decision:** Use the right run when reusing any number.

**Evidence status:** Evidence provenance. Existing report manifests and correction notice.

**Exhibit and layout:** Native evidence ledger.

**Speaker briefing:** The local historical PPTX has 15 slides. Other notes refer to separate 14-page and 13-page exports. We cannot assume they are identical. This revised deck preserves those historical files and uses an explicit evidence ledger. The 100-row proposal example is not comparable to the full-data run. New paired notebooks remain output-free/source-validated unless actual execution is recorded.

**Sources:** `docs/2_evidence_and_corrections.md`; `docs/presentation/README.md`.

## 14. Appendix: primary predictive benchmark

**Message:** Keep metrics, target units and population together.

**Reader decision:** Read complementary metrics and audit the prediction task before deployment.

**Evidence status:** Primary August snapshot. Exact JSON report values; no rerun.

**Exhibit and layout:** Native benchmark table with negative R² retained.

**Speaker briefing:** Primary numeric values are read from the saved report. Ridge trains on log duration and is scored in days after exponentiation. This target/loss choice warrants inspection of tail predictions; a negative R² can coexist with a lower MAE than the baseline. The classifier's negative class is completed funding after 24 hours, not expired or never-funded listings. The historical holdout has already been examined and informed later research, so it is not a fresh untouched evaluation.

**Sources:** `reports/generated_full_dataset/analysis_summary.json`; [Probability calibration documentation](https://scikit-learn.org/stable/modules/calibration.html).

## 15. Appendix: replace claims that exceed the evidence

**Message:** Accurate language is part of analytical quality.

**Reader decision:** Apply these replacements consistently in notebook prose and future slides.

**Evidence status:** Corrections for current use. Notebook/deck audit and current evidence map.

**Exhibit and layout:** Two-column replacement table; historical materials remain preserved.

**Speaker briefing:** Several old sentences are stronger than the data allow. The correction should be systematic rather than leaving a careful caveat at the end while overclaiming earlier. Also retire cross-unit coefficient rankings, the unsupported selectivity explanation for period trends, the 20,000-loan topic sample presented as full-data evidence, and claims that a heuristic few-cluster screen is calibrated inference.

**Sources:** `docs/4_research_review.md`; `docs/2_evidence_and_corrections.md`; [SHAP causal interpretation guidance](https://shap.readthedocs.io/en/latest/example_notebooks/overviews/Be%20careful%20when%20interpreting%20predictive%20models%20in%20search%20of%20causal%20insights.html).

## 16. Appendix: prioritised research experiments

**Message:** Complexity follows a demonstrated research need.

**Reader decision:** Run the inexpensive information and validity checks first.

**Evidence status:** Proposed experiments. Detailed notebook plan; experiments are not executed.

**Exhibit and layout:** Ranked work table with concrete gates.

**Speaker briefing:** Sparse linear text baselines and the existing tree family are sufficient to establish a strong starting comparison. Embeddings should respond to a documented measurement or prediction gap. Survival analysis requires censored and unsuccessful listing histories and an explicit competing-event design. Causal forests or double ML do not solve unidentified treatment or missing confounding information merely by being more sophisticated models.

**Sources:** `docs/5_ml_refinement_plan.md`; [Survival evaluation documentation](https://scikit-survival.readthedocs.io/en/stable/user_guide/evaluating-survival-models.html); [Egami et al.: causal inference using texts](https://collaborate.princeton.edu/en/publications/how-to-make-causal-inferences-using-texts/).

## How to update after the next research run

- Slide 5 retains the primary historical benchmark unless a new accepted run is deliberately promoted.
- Slide 6 becomes the paired incremental-text result only after the matched experiment is complete. Display gains, uncertainty, period stability and practical units; do not invent placeholder numbers.
- Slide 10 can then show the strongest actual calibration or error-diagnostic exhibit rather than the proposed notebook structure.
- Slide 8 always remains explicitly post-competition. Its OLS/LPM coefficients must not be labelled primary GLM coefficients.
- Slide 11 remains a proposed pilot until a real experiment exists. A better retrospective model does not change that status.
- If a ten-slide version is needed, move the October extension and notebook redesign to the appendix. Retain outcome scope, the missing ablation, uncertainty and the decision gate.

## Changes to the historical story

Retain the research question, data scale, chronological discipline and uncertainty lesson. Replace the blanket null ending, the unmeasured borrower-wait/capital-impact claims and the unsupported structural-dominance rhetoric. Move the 20,000-record exploratory topic exhibit to optional appendix material with its sample label. Replace screenshots of code and dense statistical output with one evidence-led exhibit per slide. Keep effect units, target, population and run source adjacent to results.

The editable source is [storyline.json](source/storyline.json). Its speaker notes and evidence entries are used to build the new deck; the September files are preserved.
