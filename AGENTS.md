# unsw-ma-hackathon-2026

Team repository for the UNSW Marketing Analytics Hackathon Challenge 2026.
Loan-level Kiva data (2016-2025, **1,453,846 rows**) studying **funding speed**
in subsistence marketplaces: which narrative choices in a borrower's loan
description associate with faster funding, for whom, and when.

Shared team repo — commits are visible to teammates and feed assessed
deliverables.

## Standards

Follow the master standard at `~/Documents/GitHub/coding-standards/`.
Project-specific rules and deliberate overrides: @docs/0_coding_standards.md

## Deltas from the master

**Analysis runs against the full dataset, not the sample.** The proposal round
used a 100-row illustrative sample; the pipeline has since been run and verified
against all 1,453,846 rows. A number sourced from the sample is not comparable
to one from the full run — say which produced any figure quoted.

**This is an inference project, not a leaderboard one.** There is no held-out
score to optimise. Claims are about association between narrative framing and
funding speed, and the judging weights insight and communication over model
performance. Prefer a defensible, well-explained effect to a marginally better
fit.

## Evidence locations

- `docs/1_data_dictionary.md` — field definitions
- `notebooks/` — the executable analysis
- `reports/` — generated outputs
- `proposal/` — the submitted proposal (round 1)
- `README.md` — full-dataset results and presentation logistics

## State

Proposal round done — **the team was selected as one of 8 finalists**. Full
dataset pipeline run and verified.

**The README's "final round: in progress" is stale.** It gives the final slides
deadline as 2026-09-03 17:00 Sydney, which has passed. Confirm the actual
current stage before acting on anything the Status section says.

## Open risks

- **Uncommitted work is present**: a feature-sensitivity notebook, script, its
  report directory, `src/feature_sensitivity.py` and its test are all untracked.
  Decide whether it belongs in the record before it is lost or accidentally
  swept into an unrelated commit.
- Deadlines and judging criteria came from the organisers and are mutable —
  re-check against their page rather than the README.
