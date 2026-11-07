import pytest


def test_cache_reuse_checks_input_identity(tmp_path, synthetic_kiva_df):
    from src.benchmark_cache import load_features
    path = tmp_path/'input.pkl'
    synthetic_kiva_df.to_pickle(path)
    cache = tmp_path/'features.pkl'
    first, audit, identity = load_features(path, cache, [2024])
    second, audit2, identity2 = load_features(path, cache, [2024])
    assert first.equals(second) and audit == audit2 and identity == identity2
    changed = synthetic_kiva_df.copy()
    changed.loc[0,'loanAmount'] = 9999
    changed.to_pickle(path)
    with pytest.raises(ValueError,match='identity'):
        load_features(path,cache,[2024])
