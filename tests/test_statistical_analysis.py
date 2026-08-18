import os

import pandas as pd
import pytest

import src.statistical_analysis as statistical_analysis_module
from src.statistical_analysis import (
    _check_well_identified,
    _term_has_variation,
    fit_explanatory_models,
    format_association_summary,
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
    # out every row whose `region_group` is "Other" (which collapses three
    # of `_LARGE_FIXTURE_REGIONS` - Latin America, Eastern Europe, Pacific -
    # so the whole "Other" level loses variation, not just one raw region).
    frame = large_synthetic_kiva_df.copy()
    from src.data_loader import prepare_analysis_data
    from src.features import extract_deterministic_features

    prepared = prepare_analysis_data(frame)
    featured_probe = extract_deterministic_features(prepared)
    other_mask = featured_probe["region_group"] == "Other"
    frame.loc[other_mask, "description"] = "to buy stock and materials for the business"

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
    assert "has a significant effect" not in content.lower()
