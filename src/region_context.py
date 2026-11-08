"""Context for slide 10's regional family-framing slopes: how many countries stand behind each region.

Reads `reports/evidence_sources/country_shares.json` (Kiva's `region` field per country) and
writes `reports/evidence_sources/region_context.json`:

- countries and eligible loans per region, and each country's share of its region's loans;
- the saved within-region family slopes (primary run, `docs/2_evidence_and_corrections.md`)
  expressed as a percentage change in (1 + days): 100 × (exp(slope) − 1).

Descriptive; aggregates only.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARES = ROOT / 'reports/evidence_sources/country_shares.json'
OUTPUT = ROOT / 'reports/evidence_sources/region_context.json'
# Saved average duration slopes, log(1 + days) per extra family mention per 100 words.
SLOPES = {'Middle East': -0.0729, 'Central America': -0.0742}


def percent_change(log_points: float) -> float:
    """Percentage change in (1 + days) for a change in log(1 + days)."""
    return 100 * (math.exp(log_points) - 1)


def region_context(shares: list[dict]) -> dict:
    regions: dict[str, list[dict]] = defaultdict(list)
    for row in shares:
        regions[row['region']].append(row)
    result = {}
    for region, rows in sorted(regions.items(), key=lambda item: -len(item[1])):
        loans = sum(row['loans'] for row in rows)
        result[region] = {
            'countries': len(rows),
            'loans': loans,
            'country_shares': [{'country': row['country'], 'loans': row['loans'],
                                'share_of_region': row['loans'] / loans}
                               for row in sorted(rows, key=lambda r: -r['loans'])],
        }
    return result


def build(shares_path: Path = SHARES) -> dict:
    shares = json.loads(shares_path.read_text())['shares']
    return {'population': 'eligible completed durations; Kiva region field; aggregates only',
            'regions': region_context(shares),
            'family_slope_percent': {region: round(percent_change(slope), 2) for region, slope in SLOPES.items()}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
