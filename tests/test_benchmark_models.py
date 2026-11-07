import numpy as np
import pytest


def test_block_membership_is_explicit():
    from src.benchmark_models import arm_columns
    from src.benchmark_data import feature_registry
    r = feature_registry()
    nums, cats, text = arm_columns('S')
    assert set(nums) == set(r['S_numeric'])
    assert set(cats) == set(r['S_categorical'])
    assert text is False
    nums, cats, text = arm_columns('T')
    assert set(nums) == set(r['M'] + r['L']) and cats == [] and text
    assert arm_columns('S+P')[1][-1] == 'programme_proxy'
    with pytest.raises(ValueError):
        arm_columns('id')


def test_sparse_encoder_never_learns_evaluation_tokens(synthetic_kiva_df):
    from src.benchmark_data import build_benchmark_frame
    from src.benchmark_models import fit_sparse_design
    frame = build_benchmark_frame(synthetic_kiva_df)
    frame.loc[6:, 'description_clean'] = 'evaluationonlytoken'
    frame.loc[6:, 'country_iso'] = 'UNSEEN'
    config = {'max_text_features': 50, 'min_df': 1}
    design = fit_sparse_design(frame, np.arange(6), np.array([6, 7]), config)
    assert 'evaluationonlytoken' not in design['vectorizer'].vocabulary_
    assert 'UNSEEN' not in set(design['encoder'].categories_[3])
    assert design['train']['R'].shape[1] == design['test']['R'].shape[1]
    assert design['test']['R'].nnz == 0


def test_all_models_preserve_test_rows_and_disable_random_early_stopping(large_synthetic_kiva_df):
    from src.benchmark_data import build_benchmark_frame, calendar_split
    from src.benchmark_models import fit_predict_window, default_config
    frame = build_benchmark_frame(large_synthetic_kiva_df)
    train, test = calendar_split(frame, 2024)
    config = default_config()
    config.update({'min_df':1, 'max_text_features':50, 'tree_iterations':4,
                   'linear_arms':['S','T','S+P+M+L+R'], 'tree_arms':['S','S+P+M+L']})
    outputs = list(fit_predict_window(frame, train, test, config))
    assert len(outputs) == 7  # two baselines + three linear + two tree
    for family, arm, predictions, metadata in outputs:
        assert predictions['days'].shape == (len(test),)
        assert predictions['probability'].shape == (len(test),)
        assert np.isfinite(predictions['days']).all()
        assert (predictions['days'] >= 0).all()
        assert ((predictions['probability'] >= 0) & (predictions['probability'] <= 1)).all()
        assert metadata['train_rows'] == len(train)
        assert metadata['test_rows'] == len(test)
        if family in ('linear','histogram_boosting'):
            assert metadata['random_early_stopping'] is False


def test_single_training_class_fails_visibly(large_synthetic_kiva_df):
    from src.benchmark_data import build_benchmark_frame, calendar_split
    from src.benchmark_models import fit_predict_window, default_config
    frame = build_benchmark_frame(large_synthetic_kiva_df)
    train, test = calendar_split(frame, 2024)
    frame.loc[train,'funded_within_24h'] = 1
    with pytest.raises(ValueError, match='both classes'):
        list(fit_predict_window(frame, train, test, default_config()))
