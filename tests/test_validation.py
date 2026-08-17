import pandas as pd
import pytest

from src.validation import chronological_holdout


def test_chronological_holdout_separates_earlier_and_later_rows(synthetic_kiva_df):
    train, holdout = chronological_holdout(synthetic_kiva_df, holdout_start="2024-01-01")
    assert pd.to_datetime(train["fundraisingDate"], utc=True).max() < pd.Timestamp("2024-01-01", tz="UTC")
    assert pd.to_datetime(holdout["fundraisingDate"], utc=True).min() >= pd.Timestamp("2024-01-01", tz="UTC")


def test_chronological_holdout_rejects_empty_side(synthetic_kiva_df):
    with pytest.raises(ValueError, match="empty training or holdout partition"):
        chronological_holdout(synthetic_kiva_df, holdout_start="2010-01-01")
