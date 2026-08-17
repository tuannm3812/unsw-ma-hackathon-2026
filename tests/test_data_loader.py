import numpy as np
import pandas as pd
import pytest

from src.data_loader import prepare_analysis_data, validate_schema


def test_prepare_analysis_data_creates_fractional_duration_and_binary_target(synthetic_kiva_df):
    result = prepare_analysis_data(synthetic_kiva_df)
    assert result.loc[0, "funding_speed_days"] == pytest.approx(0.5)
    assert result.loc[0, "funded_within_24h"] == 1
    assert result.loc[0, "log_funding_speed"] == pytest.approx(np.log1p(0.5))
    assert result.loc[0, "valid_completed_outcome"]


def test_prepare_analysis_data_flags_missing_and_negative_outcomes(synthetic_kiva_df):
    frame = synthetic_kiva_df.copy()
    frame.loc[0, "raisedDate"] = None
    frame.loc[1, "raisedDate"] = "2019-12-01T00:00:00Z"
    result = prepare_analysis_data(frame)
    assert not result.loc[0, "valid_completed_outcome"]
    assert pd.isna(result.loc[0, "funding_speed_days"])
    assert not result.loc[1, "valid_completed_outcome"]
    assert result.loc[1, "outcome_issue"] == "negative_duration"


def test_validate_schema_lists_missing_required_columns(synthetic_kiva_df):
    with pytest.raises(ValueError, match="raisedDate, use"):
        validate_schema(synthetic_kiva_df.drop(columns=["raisedDate", "use"]), ["use", "raisedDate"])
