import numpy as np
import pandas as pd

import src.appendix_experiments as ax


def _frame():
    posted = pd.to_datetime(["2019-06-01", "2020-03-01", "2020-11-20", "2021-02-01", "2020-05-01", "2019-12-30"], utc=True)
    done = pd.to_datetime(["2019-06-05", "2020-03-02", "2021-01-15", "2021-02-03", "2020-05-02", "2020-01-02"], utc=True)
    return pd.DataFrame({"fundraisingDate": posted, "raisedDate": done, "valid_completed_outcome": True})


def test_validation_uses_only_loans_completed_before_the_test_cutoff():
    fit_rows, val = ax.validation_split(_frame(), 2021)
    assert list(fit_rows) == [0]                 # completed before 2020
    assert list(val) == [1, 4]                   # posted 2020, complete before 2021; row 2 is still open


def test_choose_best_is_deterministic_on_ties():
    trials = [{"val_mae": 2.0, "id": 1}, {"val_mae": 1.0, "id": 2}, {"val_mae": 1.0, "id": 3}]
    assert ax.choose_best(trials)["id"] == 2


def test_theme_contrasts_weighted_sum_to_zero():
    rng = np.random.default_rng(0)
    n = 4000
    frame = pd.DataFrame({"theme": rng.choice([0, 1, 2], n, p=[.5, .3, .2]), "x": rng.normal(size=n),
                          "country_iso": rng.choice(list("ABCDEFGHIJ"), n)})
    frame["log_days"] = 0.4 * (frame["theme"] == 1) + 0.2 * frame["x"] + rng.normal(size=n)
    rows = ax.theme_contrasts(frame, "theme", ["x"], ["country_iso"])
    shares = frame["theme"].value_counts(normalize=True)
    weighted = sum(shares[r["theme"]] * np.log1p(r["pct_change_in_1_plus_days"] / 100) for r in rows)
    assert abs(weighted) < 1e-8
    t1 = next(r for r in rows if r["theme"] == 1)
    assert t1["pct_ci95"][0] > 0
