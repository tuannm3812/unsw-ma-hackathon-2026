# Reviewed expanded inference — 2026-10-24

Completed and independently reviewed on **2026-10-24 (Sydney)**.
[Accepted as exploratory sensitivity evidence](review_status.json).

This post-competition extension compares expanded narrative inference with
and without programme-text controls. It is separate from the
[primary August snapshot](../generated_full_dataset/) and the
[recovered September sensitivity](../expanded_feature_sensitivity/README.md).
It does not rerun primary models, chronological Ridge comparisons, or holdout
validation. The paired sensitivity notebook remains source-validated and
output-free; this CLI run is not evidence of full notebook execution.

## Verified results

All four fits use **1,453,840 eligible completed durations from 1,453,846 input
records**, with **48 country clusters**. Six negative durations were excluded;
there are **zero additional complete-case exclusions** and zero missing values
in every modeled column in all four fits. Programme controls add no row loss.
Source and vendored-resource hashes were unchanged during the run.

The expanded control matrix has rank **244/244**; the programme-adjusted matrix
has rank **883/886**. Both omit neutral sentiment as a deliberate reference.
Expanded inference retains 26 narrative terms. Programme controls additionally
absorb `whySpecial_missing`, `whySpecial_char_count` and `whySpecial_word_count`,
leaving **23** narrative terms and total parameter rank **906**.

The corrected expanded coefficients match the recovered September coefficients
to within 2.1e-8 in absolute value. This verifies agreement of the current rerun;
it does not recover the old run's missing provenance. The rejected first run's
programme results must not be mixed into this comparison.

**Third-person framing:** programme adjustment changes the duration estimate
modestly, while its individual BH-adjusted p-value moves from **0.01236 to
0.06062**. Its 24-hour adjusted p-value is above 0.05 in both specifications.
This is sensitivity of statistical support, not proof that the association
vanishes or that programme differences explain it causally.

| Specification | Outcome | Coefficient | Pointwise 95% country-clustered interval | BH-adjusted p |
| --- | --- | ---: | --- | ---: |
| Expanded | Log duration | -0.009008 | [-0.013833, -0.004183] | 0.01236 |
| Expanded | 24-hour probability | 0.001502 | [0.000110, 0.002893] | 0.22748 |
| Programme-adjusted | Log duration | -0.008088 | [-0.013210, -0.002965] | 0.06062 |
| Programme-adjusted | 24-hour probability | 0.001436 | [-0.000499, 0.003371] | 0.49655 |

Units are per additional third-person mention per 100 words. Intervals are
pointwise, not simultaneous BH-adjusted intervals; an interval excluding zero
can coexist with an adjusted p-value above 0.05.

**Individual terms and joint families:** third-person framing is the only
individual term below BH 0.05 in expanded duration; none pass in expanded
24-hour funding. No individual duration term passes after programme adjustment.
Business framing is the only programme-adjusted 24-hour term below BH 0.05:
**-0.002579 probability units** (-0.258 percentage points) per additional mention
per 100 words, with pointwise 95% interval [-0.003898, -0.001259]
and adjusted p = **0.00635**.

Several joint families remain associated, so a blanket “no text association”
conclusion is unsupported. Auxiliary-text joint tests do not pass after
programme adjustment. These differ materially from the rejected first run,
where an absorbed indicator contaminated that family test. All family tests
in the corrected run are available:

| Feature family | Expanded duration q | Expanded 24h q | Programme duration q | Programme 24h q |
| --- | ---: | ---: | ---: | ---: |
| description form | 0.00028444 | 0.013221 | 1.8981e-09 | 0.015576 |
| auxiliary text | 0.016017 | 0.26078 | 0.38583 | 0.61488 |
| specificity | 0.064548 | 0.00064127 | 0.38583 | 0.0037369 |
| framing | 6.7673e-05 | 0.00036665 | 6.2626e-05 | 7.6754e-05 |
| sentiment | 0.016017 | 0.076061 | 0.066492 | 0.034507 |

Full coefficients and tests are in the [expanded report](expanded/expanded_sensitivity.json)
and [programme-adjusted report](programme_adjusted/expanded_sensitivity.json),
with CSV and text companions in each directory. All JSON/CSV values and BH
calculations were cross-checked; matching populations and provenance were
verified. The [completion record](provenance.json), [environment receipt](environment_supplement.json)
and [execution log](run.log) accompany this snapshot.

