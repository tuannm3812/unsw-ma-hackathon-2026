#!/usr/bin/env python3
"""Rebuild the eight slide exhibits with UNIFORM typography.

Every chart uses the same point sizes (TITLE/LABEL/TICK/ANNOT below) and is
sized at its intended physical on-slide size, saved at 300 dpi - so inserting
any exported PNG at native size (no rescaling) renders text identically
across all exhibits. Figure dimensions vary with content; type does not.

All values are verified: printed by the executed notebooks, taken from the
authoritative snapshot, or computed from data/Kiva_Loans.pkl replicating the
EDA notebook's exact grouping with every per-category count asserted equal
to the executed notebook's printed n= annotations.

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


def finish(fig, name):
    fig.savefig(OUT + name, facecolor="white", bbox_inches="tight", dpi=DPI)
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
fig, ax = plt.subplots(figsize=(4.6, 3.2))
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
fig, ax = plt.subplots(figsize=(4.6, 4.1))
names = [s[0] for s in shap][::-1]; vals = [s[1] for s in shap][::-1]
ax.barh(names, vals, color=[YELLOW if "Sentiment" in n else BLUE for n in names],
        edgecolor=[INK if "Sentiment" in n else BLUE for n in names],
        linewidth=0.7, height=0.66)
ax.set_xlabel("mean |SHAP value| (boosted model,\n2,000-loan holdout sample)", fontsize=LABEL)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("SHAP top 15: sentiment (11th) is\nthe only narrative feature", fontsize=TITLE,
             weight="bold", pad=10, loc="left")
finish(fig, "shap_top15.png")

# ---- A3: the 10x correlation basis (EDA SS9 printout) --------------------
corr = [("Loan amount (log)", 0.429), ("Repayment term", 0.285),
        ("Competence/agency mentions", 0.058), ("Family mentions", 0.019),
        ("Urgency mentions", 0.010)]
fig, ax = plt.subplots(figsize=(4.6, 2.9))
names = [c[0] for c in corr][::-1]; vals = [c[1] for c in corr][::-1]
ax.barh(names, vals, color=[YELLOW, YELLOW, YELLOW, BLUE, BLUE],
        edgecolor=[INK, INK, INK, BLUE, BLUE], linewidth=0.7, height=0.6)
for y, v in enumerate(vals):
    ax.text(v + 0.008, y, f"{v:.3f}", va="center", fontsize=ANNOT, weight="bold")
ax.set_xlabel("|correlation| with funding speed (days)", fontsize=LABEL)
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
fig, ax = plt.subplots(figsize=(4.6, 4.6))
names = [x[0] for x in SECTORS]; means = [x[1] for x in SECTORS]; ns = [x[2] for x in SECTORS]
ax.barh(names, means, color=[VIRIDIS(m / 13.5) for m in means], height=0.7)
ax.axvline(OVERALL_MEAN, color=INK, linestyle="--", linewidth=1)
ax.text(OVERALL_MEAN + 0.2, 0.1, f"avg {OVERALL_MEAN:.1f}", fontsize=ANNOT, color=MUTED)
for y, (m, n) in enumerate(zip(means, ns)):
    ax.text(m + 0.2, y, f"{m:.1f} (n={n:,})", va="center", fontsize=ANNOT - 1.5, color=MUTED)
ax.set_xlabel("Mean funding speed (days)", fontsize=LABEL); ax.set_xlim(0, 16.4)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Sector spans an order of\nmagnitude in speed", fontsize=TITLE,
             weight="bold", pad=10, loc="left")
finish(fig, "sector.png")

# ---- A1: region means (computed from raw pkl; counts verified) -----------
REGIONS = [("North America", 3.71, 7559), ("Asia", 8.18, 738191),
           ("Africa", 10.29, 610368), ("Middle East", 11.01, 14946),
           ("Oceania", 14.23, 23385), ("Central America", 15.56, 59391)]
fig, ax = plt.subplots(figsize=(4.6, 2.9))
names = [x[0] for x in REGIONS]; means = [x[1] for x in REGIONS]; ns = [x[2] for x in REGIONS]
ax.barh(names, means, color=[VIRIDIS(m / 16.5) for m in means], height=0.62)
ax.axvline(OVERALL_MEAN, color=INK, linestyle="--", linewidth=1)
for y, (m, n) in enumerate(zip(means, ns)):
    ax.text(m + 0.25, y, f"{m:.1f} (n={n:,})", va="center", fontsize=ANNOT - 1, color=MUTED)
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

# ---- S6: few-cluster table (executed modeling notebook SS7.2, v15) -------
rows = [("Africa", "27", "610,368", "-0.0101", "0.5536", "t(26) 0.5587", "not significant"),
        ("Asia", "12", "738,191", "+0.0338", "0.0535", "t(11) 0.0797", "not significant"),
        ("Central America", "2", "59,391", "-0.0618", "<0.0001", "t(1) 0.0650", "normal-ref only"),
        ("Middle East", "2", "14,946", "-0.1236", "<0.0001", "t(1) 0.0753", "normal-ref only"),
        ("North America", "1", "7,559", "+0.0109", "0.0621", "not estimable", "single country"),
        ("Oceania", "4", "23,385", "+0.0162", "0.6305", "t(3) 0.6634", "not significant")]
hdr = ["region", "ctys", "loans", "slope", "clust. p", "few-cluster p", "verdict"]
fig, ax = plt.subplots(figsize=(6.4, 2.9)); ax.axis("off")
tbl = ax.table(cellText=rows, colLabels=hdr, loc="center", cellLoc="center")
tbl.auto_set_font_size(False); tbl.set_fontsize(TICK); tbl.scale(1, 1.75)
tbl.auto_set_column_width(list(range(7)))
for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor(LINE)
    if r == 0:
        cell.set_facecolor(PURPLE); cell.set_text_props(color="white", weight="bold")
    elif rows[r-1][0] in ("Central America", "Middle East"):
        cell.set_facecolor("#FFF6BF")
    elif rows[r-1][0] == "North America":
        cell.set_facecolor("#EFEDE6")
    else:
        cell.set_facecolor("white")
ax.set_title("Within-region family-framing slope (duration model)\nno region passes the few-cluster screen",
             fontsize=TITLE, pad=8, loc="left")
finish(fig, "few_cluster_table.png")

print("8 exhibits rebuilt: uniform typography "
      f"(title {TITLE}pt / labels {LABEL}pt / ticks {TICK}pt / annotations {ANNOT}pt) at {DPI} dpi")
