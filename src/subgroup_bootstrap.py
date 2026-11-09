"""Slide 13 check: the corrected wild cluster bootstrap within each subgroup.

Exploratory, 2026-11-09. Reuses `src.wild_cluster.run_spec` on the same subgroups
as `src.subgroup_inference` (period, loan size, gender, Asia and Africa). It tests
the same terms and bounds, BH-adjusted within each subgroup x outcome family of nine
terms. Nothing is adjusted across the subgroups; patterns found here stay hypotheses.
Asia has 12 countries, so its bootstrap is itself approximate.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.feature_sensitivity import RICH_CATEGORICAL_CONTROLS
from src.subgroup_inference import MIN_CLUSTERS, SUBGROUPS
from src.wild_cluster import BOUNDS, run_spec


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--frame", type=Path, default=Path("reports/inference_private/review_frame.pkl"))
    parser.add_argument("--output", type=Path, default=Path("reports/subgroup_bootstrap"))
    parser.add_argument("--draws", type=int, default=9999)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)
    frame = pd.read_pickle(args.frame)
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / "subgroup_bootstrap.json"
    out = {"generated_at": datetime.now(timezone.utc).isoformat(), "draws": args.draws,
           "method": "WCR bootstrap with controls refitted, Webb weights",
           "bounds": BOUNDS, "results": []}
    for spec, extra in (("programme_adjusted", ["programme_proxy"]), ("expanded", [])):
        for column, levels in SUBGROUPS.items():
            for level in levels or sorted(frame[column].dropna().unique()):
                subset = frame.loc[frame[column] == level]
                clusters = subset["country_name"].nunique()
                if clusters < MIN_CLUSTERS:
                    continue
                controls = [c for c in RICH_CATEGORICAL_CONTROLS + extra if subset[c].nunique() > 1]
                for outcome in BOUNDS:
                    print(f"{spec} {column}={level} {outcome}: {len(subset):,} rows, {clusters} countries", flush=True)
                    result = run_spec(subset, outcome, controls, args.draws, args.seed)
                    out["results"].append({"specification": spec, "group": column, "level": str(level), **result})
                    path.write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
