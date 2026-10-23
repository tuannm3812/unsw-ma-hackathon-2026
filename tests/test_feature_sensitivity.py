import json

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

import src.feature_sensitivity as feature_sensitivity_module
from src.feature_sensitivity import (
    EXPANDED_NARRATIVE_FEATURES,
    PRIMARY_NARRATIVE_FEATURES,
    RICH_CATEGORICAL_CONTROLS,
    build_sensitivity_frame,
    evaluate_nested_ridge,
    fit_clustered_partial_regression,
    write_sensitivity_outputs,
)


@pytest.fixture
def chronological_kiva_df():
    rows = []
    years = [2018, 2019, 2019, 2020, 2020, 2021, 2021, 2022, 2022, 2023, 2023, 2023, 2024, 2024, 2024, 2025, 2025, 2025]
    countries = [("KE", "Kenya", "Africa"), ("PH", "Philippines", "Asia"), ("UG", "Uganda", "Africa")]
    activities = [("Farming", "Agriculture"), ("Retail", "Retail"), ("Food Production", "Food")]
    descriptions = [
        "She is a hardworking mother with two children and a family shop.",
        "He urgently needs clean water and sanitary equipment for his community.",
        "They plan to invest in business stock and thank lenders for support.",
    ]
    for index, year in enumerate(years):
        country_iso, country_name, region = countries[index % len(countries)]
        activity, sector = activities[index % len(activities)]
        posted = pd.Timestamp(year=year, month=1 + index % 6, day=10, tz="UTC")
        rows.append(
            {
                "id": index + 1,
                "status": "funded",
                "borrowerCount": 1 + index % 3,
                "name": f"Borrower {index}",
                "gender": ["female", "male", "female, male"][index % 3],
                "loanAmount": 100.0 + 30 * index,
                "lenderRepaymentTerm": 6 + index % 10,
                "repaymentInterval": ["monthly", "irregularly", "at_end"][index % 3],
                "sector": sector,
                "activity": activity,
                "use": "to buy tools, materials, and stock",
                "city": "Test City",
                "latitude": 0.0,
                "longitude": 0.0,
                "country_iso": country_iso,
                "country_name": country_name,
                "region": region,
                "country_ppp": 1800.0 + 100 * (index % 3),
                "fundsLentInCountry": 100000 + index,
                "country_latitude": 0.0,
                "country_longitude": 0.0,
                "description": descriptions[index % len(descriptions)] + f" She is {25 + index} years old.",
                "whySpecial": "The business supports an underserved family.",
                "image_url": "https://example.test/image.webp",
                "disbursalDate": (posted - pd.Timedelta(days=7)).isoformat(),
                "fundraisingDate": posted.isoformat(),
                "raisedDate": (posted + pd.Timedelta(hours=12 + index * 4)).isoformat(),
            }
        )
    return pd.DataFrame(rows)


def test_sensitivity_frame_exposes_omitted_narrative_families_without_redundant_controls(
    chronological_kiva_df,
):
    frame = build_sensitivity_frame(chronological_kiva_df)

    expected_expanded = {
        "basic_needs_mentions_per_100_words",
        "business_mentions_per_100_words",
        "gratitude_mentions_per_100_words",
        "first_person_mentions_per_100_words",
        "third_person_mentions_per_100_words",
        "number_token_count",
        "age_pattern_count",
        "years_in_business_count",
        "use_word_count",
        "whySpecial_word_count",
        "desc_sentiment_pos",
        "desc_sentiment_neg",
    }
    assert set(PRIMARY_NARRATIVE_FEATURES).issubset(EXPANDED_NARRATIVE_FEATURES)
    assert expected_expanded.issubset(EXPANDED_NARRATIVE_FEATURES)
    assert set(EXPANDED_NARRATIVE_FEATURES).issubset(frame.columns)

    # Country replaces region and activity replaces sector in the richer
    # sensitivity specification; including both nested representations would
    # make the fixed-effect design rank deficient.
    assert "country_iso" in RICH_CATEGORICAL_CONTROLS
    assert "activity" in RICH_CATEGORICAL_CONTROLS
    assert "region" not in RICH_CATEGORICAL_CONTROLS
    assert "region_group" not in RICH_CATEGORICAL_CONTROLS
    assert "sector" not in RICH_CATEGORICAL_CONTROLS
    assert "sector_group" not in RICH_CATEGORICAL_CONTROLS


