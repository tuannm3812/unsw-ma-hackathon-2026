import os

import pandas as pd
import pytest

import src.statistical_analysis as statistical_analysis_module
from src.statistical_analysis import (
    _check_well_identified,
    _significance_comparison_lines,
    _term_has_variation,
    fit_explanatory_models,
    format_association_summary,
    format_cluster_sensitivity_summary,
    run_ols_analysis,
)
from src.validation import InsufficientDataError


class _FakeGlmResults:
    """Minimal stand-in for a statsmodels results object - just the `.bse`
    attribute `_check_well_identified` reads - so its `separation_detected`
    branch can be tested directly without depending on which statsmodels
    version happens to produce literal NaN/inf standard errors for a given
    separated design (see the docstring on `_check_well_identified`)."""

    def __init__(self, bse):
        self.bse = pd.Series(bse)


class _FakeSignificanceResults:
    """Minimal stand-in exposing just `.params.index` and `.pvalues`, so
    `_significance_comparison_lines`'s per-coefficient agreement label can
    be tested against known, hand-picked p-values on both sides - not just
    checked for the presence of either output string somewhere in a real
    fit's output, which a same/CHANGES sign flip cannot be told apart
    from."""

    def __init__(self, pvalues):
        self.pvalues = pd.Series(pvalues)
        self.params = pd.Series(0.0, index=self.pvalues.index)


def test_default_interaction_tests_narrative_framing_by_period_not_gender(large_synthetic_kiva_df):
    # The approved design pre-specifies "narrative framing x analysis
    # period" as the temporal-heterogeneity test (the 20%-weighted
    # "evolutionary perspective" judging criterion) - not a gender x
    # period interaction, which answers a different question.
    result = fit_explanatory_models(large_synthetic_kiva_df)
    assert "family_mentions_per_100_words:C(analysis_period)" in result["duration_formula"]
    assert "family_mentions_per_100_words:C(analysis_period)" in result["binary_formula"]
    assert "C(gender_classification):C(analysis_period)" not in result["duration_formula"]


def test_continuous_by_categorical_interaction_is_not_rejected_as_sparse(large_synthetic_kiva_df):
    # A continuous narrative measure's ~unique values will almost always
    # occur in only one period each - that is not the same thing as the
    # interaction being unusable, and must not be rejected as if it were
    # a sparse categorical x categorical crosstab.
    from src.data_loader import prepare_analysis_data
    from src.features import extract_deterministic_features

    prepared = prepare_analysis_data(large_synthetic_kiva_df)
    featured = extract_deterministic_features(prepared)
    data = featured.loc[featured["valid_completed_outcome"]].copy()

    assert _term_has_variation("family_mentions_per_100_words:C(analysis_period)", data)


def test_continuous_by_categorical_interaction_requires_variation_in_every_level(large_synthetic_kiva_df):
    # Variation in *at least one* category level is not enough: if the
    # continuous measure is constant within even one observed period, that
    # period's interaction column is collinear with the period's own main-
    # effect indicator, and the *whole* design becomes rank-deficient
    # (rejecting both models) instead of just dropping the one unsupported
    # interaction term.
    from src.data_loader import prepare_analysis_data
    from src.features import extract_deterministic_features

    prepared = prepare_analysis_data(large_synthetic_kiva_df)
    featured = extract_deterministic_features(prepared)
    data = featured.loc[featured["valid_completed_outcome"]].copy()
    data.loc[data["analysis_period"] == "pandemic_disruption", "family_mentions_per_100_words"] = 0.0

    assert not _term_has_variation("family_mentions_per_100_words:C(analysis_period)", data)


