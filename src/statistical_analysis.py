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
    "C(region_group)",
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
#
# The region interaction/main-effect use `region_group` (`src/features.py`'s
# fixed Africa/Asia/"Other" collapse), not raw `region`: on this project's
# real development sample, one raw region (Oceania) has exactly one
# observation, which makes `family_mentions_per_100_words:C(region)`
# unfittable (see `_term_has_variation`'s within-level variation check) -
# collapsing sparse regions into "Other" is the same "restricted to
# adequately represented levels" principle already used for sector above,
# applied here because region (unlike sector) is one of the three
# interactions included by default rather than opt-in. Only `region_group`
# is used as a main effect here, not both `region_group` and raw `region`
# together - since `region_group` is a strict coarsening of `region`, its
# dummy columns are exact linear combinations of `region`'s, so including
# both would make the design rank-deficient by construction.
DEFAULT_SEGMENT_INTERACTIONS = [
    "family_mentions_per_100_words:C(analysis_period)",
    "family_mentions_per_100_words:C(region_group)",
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


def _check_well_identified(
    results, model_label: str, n_obs: int, n_cols: int, separation_detected: bool = False
):
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

    `separation_detected` is the caller's own record of whether
    statsmodels raised `PerfectSeparationWarning` while fitting. That
    warning is checked independently of `results.bse`'s numeric value
    because complete separation does not always leave literal NaN/inf
    standard errors behind - depending on the statsmodels version and how
    far IRLS iterates before its convergence tolerance kicks in, it can
    also converge to large-but-finite coefficients with finite-looking
    (but meaningless) standard errors. `requirements.txt` only pins
    `statsmodels>=0.14.0`, so this project cannot assume every environment
    numerically fails the same way - the warning itself, which statsmodels
    raises specifically to flag this condition, is the environment-
    independent signal, and is treated as authoritative here regardless of
    what `results.bse` happens to look like.
    """
    if separation_detected or not np.all(np.isfinite(results.bse)):
        raise InsufficientDataError(
            f"{model_label} produced non-finite standard errors or a "
            "statsmodels perfect/quasi-complete separation warning for "
            f"{n_obs} observations vs {n_cols} design columns - this usually means "
            "quasi-complete separation (a categorical level whose outcome is "
            "constant, e.g. every loan in some sector/region cell has the same "
            "24-hour outcome). Provide more rows, more balanced categorical "
            "coverage, or fewer/coarser categorical terms, and try again."
        )


def _fit_one_model(
    kind: str, formula: str, data: pd.DataFrame, model_label: str,
    cov_type: str = "HC3", cluster_col: "str | None" = None,
):
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

    `cov_type`/`cluster_col` let a caller refit the identical formula with
    cluster-robust standard errors (`cov_type="cluster"`) instead of HC3 -
    used by `fit_explanatory_models`'s `cluster_sensitivity_col` for a
    sensitivity check on HC3's independence assumption. `cluster_col` must
    name a column in `data`; the groups array passed to statsmodels is
    aligned to `X.index` (the rows patsy actually retained), not `data`'s
    full index, since patsy silently drops rows with a missing predictor
    and a misaligned groups array would silently mismatch observations to
    the wrong cluster instead of raising. A missing value in `cluster_col`
    (statsmodels' sandwich-covariance code chokes with an unhandled
    `TypeError` on a mix of `None`/strings) or fewer than 2 distinct groups
    among the fitted rows (an unhandled `ZeroDivisionError` from the
    small-sample correction) is caught here and reported as an
    `InsufficientDataError` instead, matching every other fit-failure path
    in this function.
    """
    try:
        y, X = _fit_design(formula, data, model_label)
        separation_detected = False
        fit_kwargs = {"cov_type": cov_type}
        if cov_type == "cluster":
            if not cluster_col:
                raise ValueError("cluster_col is required when cov_type='cluster'")
            if cluster_col not in data.columns:
                # A caller/config mistake (e.g. a typo in
                # --cluster-sensitivity-column), not a property of the
                # sample - so a plain ValueError that propagates, matching
                # the `cluster_col is required` check above. Deliberately
                # NOT InsufficientDataError: that type means "this sample
                # is too small/unsuitable" and is caught below to degrade
                # gracefully, which would bury a typo in a report instead
                # of surfacing it.
                raise ValueError(
                    f"{model_label}: cannot cluster standard errors by {cluster_col!r} - "
                    f"no such column in the data (available: {len(data.columns)} columns)."
                )
            groups = data.loc[X.index, cluster_col]
            if groups.isna().any():
                raise InsufficientDataError(
                    f"{model_label}: cannot cluster standard errors by {cluster_col!r} - "
                    f"{int(groups.isna().sum())} of {len(groups)} fitted rows have a "
                    "missing value in that column. Clustering requires every fitted "
                    "row to have a valid group label."
                )
            n_groups = groups.nunique()
            if n_groups < 2:
                raise InsufficientDataError(
                    f"{model_label}: cannot cluster standard errors by {cluster_col!r} - "
                    f"only {n_groups} distinct group(s) among the fitted rows. "
                    "Clustering requires at least 2 groups to estimate a sandwich "
                    "covariance."
                )
            fit_kwargs["cov_kwds"] = {"groups": groups}
        if kind == "ols":
            results = sm.OLS(y, X).fit(**fit_kwargs)
        else:
            # Quasi-complete separation in the intentionally engineered
            # test scenarios this module is designed to catch (see
            # `_check_well_identified` below) makes statsmodels' own GLM
            # `.fit()` surface RuntimeWarning/PerfectSeparationWarning -
            # that is statsmodels' internal signal of the exact condition
            # being tested for, not an accidental numerical issue.
            # RuntimeWarning is suppressed outright (never diagnostic on
            # its own), but PerfectSeparationWarning is *recorded*, not
            # suppressed: its occurrence is passed to
            # `_check_well_identified` as authoritative evidence of an
            # untrustworthy fit, independent of whether `results.bse`
            # itself happens to come out non-finite in this environment.
            # Scoped to just this call.
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                results = sm.GLM(y, X, family=sm.families.Binomial()).fit(**fit_kwargs)
            separation_detected = any(
                issubclass(w.category, PerfectSeparationWarning) for w in caught
            )
            # `record=True` captures every warning category (RuntimeWarning
            # is filtered to "ignore" above, so it never lands here).
            # PerfectSeparationWarning is deliberately captured and turned
            # into an InsufficientDataError below - handled, not discarded.
            # Any *other* category caught here is unexpected and must not
            # be silently swallowed just because it happened to fire inside
            # this block - re-emit it so it still surfaces normally (e.g.
            # under `pytest -W error`, or to a human reading terminal
            # output), in case a future statsmodels version raises a
            # different diagnostic this code doesn't yet know about.
            for warning in caught:
                if not issubclass(warning.category, PerfectSeparationWarning):
                    warnings.warn_explicit(
                        warning.message, warning.category, warning.filename, warning.lineno
                    )
        _check_well_identified(results, model_label, *X.shape, separation_detected=separation_detected)
        return results, None
    except InsufficientDataError as error:
        return None, str(error)


def fit_explanatory_models(
    df: pd.DataFrame, extra_interactions=None, cluster_sensitivity_col: "str | None" = None,
) -> "dict[str, object]":
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

    `cluster_sensitivity_col` optionally names a column (e.g.
    `"country_name"`) to refit both models a second time with cluster-
    robust standard errors instead of HC3, as a sensitivity check: HC3
    corrects for heteroskedasticity but still assumes independent
    observations, and loans sharing a country may share unobserved
    influences (field-partner writing templates, local conditions) that
    make them correlated rather than independent. Both refits use the
    exact same formula and data as the primary HC3 fit - only the
    covariance estimator differs - so a coefficient that stays
    significant under both is a materially more trustworthy finding than
    one that is only significant under HC3's stricter independence
    assumption. When `None` (the default), no extra fitting happens and
    the returned dict omits the `*_clustered*` keys entirely.

    Returns a dict with `duration`/`binary` results objects (or `None`),
    `duration_error`/`binary_error` diagnostic strings (or `None` when
    that model fit successfully), `n_duration`/`n_binary` row counts
    attempted, the exact formulas fit, and any pre-specified terms dropped
    for lacking variation in that particular sample (see the module
    docstring for why `sentiment_available` is a common one to see
    dropped). When `cluster_sensitivity_col` is given, also includes
    `duration_clustered`/`binary_clustered` (results objects or `None`),
    `duration_clustered_error`/`binary_clustered_error`, and
    `cluster_sensitivity_col` itself (echoed back for a formatter to use).
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

    result = {
        "duration": duration_results,
        "binary": binary_results,
        "duration_error": duration_error,
        "binary_error": binary_error,
        "n_duration": int(len(duration_data)),
        "n_binary": int(len(binary_data)),
        # `n_duration`/`n_binary` above count rows *eligible* for the
        # respective model (a valid completed outcome / a known 24-hour
        # outcome) - not necessarily how many rows the fitted model
        # actually used. Patsy silently drops any row with a missing
        # value in *any* formula predictor when building the design
        # matrix, so the two counts can diverge (e.g. one row with a
        # missing repaymentInterval: 100 eligible, 99 actually fitted).
        # These report the real fitted count directly from the results
        # object's own `.nobs`, `None` when the model didn't fit at all.
        "duration_model_n": int(duration_results.nobs) if duration_results is not None else None,
        "binary_model_n": int(binary_results.nobs) if binary_results is not None else None,
        "duration_formula": duration_formula,
        "binary_formula": binary_formula,
        "duration_dropped_terms": duration_dropped,
        "binary_dropped_terms": binary_dropped,
    }

    if cluster_sensitivity_col:
        # Same formula, same data, same rows - only the covariance
        # estimator differs, so any change in which coefficients clear
        # p < 0.05 is attributable to the independence assumption, not to
        # a different model.
        duration_clustered, duration_clustered_error = _fit_one_model(
            "ols", duration_formula, duration_data, "Duration (OLS, cluster-robust)",
            cov_type="cluster", cluster_col=cluster_sensitivity_col,
        )
        binary_clustered, binary_clustered_error = _fit_one_model(
            "glm", binary_formula, binary_data, "24-hour funding (GLM, cluster-robust)",
            cov_type="cluster", cluster_col=cluster_sensitivity_col,
        )
        result["duration_clustered"] = duration_clustered
        result["binary_clustered"] = binary_clustered
        result["duration_clustered_error"] = duration_clustered_error
        result["binary_clustered_error"] = binary_clustered_error
        result["cluster_sensitivity_col"] = cluster_sensitivity_col

        # Average within-group slopes for the focal narrative measure.
        # An interaction coefficient only tests whether a group's slope
        # differs from the reference group's; and because the focal term
        # is interacted with several moderators at once, "main effect +
        # group term" is the slope only at the OTHER moderators' reference
        # levels - one unrepresentative cell. The quantity a group-level
        # claim actually needs is the slope averaged over that group's own
        # observed moderator composition, which is what this computes (see
        # `_average_group_slopes`). Gated on `cluster_sensitivity_col`
        # because the whole point is reporting it under both HC3 and the
        # cluster-robust covariance.
        result["within_region_slopes"] = {
            "focal_term": WITHIN_GROUP_FOCAL_TERM,
            "group_factor": WITHIN_GROUP_FACTOR,
            "duration": _average_group_slopes(
                duration_results, duration_clustered, duration_data,
                WITHIN_GROUP_FOCAL_TERM, WITHIN_GROUP_FACTOR, cluster_sensitivity_col,
            ),
            "binary": _average_group_slopes(
                binary_results, binary_clustered, binary_data,
                WITHIN_GROUP_FOCAL_TERM, WITHIN_GROUP_FACTOR, cluster_sensitivity_col,
            ),
        }

    return result


# The focal continuous measure and grouping factor for the average
# within-group slope report. Module constants (not per-call arguments on
# `fit_explanatory_models`) because they are part of this project's
# pre-specified design - the family-framing-by-region question - not a
# free parameter a caller should vary run to run.
WITHIN_GROUP_FOCAL_TERM = "family_mentions_per_100_words"
WITHIN_GROUP_FACTOR = "region_group"


def _average_group_slopes(
    hc3_results, clustered_results, data: pd.DataFrame,
    focal_term: str, group_factor: str, cluster_col: str,
):
    """
    For each level of `group_factor`, compute the slope of the outcome in
    `focal_term`, averaged over that group's own observed composition of
    every OTHER moderator `focal_term` is interacted with - as a single
    weighted linear contrast, so `t_test` applies the fitted covariance
    (HC3 or cluster-robust) to it exactly as to any coefficient.

    Returns a list of JSON-safe dicts (one per group level, sorted), or a
    string error message when the inputs cannot support the calculation
    (either model missing, or the focal term pruned from the fit). The
    reference group has no interaction term of its own; its average slope
    is the focal main effect plus its weighted non-group interactions.

    Weights come from the rows the model actually fitted
    (`results.model.data.row_labels`), not the caller's full frame - patsy
    silently drops rows with a missing predictor, and composition weights
    must describe the fitted sample.
    """
    if hc3_results is None or clustered_results is None:
        return "not computed - the model or its cluster-robust refit did not fit"
    param_names = list(hc3_results.params.index)
    if focal_term not in param_names:
        return f"not computed - {focal_term!r} is not in the fitted model"

    row_labels = hc3_results.model.data.row_labels
    fitted = data.loc[row_labels] if row_labels is not None else data

    group_terms = {}
    other_moderator_terms = []
    group_prefix = f"{focal_term}:C({group_factor})[T."
    for name in param_names:
        if name.startswith(group_prefix):
            group_terms[name[len(group_prefix):].rstrip("]")] = name
        elif name.startswith(f"{focal_term}:C("):
            other_moderator_terms.append(name)

    rows = []
    for level in sorted(fitted[group_factor].astype(str).unique()):
        subset = fitted.loc[fitted[group_factor].astype(str) == level]
        pieces = [focal_term]
        if level in group_terms:
            pieces.append(group_terms[level])
        for term in other_moderator_terms:
            column = term.split(":C(")[1].split(")[T.")[0]
            moderator_level = term.split(")[T.")[1].rstrip("]")
            if column not in subset.columns:
                continue
            weight = float((subset[column].astype(str) == moderator_level).mean())
            if weight > 0:
                pieces.append(f"{weight:.10f} * {term}")
        contrast = " + ".join(pieces) + " = 0"

        t_hc3 = hc3_results.t_test(contrast)
        t_clustered = clustered_results.t_test(contrast)
        estimate = float(np.ravel(t_hc3.effect)[0])
        hc3_p = float(np.ravel(t_hc3.pvalue)[0])
        clustered_p = float(np.ravel(t_clustered.pvalue)[0])
        rows.append({
            "group": level,
            "n_loans": int(len(subset)),
            "n_clusters": int(subset[cluster_col].nunique()) if cluster_col in subset.columns else None,
            "estimate": estimate,
            "hc3_p": hc3_p,
            "clustered_p": clustered_p,
            "significant_under_both": bool(hc3_p < 0.05 and clustered_p < 0.05),
        })
    return rows


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


def _n_clause(eligible_n: int, model_n, eligibility_description: str) -> str:
    """
    Format the "n = ..." clause for one explanatory model's summary line.

    `eligible_n` counts rows meeting the model's *eligibility* criterion
    (a valid completed outcome, or a known 24-hour outcome) -
    `fit_explanatory_models`'s `n_duration`/`n_binary`. `model_n` is the
    actual row count the fitted statsmodels result used
    (`results.nobs`), or `None` if the model never fit. Patsy silently
    drops any row with a missing value in *any* formula predictor when
    building the design matrix, so `model_n` can be lower than
    `eligible_n` - surfaced explicitly here instead of only ever quoting
    the eligibility count, which can overstate how many rows the
    reported coefficients actually reflect.
    """
    if model_n is None or model_n == eligible_n:
        return f"n = {eligible_n} loans {eligibility_description}"
    excluded = eligible_n - model_n
    return (
        f"n = {model_n} loans used in the fitted model "
        f"({excluded} of {eligible_n} loans {eligibility_description} excluded "
        "for a missing predictor value)"
    )


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
        f"{_n_clause(results['n_duration'], results.get('duration_model_n'), 'with a valid completed outcome')}. "
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
        f"{_n_clause(results['n_binary'], results.get('binary_model_n'), 'with a known 24-hour funding outcome')}. "
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


def _significance_comparison_lines(hc3_results, clustered_results) -> "list[str]":
    """
    For every coefficient in `hc3_results`, compare its p < 0.05 call under
    HC3 against the same coefficient's call under `clustered_results` - the
    identical model, refit with cluster-robust standard errors. Every
    coefficient is reported, not only ones where the call changes: a
    reader should be able to see the full comparison, not a pre-filtered
    subset this function decided was interesting.
    """
    lines = []
    for name in hc3_results.params.index:
        if name == "Intercept":
            continue
        p_hc3 = hc3_results.pvalues[name]
        hc3_sig = p_hc3 < 0.05
        if name in clustered_results.pvalues.index:
            p_clustered = clustered_results.pvalues[name]
            clustered_sig = p_clustered < 0.05
            agreement = "same conclusion" if hc3_sig == clustered_sig else "CONCLUSION CHANGES"
            lines.append(
                f"  - {name}: HC3 p={p_hc3:.4f} ({'significant' if hc3_sig else 'not significant'}); "
                f"clustered p={p_clustered:.4f} ({'significant' if clustered_sig else 'not significant'}) "
                f"[{agreement}]"
            )
        else:
            lines.append(f"  - {name}: HC3 p={p_hc3:.4f}; dropped from the clustered refit (see its dropped-terms list)")
    return lines


def format_cluster_sensitivity_summary(results: "dict[str, object]") -> str:
    """
    Render `fit_explanatory_models`'s cluster-robust sensitivity check (when
    `cluster_sensitivity_col` was passed) as a human-readable comparison
    against the primary HC3 fit. Returns an explanatory sentence and, for
    every coefficient, whether p < 0.05 agrees between HC3 and the cluster-
    robust refit - the point is not "which numbers changed" but "does the
    significance conclusion survive relaxing HC3's independence
    assumption." Returns an empty string if no sensitivity check was run
    (`cluster_sensitivity_col` not in `results`), so a caller can safely
    call this unconditionally and skip appending it when empty.
    """
    cluster_col = results.get("cluster_sensitivity_col")
    if not cluster_col:
        return ""

    lines = [
        "Cluster-Robust Sensitivity Check",
        "=" * 62,
        "",
        f"HC3 standard errors correct for heteroskedasticity but still assume "
        f"independent observations. Loans sharing a {cluster_col} may share "
        "unobserved influences (field-partner writing templates, local "
        "conditions) that HC3 cannot see. This refits the identical duration "
        f"and 24-hour formulas with standard errors clustered by {cluster_col} "
        "instead, and compares which coefficients clear p < 0.05 under each - "
        "a same-data specification-robustness check: a coefficient "
        "significant under both is robust to relaxing HC3's independence "
        "assumption, while one significant only under HC3 is not.",
        "",
    ]

    duration_hc3, duration_clustered = results.get("duration"), results.get("duration_clustered")
    lines.append("Duration model (log funding speed):")
    if duration_hc3 is None or duration_clustered is None:
        error = results.get("duration_clustered_error") or results.get("duration_error")
        lines.append(f"  Could not compare: {error}")
    else:
        lines.extend(_significance_comparison_lines(duration_hc3, duration_clustered))
    lines.append("")

    binary_hc3, binary_clustered = results.get("binary"), results.get("binary_clustered")
    lines.append("24-hour funding model (log-odds):")
    if binary_hc3 is None or binary_clustered is None:
        error = results.get("binary_clustered_error") or results.get("binary_error")
        lines.append(f"  Could not compare: {error}")
    else:
        lines.extend(_significance_comparison_lines(binary_hc3, binary_clustered))

    return "\n".join(lines)


def format_within_region_slopes(results: "dict[str, object]") -> str:
    """
    Render `fit_explanatory_models`'s average within-group slopes (computed
    when `cluster_sensitivity_col` was passed) as a human-readable section.
    Returns an empty string when the digest is absent, so a caller can
    append it unconditionally the same way as
    `format_cluster_sensitivity_summary`.
    """
    digest = results.get("within_region_slopes")
    if not digest:
        return ""
    focal = digest["focal_term"]
    group_factor = digest["group_factor"]
    cluster_col = results.get("cluster_sensitivity_col", "cluster")

    lines = [
        "Average Within-Region Family-Framing Slopes",
        "=" * 62,
        "",
        f"An interaction coefficient only tests whether a {group_factor} level's "
        f"{focal} slope differs from the reference level's. It does NOT test "
        "whether the focal measure is associated with the outcome WITHIN that "
        "group - and because the focal term is interacted with several "
        "moderators at once, 'main effect + group term' is the slope only at "
        "the other moderators' reference levels, one unrepresentative cell. "
        "This section reports the correct quantity: each group's slope "
        "averaged over that group's own observed composition of the other "
        "moderators, as a weighted linear contrast, under both HC3 and "
        f"{cluster_col}-clustered standard errors.",
        "",
        "Sign conventions are OPPOSITE between the two models: the duration "
        "model is log(1 + days), so NEGATIVE = faster funding; the 24-hour "
        "model is log-odds of funding within 24h, so POSITIVE = faster.",
        "",
        "A group's slope is identified only by the clusters within it; a "
        "group containing very few clusters cannot separate the focal "
        "association from whatever else is idiosyncratic about those "
        "specific clusters, and its estimate pools the whole group - it is "
        "not evidence about any individual constituent cluster.",
        "",
    ]

    def _section(title, key):
        lines.append(title)
        section = digest.get(key)
        if isinstance(section, str) or section is None:
            lines.append(f"  {section or 'not computed'}")
            return
        for row in section:
            verdict = "significant under both" if row["significant_under_both"] else "not significant under both"
            clusters = f", {row['n_clusters']} {cluster_col} cluster(s)" if row.get("n_clusters") is not None else ""
            lines.append(
                f"  - {row['group']} ({row['n_loans']} loans{clusters}): "
                f"estimate={row['estimate']:.4f} HC3 p={row['hc3_p']:.4f} | "
                f"clustered p={row['clustered_p']:.4f} [{verdict}]"
            )

    _section("Duration model (log funding speed; NEGATIVE = faster):", "duration")
    lines.append("")
    _section("24-hour funding model (log-odds; POSITIVE = faster):", "binary")
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
