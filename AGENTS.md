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
better fit. The tested `src/` pipeline is authoritative; label the simpler
notebook fits and expanded sensitivity results separately.

## Evidence locations

- `docs/1_data_dictionary.md` — field definitions
- `src/` — authoritative pipeline; `notebooks/` — executable walkthroughs
- `reports/generated_full_dataset/` — primary saved results and provenance
- `reports/expanded_feature_sensitivity_reviewed/` — separate reviewed inference extension
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
- New research notebooks remain output-free and source-validated; do not
  describe this as proof of full notebook execution or a fresh predictive run.
- Deadlines and judging criteria came from the organisers and are mutable —
  re-check against their page rather than the README.
