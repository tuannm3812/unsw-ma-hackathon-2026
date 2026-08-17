import os
import pickle
import pandas as pd
import numpy as np
from typing import Union, List, Dict, Any
from collections.abc import Sequence

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

def validate_schema(df: pd.DataFrame, required_columns: Sequence[str]) -> None:
    missing = sorted(set(required_columns) - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def prepare_analysis_data(df: pd.DataFrame) -> pd.DataFrame:
    validate_schema(df, ["fundraisingDate", "raisedDate"])
    result = df.copy()
    for column in ["disbursalDate", "fundraisingDate", "raisedDate"]:
        if column in result:
            result[column] = pd.to_datetime(result[column], errors="coerce", utc=True)
    duration = (result["raisedDate"] - result["fundraisingDate"]).dt.total_seconds() / 86400
    result["funding_speed_days"] = duration.where(duration >= 0)
    result["valid_completed_outcome"] = duration.notna() & duration.ge(0)
    result["outcome_issue"] = np.select(
        [result["raisedDate"].isna(), result["fundraisingDate"].isna(), duration.lt(0)],
        ["missing_raised_date", "missing_fundraising_date", "negative_duration"],
        default="",
    )
    result["log_funding_speed"] = np.log1p(result["funding_speed_days"])
    result["funded_within_24h"] = result["funding_speed_days"].le(1).astype("Int64")
    result.loc[~result["valid_completed_outcome"], "funded_within_24h"] = pd.NA
    year = result["fundraisingDate"].dt.year
    result["fundraising_year"] = year.astype("Int64")
    result["fundraising_month"] = result["fundraisingDate"].dt.month.astype("Int64")
    result["analysis_period"] = pd.cut(
        year,
        bins=[2015, 2019, 2021, 2025],
        labels=["pre_pandemic", "pandemic_disruption", "post_pandemic"],
    )
    return result

def preprocess_dates_and_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parses dates and calculates the target variable (funding speed in days).
    Delegates to prepare_analysis_data for backward compatibility.

    Args:
        df (pd.DataFrame): Raw Kiva loans DataFrame.

    Returns:
        pd.DataFrame: Preprocessed DataFrame with datetime columns and target.
    """
    return prepare_analysis_data(df)

def load_and_prepare_data(file_path: str) -> pd.DataFrame:
    """
    Helper function to load and preprocess the Kiva dataset in a single call.

    Args:
        file_path (str): Path to the pickle file.

    Returns:
        pd.DataFrame: Preprocessed DataFrame ready for feature engineering.
    """
    df = load_kiva_pickle(file_path)
    df = prepare_analysis_data(df)
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
