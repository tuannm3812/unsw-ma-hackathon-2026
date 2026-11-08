"""Wild cluster restricted bootstrap for the October narrative coefficients.

Exploratory extension, 2026-11-08. The October inference uses CR1 standard
errors with a t(47) reference over 48 countries, but records behave like about
5.7 effective countries. The equivalence screen's t(4) stress test and the
regional t(1) screens are heuristics on unchanged standard errors. The wild
cluster restricted (WCR) bootstrap with Webb six-point weights is the standard
calibrated alternative when clusters are few or unbalanced (Cameron, Gelbach
and Miller 2008; MacKinnon and Webb 2017).

The fit is done in Frisch-Waugh-Lovell form. Controls are partialled out once
with the same helpers as `src.feature_sensitivity`; the bootstrap then runs on
cluster-level sufficient statistics, so each draw costs O(G k^2), not O(n k).

For each term j and null value d, the null beta_j = d is imposed, restricted
residuals are flipped by cluster weights, the model is refitted and a CR1 t
statistic is formed. This gives:

* a two-sided p-value for beta_j = 0 (significance);
* one-sided p-values for beta_j <= -b and beta_j >= +b (bootstrap TOST).
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from src.feature_sensitivity import (
    EXPANDED_NARRATIVE_FEATURES, RICH_CATEGORICAL_CONTROLS, RICH_NUMERIC_CONTROLS,
    _complete_case_frame, _control_matrix, _independent_columns, _residualize,
)

WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])
TERMS = {
    "family_mentions_per_100_words": 1.0, "basic_needs_mentions_per_100_words": 1.0,
    "business_mentions_per_100_words": 1.0, "agency_mentions_per_100_words": 1.0,
    "gratitude_mentions_per_100_words": 1.0, "urgency_mentions_per_100_words": 1.0,
    "first_person_mentions_per_100_words": 1.0, "third_person_mentions_per_100_words": 1.0,
    "desc_sentiment_compound": 0.5,
}
BOUNDS = {"log_funding_speed": 0.05, "funded_within_24h": 0.01}


def residualize_design(frame, outcome, categorical_controls):
    """Return residualised y, X, kept names, cluster codes and parameter count."""
    features = [f for f in EXPANDED_NARRATIVE_FEATURES if f != "desc_sentiment_neu"]
    data = _complete_case_frame(frame, outcome, features, RICH_NUMERIC_CONTROLS,
                                categorical_controls, "country_name")
    controls, _ = _control_matrix(data, RICH_NUMERIC_CONTROLS, categorical_controls)
    gram = (controls.T @ controls).toarray()
    eig = np.linalg.eigvalsh(gram)
    control_rank = int(np.sum(eig > 1e-10 * eig[-1]))
    y = _residualize(controls, data[outcome].to_numpy(float)).ravel()
    raw = data[features].to_numpy(float)
    x = _residualize(controls, raw)
    x, kept, _ = _independent_columns(x, features, np.linalg.norm(raw, axis=0))
    codes, labels = pd.factorize(data["country_name"], sort=True)
    return y, x, kept, codes, len(labels), control_rank + len(kept), controls


class ClusterStats:
    """Cluster-level cross-products for fast OLS/CR1 refits."""

    def __init__(self, y, x, codes, n_clusters, n_params, controls=None):
        self.g, self.k, self.n = n_clusters, x.shape[1], len(y)
        self.scale = np.linalg.norm(x, axis=0)
        xs = x / self.scale
        self.xs, self.y, self.codes = xs, y, codes
        self.A = np.zeros((self.g, self.k, self.k))
        for gi in range(self.g):
            rows = codes == gi
            self.A[gi] = xs[rows].T @ xs[rows]
        self.XtX = self.A.sum(axis=0)
        self.inv = np.linalg.inv(self.XtX)
        self.corr = (self.g / (self.g - 1)) * ((self.n - 1) / (self.n - n_params))
        # Partialled-out controls. Cluster-flipped residuals are not orthogonal
        # to shared controls, so a full-model refit also removes their fitted
        # part; `control_adjustment` reproduces that from cluster statistics.
        self.controls = controls
        if controls is not None:
            gram = (controls.T @ controls).toarray()
            self.gram_pinv = np.linalg.pinv(gram, rcond=1e-10, hermitian=True)
            self.rows = [np.flatnonzero(codes == gi) for gi in range(self.g)]
            self.x_z = np.stack([(controls[r].T @ xs[r]).T for r in self.rows])

    def cluster_xt(self, v):
        out = np.zeros((self.g, self.k))
        np.add.at(out, self.codes, self.xs * v[:, None])
        return out

    def control_adjustment(self, resid, weights):
        """Cluster scores of the controls' fitted part of weights * resid.

        Returns (draws, G, k): x_g' Z (Z'Z)^- sum_h w_h Z_h' u_h.
        """
        z_u = np.stack([self.controls[r].T @ resid[r] for r in self.rows])
        cross = self.x_z @ (self.gram_pinv @ z_u.T)     # (g, k, h)
        return np.moveaxis(weights[None] @ np.moveaxis(cross, (1, 2), (0, 1)), 0, 2)

    def fit(self, xty_g, adjustment=0.0):
        """xty_g: (..., G, k) cluster X'y. Returns beta (..., k), se (..., k)."""
        beta = xty_g.sum(axis=-2) @ self.inv.T
        scores = xty_g - np.einsum("gij,...j->...gi", self.A, beta) - adjustment
        meat = np.einsum("...gi,...gj->...ij", scores, scores)
        cov = self.corr * self.inv @ meat @ self.inv
        se = np.sqrt(np.clip(np.diagonal(cov, axis1=-2, axis2=-1), 0, None))
        return beta, se


