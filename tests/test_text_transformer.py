import numpy as np
import pandas as pd
import pytest

from src.text_transformer import KivaTopicTransformer


def test_topic_transformer_does_not_learn_holdout_vocabulary():
    train = pd.Series([
        "farmer buys seeds for harvest",
        "farmer needs seeds and tools",
        "retailer buys stock for shop",
        "retailer expands local shop stock",
    ])
    holdout = pd.Series(["futureonlytoken appears nowhere else"])
    transformer = KivaTopicTransformer(n_topics=2, min_df=1, random_state=42)
    transformer.fit(train)
    assert "futureonlytoken" not in transformer.vectorizer_.vocabulary_
    transformed = transformer.transform(holdout)
    assert list(transformed.columns) == ["topic_0", "topic_1"]
    assert transformed.shape == (1, 2)


def test_topic_transformer_preserves_input_index():
    text = pd.Series(["seed farm", "shop stock"], index=[10, 20])
    transformer = KivaTopicTransformer(n_topics=2, min_df=1).fit(text)
    assert transformer.transform(text).index.tolist() == [10, 20]


def test_topic_transformer_output_stays_finite_on_a_sample_that_triggers_nmf_warnings(
    large_synthetic_kiva_df,
):
    # This fixture's size/shape (120 rows, default n_topics=5) reliably
    # reproduces the benign divide-by-zero/overflow/invalid-value
    # RuntimeWarning that NMF(init="nndsvda")'s randomized_svd
    # initialization step emits on some numpy/Accelerate-BLAS backends
    # (see the `warnings.catch_warnings` block in `KivaTopicTransformer.fit`)
    # - confirmed here with real numbers that the fitted topic-probability
    # output remains finite (and a valid probability distribution)
    # regardless of that warning firing.
    transformer = KivaTopicTransformer(n_topics=5, random_state=42)
    transformer.fit(large_synthetic_kiva_df["description"])
    transformed = transformer.transform(large_synthetic_kiva_df["description"])

    values = transformed.to_numpy()
    assert np.isfinite(values).all()
    assert (values >= 0).all()
    row_sums = values.sum(axis=1)
    assert row_sums == pytest.approx(1.0)
