"""Gap H: does the listing-time forecast pick out the slowest-funding loans?

Exploratory extension, 2026-11-08, for the deck's Predict -> Prioritise -> Test
framing. No model is refitted. Reads the November benchmark's saved private
predictions (expanding windows, test years 2021-2025) and asks a triage
question: if a team could review only the top 10% or 20% of new listings,
how many of the year's slowest 20% would it catch?

* Target: funding duration at or above the 80th percentile of its test year.
* Duration models flag the longest predicted durations; 24-hour models flag
  the lowest predicted probability of funding within 24 hours.
* Precision = share of flagged loans in the slowest 20%; recall = share of the
  slowest 20% that were flagged; lift = precision / 0.20 (random flagging).
* Country robustness re-ranks and re-defines the target inside each of the
  ten largest countries, so it measures ranking within a country rather than
  country base rates.
* Month-block bootstrap (1,000 draws) for the text-minus-structure difference
  in precision at the top 10%.

Population: eventually completed loans only. Unfunded or expired listings are
absent from the data, so this is not a test on all listings, and the
August 2024-2025 holdout predictions were not saved and are not included.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PREDICTIONS = Path("reports/text_benchmark_20261102/private")
CACHE = Path("reports/text_benchmark_private/features.pkl")
OUTPUT = Path("reports/triage_value/triage_value.json")
MODELS = {  # (family, structure-only arm, structure + text arm)
    "linear": ("linear__S", "linear__S_M_L_R"),
    "tree": ("histogram_boosting__S", "histogram_boosting__S_M_L"),
}
SHARES = (0.10, 0.20)
TARGET_SHARE = 0.20


def flag_top(score: np.ndarray, share: float) -> np.ndarray:
    """Flag the `share` of rows with the highest score (stable, deterministic)."""
    k = int(round(share * len(score)))
    order = np.argsort(-score, kind="stable")
    flags = np.zeros(len(score), dtype=bool)
    flags[order[:k]] = True
    return flags


def slow_target(days: np.ndarray) -> np.ndarray:
    return days >= np.quantile(days, 1 - TARGET_SHARE)


def triage_metrics(score, target, share) -> dict:
    flags = flag_top(score, share)
    hits = int((flags & target).sum())
    precision = hits / max(int(flags.sum()), 1)
    base = float(target.mean())
    return {"flagged": int(flags.sum()), "precision": precision,
            "recall": hits / max(int(target.sum()), 1), "lift": precision / base,
            "target_rate": base}


def calibration_deciles(y, p) -> list[dict]:
    edges = np.quantile(p, np.linspace(0, 1, 11))
    codes = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, 9)
    return [{"decile": i + 1, "rows": int((codes == i).sum()),
             "mean_predicted": float(p[codes == i].mean()),
             "observed": float(y[codes == i].mean())} for i in range(10)]


def month_bootstrap(diff_hits_base, diff_hits_text, flagged_base, flagged_text, months,
                    draws=1000, seed=42):
    frame = pd.DataFrame({"m": months, "hb": diff_hits_base, "ht": diff_hits_text,
                          "fb": flagged_base, "ft": flagged_text}).groupby("m").sum()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(frame), size=(draws, len(frame)))
    v = frame.to_numpy()
    s = v[idx].sum(axis=1)
    diff = s[:, 1] / s[:, 3] - s[:, 0] / s[:, 2]
    return np.quantile(diff, [0.025, 0.975]).tolist()


def scores_for(z, key):
    return {"duration": z[f"{key}__days"], "24h": -z[f"{key}__probability"]}


def main() -> int:
    cache = pd.read_pickle(CACHE)[["country_iso", "fundraisingDate"]]
    out = {"generated_at": datetime.now(timezone.utc).isoformat(),
           "source": str(PREDICTIONS), "target": "slowest 20% of funding duration per test year",
           "population": "eventually completed loans only (no unfunded or expired listings); "
                         "retrospective expanding-window evaluation; August holdout not included",
           "years": []}
    for path in sorted(PREDICTIONS.glob("predictions-*.npz")):
        year = int(path.stem.split("-")[1])
        z = np.load(path)
        rows = cache.iloc[z["row_position"]]
        days, y24 = z["y_days"], z["y_binary"].astype(int)
        target = slow_target(days)
        months = rows["fundraisingDate"].dt.strftime("%Y-%m").to_numpy()
        countries = rows["country_iso"].to_numpy()
        top10 = pd.Series(countries).value_counts().index[:10]
        record = {"year": year, "rows": int(len(days)),
                  "slow_threshold_days": float(np.quantile(days, 0.8)), "models": {}}
        for family, (base_key, text_key) in MODELS.items():
            for outcome in ("duration", "24h"):
                entry = {}
                for label, key in (("structure", base_key), ("structure_text", text_key)):
                    score = scores_for(z, key)[outcome]
                    entry[label] = {f"top_{int(s * 100)}": triage_metrics(score, target, s)
                                    for s in SHARES}
                    precisions = []
                    for c in top10:
                        mask = countries == c
                        precisions.append(triage_metrics(score[mask], slow_target(days[mask]),
                                                         0.10)["precision"])
                    entry[label]["top10_countries_within_country_precision_top_10"] = {
                        "median": float(np.median(precisions)), "min": float(min(precisions)),
                        "max": float(max(precisions)),
                        "by_country": dict(zip(map(str, top10), map(float, precisions)))}
                    if outcome == "24h":
                        entry[label]["calibration_deciles"] = calibration_deciles(
                            y24, z[f"{key}__probability"])
                fb = flag_top(scores_for(z, base_key)[outcome], 0.10)
                ft = flag_top(scores_for(z, text_key)[outcome], 0.10)
                entry["text_minus_structure_precision_top_10"] = {
                    "difference": entry["structure_text"]["top_10"]["precision"]
                    - entry["structure"]["top_10"]["precision"],
                    "month_block_95": month_bootstrap(fb & target, ft & target, fb, ft, months)}
                record["models"][f"{family}/{outcome}"] = entry
        out["years"].append(record)
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(out, indent=1))
        for name, e in record["models"].items():
            s, t = e["structure"]["top_10"], e["structure_text"]["top_10"]
            print(f"{year} {name}: P@10 {s['precision']:.3f} -> {t['precision']:.3f} "
                  f"(lift {s['lift']:.2f} -> {t['lift']:.2f}); R@20 "
                  f"{e['structure']['top_20']['recall']:.3f} -> {e['structure_text']['top_20']['recall']:.3f}",
                  flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
