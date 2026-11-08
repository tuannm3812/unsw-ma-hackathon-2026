"""Experiment I: loan-detail coefficients from the October programme-adjusted model.

Exploratory extension, 2026-11-08. The October inference saved coefficients for
the narrative terms only, because every control was partialled out. This module
refits the same specification on the same eligible records and moves the loan
details from the absorbed block into the reported block. By Frisch-Waugh-Lovell
that leaves the fitted model unchanged, so the framing coefficients must match
the saved October table; `--compare` checks that against the saved file.

Absorbed: country, posting year, posting month, programme proxy.
Reported: the narrative terms, loan amount, repayment term, borrower count,
group loan, gender, loan-size band, repayment interval and activity.

Units. The duration outcome is log(1 + days), so exp(b) - 1 is a percentage
change in (1 + days), not in days. The 24-hour outcome is a linear probability
model, reported in percentage points.

Reading limits. Loan amount and loan-size band are in the model together, so
"per doubling" is a doubling within a band. Borrower count and the group-loan
indicator are likewise joint. These are associations among completed loans with
country-clustered CR1 standard errors and a t(47) reference. Lenders may respond
to the listing, and partners choose loan terms, so none of this is an effect of
changing a loan. This module deliberately produces no importance ranking and no
ratio of loan details to framing.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import stats as st

from src.feature_sensitivity import (
    EXPANDED_NARRATIVE_FEATURES, _control_matrix, _independent_columns, _residualize,
)
from src.wild_cluster import ClusterStats

ABSORBED = ["country_iso", "fundraising_year", "fundraising_month", "programme_proxy"]
OUTCOMES = ["log_funding_speed", "funded_within_24h"]
CATEGORIES = {  # column: fixed reference, or None for the most common level
    "gender_classification": None, "loan_size_band": "small",
    "repaymentInterval": None, "activity": None,
}
NUMERIC = {  # column: (edit size, unit)
    "log_loan_amount": (math.log(2), "per doubling of loan amount, within loan-size band"),
    "lenderRepaymentTerm": (1.0, "per additional month of repayment term"),
    "borrowerCount": (1.0, "per additional borrower, holding the group-loan indicator"),
    "is_group_loan": (1.0, "group loan vs individual loan, holding borrower count"),
}
FRAMING_SCALE = {
    **{f"{n}_mentions_per_100_words": 1.0 for n in (
        "family", "basic_needs", "business", "agency", "gratitude",
        "urgency", "first_person", "third_person")},
    "desc_sentiment_compound": 0.5,
}
EXPECTED = {"rows": 1453840, "clusters": 48, "parameters": 906}


def add_dummies(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Add one 0/1 column per non-reference level; return column metadata."""
    new, meta = {}, {}
    for column, reference in CATEGORIES.items():
        values = frame[column].astype(str)
        counts = values.value_counts()
        base = reference or str(counts.index[0])
        if base not in counts.index:
            raise ValueError(f"reference {base!r} not found in {column}")
        for level in sorted(counts.index):
            if level == base:
                continue
            name = f"{column}__{level}"
            new[name] = (values == level).to_numpy(float)
            meta[name] = {"group": column, "level": level, "reference": base,
                          "records": int(counts[level])}
    return pd.concat([frame, pd.DataFrame(new, index=frame.index)], axis=1), meta


def focal_columns(frame: pd.DataFrame, dummies: dict) -> tuple[list[str], list[str]]:
    narrative = [f for f in EXPANDED_NARRATIVE_FEATURES if f != "desc_sentiment_neu"]
    requested = narrative + list(NUMERIC) + list(dummies)
    absorbed = []
    for control in ABSORBED:  # exact nesting: as in fit_clustered_partial_regression
        remaining = [c for c in requested if c not in absorbed]
        grouped = frame[remaining].groupby(frame[control].astype(str), sort=False)
        constant = grouped.min().eq(grouped.max()).all()
        absorbed.extend(constant.index[constant])
    return [c for c in requested if c not in absorbed], absorbed


