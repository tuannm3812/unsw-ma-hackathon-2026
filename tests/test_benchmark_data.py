"""Contracts for the separate as-of research benchmark."""
import numpy as np
import pandas as pd
import pytest


def test_calendar_split_requires_mature_completed_membership(synthetic_kiva_df):
    from src.benchmark_data import calendar_split
    from src.data_loader import prepare_analysis_data
    df = synthetic_kiva_df.iloc[:5].copy().reset_index(drop=True)
    df['fundraisingDate'] = ['2023-12-30', '2023-12-31', '2023-12-31', '2024-01-01', '2025-01-01']
    df['raisedDate'] = ['2023-12-31', '2024-01-02', '2024-01-01', '2024-01-01', '2025-01-02']
    train, test = calendar_split(prepare_analysis_data(df), 2024)
    assert train.tolist() == [0]
    assert test.tolist() == [3]
    assert 1 not in train and 2 not in train  # including the exact boundary


def test_audit_counts_invalid_crossing_and_duplicates(synthetic_kiva_df):
    from src.benchmark_data import audit_availability
    df = synthetic_kiva_df.copy()
    df.loc[0, 'raisedDate'] = '2025-01-01'
    df.loc[1, 'raisedDate'] = None
    df.loc[2, 'raisedDate'] = '2000-01-01'
    df.loc[3, 'id'] = df.loc[0, 'id']
    df.loc[4, 'description'] = df.loc[3, 'description']
    df.loc[5, 'description'] = None
    result = audit_availability(df, [2024])
    assert result['input_rows'] == 8
    assert result['eligible_rows'] == 6
    assert result['duplicate_id_rows'] == 2
    assert result['windows'][0]['unavailable_completed_membership_rows'] == 1
    assert result['duplicate_description_rows'] == 2
    assert result['missing_description_rows'] == 1
    assert 'Borrower' not in str(result) and 'years and needs' not in str(result)


def test_frame_registry_blocks_identifiers_and_outcomes(synthetic_kiva_df):
    from src.benchmark_data import build_benchmark_frame, feature_registry
    df = synthetic_kiva_df.copy()
    df.loc[0, 'description'] = None
    frame = build_benchmark_frame(df, chunk_size=3)
    registry = feature_registry()
    predictors = set(sum(registry.values(), []))
    assert not predictors.intersection({'id','name','status','raisedDate','funding_speed_days','funded_within_24h','country_ppp','fundsLentInCountry'})
    assert set(registry['S_numeric']).isdisjoint(registry['M'] + registry['L'])
    assert len(frame) == len(df)
    assert frame.loc[0, 'description_clean'] == ''
    assert frame.loc[0, 'description_missing'] == 1
    assert predictors.issubset(frame.columns)
    changed = df.copy()
    changed['id'] = -1
    changed['raisedDate'] = '2026-01-01'
    other = build_benchmark_frame(changed, chunk_size=4)
    pd.testing.assert_frame_equal(frame[sorted(predictors)],other[sorted(predictors)])


def test_split_rejects_duplicate_index_and_empty_window(synthetic_kiva_df):
    from src.benchmark_data import calendar_split
    from src.data_loader import prepare_analysis_data
    frame = prepare_analysis_data(synthetic_kiva_df)
    with pytest.raises(ValueError, match='empty'):
        calendar_split(frame, 2010)
    frame.index = np.zeros(len(frame), dtype=int)
    with pytest.raises(ValueError, match='unique'):
        calendar_split(frame, 2024)
