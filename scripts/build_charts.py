#!/usr/bin/env python3
"""Rebuild the eight slide exhibits with UNIFORM typography.

Every chart uses the same point sizes (TITLE/LABEL/TICK/ANNOT below) and is
sized at its intended physical on-slide size, saved at 300 dpi - so inserting
any exported PNG at native size (no rescaling) renders text identically
across all exhibits. Figure dimensions vary with content; type does not.

All values below are TRANSCRIBED literals. Their provenance: printed by the
executed notebooks, taken from the authoritative snapshot, or computed once
from data/Kiva_Loans.pkl (verified 2026-09-01; the collaboration log records
the run). A plain run only proves image reproducibility from these literals.
Run `python3 scripts/build_charts.py --verify` to RECOMPUTE every
pkl-derived aggregate from the raw data and assert it equals the literals
(loads the 1.45M-row pickle; takes a minute or two). Printed-notebook values
(topic means, SHAP, few-cluster table, period shares) are outside --verify's
scope - their source is each block's comment.

Palette: navy ink #1C2333, viridis blue #31688E, team yellow #FFDD04
(fills only - never text on a light ground), viridis purple #440154.
Typeface: DM Sans (committed under docs/presentation/fonts/); a real
GoogleSans/ProductSans TTF dropped into that folder is auto-preferred.
Run: python3 scripts/build_charts.py && python3 scripts/build_slides_draft.py
"""
import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

OUT = "docs/presentation/charts/"
INK = "#1C2333"; BLUE = "#31688E"; YELLOW = "#FFDD04"; MUTED = "#6E7278"
PURPLE = "#440154"; LINE = "#D9D6CC"
DPI = 300
TITLE = 13; LABEL = 10.5; TICK = 10; ANNOT = 9.5; EMPH = 12

FONT_DIR = "docs/presentation/fonts/"
family = None
for pattern, name in (("GoogleSans*", None), ("ProductSans*", None), ("DMSans*", "DM Sans")):
    files = sorted(glob.glob(FONT_DIR + pattern + ".ttf"))
    if files:
        for f in files:
            fm.fontManager.addfont(f)
        family = name or fm.FontProperties(fname=files[0]).get_name()
        break
plt.rcParams.update({
    "font.size": TICK, "axes.edgecolor": LINE, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK,
    "xtick.labelsize": TICK, "ytick.labelsize": TICK,
})
if family:
    plt.rcParams["font.family"] = family
    print("charts typeface:", family)

VIRIDIS = plt.get_cmap("viridis")


def finish(fig, name, out_dir=None):
    # Fixed-size save: the PNG's physical size EQUALS the authored figsize
    # (bbox_inches="tight" would grow it and force downscaling on the slide).
    try:
        fig.tight_layout()
    except Exception:
        pass
    fig.savefig((out_dir or OUT) + name, facecolor="white", dpi=DPI)
    plt.close(fig)


# ---- S4: 24h share by period (EDA SS4 printed shares) --------------------
fig, ax = plt.subplots(figsize=(4.5, 3.3))
# period Ns (589,823 / 298,549 / 565,474) live in the Figure's Notes
# caption - keeping tick labels short so they don't collide at native size
labels = ["Pre-pandemic", "Pandemic\ndisruption", "Post-pandemic\n(to 2025)"]
vals = [46.0, 30.3, 30.0]
bars = ax.bar(labels, vals, color=[BLUE, YELLOW, YELLOW], width=0.62,
              edgecolor=[BLUE, INK, INK], linewidth=[0, 1, 1])
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width()/2, v + 1.2, f"{v:.0f}%", ha="center",
            fontsize=EMPH, weight="bold")
ax.set_ylabel("Funded within 24 hours (%)", fontsize=LABEL)
ax.set_ylim(0, 54); ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Same-day funding has not recovered", fontsize=TITLE,
             weight="bold", pad=10, loc="left")
finish(fig, "period_24h.png")

# ---- S7: topic means (EDA SS8 printout; 8 NMF topics) --------------------
topics = [("Sanitation & toilets", 1.46), ("Clean drinking water", 1.81),
          ("Pig raising", 7.26), ("Philippine small business", 7.80),
          ("General store goods", 8.96), ("Family business & income", 10.70),
          ("Smallholder farming", 12.51), ("Group solar / farm plots", 13.49)]
