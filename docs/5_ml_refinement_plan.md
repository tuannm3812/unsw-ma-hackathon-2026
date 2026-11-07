# Machine-learning and notebook refinement plan

Date: 2026-11-02. Status: approved pre-run research design.
Read with the [research review](4_research_review.md) and
[current evidence map](2_evidence_and_corrections.md).

The executed phase is documented in the [November findings](6_matched_text_results.md).
This plan preserves the original diagnosis and proposed scope; notebook line
references refer to revision `7afea5f`. Human annotation, historical field and
all-listing data, nested tuning, and a prospective pilot remain later work.

## 1. What the maintained notebook should answer

**Does narrative information improve forecasting beyond structured loan context,
and is any improvement stable enough to matter for a defined use?**

The current primary benchmark has useful retrospective performance. Its saved
2024–2025 holdout contains 278,887 completed-funding records. The nonlinear
duration benchmark has MAE 5.2031 days and R² 0.5420. The classifier has ROC AUC
0.8997, average precision 0.8301 and Brier score 0.1156. These are saved August
results, not outcomes of this review. They do not quantify text's incremental
value or validate an all-listing operational service.

Keep this project inference-led. The ML study supplies complementary predictive
evidence and a diagnostic of information content. It cannot establish the effect
of adding a word, changing a photograph or increasing a loan's visibility.

## 2. Repair the meaning before extending the modelling

| Location inspected | Issue | Planned correction |
| --- | --- | --- |
| `notebooks/2_full_dataset_modeling.py:270–275,370–373,987–989` | Classifier includes narrative features despite a narrative-free claim | State the actual feature set; replace the claim with a measured ablation result only after execution |
| Same notebook `:379–389,987–996` | A live at-risk claim conflicts with its own population limitation | Explain completed-loan ranking consistently |
| Same notebook `:819–823,863–886` | SHAP is first called an independent check, then correctly qualified | Use model-behaviour language throughout |
| Same notebook `:227–229,410–417`; `src/features.py:55–60`; `src/statistical_analysis.py:94` | Lexicons and formula differ, including description-length control | Document the crosswalk and reuse authoritative functions in the maintained workflow |
| `src/validation.py`, chronological split in `src/modeling.py` | Posting-date cutoff alone does not enforce label availability | Add explicit as-of eligibility and count affected rows before interpreting a rerun |
| `src/feature_sensitivity.py`, notebook 3 | Structural-to-expanded Ridge comparison exists but is a different study | Preserve it as historical exploratory evidence; it is not a fresh nonlinear or classifier ablation |

Update `.py` and `.ipynb` together when implementing. Preserve old result
snapshots and historical submitted artifacts. The current task prepares the
design and deck; it does not quietly rewrite results or claim notebook execution.

Correct the teaching prose as well: notebook 2 lines 41 and 45 incorrectly
describe R² as bounded by 0–100% and a p-value as confidence that a link is real.
R² can be negative; a p-value is calculated under a specified null/model, not
the probability that a claim is true. Label log-outcome and day-outcome R²
separately. Do not compare raw coefficients with different units as effect-size
rankings, or claim that better tree performance specifically proves interactions.
Notebook 1's opening explanation of borrower waiting also conflicts with the
pre-disbursal audit. These corrections belong in both walkthroughs.

The historical Ridge block comparison has MAE 6.679141 days with structure and
6.649177 with expanded text, about 0.030 days lower aggregate prediction error.
It is a recovered September result with incomplete original provenance, not a
fresh benchmark, editing benefit or equivalence test. It motivates a better
comparison without prejudging its result. The primary Ridge's negative day-space
R² despite lower MAE also motivates inspection of extreme predictions and loss
alignment, rather than an automatic conclusion about model interactions.

## 3. Data contract and as-of evaluation

Define the prediction time as the instant a listing is posted. For each field,
record its source, definition, availability at that instant and whether it can
be edited later. Check original listing text versus a later snapshot, programme
text, repayment terms, loan amount and macroeconomic variables. A field being
present in a final export does not establish its historical availability.

At every model-training cutoff:

- Require training listings to precede the cutoff and their target labels to be
  observable by that cutoff. For duration this requires a completed-funding date.
- A 24-hour negative label can become known after 24 hours only if listing
  observation is reliable; the current completed-only selection remains a
  separate limitation. Document the label rule rather than borrowing the
  duration-completion rule automatically.
