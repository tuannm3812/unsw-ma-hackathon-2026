"""Run a separate immutable retrospective structure/text benchmark.

No primary result is overwritten. Public outputs are aggregate; row positions,
labels and predictions stay in an ignored private subdirectory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import resource
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
import pandas as pd
import scipy
import sklearn

from src.benchmark_cache import load_features
from src.benchmark_data import calendar_split, feature_registry
from src.benchmark_metrics import paired_loss_intervals, reliability_bins, score_predictions
from src.benchmark_models import default_config, fit_predict_window
from src.benchmark_reporting import validate_protocol
from src.programme_audit import file_sha256


def _write(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def row_identity(positions) -> str:
    return hashlib.sha256(np.asarray(positions, dtype='<i8').tobytes()).hexdigest()


def group_diagnostics(frame, train, test, ydays, ybinary, predictions, minimum):
    observed = frame.iloc[test]
    masks = {
        'month': observed['fundraisingDate'].dt.strftime('%Y-%m').to_numpy(),
        'country': observed['country_iso'].to_numpy(),
        'sector': observed['sector'].to_numpy(),
        'amount_band': observed['loan_size_band'].to_numpy(),
        'description_missing': observed['description_missing'].astype(str).to_numpy(),
        'status': observed['status'].astype(str).to_numpy(),
        'duration_band': np.select([ydays<=1, ydays<=3, ydays<=7, ydays<=30],
                                   ['0–1 days','1–3 days','3–7 days','7–30 days'],default='over 30 days'),
    }
    for field in ['description_signature', 'template_signature', 'country_iso']:
        seen = observed[field].isin(frame.iloc[train][field]).to_numpy()
        values = np.where(seen, 'seen', 'unseen').astype(object)
        values[observed[field].eq('').to_numpy()] = 'missing'
        masks[field + '_novelty'] = values
    result = []
    for dimension, values in masks.items():
        for group in pd.unique(values):
            mask = values == group
            n = int(mask.sum())
            row = {'dimension':dimension, 'group':str(group), 'rows':n,
                   'suppressed':n < minimum}
            if n >= minimum:
                row.update({'prevalence':float(ybinary[mask].mean()),
                            'mae_days':float(np.mean(np.abs(predictions['days'][mask]-ydays[mask]))),
                            'bias_days':float(np.mean(predictions['days'][mask]-ydays[mask])),
                            'brier':float(np.mean((predictions['probability'][mask]-ybinary[mask])**2))})
            result.append(row)
    return result


def _paired(frame, test, predictions, config, year):
    candidates = [
        ('linear', 'S', 'S+M'), ('linear', 'S', 'S+M+L'),
        ('linear', 'S', 'S+M+L+R'), ('linear', 'S+P', 'S+P+M+L+R'),
        ('histogram_boosting', 'S', 'S+M+L'),
        ('histogram_boosting', 'S+P', 'S+P+M+L'),
    ]
    target = frame.iloc[test]
    yd = target['funding_speed_days'].to_numpy(dtype=float)
    yb = target['funded_within_24h'].to_numpy(dtype=int)
    grouping = {'calendar_month': target['fundraisingDate'].dt.strftime('%Y-%m').to_numpy(),
                'country': target['country_iso'].to_numpy()}
    result = []
    for family, base, added in candidates:
        if (family, base) not in predictions or (family, added) not in predictions:
            continue
        a, b = predictions[family, base], predictions[family, added]
        loss = {'mae_days':(np.abs(a['days']-yd),np.abs(b['days']-yd)),
                'brier':((a['probability']-yb)**2,(b['probability']-yb)**2)}
        for metric, (base_loss, new_loss) in loss.items():
            for name, groups in grouping.items():
                result.append(dict(year=year, family=family, baseline=base, candidate=added,
                                   metric=metric, resampling_unit=name,
                                   **paired_loss_intervals(base_loss,new_loss,groups,
                                          config['bootstrap_resamples'],config['seed'])))
    return result


def run_benchmark(data_path: Path, output_dir: Path, config: dict,
                  feature_cache: Path | None = None) -> dict:
    """Execute all configured arms; completion remains pending independent review."""
    validate_protocol(config)
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir/'private').mkdir()
    root = Path(__file__).resolve().parents[1]
    started = time.perf_counter()
    sources = sorted((root/'src').glob('*.py'))
    provenance = {
        'started_at_utc':datetime.now(timezone.utc).isoformat(),
        'git_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        'git_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip()),
        'source_hashes':{str(p.relative_to(root)):file_sha256(p) for p in sources},
        'configuration':config, 'feature_registry':feature_registry(),
        'versions':{'python':platform.python_version(),'pandas':pd.__version__,
                    'numpy':np.__version__,'sklearn':sklearn.__version__,'scipy':scipy.__version__},
        'evaluation_status':'Retrospective benchmark; no untouched final test or all-listing deployment evaluation.',
        'duration_estimand':'expm1 of a log-target squared-error prediction, clipped at zero; not a conditional mean-days estimate.',
    }
    with ZipFile(output_dir/'source_snapshot.zip','w',ZIP_DEFLATED) as archive:
        for source in sources:
            archive.write(source,str(source.relative_to(root)))
    _write(output_dir/'provenance.json',provenance)
    _write(output_dir/'status.json',{'status':'running'})
    result = {'schema_version':'matched_text_benchmark.v1','status':'running',
              'configuration':config, 'windows':[], 'models':[], 'paired_comparisons':[]}
    try:
        frame, audit, identity = load_features(data_path,feature_cache,config['years'])
        provenance['data_and_feature_identity'] = identity
        _write(output_dir/'provenance.json',provenance)
        _write(output_dir/'availability_audit.json',audit)
        if audit['duplicate_id_rows']:
            raise ValueError('duplicate loan IDs require an explicit population review before benchmarking')
        eligible = frame['valid_completed_outcome'].to_numpy(dtype=bool)
        registry = feature_registry()
        result['feature_quality'] = {
            'population':'eligible completed durations',
            'sentiment_available_rows':int((frame.loc[eligible,'sentiment_available']==1).sum()),
            'empty_clean_description_rows':int(frame.loc[eligible,'description_clean'].eq('').sum()),
            'missing_numeric_rows':{column:int(frame.loc[eligible,column].isna().sum())
                                    for column in registry['S_numeric']+registry['M']+registry['L']},
        }
        for year in config['years']:
            train,test = calendar_split(frame,year)
            print(f'Window {year}: {len(train):,} as-of training; {len(test):,} evaluation',flush=True)
            target = frame.iloc[test]
            ydays = target['funding_speed_days'].to_numpy(dtype=float)
            ybinary = target['funded_within_24h'].to_numpy(dtype=int)
            identity_hash = row_identity(test)
            window = {'year':year,'train_rows':len(train),'test_rows':len(test),
                      'train_row_identity_sha256':row_identity(train),'test_row_identity_sha256':identity_hash,
                      'training_max_completion':frame.iloc[train]['raisedDate'].max().isoformat(),
                      'posting_min':target['fundraisingDate'].min().isoformat(),
                      'posting_max':target['fundraisingDate'].max().isoformat()}
            result['windows'].append(window)
            predictions = {}
            private = {'row_position':test,'y_days':ydays,'y_binary':ybinary}
            for family,arm,prediction,metadata in fit_predict_window(frame,train,test,config):
                scores = score_predictions(ydays,ybinary,prediction['days'],prediction['probability'])
                record = {'year':year,'family':family,'arm':arm,'row_identity_sha256':identity_hash,
                          'metrics':scores,'fit':metadata,
                          'calibration':reliability_bins(ybinary,prediction['probability']),
                          'slices':group_diagnostics(frame,train,test,ydays,ybinary,prediction,config['min_slice_rows'])}
                result['models'].append(record)
                predictions[family,arm] = prediction
                key=family+'__'+arm.replace('+','_')
                for name,values in prediction.items():
                    private[key+'__'+name] = values
                print(f"  {family}/{arm}: MAE={scores['mae_days']:.5f}; Brier={scores['brier']:.6f}; warnings={len(metadata.get('warnings',[]))}",flush=True)
                _write(output_dir/'benchmark.partial.json',result)
            np.savez_compressed(output_dir/'private'/f'predictions-{year}.npz',**private)
            result['paired_comparisons'].extend(_paired(frame,test,predictions,config,year))
            _write(output_dir/'benchmark.partial.json',result)
            del predictions,private,target
        expected = len(config['years'])*(2+len(config['linear_arms'])+len(config['tree_arms']))
        if len(result['models']) != expected:
            raise RuntimeError('not all planned model arms completed')
        result['status'] = 'completed_pending_review'
        result['input_rows'],result['eligible_rows'] = audit['input_rows'],audit['eligible_rows']
        result['runtime_seconds'] = time.perf_counter()-started
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result['peak_process_memory_mib'] = rss/(1024**2 if platform.system()=='Darwin' else 1024)
        result['model_warning_count']=sum(len(x['fit'].get('warnings',[])) for x in result['models'])
        _write(output_dir/'benchmark.json',result)
        provenance['finished_at_utc']=datetime.now(timezone.utc).isoformat()
        provenance['benchmark_sha256']=file_sha256(output_dir/'benchmark.json')
        provenance['audit_sha256']=file_sha256(output_dir/'availability_audit.json')
        provenance['source_snapshot_sha256']=file_sha256(output_dir/'source_snapshot.zip')
        _write(output_dir/'provenance.json',provenance)
        _write(output_dir/'status.json',{'status':result['status'],'model_count':expected})
        print(f'BENCHMARK_COMPLETE {expected} model/arm windows; review pending',flush=True)
        return result
    except Exception as exc:
        _write(output_dir/'status.json',{'status':'failed','error_type':type(exc).__name__})
        raise


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--feature-cache',type=Path)
    args=parser.parse_args(argv)
    run_benchmark(args.data,args.output_dir,default_config(),args.feature_cache)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
