import os
import re
import pandas as pd
import numpy as np
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF


# Download VADER lexicon if not already cached
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)


def clean_html(text: str) -> str:
    """
    Removes HTML tags and cleans up whitespace in descriptions.
    """
    if not isinstance(text, str):
        return ""
    # Remove HTML tags like <br />, <p>, etc.
    clean = re.sub(r'<[^>]+>', ' ', text)
    # Remove excessive spaces
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()

def extract_text_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts NLP and narrative-based features from description and use columns.
    These features represent the communication style, narrative complexity, and persuasive elements.
    
    Hypotheses:
    1. Narrative Length: Longer descriptions may signal transparency, but can also increase cognitive load.
    2. Focus on Family/Need: Borrowers highlighting family, health, or education get funded faster.
    3. Sentiment & Tone: Positive and grateful language influences prosocial lenders.
    """
    df = df.copy()
    
    # 1. Clean description
    df['clean_description'] = df['description'].apply(clean_html)
    df['clean_use'] = df['use'].apply(clean_html)
    
    # 2. Length-based features
    df['desc_char_count'] = df['clean_description'].str.len()
    df['desc_word_count'] = df['clean_description'].apply(lambda x: len(x.split()) if x else 0)
    df['use_char_count'] = df['clean_use'].str.len()
    df['use_word_count'] = df['clean_use'].apply(lambda x: len(x.split()) if x else 0)
    
    # Average word length (as a simple metric of vocabulary complexity)
    df['desc_avg_word_length'] = df.apply(
        lambda r: r['desc_char_count'] / r['desc_word_count'] if r['desc_word_count'] > 0 else 0, axis=1
    )
    
    # 3. Narrative framing / Keyword features (Social need vs Business investment)
    # Prosocial lenders are often drawn to family, children, health, and basic necessities.
    family_words = r'\b(?:child(?:ren)?|family|son|daughter|mother|father|parent(?:s)?|wife|husband|stud(?:y|ies)|school)\b'
    basic_needs_words = r'\b(?:toilet|sanitary|water|health|medical|disease|electricity|solar|clean|energy|house|housing|roof)\b'
    business_words = r'\b(?:business|shop|store|sell|stock|buy|capital|invest|profit|client|customer|market|sales)\b'
    
    df['has_family_focus'] = df['clean_description'].str.contains(family_words, case=False, na=False).astype(int)
    df['has_basic_needs_focus'] = df['clean_description'].str.contains(basic_needs_words, case=False, na=False).astype(int)
    df['has_business_focus'] = df['clean_description'].str.contains(business_words, case=False, na=False).astype(int)
    
    # Word count of key phrases
    df['family_word_mentions'] = df['clean_description'].apply(lambda x: len(re.findall(family_words, x, flags=re.IGNORECASE)) if x else 0)
    df['basic_needs_word_mentions'] = df['clean_description'].apply(lambda x: len(re.findall(basic_needs_words, x, flags=re.IGNORECASE)) if x else 0)
    df['business_word_mentions'] = df['clean_description'].apply(lambda x: len(re.findall(business_words, x, flags=re.IGNORECASE)) if x else 0)
    
    # 4. Personalization & Pronouns
    # First-person pronouns (I, me, my, we, us, our) vs third-person (he, she, they)
    first_person = r'\b(?:i|me|my|mine|we|us|our|ours)\b'
    third_person = r'\b(?:he|him|his|she|her|hers|they|them|their|theirs)\b'
    
    df['first_person_count'] = df['clean_description'].apply(lambda x: len(re.findall(first_person, x, flags=re.IGNORECASE)) if x else 0)
    df['third_person_count'] = df['clean_description'].apply(lambda x: len(re.findall(third_person, x, flags=re.IGNORECASE)) if x else 0)
    
    # Ratio of first-person (self-reporting) vs third-person (written by field partner)
    df['first_to_third_ratio'] = df.apply(
        lambda r: r['first_person_count'] / (r['third_person_count'] + 1), axis=1
    )
    
    return df

def extract_borrower_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts features related to the borrower's demographics and structure.
    
    Hypotheses:
    1. Group vs Individual: Group loans might fund faster due to lower perceived default risk.
    2. Gender: Female-led loans are heavily favored by microfinance lenders.
    """
    df = df.copy()
    
    # 1. Group Loan indicators
    # Note: Kiva loans can be to individuals or groups of people.
    df['is_group_loan'] = (df['borrowerCount'] > 1).astype(int)
    
    # 2. Gender features
    # Standardize and analyze gender values
    df['borrower_gender_clean'] = df['gender'].str.lower().fillna('unknown')
    
    # Dummy variables for gender
    df['is_female'] = df['borrower_gender_clean'].str.contains('female').astype(int)
    df['is_male'] = ((df['borrower_gender_clean'].str.contains('male')) & (~df['borrower_gender_clean'].str.contains('female'))).astype(int)
    
    # For groups, check female ratio
    # If the format is a comma-separated list like "female, female, male"
    def calculate_female_ratio(gender_str):
        if not isinstance(gender_str, str):
            return 1.0  # Default to female if missing (standard assumption in Kiva)
        genders = [g.strip().lower() for g in gender_str.split(',')]
        females = sum(1 for g in genders if 'female' in g)
        return females / len(genders) if len(genders) > 0 else 0.0
        
    df['female_ratio'] = df['gender'].apply(calculate_female_ratio)
    
    return df

