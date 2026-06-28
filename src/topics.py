import os
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF, LatentDirichletAllocation
try:
    from src.data_loader import load_and_prepare_data
except ModuleNotFoundError:
    from data_loader import load_and_prepare_data

def extract_topics_nmf(df: pd.DataFrame, n_topics: int = 5, n_top_words: int = 10):
    """
    Fits an NMF (Non-Negative Matrix Factorization) topic model on loan descriptions.
    Extracts topic mixture probabilities and names them based on top terms.
    
    Args:
        df (pd.DataFrame): Input DataFrame containing Kiva loans.
        n_topics (int): Number of topics to extract.
        n_top_words (int): Number of top words to show per topic.
        
    Returns:
        pd.DataFrame: Copy of DataFrame with topic probability columns.
        dict: Mapping from topic index to top words.
    """
    df = df.copy()
    
    # 1. Clean descriptions
    # We clean html and fillna
    try:
        from src.features import clean_html
    except ModuleNotFoundError:
        from features import clean_html
    descriptions = df['description'].apply(clean_html).fillna("")
    
    # 2. Vectorize text using TF-IDF (removing standard English stop words)
    vectorizer = TfidfVectorizer(
        max_df=0.95,
        min_df=2,
        stop_words='english',
        lowercase=True,
        ngram_range=(1, 2)
    )
    tfidf = vectorizer.fit_transform(descriptions)
    
    # 3. Fit NMF Model
    nmf = NMF(
        n_components=n_topics,
        random_state=42,
        init='nndsvda',
        max_iter=1000
    )
    nmf_features = nmf.fit_transform(tfidf)
    
    # Normalize topic weights per row so they sum to 1 (probability distribution)
    row_sums = nmf_features.sum(axis=1, keepdims=True)
    # Avoid division by zero
    row_sums[row_sums == 0] = 1.0
    nmf_probs = nmf_features / row_sums
    
    # 4. Extract top words for each topic
    feature_names = vectorizer.get_feature_names_out()
    topic_keywords = {}
    
    for topic_idx, topic in enumerate(nmf.components_):
        top_features_ind = topic.argsort()[:-n_top_words - 1:-1]
        top_words = [feature_names[i] for i in top_features_ind]
        topic_keywords[topic_idx] = top_words
        
    # 5. Append topic probabilities to DataFrame
    topic_cols = []
    for i in range(n_topics):
        col_name = f'topic_{i}'
        df[col_name] = nmf_probs[:, i]
        topic_cols.append(col_name)
        
    # Get dominant topic index
    df['dominant_topic'] = nmf_probs.argmax(axis=1)
    
    return df, topic_keywords

def analyze_topics_speed(df_topics: pd.DataFrame, topic_keywords: dict):
    """
    Prints summary statistics and average funding speed for each dominant topic.
    """
    print("\n--- Topic Speed Analysis ---")
    print("Dominant Topic Distribution and Mean Funding Speed:")
    
    # Group by dominant topic and compute statistics
    summary = df_topics.groupby('dominant_topic').agg(
        count=('funding_speed_days', 'count'),
        mean_speed=('funding_speed_days', 'mean'),
        median_speed=('funding_speed_days', 'median')
    ).reset_index()
    
    for idx, row in summary.iterrows():
        topic_num = int(row['dominant_topic'])
        keywords = ", ".join(topic_keywords[topic_num][:5])
        print(f"\nTopic {topic_num} (Top Keywords: {keywords}):")
        print(f"  - Count of Loans: {int(row['count'])}")
        print(f"  - Mean Funding Speed: {row['mean_speed']:.2f} days")
        print(f"  - Median Funding Speed: {row['median_speed']:.2f} days")

if __name__ == "__main__":
    # Test topic modeling script
    default_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Kiva_Loans_Sample.pkl")
    try:
        df = load_and_prepare_data(default_path)
        df_topics, keywords = extract_topics_nmf(df, n_topics=5)
        print("Successfully extracted 5 topics!")
        for idx, words in keywords.items():
            print(f"Topic {idx}: {', '.join(words)}")
            
        analyze_topics_speed(df_topics, keywords)
    except Exception as e:
        print(f"Error testing topic modeling: {e}")
