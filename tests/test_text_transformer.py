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