def design(frame: pd.DataFrame, focal: list[str], outcomes: list[str], n_jobs: int) -> dict:
    controls, _ = _control_matrix(frame, [], ABSORBED)
    eigenvalues = np.linalg.eigvalsh((controls.T @ controls).toarray())
    control_rank = int(np.sum(eigenvalues > 1e-10 * eigenvalues[-1]))
    raw = frame[focal + outcomes].to_numpy(float)
    parts = Parallel(n_jobs=n_jobs, verbose=5)(
        delayed(_residualize)(controls, raw[:, [j]]) for j in range(raw.shape[1]))
    residual = np.hstack(parts)
    k = len(focal)
    x, kept, dropped = _independent_columns(
        residual[:, :k], focal, np.linalg.norm(raw[:, :k], axis=0))
    codes, labels = pd.factorize(frame["country_name"], sort=True)
    return {"x": x, "kept": kept, "dropped": dropped, "y": dict(zip(outcomes, residual[:, k:].T)),
            "codes": codes, "clusters": len(labels), "control_rank": control_rank}


def fit(d: dict, outcome: str) -> dict:
    n_params = d["control_rank"] + len(d["kept"])
    stats = ClusterStats(d["y"][outcome], d["x"], d["codes"], d["clusters"], n_params)
    xty = stats.cluster_xt(stats.y)
    beta = xty.sum(axis=0) @ stats.inv
    scores = xty - stats.A @ beta
    cov = stats.corr * stats.inv @ (scores.T @ scores) @ stats.inv
    inverse = 1.0 / stats.scale
    return {"beta": beta * inverse, "cov": cov * np.outer(inverse, inverse),
            "n_params": n_params, "n_rows": stats.n, "clusters": stats.g}


def contrast_row(c: np.ndarray, beta, cov, df, outcome) -> dict:
    """Estimate, CR1 SE, t(df) interval and display units for a linear contrast."""
    estimate = float(c @ beta)
    se = float(np.sqrt(c @ cov @ c))
    half = st.t.ppf(0.975, df) * se
    low, high = estimate - half, estimate + half
    row = {"estimate": estimate, "cr1_se": se, "ci95": [low, high],
           "p_t47": float(2 * st.t.sf(abs(estimate / se), df))}
    if outcome == "log_funding_speed":
        row["pct_change_in_1_plus_days"] = 100 * (math.exp(estimate) - 1)
        row["pct_ci95"] = [100 * (math.exp(low) - 1), 100 * (math.exp(high) - 1)]
    else:
        row["pp_change_24h"] = 100 * estimate
        row["pp_ci95"] = [100 * low, 100 * high]
    return row


def report(frame, d, fitted, dummies, outcome) -> dict:
    beta, cov, df = fitted["beta"], fitted["cov"], fitted["clusters"] - 1
    index = {name: i for i, name in enumerate(d["kept"])}

    def row(name, scale, extra):
        c = np.zeros(len(beta))
        c[index[name]] = scale
        return {"term": name, **extra, **contrast_row(c, beta, cov, df, outcome)}

    def scaled_sd(name, scale):
        sd = float(frame[name].std(ddof=0))
        return row(name, sd, {"unit": "per 1 SD of this column", "sd": sd,
                              "edit_scale_for_reference": scale})

    framing = [row(n, s, {"unit": "per +1 mention per 100 words" if s == 1.0
                          else "per +0.5 VADER compound"})
               for n, s in FRAMING_SCALE.items() if n in index]
    numeric = [row(n, s, {"unit": u}) for n, (s, u) in NUMERIC.items() if n in index]
    per_sd = [scaled_sd(n, s) for n, s in FRAMING_SCALE.items() if n in index]
    per_sd += [scaled_sd(n, s) for n, (s, _) in NUMERIC.items() if n in index]
    categories = [row(n, 1.0, {**m, "unit": f"{m['level']} vs {m['reference']}"})
                  for n, m in dummies.items() if n in index]
    # Reference-free summary of the activity block: each sector's loan-weighted
    # mean activity effect minus the loan-weighted mean over all loans.
    activity = frame["activity"].astype(str)
    shares = activity.value_counts(normalize=True)
    sectors = []
    for sector, group in frame.groupby(frame["sector"].astype(str), sort=True):
        inside = group["activity"].astype(str).value_counts(normalize=True)
        c = np.zeros(len(beta))
        for level, overall in shares.items():
            name = f"activity__{level}"
            if name in index:
                c[index[name]] = inside.get(level, 0.0) - overall
        sectors.append({"sector": sector, "records": int(len(group)),
                        "unit": "average loan in this sector vs average loan overall",
                        **contrast_row(c, beta, cov, df, outcome)})
    return {"framing": framing, "numeric": numeric, "per_1_sd": per_sd,
            "categories": categories, "sector_contrasts": sectors}


