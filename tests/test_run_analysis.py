import json
import os
import pickle

import pytest

from src.run_analysis import run_analysis


def _write_pickle(df, path):
    with path.open("wb") as handle:
        pickle.dump(df.to_dict("records"), handle)


def test_run_analysis_writes_auditable_reports(tmp_path, large_synthetic_kiva_df):
    data_path = tmp_path / "sample.pkl"
    with data_path.open("wb") as handle:
        pickle.dump(large_synthetic_kiva_df.to_dict("records"), handle)
    output_dir = tmp_path / "reports"
    summary = run_analysis(data_path, output_dir, holdout_start="2024-01-01")
    assert (output_dir / "analysis_summary.json").exists()
    assert (output_dir / "association_summary.txt").exists()
    saved = json.loads((output_dir / "analysis_summary.json").read_text())
    assert saved["data"]["n_rows"] == len(large_synthetic_kiva_df)
    assert saved["data"]["holdout_start"] == "2024-01-01"
    assert "_artifacts" not in saved
    assert summary["data"]["date_min"] <= summary["data"]["date_max"]


def test_refunded_status_rows_are_included_and_reported_separately(tmp_path, large_synthetic_kiva_df):
    # The full competition dataset (unlike the 100-row dev sample, which is
    # entirely "funded") also has a "refunded" status: a loan that
    # completed funding (valid raisedDate, normal funding-speed
    # distribution) but was later refunded to lenders - an unrelated,
    # post-disbursal event. This project models funding speed, not
    # repayment outcome, so refunded rows must be included on the same
    # footing as funded ones (valid_completed_outcome doesn't look at
    # status), and the audit trail must report the split so a reader can
    # see the decision, not just its silent effect.
    frame = large_synthetic_kiva_df.copy()
    frame.iloc[0:3, frame.columns.get_loc("status")] = "refunded"
    data_path = tmp_path / "sample.pkl"
    _write_pickle(frame, data_path)
    output_dir = tmp_path / "reports"

    summary = run_analysis(data_path, output_dir, holdout_start="2024-01-01")
    status_counts = summary["data"]["status_counts_among_valid"]

    assert status_counts.get("refunded") == 3
    assert status_counts.get("funded") == len(frame) - 3
    # All rows in this fixture have a valid completed outcome regardless of
    # status - refunded rows are not silently dropped.
    assert summary["data"]["n_valid_completed_outcome"] == len(frame)

    report_text = (output_dir / "association_summary.txt").read_text()
    assert "refunded" in report_text


def test_analysis_summary_json_has_no_nested_artifacts(tmp_path, large_synthetic_kiva_df):
    data_path = tmp_path / "sample.pkl"
    _write_pickle(large_synthetic_kiva_df, data_path)
    output_dir = tmp_path / "reports"
    run_analysis(data_path, output_dir, holdout_start="2024-01-01")
    saved = json.loads((output_dir / "analysis_summary.json").read_text())

    def _walk(node):
        if isinstance(node, dict):
            assert "_artifacts" not in node
            for value in node.values():
                _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(saved)


def test_run_analysis_records_audit_trail_and_versions(tmp_path, large_synthetic_kiva_df):
    data_path = tmp_path / "sample.pkl"
    _write_pickle(large_synthetic_kiva_df, data_path)
    output_dir = tmp_path / "reports"
    summary = run_analysis(data_path, output_dir, holdout_start="2024-01-01")

    data_section = summary["data"]
    assert data_section["n_rows"] == len(large_synthetic_kiva_df)
    assert data_section["n_valid_completed_outcome"] <= data_section["n_rows"]
    assert data_section["n_excluded"] == data_section["n_rows"] - data_section["n_valid_completed_outcome"]
    assert isinstance(data_section["exclusion_reasons"], dict)
    assert isinstance(data_section["period_counts"], dict)
    assert data_section["date_min"] <= data_section["date_max"]
    assert data_section["holdout_start"] == "2024-01-01"

    versions = summary["software_versions"]
    for key in ("python", "pandas", "numpy", "scikit_learn", "statsmodels"):
        assert key in versions
        assert isinstance(versions[key], str) and versions[key]

    import numpy
    import pandas
    import sklearn
    import statsmodels

    assert versions["pandas"] == pandas.__version__
    assert versions["numpy"] == numpy.__version__
    assert versions["scikit_learn"] == sklearn.__version__
    assert versions["statsmodels"] == statsmodels.__version__

    assert summary["baseline_ridge"]["succeeded"] is True
    assert "metrics" in summary["baseline_ridge"]

    # A regression that breaks the nonlinear benchmark on a normally-sized
    # split must fail this test, not silently degrade to a "diagnostic"
    # with nothing to catch it.
    assert summary["nonlinear_benchmark"]["attempted"] is True
    assert summary["nonlinear_benchmark"]["succeeded"] is True
    assert summary["nonlinear_benchmark"]["error"] is None
    assert "metrics" in summary["nonlinear_benchmark"]

    assert summary["explanatory"]["attempted"] is True
    assert summary["explanatory"]["n_duration"] is not None
    # No missing predictor values on this fixture, so the actual fitted
    # design size must match the eligible-row count exactly.
    assert summary["explanatory"]["duration_model_n"] == summary["explanatory"]["n_duration"]
    # Both explanatory sub-models fit on this well-behaved synthetic
    # fixture, so status must be the strict "success", not just "attempted".
    assert summary["explanatory"]["status"] == "success"

    assert summary["binary_classifier"]["attempted"] is True
    assert summary["binary_classifier"]["succeeded"] is True
    assert summary["binary_classifier"]["error"] is None
    metrics = summary["binary_classifier"]["metrics"]
    assert "roc_auc" in metrics and "average_precision" in metrics and "brier_score" in metrics


