"""Exploratory aggregates: where the text gain sits, and why sparse terms stay unresolved.

Two descriptive checks added after the November benchmark and the equivalence screen.
Neither refits a model or changes a saved result.

* ``gain_sources`` reads the reviewed benchmark's saved slices and locates the linear
  S to S+M+L+R MAE gain by country and by exact-template novelty. Groups below the
  benchmark's 200-row floor have no saved MAE, so they are reported as one residual.
* ``described_only_gains`` reads the private benchmark predictions and repeats the gain
  without records that have no description, whose predictions can be extreme.
* ``few_cluster_screen`` repeats the equivalence screen with a t reference set by the
  effective number of countries. This is a heuristic stress test, not a calibrated
  few-cluster method.
* ``term_concentration`` reads the private feature cache and measures how many countries
  supply the records that use a term. A term used in few countries gives clustered
  inference few effective clusters, whatever the row count.

Outputs are aggregates only. Nothing here measures the effect of editing a description.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.equivalence import bh_adjust, t_ppf, tost
from src.programme_audit import file_sha256

TERMS = ('urgency_mentions_per_100_words', 'first_person_mentions_per_100_words',
         'gratitude_mentions_per_100_words', 'agency_mentions_per_100_words',
         'family_mentions_per_100_words', 'third_person_mentions_per_100_words')


def effective_clusters(counts) -> float:
    """Return the inverse Herfindahl index: 1 / sum(share squared)."""
    values = np.asarray(counts, dtype=float)
    if values.sum() <= 0 or (values < 0).any():
        raise ValueError('positive non-negative counts are required')
    share = values / values.sum()
    return float(1 / np.sum(share ** 2))


def clusters_for_share(counts, share: float = .8) -> int:
    """Return how many of the largest clusters are needed to reach ``share``."""
    values = np.sort(np.asarray(counts, dtype=float))[::-1]
    return int(np.searchsorted(np.cumsum(values) / values.sum(), share) + 1)


def slice_gains(baseline: list[dict], candidate: list[dict], dimension: str) -> list[dict]:
    """Pair unsuppressed slices; gain is baseline MAE minus candidate MAE, so positive is better."""
    new = {s['group']: s for s in candidate if s['dimension'] == dimension and not s['suppressed']}
    rows = []
    for base in baseline:
        if base['dimension'] == dimension and not base['suppressed'] and base['group'] in new:
            gain = base['mae_days'] - new[base['group']]['mae_days']
            rows.append({'group': base['group'], 'rows': base['rows'], 'gain_days': gain,
                         'gain_total_days': gain * base['rows']})
    return rows


def leave_one_out(rows: list[dict], total_gain_days: float, total_rows: int) -> list[dict]:
    """Return the mean gain with each group removed, from aggregate totals."""
    return [{'group': r['group'],
             'gain_without': (total_gain_days - r['gain_total_days']) / (total_rows - r['rows'])}
            for r in rows]


def gain_sources(benchmark: dict) -> list[dict]:
    result = []
    for year in sorted({m['year'] for m in benchmark['models']}):
        arms = {m['arm']: m for m in benchmark['models'] if m['year'] == year and m['family'] == 'linear'}
        base, new = arms['S'], arms['S+M+L+R']
        rows, total_rows = base['metrics']['rows'], base['metrics']['rows']
        total = (base['metrics']['mae_days'] - new['metrics']['mae_days']) * rows
        countries = sorted(slice_gains(base['slices'], new['slices'], 'country'),
                           key=lambda r: r['gain_total_days'], reverse=True)
        loo = leave_one_out(countries, total, total_rows)
        positive = sum(r['rows'] for r in countries if r['gain_days'] > 0)
        result.append({
            'year': year, 'gain_days': total / rows, 'rows': rows,
            'countries_with_saved_slice': len(countries),
            'rows_in_saved_slices': sum(r['rows'] for r in countries),
            'countries_with_positive_gain': sum(r['gain_days'] > 0 for r in countries),
            'share_rows_in_positive_countries': positive / rows,
            'largest_country_contributions': [
                {**r, 'share_of_total_gain': r['gain_total_days'] / total} for r in countries[:5]],
            'largest_country_losses': countries[-3:],
            'leave_one_country_out_min': min(x['gain_without'] for x in loo),
            'leave_one_country_out_max': max(x['gain_without'] for x in loo),
            'template_novelty': slice_gains(base['slices'], new['slices'], 'template_signature_novelty'),
            'description_missing': slice_gains(base['slices'], new['slices'], 'description_missing'),
            'duration_band': slice_gains(base['slices'], new['slices'], 'duration_band'),
        })
    return result


def term_concentration(frame: pd.DataFrame) -> dict:
    eligible = frame.loc[frame['valid_completed_outcome'].fillna(False).astype(bool)]
    countries = eligible['country_iso']
    overall = countries.value_counts()
    terms = {}
    for term in TERMS:
        using = eligible[term].fillna(0) > 0
        counts = countries[using].value_counts()
        rate = (counts / overall).dropna()
        terms[term] = {
            'records_using_term': int(using.sum()), 'countries_using_term': int(len(counts)),
            'effective_countries': effective_clusters(counts),
            'countries_for_80pct_of_users': clusters_for_share(counts),
            'top_country_share': float(counts.iloc[0] / counts.sum()),
            'top_five_countries': {str(k): float(v / counts.sum()) for k, v in counts.head(5).items()},
            'median_country_use_rate': float(rate.median())}
    return {'population': 'eligible completed durations', 'countries': int(len(overall)),
            'effective_countries_all_records': effective_clusters(overall),
            'countries_for_80pct_of_records': clusters_for_share(overall), 'terms': terms}


def described_only_gains(predictions_dir: Path, frame: pd.DataFrame) -> list[dict]:
    """Compare the linear MAE gain on all records with records that have a description."""
    missing = frame['description_missing'].to_numpy() == 1
    result = []
    for path in sorted(predictions_dir.glob('predictions-*.npz')):
        data = np.load(path)
        y, rows = data['y_days'], data['row_position']
        base, text = data['linear__S__days'], data['linear__S_M_L_R__days']
        gain = np.abs(base - y) - np.abs(text - y)
        none = missing[rows]
        result.append({'year': int(path.stem[-4:]), 'rows': int(len(y)), 'rows_no_description': int(none.sum()),
                       'gain_all_records': float(gain.mean()), 'gain_described_records': float(gain[~none].mean()),
                       'largest_prediction_no_description': float(text[none].max()),
                       'largest_prediction_all': float(text.max())})
    return result


def few_cluster_screen(rows: list[dict], df: int) -> list[dict]:
    """Repeat the TOST on saved estimates with ``df``, BH-adjusting within each family."""
    families: dict[tuple, list[dict]] = {}
    for row in rows:
        families.setdefault((row['specification'], row['outcome']), []).append(row)
    critical = t_ppf(.95, df)
    result = []
    for (specification, outcome), members in families.items():
        tests = [tost(float(r['estimate']), float(r['standard_error']), float(r['bound']), df)
                 for r in members]
        adjusted = bh_adjust([t[2] for t in tests])
        for row, p_value in zip(members, adjusted):
            estimate, error = float(row['estimate']), float(row['standard_error'])
            result.append({'specification': specification, 'outcome': outcome, 'feature': row['feature'],
                           'ci90_low': estimate - critical * error, 'ci90_high': estimate + critical * error,
                           'p_tost_bh': p_value, 'bounded': p_value < .05,
                           'bounded_at_t47': row['equivalent'] == 'True'})
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', type=Path, default=Path('reports/text_benchmark_reviewed/benchmark.json'))
    parser.add_argument('--feature-cache', type=Path, default=Path('reports/text_benchmark_private/features.pkl'))
    parser.add_argument('--output', type=Path, default=Path('reports/evidence_sources/evidence_sources.json'))
    parser.add_argument('--predictions', type=Path, default=Path('reports/text_benchmark_20261102/private'))
    parser.add_argument('--screen', type=Path, default=Path('reports/equivalence_screen_reviewed/equivalence_screen.csv'))
    args = parser.parse_args(argv)
    metadata = json.loads(args.feature_cache.with_suffix('.metadata.json').read_text())
    if file_sha256(args.feature_cache) != metadata['cache_sha256']:
        raise ValueError('feature cache does not match its metadata')
    frame = pd.read_pickle(args.feature_cache)
    concentration = term_concentration(frame)
    df = int(concentration['effective_countries_all_records']) - 1
    with args.screen.open(newline='') as handle:
        screen_rows = list(csv.DictReader(handle))
    result = {'schema_version': 'evidence_sources.v1', 'status': 'exploratory aggregates only',
              'gain_sources': gain_sources(json.loads(args.benchmark.read_text())),
              'described_only_gains': described_only_gains(args.predictions, frame),
              'term_concentration': concentration, 'few_cluster_df': df,
              'few_cluster_screen': few_cluster_screen(screen_rows, df)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
