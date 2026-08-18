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
import warnings

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
from statsmodels.tools.sm_exceptions import PerfectSeparationWarning

try:
    from src.data_loader import load_kiva_pickle, prepare_analysis_data
    from src.features import extract_deterministic_features
    from src.validation import InsufficientDataError
except ModuleNotFoundError:
    from data_loader import load_kiva_pickle, prepare_analysis_data
    from features import extract_deterministic_features
    from validation import InsufficientDataError


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
    "C(loan_size_band)",
]

# Pre-specified segment interactions included by default: does the
# association between narrative framing and the outcome differ across
# (1) the pre-pandemic / pandemic-disruption / post-pandemic analysis
# periods, (2) broad region, or (3) loan-size band? These are three of the
# design spec's four pre-specified heterogeneity tests ("Analytical
# Design": narrative framing x period / region / loan-size band / sector).
# The fourth - narrative framing x sector - is deliberately left out of
# this default list: the brief requires it be "restricted to adequately
# represented sectors," which needs a sample-specific sector allowlist
# decision this generic default formula cannot make safely, so it remains
# available only via `extra_interactions` for a caller that has made that
# judgment call. `family_mentions_per_100_words` is used as the single
# representative framing measure for all three, to keep the default model
# parsimonious - it is one of `FRAMING_TERMS`'s three main effects already
# in the base formula, so this adds three interaction terms, not new
# predictors (`C(loan_size_band)` is added to `BASE_FORMULA_TERMS` above as
# its own main effect, since introducing an interaction without the
# corresponding main effect is not standard modeling practice - see the
# report for this project's discussion of that judgment call). Each
# interaction is independently pruned by `_select_available_terms` if the
# specific fitting sample cannot support it (see `_term_has_variation`),
# exactly like the period interaction was before this list grew to three.
# Callers investigating additional segments (sector, or other framing
# measures) pass additional patsy-formula terms via `extra_interactions`.
DEFAULT_SEGMENT_INTERACTIONS = [
    "family_mentions_per_100_words:C(analysis_period)",
    "family_mentions_per_100_words:C(region)",
    "family_mentions_per_100_words:C(loan_size_band)",
]


def _term_columns(term: str) -> "list[str]":
    """Extract the underlying data column name(s) referenced by a patsy term."""
    columns = []
    for component in term.split(":"):
        component = component.strip()
        match = re.fullmatch(r"C\(([^)]+)\)", component)
        columns.append(match.group(1) if match else component)
    return columns


def _is_categorical_component(component: str) -> bool:
    return re.fullmatch(r"C\([^)]+\)", component.strip()) is not None


