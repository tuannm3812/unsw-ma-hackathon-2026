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

    assert summary["explanatory"]["attempted"] is True
    assert summary["explanatory"]["n_duration"] is not None


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


def test_run_analysis_writes_files_atomically_no_partial_leftover(tmp_path, large_synthetic_kiva_df):
    data_path = tmp_path / "sample.pkl"
    _write_pickle(large_synthetic_kiva_df, data_path)
    output_dir = tmp_path / "reports"
    run_analysis(data_path, output_dir, holdout_start="2024-01-01")

    leftovers = [p for p in output_dir.iterdir() if p.name.startswith(".") or p.suffix == ".tmp"]
    assert leftovers == []