def test_duration_model_still_fits_when_interaction_is_dropped_for_one_constant_period(large_synthetic_kiva_df):
    frame = large_synthetic_kiva_df.copy()
    from src.data_loader import prepare_analysis_data

    prepared = prepare_analysis_data(frame)
    pandemic_mask = prepared["analysis_period"] == "pandemic_disruption"
    frame.loc[pandemic_mask, "description"] = "to buy stock and materials for the business"

    result = fit_explanatory_models(frame)
    assert result["duration"] is not None
    assert "family_mentions_per_100_words:C(analysis_period)" in result["duration_dropped_terms"]
    # Main effects survive even though the interaction was dropped.
    assert "C(analysis_period)" in result["duration_formula"]
    assert "family_mentions_per_100_words" in result["duration_formula"]


def test_default_formula_considers_all_three_pre_specified_segment_interactions(large_synthetic_kiva_df):
    # The approved design pre-specifies THREE default heterogeneity tests
    # (narrative framing x period, x region, x loan-size band - sector is
    # exploratory-only via `extra_interactions`, since the brief requires
    # it be "restricted to adequately represented sectors"). On a fixture
    # with enough variation for all three, every one of them must appear as
    # a considered candidate in the default formula - not just the period
    # interaction from before this task.
    result = fit_explanatory_models(large_synthetic_kiva_df)
    assert "family_mentions_per_100_words:C(analysis_period)" in result["duration_formula"]
    assert "family_mentions_per_100_words:C(region_group)" in result["duration_formula"]
    assert "family_mentions_per_100_words:C(loan_size_band)" in result["duration_formula"]
    # None of the three segment interactions were pruned on this fixture
    # (only the dataset-level `sentiment_available` constant is - see the
    # module docstring on why that one is always dropped).
    assert "family_mentions_per_100_words:C(analysis_period)" not in result["duration_dropped_terms"]
    assert "family_mentions_per_100_words:C(region_group)" not in result["duration_dropped_terms"]
    assert "family_mentions_per_100_words:C(loan_size_band)" not in result["duration_dropped_terms"]
    # loan_size_band's own main effect must be present too - introducing an
    # interaction without its main effect is not standard practice.
    assert "C(loan_size_band)" in result["duration_formula"]


def test_region_interaction_is_pruned_when_region_group_has_no_family_mentions_variation(
    large_synthetic_kiva_df,
):
    # Mirrors test_duration_model_still_fits_when_interaction_is_dropped_
    # for_one_constant_period, but for the region interaction: the existing
    # _term_has_variation/_select_available_terms pruning machinery (built
    # specifically to handle "this interaction isn't supportable on this
    # sample") must extend to the two new default interactions without any
    # new pruning logic. Uses `region_group` (not raw `region`), since that
    # is what the interaction and its main effect are now built on - zeros
    # out every row in the "Pacific" level specifically. `region_group` is
    # now a count-based threshold (src/features.py), not a fixed name
    # list, and every one of _LARGE_FIXTURE_REGIONS's 5 regions clears
    # that threshold on this 120-row fixture (each has 18+ rows, well
    # above MIN_REGION_OBSERVATIONS) - so region_group == region here and
    # there is no "Other" level to target; picking one real level directly
    # exercises the same pruning path.
    frame = large_synthetic_kiva_df.copy()
    from src.data_loader import prepare_analysis_data
    from src.features import extract_deterministic_features

    prepared = prepare_analysis_data(frame)
    featured_probe = extract_deterministic_features(prepared)
    pacific_mask = featured_probe["region_group"] == "Pacific"
    frame.loc[pacific_mask, "description"] = "to buy stock and materials for the business"

    result = fit_explanatory_models(frame)
    assert result["duration"] is not None
    assert "family_mentions_per_100_words:C(region_group)" in result["duration_dropped_terms"]
    # The other two default interactions and all main effects survive -
    # dropping one unsupported interaction must not take down the others.
    assert "family_mentions_per_100_words:C(analysis_period)" not in result["duration_dropped_terms"]
    assert "family_mentions_per_100_words:C(loan_size_band)" not in result["duration_dropped_terms"]
    assert "C(region_group)" in result["duration_formula"]
    assert "family_mentions_per_100_words" in result["duration_formula"]


