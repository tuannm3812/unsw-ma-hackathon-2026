import json
import numpy as np
import pytest


def test_runner_writes_immutable_complete_aggregate_bundle(tmp_path, large_synthetic_kiva_df):
    from src.run_text_benchmark import run_benchmark
    from src.benchmark_models import default_config
    path = tmp_path/'fixture.pkl'
    large_synthetic_kiva_df.to_pickle(path)
    config = default_config()
    config.update({'years':[2024], 'min_df':1, 'max_text_features':40,
                   'tree_iterations':3, 'bootstrap_resamples':50, 'min_slice_rows':2,
                   'linear_arms':['S','S+M+L+R','S+P','S+P+M+L+R'],
                   'tree_arms':['S','S+M+L']})
    out = tmp_path/'run'
    result = run_benchmark(path,out,config)
    assert result['status'] == 'completed_pending_review'
    assert len(result['models']) == 8
    assert all(m['row_identity_sha256']==result['windows'][0]['test_row_identity_sha256'] for m in result['models'])
    assert result['paired_comparisons']
    assert result['feature_quality']['sentiment_available_rows'] == len(large_synthetic_kiva_df)
    assert result['feature_quality']['population'] == 'eligible completed durations'
    assert (out/'private/predictions-2024.npz').exists()
    assert (out/'provenance.json').exists()
    assert (out/'source_snapshot.zip').exists()
    text = (out/'benchmark.json').read_text()
    for forbidden in ['Borrower','operated her family','/Users/','image_url']:
        assert forbidden not in text
    for model in result['models']:
        assert sum(b['count'] for b in model['calibration']) == model['metrics']['rows']
    with pytest.raises(FileExistsError):
        run_benchmark(path,out,config)


def test_runner_preserves_failed_run_status(tmp_path, large_synthetic_kiva_df):
    from src.run_text_benchmark import run_benchmark
    from src.benchmark_models import default_config
    path = tmp_path/'fixture.pkl'
    large_synthetic_kiva_df.to_pickle(path)
    config=default_config()
    config['years']=[1900]
    out=tmp_path/'failed'
    with pytest.raises(ValueError):
        run_benchmark(path,out,config)
    assert json.loads((out/'status.json').read_text())['status']=='failed'


@pytest.mark.parametrize('changes',[{'years':[]},{'years':[2024,2024]},
                                    {'linear_arms':['S','S']}])
def test_runner_rejects_empty_or_duplicate_protocol_before_creating_output(tmp_path,changes):
    from src.run_text_benchmark import run_benchmark
    from src.benchmark_models import default_config
    config=default_config()
    config.update(changes)
    with pytest.raises(ValueError,match='protocol'):
        run_benchmark(tmp_path/'unused.pkl',tmp_path/'run',config)
    assert not (tmp_path/'run').exists()
