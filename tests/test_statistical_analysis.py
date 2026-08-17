import os

import pandas as pd
import pytest

from src.statistical_analysis import (
    _term_has_variation,
    fit_explanatory_models,
    format_association_summary,
    run_ols_analysis,
)


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
