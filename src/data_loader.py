import os
import pickle
import pandas as pd
from typing import Union, List, Dict, Any

def load_kiva_pickle(file_path: str) -> pd.DataFrame:
    """
    Loads Kiva loan data from a pickle file and converts it into a pandas DataFrame.
    
    Args:
        file_path (str): Path to the pickle file.
        
    Returns:
        pd.DataFrame: DataFrame containing the Kiva loans.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Pickle file not found at {file_path}")
        
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
        
    # Convert list of dictionaries to DataFrame if it's not already
    if isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, pd.DataFrame):
        df = data
    else:
        raise ValueError(f"Unexpected data type in pickle file: {type(data)}")
        
    return df

def preprocess_dates_and_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parses dates and calculates the target variable (funding speed in days).
    
    Args:
        df (pd.DataFrame): Raw Kiva loans DataFrame.
        
    Returns:
        pd.DataFrame: Preprocessed DataFrame with datetime columns and target.
    """
    df = df.copy()
    
    # Parse date columns to datetime
    date_cols = ['disbursalDate', 'fundraisingDate', 'raisedDate']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
    # Calculate funding speed (target variable) in days
    # funding speed = raisedDate - fundraisingDate
    if 'raisedDate' in df.columns and 'fundraisingDate' in df.columns:
        # Convert difference to float days
        df['funding_speed_days'] = (df['raisedDate'] - df['fundraisingDate']).dt.total_seconds() / (24 * 3600)
        
    return df

def load_and_prepare_data(file_path: str) -> pd.DataFrame:
    """
    Helper function to load and preprocess the Kiva dataset in a single call.
    
    Args:
        file_path (str): Path to the pickle file.
        
    Returns:
        pd.DataFrame: Preprocessed DataFrame ready for feature engineering.
    """
    df = load_kiva_pickle(file_path)
    df = preprocess_dates_and_target(df)
    return df

if __name__ == "__main__":
    # Test data loader
    default_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Kiva_Loans_Sample.pkl")
    try:
        df = load_and_prepare_data(default_path)
        print(f"Successfully loaded Kiva loans data sample!")
        print(f"Shape: {df.shape}")
        if 'funding_speed_days' in df.columns:
            print(f"Mean funding speed (days): {df['funding_speed_days'].mean():.2f}")
    except Exception as e:
        print(f"Error testing data loader: {e}")