fig, ax = plt.subplots(figsize=(4.55, 3.0))
names = [t[0] for t in topics][::-1]; means = [t[1] for t in topics][::-1]
ax.barh(names, means, color=[VIRIDIS(m / 15.0) for m in means], height=0.66)
for y, m in enumerate(means):
    ax.text(m + 0.2, y, f"{m:.1f}", va="center", fontsize=ANNOT, weight="bold")
ax.set_xlabel("Mean funding speed (days)", fontsize=LABEL); ax.set_xlim(0, 15.6)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Story themes (8 NMF topics):\na ninefold gap", fontsize=TITLE,
             weight="bold", pad=10, loc="left")
finish(fig, "topics.png")

# ---- A2: SHAP top-15 (modeling SS8 printout) -----------------------------
shap = [("Loan amount (log)", 0.4462), ("Repayment term", 0.3373),
        ("Pre-pandemic period", 0.2201), ("Small loan-size band", 0.1490),
        ("Sector: Retail", 0.0777), ("Gender: female", 0.0646),
        ("Pandemic-disruption period", 0.0535), ("Region: Asia", 0.0445),
        ("Sector: Food", 0.0436), ("Sector: Education", 0.0393),
        ("Sentiment (VADER compound)", 0.0368), ("Gender: male", 0.0362),
        ("Post-pandemic period", 0.0263), ("Region: Africa", 0.0237),
        ("Sector: Sanitation & Hygiene", 0.0200)]
fig, ax = plt.subplots(figsize=(4.55, 3.9))
names = [s[0] for s in shap][::-1]; vals = [s[1] for s in shap][::-1]
ax.barh(names, vals, color=[YELLOW if "Sentiment" in n else BLUE for n in names],
        edgecolor=[INK if "Sentiment" in n else BLUE for n in names],
        linewidth=0.7, height=0.66)
ax.set_xlabel("mean |SHAP value| (boosted model,\n2,000-loan holdout sample)", fontsize=LABEL)
ax.spines[["top", "right"]].set_visible(False)
fig.suptitle("SHAP top 15: sentiment (11th) is\nthe only narrative feature",
             fontsize=TITLE, weight="bold", x=0.02, y=0.99, ha="left", va="top")
fig.tight_layout(rect=(0, 0, 1, 0.905))
fig.subplots_adjust(top=0.86)   # close the gap tight_layout leaves under the suptitle
fig.savefig(OUT + "shap_top15.png", facecolor="white", dpi=DPI); plt.close(fig)

# ---- A3: the 10x correlation basis (EDA SS9 printout) --------------------
corr = [("Loan amount (log)", 0.429), ("Repayment term", 0.285),
        ("Competence/agency mentions", 0.058), ("Family mentions", 0.019),
        ("Urgency mentions", 0.010)]
fig, ax = plt.subplots(figsize=(4.55, 2.7))
names = [c[0] for c in corr][::-1]; vals = [c[1] for c in corr][::-1]
ax.barh(names, vals, color=[YELLOW, YELLOW, YELLOW, BLUE, BLUE],
        edgecolor=[INK, INK, INK, BLUE, BLUE], linewidth=0.7, height=0.6)
for y, v in enumerate(vals):
    ax.text(v + 0.008, y, f"{v:.3f}", va="center", fontsize=ANNOT, weight="bold")
ax.set_xlabel("|correlation| with funding speed", fontsize=LABEL)
ax.set_xlim(0, 0.5); ax.spines[["top", "right"]].set_visible(False)
ax.set_title("The “~10×” claim, exactly:\nstructure vs narrative", fontsize=TITLE,
             weight="bold", pad=10, loc="left")
finish(fig, "correlations.png")

# ---- S5: sector means (computed from raw pkl; counts verified) -----------
SECTORS = [("Sanitation & Hygiene", 0.91, 6905), ("Clean Energy", 1.54, 35342),
           ("Personal Use", 3.06, 46323), ("Manufacturing", 4.21, 9024),
           ("Water", 5.30, 1466), ("Housing", 6.05, 81853),
           ("Arts", 6.43, 18328), ("Education", 6.48, 40302),
           ("Reuse & Recycle", 7.67, 17133), ("Health", 8.72, 17570),
           ("Food", 9.59, 304913), ("Other", 10.31, 1524),
           ("Retail", 10.37, 276710), ("Agriculture", 10.84, 461563),
           ("Construction", 10.95, 10769), ("Services", 10.98, 63205),
           ("Transportation", 11.96, 19577), ("Clothing", 12.12, 41333)]
