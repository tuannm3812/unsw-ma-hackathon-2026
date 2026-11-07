# Independent technical review

Review date: 2026-11-02. Automated independent code and artifact review,
separate from the implementing agent's verification. Benchmark SHA-256:
`40f324421975fbd3f4fbf17eba109493a11d0bf4011dd4885c99e21c143215bd`.

The reviewer supported technical acceptance conditional on the independent
prediction recomputation passing. Source/identity validation passed for the
65 model/arm records and 120 paired intervals. The five disjoint evaluation
cohorts contain 728,640 records. The archived source and current computational
source hashes match the recorded provenance.

All aggregate metrics inspected were finite. Maximum Ridge iterations were
665 of 1,000; maximum SGD iterations were 62 of 100. There were exactly three
known matmul warnings in each of the 15 TF-IDF linear fits, with no other
recorded model-warning pattern. Synthetic numerical probes and the reproduced
2021 T fit support documenting the Accelerate warning behaviour, while retaining
the explicit limitation that not every fit received a higher-precision rerun.

Linear duration gains are positive in each annual evaluation. Country-cluster
intervals include zero in four of five windows, so the temporal gains do not
establish a universal geographic or causal effect. Compact-tree gains concern
simpler text blocks and are much smaller. All intervals are pointwise
fixed-model sensitivity calculations without multiplicity adjustment or
retraining uncertainty.

Material review changes addressed before selection: require complete result
sets and valid protocols; bind both training and evaluation row hashes and the
feature cache to provenance; recompute group diagnostics; distinguish feature
blocks visibly on slides; correct the evidence register and completed-stage
briefing; keep geographic uncertainty visible. Primary/October snapshots and
the submitted proposal showed no tracked changes.

`prediction_review.json` records whether the final recomputation prerequisite
was satisfied. The snapshot selection script refuses acceptance unless that
receipt passes and matches the reviewed benchmark hash. Technical acceptance
supports this retrospective research artifact, not deployment or a writing
intervention claim.
