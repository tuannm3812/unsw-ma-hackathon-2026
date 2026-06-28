import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, KFold
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    from src.data_loader import load_and_prepare_data
    from src.features import build_features
except ModuleNotFoundError:
    from data_loader import load_and_prepare_data
    from features import build_features


def run_baseline_model(pkl_path: str):
    """
    Runs a baseline modeling pipeline to predict funding speed (in days)
    and prints feature importances / coefficients.
    """
    # 1. Load and process data
    print("Loading and preprocessing data...")
    df = load_and_prepare_data(pkl_path)
    
    # 2. Build features
    print("Building features...")
    df_feat = build_features(df)
    
    # 3. Define target and feature columns
    target_col = 'funding_speed_days'
    
    # Exclude non-numeric and raw metadata columns
    exclude_cols = [
        'id', 'status', 'name', 'gender', 'repaymentInterval', 'sector', 'activity', 
        'use', 'city', 'country_iso', 'country_name', 'region', 'description', 
        'whySpecial', 'image_url', 'disbursalDate', 'fundraisingDate', 'raisedDate',
        'clean_description', 'clean_use', 'borrower_gender_clean', target_col
    ]
    
    feature_cols = [col for col in df_feat.columns if col not in exclude_cols]
    
    # Ensure all features are numeric
    X = df_feat[feature_cols].select_dtypes(include=[np.number]).fillna(0)
    y = df_feat[target_col].fillna(df_feat[target_col].median())
    
    print(f"Number of features selected for modeling: {X.shape[1]}")
    print(f"Number of records: {X.shape[0]}")
    
    # 4. Train/Test Split (using 80-20 split since sample is small)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 5. Ridge Regression Baseline
    print("\n--- Training Ridge Regression Model ---")
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train, y_train)
    
    # Evaluate
    y_pred_train = ridge.predict(X_train)
    y_pred_test = ridge.predict(X_test)
    
    print("Train MAE:  ", f"{mean_absolute_error(y_train, y_pred_train):.4f}")
    print("Test MAE:   ", f"{mean_absolute_error(y_test, y_pred_test):.4f}")
    print("Test RMSE:  ", f"{np.sqrt(mean_squared_error(y_test, y_pred_test)):.4f}")
    print("Test R2:    ", f"{r2_score(y_test, y_pred_test):.4f}")
    
    # Print Top Coefficients
    coef_df = pd.DataFrame({
        'Feature': X.columns,
        'Coefficient': ridge.coef_
    })
    coef_df['Abs_Coefficient'] = coef_df['Coefficient'].abs()
    coef_df = coef_df.sort_values(by='Abs_Coefficient', ascending=False)
    
    print("\nTop 10 Ridge Regression Coefficients (Influence on funding speed):")
    print("(Positive coefficient = increases funding time / slows funding)")
    print("(Negative coefficient = decreases funding time / speeds up funding)")
    print(coef_df[['Feature', 'Coefficient']].head(10).to_string(index=False))
    
    # 6. Random Forest Baseline
    print("\n--- Training Random Forest Regressor ---")
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    
    # Evaluate
    y_pred_rf = rf.predict(X_test)
    print("Test MAE:   ", f"{mean_absolute_error(y_test, y_pred_rf):.4f}")
    print("Test RMSE:  ", f"{np.sqrt(mean_squared_error(y_test, y_pred_rf)):.4f}")
    print("Test R2:    ", f"{r2_score(y_test, y_pred_rf):.4f}")
    
    # Print Feature Importances
    importances = pd.DataFrame({
        'Feature': X.columns,
        'Importance': rf.feature_importances_
    }).sort_values(by='Importance', ascending=False)
    
    print("\nTop 10 Random Forest Feature Importances:")
    print(importances.head(10).to_string(index=False))
    
    return X, y, ridge, rf

if __name__ == "__main__":
    default_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Kiva_Loans_Sample.pkl")
    run_baseline_model(default_path)