OVERALL_MEAN = 9.47
fig, ax = plt.subplots(figsize=(4.55, 4.5))
names = [x[0] for x in SECTORS]; means = [x[1] for x in SECTORS]; ns = [x[2] for x in SECTORS]
ax.barh(names, means, color=[VIRIDIS(m / 13.5) for m in means], height=0.7)
ax.axvline(OVERALL_MEAN, color=INK, linestyle="--", linewidth=1)
ax.text(OVERALL_MEAN + 0.2, 0.1, f"avg {OVERALL_MEAN:.1f}", fontsize=ANNOT, color=MUTED)
for y, (m, n) in enumerate(zip(means, ns)):
    ax.text(m + 0.2, y, f"{m:.1f} (n={n:,})", va="center", fontsize=9, color=MUTED)
ax.set_xlabel("Mean funding speed (days)", fontsize=LABEL); ax.set_xlim(0, 16.4)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Sector spans an order of\nmagnitude in speed", fontsize=TITLE,
             weight="bold", pad=10, loc="left")
finish(fig, "sector.png")

# ---- A1: region means (computed from raw pkl; counts verified) -----------
REGIONS = [("North America", 3.71, 7559), ("Asia", 8.18, 738191),
           ("Africa", 10.29, 610368), ("Middle East", 11.01, 14946),
           ("Oceania", 14.23, 23385), ("Central America", 15.56, 59391)]
fig, ax = plt.subplots(figsize=(4.55, 2.7))
names = [x[0] for x in REGIONS]; means = [x[1] for x in REGIONS]; ns = [x[2] for x in REGIONS]
ax.barh(names, means, color=[VIRIDIS(m / 16.5) for m in means], height=0.62)
ax.axvline(OVERALL_MEAN, color=INK, linestyle="--", linewidth=1)
for y, (m, n) in enumerate(zip(means, ns)):
    ax.text(m + 0.25, y, f"{m:.1f} (n={n:,})", va="center", fontsize=ANNOT, color=MUTED)
ax.set_xlabel("Mean funding speed (days)", fontsize=LABEL); ax.set_xlim(0, 20.5)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Mean funding speed by region", fontsize=TITLE,
             weight="bold", pad=10, loc="left")
finish(fig, "region.png")

# ---- S3: chronological split schematic (authoritative snapshot counts) ---
fig, ax = plt.subplots(figsize=(4.5, 2.3))
ax.barh([0], [8.0], left=[0], color=BLUE, height=0.46)
ax.barh([0], [2.0], left=[8.0], color=YELLOW, edgecolor=INK, linewidth=1, height=0.46)
ax.text(4.0, 0, "TRAIN\n2016 – 2023\n1,174,953 loans", ha="center", va="center",
        color="white", fontsize=TICK, weight="bold")
ax.text(9.02, 0, "TEST\n2024–25\n278,887", ha="center", va="center",
        color=INK, fontsize=ANNOT, weight="bold")
ax.axvline(8.0, ymin=0.18, ymax=0.95, color=INK, linewidth=1.2)
ax.text(8.0, 0.42, "2024-01-01", ha="center", fontsize=ANNOT, color=INK, weight="bold")
ax.text(5.0, -0.44, "Models never see the future they are scored on",
        ha="center", fontsize=ANNOT, color=MUTED, style="italic")
ax.set_xlim(0, 10.4); ax.set_ylim(-0.62, 0.62); ax.axis("off")
ax.set_title("Chronological holdout: train on the\npast, test on the future", fontsize=TITLE,
             weight="bold", pad=8, loc="left")
finish(fig, "data_split.png")

# ---- S6: few-cluster table (authoritative duration model) ----------------
# Deck v2 (2026-09-04): the table shows the AUTHORITATIVE pipeline's average
# within-region slopes (association_summary.txt, "Average Within-Region
# Family-Framing Slopes", duration model), replacing the notebook SS7.2 fit,
# so this slide agrees with the appendix that quotes the same source.
# Compact 6-column layout so the table fits its placed 4.55in at full 10pt
# type (region label carries the country count; 3-dp rounding; full 4-dp
# values live in association_summary.txt).
rows = [("Africa (27)", "610,368", "-0.016", "0.323", "t(26) 0.332", "n.s."),
        ("Asia (12)", "738,191", "+0.023", "0.085", "t(11) 0.113", "n.s."),
        ("C. America (2)", "59,391", "-0.074", "<0.001", "t(1) 0.060", "normal-ref only"),
        ("Middle East (2)", "14,946", "-0.073", "<0.001", "t(1) 0.120", "normal-ref only"),
        ("N. America (1)", "7,559", "+0.013", "0.009", "not estimable", "single country"),
        ("Oceania (4)", "23,385", "+0.005", "0.895", "t(3) 0.903", "n.s.")]
