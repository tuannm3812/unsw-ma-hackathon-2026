"""Compare the slow-funding flag with a simple historical lookup, for the deck.

Reads `reports/experiments_2026_11_08/triage_lookup_baseline.json` and writes
`reports/evidence_sources/triage_lookup_summary.json`: lift when flagging the top 10% against the
slowest 20% of each test year, and median within-country precision, for the training-only lookup
by country, sector and calendar month and for the boosted tree on loan details.

Retrospective, on eventually completed loans only. Intervals are not read here: the triage
month-block bootstrap is being rerun.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'reports/experiments_2026_11_08/triage_lookup_baseline.json'
OUTPUT = ROOT / 'reports/evidence_sources/triage_lookup_summary.json'


def summarise(data: dict) -> dict:
    """Per-year lift and within-country precision for the lookup and the tree, with ranges."""
    years = {}
    for row in data['years']:
        lookup, tree = row['models']['lookup_B1'], row['models']['tree_structure']
        years[str(row['year'])] = {'lookup_lift': lookup['top_10']['lift'], 'tree_lift': tree['top_10']['lift'],
                                   'lookup_within': lookup['within_country_precision_top_10']['median'],
                                   'tree_within': tree['within_country_precision_top_10']['median']}
    span = lambda key: [min(y[key] for y in years.values()), max(y[key] for y in years.values())]
    return {'years': years, 'lookup_lift_range': span('lookup_lift'), 'tree_lift_range': span('tree_lift'),
            'lookup_within_range': span('lookup_within'), 'tree_within_range': span('tree_within'),
            'tree_beats_lift_years': sum(y['tree_lift'] > y['lookup_lift'] for y in years.values()),
            'tree_beats_within_years': sum(y['tree_within'] > y['lookup_within'] for y in years.values()),
            'years_compared': len(years)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(summarise(json.loads(SOURCE.read_text())), indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
