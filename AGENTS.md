# unsw-ma-hackathon-2026

Team repository for the UNSW Marketing Analytics Hackathon Challenge 2026.
Loan-level Kiva data (2016-2025, **1,453,846 rows**) studying **funding speed**
in subsistence marketplaces: which narrative choices in a borrower's loan
description associate with faster funding, for whom, and when.

Shared team repo — commits are visible to teammates. Preserve submitted
deliverables and distinguish later research extensions from the submission.

## Standards

Follow `~/Documents/GitHub/coding-standards/coding_standards.md`.
Project-specific rules and deliberate overrides: @docs/0_coding_standards.md
Read that file explicitly if your agent does not expand `@` references.

## Deltas from the master

**Analysis runs against the full dataset, not the sample.** The proposal round
used a 100-row illustrative sample; the pipeline has since been run and verified
against all 1,453,846 rows. A number sourced from the sample is not comparable
to one from the full run — say which produced any figure quoted.

**This is an inference project, not a leaderboard one.** There is no held-out
score to optimise. Claims are about association between narrative framing and
funding speed. Prefer a defensible, well-explained effect to a marginally
better fit. The tested `src/` pipeline is authoritative; label historical
simpler notebook fits, expanded sensitivity and matched predictive extensions
separately. The maintained modeling notebook reads the reviewed shared-source
benchmark; it does not contain the old self-contained fits.

## Evidence locations

- `docs/1_data_dictionary.md` — field definitions
- `src/` — authoritative pipeline; `notebooks/` — executable walkthroughs
- `reports/generated_full_dataset/` — primary saved results and provenance
- `reports/expanded_feature_sensitivity_reviewed/` — separate reviewed inference extension
- `reports/text_benchmark_reviewed/` — separate November matched predictive benchmark
- `docs/6_matched_text_results.md` — current predictive findings and limitations
- `reports/equivalence_screen_reviewed/` — exploratory equivalence screen of October coefficients (2026-11-08)
- `reports/loss_alignment_2025/` — loss-alignment extension of the November benchmark, 2025 plus all five years (2026-11-08)
- `reports/evidence_sources/` — exploratory checks on where the text gain sits and the equivalence screen (2026-11-08)
- `reports/experiments_2026_11_08/` — exploratory subgroup, wild bootstrap, placebo, forecaster, triage and loan-detail checks (2026-11-08)
- `docs/presentation/claims_register.md` — every number the current deck and case study quote
- `docs/presentation/portfolio_deck/` — current portfolio deck source; governed by `docs/presentation/DESIGN.md`
- `docs/2_evidence_and_corrections.md` — current interpretation and historical corrections
- `proposal/` — the submitted proposal (round 1)
- `README.md` — current overview and reproduction entry points

## State

Hackathon complete — **Cultural Blend was one of 8 finalist teams**.
Finalist status was confirmed by the user and the official UNSW results,
reviewed 2026-10-24. Do not describe the team as a prize winner.
The primary August snapshot is verified saved evidence. Later full-data
programme audits and sensitivity reruns are separate research extensions;
they do not replace or rerun the primary models or predictive validation.
The November matched benchmark is a fresh, separate predictive extension with
as-of training cohorts and five retrospective annual evaluations.

Final-round logistics are archived in `docs/presentation/2026_final_round_logistics.md`.
Current work is research maintenance and portfolio presentation. Historical
slide preparations contain superseded claims; consult the correction notice.
The LinkedIn deliverable is an achievement entry, not a feed post.

## Open risks

- The recovered September sensitivity snapshot lacks original execution
  provenance and predates numerical fixes. Preserve it as history; use the
  separately reviewed inference snapshot for current sensitivity claims.
- `whySpecial` categories are an unvalidated programme-text proxy, not partner
  identities. Programme controls do not identify causal narrative effects.
- Notebook 2 was executed in reviewed-report mode against the November
  benchmark; training ran separately through `src.run_text_benchmark`.
  Notebook 3 remains source-validated only. Source pairs stay output-free;
  that policy alone is not proof of execution.
- Deadlines and judging criteria came from the organisers and are mutable —
  re-check against their page rather than the README.