hdr = ["region (ctys)", "loans", "slope", "cl. p", "few-cl. p", "verdict"]
rows = [(a, b, c, d, e, f.replace("normal-ref only", "norm-ref only").replace("single country", "1 country"))
        for a, b, c, d, e, f in rows]
fig = plt.figure(figsize=(4.55, 2.75))
ax = fig.add_axes((0.005, 0.02, 0.99, 0.70)); ax.axis("off")
tbl = ax.table(cellText=rows, colLabels=hdr, loc="center", cellLoc="center")
tbl.auto_set_font_size(False); tbl.set_fontsize(9); tbl.scale(1, 1.55)
tbl.auto_set_column_width(list(range(6)))
for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor(LINE)
    if r == 0:
        cell.set_facecolor(PURPLE); cell.set_text_props(color="white", weight="bold")
    elif "America (2)" in rows[r-1][0] or "Middle East" in rows[r-1][0]:
        cell.set_facecolor("#FFF6BF")
    elif "N. America" in rows[r-1][0]:
        cell.set_facecolor("#EFEDE6")
    else:
        cell.set_facecolor("white")
fig.suptitle("Within-region family-framing slope\n(duration model, authoritative fit):\nnone pass the screen",
             fontsize=TITLE, x=0.02, y=0.97, ha="left")
fig.savefig(OUT + "few_cluster_table.png", facecolor="white", dpi=DPI); plt.close(fig)


# ============================================================================
# EXTRAS (docs/presentation/charts/extra/): house-style rebuilds of the
# remaining notebook figures. Values computed from data/Kiva_Loans.pkl with
# the notebooks' exact logic and verified against printed output where it
# exists: gender medians match the EDA SS4 printout (2.332 / 7.714), the
# repayment counts match the notebook figure's n= annotations (1,264,787 /
# 70,707 / 118,346), and the loan-amount decile bin edges match the figure's
# axis labels ((1.791, 4.836], (5.303, 5.421], ...). Period boxplot n's are
# over VALID rows, hence 6 fewer than the full-row period counts.
# mod_21 (prediction scatter) is deliberately NOT rebuilt: its points are
# model predictions, unreproducible without retraining.
# ============================================================================
import os
EXTRA = OUT + "extra/"
os.makedirs(EXTRA, exist_ok=True)

def finish_extra(fig, name):
    finish(fig, name, out_dir=EXTRA)

# -- funding-speed distribution (30 bins of 2 days, clipped at 60; 0.05%
#    of loans above the clip; 36.6% funded within 1 day) --------------------
HIST = [660265, 134700, 84174, 59418, 48645, 38357, 34438, 31178, 27303,
        25465, 23521, 22200, 25866, 28882, 75273, 18568, 23322, 59492,
        2164, 2370, 2924, 4718, 19192, 87, 100, 128, 103, 99, 72, 816]
fig, ax = plt.subplots(figsize=(4.6, 2.9))
lefts = [i * 2 for i in range(30)]
colors = [YELLOW if i == 0 else BLUE for i in range(30)]
edges = [INK if i == 0 else BLUE for i in range(30)]
ax.bar(lefts, HIST, width=1.9, align="edge", color=colors, edgecolor=edges, linewidth=0.5)
ax.annotate("36.6% fund\nwithin 1 day", xy=(1.4, 620000), xytext=(11, 560000),
            fontsize=ANNOT, weight="bold",
            arrowprops=dict(arrowstyle="-", color=INK, lw=0.8))
ax.set_xlabel("Funding speed (days, clipped at 60)", fontsize=LABEL)
ax.set_ylabel("Loans", fontsize=LABEL)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Most funding happens fast -\nor not for weeks", fontsize=TITLE,
             weight="bold", pad=10, loc="left")
finish_extra(fig, "extra_speed_distribution.png")

# -- funding speed by period (boxplot; whiskers at 1.5 IQR, outliers hidden)
PERIOD_BOX = [
    ("Pre-\npandemic",      dict(med=1.379, q1=0.17,  q3=9.695,  whislo=0.0,   whishi=23.983)),
    ("Pandemic\ndisruption", dict(med=4.903, q1=0.661, q3=25.363, whislo=0.001, whishi=62.414)),
    ("Post-\npandemic",     dict(med=4.122, q1=0.726, q3=18.518, whislo=0.001, whishi=45.001)),
]
fig, ax = plt.subplots(figsize=(4.5, 3.0))
stats = [dict(label=n, **d, fliers=[]) for n, d in PERIOD_BOX]
bp = ax.bxp(stats, showfliers=False, patch_artist=True, widths=0.55)
for i, box in enumerate(bp["boxes"]):
    box.set_facecolor(BLUE if i == 0 else YELLOW); box.set_edgecolor(INK)
