"""Exploratory equivalence (TOST) screen for saved narrative coefficients.

Reads the reviewed October country-clustered coefficient tables and asks, for
each narrative term, whether its 90% interval lies entirely inside a stated
practical-effect bound. This is the two one-sided tests (TOST) procedure at
alpha = 0.05 per side.

Scope and limits (also written into every report this module produces):

* The bounds were chosen on 2026-11-08, after the estimates were already
  known. The screen is therefore exploratory; a confirmatory version needs
  bounds fixed before looking at the data.
* Equivalence is judged per additional mention per 100 words (or per 0.5 of
  the VADER compound score). It says nothing about other edit sizes.
* Associations are observational. "Inside the bound" means the data rule out
  associations larger than the bound under this specification, not that
  editing has no effect.
* Uses only the Python standard library so it runs without the analysis
  environment; the Student t distribution is computed numerically.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

RATE_FEATURES = (
    "family_mentions_per_100_words",
    "basic_needs_mentions_per_100_words",
    "business_mentions_per_100_words",
    "agency_mentions_per_100_words",
    "gratitude_mentions_per_100_words",
    "urgency_mentions_per_100_words",
    "first_person_mentions_per_100_words",
    "third_person_mentions_per_100_words",
)
SENTIMENT_FEATURE = "desc_sentiment_compound"
SENTIMENT_SCALE = 0.5  # judge a 0.5 change in the compound score

# Primary bounds and sensitivity bounds, in outcome units per edit unit.
BOUNDS = {
    "log_funding_speed": {"primary": 0.05, "sensitivity": (0.02, 0.10)},
    "funded_within_24h": {"primary": 0.01, "sensitivity": (0.005, 0.02)},
}


def _t_pdf(x: float, df: int) -> float:
    log_c = math.lgamma((df + 1) / 2) - math.lgamma(df / 2) - 0.5 * math.log(df * math.pi)
    return math.exp(log_c - (df + 1) / 2 * math.log1p(x * x / df))


def t_cdf(x: float, df: int, steps: int = 4000) -> float:
    """Student t CDF by Simpson integration from 0; accurate to ~1e-10 for |x| < 40."""
    if df <= 0:
        raise ValueError("df must be positive")
    if x == 0:
        return 0.5
    a, b = 0.0, abs(x)
    h = (b - a) / steps
    total = _t_pdf(a, df) + _t_pdf(b, df)
    for i in range(1, steps):
        total += (4 if i % 2 else 2) * _t_pdf(a + i * h, df)
    area = total * h / 3
    return 0.5 + area if x > 0 else 0.5 - area


def t_ppf(p: float, df: int) -> float:
    """Inverse t CDF by bisection."""
    lo, hi = -60.0, 60.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


@dataclass
class TostResult:
    specification: str
    outcome: str
    feature: str
    edit_unit: str
    estimate: float
    standard_error: float
    ci90_low: float
    ci90_high: float
    bound: float
    p_lower: float
    p_upper: float
    p_tost: float
    p_tost_bh: float
    equivalent: bool
    equivalent_at_sensitivity_bounds: dict


def tost(estimate: float, se: float, bound: float, df: int) -> tuple[float, float, float]:
    """Return (p_lower, p_upper, p_tost) for H0: |beta| >= bound."""
    if se <= 0 or bound <= 0:
        raise ValueError("standard error and bound must be positive")
    p_lower = 1 - t_cdf((estimate + bound) / se, df)  # H0: beta <= -bound
    p_upper = t_cdf((estimate - bound) / se, df)      # H0: beta >= +bound
    p_lower, p_upper = (min(1.0, max(0.0, v)) for v in (p_lower, p_upper))
    return p_lower, p_upper, max(p_lower, p_upper)


def bh_adjust(pvalues: list[float]) -> list[float]:
    """Benjamini-Hochberg adjusted p-values, returned in input order."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        running = min(running, pvalues[i] * m / rank)
        adjusted[i] = running
    return adjusted


def screen(coef_csv: Path, specification: str, n_clusters: int) -> list[TostResult]:
    df = n_clusters - 1
    crit = t_ppf(0.95, df)
    results: list[TostResult] = []
    with coef_csv.open(newline="") as handle:
        for row in csv.DictReader(handle):
            feature, outcome = row["feature"], row["outcome"]
            if feature in RATE_FEATURES:
                scale, unit = 1.0, "+1 mention per 100 words"
            elif feature == SENTIMENT_FEATURE:
                scale, unit = SENTIMENT_SCALE, "+0.5 VADER compound"
            else:
                continue
            est = float(row["coefficient"]) * scale
            se = float(row["standard_error"]) * scale
            bounds = BOUNDS[outcome]
            p_lo, p_hi, p = tost(est, se, bounds["primary"], df)
            sens = {str(b): tost(est, se, b, df)[2] < 0.05 for b in bounds["sensitivity"]}
            results.append(TostResult(
                specification, outcome, feature, unit, est, se,
                est - crit * se, est + crit * se, bounds["primary"],
                p_lo, p_hi, p, float("nan"), False, sens,
            ))
    # Multiplicity family: one specification x one outcome (nine terms).
    for outcome in BOUNDS:
        family = [r for r in results if r.outcome == outcome]
        for r, q in zip(family, bh_adjust([r.p_tost for r in family])):
            r.p_tost_bh = q
            r.equivalent = q < 0.05
    return results


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reviewed-dir", type=Path,
                        default=Path("reports/expanded_feature_sensitivity_reviewed"))
    parser.add_argument("--n-clusters", type=int, default=48)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    rows: list[TostResult] = []
    for spec in ("expanded", "programme_adjusted"):
        rows += screen(args.reviewed_dir / spec / "narrative_coefficients.csv", spec, args.n_clusters)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_by": "src.equivalence",
        "inputs": str(args.reviewed_dir),
        "n_clusters": args.n_clusters,
        "df": args.n_clusters - 1,
        "alpha_per_side": 0.05,
        "bounds": BOUNDS,
        "bounds_chosen": "2026-11-08, after estimates were known (exploratory)",
        "multiplicity": "BH within each specification x outcome family of nine terms; "
                        "'equivalent' uses the BH-adjusted TOST p at the primary bound; "
                        "sensitivity-bound flags are unadjusted",
        "results": [asdict(r) for r in rows],
    }
    (args.output_dir / "equivalence_screen.json").write_text(json.dumps(payload, indent=2))
    fields = [f for f in asdict(rows[0]) if f != "equivalent_at_sensitivity_bounds"]
    with (args.output_dir / "equivalence_screen.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields + ["equivalent_at_sensitivity_bounds"])
        for r in rows:
            d = asdict(r)
            writer.writerow([d[f] for f in fields] + [json.dumps(d["equivalent_at_sensitivity_bounds"])])


if __name__ == "__main__":
    main()
