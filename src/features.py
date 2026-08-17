import os
import re
import pandas as pd
import numpy as np

try:
    from src.data_loader import validate_schema
except ModuleNotFoundError:
    from data_loader import validate_schema

# NLTK's VADER sentiment analyzer is used only when its lexicon is already
# installed locally. Nothing in this module ever downloads it: the project's
# constraint is that no network access happens during import or feature
# extraction.
try:
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
except ImportError:  # pragma: no cover - nltk is a listed dependency
    nltk = None
    SentimentIntensityAnalyzer = None


# Columns required to compute the deterministic narrative and borrower
# feature set. Missing columns raise a clear error instead of failing deep
# inside a lambda.
REQUIRED_DETERMINISTIC_COLUMNS = [
    "description",
    "use",
    "whySpecial",
    "gender",
    "borrowerCount",
    "loanAmount",
]

# Narrative framing patterns. These are theory-guided keyword lists, not
# claims about lender psychology - they only count how often a borrower's
# text touches on each theme.
FAMILY_PATTERN = r"\b(?:child(?:ren)?|family|son|daughter|mother|father|parent(?:s)?|wife|husband|stud(?:y|ies)|school)\b"
BASIC_NEEDS_PATTERN = r"\b(?:toilet|sanitary|water|health|medical|disease|electricity|solar|clean|energy|house|housing|roof)\b"
BUSINESS_PATTERN = r"\b(?:business|shop|store|sell|stock|buy|capital|invest|profit|client|customer|market|sales)\b"
AGENCY_PATTERN = r"\b(?:decide(?:d|s)?|plan(?:s|ned|ning)?|manage(?:s|d|ment)?|responsible|determined|hard[- ]?working|independent(?:ly)?|control(?:s|led)?|own(?:s|ed)?|run(?:s|ning)?|lead(?:s|ing)?)\b"
GRATITUDE_PATTERN = r"\b(?:thank(?:s|ful|you)?|grateful(?:ly)?|appreciate(?:s|d|ion)?|bless(?:ed|ing|ings)?)\b"
URGENCY_PATTERN = r"\b(?:urgent(?:ly)?|immediately|emergency|crisis|desperate(?:ly)?|asap|deadline|right away|as soon as possible|without delay|quickly)\b"
FIRST_PERSON_PATTERN = r"\b(?:i|me|my|mine|we|us|our|ours)\b"
THIRD_PERSON_PATTERN = r"\b(?:he|him|his|she|her|hers|they|them|their|theirs)\b"

FRAMING_PATTERNS = {
    "family": FAMILY_PATTERN,
    "basic_needs": BASIC_NEEDS_PATTERN,
    "business": BUSINESS_PATTERN,
    "agency": AGENCY_PATTERN,
    "gratitude": GRATITUDE_PATTERN,
    "urgency": URGENCY_PATTERN,
    "first_person": FIRST_PERSON_PATTERN,
    "third_person": THIRD_PERSON_PATTERN,
}

# Concrete-detail patterns: numbers, borrower age mentions, and years of
# operating history. These are proxies for narrative specificity, not for
# whether the detail is true.
NUMBER_TOKEN_PATTERN = r"\b\d+\b"
AGE_PATTERN = r"\b(?:age[ds]?\s+\d{1,3}|\d{1,3}[- ]years?[- ]old)\b"
YEARS_IN_BUSINESS_PATTERN = (
    r"\b(?:for|since)\s+\d{1,2}\s+years?\b"
    r"|\b\d{1,2}\s+years?\s+(?:in\s+business|of\s+business|experience)\b"
)


def _vader_lexicon_available() -> bool:
    """Return True only if the VADER lexicon is already installed locally.

    This never triggers a network call: nltk.data.find only searches local
    NLTK data paths and raises LookupError when the resource is absent.
    """
    if nltk is None:
        return False
    try:
        nltk.data.find("sentiment/vader_lexicon.zip")
        return True
    except LookupError:
        return False


