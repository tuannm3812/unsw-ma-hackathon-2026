"""Render a portfolio exhibit directly from the saved primary JSON report."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "reports/generated_full_dataset/analysis_summary.json"
OUTPUT = REPO / "docs/presentation/charts/portfolio_uncertainty.png"


def main() -> None:
    payload = json.loads(SOURCE.read_text())
    rows = {r['group']: r for r in
            payload['explanatory']['within_region_slopes']['duration']}
    groups = ['Middle East', 'Central America']
    ink, muted = '#172B3A', '#536475'
    normal, heuristic = plt.cm.viridis(0.34), plt.cm.viridis(0.64)
    fig, ax = plt.subplots(figsize=(10.5, 6.4), dpi=180)
    fig.patch.set_facecolor('#FAFBFC')
    ax.set_facecolor('#FAFBFC')
    fig.subplots_adjust(left=.23, right=.95, top=.68, bottom=.34)
    fig.text(.06, .92, 'BEYOND A GOOD STORY', size=10, weight='bold', color=normal)
    fig.text(.06, .855, 'A promising pattern needs more evidence',
             size=21, weight='bold', color=ink)
    fig.text(.06, .795,
             'Family framing and funding duration | two country clusters per region',
             size=11, color=muted)
    ax.axvline(0, color='#9BA7B0', linestyle='--', linewidth=1)
    for y, group in zip([1, 0], groups):
        row = rows[group]
        estimate = row['estimate']
        for offset, prefix, color in [(0.10, 'clustered', normal),
                                     (-0.10, 'few_cluster', heuristic)]:
            lower, upper = row[f'{prefix}_ci_low'], row[f'{prefix}_ci_high']
            ax.errorbar(estimate, y + offset,
                        xerr=[[estimate - lower], [upper - estimate]],
                        fmt='o', color=color, markersize=6, capsize=5,
                        elinewidth=2.5)
    ax.set_yticks([1, 0])
    ax.set_yticklabels([f"{g}\n{rows[g]['n_loans']:,} loans" for g in groups],
                       fontsize=11, color=ink)
    ax.set_ylim(-.45, 1.45)
    ax.set_xlim(-.28, .13)
    ax.set_xticks([-.2, -.1, 0, .1])
    ax.tick_params(axis='both', length=0, pad=10, colors=muted)
    ax.set_xlabel('Change in log(1 + funding days) per extra family mention / 100 words',
                  fontsize=10, color=muted, labelpad=14)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(axis='x', color='#E4E9ED', linewidth=.7)
    ax.set_axisbelow(True)
    handles = [Line2D([0], [0], color=c, marker='o', lw=2.5) for c in [normal, heuristic]]
    fig.legend(handles, ['Country-clustered 95% interval (normal reference)',
                         'Heuristic 95% interval using t(1) reference'],
               loc='lower left', bbox_to_anchor=(.055, .12), frameon=False,
               fontsize=10, labelcolor=ink)
    fig.text(.06, .085,
             'Heuristic intervals cross zero. This screen cannot certify an effect; associations are not causal.',
             fontsize=9, color=muted)
    fig.text(.06, .045,
             'Source: primary full-data snapshot, 31 Aug 2026 | 1,453,840 valid durations | Team Cultural Blend',
             fontsize=8.5, color=muted)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(OUTPUT)


if __name__ == '__main__':
    main()