def test_explanatory_models_use_valid_rows_and_robust_covariance(large_synthetic_kiva_df):
    result = fit_explanatory_models(large_synthetic_kiva_df)
    assert result["duration"].cov_type == "HC3"
    assert result["n_duration"] == len(large_synthetic_kiva_df)
    assert result["n_binary"] == len(large_synthetic_kiva_df)
    # No missing predictor values on this fixture, so the actual fitted
    # design size must match the eligible-row count exactly.
    assert result["duration_model_n"] == result["n_duration"]
    assert result["binary_model_n"] == result["n_binary"]


def test_model_n_reflects_rows_patsy_actually_dropped_for_a_missing_predictor(large_synthetic_kiva_df):
    # Patsy silently drops any row with a missing value in *any* formula
    # predictor when building the design matrix - n_duration/n_binary
    # (the "eligible" counts) do not reflect this on their own. Force one
    # row's repaymentInterval to be missing and confirm duration_model_n
    # correctly comes out one lower than n_duration, and that the
    # human-readable summary states both numbers rather than only the
    # (now overstated) eligible count.
    frame = large_synthetic_kiva_df.copy()
    frame.loc[frame.index[0], "repaymentInterval"] = None

    result = fit_explanatory_models(frame)
    assert result["duration"] is not None
    assert result["n_duration"] == len(frame)
    assert result["duration_model_n"] == len(frame) - 1

    summary = format_association_summary(result)
    assert f"n = {len(frame) - 1} loans used in the fitted model" in summary
    assert f"1 of {len(frame)} loans with a valid completed outcome excluded" in summary


def test_summary_uses_association_not_effect_language(large_synthetic_kiva_df):
    summary = format_association_summary(fit_explanatory_models(large_synthetic_kiva_df))
    assert "associated with" in summary
    assert "causes" not in summary.lower()
    assert "has a significant effect" not in summary.lower()


def test_binary_model_uses_binomial_family_and_robust_covariance(large_synthetic_kiva_df):
    result = fit_explanatory_models(large_synthetic_kiva_df)
    assert result["binary"].cov_type == "HC3"
    assert result["binary"].model.family.__class__.__name__ == "Binomial"


def test_fit_excludes_rows_without_a_valid_completed_outcome(large_synthetic_kiva_df):
    invalid_row = large_synthetic_kiva_df.iloc[[0]].copy()
    invalid_row["id"] = -1
    # raisedDate before fundraisingDate => negative duration => invalid outcome.
    invalid_row["fundraisingDate"] = "2024-06-01T00:00:00Z"
    invalid_row["raisedDate"] = "2024-05-01T00:00:00Z"
    augmented = pd.concat([large_synthetic_kiva_df, invalid_row], ignore_index=True)

    result = fit_explanatory_models(augmented)

    assert result["n_duration"] == len(large_synthetic_kiva_df)
    assert result["n_binary"] == len(large_synthetic_kiva_df)


def test_fit_raises_clear_error_on_too_small_design(large_synthetic_kiva_df):
    tiny = large_synthetic_kiva_df.head(3).copy()
    with pytest.raises(ValueError, match="observations"):
        fit_explanatory_models(tiny)


def test_fit_does_not_mask_unrelated_value_errors_from_model_fitting(large_synthetic_kiva_df, monkeypatch):
    # _fit_one_model must only catch the deliberate "this design can't be
    # trusted" checks (_fit_design's size/rank check, _check_well_identified's
    # non-finite-standard-error check) - not every ValueError from the
    # model-fitting integration boundary. An unrelated bug there (e.g. a
    # patsy/statsmodels integration error) must propagate unchanged, not
    # get relabeled as "neither model could be fit" (InsufficientDataError)
    # and silently reported as a data-insufficiency diagnostic.
    def _broken_fit_design(*args, **kwargs):
        raise ValueError("unexpected patsy integration bug")

    monkeypatch.setattr(statistical_analysis_module, "_fit_design", _broken_fit_design)

    with pytest.raises(ValueError, match="unexpected patsy integration bug") as excinfo:
        fit_explanatory_models(large_synthetic_kiva_df)
    assert not isinstance(excinfo.value, InsufficientDataError)


