"""Systematic sweep of EVERY raw field against funding speed, to check the
deck hasn't missed a material driver. Same valid-row filter as the EDA
notebook (non-null, non-negative funding_speed_days -> 1,453,840 rows).

Numeric fields: Pearson + Spearman with speed, and the mean-speed spread
across deciles. Categorical fields (cardinality <= 700): mean/median speed
per level with counts, reported as the spread between the largest and
smallest well-populated level (>= 1,000 loans).
"""
import pickle
import numpy as np
import pandas as pd

pd.set_option("display.width", 200)

with open("data/Kiva_Loans.pkl", "rb") as f:
    df = pd.DataFrame(pickle.load(f))

fr = pd.to_datetime(df["fundraisingDate"], errors="coerce", utc=True)
ra = pd.to_datetime(df["raisedDate"], errors="coerce", utc=True)
di = pd.to_datetime(df["disbursalDate"], errors="coerce", utc=True)
df["funding_speed_days"] = (ra - fr).dt.total_seconds() / 86400
df["disbursal_lead_days"] = (fr - di).dt.total_seconds() / 86400
df["fundraising_year"] = fr.dt.year
df["fundraising_month"] = fr.dt.month
df["desc_word_count"] = df["description"].astype(str).str.split().str.len()

v = df.loc[df["funding_speed_days"].notna() & (df["funding_speed_days"] >= 0)].copy()
assert len(v) == 1453840, len(v)
y = v["funding_speed_days"]
print(f"valid rows: {len(v):,}   mean speed {y.mean():.2f}d   median {y.median():.2f}d\n")

SKIP = {"id", "name", "image_url", "description", "use", "funding_speed_days",
        "fundraisingDate", "raisedDate", "disbursalDate"}

print("=" * 96)
print("NUMERIC FIELDS — correlation with speed, and decile spread")
print("=" * 96)
print(f"{'field':<26}{'pearson':>9}{'spearman':>10}{'D1 mean':>10}{'D10 mean':>10}{'ratio':>8}")
num_rows = []
for c in v.columns:
    if c in SKIP:
        continue
    s = pd.to_numeric(v[c], errors="coerce")
    if s.notna().sum() < 100_000 or s.nunique() < 10:
        continue
    ok = s.notna()
    pear = s[ok].corr(y[ok])
    spear = s[ok].corr(y[ok], method="spearman")
    try:
        d = pd.qcut(s[ok], 10, duplicates="drop")
        g = y[ok].groupby(d, observed=True).mean()
        lo, hi = g.iloc[0], g.iloc[-1]
        ratio = hi / lo if lo > 0 else float("nan")
    except Exception:
        lo = hi = ratio = float("nan")
    num_rows.append((c, pear, spear, lo, hi, ratio))
for c, pear, spear, lo, hi, ratio in sorted(num_rows, key=lambda r: -abs(r[1])):
    print(f"{c:<26}{pear:>9.3f}{spear:>10.3f}{lo:>10.2f}{hi:>10.2f}{ratio:>8.2f}")

print("\n" + "=" * 96)
print("CATEGORICAL FIELDS — spread across levels with >= 1,000 loans")
print("=" * 96)
print(f"{'field':<22}{'levels':>7}{'used':>6}{'fastest level':>34}{'mean':>7}{'slowest level':>34}{'mean':>7}")
for c in v.columns:
    if c in SKIP:
        continue
    if v[c].dtype.kind in "ifc" and v[c].nunique() > 50:
        continue
    nu = v[c].nunique()
    if nu < 2 or nu > 700:
        continue
    g = y.groupby(v[c].astype(str), observed=True).agg(["mean", "count"])
    g = g[g["count"] >= 1000].sort_values("mean")
    if len(g) < 2:
        continue
    fast, slow = g.index[0], g.index[-1]
    print(f"{c:<22}{nu:>7}{len(g):>6}{str(fast)[:33]:>34}{g['mean'].iloc[0]:>7.1f}"
          f"{str(slow)[:33]:>34}{g['mean'].iloc[-1]:>7.1f}")

print("\n" + "=" * 96)
print("SPECIFIC CHECKS the deck relies on")
print("=" * 96)
grp = pd.to_numeric(v["borrowerCount"], errors="coerce") > 1
print(f"group loans (borrowerCount>1): n={grp.sum():,} mean {y[grp].mean():.2f}d median {y[grp].median():.2f}d"
      f"  |  individual: n={(~grp).sum():,} mean {y[~grp].mean():.2f}d median {y[~grp].median():.2f}d")
st = y.groupby(v["status"].astype(str)).agg(["mean", "count"])
print("status:\n", st.round(2).to_string())
ws = y.groupby(v["whySpecial"].astype(str)).agg(["mean", "count"])
ws = ws[ws["count"] >= 1000].sort_values("mean")
print(f"whySpecial levels >=1k loans: {len(ws)}  fastest {ws['mean'].iloc[0]:.1f}d  slowest {ws['mean'].iloc[-1]:.1f}d")
