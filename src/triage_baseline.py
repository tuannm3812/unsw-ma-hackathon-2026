"""Gap H follow-up: does the flag beat a simple historical lookup, not just chance?

Exploratory, 2026-11-08. Reuses the November benchmark's saved B1 predictions:
a training-only, shrunken median by country x sector x calendar month. Same
target and metrics as `src.triage_value`, duration flags only. B1 has many tied
scores, so ties are broken at random with a fixed seed. Completed loans only.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.triage_value import CACHE, PREDICTIONS, slow_target, triage_metrics

OUTPUT = Path("reports/experiments_2026_11_08/triage_lookup_baseline.json")
MODELS = {"lookup_B1": "baseline__B1__days", "tree_structure": "histogram_boosting__S__days",
          "linear_structure": "linear__S__days"}


def break_ties(score: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Return ranks with ties ordered at random; distinct scores keep their order."""
    order = np.lexsort((rng.random(len(score)), score))
    ranks = np.empty(len(score))
    ranks[order] = np.arange(len(score))
    return ranks


def main() -> int:
    countries = pd.read_pickle(CACHE)["country_iso"]
    rng = np.random.default_rng(42)
    years = []
    for path in sorted(PREDICTIONS.glob("predictions-*.npz")):
        z = np.load(path)
        days, target = z["y_days"], slow_target(z["y_days"])
        country = countries.iloc[z["row_position"]].to_numpy()
        top = pd.Series(country).value_counts().index[:10]
        row = {"year": int(path.stem.split("-")[1]), "rows": int(len(days)), "models": {}}
        for name, key in MODELS.items():
            ranks = break_ties(z[key], rng)
            within = [triage_metrics(ranks[country == c], slow_target(days[country == c]), 0.10)["precision"]
                      for c in top]
            row["models"][name] = {
                "top_10": triage_metrics(ranks, target, 0.10),
                "top_20": triage_metrics(ranks, target, 0.20),
                "within_country_precision_top_10": {
                    "median": float(np.median(within)), "min": float(min(within)),
                    "max": float(max(within))}}
        years.append(row)
        print(row["year"], {k: (round(v["top_10"]["lift"], 2), round(v["within_country_precision_top_10"]["median"], 2))
                            for k, v in row["models"].items()}, flush=True)
    OUTPUT.write_text(json.dumps({
        "target": "slowest 20% of funding duration per test year",
        "lookup": "training-only shrunken median by country x sector x calendar month (benchmark B1)",
        "population": "eventually completed loans only; retrospective", "years": years}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