def test_summary_reports_coefficients_regardless_of_significance(large_synthetic_kiva_df):
    results = fit_explanatory_models(large_synthetic_kiva_df)
    summary = format_association_summary(results)

    n_duration_terms = len(results["duration"].params) - 1  # exclude intercept
    n_binary_terms = len(results["binary"].params) - 1  # exclude intercept

    # Every pre-specified coefficient must be reported, not only p < 0.05
    # ones - checked per model (not a combined total) so that filtering
    # applied to only one section would still be caught.
    duration_section, binary_section = summary.split("24-hour funding model:", 1)
    duration_coef_lines = [
        line for line in duration_section.splitlines() if line.strip().startswith("- ")
    ]
    binary_coef_lines = [
        line for line in binary_section.splitlines() if line.strip().startswith("- ")
    ]
    assert len(duration_coef_lines) == n_duration_terms
    assert len(binary_coef_lines) == n_binary_terms


def test_check_well_identified_passes_finite_bse_and_no_separation():
    _check_well_identified(_FakeGlmResults([0.5, 0.5]), "label", n_obs=20, n_cols=2)  # no raise


def test_check_well_identified_raises_on_separation_even_with_finite_bse():
    # Complete separation does not reliably leave literal NaN/inf standard
    # errors behind in every statsmodels version (requirements.txt only
    # pins statsmodels>=0.14.0) - it can also converge to large-but-finite,
    # meaningless coefficients/SEs depending on how IRLS terminates. The
    # `PerfectSeparationWarning` statsmodels raises specifically for this
    # condition must be treated as authoritative on its own, not only as a
    # hint that happens to correlate with non-finite `bse`.
    with pytest.raises(InsufficientDataError, match="non-finite standard errors"):
        _check_well_identified(
            _FakeGlmResults([0.5, 0.5]), "label", n_obs=20, n_cols=2, separation_detected=True
        )


def test_fit_one_model_treats_a_recorded_perfect_separation_warning_as_insufficient_data(monkeypatch):
    # Integration-level check that `_fit_one_model`'s GLM branch actually
    # wires the captured `PerfectSeparationWarning` through to
    # `_check_well_identified`, rather than only relying on `bse` - forces
    # a fake GLM fit that emits the warning but returns finite `bse`, and
    # confirms the caller still raises InsufficientDataError. Only needs
    # enough columns for `_fit_design`'s real `patsy.dmatrices` call to
    # succeed - the GLM fit itself is faked below.
    from statsmodels.tools.sm_exceptions import PerfectSeparationWarning

    data = pd.DataFrame({
        "y": [0, 1, 0, 1, 0, 1, 0, 1],
        "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
    })

    class _FakeFittedGlm:
        def fit(self, cov_type):
            import warnings as warnings_module
            warnings_module.warn("perfect separation", PerfectSeparationWarning)
            return _FakeGlmResults([0.5, 0.5])

    def _fake_glm(*args, **kwargs):
        return _FakeFittedGlm()

    monkeypatch.setattr(statistical_analysis_module.sm, "GLM", _fake_glm)
    results, error = statistical_analysis_module._fit_one_model("glm", "y ~ x", data, "test_model")

    assert results is None
    assert error is not None
    assert "non-finite standard errors" in error