def _term_has_variation(term: str, data: pd.DataFrame) -> bool:
    """
    A term is usable only if every column it references has at least two
    distinct non-null values in `data`, AND - for a two-way interaction
    between two *categorical* (`C(...)`) factors - every observed
    combination of the two factors' levels actually occurs at least once.

    The categorical x categorical check matters on real (not synthetic)
    data: e.g. on the project's ~100-row sample, `gender_classification`
    only has "female" and "male" observed (no "mixed"/"unknown"), and no
    loan happens to be both "male" and posted during "pandemic_disruption".
    Both factors vary on their own, but that one interaction dummy (male x
    pandemic_disruption) is a column of all zeros - contributing nothing
    while still inflating the column count, which trips the rank check
    below for a reason that has nothing to do with overall sample size.
    Dropping just the interaction (not the main effects) here keeps the
    default pre-specified model actually fittable on realistically sparse
    categorical data, instead of only ever working on generously-varied
    fixtures.

    That full-crosstab check is meaningless for a *continuous* narrative
    measure x categorical period, though: a continuous column's dozens of
    near-unique values will almost always occur in only one period each,
    so a literal crosstab is nearly always sparse-with-zeros by
    construction - not because the interaction is actually unusable. For a
    continuous x categorical term, instead require that the continuous
    side varies *within every observed level* of the categorical side, not
    merely at least one. Variation in just one level is not enough: patsy
    fits a separate interaction column per category level, so if the
    continuous measure is constant within even a single level, that
    level's interaction column is exactly collinear with that level's own
    main-effect indicator - making the *whole* design rank-deficient
    (`_fit_design` then rejects both models entirely) instead of merely
    losing one unsupported interaction term. The rank check in
    `_fit_design` remains the authoritative backstop for anything subtler
    that this heuristic misses.
    """
    columns = _term_columns(term)
    for col in columns:
        if col not in data.columns:
            raise KeyError(f"Formula term {term!r} references unknown column {col!r}")
        if data[col].dropna().nunique() < 2:
            return False
    if len(columns) != 2:
        return True

    components = [component.strip() for component in term.split(":")]
    categorical_flags = [_is_categorical_component(component) for component in components]

    if all(categorical_flags):
        crosstab = pd.crosstab(data[columns[0]], data[columns[1]])
        if (crosstab.to_numpy() == 0).any():
            return False
        return True

    if any(categorical_flags):
        cat_index = categorical_flags.index(True)
        cat_col, cont_col = columns[cat_index], columns[1 - cat_index]
        within_group_variation = data.groupby(data[cat_col], observed=True)[cont_col].nunique()
        if not (within_group_variation >= 2).all():
            return False
        return True

    # Continuous x continuous: both components already passed the overall
    # nunique >= 2 check above; the rank check is the backstop.
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
    candidates = list(BASE_FORMULA_TERMS) + list(DEFAULT_SEGMENT_INTERACTIONS)
    if extra_interactions:
        candidates += list(extra_interactions)
    kept, dropped = _select_available_terms(candidates, data)
    if not kept:
        raise InsufficientDataError(f"No usable predictors remain for target {target!r} after pruning constant terms")
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
        raise InsufficientDataError(
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
        raise InsufficientDataError(
            f"{model_label} produced non-finite standard errors for "
            f"{n_obs} observations vs {n_cols} design columns - this usually means "
            "quasi-complete separation (a categorical level whose outcome is "
            "constant, e.g. every loan in some sector/region cell has the same "
            "24-hour outcome). Provide more rows, more balanced categorical "
            "coverage, or fewer/coarser categorical terms, and try again."
        )


def _fit_one_model(kind: str, formula: str, data: pd.DataFrame, model_label: str):
    """
    Fit one explanatory model (OLS for `kind == "ols"`, binomial GLM for
    `kind == "glm"`) and return `(results, error_message)`.

    `_fit_design`'s rank/size check and `_check_well_identified`'s
    non-finite-standard-error check both raise `InsufficientDataError` on
    a design this task cannot trust. Rather than let that abort the whole
    `fit_explanatory_models` call - discarding a *different*, perfectly
    well-identified model along with it - the failure is caught here and
    returned as a diagnostic string. This is what lets, e.g., a real
    dataset with sparse sector/region cells still produce a usable
    duration-model report even when the 24-hour binary model cannot be
    reliably fit on the same sample (see the acceptance criterion:
    insufficient data must yield a clear diagnostic, not a discarded
    result or a misleading metric).

    Only `InsufficientDataError` is caught here, not every `ValueError`:
    `sm.OLS`/`sm.GLM`'s own `.fit()` can raise `ValueError` for reasons
    unrelated to the deliberate size/rank/separation checks above (a
    patsy/statsmodels integration bug, say), and that must propagate
    rather than being relabeled as "this model couldn't be fit" and
    silently reported as a data-insufficiency diagnostic.
    """
    try:
        y, X = _fit_design(formula, data, model_label)
        if kind == "ols":
            results = sm.OLS(y, X).fit(cov_type="HC3")
        else:
            # Quasi-complete separation in the intentionally engineered
            # test scenarios this module is designed to catch (see
            # `_check_well_identified` below) makes statsmodels' own GLM
            # `.fit()` surface RuntimeWarning/PerfectSeparationWarning -
            # that is statsmodels' internal signal of the exact condition
            # being tested for, not an accidental numerical issue, and
            # `_check_well_identified` still turns it into a clear
            # `InsufficientDataError` diagnostic rather than an unstable
            # fit. Scoped to just this call.
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                warnings.filterwarnings("ignore", category=PerfectSeparationWarning)
                results = sm.GLM(y, X, family=sm.families.Binomial()).fit(cov_type="HC3")
        _check_well_identified(results, model_label, *X.shape)
        return results, None
    except InsufficientDataError as error:
        return None, str(error)


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
    terms (e.g. a narrative-by-sector interaction restricted to adequately
    represented sectors) on top of the three default
    `DEFAULT_SEGMENT_INTERACTIONS` (narrative framing by analysis period,
    region, and loan-size band) - useful for exploratory follow-up on the
    full dataset without changing the default pre-specified model.

    Each model is fit independently: if one is too small, rank-deficient,
    or not well-identified (e.g. quasi-complete separation in the binary
    model from a sparse categorical cell), that model's slot is `None` and
    its `*_error` string explains why - the *other* model's results are
    still returned if it fit successfully. Only if *neither* model can be
    fit does this function raise, since there would be nothing left to
    report.

    Returns a dict with `duration`/`binary` results objects (or `None`),
    `duration_error`/`binary_error` diagnostic strings (or `None` when
    that model fit successfully), `n_duration`/`n_binary` row counts
    attempted, the exact formulas fit, and any pre-specified terms dropped
    for lacking variation in that particular sample (see the module
    docstring for why `sentiment_available` is a common one to see
    dropped).
    """
    prepared = prepare_analysis_data(df)
    featured = extract_deterministic_features(prepared)

    duration_data = featured.loc[featured["valid_completed_outcome"]].copy()
    if duration_data.empty:
        raise InsufficientDataError("fit_explanatory_models found no rows with a valid completed outcome")

    binary_data = featured.loc[featured["funded_within_24h"].notna()].copy()
    if binary_data.empty:
        raise InsufficientDataError("fit_explanatory_models found no rows with a known 24-hour funding outcome")
    binary_data["funded_within_24h"] = binary_data["funded_within_24h"].astype(int)

    duration_formula, duration_dropped = _build_formula(
        "log_funding_speed", duration_data, extra_interactions
    )
    binary_formula, binary_dropped = _build_formula(
        "funded_within_24h", binary_data, extra_interactions
    )

    duration_results, duration_error = _fit_one_model(
        "ols", duration_formula, duration_data, "Duration (OLS)"
    )
    binary_results, binary_error = _fit_one_model(
        "glm", binary_formula, binary_data, "24-hour funding (GLM)"
    )

    if duration_results is None and binary_results is None:
        raise InsufficientDataError(
            "fit_explanatory_models could not fit either model: "
            f"duration - {duration_error}; binary - {binary_error}"
        )

    return {
        "duration": duration_results,
        "binary": binary_results,
        "duration_error": duration_error,
        "binary_error": binary_error,
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

    Either model may be `None` (see `fit_explanatory_models`) if it could
    not be reliably fit on this sample; that section reports the clear
    diagnostic in `*_error` instead of coefficients, rather than crashing
    or silently disappearing.
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
    ]
    if duration_results is None:
        lines.append(
            f"This model could not be reliably fit on this sample: {results['duration_error']}"
        )
    else:
        lines.append(
            "Coefficients below describe how each pre-specified predictor is "
            "associated with funding speed, holding the other modeled predictors "
            "fixed. They describe statistical association, not a causal claim, "
            "and every pre-specified predictor is reported regardless of "
            "statistical significance."
        )
        if results.get("duration_dropped_terms"):
            lines.append(
                "Dropped for lacking variation in this sample: "
                + ", ".join(results["duration_dropped_terms"])
            )
        lines.append("")
        lines.extend(_format_coefficient_lines(duration_results, "funding speed"))
    lines.append("")

    lines.append(
        f"24-hour funding model: funded within 24 hours ~ pre-specified predictors, "
        f"n = {results['n_binary']} loans with a known 24-hour funding outcome. "
        "Binomial GLM (log-odds scale) with HC3 heteroskedasticity-robust "
        "standard errors."
    )
    if binary_results is None:
        lines.append(
            f"This model could not be reliably fit on this sample: {results['binary_error']}"
        )
    else:
        lines.extend([
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
        lines.extend(_format_coefficient_lines(binary_results, "the log-odds of funding within 24 hours"))

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
