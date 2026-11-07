"""Private deterministic-feature cache with strict data/source identity checks."""
from __future__ import annotations

import json
import platform
from pathlib import Path

import nltk
import numpy as np
import pandas as pd

from src.benchmark_data import audit_availability, build_benchmark_frame
from src.data_loader import load_kiva_pickle
from src.programme_audit import file_sha256


def load_features(data_path: Path, cache_path: Path | None, years: list[int]):
    """Return frame, aggregate audit and identity; never reuse mismatched caches."""
    root = Path(__file__).resolve().parents[1]
    sources = [root/'src'/name for name in
               ['benchmark_cache.py','benchmark_data.py','features.py','data_loader.py']]
    sources += sorted((root/'resources/nltk_data').rglob('*.zip'))
    identity = {'data_filename': data_path.name, 'data_sha256':file_sha256(data_path),
                'data_size_bytes':data_path.stat().st_size, 'years':years,
                'source_hashes':{str(p.relative_to(root)):file_sha256(p) for p in sources},
                'versions':{'python':platform.python_version(), 'pandas':pd.__version__,
                            'numpy':np.__version__, 'nltk':nltk.__version__}}
    meta_path = cache_path.with_suffix('.metadata.json') if cache_path else None
    if cache_path and (cache_path.exists() or meta_path.exists()):
        if not (cache_path.exists() and meta_path.exists()):
            raise ValueError('incomplete feature cache; use a new cache path')
        metadata = json.loads(meta_path.read_text())
        if identity != metadata['identity'] or file_sha256(cache_path) != metadata['cache_sha256']:
            raise ValueError('feature cache identity mismatch; use a new cache path')
        print('Verified deterministic-feature cache', flush=True)
        return pd.read_pickle(cache_path), metadata['audit'], identity
    print('Loading restricted source; only aggregate statistics will be reported', flush=True)
    raw = load_kiva_pickle(str(data_path))
    audit = audit_availability(raw, years)
    print(f"Availability audit: {audit['eligible_rows']:,}/{audit['input_rows']:,} eligible rows",flush=True)
    for row in audit['windows']:
        print(f"{row['year']}: {row['unavailable_completed_membership_rows']:,} pre-cutoff postings complete at/after cutoff",flush=True)
    frame = build_benchmark_frame(raw)
    if cache_path:
        cache_path.parent.mkdir(parents=True,exist_ok=True)
        frame.to_pickle(cache_path)
        metadata = {'identity':identity, 'audit':audit, 'cache_sha256':file_sha256(cache_path)}
        meta_path.write_text(json.dumps(metadata,indent=2,allow_nan=False)+'\n')
    return frame, audit, identity
