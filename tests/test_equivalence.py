"""Offline tests for the exploratory equivalence screen (no dataset needed)."""

import csv
import json

import pytest

from src.equivalence import bh_adjust, main, t_cdf, t_ppf, tost


def test_t_distribution_matches_reference_values():
    assert t_cdf(1.0, 1) == pytest.approx(0.75, abs=1e-9)
    assert t_ppf(0.975, 1) == pytest.approx(12.7062, abs=1e-3)
    assert t_ppf(0.975, 47) == pytest.approx(2.0117, abs=1e-4)
    assert t_cdf(-2.0, 10) == pytest.approx(1 - t_cdf(2.0, 10), abs=1e-12)


def test_tost_accepts_tight_interval_and_rejects_wide_one():
    assert tost(0.0, 0.01, 0.05, 47)[2] < 0.001
    assert tost(0.0, 0.05, 0.05, 47)[2] > 0.1
    assert tost(0.06, 0.001, 0.05, 47)[2] > 0.99  # clearly outside the bound
    p_lo, p_hi, _ = tost(0.0, 1e-6, 0.05, 47)
    assert 0.0 <= p_lo <= 1.0 and 0.0 <= p_hi <= 1.0


def test_bh_adjust_is_monotone_and_in_input_order():
    assert bh_adjust([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.04, 0.04])


def test_cli_writes_reports_for_rate_and_sentiment_terms(tmp_path):
    header = ["outcome", "feature", "coefficient", "standard_error", "t_value",
              "p_value", "fdr_p_value", "ci_low", "ci_high"]
    rows = [
        ["log_funding_speed", "urgency_mentions_per_100_words", "-0.05", "0.05", "", "", "", "", ""],
        ["log_funding_speed", "agency_mentions_per_100_words", "0.004", "0.004", "", "", "", "", ""],
        ["log_funding_speed", "desc_word_count", "0.001", "0.001", "", "", "", "", ""],
        ["funded_within_24h", "desc_sentiment_compound", "-0.002", "0.002", "", "", "", "", ""],
    ]
    for spec in ("expanded", "programme_adjusted"):
        (tmp_path / spec).mkdir()
        with (tmp_path / spec / "narrative_coefficients.csv").open("w", newline="") as f:
            csv.writer(f).writerows([header, *rows])
    main(["--reviewed-dir", str(tmp_path), "--output-dir", str(tmp_path / "out")])
    result = json.loads((tmp_path / "out" / "equivalence_screen.json").read_text())["results"]
    assert {r["feature"] for r in result} == {
        "urgency_mentions_per_100_words", "agency_mentions_per_100_words", "desc_sentiment_compound"}
    by = {(r["specification"], r["feature"]): r for r in result}
    assert by[("expanded", "agency_mentions_per_100_words")]["equivalent"] is True
    assert by[("expanded", "urgency_mentions_per_100_words")]["equivalent"] is False
    assert by[("expanded", "desc_sentiment_compound")]["estimate"] == pytest.approx(-0.001)
