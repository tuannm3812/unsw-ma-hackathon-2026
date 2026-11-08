import numpy as np
import pandas as pd
import statsmodels.api as sm

import src.loan_detail_coefficients as ld


def _frame(n=6000, seed=0):
    rng = np.random.default_rng(seed)
    f = pd.DataFrame({
        "country_iso": rng.choice(list("ABCDEFGH"), n),
        "fundraising_year": rng.choice([2020, 2021], n),
        "fundraising_month": rng.choice([1, 2, 3], n),
        "programme_proxy": rng.choice(["p", "q", "r"], n),
        "gender_classification": rng.choice(["female", "female", "male"], n),
        "loan_size_band": rng.choice(["small", "medium", "large"], n),
    })
    f["country_name"] = f["country_iso"]
    f["x1"] = rng.normal(size=n)
    f["group_x"] = (f["gender_classification"] == "male").astype(float)
    f["y"] = 0.3 * f["x1"] + 0.5 * f["group_x"] + rng.normal(size=n)
    return f


def test_add_dummies_uses_fixed_and_modal_references(monkeypatch):
    monkeypatch.setattr(ld, "CATEGORIES", {"gender_classification": None, "loan_size_band": "small"})
    out, meta = ld.add_dummies(_frame())
    assert meta["gender_classification__male"]["reference"] == "female"
    assert {m["reference"] for k, m in meta.items() if "band" in k} == {"small"}
    assert "loan_size_band__small" not in meta
    assert out["loan_size_band__large"].isin([0.0, 1.0]).all()


def test_contrast_row_units():
    beta, cov = np.array([np.log(1.5)]), np.array([[0.0001]])
    row = ld.contrast_row(np.array([1.0]), beta, cov, 47, "log_funding_speed")
    assert abs(row["pct_change_in_1_plus_days"] - 50.0) < 1e-9
    pp = ld.contrast_row(np.array([1.0]), np.array([0.02]), cov, 47, "funded_within_24h")
    assert abs(pp["pp_change_24h"] - 2.0) < 1e-9


def test_fit_matches_full_ols_with_cr1(monkeypatch):
    monkeypatch.setattr(ld, "ABSORBED", ["country_iso", "fundraising_year"])
    frame = _frame()
    d = ld.design(frame, ["x1", "group_x"], ["y"], n_jobs=1)
    got = ld.fit(d, "y")
    X = pd.concat([frame[["x1", "group_x"]],
                   pd.get_dummies(frame[["country_iso", "fundraising_year"]].astype(str), drop_first=True).astype(float)], axis=1)
    X = sm.add_constant(X)
    ref = sm.OLS(frame["y"], X).fit(cov_type="cluster", cov_kwds={"groups": frame["country_name"].astype("category").cat.codes})
    assert got["n_params"] == X.shape[1]
    np.testing.assert_allclose(got["beta"], ref.params[["x1", "group_x"]].to_numpy(), rtol=1e-6)
    np.testing.assert_allclose(np.sqrt(np.diag(got["cov"])), ref.bse[["x1", "group_x"]].to_numpy(), rtol=1e-5)


def test_doubling_scale_uses_log1p_at_the_median():
    amounts = pd.Series(np.log1p([100.0, 325.0, 1000.0]))
    scale, median = ld.doubling_scale(amounts)
    assert abs(median - 325) < 1e-6
    assert abs(scale - np.log(651 / 326)) < 1e-9