def compare(result_path: Path, saved_csv: Path) -> dict:
    """Compare every reported narrative term with the saved October table."""
    result = json.loads(result_path.read_text())
    saved = pd.read_csv(saved_csv)
    out = {}
    for outcome, body in result["outcomes"].items():
        table = saved[saved["outcome"] == outcome].set_index("feature")
        rows = []
        for term, new in body["raw_narrative"].items():
            if term not in table.index:
                raise ValueError(f"{term} missing from saved table")
            old = table.loc[term]
            rows.append({"term": term, "saved": float(old["coefficient"]), "refit": new["estimate"],
                         "abs_diff": abs(float(old["coefficient"]) - new["estimate"]),
                         "se_abs_diff": abs(float(old["standard_error"]) - new["cr1_se"])})
        framing = [r for r in rows if r["term"] in FRAMING_SCALE]
        out[outcome] = {"terms_compared": len(rows),
                        "same_terms_as_saved": sorted(table.index) == sorted(body["raw_narrative"]),
                        "max_coef_abs_diff": max(r["abs_diff"] for r in rows),
                        "max_se_abs_diff": max(r["se_abs_diff"] for r in rows),
                        "framing": framing}
    result["comparison_with_saved_october_table"] = {"file": str(saved_csv), **out}
    result_path.write_text(json.dumps(result, indent=1))
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--frame", type=Path, default=Path("reports/inference_private/review_frame.pkl"))
    parser.add_argument("--output", type=Path, default=Path("reports/loan_detail_coefficients"))
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument("--compare", type=Path, help="existing result JSON to compare with the saved table")
    parser.add_argument("--saved", type=Path, default=Path(
        "reports/expanded_feature_sensitivity_reviewed/programme_adjusted/narrative_coefficients.csv"))
    args = parser.parse_args(argv)
    if args.compare:
        for outcome, body in compare(args.compare, args.saved).items():
            print(outcome, {k: v for k, v in body.items() if k != "framing"})
        return 0
    frame, dummies = add_dummies(pd.read_pickle(args.frame))
    focal, absorbed = focal_columns(frame, dummies)
    print(f"{len(focal)} focal columns; absorbed before fitting: {absorbed}", flush=True)
    d = design(frame, focal, OUTCOMES, args.n_jobs)
    print(f"residualised; dropped {d['dropped']}; control rank {d['control_rank']}", flush=True)
    out = {"generated_at": datetime.now(timezone.utc).isoformat(),
           "specification": "October programme-adjusted, loan details moved to the reported block",
           "absorbed": ABSORBED, "absorbed_before_fitting": absorbed,
           "dropped_for_rank": d["dropped"], "outcomes": {},
           "limits": ("Completed loans only; associations, not effects of changing a loan; CR1 "
                      "standard errors with t(47). Duration percentages are changes in (1 + days). "
                      "Loan amount is within loan-size band; borrower count and group loan are "
                      "joint. No importance ranking or loan-details-to-framing ratio.")}
    args.output.mkdir(parents=True, exist_ok=True)
    for outcome in OUTCOMES:
        fitted = fit(d, outcome)
        for label, got in [("rows", fitted["n_rows"]), ("clusters", fitted["clusters"]),
                           ("parameters", fitted["n_params"])]:
            if got != EXPECTED[label]:
                print(f"WARNING {outcome}: {label} {got} != expected {EXPECTED[label]}", flush=True)
        body = report(frame, d, fitted, dummies, outcome)
        narrative = [n for n in EXPANDED_NARRATIVE_FEATURES if n in d["kept"]]
        se = np.sqrt(np.diag(fitted["cov"]))
        body["raw_narrative"] = {n: {"estimate": float(fitted["beta"][d["kept"].index(n)]),
                                     "cr1_se": float(se[d["kept"].index(n)])} for n in narrative}
        body["rows"], body["clusters"], body["parameters"] = (
            fitted["n_rows"], fitted["clusters"], fitted["n_params"])
        out["outcomes"][outcome] = body
        (args.output / "loan_detail_coefficients.json").write_text(json.dumps(out, indent=1))
        print(f"{outcome} done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