def test_fit_one_model_re_emits_an_unrelated_warning_instead_of_silently_discarding_it(
    monkeypatch,
):
    # `_fit_one_model`'s GLM branch uses `warnings.catch_warnings(record=True)`
    # + `simplefilter("always")` to capture PerfectSeparationWarning without
    # depending on `results.bse` - but that same mechanism captures *every*
    # warning category, not just PerfectSeparationWarning. Only
    # RuntimeWarning (filtered to "ignore") and PerfectSeparationWarning
    # (converted into InsufficientDataError) are meant to be handled; any
    # other category (e.g. a future statsmodels diagnostic this code
    # doesn't know about) must still surface, not be silently swallowed
    # just because it fired inside this block.
    data = pd.DataFrame({
        "y": [0, 1, 0, 1, 0, 1, 0, 1],
        "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
    })

    class _FakeFittedGlm:
        def fit(self, cov_type):
            import warnings as warnings_module
            warnings_module.warn("some unrelated diagnostic", UserWarning)
            return _FakeGlmResults([0.5, 0.5])

    def _fake_glm(*args, **kwargs):
        return _FakeFittedGlm()

    monkeypatch.setattr(statistical_analysis_module.sm, "GLM", _fake_glm)
    with pytest.warns(UserWarning, match="some unrelated diagnostic"):
        results, error = statistical_analysis_module._fit_one_model("glm", "y ~ x", data, "test_model")

    # The unrelated warning does not itself indicate an untrustworthy fit -
    # the model still fits successfully (finite bse, no separation).
    assert results is not None
    assert error is None


def test_fit_degrades_gracefully_when_one_model_is_not_well_identified(separated_binary_kiva_df):
    # `separated_binary_kiva_df` forces quasi-complete separation in the
    # 24-hour binary model (one sector always funds within 24h) while the
    # continuous duration target is unaffected - reproducing the real
    # project sample's failure mode. A single unfittable model must not
    # discard an otherwise-successful one.
    result = fit_explanatory_models(separated_binary_kiva_df)

    assert result["duration"] is not None
    assert result["duration"].cov_type == "HC3"
    assert result["duration_error"] is None

    assert result["binary"] is None
    assert result["binary_error"] is not None
    assert "non-finite standard errors" in result["binary_error"]


def test_summary_reports_diagnostic_for_a_model_that_could_not_be_fit(separated_binary_kiva_df):
    results = fit_explanatory_models(separated_binary_kiva_df)
    summary = format_association_summary(results)

    # The duration model's coefficients are still reported normally...
    assert "associated with funding speed" in summary
    # ...and the binary section explains why it has no coefficients,
    # instead of crashing or silently omitting the section.
    assert results["binary_error"] in summary
    assert "causes" not in summary.lower()
    assert "has a significant effect" not in summary.lower()


def test_run_ols_analysis_writes_report_when_one_model_cannot_be_fit(separated_binary_kiva_df, tmp_path):
    pkl_path = tmp_path / "kiva.pkl"
    separated_binary_kiva_df.to_pickle(pkl_path)
    report_dir = tmp_path / "reports"

    results = run_ols_analysis(str(pkl_path), str(report_dir))

    assert results["duration"] is not None
    assert results["binary"] is None
    report_path = os.path.join(str(report_dir), "statistical_summary.txt")
    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "associated with funding speed" in content
    assert results["binary_error"] in content


def test_run_ols_analysis_wrapper_writes_association_language_report(large_synthetic_kiva_df, tmp_path):
    pkl_path = tmp_path / "kiva.pkl"
    large_synthetic_kiva_df.to_pickle(pkl_path)
    report_dir = tmp_path / "reports"

    results = run_ols_analysis(str(pkl_path), str(report_dir))

    assert results["duration"].cov_type == "HC3"
    report_path = os.path.join(str(report_dir), "statistical_summary.txt")
    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "associated with" in content
    assert "causes" not in content.lower()


# --- Codex review follow-up: cluster-robust sensitivity check -------------
#
# HC3 corrects for heteroskedasticity but still assumes independent
# observations; Kiva loans may cluster by country (shared field-partner
# writing templates, local conditions). These tests cover the opt-in
# `cluster_sensitivity_col` refit: present only when requested, uses the
# identical formula/data as the primary HC3 fit, and stays correctly
# aligned to whichever rows patsy actually retained (not `data`'s full
# index) even when some rows get dropped for a missing predictor.