- Cohort membership must also be knowable. For a completed-only historical
  training replay, require completion by the cutoff for both targets. An open
  listing's 24-hour label may be known while its eventual inclusion in this
  dataset is still future information. Using it would create retrospective,
  oracle-selected membership. A true all-listing classification replay needs
  the complete historical listing population. Even with matured training,
  completed-only evaluation remains conditional on eventual completion.
- Count pre-cutoff postings with post-cutoff completions. Report their duration
  and group distribution. No such count has been computed in this review.
- Audit duplicate identifiers, exact/near-duplicate narratives and repeated
  templates across time. Duplication is a realistic deployment characteristic
  as well as a memorisation risk; show ordinary and novelty-sensitive results.
- Keep all six invalid-duration exclusions visible. Report refunded records
  separately and add an exclusion sensitivity; do not silently change the
  primary population of 1,453,840 valid completed durations.

Prevent newly computed group outcome averages from using current or future
outcomes. Only historical matured labels may contribute, with smoothing,
minimum-support rules and explicit fallback values for unseen groups.

## 4. A fair feature-block experiment

Create an explicit registry that assigns every predictor to one block. The
structured baseline must exclude all text-derived variables, including length,
sentiment, topics, text missingness and `whySpecial` categories. Retain missing
text records in matched comparisons with a documented empty-text treatment;
separately report that subpopulation. This makes the comparison interpretable.

| ID | Inputs | What it answers |
| --- | --- | --- |
| B0 | Training median for duration; training prevalence for classification | Can the model beat a naive, available baseline? |
| B1 | Past-only smoothed country/sector/calendar baseline | Does complexity improve on a simple context forecast? |
| S | Structured listing-time fields | How much can be learned without narrative information? |
| T | Text alone, including prespecified text metadata | What information does narrative carry, including proxy context? |
| S+M | Structure plus text presence, length and form | Is a gain mainly from missingness or formatting? |
| S+M+L | Add reviewed lexicon and sentiment measures | Do transparent constructs add information? |
| S+M+L+R | Add training-fitted TF-IDF/NMF or another representation | Does richer content help beyond simple measures? |
| S+P | Structure plus programme-text categories, separate from other narrative blocks | What does the proxy add before other text? |
| S+P+M+L+R | Add narrative blocks to the proxy-adjusted baseline | Does text still add information after that possible context proxy? |

Run within-family comparisons with identical eligible rows, splits, outcomes,
metrics, seeds and tuning budgets. An improvement from a linear structured model
to a nonlinear combined model does not isolate text value. Text-only accuracy
also does not isolate persuasion: descriptions encode sector, place and purpose.

Compare text's gain both without P (S versus S+M+L+R) and with P (S+P versus
S+P+M+L+R). Merely adding P after all text cannot determine whether P accounts
for the previously observed text gain. These remain predictive proxy comparisons,
not estimates of confounding removed or partner effects.

Start with Ridge/regularised logistic models, which accommodate sparse text,
and the existing histogram gradient-boosting family for structured and compact
representation blocks. Avoid densifying millions of high-dimensional TF-IDF
rows for tree models. Use a bounded training-fitted representation or a separate
sparse linear branch. Record peak memory, training time and inference time.

## 5. Validation that matches the question

Use explicit calendar cutoffs rather than equal row-count folds, because loan
arrivals are irregular. Proposed development backtests: train on available
history and evaluate successive 2021, 2022 and 2023 calendar windows; tune using
earlier nested windows only. Inspect both 2024 and 2025 separately under a frozen
protocol. These years have already been inspected in this project, so the new
comparison is a **retrospective benchmark**, not a newly untouched final test.
Independent confirmation needs genuinely unseen future data or a new external
evaluation population. No split can make previously seen results unseen again.

Within each outer training partition, fit vocabulary, topic model, imputation,
scaling, encoders and any calibration on appropriate earlier data only. Audit
histogram boosting's internal early-stopping behaviour for the pinned library
version. Use an explicit chronological validation tail where supported, or
choose iteration counts on earlier folds and disable automatic random validation
for the final training fit. Calibration needs its own suitable temporal data.

Report two distinct generalisation questions:

1. **Future loans in familiar contexts:** chronological evaluation, allowing
   previously seen countries/templates if that matches the intended setting.
2. **New contexts:** forward-time tests excluding seen partners where validated
   IDs exist, or labelled country/template novelty sensitivity. This is a harder
   transfer question, not a replacement score for routine deployment.

