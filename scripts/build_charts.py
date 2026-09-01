#!/usr/bin/env python3
"""Rebuild the five purpose-built slide exhibits in the deck palette.

Single committed source for the scripted charts (the two retained notebook
figures - sector, region - are cropped/masked exports of executed-notebook
output and are NOT regenerated here). Every number below is a verified value
from the executed notebooks / authoritative snapshot - see each block's
comment. Palette: navy ink #1C2333, viridis blue #31688E base, team yellow
#FFDD04 as the single highlight group per chart, viridis purple #440154 for
the table header. Yellow is used only as a fill (never text on light).
Run: python3 scripts/build_charts.py  (then scripts/build_slides_draft.py)
"""
import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

OUT = "docs/presentation/charts/"
INK = "#1C2333"; BLUE = "#31688E"; YELLOW = "#FFDD04"; MUTED = "#6E7278"
PURPLE = "#440154"; LINE = "#D9D6CC"

# Typeface: prefer a real Google Sans TTF if the team drops one into
# docs/presentation/fonts/ (it is not freely redistributable, so it is not
# committed); otherwise use the committed DM Sans (SIL-OFL, the standard
# open substitute with the same geometric feel).
FONT_DIR = "docs/presentation/fonts/"
family = None
for pattern, name in (("GoogleSans*", None), ("ProductSans*", None), ("DMSans*", "DM Sans")):
    files = [f for f in glob.glob(FONT_DIR + pattern + ".ttf") if "Italic" not in f]             + [f for f in glob.glob(FONT_DIR + pattern + ".ttf") if "Italic" in f]
    if files:
        for f in files:
            fm.fontManager.addfont(f)
        family = name or fm.FontProperties(fname=files[0]).get_name()
        break
plt.rcParams.update({
    "font.size": 14, "axes.edgecolor": LINE, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK,
})
if family:
    plt.rcParams["font.family"] = family
    print("charts typeface:", family)

# S4 - shares printed by EDA SS4 (0.46028 / 0.30321 / 0.299945) + period Ns
fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=200)
labels = ["Pre-pandemic\n(589,823 loans)", "Pandemic disruption\n(298,549)",
          "Post-pandemic\nthrough 2025 (565,474)"]
vals = [46.0, 30.3, 30.0]
bars = ax.bar(labels, vals, color=[BLUE, YELLOW, YELLOW], width=0.62,
              edgecolor=[BLUE, INK, INK], linewidth=[0, 1.2, 1.2])
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width()/2, v + 1, f"{v:.0f}%", ha="center",
            fontsize=17, weight="bold")
ax.set_ylabel("Share funded within 24 hours (%)", fontsize=13)
ax.set_ylim(0, 54); ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Same-day funding has not recovered", fontsize=16, weight="bold", pad=12, loc="left")
fig.savefig(OUT + "period_24h.png", facecolor="white", bbox_inches="tight"); plt.close(fig)

# S7 - means printed by EDA SS8 (8 NMF topics), semantic labels from top-words
topics = [("Sanitation & toilets", 1.46), ("Clean drinking water", 1.81),
          ("Pig raising", 7.26), ("Philippine small business", 7.80),
          ("General store goods", 8.96), ("Family business & income", 10.70),
          ("Smallholder farming", 12.51), ("Group solar / farm plots", 13.49)]
fig, ax = plt.subplots(figsize=(7.4, 4.8), dpi=200)
names = [t[0] for t in topics][::-1]; means = [t[1] for t in topics][::-1]
cmap = plt.get_cmap("viridis")
colors = [cmap(m / 15.0) for m in means]   # sequential: order IS the message
ax.barh(names, means, color=colors, height=0.66)
for y, m in enumerate(means):
    ax.text(m + 0.15, y, f"{m:.1f}", va="center", fontsize=13, weight="bold")
ax.set_xlabel("Mean funding speed (days)", fontsize=13); ax.set_xlim(0, 15.4)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Story themes (8 NMF topics): a ninefold gap", fontsize=15,
             weight="bold", pad=12, loc="left")
fig.savefig(OUT + "topics.png", facecolor="white", bbox_inches="tight"); plt.close(fig)