def test_clustered_partial_regression_matches_statsmodels_on_hand_checked_design():
    rng = np.random.default_rng(17)
    n_clusters = 12
    rows_per_cluster = 18
    n = n_clusters * rows_per_cluster
    cluster = np.repeat([f"c{i}" for i in range(n_clusters)], rows_per_cluster)
    group = np.tile(np.repeat(["a", "b", "c"], 6), n_clusters)
    control = rng.normal(size=n)
    narrative_a = rng.normal(size=n)
    narrative_b = rng.normal(size=n)
    cluster_shock = np.repeat(rng.normal(scale=0.8, size=n_clusters), rows_per_cluster)
    outcome = (
        0.7 * control
        + 0.4 * (group == "b")
        - 0.2 * (group == "c")
        + 1.25 * narrative_a
        - 0.65 * narrative_b
        + cluster_shock
        + rng.normal(scale=0.3, size=n)
    )
    frame = pd.DataFrame(
        {
            "outcome": outcome,
            "control": control,
            "group": group,
            "narrative_a": narrative_a,
            "narrative_b": narrative_b,
            "cluster": cluster,
        }
    )

    actual = fit_clustered_partial_regression(
        frame,
        outcome="outcome",
        narrative_features=["narrative_a", "narrative_b"],
        numeric_controls=["control"],
        categorical_controls=["group"],
        cluster_col="cluster",
        feature_families={"narrative": ["narrative_a", "narrative_b"]},
    )

    reference_x = pd.get_dummies(
        frame[["control", "group", "narrative_a", "narrative_b"]],
        columns=["group"],
        drop_first=True,
        dtype=float,
    )
    reference_x = sm.add_constant(reference_x)
    reference = sm.OLS(frame["outcome"], reference_x).fit(
        cov_type="cluster", cov_kwds={"groups": frame["cluster"]}
    )

    estimates = actual["coefficients"].set_index("feature")
    for feature in ["narrative_a", "narrative_b"]:
        assert np.isclose(estimates.loc[feature, "coefficient"], reference.params[feature], atol=1e-7)
        assert np.isclose(estimates.loc[feature, "standard_error"], reference.bse[feature], rtol=2e-3)
    assert actual["n_rows"] == n
    assert actual["n_clusters"] == n_clusters
    assert actual["joint_tests"].loc[0, "family"] == "narrative"
    assert 0.0 <= actual["joint_tests"].loc[0, "p_value"] <= 1.0
    assert estimates["fdr_p_value"].between(0, 1).all()


