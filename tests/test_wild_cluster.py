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
