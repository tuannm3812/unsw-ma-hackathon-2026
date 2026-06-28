import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb

from data_loader import load_and_prepare_data
from features import build_features

def run_advanced_cv_modeling(pkl_path: str):
    """
    Runs a 5-Fold Cross-Validation pipeline using LightGBM and XGBoost models.
    Saves evaluations and compares performance to baseline models.
    """
    # 1. Load data & extract features
    print("Loading and preparing data...")
    df = load_and_prepare_data(pkl_path)
    df_feat = build_features(df)
    
    # 2. Define features & target
    target_col = 'funding_speed_days'
    exclude_cols = [
        'id', 'status', 'name', 'gender', 'repaymentInterval', 'sector', 'activity', 
        'use', 'city', 'country_iso', 'country_name', 'region', 'description', 
        'whySpecial', 'image_url', 'disbursalDate', 'fundraisingDate', 'raisedDate',
        'clean_description', 'clean_use', 'borrower_gender_clean', target_col
    ]
    feature_cols = [col for col in df_feat.columns if col not in exclude_cols]
    
    X = df_feat[feature_cols].select_dtypes(include=[np.number]).fillna(0)
    y = df_feat[target_col].fillna(df_feat[target_col].median())
    
    print(f"Dataset Size: {X.shape[0]} samples, {X.shape[1]} features.")
    
    # 3. Setup K-Fold Cross Validation
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    xgb_maes, xgb_rmses, xgb_r2s = [], [], []
    lgb_maes, lgb_rmses, lgb_r2s = [], [], []
    
    print("\n--- Training Models with 5-Fold Cross-Validation ---")
    
    for fold, (train_idx, val_idx) in enumerate(kf.split(X, y)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        # XGBoost
        xgb_model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            random_state=42,
            n_jobs=-1
        )
        xgb_model.fit(X_train, y_train)
        y_pred_xgb = xgb_model.predict(X_val)
        
        xgb_maes.append(mean_absolute_error(y_val, y_pred_xgb))
        xgb_rmses.append(np.sqrt(mean_squared_error(y_val, y_pred_xgb)))
        xgb_r2s.append(r2_score(y_val, y_pred_xgb))
        
        # LightGBM
        lgb_model = lgb.LGBMRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        lgb_model.fit(X_train, y_train)
        y_pred_lgb = lgb_model.predict(X_val)
        
        lgb_maes.append(mean_absolute_error(y_val, y_pred_lgb))
        lgb_rmses.append(np.sqrt(mean_squared_error(y_val, y_pred_lgb)))
        lgb_r2s.append(r2_score(y_val, y_pred_lgb))
        
        print(f"Fold {fold+1} | XGB MAE: {xgb_maes[-1]:.3f} | LGB MAE: {lgb_maes[-1]:.3f}")
        
    # 4. Summary metrics
    print("\n--- CV Results Summary ---")
    print(f"XGBoost  - Mean MAE: {np.mean(xgb_maes):.4f} +/- {np.std(xgb_maes):.4f}")
    print(f"XGBoost  - Mean RMSE: {np.mean(xgb_rmses):.4f} +/- {np.std(xgb_rmses):.4f}")
    print(f"XGBoost  - Mean R2: {np.mean(xgb_r2s):.4f} +/- {np.std(xgb_r2s):.4f}")
    
    print(f"LightGBM - Mean MAE: {np.mean(lgb_maes):.4f} +/- {np.std(lgb_maes):.4f}")
    print(f"LightGBM - Mean RMSE: {np.mean(lgb_rmses):.4f} +/- {np.std(lgb_rmses):.4f}")
    print(f"LightGBM - Mean R2: {np.mean(lgb_r2s):.4f} +/- {np.std(lgb_r2s):.4f}")
    
    # 5. Fit final models on full dataset to analyze feature importances
    xgb_full = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42, n_jobs=-1)
    xgb_full.fit(X, y)
    
    importances = pd.DataFrame({
        'Feature': X.columns,
        'Importance': xgb_full.feature_importances_
    }).sort_values(by='Importance', ascending=False)
    
    print("\nTop 10 XGBoost Feature Importances:")
    print(importances.head(10).to_string(index=False))
    
    return X, y, xgb_full, importances

if __name__ == "__main__":
    default_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Kiva_Loans_Sample.pkl")
    run_advanced_cv_modeling(default_path)
