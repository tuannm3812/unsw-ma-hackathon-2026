"""Fixed, matched model families. No evaluation-dependent model selection."""
from __future__ import annotations

import time
import warnings

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge, SGDClassifier
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from threadpoolctl import threadpool_limits

from src.benchmark_data import LEXICAL, METADATA, S_CATEGORICAL, S_NUMERIC


def default_config() -> dict:
    return {'years': [2021, 2022, 2023, 2024, 2025], 'seed': 42,
            'max_text_features': 5000, 'min_df': 5, 'tree_iterations': 100,
            'linear_arms': ['S', 'T', 'S+M', 'S+M+L', 'S+M+L+R', 'S+P', 'S+P+M+L+R'],
            'tree_arms': ['S', 'S+M+L', 'S+P', 'S+P+M+L'],
            'bootstrap_resamples': 1000, 'min_slice_rows': 200, 'threads': 4}


def arm_columns(arm: str) -> tuple[list[str], list[str], bool]:
    blocks = set('M+L+R'.split('+') if arm == 'T' else arm.split('+'))
    if not blocks or blocks - {'S', 'M', 'L', 'R', 'P'}:
        raise ValueError(f'unknown feature arm: {arm}')
    numeric = (S_NUMERIC if 'S' in blocks else []) + (METADATA if 'M' in blocks else []) + (LEXICAL if 'L' in blocks else [])
    categories = (S_CATEGORICAL if 'S' in blocks else []) + (['programme_proxy'] if 'P' in blocks else [])
    return list(numeric), list(categories), 'R' in blocks


def _numeric(frame, train, test, columns, *, scale):
    imputer = SimpleImputer(strategy='median', keep_empty_features=True)
    a = imputer.fit_transform(frame.iloc[train][columns]).astype(np.float32)
    b = imputer.transform(frame.iloc[test][columns]).astype(np.float32)
    if scale:
        scaler = StandardScaler()
        a, b = scaler.fit_transform(a), scaler.transform(b)
    return a, b


def fit_sparse_design(frame: pd.DataFrame, train, test, config: dict) -> dict:
    """Fit block transforms only on training rows, keeping TF-IDF sparse."""
    train_blocks, test_blocks = {}, {}
    for name, cols in [('S_num', S_NUMERIC), ('M', METADATA), ('L', LEXICAL)]:
        a, b = _numeric(frame, train, test, cols, scale=True)
        train_blocks[name], test_blocks[name] = sparse.csr_matrix(a), sparse.csr_matrix(b)
    enc = OneHotEncoder(handle_unknown='ignore', sparse_output=True, dtype=np.float32)
    train_blocks['S_cat'] = enc.fit_transform(frame.iloc[train][S_CATEGORICAL]).tocsr()
    test_blocks['S_cat'] = enc.transform(frame.iloc[test][S_CATEGORICAL]).tocsr()
    penc = OneHotEncoder(handle_unknown='ignore', sparse_output=True, dtype=np.float32)
    train_blocks['P'] = penc.fit_transform(frame.iloc[train][['programme_proxy']]).tocsr()
    test_blocks['P'] = penc.transform(frame.iloc[test][['programme_proxy']]).tocsr()
    vectorizer = TfidfVectorizer(max_features=config['max_text_features'], min_df=config['min_df'],
                                 ngram_range=(1, 2), sublinear_tf=True, dtype=np.float32)
    train_blocks['R'] = vectorizer.fit_transform(frame.iloc[train]['description_clean']).tocsr()
    test_blocks['R'] = vectorizer.transform(frame.iloc[test]['description_clean']).tocsr()
    return {'train': train_blocks, 'test': test_blocks, 'encoder': enc, 'vectorizer': vectorizer}


def _stack(blocks: dict, arm: str):
    parts = ['M', 'L', 'R'] if arm == 'T' else arm.split('+')
    keys = []
    for part in parts:
        keys.extend(['S_num', 'S_cat'] if part == 'S' else [part])
    return sparse.hstack([blocks[k] for k in keys], format='csr', dtype=np.float32)


def _context_baseline(frame, train, test, days, binary):
    cols = ['country_iso', 'sector', 'fundraising_month']
    source = frame.iloc[train][cols].copy()
    source['days'], source['binary'] = days, binary
    grouped = source.groupby(cols, observed=True, dropna=False).agg(
        n=('days','size'), days=('days','median'), binary=('binary','mean'))
    merged = frame.iloc[test][cols].merge(grouped, how='left', on=cols, sort=False)
    weight = merged['n'].fillna(0).to_numpy() / (merged['n'].fillna(0).to_numpy() + 50)
    global_days, global_p = np.median(days), np.mean(binary)
    return {'days': weight * merged['days'].fillna(global_days).to_numpy() + (1-weight)*global_days,
            'probability': weight * merged['binary'].fillna(global_p).to_numpy() + (1-weight)*global_p}


