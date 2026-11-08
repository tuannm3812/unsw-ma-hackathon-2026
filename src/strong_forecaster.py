"""Does text still help a stronger forecaster? Exploratory extension, 2026-11-08.

The November benchmark found a 0.26-0.39 day text gain on a sparse linear
model whose MAE (about 8 days) is far worse than its compact tree (about
4.9 days), and almost no gain on that small tree, which never saw TF-IDF.
This leaves the forecasting question open: is the linear gain only a weak
baseline catching up?

This module refits one larger histogram-boosting configuration, fixed before
any evaluation result was seen, on the same as-of windows, with three arms:

* ``S``          structured context only;
* ``S+M+L``      plus description form and lexical measures;
* ``S+M+L+D``    plus a 64-component truncated SVD of training-fitted TF-IDF
                 (the same vectoriser settings as the benchmark's R block).

The SVD closes the representation gap the benchmark documented: its tree arms
never contained any bag-of-words information. Paired intervals reuse the
benchmark's month and country resampling.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OrdinalEncoder
from threadpoolctl import threadpool_limits

from src.benchmark_data import LEXICAL, METADATA, S_CATEGORICAL, S_NUMERIC, calendar_split
from src.benchmark_models import _numeric
from src.benchmark_metrics import paired_loss_intervals, score_predictions

CONFIG = {
    'years': [2021, 2022, 2023, 2024, 2025], 'seed': 42,
    'max_text_features': 5000, 'min_df': 5, 'svd_components': 64,
    # Fixed a priori: five times the benchmark's iterations and four times
    # its leaves, with a lower learning rate. No evaluation-dependent tuning.
    'tree': {'max_iter': 500, 'max_leaf_nodes': 63, 'learning_rate': 0.05,
             'min_samples_leaf': 100, 'l2_regularization': 1.0, 'early_stopping': False},
    # As run for the large tree: missing categories become the string 'nan'.
    'encoding': {'max_categories': 255, 'missing_as_string': True},
    'arms': ['S', 'S+M+L', 'S+M+L+D'], 'bootstrap_resamples': 1000, 'threads': 8,
}
# The benchmark's own compact tree, to isolate adding bag-of-words alone.
BENCHMARK_TREE = {'max_iter': 100, 'max_leaf_nodes': 15, 'learning_rate': 0.1,
                  'l2_regularization': 1.0, 'early_stopping': False}
PAIRS = [('S', 'S+M+L'), ('S', 'S+M+L+D'), ('S+M+L', 'S+M+L+D')]


def _design(frame, train, test, arm, svd, encoding):
    numeric = list(S_NUMERIC) + (METADATA + LEXICAL if 'M' in arm else [])
    if encoding.get('median_impute'):
        a_num, b_num = _numeric(frame, train, test, numeric, scale=False)
    else:
        a_num = frame.iloc[train][numeric].to_numpy(np.float32)
        b_num = frame.iloc[test][numeric].to_numpy(np.float32)
    enc = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1,
                         encoded_missing_value=-1, max_categories=encoding['max_categories'],
                         dtype=np.float32)
    a_cat, b_cat = frame.iloc[train][S_CATEGORICAL], frame.iloc[test][S_CATEGORICAL]
    if encoding['missing_as_string']:
        a_cat, b_cat = a_cat.astype(str), b_cat.astype(str)
    a_cat, b_cat = enc.fit_transform(a_cat), enc.transform(b_cat)
    parts_a, parts_b = [a_num, a_cat], [b_num, b_cat]
    if 'D' in arm:
        parts_a.append(svd['train'])
        parts_b.append(svd['test'])
    cat_index = list(range(a_num.shape[1], a_num.shape[1] + a_cat.shape[1]))
    return np.column_stack(parts_a), np.column_stack(parts_b), cat_index


def _svd(frame, train, test, config):
    vec = TfidfVectorizer(max_features=config['max_text_features'], min_df=config['min_df'],
                          ngram_range=(1, 2), sublinear_tf=True, dtype=np.float32)
    text = frame['description_clean'].fillna('')
    a = vec.fit_transform(text.iloc[train])
    b = vec.transform(text.iloc[test])
    svd = TruncatedSVD(n_components=config['svd_components'], random_state=config['seed'])
    return {'train': svd.fit_transform(a).astype(np.float32),
            'test': svd.transform(b).astype(np.float32),
            'explained_variance': float(svd.explained_variance_ratio_.sum())}


def run(cache: Path, output: Path, config: dict) -> dict:
    frame = pd.read_pickle(cache)
    output.mkdir(parents=True, exist_ok=True)
    results = {'config': config, 'started_utc': datetime.now(timezone.utc).isoformat(),
               'windows': [], 'paired': []}
    for year in config['years']:
        train, test = calendar_split(frame, year)
        yd = frame.iloc[train]['funding_speed_days'].to_numpy(float)
        yb = frame.iloc[train]['funded_within_24h'].to_numpy(int)
        target = frame.iloc[test]
        td = target['funding_speed_days'].to_numpy(float)
        tb = target['funded_within_24h'].to_numpy(int)
        with threadpool_limits(limits=config['threads']):
            t0 = time.perf_counter()
            svd = _svd(frame, train, test, config)
            print(f'{year}: SVD {time.perf_counter()-t0:.0f}s, '
                  f'explained {svd["explained_variance"]:.3f}', flush=True)
            preds = {}
            for arm in config['arms']:
                a, b, cats = _design(frame, train, test, arm, svd, config['encoding'])
                params = dict(config['tree'], random_state=config['seed'], categorical_features=cats)
                t0 = time.perf_counter()
                reg = HistGradientBoostingRegressor(**params).fit(a, np.log1p(yd))
                clf = HistGradientBoostingClassifier(**params).fit(a, yb)
                days = np.maximum(np.expm1(reg.predict(b)), 0)
                preds[arm] = {'days': days, 'probability': clf.predict_proba(b)[:, 1]}
                score = score_predictions(td, tb, days, preds[arm]['probability'])
                results['windows'].append(dict(year=year, arm=arm, train_rows=len(train),
                                               test_rows=len(test), features=a.shape[1],
                                               fit_seconds=time.perf_counter()-t0,
                                               svd_explained_variance=svd['explained_variance'],
                                               **score))
                print(f'  {arm}: MAE={score["mae_days"]:.4f} Brier={score["brier"]:.5f} '
                      f'AUC={score["roc_auc"]:.4f} ({time.perf_counter()-t0:.0f}s)', flush=True)
        groups = {'calendar_month': target['fundraisingDate'].dt.strftime('%Y-%m').to_numpy(),
                  'country': target['country_iso'].to_numpy()}
        for base, added in PAIRS:
            a, b = preds[base], preds[added]
            losses = {'mae_days': (np.abs(a['days']-td), np.abs(b['days']-td)),
                      'brier': ((a['probability']-tb)**2, (b['probability']-tb)**2)}
            for metric, (lb, la) in losses.items():
                for unit, g in groups.items():
                    results['paired'].append(dict(
                        year=year, baseline=base, candidate=added, metric=metric,
                        resampling_unit=unit,
                        **paired_loss_intervals(lb, la, g, config['bootstrap_resamples'],
                                                config['seed'])))
        (output / 'strong_forecaster.json').write_text(json.dumps(results, indent=1, default=float))
    results['finished_utc'] = datetime.now(timezone.utc).isoformat()
    (output / 'strong_forecaster.json').write_text(json.dumps(results, indent=1, default=float))
    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--cache', type=Path, default=Path('reports/text_benchmark_private/features.pkl'))
    parser.add_argument('--output', type=Path, default=Path('reports/strong_forecaster'))
    parser.add_argument('--years', type=int, nargs='*')
    parser.add_argument('--tree', choices=['large', 'benchmark'], default='large')
    args = parser.parse_args(argv)
    config = dict(CONFIG)
    if args.tree == 'benchmark':
        config['tree'] = dict(BENCHMARK_TREE)
        # Match the benchmark encoder exactly so its S and S+M+L reproduce.
        config['encoding'] = {'max_categories': 127, 'missing_as_string': False,
                              'median_impute': True}
    config['tree_name'] = args.tree
    if args.years:
        config['years'] = args.years
    run(args.cache, args.output, config)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