def extract_financial_and_geography_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts numeric and encoded features relating to money, repayment, and local economic conditions.
    
    Hypotheses:
    1. Higher Loan Amount: Takes longer to coordinate and fund.
    2. Higher Country PPP: Slower funding speed, as lenders prioritize lower-income environments.
    """
    df = df.copy()
    
    # 1. Financial transformations
    df['log_loan_amount'] = np.log1p(df['loanAmount'])
    df['monthly_payment_est'] = df['loanAmount'] / df['lenderRepaymentTerm'].replace(0, 1)
    
    # 2. Economic variables
    # Log transform of country purchasing power parity and funds lent
    df['log_country_ppp'] = np.log1p(df['country_ppp'])
    df['log_funds_lent_in_country'] = np.log1p(df['fundsLentInCountry'])
    
    # 3. Categorical encodings (One-hot encoding for sectors and regions)
    sector_dummies = pd.get_dummies(df['sector'], prefix='sector', drop_first=False).astype(int)
    region_dummies = pd.get_dummies(df['region'], prefix='region', drop_first=False).astype(int)
    repayment_dummies = pd.get_dummies(df['repaymentInterval'], prefix='repay', drop_first=False).astype(int)
    
    df = pd.concat([df, sector_dummies, region_dummies, repayment_dummies], axis=1)
    
    return df

def extract_sentiment_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts sentiment and emotional charge scores from the description and use texts
    using NLTK's VADER SentimentIntensityAnalyzer.
    
    Hypotheses:
    1. Positive Appeal: More positive language attracts lenders looking for uplifting stories.
    2. Emotional Intensity: High compound sentiment signals strong emotional framing.
    """
    df = df.copy()
    
    # Initialize VADER analyzer
    try:
        sia = SentimentIntensityAnalyzer()
    except Exception as e:
        print(f"Warning: Sentiment Intensity Analyzer failed to initialize: {e}")
        # Return fallback zeros
        for prefix in ['desc', 'use']:
            df[f'{prefix}_sentiment_compound'] = 0.0
            df[f'{prefix}_sentiment_pos'] = 0.0
            df[f'{prefix}_sentiment_neg'] = 0.0
            df[f'{prefix}_sentiment_neu'] = 1.0
        return df
        
    def get_sentiment_scores(text, prefix):
        if not isinstance(text, str) or len(text.strip()) == 0:
            return {
                f'{prefix}_sentiment_compound': 0.0,
                f'{prefix}_sentiment_pos': 0.0,
                f'{prefix}_sentiment_neg': 0.0,
                f'{prefix}_sentiment_neu': 1.0
            }
        scores = sia.polarity_scores(text)
        return {
            f'{prefix}_sentiment_compound': scores['compound'],
            f'{prefix}_sentiment_pos': scores['pos'],
            f'{prefix}_sentiment_neg': scores['neg'],
            f'{prefix}_sentiment_neu': scores['neu']
        }
        
    # Get scores for description
    desc_scores = df['clean_description'].apply(lambda x: get_sentiment_scores(x, 'desc'))
    desc_scores_df = pd.DataFrame(desc_scores.tolist(), index=df.index)
    
    # Get scores for use description
    use_scores = df['clean_use'].apply(lambda x: get_sentiment_scores(x, 'use'))
    use_scores_df = pd.DataFrame(use_scores.tolist(), index=df.index)
    
    # Concatenate features
    df = pd.concat([df, desc_scores_df, use_scores_df], axis=1)
    
    return df

def extract_topic_features(df: pd.DataFrame, n_topics: int = 5) -> pd.DataFrame:
    """
    Extracts NMF topic proportions from loan descriptions as features.
    
    Hypothesis:
    Certain request themes (like sanitation/toilets) receive rapid funding,
    whereas general retail/farm expansion might take longer.
    """
    df = df.copy()
    
    descriptions = df['clean_description'].fillna("")
    
    # Vectorizer
    vectorizer = TfidfVectorizer(
        max_df=0.95,
        min_df=2,
        stop_words='english',
        lowercase=True,
        ngram_range=(1, 2)
    )
    
    try:
        tfidf = vectorizer.fit_transform(descriptions)
        nmf = NMF(n_components=n_topics, random_state=42, init='nndsvda', max_iter=1000)
        nmf_features = nmf.fit_transform(tfidf)
        
        # Normalize weights
        row_sums = nmf_features.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        nmf_probs = nmf_features / row_sums
        
        for i in range(n_topics):
            df[f'topic_{i}'] = nmf_probs[:, i]
            
    except Exception as e:
        print(f"Warning: Topic extraction failed: {e}")
        for i in range(n_topics):
            df[f'topic_{i}'] = 0.0
            
    return df

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies all feature engineering functions to the Kiva loans dataset.
    
    Args:
        df (pd.DataFrame): Preprocessed DataFrame from data_loader.
        
    Returns:
        pd.DataFrame: Feature-enriched DataFrame.
    """
    df = extract_text_features(df)
    df = extract_sentiment_features(df)
    df = extract_topic_features(df)
    df = extract_borrower_features(df)
    df = extract_financial_and_geography_features(df)
    
    # Select clean numeric features + target for modelling
    # Drop raw text or date columns that cannot go straight into standard ML models
    return df

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
        feat_cols = ['desc_char_count', 'desc_word_count', 'has_family_focus', 'is_group_loan', 'female_ratio', 'log_loan_amount']
        print(df_feat[feat_cols].head(2))
    except Exception as e:
        print(f"Error testing feature builder: {e}")
