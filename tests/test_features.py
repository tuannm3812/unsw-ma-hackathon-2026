import pandas as pd
import pytest

import src.features as features_module
from src.features import (
    MIN_REGION_OBSERVATIONS,
    MIN_SECTOR_OBSERVATIONS,
    _add_region_group_feature,
    _add_sector_group_feature,
    _add_sentiment_features,
    _vader_lexicon_available,
    classify_gender,
    extract_deterministic_features,
)


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


def test_region_group_keeps_a_region_that_reaches_the_observation_threshold():
    # `region_group` (src/features.py) uses a fixed *count threshold*, not
    # a fixed name list: any region with at least MIN_REGION_OBSERVATIONS
    # rows in the data actually passed to `extract_deterministic_features`
    # keeps its own level - proven here with "Oceania", a region name
    # that never appears anywhere in `src/features.py`'s code, to confirm
    # the rule generalizes rather than being secretly hardcoded to
    # Africa/Asia (a real regression an earlier version of this feature
    # had: a hardcoded `["Africa", "Asia"]` allowlist that would not have
    # adapted to a different dataset's regional distribution).
    df = pd.DataFrame({"region": ["Oceania"] * MIN_REGION_OBSERVATIONS + ["Mars"] * 2})
    result = _add_region_group_feature(df.copy())
    assert (result.loc[result["region"] == "Oceania", "region_group"] == "Oceania").all()
    assert (result.loc[result["region"] == "Mars", "region_group"] == "Other").all()


def test_region_group_collapses_a_region_just_under_the_observation_threshold():
    df = pd.DataFrame({
        "region": ["Africa"] * MIN_REGION_OBSERVATIONS + ["Latin America"] * (MIN_REGION_OBSERVATIONS - 1)
    })
    result = _add_region_group_feature(df.copy())
    assert (result.loc[result["region"] == "Africa", "region_group"] == "Africa").all()
    assert (result.loc[result["region"] == "Latin America", "region_group"] == "Other").all()


def test_region_group_maps_missing_region_to_other():
    df = pd.DataFrame({"region": ["Africa"] * MIN_REGION_OBSERVATIONS + [None]})
    result = _add_region_group_feature(df.copy())
    assert result["region_group"].iloc[-1] == "Other"


def test_region_group_wires_through_extract_deterministic_features(large_synthetic_kiva_df):
    # End-to-end check (not just the private helper) that region_group
    # reaches the real feature-extraction pipeline. large_synthetic_kiva_df
    # has 5 distinct regions, each with 18+ rows - all above
    # MIN_REGION_OBSERVATIONS - so none should collapse into "Other" here,
    # unlike the ~100-row real Kiva sample where several do.
    result = extract_deterministic_features(large_synthetic_kiva_df)
    assert "Other" not in set(result["region_group"])
    assert set(result["region_group"]) == set(result["region"])


def test_sector_group_keeps_a_sector_that_reaches_the_observation_threshold():
    # sector_group (src/features.py) uses the same count-threshold design
    # as region_group, but with MIN_SECTOR_OBSERVATIONS - a much higher
    # floor, since the design spec requires the sector interaction
    # specifically to be "restricted to adequately represented sectors"
    # on data at the scale of the full competition dataset (hundreds of
    # thousands to millions of rows), not just the ~10-row bar that's
    # meaningful for region on a 100-row sample.
    df = pd.DataFrame({
        "sector": ["Retail"] * MIN_SECTOR_OBSERVATIONS + ["Arts"] * 2
    })
    result = _add_sector_group_feature(df.copy())
    assert (result.loc[result["sector"] == "Retail", "sector_group"] == "Retail").all()
    assert (result.loc[result["sector"] == "Arts", "sector_group"] == "Other").all()


