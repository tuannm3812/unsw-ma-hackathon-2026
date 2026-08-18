import warnings

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF

try:
    from src.features import clean_html
except ModuleNotFoundError:
    from features import clean_html


class KivaTopicTransformer(BaseEstimator, TransformerMixin):
    """
    A scikit-learn compatible transformer for extracting topics from text using
    TF-IDF vectorization and Non-Negative Matrix Factorization (NMF).

    This transformer fits on training text only and transforms other splits
    without re-fitting, preventing data leakage.

    Parameters:
    -----------
    n_topics : int, default=5
        Number of topics to extract.
    min_df : int, default=2
        Minimum document frequency threshold for TF-IDF vectorizer.
    random_state : int, default=42
        Random seed for reproducible NMF initialization.
    """

    def __init__(self, n_topics=5, min_df=2, random_state=42):
        self.n_topics = n_topics
        self.min_df = min_df
        self.random_state = random_state

    def _coerce_text(self, X):
        """
        Convert input to a list of cleaned strings and extract index if present.

        Parameters:
        -----------
        X : pd.Series, one-column pd.DataFrame, or iterable of strings
            Text input to clean and convert.

        Returns:
        --------
        text : list of str
            Cleaned text strings.
        index : pd.Index or None
            Original index if input was a Series or DataFrame, else None.
        """
        index = None

        # Handle pd.Series
        if isinstance(X, pd.Series):
            index = X.index
            text = X.apply(clean_html).fillna("").tolist()
        # Handle one-column pd.DataFrame
        elif isinstance(X, pd.DataFrame):
            if X.shape[1] != 1:
                raise ValueError(f"Expected single-column DataFrame, got {X.shape[1]} columns")
            index = X.index
            text = X.iloc[:, 0].apply(clean_html).fillna("").tolist()
        # Handle iterable of strings
        else:
            try:
                text = [clean_html(t) if t else "" for t in X]
            except TypeError:
                raise ValueError("X must be a pd.Series, one-column pd.DataFrame, or iterable of strings")

        return text, index

    def fit(self, X, y=None):
        """
        Fit the topic transformer on training text.

        Parameters:
        -----------
        X : pd.Series, one-column pd.DataFrame, or iterable of strings
            Training text to fit topics on.
        y : ignored
            Not used, present for API consistency.

        Returns:
        --------
        self : KivaTopicTransformer
            Fitted transformer instance.
        """
        if self.n_topics < 1:
            raise ValueError(f"n_topics must be >= 1, got {self.n_topics}")

        text, _ = self._coerce_text(X)

        if not text or all(t == "" for t in text):
            raise ValueError("Training text cannot be empty")

        # Fit TF-IDF vectorizer
        self.vectorizer_ = TfidfVectorizer(
            max_df=0.95,
            min_df=self.min_df,
            stop_words="english",
            ngram_range=(1, 2)
        )
        matrix = self.vectorizer_.fit_transform(text)

        # Validate n_topics against matrix dimensions
        if self.n_topics > min(matrix.shape):
            raise ValueError(
                f"n_topics ({self.n_topics}) exceeds the fitted text matrix dimensions "
                f"({matrix.shape[0]} documents, {matrix.shape[1]} features)"
            )

        # Fit NMF model.
        #
        # init="nndsvda"'s randomized_svd initialization step can trigger a
        # benign RuntimeWarning (divide-by-zero/overflow/invalid value in
        # matmul) from numpy/Accelerate-BLAS on Apple Silicon - reproduced
        # identically on unrelated random matrices with no Kiva data
        # involved, and confirmed the resulting topic-probability outputs
        # (see `transform` below) remain finite regardless. Scoped to just
        # this call so any other RuntimeWarning in this module still
        # surfaces normally.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            self.nmf_ = NMF(
                n_components=self.n_topics,
                random_state=self.random_state,
                init="nndsvda",
                max_iter=1000,
            ).fit(matrix)

        return self

    def transform(self, X):
        """
        Transform text into topic probability distributions.

        Parameters:
        -----------
        X : pd.Series, one-column pd.DataFrame, or iterable of strings
            Text to transform.

        Returns:
        --------
        pd.DataFrame
            Topic probability matrix with columns ["topic_0", "topic_1", ...].
            Preserves input index if X was a Series or DataFrame.
        """
        check_is_fitted(self, ["vectorizer_", "nmf_"])

        text, index = self._coerce_text(X)

        # Transform text through TF-IDF and NMF
        weights = self.nmf_.transform(self.vectorizer_.transform(text))

        # Normalize to probabilities (sum to 1 per row)
        totals = weights.sum(axis=1, keepdims=True)
        probabilities = np.divide(
            weights, totals, out=np.zeros_like(weights), where=totals != 0
        )

        return pd.DataFrame(
            probabilities,
            index=index,
            columns=self.get_feature_names_out()
        )

    def get_feature_names_out(self, input_features=None):
        """
        Get output feature names (topic column names).

        Parameters:
        -----------
        input_features : ignored
            Not used, present for API consistency.

        Returns:
        --------
        np.ndarray
            Array of topic column names ["topic_0", "topic_1", ...].
        """
        return np.array([f"topic_{i}" for i in range(self.n_topics)])

    def get_topic_terms(self, n_top_words=10):
        """
        Extract top words for each topic.

        Parameters:
        -----------
        n_top_words : int, default=10
            Number of top words per topic to extract.

        Returns:
        --------
        dict
            Mapping from topic index to list of top words.
        """
        check_is_fitted(self, ["vectorizer_", "nmf_"])

        feature_names = self.vectorizer_.get_feature_names_out()
        topic_keywords = {}

        for topic_idx, topic in enumerate(self.nmf_.components_):
            top_features_ind = topic.argsort()[:-n_top_words - 1:-1]
            top_words = [feature_names[i] for i in top_features_ind]
            topic_keywords[topic_idx] = top_words

        return topic_keywords
