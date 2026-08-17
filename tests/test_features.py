import pandas as pd
import pytest

from src.features import classify_gender, extract_deterministic_features


@pytest.mark.parametrize(("raw", "expected"), [
    ("female", "female"),
    ("male", "male"),
    ("female, male", "mixed"),
    (None, "unknown"),
    ("", "unknown"),
])
def test_classify_gender_does_not_assume_missing_is_female(raw, expected):
    assert classify_gender(raw) == expected


def test_narrative_counts_are_normalized_per_100_words(synthetic_kiva_df):
    frame = synthetic_kiva_df.iloc[[0]].copy()
    frame.loc[frame.index[0], "description"] = "family business needs support"
    result = extract_deterministic_features(frame)
    assert result.iloc[0]["family_mentions"] == 1
    assert result.iloc[0]["family_mentions_per_100_words"] == pytest.approx(25.0)


def test_deterministic_features_do_not_create_unverified_female_ratio(synthetic_kiva_df):
    result = extract_deterministic_features(synthetic_kiva_df)
    assert "female_ratio" not in result.columns
    assert set(result["gender_classification"]) == {"female", "male", "mixed", "unknown"}
