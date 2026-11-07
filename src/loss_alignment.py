"""2025 loss-alignment extension: is the negative day-space R² a back-transform effect?

A separate, retrospective extension of the November matched benchmark. It reuses
the same deterministic-feature cache, as-of 2025 cohort, S and S+M+L+R blocks,
seed and fixed Ridge settings, with no evaluation-dependent tuning. Three duration
estimators share one fitted design:

* ``log1p`` - the benchmark estimator: Ridge on log(1 + days), expm1, clip at 0.
* ``days`` - Ridge on raw days, clip at 0.
* ``log1p_smeared`` - the log1p fit with a Duan smearing back-transform, the factor
  estimated on training residuals only.
* ``log1p_capped`` - a diagnostic, not a proposed estimator: the log1p prediction capped
  at the longest training duration, which isolates the extreme predicted tail.

Outputs are aggregate. No primary or November snapshot is changed. Associations and
forecast errors here say nothing about editing a description.
"""
from __future__ import annotations

import argparse
import json
import platform
import resource
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits

from src.benchmark_data import calendar_split
from src.benchmark_metrics import paired_loss_intervals
from src.benchmark_models import _stack, default_config, fit_sparse_design
from src.programme_audit import file_sha256

YEAR = 2025
ARMS = ('S', 'S+M+L+R')
ESTIMATORS = ('log1p', 'days', 'log1p_smeared', 'log1p_capped')


def duan_smearing_factor(y_log_train, pred_log_train) -> float:
    """Return Duan's factor mean(exp(residual)) from training residuals."""
    y, pred = (np.asarray(x, dtype=float) for x in (y_log_train, pred_log_train))
    if not y.size or y.shape != pred.shape:
        raise ValueError('nonempty matching training arrays are required')
    return float(np.mean(np.exp(y - pred)))


def smeared_days(pred_log, factor: float) -> np.ndarray:
    """Back-transform log(1 + days): factor * exp(pred) - 1, clipped at zero days."""
    return np.maximum(factor * np.exp(np.asarray(pred_log, dtype=float)) - 1, 0)


def duration_scores(y_days, days) -> dict:
    """Return the day-space losses this extension reports."""
    y, p = (np.asarray(x, dtype=float) for x in (y_days, days))
    if not y.size or y.shape != p.shape or not (np.isfinite(y).all() and np.isfinite(p).all()):
        raise ValueError('finite matching arrays are required')
    error = p - y
    total = float(np.sum((y - y.mean()) ** 2))
    return {'mae_days': float(np.mean(np.abs(error))),
            'rmse_days': float(np.sqrt(np.mean(error ** 2))),
            'r2_days': 1 - float(np.sum(error ** 2)) / total,
            'median_ae_days': float(np.median(np.abs(error))),
            'bias_days': float(np.mean(error))}


def error_anatomy(y_days, days) -> dict:
    """Locate squared error: over- versus under-prediction and the extreme tail."""
    y, p = (np.asarray(x, dtype=float) for x in (y_days, days))
    squared = (p - y) ** 2
    total = float(squared.sum())
    tail = p >= np.quantile(p, .99)
    return {'share_squared_error_overprediction': float(squared[p > y].sum()) / total,
            'share_squared_error_top_1pct_predictions': float(squared[tail].sum()) / total,
            'prediction_quantiles_days': {str(q): float(np.quantile(p, q))
                                          for q in (.5, .9, .99, .999)},
            'prediction_max_days': float(p.max()),
            'predictions_above_observed_max': int((p > y.max()).sum()),
            'observed_max_days': float(y.max())}


def _gain(base: dict, new: dict) -> dict:
    """Positive is better for every entry."""
    return {'mae_days': base['mae_days'] - new['mae_days'],
            'rmse_days': base['rmse_days'] - new['rmse_days'],
            'r2_days': new['r2_days'] - base['r2_days'],
            'median_ae_days': base['median_ae_days'] - new['median_ae_days']}


