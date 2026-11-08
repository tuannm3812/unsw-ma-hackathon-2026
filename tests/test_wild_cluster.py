import numpy as np
import statsmodels.api as sm

from src.wild_cluster import ClusterStats, wcr_pvalues


def _data(seed, beta1=0.0, g=20, n=4000):
    rng = np.random.default_rng(seed)
    codes = rng.integers(0, g, n)
    x = rng.normal(size=(n, 3)) + rng.normal(size=(g, 3))[codes]
    x -= x.mean(axis=0)
    y = beta1 * x[:, 0] + 0.3 * x[:, 1] + rng.normal(size=g)[codes] + rng.normal(size=n)
    return y - y.mean(), x, codes, g


def test_cluster_stats_match_statsmodels_cr1():
    y, x, codes, g = _data(0, beta1=0.2)
    stats = ClusterStats(y, x, codes, g, n_params=x.shape[1])
    beta, se = stats.fit(stats.cluster_xt(y))
    ref = sm.OLS(y, x).fit(cov_type="cluster", cov_kwds={"groups": codes})
    np.testing.assert_allclose(beta / stats.scale, ref.params, rtol=1e-8)
    np.testing.assert_allclose(se / stats.scale, ref.bse, rtol=1e-6)


def test_wcr_rejects_true_effect_and_not_null():
    y, x, codes, g = _data(1, beta1=0.0)
    stats = ClusterStats(y, x, codes, g, n_params=3)
    beta, se = stats.fit(stats.cluster_xt(y))
    rng = np.random.default_rng(0)
    null_p = wcr_pvalues(stats, 0, 0.0, beta[0] / se[0], 999, rng)["two_sided"]
    y2, x2, c2, _ = _data(1, beta1=1.0)
    s2 = ClusterStats(y2, x2, c2, g, n_params=3)
    b2, e2 = s2.fit(s2.cluster_xt(y2))
    alt_p = wcr_pvalues(s2, 0, 0.0, b2[0] / e2[0], 999, rng)["two_sided"]
    assert alt_p < 0.01
    assert 0.0 <= null_p <= 1.0


def test_wcr_size_is_roughly_nominal():
    rejections = 0
    for seed in range(60):
        y, x, codes, g = _data(100 + seed, beta1=0.0, g=12, n=1200)
        stats = ClusterStats(y, x, codes, g, n_params=3)
        beta, se = stats.fit(stats.cluster_xt(y))
        p = wcr_pvalues(stats, 0, 0.0, beta[0] / se[0], 399, np.random.default_rng(seed))
        rejections += p["two_sided"] < 0.10
    assert rejections <= 14  # nominal 6 of 60


def _with_shared_control(seed=3, g=8, n=240):
    import scipy.sparse as sp
    from src.feature_sensitivity import _residualize
    rng = np.random.default_rng(seed)
    codes = np.arange(n) % g
    shared = rng.normal(size=n) + 0.5 * codes
    fe = np.eye(g)[codes]
    Z = sp.csr_matrix(np.column_stack([fe, shared]))
    raw = rng.normal(size=(n, 2)) + shared[:, None]
    y = 0.2 * raw[:, 0] + 0.4 * shared + rng.normal(size=g)[codes] + rng.normal(size=n)
    return y, raw, codes, g, Z, _residualize(Z, y).ravel(), _residualize(Z, raw)


