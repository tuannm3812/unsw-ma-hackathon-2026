"""Share of eligible loans by country, sorted (aggregates only; country codes, no rows)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.evidence_sources import clusters_for_share, effective_clusters
from src.programme_audit import file_sha256


def country_shares(frame: pd.DataFrame) -> dict:
    eligible = frame.loc[frame['valid_completed_outcome'].fillna(False).astype(bool)]
    counts = eligible['country_iso'].value_counts()
    shares = counts / counts.sum()
    return {'countries': int(len(counts)), 'records': int(counts.sum()),
            'top10_share': float(shares.head(10).sum()),
            'countries_for_80pct': clusters_for_share(counts),
            'effective_countries': effective_clusters(counts),
            'shares': [{'country': str(k), 'share': float(v)} for k, v in shares.items()]}


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