def test_cluster_sensitivity_check_omitted_by_default(large_synthetic_kiva_df):
    result = fit_explanatory_models(large_synthetic_kiva_df)
    assert "duration_clustered" not in result
    assert "binary_clustered" not in result
    assert "cluster_sensitivity_col" not in result


def test_cluster_sensitivity_check_fits_both_models_with_cluster_covariance(large_synthetic_kiva_df):
    result = fit_explanatory_models(large_synthetic_kiva_df, cluster_sensitivity_col="country_name")

    assert result["cluster_sensitivity_col"] == "country_name"
    assert result["duration_clustered"] is not None
    assert result["duration_clustered"].cov_type == "cluster"
    assert result["binary_clustered"] is not None
    assert result["binary_clustered"].cov_type == "cluster"
    # The primary HC3 fit must be untouched by requesting the sensitivity
    # check - same formula, same result, just an additional refit alongside it.
    assert result["duration"].cov_type == "HC3"
    assert result["duration_clustered"].params.index.equals(result["duration"].params.index)


def test_cluster_sensitivity_check_stays_aligned_when_patsy_drops_a_row(large_synthetic_kiva_df):
    # Same scenario as test_model_n_reflects_rows_patsy_actually_dropped_for_a_missing_predictor:
    # patsy silently drops a row with a missing predictor when building the
    # design matrix. The cluster `groups` array must be aligned to that
    # smaller retained set (X.index), not the original data's full index -
    # a naive `data[cluster_col]` would be one row too long and either
    # raise a length-mismatch error or (worse) silently misalign every
    # row after the dropped one to the wrong cluster. Fitting without
    # error and matching the primary fit's row count is the evidence
    # alignment is correct.
    frame = large_synthetic_kiva_df.copy()
    frame.loc[frame.index[0], "repaymentInterval"] = None

    result = fit_explanatory_models(frame, cluster_sensitivity_col="country_name")

    assert result["duration_clustered"] is not None
    assert int(result["duration_clustered"].nobs) == result["duration_model_n"]


def test_fit_one_model_clusters_align_to_the_row_patsy_kept_not_a_positional_slice():
    # test_cluster_sensitivity_check_stays_aligned_when_patsy_drops_a_row
    # only checks that the clustered fit's row count (nobs) matches - but
    # a naive `data[cluster_col].iloc[:len(X)]` (or plain `data[cluster_col]`)
    # is the *same length* as the correctly-aligned `data.loc[X.index,
    # cluster_col]` whenever exactly one row is dropped, so a count-only
    # check cannot tell a same-length positional shift apart from correct
    # alignment. This asserts on the actual group labels statsmodels
    # received (`results.cov_kwds["groups"]`), which a shifted array gets
    # wrong even though it has the right length.
    data = pd.DataFrame({
        "y": [1.0, 2.0, None, 11.0, 3.0, 12.0],  # row index 2 is dropped by patsy
        "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "grp": ["A", "A", "B", "B", "A", "B"],
    })

    results, error = statistical_analysis_module._fit_one_model(
        "ols", "y ~ x", data, "test_model", cov_type="cluster", cluster_col="grp"
    )

    assert error is None
    assert results is not None
    expected_groups = data.loc[[0, 1, 3, 4, 5], "grp"]
    pd.testing.assert_series_equal(
        results.cov_kwds["groups"], expected_groups, check_names=False
    )