def fit_predict_window(frame: pd.DataFrame, train_index, test_index, config: dict):
    """Yield predictions in the supplied test-row order plus auditable metadata."""
    train, test = np.asarray(train_index), np.asarray(test_index)
    yd = frame.iloc[train]['funding_speed_days'].to_numpy(dtype=float)
    ylog = np.log1p(yd)
    yb = frame.iloc[train]['funded_within_24h'].to_numpy(dtype=int)
    if len(np.unique(yb)) != 2:
        raise ValueError('training requires both classes for the matched classifier study')
    common = {'train_rows': len(train), 'test_rows': len(test), 'random_early_stopping': False}
    yield 'baseline', 'B0', {'days': np.full(len(test), np.median(yd)),
                            'probability': np.full(len(test), np.mean(yb))}, dict(common)
    yield 'baseline', 'B1', _context_baseline(frame, train, test, yd, yb), dict(common)
    with threadpool_limits(limits=config['threads']):
        design_start = time.perf_counter()
        design = fit_sparse_design(frame, train, test, config)
        transform_seconds = time.perf_counter() - design_start
        for arm in config['linear_arms']:
            a, b = _stack(design['train'], arm), _stack(design['test'], arm)
            reg = Ridge(alpha=10, solver='lsqr', tol=1e-5, max_iter=1000)
            clf = SGDClassifier(loss='log_loss', alpha=1e-5, max_iter=100, tol=1e-4,
                                average=True, early_stopping=False, random_state=config['seed'])
            started = time.perf_counter()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                reg.fit(a, ylog)
                clf.fit(a, yb)
            fit_seconds = time.perf_counter() - started
            predict_start = time.perf_counter()
            raw_days = np.expm1(reg.predict(b).astype(float))
            predictions = {'days': np.maximum(raw_days, 0), 'probability': clf.predict_proba(b)[:, 1]}
            metadata = dict(common, features=a.shape[1], train_nonzero=a.nnz,
                            transform_seconds=transform_seconds, fit_seconds=fit_seconds,
                            predict_seconds=time.perf_counter()-predict_start,
                            duration_iterations=np.atleast_1d(reg.n_iter_).tolist(),
                            classifier_iterations=int(clf.n_iter_),
                            negative_duration_predictions_clipped=int((raw_days < 0).sum()),
                            warnings=[str(w.message) for w in caught])
            yield 'linear', arm, predictions, metadata
            del a, b, reg, clf
        del design
        # Compact tree arms never contain R, and never densify TF-IDF.
        for arm in config['tree_arms']:
            numeric, categorical, has_text = arm_columns(arm)
            if has_text:
                raise ValueError('compact tree arms cannot contain sparse R')
            start = time.perf_counter()
            a_num, b_num = _numeric(frame, train, test, numeric, scale=False)
            enc = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1,
                                 encoded_missing_value=-1, max_categories=127, dtype=np.float32)
            a_cat = enc.fit_transform(frame.iloc[train][categorical])
            b_cat = enc.transform(frame.iloc[test][categorical])
            a, b = np.column_stack([a_num, a_cat]), np.column_stack([b_num, b_cat])
            params = {'max_iter':config['tree_iterations'], 'max_leaf_nodes':15,
                      'learning_rate':.1, 'l2_regularization':1, 'early_stopping':False,
                      'random_state':config['seed'],
                      'categorical_features':list(range(len(numeric), a.shape[1]))}
            reg, clf = HistGradientBoostingRegressor(**params), HistGradientBoostingClassifier(**params)
            transform_seconds = time.perf_counter()-start
            fit_start = time.perf_counter()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                reg.fit(a, ylog)
                clf.fit(a, yb)
            fit_seconds = time.perf_counter()-fit_start
            predict_start = time.perf_counter()
            raw_days = np.expm1(reg.predict(b))
            predictions = {'days':np.maximum(raw_days,0), 'probability':clf.predict_proba(b)[:,1]}
            metadata = dict(common, features=a.shape[1], transform_seconds=transform_seconds,
                            fit_seconds=fit_seconds, predict_seconds=time.perf_counter()-predict_start,
                            duration_iterations=int(reg.n_iter_), classifier_iterations=int(clf.n_iter_),
                            negative_duration_predictions_clipped=int((raw_days < 0).sum()),
                            warnings=[str(w.message) for w in caught])
            yield 'histogram_boosting', arm, predictions, metadata
            del a, b, a_cat, b_cat, a_num, b_num, reg, clf
