import os

import pandas as pd
import pytest

from src.statistical_analysis import fit_explanatory_models, format_association_summary, run_ols_analysis


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
    # Every pre-specified coefficient must be reported, not only p < 0.05 ones.
    reported_coef_lines = [
        line for line in summary.splitlines() if line.strip().startswith("- ")
    ]
    assert len(reported_coef_lines) >= n_duration_terms


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
