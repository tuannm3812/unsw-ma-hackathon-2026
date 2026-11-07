"""Aggregate feature distributions that convert the equivalence bounds to realistic edit sizes.

Reads the private deterministic-feature cache and writes aggregates only: no rows,
no text. Population: the eligible completed durations used by the October fits and
the equivalence screen.

The equivalence screen judges a fixed edit unit (+1 mention per 100 words, +0.5
VADER compound). This module expresses the same coefficients per one population
standard deviation, so a reader can see how large that edit unit is against the
variation that descriptions actually show. A standard deviation is a scale for
comparison; it is not an estimate of what a feasible rewrite would change.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.equivalence import BOUNDS, RATE_FEATURES, SENTIMENT_FEATURE, SENTIMENT_SCALE
from src.programme_audit import file_sha256

FEATURES = (*RATE_FEATURES, SENTIMENT_FEATURE)


def summarise(values) -> dict:
    """Return mean, SD (ddof=1), share of zeros and 90th percentile, ignoring missing."""
    array = np.asarray(values, dtype=float)
    observed = array[~np.isnan(array)]
    if observed.size < 2:
        raise ValueError('at least two observed values are required')
    return {'rows': int(array.size), 'observed_rows': int(observed.size),
            'mean': float(observed.mean()), 'sd': float(observed.std(ddof=1)),
            'share_zero': float(np.mean(observed == 0)),
            'p90': float(np.quantile(observed, .9)),
            'mean_nonzero': float(observed[observed != 0].mean()) if (observed != 0).any() else None}


def edit_unit(feature: str) -> float:
    """Return the size of the screen's edit unit in feature units."""
    return SENTIMENT_SCALE if feature == SENTIMENT_FEATURE else 1.0


def per_sd(row: dict, stats: dict) -> dict:
    """Rescale a screen row from its edit unit to one population SD of the feature.

    Screen rows are already per edit unit, so the multiplier is SD / edit unit.
    ``bound_equivalent_per_sd`` is the primary bound carried to the same scale: what a
    one-SD change would be associated with at exactly the bound per edit unit.
    ``inside_primary_bound_per_sd`` instead holds the unscaled bound against the rescaled
    interval, so it asks whether a one-SD change stays inside the primary bound.
    """
    scale = stats['sd'] / edit_unit(row['feature'])
    low, high = float(row['ci90_low']) * scale, float(row['ci90_high']) * scale
    bound = BOUNDS[row['outcome']]['primary']
    return {'specification': row['specification'], 'outcome': row['outcome'],
            'feature': row['feature'], 'sd_per_edit_unit': scale,
            'estimate_per_sd': float(row['estimate']) * scale,
            'ci90_low_per_sd': low, 'ci90_high_per_sd': high,
            'primary_bound': bound, 'bound_equivalent_per_sd': bound * scale,
            'inside_primary_bound_per_sd': bool(-bound < low and high < bound)}


def run(cache: Path, screen_csv: Path, output: Path) -> dict:
    metadata = json.loads(cache.with_suffix('.metadata.json').read_text())
    cache_sha = file_sha256(cache)
    if cache_sha != metadata['cache_sha256']:
        raise ValueError('feature cache does not match its metadata')
    frame = pd.read_pickle(cache)
    eligible = frame.loc[frame['valid_completed_outcome'].fillna(False).astype(bool)]
    described = eligible.loc[eligible['description_missing'].eq(0)]
    stats = {name: summarise(eligible[name]) for name in FEATURES}
    described_stats = {name: summarise(described[name]) for name in FEATURES}
    with screen_csv.open(newline='') as handle:
        rows = list(csv.DictReader(handle))
    result = {
        'schema_version': 'equivalence_feature_distribution.v1',
        'population': 'eligible completed durations; aggregates only',
        'eligible_rows': len(eligible), 'rows_with_description': len(described),
        'median_words_rows_with_description': float(described['desc_word_count'].median()),
        'feature_cache_sha256': cache_sha,
        'boundary': 'SD is a comparison scale, not a feasible rewrite size. Observational; '
                    'nothing here measures an edit.',
        'features': stats, 'features_rows_with_description': described_stats,
        'per_sd': [per_sd(row, stats[row['feature']]) for row in rows]}
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--feature-cache', type=Path,
                        default=Path('reports/text_benchmark_private/features.pkl'))
    parser.add_argument('--screen', type=Path,
                        default=Path('reports/equivalence_screen_reviewed/equivalence_screen.csv'))
    parser.add_argument('--output', type=Path,
                        default=Path('reports/equivalence_screen_reviewed/feature_distribution.json'))
    args = parser.parse_args(argv)
    run(args.feature_cache, args.screen, args.output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
