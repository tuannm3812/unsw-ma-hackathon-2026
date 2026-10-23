"""Hand-checked coverage and privacy contracts for programme proxy audit."""
import json

import pandas as pd
import pytest

from src import programme_audit


def proxy_fixture():
    return pd.DataFrame({
        "fundraisingDate": ["2020-01-01"] * 7,
        "raisedDate": ["2020-01-02", "2020-01-04", "2020-01-03",
                       "2020-01-05", "2020-01-06", "2020-01-07",
                       "2019-12-31"],
        "whySpecial": ["private alpha", "private alpha", "private beta",
                       "private beta", None, "  ", "excluded text"],
        "country_iso": ["AA", "AA", "AA", "BB", "BB", None, "CC"],
        "description": ["she works", "she works", "his shop", "their farm",
                        "missing programme", "blank programme", "excluded"],
    })


def test_proxy_audit_excludes_invalid_outcomes_and_keeps_missing_separate():
    result = programme_audit.audit_programme_proxy(proxy_fixture(), min_group_size=2)
    assert result["input_rows"] == 7
    assert result["valid_rows"] == 6
    assert result["excluded_rows"] == 1
    assert result["missing_programme_rows"] == 2
    assert result["observed_programme_levels"] == 2
    assert result["single_country_levels"] == 1
    assert result["fully_observed_country_levels"] == 2
    assert result["single_country_level_share"] == 0.5
    assert result["single_country_loan_share_among_observed_programmes"] == 0.5
    assert result["well_populated_levels"] == 2
    assert result["well_populated_mean_days_range"] == [2.0, 3.0]
    assert result["rows_in_repeated_descriptions_among_observed_programmes"] == 2
    assert "private alpha" not in json.dumps(result)
    assert "she works" not in json.dumps(result)


def test_unknown_country_does_not_certify_single_country_nesting():
    frame = proxy_fixture().iloc[:2].copy()
    frame.loc[1, "country_iso"] = None
    result = programme_audit.audit_programme_proxy(frame)
    assert result["fully_observed_country_levels"] == 0
    assert result["single_country_levels"] == 0
    assert result["single_country_level_share"] is None
    assert result["well_populated_mean_days_range"] is None


def test_all_missing_programmes_produce_json_safe_empty_summary():
    frame = proxy_fixture().iloc[4:6].copy()
    result = programme_audit.audit_programme_proxy(frame)
    assert result["observed_programme_levels"] == 0
    assert result["single_country_loan_share_among_observed_programmes"] is None
    json.dumps(result, allow_nan=False)


def test_audit_cli_records_provenance_and_refuses_to_replace_a_run(tmp_path):
    source = tmp_path / "private.pkl"
    proxy_fixture().to_pickle(source)
    destination = tmp_path / "run"
    args = ["--data", str(source), "--output-dir", str(destination),
            "--min-group-size", "2"]
    assert programme_audit.main(args) == 0
    report = json.loads((destination / "programme_audit.json").read_text())
    assert report["audit"]["valid_rows"] == 6
    assert len(report["provenance"]["data_sha256"]) == 64
    assert report["provenance"]["data_filename"] == "private.pkl"
    assert report["provenance"]["source_hashes"]
    with pytest.raises(FileExistsError):
        programme_audit.main(args)
