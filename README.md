# UNSW Marketing Analytics Hackathon Challenge 2026

Welcome to the starter repository for the **UNSW Marketing Analytics Hackathon Challenge 2026**! 

This challenge focuses on **prosocial crowdfunding** using loan-level data from the micro-lending platform **Kiva** (spanning 2016 to 2025). The core objective is to identify key factors that influence lender decision-making and **funding speed** (how fast a loan is fully raised) within subsistence marketplaces.

---

## 🎯 The Challenge & Objectives

Prosocial lending platforms like Kiva allow micro-entrepreneurs in emerging and subsistence markets to raise funding. Unlike traditional financial systems, lenders on Kiva are driven by social impact (prosocial motives) rather than financial return.

Your task is to analyze how different factors affect the **funding speed**:
$$\text{funding\_speed\_days} = \text{raisedDate} - \text{fundraisingDate}$$

### Key Research Questions & Hypotheses
1. **Persuasive Communication & Narrative Styling**: How does the framing of the borrower's story (`description`, `use`, `whySpecial`) affect lending decisions? Does a focus on family, children, health, or basic needs lead to faster funding compared to a purely business-centric narrative?
2. **Borrower Demographics**: Do female-led loans or collective group loans (`borrowerCount > 1`) get funded faster? (Traditional microfinance heavily favors female groups due to perceived reliability and high social impact).
3. **Financial Term Structures**: How does the requested loan amount (`loanAmount`) and the repayment schedule (`lenderRepaymentTerm`, `repaymentInterval`) influence lender patience?
4. **Geographic & Macroeconomic Context**: Do lenders prioritize loans from poorer countries (lower `country_ppp`) or regions with lower historical funding volumes?

---

## 📂 Repository Structure

The project has been organized into a clean, modular structure:

```
unsw-ma-hackathon-2026/
├── data/                       # Directory for raw and processed datasets (ignored in git)
├── notebooks/
│   ├── starter_eda.ipynb      # Jupyter Notebook for EDA, visualizations, and modeling
│   └── starter_eda.py         # Percent-format script counterpart for VS Code / Spyder
├── src/
│   ├── __init__.py            # Marks src/ as a python package
│   ├── data_loader.py         # Loads pickle, parses dates, and computes target variable
│   ├── features.py            # Feature engineering (NLP metrics, demographics, encodings)
│   └── modeling.py            # Baseline modeling pipeline (Ridge, Random Forest)
├── .gitignore                  # Prevents committing large data files/virtual environments
├── requirements.txt            # Python dependencies
└── README.md                   # Project overview and setup instructions (This file)
```

---

## 🛠️ Setup & Installation

### 1. Prerequisites
Ensure you have Python 3.9+ installed.

### 2. Clone and Setup Environment
Navigate to the repository folder and create a virtual environment:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Windows Command Prompt:
.venv\Scripts\activate.bat
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
Install all required libraries (includes `pandas`, `scikit-learn`, `matplotlib`, `seaborn`, `openpyxl`, `xgboost`, `lightgbm`, etc.):

```bash
pip install -r requirements.txt
```

---

## 🚀 How to Run the Starter Code

### Running the Jupyter Notebook
You can open and execute the starter notebook:
```bash
jupyter notebook notebooks/starter_eda.ipynb
```
Or simply open [starter_eda.ipynb](file:///F:/drive_tuannm3812/My%20Drive/10_Github/4.%20Training/unsw-ma-hackathon-2026/notebooks/starter_eda.ipynb) in **VS Code** and click **Run All**.

### Running the Scripts directly
You can execute the baseline model pipeline from the terminal to see immediate outputs:
```bash
python src/modeling.py
```

---

## 📊 Features Engineered in the Starter Code

The [features.py](file:///F:/drive_tuannm3812/My%20Drive/10_Github/4.%20Training/unsw-ma-hackathon-2026/src/features.py) file automatically extracts features aligned with marketing analytics theory:

| Feature Category | Features Extracted | Marketing / Prosocial Hypothesis |
| :--- | :--- | :--- |
| **Narrative Framing (NLP)** | Word/Char Count, Average Word Length, HTML tags count | Longer narratives might reveal transparency but increase cognitive load for lenders. |
| **Narrative Focus** | `has_family_focus`, `has_basic_needs_focus`, `has_business_focus` | Prosocial lenders are drawn to stories mentioning children, study, health, and clean water. |
| **Narrative Style** | `first_person_count`, `third_person_count`, `first_to_third_ratio` | First-person stories (written by borrower) feel more authentic than third-person profiles written by partners. |
| **Demographics** | `is_group_loan`, `female_ratio`, `is_female`, `is_male` | Female borrowers and group structures receive faster funding due to lower perceived credit risk. |
| **Financial & Terms** | `log_loan_amount`, `monthly_payment_est`, Repayment Interval dummy | Larger amounts take longer to coordinate; irregular repayments increase lender hesitation. |
| **Economic Context** | `log_country_ppp`, `log_funds_lent_in_country` | Low-GDP regions (low PPP) are prioritized due to higher perceived social need. |

---

## 💡 Recommended Next Steps for the Competition
* **Sentiment Analysis**: Use the `nltk` package to analyze emotional charge (valence) in borrower descriptions.
* **Topic Modeling (LDA)**: Uncover latent themes (e.g. agricultural machinery vs. emergency family medical bills) to determine how they affect funding speed.
* **Model Optimization**: Train and optimize `XGBoost` or `LightGBM` models, performing hyperparameter tuning using cross-validation.
* **Data Dictionary**: Reference the [Kiva Data Dictionary.xlsx](file:///F:/drive_tuannm3812/My%20Drive/10_Github/4.%20Training/unsw-ma-hackathon-2026/Kiva%20Data%20Dictionary.xlsx) for the full schema details.
