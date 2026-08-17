"""
Robust explanatory (inferential) models of Kiva funding speed and 24-hour
funding, using statsmodels OLS/GLM with heteroskedasticity-robust (HC3)
standard errors.

This module is deliberately separate from `src/modeling.py`: that module
fits leakage-safe *predictive* models on a chronological train/holdout
split and reports out-of-sample accuracy. This module fits *explanatory*
(association) models on every valid, completed loan - there is no
train/holdout split here because the goal is not out-of-sample prediction,
it is a robust-uncertainty description of how pre-specified predictors are
associated with funding speed and 24-hour funding across the whole sample.

Two hard constraints from the project's ethics/quality bar, both enforced
directly in code (not just in prose):

  1. Never impute a missing outcome. Only rows with `valid_completed_outcome`
     are used for the duration (OLS) model; only rows with a non-null
     `funded_within_24h` are used for the binary (GLM) model. Rows with an
     invalid/missing outcome are excluded, never filled with a mean/median.
  2. Report association, never causal, language. `format_association_summary`
     always says "associated with" and never "causes"/"effect"/"proves", and
     it reports every pre-specified coefficient with a 95% CI - not only the
     ones with p < 0.05.

A structural wrinkle worth documenting explicitly: `sentiment_available`
(and, when the VADER lexicon is not installed, `desc_sentiment_compound`
too) is a *dataset-level* flag from `src/features.py`, not a per-row one -
every row in a single call gets the same value, because it just records
whether the VADER lexicon happened to be available on the machine that ran
feature extraction. A literal constant column is exactly collinear with the
intercept (or, if it happens to be all zero, contributes nothing but still
inflates the column count) - so unconditionally including it would make the
model rank-deficient by construction, on every machine where VADER is
consistently present or consistently absent, regardless of sample size.
`_select_available_terms` below prunes any pre-specified term that turns out
to be constant (no variation) in the *specific* modeling sample before the
formula is built, and records what was dropped and why in the returned
dict. The rank check that follows is a safety net for anything not caught
by that pruning (e.g. a categorical level with zero observations, or a
sample that is simply too small), not a substitute for it.
"""

import os
import re

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm

try:
    from src.data_loader import load_kiva_pickle, prepare_analysis_data
    from src.features import extract_deterministic_features
except ModuleNotFoundError:
    from data_loader import load_kiva_pickle, prepare_analysis_data
    from features import extract_deterministic_features


# Pre-specified predictors for both the duration and 24-hour models, per the
# task brief. Framing measures are the per-100-word rates (not raw counts)
# so they are comparable across descriptions of different lengths.
#
# Of the eight available framing measures in `src/features.py`, three are
# selected here as theoretically distinct, established dimensions of
# crowdfunding narrative framing rather than an arbitrary subset:
#   - family_mentions_per_100_words:  communal/relatedness framing
#   - agency_mentions_per_100_words:  agentic/competence framing
#   - urgency_mentions_per_100_words: urgency/need framing
# (Kiva narrative research - e.g. Moss, Neubaum & Meyskens (2015) on
# borrower legitimacy narratives - repeatedly distinguishes communal and
# agentic framing as separate constructs; urgency is added as a third,
# distinct appeal to time pressure.) The remaining five (basic_needs,
# business, gratitude, first_person, third_person) are left out to keep the
# formula compact and reduce collinearity among highly related counts
# (e.g. first/third person overlap heavily with the pronoun content already
# implicit in family/agency framing).
FRAMING_TERMS = [
    "family_mentions_per_100_words",
    "agency_mentions_per_100_words",
    "urgency_mentions_per_100_words",
]

BASE_FORMULA_TERMS = [
    "log_loan_amount",
    "lenderRepaymentTerm",
    "is_group_loan",
    "C(gender_classification)",
    "desc_word_count",
    *FRAMING_TERMS,
    "desc_sentiment_compound",
    "sentiment_available",
    "C(repaymentInterval)",
    "C(sector)",
    "C(region)",
    "C(analysis_period)",
]

