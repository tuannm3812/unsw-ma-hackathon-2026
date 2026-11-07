"""Validate and read aggregate evidence without silently recomputing models."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from src.programme_audit import file_sha256


def validate_protocol(config: dict) -> None:
    """Reject empty/duplicate protocols before a run can claim completion."""
    years=config.get('years',[])
    linear=config.get('linear_arms',[])
    tree=config.get('tree_arms',[])
    allowed_linear={'S','T','S+M','S+M+L','S+M+L+R','S+P','S+P+M+L+R'}
    allowed_tree={'S','S+M+L','S+P','S+P+M+L'}
    if (not years or len(years)!=len(set(years)) or
        any(type(y) is not int or y<1 or y>9998 for y in years) or
        len(linear)!=len(set(linear)) or len(tree)!=len(set(tree)) or
        not (linear or tree) or set(linear)-allowed_linear or set(tree)-allowed_tree):
        raise ValueError('protocol needs unique nonempty years and valid unique model arms')


def _validate_contents(benchmark, audit, provenance, status) -> None:
    config=benchmark['configuration']
    validate_protocol(config)
    if config != provenance['configuration']:
        raise ValueError('configuration differs from provenance')
    expected={(y,'baseline',a) for y in config['years'] for a in ['B0','B1']}
    expected.update((y,'linear',a) for y in config['years'] for a in config['linear_arms'])
    expected.update((y,'histogram_boosting',a) for y in config['years'] for a in config['tree_arms'])
    actual=[(m['year'],m['family'],m['arm']) for m in benchmark['models']]
    if len(actual)!=len(expected) or set(actual)!=expected:
        raise ValueError('missing or duplicate model results')
    if status.get('status')!='completed_pending_review' or status.get('model_count')!=len(expected):
        raise ValueError('execution status does not confirm complete model results')
    windows={w['year']:w for w in benchmark['windows']}
    audits={w['year']:w for w in audit['windows']}
    if len(benchmark['windows'])!=len(windows) or set(windows)!=set(config['years']) or set(audits)!=set(windows):
        raise ValueError('missing or duplicate evaluation windows')
    if benchmark['input_rows']!=audit['input_rows'] or benchmark['eligible_rows']!=audit['eligible_rows']:
        raise ValueError('population differs from availability audit')
    for model in benchmark['models']:
        window=windows[model['year']]
        audit_window=audits[model['year']]
        if (window['train_rows']<1 or window['test_rows']<1 or
            model['metrics']['rows']!=window['test_rows'] or
            model['fit']['train_rows']!=window['train_rows'] or
            model['fit']['test_rows']!=window['test_rows'] or
            audit_window['asof_train_rows']!=window['train_rows'] or
            audit_window['evaluation_rows']!=window['test_rows'] or
            model['row_identity_sha256']!=window['test_row_identity_sha256']):
            raise ValueError('model rows or identities differ from window/audit')
    possible=[('linear','S','S+M'),('linear','S','S+M+L'),('linear','S','S+M+L+R'),
              ('linear','S+P','S+P+M+L+R'),('histogram_boosting','S','S+M+L'),
              ('histogram_boosting','S+P','S+P+M+L')]
    paired_expected={(y,f,a,b,m,g) for y in config['years'] for f,a,b in possible
                     if (y,f,a) in expected and (y,f,b) in expected
                     for m in ['mae_days','brier'] for g in ['calendar_month','country']}
    paired=[(p['year'],p['family'],p['baseline'],p['candidate'],p['metric'],p['resampling_unit'])
            for p in benchmark.get('paired_comparisons',[])]
    if len(paired)!=len(paired_expected) or set(paired)!=paired_expected:
        raise ValueError('missing or duplicate paired comparisons')


def load_bundle(directory: Path, *, require_review: bool = True) -> dict:
    """Require complete protocol results, consistent artifacts and a bound review."""
    try:
        provenance=json.loads((directory/'provenance.json').read_text())
        for name,key in [('benchmark.json','benchmark_sha256'),
                         ('availability_audit.json','audit_sha256'),
                         ('source_snapshot.zip','source_snapshot_sha256')]:
            if file_sha256(directory/name) != provenance[key]:
                raise ValueError(f'{name} hash differs from recorded provenance')
        benchmark=json.loads((directory/'benchmark.json').read_text())
        audit=json.loads((directory/'availability_audit.json').read_text())
        status=json.loads((directory/'status.json').read_text())
        if benchmark.get('schema_version')!='matched_text_benchmark.v1' or benchmark.get('status')!='completed_pending_review':
            raise ValueError('unsupported or incomplete benchmark')
        _validate_contents(benchmark,audit,provenance,status)
        with ZipFile(directory/'source_snapshot.zip') as archive:
            for name,digest in provenance['source_hashes'].items():
                if hashlib.sha256(archive.read(name)).hexdigest()!=digest:
                    raise ValueError('source snapshot differs from source hash')
        review_path=directory/'review_status.json'
        review=json.loads(review_path.read_text()) if review_path.exists() else {}
        if require_review and (review.get('status')!='accepted' or
                               review.get('benchmark_sha256')!=provenance['benchmark_sha256'] or
                               review.get('audit_sha256')!=provenance['audit_sha256'] or
                               review.get('provenance_sha256')!=file_sha256(directory/'provenance.json')):
            raise ValueError('An accepted review tied to this report, audit and provenance is required')
        return {'benchmark':benchmark,'audit':audit,'provenance':provenance,'review':review}
    except (KeyError,TypeError) as exc:
        raise ValueError('malformed benchmark bundle') from exc