def test_clustered_partial_regression_drops_a_numerically_dependent_narrative_column():
    rng = np.random.default_rng(29)
    n = 240
    frame = pd.DataFrame(
        {
            "outcome": rng.normal(size=n),
            "control": rng.normal(size=n),
            "group": np.tile(["a", "b", "c"], n // 3),
            "narrative_a": rng.normal(size=n),
            "narrative_b": rng.normal(size=n),
            "cluster": np.repeat([f"c{i}" for i in range(12)], n // 12),
        }
    )
    frame["narrative_near_sum"] = (
        frame["narrative_a"] + frame["narrative_b"] + rng.normal(scale=1e-6, size=n)
    )

    result = fit_clustered_partial_regression(
        frame,
        outcome="outcome",
        narrative_features=["narrative_a", "narrative_b", "narrative_near_sum"],
        numeric_controls=["control"],
        categorical_controls=["group"],
        cluster_col="cluster",
        feature_families={"narrative": ["narrative_a", "narrative_b", "narrative_near_sum"]},
    )

    assert len(result["dropped_narrative_features"]) == 1
    numeric = result["coefficients"].select_dtypes(include=[np.number]).to_numpy()
    assert np.isfinite(numeric).all()


def test_clustered_partial_regression_uses_neutral_sentiment_as_compositional_reference():
    rng = np.random.default_rng(41)
    n = 240
    positive = rng.uniform(0.05, 0.45, size=n)
    negative = rng.uniform(0.05, 0.45, size=n)
    negative = np.minimum(negative, 0.9 - positive)
    frame = pd.DataFrame(
        {
            "outcome": rng.normal(size=n),
            "control": rng.normal(size=n),
            "desc_sentiment_compound": rng.uniform(-1, 1, size=n),
            "desc_sentiment_pos": positive,
            "desc_sentiment_neg": negative,
            "desc_sentiment_neu": 1.0 - positive - negative,
            "cluster": np.repeat([f"c{i}" for i in range(12)], n // 12),
        }
    )

    result = fit_clustered_partial_regression(
        frame,
        outcome="outcome",
        narrative_features=[
            "desc_sentiment_compound",
            "desc_sentiment_pos",
            "desc_sentiment_neg",
            "desc_sentiment_neu",
        ],
        numeric_controls=["control"],
        categorical_controls=[],
        cluster_col="cluster",
        feature_families={
            "sentiment": [
                "desc_sentiment_compound",
                "desc_sentiment_pos",
                "desc_sentiment_neg",
                "desc_sentiment_neu",
            ]
        },
    )

    assert "desc_sentiment_neu" in result["dropped_narrative_features"]
    assert "desc_sentiment_neu" not in set(result["coefficients"]["feature"])
    assert result["joint_tests"].loc[0, "n_features"] == 3


def test_nested_ridge_reports_all_three_feature_blocks(chronological_kiva_df):
    result = evaluate_nested_ridge(
        chronological_kiva_df,
        holdout_start="2024-01-01",
        n_topics=2,
    )

    assert list(result["blocks"]) == ["structural_only", "primary_narrative", "expanded_narrative"]
    assert result["train_rows"] == 12
    assert result["holdout_rows"] == 6
    assert result["blocks"]["structural_only"]["n_features"] < result["blocks"]["primary_narrative"]["n_features"]
    assert result["blocks"]["primary_narrative"]["n_features"] < result["blocks"]["expanded_narrative"]["n_features"]
    expanded_names = set(result["blocks"]["expanded_narrative"]["included_narrative_features"])
    assert "use_word_count" in expanded_names
    assert "whySpecial_word_count" in expanded_names
    assert {"topic_0", "topic_1"}.issubset(expanded_names)
    for block in result["blocks"].values():
        assert np.isfinite(block["holdout_mae_days"])
        assert np.isfinite(block["holdout_r2"])


def test_nested_ridge_reuses_a_precomputed_feature_frame(chronological_kiva_df, monkeypatch):
    featured = build_sensitivity_frame(chronological_kiva_df)

    def fail_if_recomputed(_frame):
        raise AssertionError("deterministic text features were recomputed")

    monkeypatch.setattr(
        feature_sensitivity_module,
        "extract_deterministic_features",
        fail_if_recomputed,
    )
    result = evaluate_nested_ridge(
        chronological_kiva_df,
        featured_frame=featured,
        holdout_start="2024-01-01",
        n_topics=2,
    )

    assert result["train_rows"] == 12
    assert result["holdout_rows"] == 6


def test_output_writer_persists_machine_and_human_readable_results(tmp_path):
    coefficients = pd.DataFrame(
        [
            {
                "feature": "family_mentions_per_100_words",
                "coefficient": -0.03,
                "standard_error": 0.02,
                "p_value": 0.15,
                "fdr_p_value": 0.20,
            }
        ]
    )
    joint_tests = pd.DataFrame(
        [{"family": "framing", "n_features": 1, "statistic": 2.1, "p_value": 0.15}]
    )
    payload = {
        "generated_at": "2026-09-03T00:00:00Z",
        "prediction": {"blocks": {}},
        "inference": {
            "duration": {
                "n_rows": 10,
                "n_clusters": 3,
                "coefficients": coefficients,
                "joint_tests": joint_tests,
            }
        },
    }

    paths = write_sensitivity_outputs(payload, tmp_path)

    loaded = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert loaded["inference"]["duration"]["coefficients"][0]["feature"] == "family_mentions_per_100_words"
    report = paths["report"].read_text(encoding="utf-8")
    assert "Expanded Feature Sensitivity" in report
    assert "family_mentions_per_100_words" in report
    assert paths["coefficients"].read_text(encoding="utf-8").startswith("outcome,feature,")


@pytest.fixture
def regression_frame():
    rng = np.random.default_rng(71)
    n = 240
    frame = pd.DataFrame({
        "cluster": np.repeat(np.arange(12), 20),
        "group": np.tile(["a", "b", "c"], 80),
        "x": rng.normal(size=n),
        "z": rng.normal(size=n),
    })
    frame["y"] = 0.4 * frame["x"] + rng.normal(size=n)
    return frame


def _fit_fixture(frame, **kwargs):
    options = dict(outcome="y", narrative_features=["x"], numeric_controls=["z"],
                   categorical_controls=["group"], cluster_col="cluster",
                   feature_families={"narrative": ["x"]})
    options.update(kwargs)
    return fit_clustered_partial_regression(frame, **options)


def test_absorbed_narrative_feature_is_not_rescaled_from_solver_noise(regression_frame):
    frame = regression_frame
    frame["absorbed"] = 3.0 + 2.0 * frame["z"] + (frame["group"] == "b")
    result = _fit_fixture(frame, narrative_features=["x", "absorbed"])
    assert result["dropped_narrative_features"] == ["absorbed"]
    assert result["coefficients"]["feature"].tolist() == ["x"]


def test_nested_controls_use_rank_in_cluster_finite_sample_correction(regression_frame):
    frame = regression_frame
    frame["nested"] = (frame["group"] == "a").astype(str)
    baseline = _fit_fixture(frame)
    nested = _fit_fixture(frame, categorical_controls=["group", "nested"])
    assert np.allclose(nested["coefficients"]["standard_error"],
                       baseline["coefficients"]["standard_error"], rtol=1e-8)
    assert nested["control_rank"] == baseline["control_rank"] == 4
    assert nested["full_parameter_count"] == 5


def test_unconverged_partialling_out_fails_instead_of_returning_estimates(
    regression_frame, monkeypatch,
):
    original = feature_sensitivity_module.lsmr

    def unconverged(*args, **kwargs):
        result = list(original(*args, **kwargs))
        result[1] = 7
        return tuple(result)

    monkeypatch.setattr(feature_sensitivity_module, "lsmr", unconverged)
    with pytest.raises(ValueError, match="converg"):
        _fit_fixture(regression_frame)


def test_singular_joint_covariance_does_not_claim_full_family_test(regression_frame):
    frame = regression_frame
    frame["cluster"] = np.repeat([0, 1], len(frame) // 2)
    result = _fit_fixture(frame, narrative_features=["x", "z"], numeric_controls=[],
                          feature_families={"both": ["x", "z"]})
    joint = result["joint_tests"].iloc[0]
    assert joint["covariance_rank"] < joint["n_features"]
    assert joint["test_status"] == "unavailable_singular_covariance"
    assert np.isnan(joint["p_value"])


def test_complete_case_population_reports_exclusions_without_imputing_outcomes(regression_frame):
    frame = regression_frame
    frame.loc[0, "y"] = np.nan
    frame.loc[1, "z"] = np.inf
    frame.loc[2, "group"] = None
    result = _fit_fixture(frame)
    assert result["n_rows"] == len(frame) - 3
    assert result["input_rows"] == len(frame)
    assert result["complete_case_excluded_rows"] == 3
    assert result["missing_by_column"]["y"] == 1


def test_output_writer_preserves_existing_snapshot(tmp_path):
    payload = {"prediction": {"blocks": {}}, "inference": {}}
    paths = write_sensitivity_outputs(payload, tmp_path)
    before = {key: path.read_bytes() for key, path in paths.items()}
    with pytest.raises(FileExistsError, match="snapshot"):
        write_sensitivity_outputs({**payload, "generated_at": "different"}, tmp_path)
    assert before == {key: path.read_bytes() for key, path in paths.items()}


def test_output_writer_uses_json_null_for_unavailable_inference(tmp_path):
    payload = {"prediction": {"blocks": {}}, "inference": {},
               "diagnostic": float("nan")}
    paths = write_sensitivity_outputs(payload, tmp_path)
    loaded = json.loads(paths["json"].read_text())
    assert loaded["diagnostic"] is None


def test_absorbed_reference_indicator_with_many_categories_is_never_estimated():
    # LSMR can stop successfully with residue above the numerical absorption
    # cutoff when a reference indicator is intercept minus hundreds of dummies.
    rng = np.random.default_rng(2)
    n = 12000
    country = rng.integers(0, 48, n)
    programme = country * 13 + rng.integers(0, 13, n)
    programme[rng.random(n) < 0.028] = -1
    frame = pd.DataFrame({
        "country": country.astype(str),
        "programme": programme.astype(str),
        "activity": rng.integers(0, 150, n).astype(str),
        "year": rng.integers(0, 10, n).astype(str),
        "month": rng.integers(0, 12, n).astype(str),
        "z": rng.normal(size=n),
    })
    frame["missing"] = (programme == -1).astype(float)
    frame["x"] = rng.normal(size=n)
    frame["y"] = 0.6 * frame.x + rng.normal(size=n)
    options = dict(
        outcome="y", numeric_controls=["z"],
        categorical_controls=["country", "programme", "activity", "year", "month"],
        cluster_col="country", feature_families={"narrative": ["x", "missing"]},
    )
    result = fit_clustered_partial_regression(
        frame, narrative_features=["x", "missing"], **options,
    )
    assert "missing" in result["dropped_narrative_features"]
    reference = fit_clustered_partial_regression(
        frame, narrative_features=["x"], **options,
    )
    pd.testing.assert_frame_equal(result["coefficients"], reference["coefficients"])
    pd.testing.assert_frame_equal(result["joint_tests"], reference["joint_tests"])
    assert result["full_parameter_count"] == reference["full_parameter_count"]
