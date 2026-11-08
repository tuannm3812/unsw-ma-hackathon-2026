"""Read the equivalence screen against three bounds and translate the primary bound into hours.

Reads `reports/equivalence_screen_reviewed/equivalence_screen.csv` and
`feature_distribution.json`, and writes `reports/evidence_sources/bound_ladder.json` for
slide 9:

- For each term and specification (duration outcome), the tightest bound at which the
  screen calls it equivalent. The ±0.05 verdict is the BH-adjusted primary decision; the
  ±0.02 and ±0.10 verdicts are the screen's unadjusted sensitivity flags.
- The primary ±0.05 bound on log(1 + days) at the median funding duration, in hours:
  (1 + median) × (exp(±bound) − 1) × 24.
- The share of eligible records with no mention of each term (for sentiment, a score of
  exactly zero).

Exploratory: the bounds were set after the estimates. Aggregates only.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / 'reports/equivalence_screen_reviewed'
OUTPUT = ROOT / 'reports/evidence_sources/bound_ladder.json'
# Median funding duration of eligible records (claims register, "Funding duration").
MEDIAN_DAYS = 2.85
PRIMARY = 0.05
BOUNDS = (0.02, 0.05, 0.10)
OUTCOME = 'log_funding_speed'


def term_name(feature: str) -> str:
    return feature.replace('_mentions_per_100_words', '').replace('desc_sentiment_compound', 'sentiment')


def tightest_bound(primary: bool, sensitivity: dict[str, bool]) -> float | None:
    """Smallest of ±0.02, ±0.05 and ±0.10 at which the term is called equivalent, else None."""
    held = {0.02: sensitivity['0.02'], PRIMARY: primary, 0.10: sensitivity['0.1']}
    return next((bound for bound in BOUNDS if held[bound]), None)


def hours_at_median(bound: float, median_days: float = MEDIAN_DAYS) -> tuple[float, float]:
    """Hours of funding time a ±bound on log(1 + days) spans at the median: (shorter, longer)."""
    base = 1 + median_days
    return base * (1 - math.exp(-bound)) * 24, base * (math.exp(bound) - 1) * 24


def ladder(rows: list[dict]) -> dict:
    result: dict[str, dict] = {}
    for row in rows:
        if row['outcome'] != OUTCOME:
            continue
        flags = json.loads(row['equivalent_at_sensitivity_bounds'])
        bound = tightest_bound(row['equivalent'] == 'True', flags)
        result.setdefault(row['specification'], {})[term_name(row['feature'])] = bound
    return result


def build(screen: Path = SCREEN) -> dict:
    with (screen / 'equivalence_screen.csv').open() as handle:
        rows = list(csv.DictReader(handle))
    features = json.loads((screen / 'feature_distribution.json').read_text())['features']
    shorter, longer = hours_at_median(PRIMARY)
    tight = ladder(rows)
    counts = {spec: {str(bound): sum(1 for b in terms.values() if b is not None and b <= bound) for bound in BOUNDS}
              for spec, terms in tight.items()}
    return {
        'population': 'eligible completed durations; duration outcome; aggregates only',
        'rule': '±0.05 is the BH-adjusted primary decision; ±0.02 and ±0.10 are unadjusted sensitivity flags',
        'median_days': MEDIAN_DAYS,
        'primary_bound_hours': {'shorter': round(shorter, 2), 'longer': round(longer, 2)},
        'bound_percent_of_one_plus_days': {str(b): round((math.exp(b) - 1) * 100, 2) for b in BOUNDS},
        'tightest_bound': tight,
        'terms_equivalent_by_bound': counts,
        'share_no_mention': {term_name(name): round(stats['share_zero'], 4) for name, stats in features.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