for el in bp["medians"]: el.set_color(INK); el.set_linewidth(1.6)
for el in bp["whiskers"] + bp["caps"]: el.set_color(INK)
for i, (n, d) in enumerate(PERIOD_BOX, 1):
    ax.text(i, d["med"] + 1.2, f"{d['med']:.1f}", ha="center", fontsize=ANNOT, weight="bold")
ax.set_ylabel("Funding speed (days)", fontsize=LABEL)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Funding got slower across the board\n(median days, outliers hidden)",
             fontsize=TITLE, weight="bold", pad=10, loc="left")
finish_extra(fig, "extra_period_speed_box.png")

# -- funding speed by gender (medians match EDA SS4 printout) ---------------
GENDER_BOX = [
    ("Female-posted\n(n=1,220,450)", dict(med=2.332, q1=0.328, q3=13.590, whislo=0.0, whishi=33.482), BLUE),
    ("Male-posted\n(n=233,390)",     dict(med=7.714, q1=1.024, q3=27.284, whislo=0.0, whishi=66.560), YELLOW),
]
fig, ax = plt.subplots(figsize=(4.5, 2.9))
stats = [dict(label=n, **d, fliers=[]) for n, d, _ in GENDER_BOX]
bp = ax.bxp(stats, showfliers=False, patch_artist=True, widths=0.5)
for box, (_, _, c) in zip(bp["boxes"], GENDER_BOX):
    box.set_facecolor(c); box.set_edgecolor(INK)
for el in bp["medians"]: el.set_color(INK); el.set_linewidth(1.6)
for el in bp["whiskers"] + bp["caps"]: el.set_color(INK)
for i, (n, d, _) in enumerate(GENDER_BOX, 1):
    ax.text(i, d["med"] + 1.6, f"median {d['med']:.1f}", ha="center", fontsize=ANNOT, weight="bold")
ax.set_ylabel("Funding speed (days)", fontsize=LABEL)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("2.3 vs 7.7 days: the gender gap\n(outliers hidden)", fontsize=TITLE,
             weight="bold", pad=10, loc="left")
finish_extra(fig, "extra_gender_speed_box.png")

# -- mean speed by repayment interval (counts match figure annotations) -----
REPAY = [("monthly", 9.09, 1264787), ("irregularly", 10.79, 70707), ("at_end", 12.75, 118346)]
fig, ax = plt.subplots(figsize=(4.6, 2.3))
names = [x[0] for x in REPAY][::-1]; means = [x[1] for x in REPAY][::-1]; ns = [x[2] for x in REPAY][::-1]
ax.barh(names, means, color=[VIRIDIS(m / 14.0) for m in means], height=0.55)
for y, (m, n) in enumerate(zip(means, ns)):
    ax.text(m + 0.2, y, f"{m:.1f} (n={n:,})", va="center", fontsize=ANNOT, color=MUTED)
ax.set_xlabel("Mean funding speed (days)", fontsize=LABEL); ax.set_xlim(0, 17.5)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Mean funding speed by\nrepayment interval", fontsize=TITLE,
             weight="bold", pad=10, loc="left")
finish_extra(fig, "extra_repayment.png")

# -- mean speed by loan-amount decile (bin edges match figure labels) -------
DECILES = [2.14, 2.46, 5.03, 6.08, 8.87, 10.93, 13.07, 14.32, 16.97, 18.56]
fig, ax = plt.subplots(figsize=(4.6, 2.9))
xs = list(range(1, 11))
ax.plot(xs, DECILES, "-o", color=BLUE, linewidth=2, markersize=5)
ax.plot([1], [DECILES[0]], "o", color=YELLOW, markeredgecolor=INK, markersize=8)
ax.plot([10], [DECILES[-1]], "o", color=YELLOW, markeredgecolor=INK, markersize=8)
ax.text(1.15, DECILES[0] + 1.0, f"{DECILES[0]:.1f}", fontsize=ANNOT, weight="bold")
ax.text(9.85, DECILES[-1] - 2.4, f"{DECILES[-1]:.1f}", ha="right", fontsize=ANNOT, weight="bold")
ax.set_xticks(xs); ax.set_xticklabels(["1\nsmallest", "2", "3", "4", "5", "6", "7", "8", "9", "10\nlargest"])
ax.set_xlabel("Loan-amount decile", fontsize=LABEL)
ax.set_ylabel("Mean funding speed (days)", fontsize=LABEL)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Bigger asks fund slower -\nalmost monotonically", fontsize=TITLE,
             weight="bold", pad=10, loc="left")
