# %% [markdown]
# # UNSW Marketing Analytics Hackathon 2026 - Starter EDA & Baseline
# This notebook/script serves as a starter template for analyzing the Kiva loans dataset 
# and building a baseline model to predict **funding speed** (raisedDate - fundraisingDate).
# 
# **Goal of the Hackathon:**
# Identify key factors that influence lender decision-making and funding speed 
# within "subsistence marketplaces."

# %%
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Add src/ to path so we can import helper modules
sys.path.append(os.path.abspath('../'))
from src.data_loader import load_and_prepare_data
from src.features import build_features
from src.modeling import run_baseline_model

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12

# %% [markdown]
# ## 1. Load the Kiva Loans Sample
# We will use the helper functions in `src/data_loader.py` to load the pickle file 
# and compute the target variable: `funding_speed_days`.

# %%
pkl_path = "../data/Kiva_Loans_Sample.pkl"
df = load_and_prepare_data(pkl_path)
print(f"Dataset shape: {df.shape}")
df.head(2)

# %% [markdown]
# ## 2. Exploratory Data Analysis (EDA)
# Let's inspect the target variable: `funding_speed_days`.

# %%
# Target Summary Stats
print("--- Funding Speed (Days) Summary Statistics ---")
print(df['funding_speed_days'].describe())

# Plot Distribution
plt.figure()
sns.histplot(df['funding_speed_days'], kde=True, bins=20, color='darkblue')
plt.title('Distribution of Funding Speed (Days)')
plt.xlabel('Funding Speed (Days)')
plt.ylabel('Count')
plt.show()

# Log Target Distribution (highly right-skewed)
plt.figure()
sns.histplot(np.log1p(df['funding_speed_days']), kde=True, bins=20, color='teal')
plt.title('Distribution of Log(Funding Speed + 1)')
plt.xlabel('Log(Funding Speed in Days)')
plt.ylabel('Count')
plt.show()

# %% [markdown]
# ### 2.1 Loan Amount vs. Funding Speed
# Let's see if larger loans take longer to get funded.

# %%
plt.figure()
sns.scatterplot(data=df, x='loanAmount', y='funding_speed_days', hue='region', alpha=0.8, s=80)
plt.title('Loan Amount vs. Funding Speed by Region')
plt.xlabel('Loan Amount ($)')
plt.ylabel('Funding Speed (Days)')
plt.show()

# Correlation
corr = df['loanAmount'].corr(df['funding_speed_days'])
print(f"Correlation between Loan Amount and Funding Speed: {corr:.3f}")

# %% [markdown]
# ### 2.2 Sector and Repayment Term vs. Funding Speed
# Prosocial lenders might prioritize specific sectors (e.g., Education, Health) or prefer shorter repayment periods.

# %%
# Sector boxplot
plt.figure(figsize=(12, 6))
order = df.groupby('sector')['funding_speed_days'].median().sort_values().index
sns.boxplot(data=df, x='sector', y='funding_speed_days', order=order, palette='viridis')
plt.title('Funding Speed by Loan Sector')
plt.xticks(rotation=45, ha='right')
plt.ylabel('Funding Speed (Days)')
plt.tight_layout()
plt.show()

# Repayment term vs. Funding speed
plt.figure()
sns.regplot(data=df, x='lenderRepaymentTerm', y='funding_speed_days', scatter_kws={'alpha':0.6}, line_kws={'color':'red'})
plt.title('Repayment Term vs. Funding Speed')
plt.xlabel('Repayment Term (Months)')
plt.ylabel('Funding Speed (Days)')
plt.show()

# %% [markdown]
# ### 2.3 Gender & Group Loans
# Does the borrower gender or group structure affect funding speed?

# %%
# Group vs Individual
df['is_group'] = df['borrowerCount'] > 1
plt.figure()
sns.boxplot(data=df, x='is_group', y='funding_speed_days', palette='pastel')
plt.title('Funding Speed: Individual vs. Group Loans')
plt.xlabel('Is Group Loan?')
plt.ylabel('Funding Speed (Days)')
plt.xticks([0, 1], ['Individual', 'Group'])
plt.show()

# Female ratio vs Funding speed
# (We parse gender to get female ratio)
from src.features import extract_borrower_features
df_gender = extract_borrower_features(df)

plt.figure()
sns.scatterplot(data=df_gender, x='female_ratio', y='funding_speed_days', alpha=0.7, s=100)
plt.title('Female Borrower Ratio vs. Funding Speed')
plt.xlabel('Female Borrower Ratio (0 = All Male, 1 = All Female)')
plt.ylabel('Funding Speed (Days)')
plt.show()

# %% [markdown]
# ## 3. Feature Engineering and Narrative (Text) Analysis
# Kiva loans include description and use texts. The narrative quality and framing 
# (e.g. personal, family-focused, business-focused) represent key marketing levers.

# %%
# Apply feature engineering
df_feat = build_features(df)

# Plot word count vs funding speed
plt.figure()
sns.regplot(data=df_feat, x='desc_word_count', y='funding_speed_days', scatter_kws={'alpha':0.6}, line_kws={'color':'purple'})
plt.title('Description Word Count vs. Funding Speed')
plt.xlabel('Word Count')
plt.ylabel('Funding Speed (Days)')
plt.show()