# A2 - SHAP top-15 printed by modeling SS8 (v14/v15 runs)
shap = [("Loan amount (log)", 0.4462), ("Repayment term", 0.3373),
        ("Pre-pandemic period", 0.2201), ("Small loan-size band", 0.1490),
        ("Sector: Retail", 0.0777), ("Gender: female", 0.0646),
        ("Pandemic-disruption period", 0.0535), ("Region: Asia", 0.0445),
        ("Sector: Food", 0.0436), ("Sector: Education", 0.0393),
        ("Sentiment (VADER compound)", 0.0368), ("Gender: male", 0.0362),
        ("Post-pandemic period", 0.0263), ("Region: Africa", 0.0237),
        ("Sector: Sanitation & Hygiene", 0.0200)]
fig, ax = plt.subplots(figsize=(7.6, 5.2), dpi=200)
names = [s[0] for s in shap][::-1]; vals = [s[1] for s in shap][::-1]
colors = [YELLOW if "Sentiment" in n else BLUE for n in names]
edges = [INK if "Sentiment" in n else BLUE for n in names]
ax.barh(names, vals, color=colors, edgecolor=edges, linewidth=0.8, height=0.66)
ax.set_xlabel("mean |SHAP value| (boosted model, 2,000-loan holdout sample)", fontsize=12)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("SHAP top 15: structure fills the ranks;\nsentiment (11th) is the only narrative feature",
             fontsize=14, weight="bold", pad=12, loc="left")
fig.savefig(OUT + "shap_top15.png", facecolor="white", bbox_inches="tight"); plt.close(fig)

# A3 - correlations printed by EDA SS9
corr = [("Loan amount (log)", 0.429), ("Repayment term", 0.285),
        ("Competence/agency mentions", 0.058), ("Family mentions", 0.019),
        ("Urgency mentions", 0.010)]
fig, ax = plt.subplots(figsize=(7.4, 4.4), dpi=200)
names = [c[0] for c in corr][::-1]; vals = [c[1] for c in corr][::-1]
colors = [YELLOW, YELLOW, YELLOW, BLUE, BLUE]   # narrative group highlighted
edges = [INK, INK, INK, BLUE, BLUE]
ax.barh(names, vals, color=colors, edgecolor=edges, linewidth=0.8, height=0.6)
for y, v in enumerate(vals):
    ax.text(v + 0.006, y, f"{v:.3f}", va="center", fontsize=13, weight="bold")
ax.set_xlabel("|correlation| with funding speed (days)", fontsize=13); ax.set_xlim(0, 0.5)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("The “~10×” claim, exactly:\nstructure vs narrative correlations",
             fontsize=14, weight="bold", pad=12, loc="left")
fig.savefig(OUT + "correlations.png", facecolor="white", bbox_inches="tight"); plt.close(fig)

# S6 - few-cluster table, values from the executed modeling notebook SS7.2 (v15)
rows = [("Africa", "27", "610,368", "-0.0101", "0.5536", "t(26) 0.5587", "not significant"),
        ("Asia", "12", "738,191", "+0.0338", "0.0535", "t(11) 0.0797", "not significant"),
        ("Central America", "2", "59,391", "-0.0618", "<0.0001", "t(1) 0.0650", "normal-ref only"),
        ("Middle East", "2", "14,946", "-0.1236", "<0.0001", "t(1) 0.0753", "normal-ref only"),
        ("North America", "1", "7,559", "+0.0109", "0.0621", "not estimable", "single country"),
        ("Oceania", "4", "23,385", "+0.0162", "0.6305", "t(3) 0.6634", "not significant")]
hdr = ["region", "ctys", "loans", "slope", "clust. p", "few-cluster p", "verdict"]
fig, ax = plt.subplots(figsize=(7.8, 4.6), dpi=200); ax.axis("off")
tbl = ax.table(cellText=rows, colLabels=hdr, loc="center", cellLoc="center")
tbl.auto_set_font_size(False); tbl.set_fontsize(12); tbl.scale(1, 2.1)
tbl.auto_set_column_width(list(range(7)))
for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor(LINE)
    if r == 0:
        cell.set_facecolor(PURPLE); cell.set_text_props(color="white", weight="bold")
    elif rows[r-1][0] in ("Central America", "Middle East"):
        cell.set_facecolor("#FFF6BF")   # pale team-yellow highlight
    elif rows[r-1][0] == "North America":
        cell.set_facecolor("#EFEDE6")
    else:
        cell.set_facecolor("white")
ax.set_title("Within-region family-framing slope (duration model)\nno region passes the few-cluster screen",
             fontsize=13, pad=10, loc="left")