def clean_html(text: object) -> str:
    """
    Removes HTML tags and cleans up whitespace in narrative text fields.
    """
    if not isinstance(text, str):
        return ""
    # Remove HTML tags like <br />, <p>, etc.
    clean = re.sub(r"<[^>]+>", " ", text)
    # Remove excessive spaces
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def classify_gender(value: object) -> str:
    """
    Classify a raw Kiva `gender` value without ever assuming missing means
    female. Returns "unknown" for missing/blank values, "mixed" when both
    female and male tokens are present, otherwise "female" or "male".
    """
    if not isinstance(value, str) or not value.strip():
        return "unknown"
    tokens = {token.strip().lower() for token in value.split(",") if token.strip()}
    has_female = "female" in tokens
    has_male = "male" in tokens
    if has_female and has_male:
        return "mixed"
    if has_female:
        return "female"
    if has_male:
        return "male"
    return "unknown"


def _count_pattern(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def _per_100(counts: pd.Series, words: pd.Series) -> pd.Series:
    return np.where(words.gt(0), counts / words * 100, 0.0)


def _is_missing_text(raw: object) -> bool:
    return not isinstance(raw, str) or not raw.strip()


def _sentence_count(text: str) -> int:
    if not text:
        return 0
    return len([segment for segment in re.split(r"[.!?]+", text) if segment.strip()])


def _add_text_length_features(df: pd.DataFrame) -> pd.DataFrame:
    df["clean_description"] = df["description"].apply(clean_html)
    df["clean_use"] = df["use"].apply(clean_html)
    df["clean_whySpecial"] = df["whySpecial"].apply(clean_html)

    df["description_missing"] = df["description"].apply(_is_missing_text).astype(int)
    df["use_missing"] = df["use"].apply(_is_missing_text).astype(int)
    df["whySpecial_missing"] = df["whySpecial"].apply(_is_missing_text).astype(int)

    df["desc_char_count"] = df["clean_description"].str.len()
    df["desc_word_count"] = df["clean_description"].apply(lambda x: len(x.split()) if x else 0)
    df["desc_sentence_count"] = df["clean_description"].apply(_sentence_count)
    desc_token_char_total = df["clean_description"].apply(
        lambda x: sum(len(token) for token in x.split()) if x else 0
    )
    df["desc_avg_word_length"] = np.where(
        df["desc_word_count"] > 0, desc_token_char_total / df["desc_word_count"], 0.0
    )
    df["desc_avg_sentence_length"] = np.where(
        df["desc_sentence_count"] > 0, df["desc_word_count"] / df["desc_sentence_count"], 0.0
    )

    df["use_char_count"] = df["clean_use"].str.len()
    df["use_word_count"] = df["clean_use"].apply(lambda x: len(x.split()) if x else 0)

    df["whySpecial_char_count"] = df["clean_whySpecial"].str.len()
    df["whySpecial_word_count"] = df["clean_whySpecial"].apply(lambda x: len(x.split()) if x else 0)

    return df


def _add_concrete_detail_features(df: pd.DataFrame) -> pd.DataFrame:
    df["number_token_count"] = df["clean_description"].apply(
        lambda x: _count_pattern(x, NUMBER_TOKEN_PATTERN)
    )
    df["age_pattern_count"] = df["clean_description"].apply(
        lambda x: _count_pattern(x, AGE_PATTERN)
    )
    df["years_in_business_count"] = df["clean_description"].apply(
        lambda x: _count_pattern(x, YEARS_IN_BUSINESS_PATTERN)
    )
    return df


def _add_framing_features(df: pd.DataFrame) -> pd.DataFrame:
    for name, pattern in FRAMING_PATTERNS.items():
        counts = df["clean_description"].apply(lambda x: _count_pattern(x, pattern))
        df[f"{name}_mentions"] = counts
        df[f"{name}_mentions_per_100_words"] = _per_100(counts, df["desc_word_count"])
    return df


def _add_sentiment_features(df: pd.DataFrame) -> pd.DataFrame:
    if _vader_lexicon_available():
        analyzer = SentimentIntensityAnalyzer()

        def score(text):
            if not text:
                return pd.Series({
                    "desc_sentiment_compound": 0.0,
                    "desc_sentiment_pos": 0.0,
                    "desc_sentiment_neg": 0.0,
                    "desc_sentiment_neu": 1.0,
                })
            scores = analyzer.polarity_scores(text)
            return pd.Series({
                "desc_sentiment_compound": scores["compound"],
                "desc_sentiment_pos": scores["pos"],
                "desc_sentiment_neg": scores["neg"],
                "desc_sentiment_neu": scores["neu"],
            })

        sentiment_df = df["clean_description"].apply(score)
        df = pd.concat([df, sentiment_df], axis=1)
        df["sentiment_available"] = 1
    else:
        df["desc_sentiment_compound"] = 0.0
        df["desc_sentiment_pos"] = 0.0
        df["desc_sentiment_neg"] = 0.0
        df["desc_sentiment_neu"] = 1.0
        df["sentiment_available"] = 0
    return df


def extract_text_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compatibility wrapper: cleans narrative text and adds length,
    concrete-detail, framing, and sentiment features by delegating to
    focused deterministic helpers.
    """
    df = df.copy()
    df = _add_text_length_features(df)
    df = _add_concrete_detail_features(df)
    df = _add_framing_features(df)
    df = _add_sentiment_features(df)
    return df


def _add_borrower_features(df: pd.DataFrame) -> pd.DataFrame:
    # Gender is classified from the raw field only; missing/blank values are
    # "unknown", never assumed to be female.
    df["gender_classification"] = df["gender"].apply(classify_gender)
    df["is_group_loan"] = (df["borrowerCount"] > 1).astype(int)
    return df


def extract_borrower_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compatibility wrapper: adds borrower structure features by delegating
    to a focused deterministic helper.
    """
    df = df.copy()
    return _add_borrower_features(df)


def _add_financial_features(df: pd.DataFrame) -> pd.DataFrame:
    df["log_loan_amount"] = np.log1p(df["loanAmount"])
    df["loan_size_band"] = pd.cut(
        df["loanAmount"],
        bins=[-np.inf, 250, 750, np.inf],
        labels=["small", "medium", "large"],
    )
    return df


def extract_financial_and_geography_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compatibility wrapper: adds transparent, fixed-threshold loan-size
    features by delegating to a focused deterministic helper. Raw
    categorical and geography columns are left untouched for downstream
    pipelines to encode after a train/validation split.
    """
    df = df.copy()
    return _add_financial_features(df)


def extract_deterministic_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the full deterministic narrative and borrower feature set.

    No step here fits anything on the input observations (no TF-IDF, no
    NMF, no target-derived statistics), so it is safe to call on training,
    validation, or holdout rows alike. Raw categorical and time columns are
    preserved unchanged for downstream, training-fitted pipelines.
    """
    validate_schema(df, REQUIRED_DETERMINISTIC_COLUMNS)
    df = extract_text_features(df)
    df = extract_borrower_features(df)
    df = extract_financial_and_geography_features(df)
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Backward-compatible alias for the deterministic feature set. Topic
    modeling is intentionally not fitted here: fitting TF-IDF/NMF must
    happen only on training observations, via a dedicated transformer.
    """
    return extract_deterministic_features(df)


if __name__ == "__main__":
    # Test feature builder
    try:
        from src.data_loader import load_and_prepare_data
    except ModuleNotFoundError:
        from data_loader import load_and_prepare_data

    default_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Kiva_Loans_Sample.pkl")
    try:
        df = load_and_prepare_data(default_path)
        df_feat = build_features(df)
        print("Feature building successful!")
        print(f"Original columns: {df.shape[1]} -> Engineered columns: {df_feat.shape[1]}")
        print("\nEngineered Feature Sample (first 2 rows):")
        feat_cols = [
            "desc_char_count",
            "desc_word_count",
            "family_mentions",
            "is_group_loan",
            "gender_classification",
            "log_loan_amount",
        ]
        print(df_feat[feat_cols].head(2))
    except Exception as e:
        print(f"Error testing feature builder: {e}")
