"""Share of eligible loans by country, sorted (aggregates only; country codes, no rows)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.evidence_sources import clusters_for_share, effective_clusters
from src.programme_audit import file_sha256

LONG_WAIT_DAYS = 14


def country_shares(frame: pd.DataFrame) -> dict:
    eligible = frame.loc[frame['valid_completed_outcome'].fillna(False).astype(bool)]
    counts = eligible['country_iso'].value_counts()
    shares = counts / counts.sum()
    same_day = eligible.groupby('country_iso')['funded_within_24h'].mean()
    # Kiva's own region field; each country must sit in exactly one region.
    regions = eligible.groupby('country_iso')['region'].agg(lambda r: r.dropna().unique().tolist())
    ambiguous = [k for k, values in regions.items() if len(values) != 1]
    if ambiguous:
        raise ValueError(f'countries without exactly one region: {ambiguous}')
    region_counts = eligible['region'].value_counts()
    result = {'countries': int(len(counts)), 'records': int(counts.sum()),
            'top10_share': float(shares.head(10).sum()),
            'countries_for_80pct': clusters_for_share(counts),
            'effective_countries': effective_clusters(counts),
            'region_shares': {str(k): float(v / counts.sum()) for k, v in region_counts.items()},
            'shares': [{'country': str(k), 'region': str(regions[k][0]), 'loans': int(counts[k]), 'share': float(v),
                        'same_day_share': float(same_day[k])} for k, v in shares.items()]}
    if 'funding_speed_days' in eligible:
        # Long waits: more than two weeks from listing to full funding.
        days = eligible.groupby('country_iso')['funding_speed_days']
        long_counts = days.apply(lambda d: int((d > LONG_WAIT_DAYS).sum()))
        total_long = int(long_counts.sum())
        for row in result['shares']:
            k = row['country']
            row.update({'median_days': float(days.median()[k]), 'records_over_14_days': int(long_counts[k]),
                        'share_over_14_days': float(long_counts[k] / counts[k]),
                        'share_of_all_long_waits': float(long_counts[k] / total_long)})
        result['records_over_14_days'] = total_long
        result['top10_share_of_long_waits'] = float(sum(r['share_of_all_long_waits'] for r in result['shares'][:10]))
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--feature-cache', type=Path, default=Path('reports/text_benchmark_private/features.pkl'))
    parser.add_argument('--output', type=Path, default=Path('reports/evidence_sources/country_shares.json'))
    args = parser.parse_args(argv)
    meta = json.loads(args.feature_cache.with_suffix('.metadata.json').read_text())
    if file_sha256(args.feature_cache) != meta['cache_sha256']:
        raise ValueError('feature cache does not match its metadata')
    args.output.write_text(json.dumps(country_shares(pd.read_pickle(args.feature_cache)), indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