def run(cache: Path, output: Path, year: int = YEAR) -> dict:
    started = time.perf_counter()
    config = default_config()
    metadata = json.loads(cache.with_suffix('.metadata.json').read_text())
    cache_sha = file_sha256(cache)
    if cache_sha != metadata['cache_sha256']:
        raise ValueError('feature cache does not match its metadata')
    frame = pd.read_pickle(cache)
    train, test = calendar_split(frame, year)
    yd_train = frame.iloc[train]['funding_speed_days'].to_numpy(dtype=float)
    yd = frame.iloc[test]['funding_speed_days'].to_numpy(dtype=float)
    ylog_train = np.log1p(yd_train)
    months = frame.iloc[test]['fundraisingDate'].dt.strftime('%Y-%m').to_numpy()
    countries = frame.iloc[test]['country_iso'].to_numpy()
    predictions, arms = {}, {}
    with threadpool_limits(limits=config['threads']):
        design = fit_sparse_design(frame, train, test, config)
        print('design fitted', flush=True)
        for arm in ARMS:
            a, b = _stack(design['train'], arm), _stack(design['test'], arm)
            log_model = Ridge(alpha=10, solver='lsqr', tol=1e-5, max_iter=1000).fit(a, ylog_train)
            pred_log = log_model.predict(b).astype(float)
            pred_log_train = log_model.predict(a).astype(float)
            factor = duan_smearing_factor(ylog_train, pred_log_train)
            day_model = Ridge(alpha=10, solver='lsqr', tol=1e-5, max_iter=1000).fit(a, yd_train)
            raw_days = day_model.predict(b).astype(float)
            predictions[arm] = {'log1p': np.maximum(np.expm1(pred_log), 0),
                                'days': np.maximum(raw_days, 0),
                                'log1p_smeared': smeared_days(pred_log, factor),
                                'log1p_capped': np.clip(np.expm1(pred_log), 0, yd_train.max())}
            residual = ylog_train - pred_log_train
            arms[arm] = {'features': a.shape[1], 'smearing_factor': factor,
                         'train_log_residual_sd': float(residual.std()),
                         'log_space_r2': 1 - float(np.sum((np.log1p(yd) - pred_log) ** 2))
                         / float(np.sum((np.log1p(yd) - np.log1p(yd).mean()) ** 2)),
                         'negative_predictions_clipped_days_target': int((raw_days < 0).sum()),
                         'days_iterations': np.atleast_1d(day_model.n_iter_).tolist(),
                         'log_iterations': np.atleast_1d(log_model.n_iter_).tolist()}
            print(f'{arm}: fitted', flush=True)
            del a, b, log_model, day_model
    estimators = {}
    for name in ESTIMATORS:
        scores = {arm: duration_scores(yd, predictions[arm][name]) for arm in ARMS}
        base, new = (np.abs(predictions[arm][name] - yd) for arm in ARMS)
        estimators[name] = {
            'arms': scores,
            'anatomy': {arm: error_anatomy(yd, predictions[arm][name]) for arm in ARMS},
            'text_gain': _gain(scores['S'], scores['S+M+L+R']),
            'text_gain_mae_intervals': {
                unit: paired_loss_intervals(base, new, groups, config['bootstrap_resamples'],
                                            config['seed'])
                for unit, groups in [('calendar_month', months), ('country', countries)]}}
        print(name, json.dumps(scores), flush=True)
    constants = {'training_mean_days': float(yd_train.mean()),
                 'training_max_days': float(yd_train.max()),
                 'training_median_days': float(np.median(yd_train)),
                 'evaluation_mean_days': float(yd.mean()),
                 'evaluation_median_days': float(np.median(yd))}
    for name, value in [('training_mean', yd_train.mean()), ('training_median', np.median(yd_train))]:
        constants[name + '_predictor'] = duration_scores(yd, np.full(len(yd), value))
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result = {
        'schema_version': 'loss_alignment_2025.v1',
        'status': 'separate retrospective extension; aggregates only',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'year': year, 'train_rows': len(train), 'test_rows': len(test),
        'configuration': {'seed': config['seed'], 'ridge': 'alpha=10, lsqr, tol=1e-5, max_iter=1000',
                          'max_text_features': config['max_text_features'], 'min_df': config['min_df'],
                          'threads': config['threads'], 'evaluation_dependent_tuning': False},
        'feature_cache_sha256': cache_sha, 'arm_fit': arms, 'constants': constants,
        'estimators': estimators, 'runtime_seconds': time.perf_counter() - started,
        'peak_process_memory_mib': rss / (1024 ** 2 if platform.system() == 'Darwin' else 1024),
        'versions': {'python': platform.python_version(), 'pandas': pd.__version__,
                     'numpy': np.__version__, 'sklearn': sklearn.__version__}}
    output.mkdir(parents=True, exist_ok=True)
    name = 'loss_alignment.json' if year == YEAR else f'loss_alignment_{year}.json'
    (output / name).write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--feature-cache', type=Path,
                        default=Path('reports/text_benchmark_private/features.pkl'))
    parser.add_argument('--output-dir', type=Path, default=Path('reports/loss_alignment_2025'))
    parser.add_argument('--year', type=int, default=YEAR)
    args = parser.parse_args(argv)
    run(args.feature_cache, args.output_dir, args.year)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
