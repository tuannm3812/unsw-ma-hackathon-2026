"""Appendix experiments, 2026-11-08. Exploratory; no result replaces the benchmark.

Three parts, all on completed loans only:

1. Tuning. HistGradientBoosting and XGBoost, each tuned only on earlier years:
   for test year Y, fit on the as-of training set for Y-1, validate on loans
   posted in Y-1 that completed before Y, choose settings by validation MAE on
   the structure-only arm, then refit on the as-of training set for Y. Both are
   scored on the same test rows with and without text. Validation excludes
   loans still open at the cutoff, so it favours faster loans.
2. Triage. The slowest-20% flag on the fixed and tuned models, with month- and
   country-block intervals for "flag minus lookup".
3. Themes. The 8 NMF themes on the 20,000-description EDA sample, with unadjusted
   means and adjusted contrasts. Exploratory; these are sample results.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as st
from sklearn.decomposition import NMF
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from threadpoolctl import threadpool_limits

from src.benchmark_data import LEXICAL, METADATA, S_CATEGORICAL, S_NUMERIC, calendar_split
from src.benchmark_metrics import paired_loss_intervals, score_predictions
from src.benchmark_models import _context_baseline
from src.data_loader import load_kiva_pickle
from src.strong_forecaster import BENCHMARK_TREE, CONFIG, _design, _svd
from src.triage_baseline import break_ties
from src.triage_value import slow_target, triage_metrics

YEARS = [2021, 2022, 2023, 2024, 2025]
ARMS = ["S", "S+M+L", "S+M+L+D"]
CHECKPOINTS = (100, 300, 500)
HGB_GRID = [{"max_leaf_nodes": n, "learning_rate": r, "min_samples_leaf": m,
             "l2_regularization": 1.0, "early_stopping": False}
            for n in (15, 63) for r in (0.05, 0.1) for m in (20, 100)]
XGB_GRID = [{"max_depth": d, "eta": r, "min_child_weight": m, "lambda": 1.0}
            for d in (4, 8) for r in (0.05, 0.1) for m in (1, 100)]
LARGE_ENCODING = {"max_categories": 255, "missing_as_string": True}
COMPACT_ENCODING = {"max_categories": 127, "missing_as_string": False, "median_impute": True}
TEXT_PAIRS = [("S", "S+M+L"), ("S", "S+M+L+D")]


def validation_split(frame: pd.DataFrame, year: int) -> tuple[np.ndarray, np.ndarray]:
    """Rows to fit and validate on for test year `year`, using only earlier data."""
    fit_rows, posted_prior = calendar_split(frame, year - 1)
    available, _ = calendar_split(frame, year)
    return fit_rows, np.intersect1d(posted_prior, available)


def choose_best(trials: list[dict]) -> dict:
    """Lowest validation MAE; earlier trials win exact ties, so selection is deterministic."""
    if not trials:
        raise ValueError("no tuning trials")
    return min(enumerate(trials), key=lambda t: (t[1]["val_mae"], t[0]))[1]


def days(pred_log: np.ndarray) -> np.ndarray:
    return np.maximum(np.expm1(pred_log), 0)


def _hgb(a, y, cats, params, seed):
    return HistGradientBoostingRegressor(categorical_features=cats, random_state=seed, **params).fit(a, y)


def _xgb_frame(frame, rows, numeric, levels):
    out = frame.iloc[rows][numeric].astype(float).copy()
    for c in S_CATEGORICAL:
        out[c] = pd.Categorical(frame.iloc[rows][c].astype(object), categories=levels[c])
    return out


def _numeric_columns(arm):
    return list(S_NUMERIC) + (METADATA + LEXICAL if "M" in arm else [])


def _xgb_inputs(frame, train, test, arm, svd):
    import xgboost as xgb
    numeric = _numeric_columns(arm)
    levels = {c: pd.Index(frame.iloc[train][c].dropna().unique()) for c in S_CATEGORICAL}
    a, b = _xgb_frame(frame, train, numeric, levels), _xgb_frame(frame, test, numeric, levels)
    if "D" in arm:
        names = [f"svd_{i}" for i in range(svd["train"].shape[1])]
        a[names], b[names] = svd["train"], svd["test"]
    return xgb.DMatrix(a, enable_categorical=True), xgb.DMatrix(b, enable_categorical=True)


def _xgb_train(dtrain, y, params, rounds, seed, threads):
    import xgboost as xgb
    dtrain.set_label(y)
    full = dict(params, objective="reg:squarederror", tree_method="hist", seed=seed, nthread=threads)
    return xgb.train(full, dtrain, num_boost_round=rounds)


def tune_year(frame, year, seed, threads):
    fit_rows, val_rows = validation_split(frame, year)
    y_fit = np.log1p(frame.iloc[fit_rows]["funding_speed_days"].to_numpy(float))
    y_val = frame.iloc[val_rows]["funding_speed_days"].to_numpy(float)
    hgb_trials, xgb_trials = [], []
    a, b, cats = _design(frame, fit_rows, val_rows, "S", None, LARGE_ENCODING)
    for params in HGB_GRID:
        model = _hgb(a, y_fit, cats, dict(params, max_iter=max(CHECKPOINTS)), seed)
        for i, pred in enumerate(model.staged_predict(b), start=1):
            if i in CHECKPOINTS:
                hgb_trials.append({"params": dict(params, max_iter=i),
                                   "val_mae": float(np.mean(np.abs(days(pred) - y_val)))})
    best_hgb = choose_best(hgb_trials)
    dtrain, dval = _xgb_inputs(frame, fit_rows, val_rows, "S", None)
    for params in XGB_GRID:
        booster = _xgb_train(dtrain, y_fit, params, max(CHECKPOINTS), seed, threads)
        for k in CHECKPOINTS:
            pred = booster.predict(dval, iteration_range=(0, k))
            xgb_trials.append({"params": dict(params, rounds=k),
                               "val_mae": float(np.mean(np.abs(days(pred) - y_val)))})
    best_xgb = choose_best(xgb_trials)
    return {"fit_rows": int(len(fit_rows)), "val_rows": int(len(val_rows)),
            "hgb": best_hgb, "xgb": best_xgb, "hgb_trials": hgb_trials, "xgb_trials": xgb_trials}


def score_arm(frame, train, test, arm, svd, family, params, seed, threads):
    y = np.log1p(frame.iloc[train]["funding_speed_days"].to_numpy(float))
    if family == "hgb":
        a, b, cats = _design(frame, train, test, arm, svd, LARGE_ENCODING)
        return days(_hgb(a, y, cats, params, seed).predict(b))
    dtrain, dtest = _xgb_inputs(frame, train, test, arm, svd)
    p = {k: v for k, v in params.items() if k != "rounds"}
    return days(_xgb_train(dtrain, y, p, params["rounds"], seed, threads).predict(dtest))


def block_intervals(ranks: dict, lookup: str, d, groups, country, top10, draws=1000, seed=42):
    """Bootstrap whole blocks; reselect flags and the target within every draw."""
    blocks = [np.flatnonzero(groups == g) for g in np.unique(groups)]
    rng = np.random.default_rng(seed)
    names = [n for n in ranks if n != lookup]
    out = {n: {"lift": [], "within": []} for n in names}
    for picks in rng.integers(0, len(blocks), size=(draws, len(blocks))):
        rows = np.concatenate([blocks[p] for p in picks])
        target = slow_target(d[rows])
        lifts = {n: triage_metrics(r[rows], target, 0.10)["lift"] for n, r in ranks.items()}
        withins = {}
        for n, r in ranks.items():
            values = []
            for c in top10:
                mask = country[rows] == c
                if mask.sum() >= 100:
                    values.append(triage_metrics(r[rows][mask], slow_target(d[rows][mask]), 0.10)["precision"])
            withins[n] = float(np.median(values)) if values else float("nan")
        for n in names:
            out[n]["lift"].append(lifts[n] - lifts[lookup])
            out[n]["within"].append(withins[n] - withins[lookup])
    return {n: {k: np.nanquantile(v, [0.025, 0.975]).tolist() for k, v in out[n].items()} for n in names}


def triage_row(rank, d, country, top10):
    target = slow_target(d)
    within = [triage_metrics(rank[country == c], slow_target(d[country == c]), 0.10)["precision"] for c in top10]
    return {"top_10": triage_metrics(rank, target, 0.10), "top_20": triage_metrics(rank, target, 0.20),
            "within_country_median_precision_top_10": float(np.median(within)),
            "within_country_range": [float(min(within)), float(max(within))]}


def theme_contrasts(frame: pd.DataFrame, theme: str, controls: list[str], categorical: list[str]) -> list[dict]:
    """Each theme against the sample-weighted average theme, with cluster-robust t(G-1)."""
    levels = sorted(frame[theme].unique())
    dummies = pd.get_dummies(frame[theme], prefix="t", dtype=float).iloc[:, 1:]
    cats = pd.get_dummies(frame[categorical].astype(str), drop_first=True, dtype=float) if categorical else pd.DataFrame(index=frame.index)
    X = sm.add_constant(pd.concat([dummies, frame[controls].astype(float), cats], axis=1), has_constant="add")
    codes = frame["country_iso"].astype("category").cat.codes
    fit = sm.OLS(frame["log_days"].astype(float), X).fit(cov_type="cluster", cov_kwds={"groups": codes})
    columns = list(X.columns)
    shares = frame[theme].value_counts(normalize=True)
    df = int(codes.nunique()) - 1
    cov, beta = fit.cov_params().to_numpy(), fit.params.to_numpy()
    rows = []
    for level in levels:
        c = np.zeros(len(columns))
        for other in levels[1:]:
            c[columns.index(f"t_{other}")] = (level == other) - shares[other]
        est = float(c @ beta)
        se = float(np.sqrt(c @ cov @ c))
        half = st.t.ppf(0.975, df) * se
        rows.append({"theme": int(level), "pct_change_in_1_plus_days": 100 * (np.exp(est) - 1),
                     "pct_ci95": [100 * (np.exp(est - half) - 1), 100 * (np.exp(est + half) - 1)],
                     "p": float(2 * st.t.sf(abs(est / se), df))})
    return rows


def run_themes(data_path: Path, cache: pd.DataFrame) -> dict:
    """Refit the EDA notebook's 20,000-description NMF and add adjusted contrasts."""
    raw = load_kiva_pickle(str(data_path))[["description", "loanAmount"]]
    if len(raw) != len(cache):
        raise ValueError("raw and cache rows differ")
    valid = np.flatnonzero(cache["valid_completed_outcome"].to_numpy(bool))
    text = (raw["description"].iloc[valid].fillna("").str.replace(r"<[^>]+>", " ", regex=True)
            .str.replace(r"\s+", " ", regex=True).str.strip())
    sample = text.sample(20_000, random_state=42)
    positions = valid[text.index.get_indexer(sample.index)]
    vectorizer = TfidfVectorizer(max_features=1000, stop_words="english", min_df=5)
    weights = NMF(n_components=8, random_state=42, max_iter=300).fit(vectorizer.fit_transform(sample))
    matrix = weights.transform(vectorizer.transform(sample))
    names = vectorizer.get_feature_names_out()
    words = {i: [names[j] for j in c.argsort()[-8:][::-1]] for i, c in enumerate(weights.components_)}
    frame = cache.iloc[positions].copy().reset_index(drop=True)
    frame["theme"] = matrix.argmax(axis=1)
    frame["log_days"] = np.log1p(frame["funding_speed_days"].astype(float))
    means = frame.groupby("theme")["funding_speed_days"].agg(["mean", "median", "count"])
    numeric = ["log_loan_amount", "lenderRepaymentTerm", "borrowerCount", "is_group_loan"]
    base = ["gender_classification", "loan_size_band", "repaymentInterval", "country_iso",
            "fundraising_year", "fundraising_month"]
    details = {r["theme"]: r for r in theme_contrasts(frame, "theme", numeric, base)}
    with_activity = {r["theme"]: r for r in theme_contrasts(frame, "theme", numeric, base + ["activity"])}
    return {"sample_rows": len(frame), "clusters": int(frame["country_iso"].nunique()),
            "note": "Dominant NMF theme on the EDA 20,000-description sample; sample only. Contrasts compare a "
                    "theme with the sample-weighted average theme.",
            "themes": [{"theme": int(t), "top_words": words[int(t)], "n": int(means.loc[t, "count"]),
                        "mean_days": float(means.loc[t, "mean"]), "median_days": float(means.loc[t, "median"]),
                        "adjusted_loan_details": details[int(t)], "adjusted_plus_activity": with_activity[int(t)]}
                       for t in means.index]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--years", type=int, nargs="*", default=YEARS)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args(argv)
    import xgboost
    frame = pd.read_pickle(args.cache)
    args.output.mkdir(parents=True, exist_ok=True)
    out = {"generated_at": datetime.now(timezone.utc).isoformat(), "xgboost_version": xgboost.__version__,
           "label": "exploratory; completed loans only; retrospective", "themes": None, "years": []}
    path = args.output / "appendix_experiments.json"
    out["themes"] = run_themes(args.data, frame)
    path.write_text(json.dumps(out, indent=1))
    print("themes done", flush=True)
    seed = CONFIG["seed"]
    for year in args.years:
        t0 = time.perf_counter()
        with threadpool_limits(limits=args.threads):
            tuned = tune_year(frame, year, seed, args.threads)
            print(f"{year} tuned in {time.perf_counter()-t0:.0f}s: hgb {tuned['hgb']} xgb {tuned['xgb']}", flush=True)
            train, test = calendar_split(frame, year)
            target = frame.iloc[test]
            y = target["funding_speed_days"].to_numpy(float)
            y01 = target["funded_within_24h"].to_numpy(int)
            svd = _svd(frame, train, test, CONFIG)
            preds = {}
            for family, best in (("hgb", tuned["hgb"]["params"]), ("xgb", tuned["xgb"]["params"])):
                for arm in ARMS:
                    preds[family, arm] = score_arm(frame, train, test, arm, svd, family, best, seed, args.threads)
                    print(f"  {family} {arm} MAE {np.mean(np.abs(preds[family, arm]-y)):.4f}", flush=True)
            yt = np.log1p(frame.iloc[train]["funding_speed_days"].to_numpy(float))
            yb = frame.iloc[train]["funded_within_24h"].to_numpy(int)
            a, b, cats = _design(frame, train, test, "S", None, COMPACT_ENCODING)
            compact = days(_hgb(a, yt, cats, BENCHMARK_TREE, seed).predict(b))
            a, b, cats = _design(frame, train, test, "S", None, LARGE_ENCODING)
            large = days(_hgb(a, yt, cats, CONFIG["tree"], seed).predict(b))
            lookup = _context_baseline(frame, train, test, frame.iloc[train]["funding_speed_days"].to_numpy(float), yb)["days"]
        scores = {"compact_fixed_S": compact, "large_fixed_S": large,
                  "hgb_tuned_S": preds["hgb", "S"], "xgb_tuned_S": preds["xgb", "S"]}
        rec = {"year": year, "tuning": tuned, "test_rows": int(len(test)), "mae": {}, "text_gain": [], "triage": {}}
        for name, p in {**scores, "lookup_B1": lookup}.items():
            rec["mae"][name] = float(score_predictions(y, y01, p, np.clip(np.full(len(y), y01.mean()), 0, 1))["mae_days"])
        for family in ("hgb", "xgb"):
            for arm in ARMS:
                rec["mae"][f"{family}_tuned_{arm}"] = float(np.mean(np.abs(preds[family, arm] - y)))
        months = target["fundraisingDate"].dt.strftime("%Y-%m").to_numpy()
        country = target["country_iso"].to_numpy()
        for family in ("hgb", "xgb"):
            for base, added in TEXT_PAIRS:
                lb, la = np.abs(preds[family, base] - y), np.abs(preds[family, added] - y)
                for unit, g in (("month", months), ("country", country)):
                    rec["text_gain"].append(dict(family=family, baseline=base, candidate=added, unit=unit,
                                                 **paired_loss_intervals(lb, la, g, 1000, seed)))
        top10 = pd.Series(country).value_counts().index[:10]
        rng = np.random.default_rng(seed + year)
        ranks = {n: break_ties(p, rng) for n, p in {**scores, "lookup_B1": lookup}.items()}
        rec["triage"]["models"] = {n: triage_row(r, y, country, top10) for n, r in ranks.items()}
        rec["triage"]["minus_lookup_95"] = {
            "month_block": block_intervals(ranks, "lookup_B1", y, months, country, top10),
            "country_block_lift_only": block_intervals(ranks, "lookup_B1", y, country, country, top10)}
        out["years"].append(rec)
        path.write_text(json.dumps(out, indent=1))
        print(f"{year} done in {time.perf_counter()-t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
