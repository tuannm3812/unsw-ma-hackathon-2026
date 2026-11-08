"""Is the linear text gain about the loan, or about its context? 2026-11-08.

Exploratory extension of the November benchmark. Text may help forecasts only
because it encodes context the structured block already holds coarsely:
country, sector and the month of posting. This placebo shuffles every
text-derived input (description form M, lexical measures L and the raw text
behind TF-IDF R) among loans in the same country x sector x posting month,
in both training and evaluation rows, and refits the benchmark's Ridge.

* If the shuffled gain is close to the real gain, text mostly carries
  context-level information.
* If it collapses, the gain depends on which loan the text belongs to.

Uses the benchmark's own design helpers and Ridge settings. Duration only.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits

from src.benchmark_data import LEXICAL, METADATA, calendar_split
from src.benchmark_metrics import paired_loss_intervals
from src.benchmark_models import _stack, default_config, fit_sparse_design

TEXT_COLUMNS = METADATA + LEXICAL + ['description_clean']


def shuffle_within(frame: pd.DataFrame, columns, keys, seed: int) -> pd.DataFrame:
    """Permute `columns` jointly among rows sharing `keys` (one draw per stratum)."""
    rng = np.random.default_rng(seed)
    out = frame.copy()
    strata = frame.groupby(keys, observed=True, dropna=False, sort=False).indices
    source = np.arange(len(frame))
    for rows in strata.values():
        if len(rows) > 1:
            source[rows] = rows[rng.permutation(len(rows))]
    for column in columns:
        out[column] = frame[column].to_numpy()[source]
    return out, float(np.mean(source != np.arange(len(frame))))


def _ridge_days(design, arm, y_log):
    a, b = _stack(design['train'], arm), _stack(design['test'], arm)
    reg = Ridge(alpha=10, solver='lsqr', tol=1e-5, max_iter=1000).fit(a, y_log)
    return np.maximum(np.expm1(reg.predict(b).astype(float)), 0)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--cache', type=Path, default=Path('reports/text_benchmark_private/features.pkl'))
    parser.add_argument('--output', type=Path, default=Path('reports/text_placebo'))
    parser.add_argument('--years', type=int, nargs='*', default=[2021, 2022, 2023, 2024, 2025])
    args = parser.parse_args(argv)
    config = default_config()
    frame = pd.read_pickle(args.cache)
    frame['posting_month'] = frame['fundraisingDate'].dt.strftime('%Y-%m')
    keys = ['country_iso', 'sector', 'posting_month']
    placebo, moved = shuffle_within(frame, TEXT_COLUMNS, keys, config['seed'])
    args.output.mkdir(parents=True, exist_ok=True)
    out = {'generated_at': datetime.now(timezone.utc).isoformat(), 'strata': keys,
           'shuffled_columns': TEXT_COLUMNS, 'share_rows_moved': moved, 'years': []}
    for year in args.years:
        train, test = calendar_split(frame, year)
        y_log = np.log1p(frame.iloc[train]['funding_speed_days'].to_numpy(float))
        target = frame.iloc[test]
        yd = target['funding_speed_days'].to_numpy(float)
        months = target['fundraisingDate'].dt.strftime('%Y-%m').to_numpy()
        countries = target['country_iso'].to_numpy()
        with threadpool_limits(limits=8):
            real = fit_sparse_design(frame, train, test, config)
            base = _ridge_days(real, 'S', y_log)
            with_text = _ridge_days(real, 'S+M+L+R', y_log)
            del real
            fake = fit_sparse_design(placebo, train, test, config)
            shuffled = _ridge_days(fake, 'S+M+L+R', y_log)
            del fake
        lb, lr, ls = np.abs(base - yd), np.abs(with_text - yd), np.abs(shuffled - yd)
        # Cap at the training maximum as a tail diagnostic (see loss_alignment).
        cap = frame.iloc[train]['funding_speed_days'].max()
        cb, cr, cs = (np.abs(np.minimum(p, cap) - yd) for p in (base, with_text, shuffled))
        row = {'year': year, 'mae_S': float(lb.mean()), 'mae_text': float(lr.mean()),
               'mae_shuffled_text': float(ls.mean()),
               'gain_real': paired_loss_intervals(lb, lr, months, 1000, 42),
               'gain_shuffled': paired_loss_intervals(lb, ls, months, 1000, 42),
               'real_minus_shuffled': paired_loss_intervals(ls, lr, months, 1000, 42),
               'real_minus_shuffled_country': paired_loss_intervals(ls, lr, countries, 1000, 42),
               'capped': {'gain_real': float((cb - cr).mean()),
                          'gain_shuffled': float((cb - cs).mean())}}
        out['years'].append(row)
        print(f"{year}: S {row['mae_S']:.4f}  text {row['mae_text']:.4f}  "
              f"shuffled {row['mae_shuffled_text']:.4f}  capped gains "
              f"{row['capped']['gain_real']:.3f} / {row['capped']['gain_shuffled']:.3f}", flush=True)
        (args.output / 'text_placebo.json').write_text(json.dumps(out, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
