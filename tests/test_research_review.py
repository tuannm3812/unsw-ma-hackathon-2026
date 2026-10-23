"""Checks that bounded-memory extraction preserves the inference design."""
import pandas as pd
import pytest

from src import research_review
from src.feature_sensitivity import build_sensitivity_frame


def test_chunked_review_preserves_estimator_inputs_and_omits_raw_text(synthetic_kiva_df):
    frame = synthetic_kiva_df.copy()
    frame.loc[0, "whySpecial"] = None
    frame.loc[1, "whySpecial"] = " "
    frame.loc[2, "whySpecial"] = "Other programme"
    expected = build_sensitivity_frame(frame)
    actual = research_review.build_review_frame(frame, chunk_size=3)
    original_columns = [column for column in actual if column != "programme_proxy"]
    pd.testing.assert_frame_equal(actual[original_columns], expected[original_columns])
    assert actual["programme_proxy"].iloc[0] == actual["programme_proxy"].iloc[1]
    assert actual["programme_proxy"].iloc[2] != actual["programme_proxy"].iloc[3]
    assert not {"description", "whySpecial", "name", "id"}.intersection(actual.columns)
    with pytest.raises(ValueError):
        research_review.build_review_frame(frame, chunk_size=0)
