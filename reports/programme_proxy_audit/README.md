# Programme-text proxy audit — 2026-10-24

Fresh aggregate audit of the full 1,453,846-row input, using 1,453,840 valid
completed durations. Six negative durations are excluded by the primary
outcome-preparation function. The [JSON](programme_audit.json) records the
input SHA-256, inspected source hashes, revision/dirty state, configuration,
and actual Python/pandas versions. No raw programme text or borrower records
are exported.

## Findings

After trimming whitespace and treating blank/null text as missing:

- 40,012 valid-duration records lack programme text.
- 1,413,828 records have text, with 642 distinct nonblank categories.
- 590 of 642 categories (91.90%) appear in only one country; all these
  categories have complete country data. These categories account for
  93.36% of records with observed programme text.
- 140 categories contain at least 1,000 valid-duration records, covering
  1,348,259 records. Their unadjusted mean funding durations span
  0.224–30.933 days.

Earlier preparation notes counted 643 categories and 141 populated groups.
Those figures used a different missing/blank-label treatment. The current
figures explicitly exclude blank/null programme categories from these totals.
Neither counting convention verifies field-partner identity.

This pattern makes programme text a candidate grouping control. It does not
prove who wrote a description, identify distinct partners, or show a causal
programme effect. Country clustering already allows within-country dependence;
adding programme controls addresses a different question about the association
conditional on those categories.

## Reproduction

From the repository root in the project environment:

```bash
python3 -m src.programme_audit --data data/Kiva_Loans.pkl \
  --output-dir reports/programme_proxy_audit_new
```

Use a new directory for each run; the CLI refuses to replace an existing one.
The default populated-group threshold is 1,000 records. Single-country
nesting is not certified for a category with any missing country values.