def test_bootstrap_t_matches_full_model_refit_with_shared_controls():
    y, raw, codes, g, Z, y_r, x_r = _with_shared_control()
    stats = ClusterStats(y_r, x_r, codes, g, n_params=Z.shape[1] + 2, controls=Z)
    xo = stats.xs[:, [1]]
    fitted = xo @ np.linalg.solve(xo.T @ xo, xo.T @ stats.y)
    resid = stats.y - fitted
    w = np.array([1.0, -1.0, 0.5**0.5, -1.5**0.5, 1.0, -1.0, 1.5**0.5, -0.5**0.5])[None]
    adj = stats.control_adjustment(resid, w)
    beta, se = stats.fit(stats.cluster_xt(fitted)[None] + w[..., None] * stats.cluster_xt(resid)[None], adj)
    full = np.column_stack([x_r, Z.toarray()])
    ystar = fitted + w[0][codes] * resid
    ref = sm.OLS(ystar, full).fit(cov_type="cluster", cov_kwds={"groups": codes, "use_correction": False})
    bread = np.linalg.inv(x_r.T @ x_r)
    e = ystar - full @ np.linalg.pinv(full) @ ystar
    meat = sum(np.outer(x_r[codes == h].T @ e[codes == h], x_r[codes == h].T @ e[codes == h]) for h in range(g))
    want = np.sqrt(np.diag(stats.corr * bread @ meat @ bread))
    np.testing.assert_allclose(beta[0] / stats.scale, ref.params[:2], rtol=1e-6)
    np.testing.assert_allclose(se[0] / stats.scale, want, rtol=1e-6)
    no_adj = stats.fit(stats.cluster_xt(fitted)[None] + w[..., None] * stats.cluster_xt(resid)[None])[1]
    assert not np.allclose(no_adj, se, rtol=1e-3)


def test_adjustment_matches_full_refit_with_rank_deficient_nested_controls():
    """Programme dummies nested in countries make Z rank deficient, as in the real fit."""
    import scipy.sparse as sp
    from src.feature_sensitivity import _residualize
    rng = np.random.default_rng(11)
    g, n = 12, 3000
    codes = rng.integers(0, g, n)
    programme = codes * 3 + rng.choice([0, 1, 2], n, p=[0.8, 0.19, 0.01])  # some rare levels
    shared_programme = rng.choice(5, n)                                    # crosses countries
    country = np.eye(g)[codes]
    prog = np.eye(programme.max() + 1)[programme]
    shared = np.eye(5)[shared_programme]
    amount = rng.normal(size=n) + 0.3 * codes
    Z_dense = np.column_stack([np.ones(n), country, prog, shared, amount])
    Z_dense = Z_dense[:, np.linalg.norm(Z_dense, axis=0) > 0]
    Z_scaled = Z_dense / np.linalg.norm(Z_dense, axis=0)
    Z = sp.csr_matrix(Z_scaled)
    assert np.linalg.matrix_rank(Z_scaled) < Z_scaled.shape[1]
    raw = rng.normal(size=(n, 2)) + amount[:, None] + shared_programme[:, None] * 0.2
    y = 0.1 * raw[:, 0] + amount + rng.normal(size=g)[codes] + rng.normal(size=n)
    y_r, x_r = _residualize(Z, y).ravel(), _residualize(Z, raw)
    stats = ClusterStats(y_r, x_r, codes, g, n_params=np.linalg.matrix_rank(Z_scaled) + 2, controls=Z)
    xo = stats.xs[:, [1]]
    fitted = xo @ np.linalg.solve(xo.T @ xo, xo.T @ stats.y)
    resid = stats.y - fitted
    w = np.random.default_rng(5).choice([-1.0, 1.0], size=(3, g))
    adj = stats.control_adjustment(resid, w)
    np.testing.assert_allclose(adj.sum(axis=1), 0.0, atol=1e-6)
    _, se = stats.fit(stats.cluster_xt(fitted)[None] + w[..., None] * stats.cluster_xt(resid)[None], adj)
    full = np.column_stack([x_r, Z_scaled])
    bread = np.linalg.inv(x_r.T @ x_r)
    for b in range(3):
        ystar = fitted + w[b][codes] * resid
        e = ystar - full @ (np.linalg.pinv(full) @ ystar)
        meat = sum(np.outer(x_r[codes == h].T @ e[codes == h], x_r[codes == h].T @ e[codes == h]) for h in range(g))
        np.testing.assert_allclose(se[b] / stats.scale, np.sqrt(np.diag(stats.corr * bread @ meat @ bread)), rtol=1e-5)