# Check family focus vs business focus
plt.figure()
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
sns.boxplot(ax=axes[0], data=df_feat, x='has_family_focus', y='funding_speed_days', palette='Set2')
axes[0].set_title('Funding Speed by Family/Need Focus')
axes[0].set_xticklabels(['No Mention', 'Mentioned'])

sns.boxplot(ax=axes[1], data=df_feat, x='has_business_focus', y='funding_speed_days', palette='Set2')
axes[1].set_title('Funding Speed by Business Focus')
axes[1].set_xticklabels(['No Mention', 'Mentioned'])
plt.show()

# %% [markdown]
# ### 3.1 Narrative Sentiment Analysis (VADER)
# Let's explore how the sentiment (emotional tone) of the borrower's description 
# relates to funding speed. We look at the VADER compound sentiment score, which 
# ranges from -1 (extremely negative) to +1 (extremely positive).

# %%
# Plot Sentiment Distribution
plt.figure()
sns.histplot(df_feat['desc_sentiment_compound'], kde=True, bins=15, color='orange')
plt.title('Distribution of Description Compound Sentiment')
plt.xlabel('Compound Sentiment Score')
plt.ylabel('Count')
plt.show()

# Scatter plot: Sentiment vs Funding Speed
plt.figure()
sns.regplot(data=df_feat, x='desc_sentiment_compound', y='funding_speed_days', scatter_kws={'alpha':0.6}, line_kws={'color':'red'})
plt.title('Description Sentiment vs. Funding Speed')
plt.xlabel('Description Compound Sentiment')
plt.ylabel('Funding Speed (Days)')
plt.show()

# Correlation
sentiment_corr = df_feat['desc_sentiment_compound'].corr(df_feat['funding_speed_days'])
print(f"Correlation between Description Sentiment and Funding Speed: {sentiment_corr:.3f}")

# %% [markdown]
# ### 3.2 Narrative Topic Modeling (NMF)
# Let's extract hidden themes (topics) from the loan descriptions using Non-Negative Matrix 
# Factorization (NMF) and see how the theme of the request affects its funding speed.

# %%
from src.topics import extract_topics_nmf, analyze_topics_speed
df_topics, topic_keywords = extract_topics_nmf(df, n_topics=5)

# Print topics and keywords
for idx, words in topic_keywords.items():
    print(f"Topic {idx} Top Words: {', '.join(words[:6])}")

# Print mean speed per dominant topic
analyze_topics_speed(df_topics, topic_keywords)

# Boxplot of dominant topic vs funding speed
plt.figure(figsize=(10, 6))
# Create labels for boxplot x-axis using the first 3 keywords
labels = [f"Topic {i}\n({', '.join(words[:3])})" for i, words in topic_keywords.items()]
sns.boxplot(data=df_topics, x='dominant_topic', y='funding_speed_days', palette='Set3')
plt.xticks(ticks=range(5), labels=labels, rotation=30, ha='right')
plt.title('Funding Speed by Dominant Loan Topic')
plt.xlabel('Dominant Topic')
plt.ylabel('Funding Speed (Days)')
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 4. Baseline Modeling & Feature Influence
# Let's run the modeling pipeline to predict funding speed and look at the variables 
# that are most predictive of speed.

# %%
X, y, ridge_model, rf_model = run_baseline_model(pkl_path)

# %% [markdown]
# ### 4.1 Feature Importances (Random Forest)
# Visualize which variables have the highest predictive power for funding speed.

# %%
importances = pd.DataFrame({
    'Feature': X.columns,
    'Importance': rf_model.feature_importances_
}).sort_values(by='Importance', ascending=False)

plt.figure(figsize=(10, 8))
sns.barplot(data=importances.head(15), x='Importance', y='Feature', palette='crest')
plt.title('Top 15 Most Important Features (Random Forest)')
plt.xlabel('Feature Importance')
plt.ylabel('Feature')
plt.show()

# %% [markdown]
# ## 5. Statistical Hypothesis Testing (OLS Regression)
# While machine learning baseline models show feature predictive importance, fitting an OLS 
# (Ordinary Least Squares) regression allows us to officially calculate p-values and verify 
# which features have statistically significant effects on funding speed.

# %%
import statsmodels.api as sm
from src.statistical_analysis import run_ols_analysis

reports_dir = "../reports"
results = run_ols_analysis(pkl_path, reports_dir)

# %% [markdown]
# ## Next Steps for the Hackathon:
# 1. **Interaction Effects**: Check if the impact of narrative framing (e.g. sentiment or family focus) varies across regions/sectors. For example, does positive sentiment matter more in Africa or Asia?
# 2. **Topic Modeling**: Use LDA (Latent Dirichlet Allocation) to extract topics from descriptions (e.g. farming, education, emergency) and see how topic mix affects speed.
# 3. **Advanced Models**: Try LightGBM, XGBoost, or CatBoost, tuning hyperparameters using cross-validation.
# 4. **Additional Text Features**: Score readability (Flesch-Kincaid) or check for specific stylistic metrics like punctuation (exclamations, question marks).

