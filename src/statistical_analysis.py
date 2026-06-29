import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
try:
    from src.data_loader import load_and_prepare_data
    from src.features import build_features
except ModuleNotFoundError:
    from data_loader import load_and_prepare_data
    from features import build_features

def run_ols_analysis(pkl_path: str, report_dir: str):
    """
    Performs an Ordinary Least Squares (OLS) regression analysis using Statsmodels.
    Evaluates the statistical significance of financial, demographic, narrative, 
    and topic features in explaining Kiva loan funding speed.
    """
    # 1. Load data and extract features
    print("Loading data and building features...")
    df = load_and_prepare_data(pkl_path)
    df_feat = build_features(df)
    
    # 2. Select variables for statistical testing (dependent and independent)
    # Dependent variable: funding speed in days
    y = df_feat['funding_speed_days'].fillna(df_feat['funding_speed_days'].median())
    
    # Independent variables (Key hypotheses testing columns)
    # Note: We select representative columns from each category to avoid high multicollinearity.
    independent_vars = [
        # Financial Term Structure
        'log_loan_amount',          # Is larger loan amount slower?
        'lenderRepaymentTerm',      # Does longer term slow funding?
        'repay_monthly',            # Reference is other repayment intervals
        
        # Demographics
        'is_group_loan',            # Are group loans funded faster?
        'female_ratio',             # Are women-led loans funded faster?
        
        # Economic Context
        'log_country_ppp',          # Do poorer countries (lower ppp) fund faster?
        
        # Narrative Style & Sentiment
        'desc_word_count',          # Does description length increase cognitive load?
        'first_to_third_ratio',     # Does first-person narrative increase authenticity?
        'desc_sentiment_compound',  # Does positive emotional appeal speed up funding?
        
        # Latent Topics (NMF Proportions)
        'topic_0',                  # Micro-retail in Philippines
        'topic_2',                  # Sanitary toilet necessity
        'topic_3',                  # Farming & agriculture
        'topic_4'                   # Sustaining family business
        # Note: Topic 1 is omitted as the reference category to prevent collinearity
    ]
    
    X = df_feat[independent_vars].copy()
    
    # Fill missing values with median/0
    for col in X.columns:
        X[col] = X[col].fillna(0)
        
    # Add a constant (intercept) to the model
    X_with_const = sm.add_constant(X)
    
    # 3. Fit OLS regression
    print("Fitting OLS Regression model...")
    model = sm.OLS(y, X_with_const)
    results = model.fit()
    
    # 4. Generate summary
    summary_text = results.summary().as_text()
    print("\n--- OLS Regression Analysis Summary ---")
    print(summary_text)
    
    # 5. Extract significant variables (p < 0.05)
    p_values = results.pvalues
    coefs = results.params
    std_errors = results.bse
    
    significant_vars = p_values[p_values < 0.05].index.tolist()
    
    print("\n--- Statistical Significance Highlights (p < 0.05) ---")
    if not significant_vars:
        print("No variables are statistically significant at the 95% confidence level (typical for small samples).")
    else:
        for var in significant_vars:
            if var == 'const':
                continue
            sig_status = "Negative Coefficient (Speeds up funding)" if coefs[var] < 0 else "Positive Coefficient (Slows funding)"
            print(f" * {var}: p-value = {p_values[var]:.4f} | Coef = {coefs[var]:.4f} ({sig_status})")
            
    # 6. Save results to reports directory
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "statistical_summary.txt")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("UNSW Marketing Analytics Hackathon 2026 - Statistical Analysis Report\n")
        f.write("========================================================================\n\n")
        f.write("Hypotheses Testing on Kiva Funding Speed (raisedDate - fundraisingDate)\n")
        f.write(f"Sample Size: {len(df)} loans\n\n")
        f.write("OLS Regression Summary Table:\n")
        f.write("-----------------------------\n")
        f.write(summary_text)
        f.write("\n\nSignificant Variables Interpretation:\n")
        f.write("-------------------------------------\n")
        if not significant_vars:
            f.write("No variables found statistically significant at p < 0.05 level on this sample.\n")
        else:
            for var in significant_vars:
                if var == 'const':
                    continue
                direction = "faster funding (speeds up)" if coefs[var] < 0 else "slower funding (delays)"
                f.write(f"- Variable '{var}' has a significant effect (p = {p_values[var]:.4f}).\n")
                f.write(f"  A unit increase in '{var}' changes the funding time by {coefs[var]:.2f} days, leading to {direction}.\n\n")
                
    print(f"\nReport successfully saved to: {report_path}")
    return results

if __name__ == "__main__":
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(src_dir)
    pkl_path = os.path.join(project_root, "data", "Kiva_Loans_Sample.pkl")
    report_dir = os.path.join(project_root, "reports")
    
    run_ols_analysis(pkl_path, report_dir)
