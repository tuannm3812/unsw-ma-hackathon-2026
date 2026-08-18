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


def test_desc_avg_word_length_excludes_whitespace(synthetic_kiva_df):
    frame = synthetic_kiva_df.iloc[[0]].copy()
    frame.loc[frame.index[0], "description"] = "family business needs support"
    result = extract_deterministic_features(frame)
    assert result.iloc[0]["desc_avg_word_length"] == pytest.approx(6.5)


@pytest.mark.parametrize(("raw_region", "expected_group"), [
    ("Africa", "Africa"),
    ("Asia", "Asia"),
    ("Latin America", "Other"),  # known but not in the fixed major-category allowlist
    ("Antarctica", "Other"),  # unseen/novel region string
    (None, "Other"),  # missing region
])
def test_region_group_uses_fixed_allowlist_everything_else_maps_to_other(
    synthetic_kiva_df, raw_region, expected_group,
):
    # `region_group` (src/features.py) is a fixed Africa/Asia/"Other"
    # allowlist, not a sample-relative computation - so it must behave
    # identically regardless of what other regions happen to be present in
    # a given call's data, including a region string it has never seen
    # before or a missing value.
    frame = synthetic_kiva_df.iloc[[0]].copy()
    frame.loc[frame.index[0], "region"] = raw_region
    result = extract_deterministic_features(frame)
    assert result.iloc[0]["region_group"] == expected_group