def wcr_pvalues(stats: ClusterStats, j: int, null: float, t_obs: float,
                draws: int, rng) -> dict:
    """Bootstrap the t statistic for beta_j (scaled units) under beta_j = null."""
    others = [i for i in range(stats.k) if i != j]
    xo = stats.xs[:, others]
    y0 = stats.y - null * stats.xs[:, j]
    br = np.linalg.solve(xo.T @ xo, xo.T @ y0)
    fitted = xo @ br + null * stats.xs[:, j]
    resid = stats.y - fitted
    b_g, c_g = stats.cluster_xt(fitted), stats.cluster_xt(resid)
    w = WEBB[rng.integers(0, 6, size=(draws, stats.g))]
    adjustment = 0.0 if stats.controls is None else stats.control_adjustment(resid, w)
    beta, se = stats.fit(b_g[None] + w[..., None] * c_g[None], adjustment)
    t = (beta[:, j] - null) / se[:, j]
    return {"two_sided": float(np.mean(np.abs(t) >= abs(t_obs))),
            "upper": float(np.mean(t >= t_obs)), "lower": float(np.mean(t <= t_obs))}


def run_spec(frame, outcome, categorical_controls, draws, seed):
    y, x, kept, codes, g, n_params, controls = residualize_design(
        frame, outcome, categorical_controls)
    stats = ClusterStats(y, x, codes, g, n_params, controls)
    beta_s, se_s = stats.fit(stats.cluster_xt(y))
    rng = np.random.default_rng(seed)
    bound = BOUNDS[outcome]
    rows = []
    for name, edit in TERMS.items():
        if name not in kept:
            continue
        j = kept.index(name)
        # Convert between per-edit units and scaled-design units.
        unit = edit / stats.scale[j]
        est, se = beta_s[j] * unit, se_s[j] * unit
        t0 = beta_s[j] / se_s[j]
        p0 = wcr_pvalues(stats, j, 0.0, t0, draws, rng)
        lo_null, hi_null = -bound / unit, bound / unit
        p_lo = wcr_pvalues(stats, j, lo_null, (beta_s[j] - lo_null) / se_s[j], draws, rng)["upper"]
        p_hi = wcr_pvalues(stats, j, hi_null, (beta_s[j] - hi_null) / se_s[j], draws, rng)["lower"]
        rows.append({"feature": name, "edit_scale": edit, "estimate": float(est),
                     "cr1_se": float(se), "t": float(t0), "p_t47": None,
                     "wcr_p_zero": p0["two_sided"], "bound": bound,
                     "wcr_p_tost": float(max(p_lo, p_hi)),
                     "wcr_p_lower": float(p_lo), "wcr_p_upper": float(p_hi)})
        print(f"  {name}: est={est:.5f} p0={p0['two_sided']:.4f} "
              f"tost={max(p_lo, p_hi):.4f}", flush=True)
    from scipy import stats as st
    from statsmodels.stats.multitest import multipletests
    for r in rows:
        r["p_t47"] = float(2 * st.t.sf(abs(r["t"]), g - 1))
    tost_bh = multipletests([r["wcr_p_tost"] for r in rows], method="fdr_bh")[1]
    zero_bh = multipletests([r["wcr_p_zero"] for r in rows], method="fdr_bh")[1]
    for r, a, b in zip(rows, tost_bh, zero_bh):
        r["wcr_p_tost_bh"], r["wcr_p_zero_bh"] = float(a), float(b)
        r["equivalent_wcr"] = bool(a < 0.05)
    return {"outcome": outcome, "n_rows": int(len(y)), "n_clusters": int(g),
            "draws": draws, "weights": "Webb six-point", "rows": rows}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--frame", type=Path, default=Path("reports/inference_private/review_frame.pkl"))
    parser.add_argument("--output", type=Path, default=Path("reports/wild_cluster_bootstrap"))
    parser.add_argument("--draws", type=int, default=9999)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)
    frame = pd.read_pickle(args.frame)
    out = {"generated_at": datetime.now(timezone.utc).isoformat(),
           "method": "WCR bootstrap, CR1 t statistic, Webb weights, FWL form",
           "bounds": BOUNDS, "edit_units": TERMS, "results": {}}
    args.output.mkdir(parents=True, exist_ok=True)
    for spec, extra in [("expanded", []), ("programme_adjusted", ["programme_proxy"])]:
        for outcome in BOUNDS:
            print(f"{spec} / {outcome}", flush=True)
            out["results"][f"{spec}/{outcome}"] = run_spec(
                frame, outcome, RICH_CATEGORICAL_CONTROLS + extra, args.draws, args.seed)
            (args.output / "wild_cluster.json").write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