finish_extra(fig, "extra_amount_deciles.png")

print("5 extra exhibits rebuilt in house style under charts/extra/")

print("8 exhibits rebuilt: uniform typography "
      f"(title {TITLE}pt / labels {LABEL}pt / ticks {TICK}pt / annotations {ANNOT}pt) at {DPI} dpi")


# ---------------------------------------------------------------------------
if "--verify" in __import__("sys").argv:
    import pickle
    import numpy as np
    import pandas as pd
    print("--verify: recomputing pkl-derived aggregates from data/Kiva_Loans.pkl ...")
    with open("data/Kiva_Loans.pkl", "rb") as f:
        _df = pd.DataFrame(pickle.load(f))
    _fr = pd.to_datetime(_df["fundraisingDate"], errors="coerce", utc=True)
    _ra = pd.to_datetime(_df["raisedDate"], errors="coerce", utc=True)
    _df["funding_speed_days"] = (_ra - _fr).dt.total_seconds() / 86400
    _year = _fr.dt.year
    _df["analysis_period"] = pd.cut(_year, bins=[-np.inf, 2019, 2021, np.inf],
        labels=["pre_pandemic", "pandemic_disruption", "post_pandemic"])
    _v = _df.loc[_df["funding_speed_days"].notna() & (_df["funding_speed_days"] >= 0)].copy()
    assert len(_v) == 1453840, len(_v)
    assert round(float(_v["funding_speed_days"].mean()), 2) == OVERALL_MEAN

    def _grp(col, min_obs):
        c = _v[col].value_counts()
        g = _v[col].where(_v[col].isin(c[c >= min_obs].index), "Other")
        return _v.groupby(g, observed=True)["funding_speed_days"].agg(["mean", "count"])

    _sec = _grp("sector", 1000)
    for name, m, n in SECTORS:
        assert int(_sec.loc[name, "count"]) == n, (name, n)
        assert round(float(_sec.loc[name, "mean"]), 2) == m, (name, m)
    _reg = _grp("region", 10)
    for name, m, n in REGIONS:
        assert int(_reg.loc[name, "count"]) == n, (name, n)
        assert round(float(_reg.loc[name, "mean"]), 2) == m, (name, m)
    _rep = _v.groupby("repaymentInterval", observed=True)["funding_speed_days"].agg(["mean", "count"])
    for name, m, n in REPAY:
        assert int(_rep.loc[name, "count"]) == n, (name, n)
        assert round(float(_rep.loc[name, "mean"]), 2) == m, (name, m)
    _v["log_loan_amount"] = np.log1p(pd.to_numeric(_v["loanAmount"], errors="coerce"))
    _dec = _v.groupby(pd.qcut(_v["log_loan_amount"], 10, duplicates="drop"),
                      observed=True)["funding_speed_days"].mean()
    for lit, got in zip(DECILES, _dec):
        assert abs(float(got) - lit) <= 0.0055, (lit, float(got))

    def _box(sr):
        q1, med, q3 = sr.quantile([.25, .5, .75]); iqr = q3 - q1
        return dict(med=round(float(med), 3), q1=round(float(q1), 3), q3=round(float(q3), 3),
                    whislo=round(float(sr[sr >= q1 - 1.5*iqr].min()), 3),
                    whishi=round(float(sr[sr <= q3 + 1.5*iqr].max()), 3))
    for (label, d), period in zip(PERIOD_BOX, ["pre_pandemic", "pandemic_disruption", "post_pandemic"]):
        assert _box(_v.loc[_v["analysis_period"] == period, "funding_speed_days"]) == d, label
    for (label, d, _), gender in zip(GENDER_BOX, ["female", "male"]):
        assert _box(_v.loc[_v["gender"] == gender, "funding_speed_days"]) == d, label
    _h, _ = np.histogram(_v["funding_speed_days"].clip(upper=60), bins=30)
    assert [int(x) for x in _h] == HIST
    print("--verify: ALL pkl-derived literals reproduced from raw data.")
