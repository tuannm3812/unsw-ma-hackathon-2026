# Rejected programme inference — diagnostic record

This first maintenance run completed on 2026-10-24, but final review found a
numerical defect in the programme-adjusted model. **Do not use its programme
coefficients or family tests as substantive evidence.** The outputs, execution
log and provenance are preserved unchanged to document the failure. Use the
[corrected reviewed run](../expanded_feature_sensitivity_reviewed/README.md)
for current sensitivity findings once its completion record is available.

On all 1,453,840 eligible rows, `whySpecial_missing` exactly equals the missing
programme category indicator (40,012 records; zero disagreements). It lies in
the span of the categorical programme controls and must not be estimated as a
separate narrative feature. The old iterative projection left residual norm
3.049656584e-6 against original norm 200.02999775, a ratio of 1.524599619e-8.
That narrowly exceeded the 1e-8 absorption guard. Normalizing this solver noise
created a false predictor, with standard error 3,356,206 in duration and
1,114,428 in the 24-hour model.

LSMR's successful backward-error stop is not a guarantee of the forward
residual bound assumed by that guard. A 12,000-row synthetic regression test
reproduced the defect. The fix detects exact constancy within each categorical
control on complete cases, using the encoder's string grouping semantics,
before residualization. The numerical guard remains for general dependencies.
This removes all three programme-determined `whySpecial` features without
changing row eligibility or arbitrarily widening a tolerance.

The baseline expanded outputs passed independent numerical checks, but this
bundle as a whole is diagnostic, not the accepted maintenance snapshot. The
original August primary reports and September recovered outputs are unaffected.

The rejected run's estimator is preserved in local commit `f98e7e1`; the
runner and audit helpers are in `e57e5f2`. All recorded source hashes were
checked against that estimator version and the unchanged other sources.
The completion record's original base revision and dirty-tree state are
retained rather than rewritten to claim a clean historical run.

Machine-readable rejection status: [review_status.json](review_status.json).