fig.savefig(OUT + "few_cluster_table.png", bbox_inches="tight", facecolor="white"); plt.close(fig)



# S5 - average funding speed by sector. Values computed from
# data/Kiva_Loans.pkl replicating the EDA notebook's exact grouping
# (valid = non-null, non-negative funding_speed_days; sectors with
# < 1,000 loans folded into "Other"); every count below matches the
# executed notebook's printed n= annotations, and valid rows = 1,453,840.
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
fig, ax = plt.subplots(figsize=(7.6, 6.4), dpi=200)
names = [x[0] for x in SECTORS]; means = [x[1] for x in SECTORS]; ns = [x[2] for x in SECTORS]
colors = [plt.get_cmap('viridis')(m / 13.5) for m in means]
ax.barh(names, means, color=colors, height=0.7)
ax.axvline(OVERALL_MEAN, color=INK, linestyle="--", linewidth=1)
ax.text(OVERALL_MEAN + 0.15, 0.2, f"overall avg {OVERALL_MEAN:.1f}", fontsize=10, color=MUTED)
for y, (m, n) in enumerate(zip(means, ns)):
    ax.text(m + 0.15, y, f"{m:.1f}  (n={n:,})", va="center", fontsize=9, color=MUTED)
ax.set_xlabel("Mean funding speed (days)", fontsize=13); ax.set_xlim(0, 15.6)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Sector spans an order of magnitude in speed", fontsize=15,
             weight="bold", pad=12, loc="left")
fig.savefig(OUT + "sector.png", facecolor="white", bbox_inches="tight"); plt.close(fig)

# A1 - average funding speed by region (same computation and verification)
REGIONS = [("North America", 3.71, 7559), ("Asia", 8.18, 738191),
           ("Africa", 10.29, 610368), ("Middle East", 11.01, 14946),
           ("Oceania", 14.23, 23385), ("Central America", 15.56, 59391)]
fig, ax = plt.subplots(figsize=(7.4, 4.4), dpi=200)
names = [x[0] for x in REGIONS]; means = [x[1] for x in REGIONS]; ns = [x[2] for x in REGIONS]
colors = [plt.get_cmap('viridis')(m / 16.5) for m in means]
ax.barh(names, means, color=colors, height=0.62)
ax.axvline(OVERALL_MEAN, color=INK, linestyle="--", linewidth=1)
for y, (m, n) in enumerate(zip(means, ns)):
    ax.text(m + 0.2, y, f"{m:.1f}  (n={n:,})", va="center", fontsize=10.5, color=MUTED)
ax.set_xlabel("Mean funding speed (days)", fontsize=13); ax.set_xlim(0, 19.5)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Average funding speed by region", fontsize=15, weight="bold", pad=12, loc="left")
fig.savefig(OUT + "region.png", facecolor="white", bbox_inches="tight"); plt.close(fig)

# S3 - chronological data-split schematic. Counts from the authoritative
# snapshot (train 1,174,953 / holdout 278,887; boundary 2024-01-01).
fig, ax = plt.subplots(figsize=(7.4, 3.4), dpi=200)
ax.barh([0], [8.0], left=[0], color=BLUE, height=0.42)
ax.barh([0], [2.0], left=[8.0], color=YELLOW, edgecolor=INK, linewidth=1.2, height=0.42)
ax.text(4.0, 0, "TRAIN\n2016 - 2023\n1,174,953 loans", ha="center", va="center",
        color="white", fontsize=13, weight="bold")
ax.text(9.0, 0, "TEST\n2024 - 2025\n278,887", ha="center", va="center",
        color=INK, fontsize=11.5, weight="bold")
ax.axvline(8.0, color=INK, linewidth=1.4)
ax.text(8.0, 0.38, "2024-01-01", ha="center", fontsize=11, color=INK, weight="bold")
ax.text(5.0, -0.42, "Models never see the future they are scored on", ha="center",
        fontsize=12, color=MUTED, style="italic")
ax.set_xlim(0, 10.4); ax.set_ylim(-0.62, 0.62); ax.axis("off")
ax.set_title("Chronological holdout: train on the past, test on the future",
             fontsize=14.5, weight="bold", pad=10, loc="left")
fig.savefig(OUT + "data_split.png", facecolor="white", bbox_inches="tight"); plt.close(fig)

print("3 additional exhibits built (sector, region, data_split)")

print("8 exhibits rebuilt in the deck palette")