# Pre-specified period interaction included by default: does the
# association between gender classification and the outcome differ across
# the pre-pandemic / pandemic-disruption / post-pandemic analysis periods?
# This is the only interaction fit by default, per the brief ("add only
# pre-specified period interactions in the default sample model"). Callers
# investigating other segments pass additional patsy-formula terms via
# `extra_interactions`.
DEFAULT_PERIOD_INTERACTIONS = ["C(analysis_period):C(gender_classification)"]


def _term_columns(term: str) -> "list[str]":
    """Extract the underlying data column name(s) referenced by a patsy term."""
    columns = []
    for component in term.split(":"):
        component = component.strip()
        match = re.fullmatch(r"C\(([^)]+)\)", component)
        columns.append(match.group(1) if match else component)
    return columns


def _term_has_variation(term: str, data: pd.DataFrame) -> bool:
    """
    A term is usable only if every column it references has at least two
    distinct non-null values in `data`, AND - for a two-way interaction -
    every observed combination of the two factors' levels actually occurs
    at least once.

    The second check matters on real (not synthetic) data: e.g. on the
    project's ~100-row sample, `gender_classification` only has "female"
    and "male" observed (no "mixed"/"unknown"), and no loan happens to be
    both "male" and posted during "pandemic_disruption". Both factors vary
    on their own, but that one interaction dummy (male x pandemic_disruption)
    is a column of all zeros - contributing nothing while still inflating
    the column count, which trips the rank check below for a reason that
    has nothing to do with overall sample size. Dropping just the
    interaction (not the main effects) here keeps the default pre-specified
    model actually fittable on realistically sparse categorical data,
    instead of only ever working on generously-varied fixtures.
    """
    columns = _term_columns(term)
    for col in columns:
        if col not in data.columns:
            raise KeyError(f"Formula term {term!r} references unknown column {col!r}")
        if data[col].dropna().nunique() < 2:
            return False
    if len(columns) == 2:
        crosstab = pd.crosstab(data[columns[0]], data[columns[1]])
        if (crosstab.to_numpy() == 0).any():
            return False
    return True


def _select_available_terms(candidate_terms, data: pd.DataFrame):
    """Split candidate formula terms into (usable, dropped-for-no-variation)."""
    kept, dropped = [], []
    for term in candidate_terms:
        if _term_has_variation(term, data):
            kept.append(term)
        else:
            dropped.append(term)
    return kept, dropped


def _build_formula(target: str, data: pd.DataFrame, extra_interactions=None):
    """
    Build a pre-specified explanatory formula for `target`, pruning any
    candidate term (main effect or interaction) that is constant in `data`.
    Returns (formula, dropped_terms).
    """
    candidates = list(BASE_FORMULA_TERMS) + list(DEFAULT_PERIOD_INTERACTIONS)
    if extra_interactions:
        candidates += list(extra_interactions)
    kept, dropped = _select_available_terms(candidates, data)
    if not kept:
        raise ValueError(f"No usable predictors remain for target {target!r} after pruning constant terms")
    formula = f"{target} ~ " + " + ".join(kept)
    return formula, dropped


def _fit_design(formula: str, data: pd.DataFrame, model_label: str):
    """
    Build the (y, X) design matrices for `formula` and raise a clear error
    if the design is too small or rank-deficient, instead of letting a
    cryptic linear-algebra exception surface from inside statsmodels.
    """
    y, X = patsy.dmatrices(formula, data=data, return_type="dataframe")
    n_obs, n_cols = X.shape
    rank = int(np.linalg.matrix_rank(X.to_numpy()))
    if n_obs <= n_cols or rank < n_cols:
        raise ValueError(
            f"{model_label} design is too small or rank-deficient: "
            f"{n_obs} observations vs {n_cols} design columns (matrix rank {rank}). "
            "Provide more rows with varied categorical coverage, or reduce "
            "categorical/interaction terms, and try again."
        )
    return y, X


