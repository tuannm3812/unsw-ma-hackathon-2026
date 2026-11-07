"""Metrics and paired fixed-model uncertainty for retrospective comparisons."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score, log_loss, mean_absolute_error,
    mean_squared_error, median_absolute_error, r2_score, roc_auc_score,
)


def score_predictions(y_days, y_binary, days, probability) -> dict:
    arrays = [np.asarray(x, dtype=float) for x in (y_days, y_binary, days, probability)]
    if not arrays[0].size or len({x.shape for x in arrays}) != 1:
        raise ValueError('nonempty prediction and target arrays must have matching shapes')
    if not all(np.isfinite(x).all() for x in arrays):
        raise ValueError('all targets and predictions must be finite')
    y_days, y_binary, days, probability = arrays
    if (days < 0).any() or (y_days < 0).any() or ((probability < 0) | (probability > 1)).any():
        raise ValueError('invalid duration or probability range')
    both = len(np.unique(y_binary)) == 2
    return {
        'rows': len(days), 'prevalence': float(np.mean(y_binary)),
        'mae_days': float(mean_absolute_error(y_days, days)),
        'median_ae_days': float(median_absolute_error(y_days, days)),
        'rmse_days': float(np.sqrt(mean_squared_error(y_days, days))),
        'r2_days': float(r2_score(y_days, days)) if len(days) > 1 else None,
        'bias_days': float(np.mean(days - y_days)),
        'log_mae': float(mean_absolute_error(np.log1p(y_days), np.log1p(days))),
        'roc_auc': float(roc_auc_score(y_binary, probability)) if both else None,
        'average_precision': float(average_precision_score(y_binary, probability)) if both else None,
        'brier': float(np.mean((probability - y_binary) ** 2)),
        'log_loss': float(log_loss(y_binary, probability, labels=[0, 1])),
    }


def reliability_bins(y, probability, bins: int = 10) -> list[dict]:
    y, probability = np.asarray(y), np.asarray(probability)
    codes = np.minimum((probability * bins).astype(int), bins - 1)
    result = []
    for i in range(bins):
        mask = codes == i
        result.append({'lower': i / bins, 'upper': (i + 1) / bins, 'count': int(mask.sum()),
                       'mean_probability': float(probability[mask].mean()) if mask.any() else None,
                       'observed_rate': float(y[mask].mean()) if mask.any() else None})
    return result


def paired_loss_intervals(baseline_loss, candidate_loss, groups,
                          resamples: int = 1000, seed: int = 42) -> dict:
    """Bootstrap complete clusters with paired losses and record-count weighting.

    The interval is conditional on fixed fitted models. It does not include
    retraining uncertainty and may be unstable with few or dependent clusters.
    """
    base, new, groups = map(np.asarray, (baseline_loss, candidate_loss, groups))
    if not len(base) or len({len(base), len(new), len(groups)}) != 1:
        raise ValueError('arrays must have the same length and be nonempty')
    if not np.isfinite(base).all() or not np.isfinite(new).all():
        raise ValueError('losses must be finite')
    if resamples < 1:
        raise ValueError('resamples must be positive')
    grouped = pd.DataFrame({'gain': base - new, 'group': groups}).groupby(
        'group', dropna=False, observed=True)['gain'].agg(['sum', 'size'])
    totals, sizes = grouped['sum'].to_numpy(), grouped['size'].to_numpy()
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(grouped), size=(resamples, len(grouped)))
    boot = totals[draws].sum(axis=1) / sizes[draws].sum(axis=1)
    return {'gain': float(np.mean(base - new)), 'clusters': len(grouped),
            'interval_95': np.quantile(boot, [.025, .975]).tolist() if len(grouped) > 1 else None,
            'resamples': resamples,
            'boundary': 'Fixed-model cluster-resampling sensitivity; positive means lower loss. '
                        'Not causal, not retraining uncertainty, few clusters limit interpretation.'}