## Design and interpretation

Both specifications use the same deterministic narrative features and rich
loan, borrower, country, activity and calendar controls. Duration is OLS on
`log(1 + funding days)`; 24-hour funding is a linear-probability model. Negative
duration and positive 24-hour coefficients both point toward faster funding.
A probability coefficient multiplied by 100 is in percentage points.

The additional control groups trimmed, nonblank `whySpecial` text into
categories, with a separate missing category. Only anonymous category codes
are exported. The [programme audit](../programme_proxy_audit/README.md) records
coverage and nesting. These are unvalidated programme-text categories, not
observed partner identities. Conditional comparisons do not establish that
confounding is removed, identify authorship, or demonstrate causal effects.
Country clustering does not account for any unmodeled cross-country dependence.

The estimator first removes features exactly constant within every level of
any categorical control, on the complete-case estimation sample. It then
partials out controls using unit-preconditioned sparse least squares, checks
convergence, drops remaining absorbed/dependent narrative columns, and uses
numerical control rank in the CR1 country-cluster correction. Individual
intervals/tests use a t(G−1) reference. Family Wald tests use an F reference
only when their covariance is nonsingular; otherwise they are unavailable.
These are approximate procedures, not finite-sample guarantees.

Benjamini–Hochberg adjustment is separate for retained narrative terms and
reported feature-family tests within each outcome and specification. It does
not control a single study-wide error rate across both outcomes, specifications
and earlier searches. A family after dropping columns tests only its retained
terms. Dropped columns are not estimated as zero effects. Neutral sentiment is
a deliberate reference restriction, not proof of exact compositional dependence.

A joint family test can support an association among correlated features even
when no individual coefficient passes its own multiple-testing adjustment.
Neither test selects a causal writing intervention. Non-significance does not
establish no association or practical equivalence. Compare sample membership,
effect sizes and uncertainty, not only whether a p-value crosses 0.05.

## Numerical correction and rejected first run

The [first maintenance run](../expanded_feature_sensitivity_diagnostic/README.md)
is preserved as rejected programme inference. LSMR left a small residual for a
missingness indicator exactly determined by the programme category. That noise
survived a numerical cutoff and was normalized into a false predictor with an
enormous standard error. An actual-data check and a synthetic regression test
reproduced the failure. The exact categorical-absorption check fixes the cause
without changing row eligibility or widening a numerical tolerance.

The corrected source passed 135 offline tests, including a high-cardinality
reference-indicator regression that matches explicitly omitting the absorbed
feature. The estimator and fix also received independent review. Test success
alone is not evidence of successful full-data execution; the completion and
result checks below establish that separately.

## Reproduction and provenance

Run from the repository root with the restricted input and project environment:

```bash
.venv/bin/python -u -m src.research_review \
  --data data/Kiva_Loans.pkl \
  --output-dir reports/expanded_feature_sensitivity_reviewed_NEW_RUN_ID \
  > /tmp/reviewed-inference_NEW_RUN_ID.log 2>&1
```

Choose a fresh directory; existing destinations are refused. The default chunk
size is 25,000 records. Chunking bounds feature-extraction memory while retaining
the same inputs used by the regression. No borrower-level feature cache is
exported. Save a privacy-reviewed execution log beside the outputs.

`provenance.json` is written after all four fits and contains start/end times,
input SHA-256 and size, eligible rows, package versions, base Git revision,
dirty-tree state and per-source hashes. This run began from a maintenance tree
with uncommitted work, so the base revision alone does not identify all sources;
use the content hashes. The source content is preserved in commit `e57e5f2`,
verified against every recorded source hash. This does not change the original
run-start dirty-tree record. Source hashes are checked again at completion.
Each scenario's embedded provenance is the run-start record; the root record
confirms completion. `environment_supplement.json` captures NLTK and vendored
lexicon/resource hashes at the start and verifies them again at completion.

A missing root completion record means the run is incomplete. Output files
are atomic individually; the multi-file bundle is not a transaction. A
completed run still requires numerical and substantive review, as the rejected
first attempt demonstrates.