def test_run_analysis_reports_partial_success_when_only_one_explanatory_model_fits(
    tmp_path, separated_binary_kiva_df,
):
    # `separated_binary_kiva_df` forces quasi-complete separation in the
    # 24-hour binary explanatory model while the duration model fits fine
    # - exactly the real 100-row development sample's behavior. The old
    # `succeeded` semantics reported `True` here (the stage "attempted"
    # without raising), which an automated consumer could misread as
    # "everything in this section is trustworthy." `status` must say
    # "partial_success", and `succeeded` must be strictly `False` since
    # not everything fit.
    data_path = tmp_path / "sample.pkl"
    _write_pickle(separated_binary_kiva_df, data_path)
    output_dir = tmp_path / "reports"
    summary = run_analysis(data_path, output_dir, holdout_start="2024-01-01")

    explanatory = summary["explanatory"]
    assert explanatory["attempted"] is True
    assert explanatory["duration_fitted"] is True
    assert explanatory["binary_fitted"] is False
    assert explanatory["status"] == "partial_success"
    assert explanatory["succeeded"] is False

    report_text = (output_dir / "association_summary.txt").read_text()
    assert "24-Hour Funding Classifier" in report_text


def test_run_analysis_resolves_paths_without_assuming_cwd(tmp_path, large_synthetic_kiva_df, monkeypatch):
    data_path = tmp_path / "sample.pkl"
    _write_pickle(large_synthetic_kiva_df, data_path)
    output_dir = tmp_path / "reports_relative"

    other_cwd = tmp_path / "elsewhere"
    other_cwd.mkdir()
    monkeypatch.chdir(other_cwd)

    # Relative to the *new* cwd, not to the repo root or the original cwd.
    rel_data = os.path.relpath(data_path, other_cwd)
    rel_output = os.path.relpath(output_dir, other_cwd)

    summary = run_analysis(rel_data, rel_output, holdout_start="2024-01-01")
    assert (output_dir / "analysis_summary.json").exists()
    assert summary["data"]["n_rows"] == len(large_synthetic_kiva_df)


def test_run_analysis_records_diagnostic_when_nonlinear_split_too_small(tmp_path, large_synthetic_kiva_df):
    data_path = tmp_path / "sample.pkl"
    _write_pickle(large_synthetic_kiva_df, data_path)
    output_dir = tmp_path / "reports"

    # Far-future holdout boundary leaves far fewer than
    # MIN_SPLIT_OBSERVATIONS rows (if any) on the holdout side, which must
    # produce a diagnostic instead of crashing the whole run.
    summary = run_analysis(data_path, output_dir, holdout_start="2025-12-15")

    nonlinear = summary["nonlinear_benchmark"]
    assert nonlinear["attempted"] is True
    if not nonlinear["succeeded"]:
        assert nonlinear["error"]
    assert (output_dir / "analysis_summary.json").exists()
    assert (output_dir / "association_summary.txt").exists()


def test_run_analysis_does_not_swallow_unrelated_value_errors(tmp_path, large_synthetic_kiva_df, monkeypatch):
    # The "catch and record a diagnostic" pattern exists specifically for
    # the chronological split being too small - not as a blanket net for
    # any ValueError anywhere in the call chain. A genuinely different bug
    # (e.g. a misconfigured predictor allowlist, or an unrelated modeling
    # error) must still crash loudly, not get silently downgraded into a
    # report that merely looks like "sample too small."
    import src.run_analysis as run_analysis_module

    def _broken_evaluate_chronological_models(*args, **kwargs):
        raise ValueError("predictor allowlist references a column that does not exist")

    monkeypatch.setattr(
        run_analysis_module, "evaluate_chronological_models", _broken_evaluate_chronological_models
    )

    data_path = tmp_path / "sample.pkl"
    _write_pickle(large_synthetic_kiva_df, data_path)
    output_dir = tmp_path / "reports"

    with pytest.raises(ValueError, match="predictor allowlist"):
        run_analysis(data_path, output_dir, holdout_start="2024-01-01")