def _check_well_identified(results, model_label: str, n_obs: int, n_cols: int):
    """
    A design can pass the rank check above (the X matrix is technically
    full rank) and still not support the fitted model: with many sparse
    categorical levels and a binary outcome in particular, quasi-complete
    separation can drive the GLM's fitted probabilities to 0/1 and its HC3
    sandwich covariance singular, producing enormous coefficients and
    non-finite standard errors - not a matrix-rank problem, but the same
    underlying cause (too little data for this many pre-specified
    categorical parameters). Reporting those as if they were valid 95% CIs
    would be a "robust" model in name only, so this is checked and raised
    just as explicitly as the rank check.
    """
    if not np.all(np.isfinite(results.bse)):
        raise ValueError(
            f"{model_label} produced non-finite standard errors for "
            f"{n_obs} observations vs {n_cols} design columns - this usually means "
            "quasi-complete separation (a categorical level whose outcome is "
            "constant, e.g. every loan in some sector/region cell has the same "
            "24-hour outcome). Provide more rows, more balanced categorical "
            "coverage, or fewer/coarser categorical terms, and try again."
        )


def fit_explanatory_models(df: pd.DataFrame, extra_interactions=None) -> "dict[str, object]":
    """
    Fit the two robust explanatory (association) models of Kiva funding
    behavior:

      - `duration`: OLS of `log_funding_speed` on the pre-specified
        predictors, fit only on rows with a `valid_completed_outcome`,
        with HC3 heteroskedasticity-robust standard errors.
      - `binary`: binomial GLM of `funded_within_24h` on the same
        predictors, fit only on rows where `funded_within_24h` is not null,
        also with HC3 robust standard errors.

    `df` is a raw (or already-prepared) Kiva loans frame; this function
    runs `prepare_analysis_data` and `extract_deterministic_features`
    itself, so both the outcome/period columns and the narrative/borrower
    features are available regardless of what the caller already computed.

    `extra_interactions` optionally adds more patsy-formula interaction
    terms (e.g. segment-specific interactions) on top of the default
    `C(analysis_period):C(gender_classification)` interaction - useful for
    exploratory follow-up on the full dataset without changing the default
    pre-specified model.

    Returns a dict with the fitted `duration`/`binary` results objects,
    `n_duration`/`n_binary` row counts actually used, the exact formulas
    fit, and any pre-specified terms dropped for lacking variation in that
    particular sample (see the module docstring for why `sentiment_available`
    is a common one to see dropped).
    """
    prepared = prepare_analysis_data(df)
    featured = extract_deterministic_features(prepared)

    duration_data = featured.loc[featured["valid_completed_outcome"]].copy()
    if duration_data.empty:
        raise ValueError("fit_explanatory_models found no rows with a valid completed outcome")

    binary_data = featured.loc[featured["funded_within_24h"].notna()].copy()
    if binary_data.empty:
        raise ValueError("fit_explanatory_models found no rows with a known 24-hour funding outcome")
    binary_data["funded_within_24h"] = binary_data["funded_within_24h"].astype(int)

    duration_formula, duration_dropped = _build_formula(
        "log_funding_speed", duration_data, extra_interactions
    )
    binary_formula, binary_dropped = _build_formula(
        "funded_within_24h", binary_data, extra_interactions
    )

    y_dur, X_dur = _fit_design(duration_formula, duration_data, "Duration (OLS)")
    duration_results = sm.OLS(y_dur, X_dur).fit(cov_type="HC3")
    _check_well_identified(duration_results, "Duration (OLS)", *X_dur.shape)

    y_bin, X_bin = _fit_design(binary_formula, binary_data, "24-hour funding (GLM)")
    binary_results = sm.GLM(y_bin, X_bin, family=sm.families.Binomial()).fit(cov_type="HC3")
    _check_well_identified(binary_results, "24-hour funding (GLM)", *X_bin.shape)

    return {
        "duration": duration_results,
        "binary": binary_results,
        "n_duration": int(len(duration_data)),
        "n_binary": int(len(binary_data)),
        "duration_formula": duration_formula,
        "binary_formula": binary_formula,
        "duration_dropped_terms": duration_dropped,
        "binary_dropped_terms": binary_dropped,
    }