def test_sector_group_collapses_a_sector_just_under_the_observation_threshold():
    df = pd.DataFrame({
        "sector": ["Agriculture"] * MIN_SECTOR_OBSERVATIONS + ["Food"] * (MIN_SECTOR_OBSERVATIONS - 1)
    })
    result = _add_sector_group_feature(df.copy())
    assert (result.loc[result["sector"] == "Agriculture", "sector_group"] == "Agriculture").all()
    assert (result.loc[result["sector"] == "Food", "sector_group"] == "Other").all()


def test_sector_group_maps_missing_sector_to_other():
    df = pd.DataFrame({"sector": ["Retail"] * MIN_SECTOR_OBSERVATIONS + [None]})
    result = _add_sector_group_feature(df.copy())
    assert result["sector_group"].iloc[-1] == "Other"


def test_sector_group_wires_through_extract_deterministic_features(large_synthetic_kiva_df):
    # large_synthetic_kiva_df only has 120 rows total, far below
    # MIN_SECTOR_OBSERVATIONS - every sector should collapse to "Other"
    # here, which is the correct, intended behavior on a sample this
    # small (mirrors how region_group behaves on the real ~100-row Kiva
    # sample), not a bug.
    result = extract_deterministic_features(large_synthetic_kiva_df)
    assert set(result["sector_group"]) == {"Other"}


def test_vader_lexicon_is_available_via_the_vendored_copy_alone(monkeypatch):
    # `pip install nltk` does not itself include the VADER lexicon - it
    # normally requires a separate `nltk.download("vader_lexicon")` call,
    # which made sentiment scoring silently environment-dependent (real
    # scores on a machine that happened to have already run that download,
    # silent constant placeholders on a clean checkout). Simulate exactly
    # a clean checkout by wiping every real nltk data search path, keeping
    # only what src.features itself vendors, and confirm the resource is
    # still found - no download, no network access, no reliance on
    # whatever happens to already be on this machine.
    import nltk

    monkeypatch.setattr(nltk.data, "path", [features_module._VENDORED_NLTK_DATA_DIR])
    assert _vader_lexicon_available() is True


def test_sentiment_features_use_real_vader_scores_when_lexicon_available():
    df = pd.DataFrame({
        "clean_description": [
            "This is a wonderful business opportunity and I am so grateful.",
            "",
        ],
        "desc_word_count": [11, 0],
    })
    result = _add_sentiment_features(df.copy())
    assert (result["sentiment_available"] == 1).all()
    # A clearly positive sentence must score positively, not the constant
    # 0.0/0.0/0.0/1.0 placeholder used when the lexicon is unavailable.
    assert result.iloc[0]["desc_sentiment_compound"] > 0.5
    assert result.iloc[0]["desc_sentiment_pos"] > 0.0
    # Empty text still degrades to the same neutral placeholder even when
    # the lexicon is available - there is nothing to score.
    assert result.iloc[1]["desc_sentiment_compound"] == 0.0
    assert result.iloc[1]["desc_sentiment_neu"] == 1.0


def test_sentiment_features_degrade_to_constant_placeholder_when_lexicon_unavailable(monkeypatch):
    # The unavailable path (nltk missing, or the lexicon resource missing
    # for any reason) must still produce a complete, clearly-labeled
    # feature set - constant neutral placeholder values plus
    # sentiment_available = 0 - not a crash and not a silently different
    # column set.
    monkeypatch.setattr(features_module, "_vader_lexicon_available", lambda: False)
    df = pd.DataFrame({
        "clean_description": ["This is a wonderful business opportunity."],
        "desc_word_count": [6],
    })
    result = _add_sentiment_features(df.copy())
    assert result.iloc[0]["sentiment_available"] == 0
    assert result.iloc[0]["desc_sentiment_compound"] == 0.0
    assert result.iloc[0]["desc_sentiment_pos"] == 0.0
    assert result.iloc[0]["desc_sentiment_neg"] == 0.0
    assert result.iloc[0]["desc_sentiment_neu"] == 1.0
