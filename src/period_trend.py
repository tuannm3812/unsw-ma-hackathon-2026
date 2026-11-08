"""Yearly share of loans fully funded within 24 hours, 2016-2025 (descriptive aggregates only).

Reads the private deterministic-feature cache (hash verified). Population: eligible
completed durations, as in the August audit. No model; nothing here is causal.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.programme_audit import file_sha256


LONG_WAIT_DAYS = 14


def yearly_share(frame: pd.DataFrame) -> list[dict]:
    """Return per-year record counts, the share funded within 24 hours and, when funding time is
    available, the median wait and the share waiting more than two weeks."""
    eligible = frame.loc[frame['valid_completed_outcome'].fillna(False).astype(bool)]
    grouped = eligible.groupby('fundraising_year')['funded_within_24h'].agg(['size', 'sum'])
    rows = [{'year': int(year), 'records': int(row['size']), 'funded_within_24h': int(row['sum']),
             'share_within_24h': float(row['sum'] / row['size'])} for year, row in grouped.iterrows()]
    if 'funding_speed_days' in eligible:
        days = eligible.groupby('fundraising_year')['funding_speed_days']
        median, long_wait = days.median(), days.apply(lambda d: float((d > LONG_WAIT_DAYS).mean()))
        long_count = days.apply(lambda d: int((d > LONG_WAIT_DAYS).sum()))
        for row in rows:
            row.update({'median_days': float(median[row['year']]),
                        'share_over_14_days': float(long_wait[row['year']]),
                        'records_over_14_days': int(long_count[row['year']])})
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--feature-cache', type=Path, default=Path('reports/text_benchmark_private/features.pkl'))
    parser.add_argument('--output', type=Path, default=Path('reports/period_trend/yearly_same_day_share.json'))
    args = parser.parse_args(argv)
    metadata = json.loads(args.feature_cache.with_suffix('.metadata.json').read_text())
    if file_sha256(args.feature_cache) != metadata['cache_sha256']:
        raise ValueError('feature cache does not match its metadata')
    rows = yearly_share(pd.read_pickle(args.feature_cache))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({'schema_version': 'yearly_same_day_share.v1',
                                       'population': 'eligible completed durations; descriptive',
                                       'source': 'reports/text_benchmark_private/features.pkl',
                                       'years': rows}, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
