import os
import pandas as pd
try:
    from src.data_loader import load_and_prepare_data
    from src.text_transformer import KivaTopicTransformer
except ModuleNotFoundError:
    from data_loader import load_and_prepare_data
    from text_transformer import KivaTopicTransformer


def extract_topics_nmf(df: pd.DataFrame, n_topics: int = 5, n_top_words: int = 10):
    """
    FULL-SAMPLE EXPLORATORY ANALYSIS ONLY — NOT FOR LEAKAGE-SAFE EVALUATION.

    Fits an NMF (Non-Negative Matrix Factorization) topic model on the entire input
    DataFrame. This is a convenience function for descriptive exploratory analysis,
    where fitting on the full sample is acceptable because the results are never used
    to evaluate held-out predictions. For leakage-safe evaluation, use KivaTopicTransformer
    directly, fitting on training data only and transforming other splits separately.

    Args:
        df (pd.DataFrame): Input DataFrame containing Kiva loans.
        n_topics (int): Number of topics to extract.
        n_top_words (int): Number of top words to show per topic.

    Returns:
        pd.DataFrame: Copy of DataFrame with topic probability columns.
        dict: Mapping from topic index to top words.
    """
    df = df.copy()

    # Extract descriptions (cleaned text already contains the description column)
    descriptions = df['description']

    # Fit transformer on full sample (exploratory use only)
    transformer = KivaTopicTransformer(
        n_topics=n_topics,
        min_df=2,
        random_state=42
    )
    transformer.fit(descriptions)

    # Transform to get topic probabilities
    topic_probs = transformer.transform(descriptions)

    # Get topic keywords
    topic_keywords = transformer.get_topic_terms(n_top_words=n_top_words)

    # Append topic probabilities to DataFrame
    for i in range(n_topics):
        col_name = f'topic_{i}'
        df[col_name] = topic_probs[col_name].values

    # Get dominant topic index
    df['dominant_topic'] = topic_probs.idxmax(axis=1).str.replace('topic_', '').astype(int)

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