The scikit-learn guidance supports respecting both
[temporal and group structure](https://scikit-learn.org/stable/modules/cross_validation.html).
The exact windows above are proposed project choices and must be frozen before
comparing new candidates.

## 6. Metrics, uncertainty and practical relevance

| Target | Core measures | Decision interpretation |
| --- | --- | --- |
| Completed funding duration | MAE and median absolute error in days, RMSE, residual bias by duration/amount/time | Typical versus tail error; no single average describes all cases |
| Log-duration diagnostic | Error in `log1p(days)` and residual plots | Whether long tails dominate; distinguish from day-scale performance |
| Completion within 24h among observed completed loans | Average precision, ROC AUC, log loss, Brier, prevalence | Ranking and probability quality within the observed population |
| Defined capacity-limited review policy | Precision/recall at an agreed review capacity, coverage and workload | Whether an operational queue could be useful; needs the right population |

Fit a simple constant-probability baseline on training prevalence. Do not call
the holdout prevalence a trained baseline. Show reliability plots and bin counts:
[Brier score mixes several properties and is not a calibration test alone](https://scikit-learn.org/stable/modules/calibration.html).
Select decision thresholds on development data and show workload tradeoffs.

Report paired metric differences between S and each added block on identical
observations, not just two rounded scores. Prespecify dependence-aware resampling
appropriate to the claim: temporal blocks for future-period variation and a
country-cluster sensitivity for geographic dependence. Record block choices and
the population each uncertainty calculation represents. With only 48 countries
and uneven groups, avoid claiming exact uncertainty guarantees.

Use period, country, sector, amount-band, text-missingness and template-novelty
slices. Include group sizes, base rates and uncertainty, and suppress conclusions
for tiny groups. A slice is an error diagnostic, not permission to deprioritise
its borrowers. Choose a practical gain threshold with stakeholders before seeing
new results; there is no defensible universal “good AUC” or minimum improvement
for this project.

For duration, explain the loss function. `expm1` of a log-target prediction does
not generally estimate the conditional mean in days. Compare an appropriate
day-scale objective and a train-only retransformation strategy if mean forecasts
are required. Pinball-loss quantile forecasts are a useful optional extension
when an interval would improve expectations, with empirical coverage checked
over time. Treat them as predictions, not confidence intervals for causal effects.

## 7. Better text measurement before more text models

Create a private, stratified annotation pilot drawn across time, country,
sector, loan size, text length and template frequency. Sampling for annotation
or compute diagnostics is legitimate; all final model comparisons still use
the full eligible dataset. An initial 300–500 dual-coded records is a planning
range, not a proven sufficient sample size. Expand until construct-specific
uncertainty and subgroup coverage are adequate.

Use a written codebook for factual specificity, clarity, family orientation,
agency, need and urgency. Include ambiguous/absent cases, negation, translation
artifacts and boilerplate. Two reviewers code independently, discuss disagreements
and preserve both pre-adjudication labels and adjudicated labels. Report agreement
with uncertainty and per-label confusion, not a single overall accuracy number.
Do not show funding outcomes during construct labelling.

Separate annotation development from locked validation. Refine the codebook,
lexicons and prompts using development-period texts only for predictive
backtests. Hold later-period annotations for audit; use them to improve a
measure only in a newly labelled development round. Freeze definitions before
evaluating the corresponding prediction fold. A full-period descriptive
annotation study can be useful, but must not be presented as untouched
validation of a representation developed using those same texts.

Test lexicons and sentiment against this reference. A mention of family is not
automatically a persuasive family appeal. A positive sentiment score is not a
measure of credibility. VADER's social-media origin makes domain validation
worth checking, rather than assuming failure or suitability.

An embedding or locally run language model can be a challenger after this
baseline. Freeze model/version, prompts and label schema, check error patterns
and incremental benefit, and preserve factual text. Do not upload restricted
borrower narratives to an external service without a separate authorised data
workflow. No LLM-based causal interpretation or automated rewrite benefit is
established by predictive accuracy.

## 8. Explanations and inference

Use grouped ablation as the main incremental-information result. Then inspect
grouped holdout permutation, representative SHAP explanations and residual
examples. Independent one-hot-column permutation can create impossible categories;
permute a coherent source field or block. Correlated features can mask each
other's importance, as the [official documentation](https://scikit-learn.org/stable/modules/permutation_importance.html)
explains. Conditional permutations answer a different question and need a
defensible conditioning design.

Keep explanatory models in their own section with outcome, controls, estimand,
units, cluster counts, overlap and multiplicity explicit. Review country and
time dependence; investigate validated partner clustering if identities become
available. CR2 or wild-cluster methods may be sensitivities when their assumptions
fit, but none manufactures independent information for a two-country subgroup.
See [Cameron & Miller](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015.pdf).

Do not add causal forests or double ML merely to make the notebook more advanced.
Those methods still need an identified treatment, confounding assumptions,
overlap and a coherent counterfactual. A universal claim of no effect would
instead require a defensible equivalence margin, a suitable design and adequate
precision; the existing tests do not provide this.

## 9. When survival analysis becomes appropriate

Request all posted listings, event/status histories, expiry/withdrawal dates,
observation end dates and data-extract time before studying funding success.
Do not create artificial censored observations from the completed-only sample.
Treat funding, withdrawal and expiry according to the actual process; expiry
can be a competing event rather than innocuous independent censoring.

A transparent discrete-time hazard or Cox/AFT baseline may then precede survival
boosting. Evaluate at operational horizons with calibration and censoring-aware
scores, not only concordance. Check support for censoring weights and validate
their assumptions. [Scikit-survival's evaluation guide](https://scikit-survival.readthedocs.io/en/stable/user_guide/evaluating-survival-models.html)
explains the available metrics; it does not establish that the current data are
suitable. Survival analysis is therefore a data-dependent extension, not the
first fix to the current notebook.

## 10. Proposed notebook architecture

Refactor the existing maintained modelling walkthrough after its configuration
is agreed, using `src/` helpers. Keep notebook 3 as a separate reviewed sensitivity
walkthrough. Do not create several near-duplicate notebooks for each model.

| Section | Question and required output |
| --- | --- |
| 0. Decision and evidence status | Research question, population, saved-versus-fresh status, run manifest |
| 1. Outcome and availability audit | Row flow, status inclusion, outcome maturity and snapshot limitations |
| 2. Validation contract | Calendar windows, groups, novelty, preprocessing and early-stopping rules |
| 3. Baselines | Median/prevalence and past-only context benchmark |
| 4. Feature registry | Exact S/M/L/R/P block membership and availability |
| 5. Matched model comparisons | One experiment table with all blocks and models, same sample |
| 6. Incremental text value | Paired differences with uncertainty and practical units |
| 7. Probability and error quality | Reliability plot, residual distributions, tail and interval checks |
| 8. Stability and coverage | Time/group/novelty slices, failure cases, missing text |
| 9. Text construct validity | Annotation agreement, errors, topic/template stability |
| 10. Explanatory evidence | Primary and later sensitivity labelled separately; no causal attribution |
| 11. Decision and next test | What the model supports, what changes would need experiments |
| 12. Reproduction and limitations | Command, hashes, environment, exclusions, runtime and output provenance |

Every major exhibit should have three short sentences: **what is observed,
why it matters, and what remains unresolved**. Generate factual insight text
from accepted result artifacts where possible; avoid hardcoded celebratory
paragraphs that survive after a different model or dataset is run.

## 11. Implementation sequence and exit criteria

| Stage | Deliverable | Exit criterion |
| --- | --- | --- |
| A. Claims and specification | Notebook/deck claim crosswalk and feature registry | No narrative-free, live-deployment or universal-null claim without evidence |
| B. As-of data audit | Availability/duplicate/outcome-maturity report | Boundary violations quantified; inclusion rules explicit |
| C. Evaluation runner | Shared calendar splits and matched model/feature blocks | Synthetic tests prove no training beyond cutoff and identical comparison rows |
| D. Full-data benchmark | Immutable result bundle with logs and private row identity | All intended comparisons completed, failures visible, source/data hashes captured |
| E. Insight notebook | Paired sources, executable workflow and result-linked text | Full intended execution verified; output policy and private-data checks pass |
| F. Deck update | Paired text-gain chart, calibrated interpretation and group diagnostics | Every displayed number points to one accepted run and sample |
| G. External extension | All-listing data contract or powered pilot protocol | Stakeholder endpoint, assignment, feasibility and observation rules agreed |

Resource strategy: smoke-test on synthetic data, use a clearly labelled small
training subset only for implementation/performance checks, then conduct final
research on the full data. Cap model candidates and tuning budgets before running.
Do not claim a schedule or compute cost until a representative resource check.

The first three experiments to prioritise are **outcome-availability audit**,
**matched S versus S+text comparisons**, and **temporal calibration/error
stability**. Text annotation can proceed alongside them. Embeddings, multimodal
models, survival analysis and deployment follow only when their prerequisites
and decision value are established.