def test_fit_one_model_raises_for_an_unknown_cluster_column_instead_of_degrading():
    # A typo'd cluster column is a caller/config mistake, not an
    # unsuitable sample - so it must propagate as a plain ValueError
    # rather than being caught and buried in a report as an
    # InsufficientDataError diagnostic (which is what every genuine
    # data-insufficiency path here does). Without the guard this surfaces
    # as a raw pandas KeyError from deep inside .loc instead.
    data = pd.DataFrame({
        "y": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    })

    with pytest.raises(ValueError, match="no such column") as excinfo:
        statistical_analysis_module._fit_one_model(
            "ols", "y ~ x", data, "test_model", cov_type="cluster", cluster_col="does_not_exist"
        )
    assert not isinstance(excinfo.value, InsufficientDataError)


def test_fit_one_model_reports_insufficient_data_for_a_cluster_column_with_missing_values():
    data = pd.DataFrame({
        "y": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "grp": ["A", "A", None, "B", "B", "B"],
    })

    results, error = statistical_analysis_module._fit_one_model(
        "ols", "y ~ x", data, "test_model", cov_type="cluster", cluster_col="grp"
    )

    assert results is None
    assert error is not None
    assert "missing value" in error


def test_fit_one_model_reports_insufficient_data_for_a_single_cluster_group():
    data = pd.DataFrame({
        "y": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "grp": ["A", "A", "A", "A", "A", "A"],
    })

    results, error = statistical_analysis_module._fit_one_model(
        "ols", "y ~ x", data, "test_model", cov_type="cluster", cluster_col="grp"
    )

    assert results is None
    assert error is not None
    assert "1 distinct group" in error


def test_significance_comparison_lines_labels_each_coefficient_correctly():
    # A prior version of this file's coverage only checked that either
    # "same conclusion" or "CONCLUSION CHANGES" appeared *somewhere* in
    # the formatted output - a tautology that a flipped `==`/`!=` in the
    # agreement computation cannot fail (with >=1 coefficient, one of the
    # two fixed strings is essentially guaranteed to appear regardless of
    # whether labels are attached to the right coefficient). This asserts
    # the exact label for four hand-picked p-value combinations covering
    # every case: (significant, significant), (not, not), and both
    # directions of a flip.
    hc3 = _FakeSignificanceResults({
        "Intercept": 0.001,  # must be skipped, not compared
        "both_significant": 0.001,
        "both_not_significant": 0.5,
        "flips_to_not_significant": 0.001,
        "flips_to_significant": 0.5,
    })
    clustered = _FakeSignificanceResults({
        "both_significant": 0.001,
        "both_not_significant": 0.5,
        "flips_to_not_significant": 0.5,
        "flips_to_significant": 0.001,
    })

    lines = _significance_comparison_lines(hc3, clustered)
    by_name = {line.split(":")[0].strip("  - "): line for line in lines}

    assert "Intercept" not in by_name
    assert "[same conclusion]" in by_name["both_significant"]
    assert "[same conclusion]" in by_name["both_not_significant"]
    assert "[CONCLUSION CHANGES]" in by_name["flips_to_not_significant"]
    assert "[CONCLUSION CHANGES]" in by_name["flips_to_significant"]


def test_format_cluster_sensitivity_summary_empty_when_not_requested(large_synthetic_kiva_df):
    result = fit_explanatory_models(large_synthetic_kiva_df)
    assert format_cluster_sensitivity_summary(result) == ""


def test_format_cluster_sensitivity_summary_reports_every_coefficient_with_agreement_call(large_synthetic_kiva_df):
    result = fit_explanatory_models(large_synthetic_kiva_df, cluster_sensitivity_col="country_name")
    summary = format_cluster_sensitivity_summary(result)

    assert "Cluster-Robust Sensitivity Check" in summary
    assert "country_name" in summary
    assert "Duration model" in summary
    assert "24-hour funding model" in summary
    # Every non-intercept duration coefficient must appear with both p-values.
    for name in result["duration"].params.index:
        if name == "Intercept":
            continue
        assert name in summary
    assert "HC3 p=" in summary and "clustered p=" in summary
    assert ("same conclusion" in summary) or ("CONCLUSION CHANGES" in summary)
