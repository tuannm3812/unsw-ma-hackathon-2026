"""For whom and when: the October specification refitted within subgroups.

Exploratory extension, 2026-11-08. The research question asks which narrative
choices are linked to faster funding "for whom and when". The August
interactions mostly lost significance under country clustering, and the
October and equivalence layers report only pooled coefficients. This module
refits the October programme-adjusted specification (rich controls plus the
unvalidated programme-text proxy, country clusters; `--spec expanded` drops
the proxy) separately within each period, loan-size band, borrower gender
group and the two large Kiva regions, then applies the same TOST screen (bound +/-0.05 log(1 + days) per
mention per 100 words, +/-1 pp for the 24-hour outcome; t(G - 1); BH within
each subgroup x outcome family of nine terms).

Separate fits let every control coefficient differ by subgroup. They are not a
formal heterogeneity test: subgroups share countries, so their estimates are
not independent. Subgroups were chosen from the research question before any
subgroup estimate was seen; the bounds were not (see `src.equivalence`).
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from scipy import stats

from src.equivalence import BOUNDS, SENTIMENT_FEATURE, SENTIMENT_SCALE, RATE_FEATURES, bh_adjust
from src.feature_sensitivity import (
    EXPANDED_NARRATIVE_FEATURES, NARRATIVE_FEATURE_FAMILIES, RICH_CATEGORICAL_CONTROLS,
    RICH_NUMERIC_CONTROLS, fit_clustered_partial_regression,
)

SUBGROUPS = {
    "analysis_period": None,             # all three periods
    "loan_size_band": None,              # small, medium, large
    "gender_classification": ["female", "male"],
    "region": ["Asia", "Africa"],
}
MIN_CLUSTERS = 8


def screen_table(table: pd.DataFrame, outcome: str, n_clusters: int) -> list[dict]:
    df = n_clusters - 1
    crit = stats.t.ppf(0.95, df)
    bound = BOUNDS[outcome]["primary"]
    rows = []
    for _, r in table.iterrows():
        if r["feature"] in RATE_FEATURES:
            scale = 1.0
        elif r["feature"] == SENTIMENT_FEATURE:
            scale = SENTIMENT_SCALE
        else:
            continue
        est, se = r["coefficient"] * scale, r["standard_error"] * scale
        p_lo = stats.t.sf((est + bound) / se, df)
        p_hi = stats.t.cdf((est - bound) / se, df)
        rows.append({"feature": r["feature"], "estimate": float(est), "se": float(se),
                     "ci90": [float(est - crit * se), float(est + crit * se)],
                     "p_zero": float(r["p_value"]), "p_tost": float(max(p_lo, p_hi))})
    for row, q in zip(rows, bh_adjust([x["p_tost"] for x in rows])):
        row["p_tost_bh"], row["equivalent"] = q, q < 0.05
    for row, q in zip(rows, bh_adjust([x["p_zero"] for x in rows])):
        row["p_zero_bh"] = q
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--frame", type=Path, default=Path("reports/inference_private/review_frame.pkl"))
    parser.add_argument("--output", type=Path, default=Path("reports/subgroup_inference"))
    parser.add_argument("--spec", choices=["programme_adjusted", "expanded"],
                        default="programme_adjusted")
    args = parser.parse_args(argv)
    extra = ["programme_proxy"] if args.spec == "programme_adjusted" else []
    frame = pd.read_pickle(args.frame)
    args.output.mkdir(parents=True, exist_ok=True)
    out = {"generated_at": datetime.now(timezone.utc).isoformat(),
           "specification": f"October {args.spec}, refitted within subgroup",
           "bounds": {k: v["primary"] for k, v in BOUNDS.items()}, "results": []}
    for column, levels in SUBGROUPS.items():
        levels = levels or sorted(frame[column].dropna().unique())
        for level in levels:
            subset = frame.loc[frame[column] == level]
            n_clusters = subset["country_name"].nunique()
            if n_clusters < MIN_CLUSTERS:
                print(f"skip {column}={level}: {n_clusters} clusters", flush=True)
                continue
            # A control that is constant inside the subgroup is dropped from it.
            controls = [c for c in RICH_CATEGORICAL_CONTROLS + extra if subset[c].nunique() > 1]
            for outcome in BOUNDS:
                print(f"{column}={level} / {outcome}: {len(subset):,} rows, "
                      f"{n_clusters} countries", flush=True)
                fit = fit_clustered_partial_regression(
                    subset, outcome=outcome, narrative_features=EXPANDED_NARRATIVE_FEATURES,
                    numeric_controls=RICH_NUMERIC_CONTROLS, categorical_controls=controls,
                    cluster_col="country_name", feature_families=NARRATIVE_FEATURE_FAMILIES)
                out["results"].append({
                    "group": column, "level": str(level), "outcome": outcome,
                    "rows": int(fit["n_rows"]), "clusters": int(fit["n_clusters"]),
                    "dropped": fit["dropped_narrative_features"],
                    "terms": screen_table(fit["coefficients"], outcome, fit["n_clusters"])})
                (args.output / f"subgroup_{args.spec}.json").write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