def test_run_analysis_does_not_swallow_unrelated_explanatory_value_errors(
    tmp_path, large_synthetic_kiva_df, monkeypatch
):
    # Same principle as the chronological-stage test above, applied to the
    # explanatory (Task 5) stage: fit_explanatory_models raising a
    # ValueError for a reason unrelated to insufficient data (e.g. a bug
    # in feature extraction or formula construction) must propagate, not
    # get silently recorded as a "couldn't fit" diagnostic.
    import src.run_analysis as run_analysis_module

    def _broken_fit_explanatory_models(*args, **kwargs):
        raise ValueError("unexpected formula-construction bug")

    monkeypatch.setattr(
        run_analysis_module, "fit_explanatory_models", _broken_fit_explanatory_models
    )

    data_path = tmp_path / "sample.pkl"
    _write_pickle(large_synthetic_kiva_df, data_path)
    output_dir = tmp_path / "reports"

    with pytest.raises(ValueError, match="unexpected formula-construction bug"):
        run_analysis(data_path, output_dir, holdout_start="2024-01-01")


def test_run_analysis_still_degrades_when_neither_explanatory_model_fits(
    tmp_path, large_synthetic_kiva_df, monkeypatch
):
    # The expected "neither model could be fit" case must still degrade
    # gracefully to a report diagnostic, not crash - this is the behavior
    # narrowing the except clause must preserve.
    from src.validation import InsufficientDataError

    import src.run_analysis as run_analysis_module

    def _unfittable_explanatory_models(*args, **kwargs):
        raise InsufficientDataError("fit_explanatory_models could not fit either model: forced for test")

    monkeypatch.setattr(
        run_analysis_module, "fit_explanatory_models", _unfittable_explanatory_models
    )

    data_path = tmp_path / "sample.pkl"
    _write_pickle(large_synthetic_kiva_df, data_path)
    output_dir = tmp_path / "reports"

    summary = run_analysis(data_path, output_dir, holdout_start="2024-01-01")

    assert summary["explanatory"]["attempted"] is True
    assert summary["explanatory"]["succeeded"] is False
    assert summary["explanatory"]["status"] == "failed"
    assert "could not fit either model" in summary["explanatory"]["error"]
    # Other sections are unaffected by the explanatory stage's failure.
    assert summary["baseline_ridge"]["succeeded"] is True
    assert (output_dir / "analysis_summary.json").exists()
    assert (output_dir / "association_summary.txt").exists()


def test_run_analysis_writes_files_atomically_no_partial_leftover(tmp_path, large_synthetic_kiva_df):
    data_path = tmp_path / "sample.pkl"
    _write_pickle(large_synthetic_kiva_df, data_path)
    output_dir = tmp_path / "reports"
    run_analysis(data_path, output_dir, holdout_start="2024-01-01")

    leftovers = [p for p in output_dir.iterdir() if p.name.startswith(".") or p.suffix == ".tmp"]
    assert leftovers == []


def test_run_analysis_appends_cluster_sensitivity_check_when_requested(tmp_path, large_synthetic_kiva_df):
    # Codex review follow-up: confirms the full CLI-to-report wiring for
    # the cluster-robust sensitivity check, not just the underlying
    # statistical_analysis.py functions (already covered directly in
    # tests/test_statistical_analysis.py).
    data_path = tmp_path / "sample.pkl"
    _write_pickle(large_synthetic_kiva_df, data_path)
    output_dir = tmp_path / "reports"

    summary = run_analysis(
        data_path, output_dir, holdout_start="2024-01-01", cluster_sensitivity_col="country_name",
    )

    assert summary["explanatory"]["cluster_sensitivity_col"] == "country_name"
    assert summary["explanatory"]["duration_clustered_fitted"] is True
    assert summary["explanatory"]["binary_clustered_fitted"] is True

    report_text = (output_dir / "association_summary.txt").read_text()
    assert "Cluster-Robust Sensitivity Check" in report_text
    assert "country_name" in report_text


def test_run_analysis_omits_cluster_sensitivity_section_by_default(tmp_path, large_synthetic_kiva_df):
    data_path = tmp_path / "sample.pkl"
    _write_pickle(large_synthetic_kiva_df, data_path)
    output_dir = tmp_path / "reports"

    summary = run_analysis(data_path, output_dir, holdout_start="2024-01-01")

    assert "cluster_sensitivity_col" not in summary["explanatory"]
    report_text = (output_dir / "association_summary.txt").read_text()
    assert "Cluster-Robust Sensitivity Check" not in report_text