def _format_coefficient_lines(results, dependent_label: str) -> "list[str]":
    """
    Format every fitted coefficient (never filtered by p-value) as an
    association with a 95% confidence interval, on its native model scale.
    """
    params = results.params
    conf_int = results.conf_int()
    conf_int.columns = ["ci_low", "ci_high"]
    pvalues = results.pvalues

    lines = []
    for name in params.index:
        if name == "Intercept":
            continue
        coef = params[name]
        low, high = conf_int.loc[name, "ci_low"], conf_int.loc[name, "ci_high"]
        p_value = pvalues[name]
        lines.append(
            f"  - {name}: coefficient {coef:.4f} (95% CI [{low:.4f}, {high:.4f}], "
            f"p={p_value:.4f}) is associated with {dependent_label}, holding the "
            "other modeled predictors fixed."
        )
    return lines


def format_association_summary(results: "dict[str, object]") -> str:
    """
    Render `fit_explanatory_models`'s results as a human-readable summary
    using association language throughout. Every pre-specified coefficient
    is reported with its 95% CI, not only ones with p < 0.05 - readers can
    apply their own significance threshold, but this function never selects
    variables for them. Deliberately never uses "effect", "causes", or
    "proves" - the models here describe statistical association among
    pre-specified predictors and outcomes, not a causal claim.
    """
    duration_results = results["duration"]
    binary_results = results["binary"]

    lines = [
        "Explanatory Association Summary (robust HC3 standard errors)",
        "=" * 62,
        "",
        f"Duration model: log(1 + funding speed in days) ~ pre-specified predictors, "
        f"n = {results['n_duration']} loans with a valid completed outcome. "
        "OLS with HC3 heteroskedasticity-robust standard errors.",
        "Coefficients below describe how each pre-specified predictor is "
        "associated with funding speed, holding the other modeled predictors "
        "fixed. They describe statistical association, not a causal claim, "
        "and every pre-specified predictor is reported regardless of "
        "statistical significance.",
    ]
    if results.get("duration_dropped_terms"):
        lines.append(
            "Dropped for lacking variation in this sample: "
            + ", ".join(results["duration_dropped_terms"])
        )
    lines.append("")
    lines.extend(_format_coefficient_lines(duration_results, "funding speed"))
    lines.append("")

    lines.extend([
        f"24-hour funding model: funded within 24 hours ~ pre-specified predictors, "
        f"n = {results['n_binary']} loans with a known 24-hour funding outcome. "
        "Binomial GLM (log-odds scale) with HC3 heteroskedasticity-robust "
        "standard errors.",
        "Coefficients below describe how each pre-specified predictor is "
        "associated with the log-odds of funding within 24 hours, holding "
        "the other modeled predictors fixed. They describe statistical "
        "association, not a causal claim, and every pre-specified predictor "
        "is reported regardless of statistical significance.",
    ])
    if results.get("binary_dropped_terms"):
        lines.append(
            "Dropped for lacking variation in this sample: "
            + ", ".join(results["binary_dropped_terms"])
        )
    lines.append("")
    lines.extend(_format_coefficient_lines(binary_results, "the odds of funding within 24 hours"))

    return "\n".join(lines)


def run_ols_analysis(pkl_path: str, report_dir: str):
    """
    Backward-compatible, notebook-facing entry point. Loads a raw Kiva
    pickle, fits the robust explanatory duration/24-hour models via
    `fit_explanatory_models`, writes an association-language report to
    `report_dir`, and returns the fitted results dict - same shape as
    `fit_explanatory_models`'s return value.
    """
    print("Loading data and fitting robust explanatory funding models...")
    df = load_kiva_pickle(pkl_path)
    results = fit_explanatory_models(df)

    summary_text = format_association_summary(results)
    print("\n" + summary_text)

    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "statistical_summary.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("UNSW Marketing Analytics Hackathon 2026 - Statistical Analysis Report\n")
        f.write("=" * 72 + "\n\n")
        f.write(f"Sample size (duration model): {results['n_duration']} loans\n")
        f.write(f"Sample size (24-hour funding model): {results['n_binary']} loans\n\n")
        f.write(summary_text)
        f.write("\n")

    print(f"\nReport successfully saved to: {report_path}")
    return results


if __name__ == "__main__":
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(src_dir)
    pkl_path = os.path.join(project_root, "data", "Kiva_Loans_Sample.pkl")
    report_dir = os.path.join(project_root, "reports")

    run_ols_analysis(pkl_path, report_dir)
