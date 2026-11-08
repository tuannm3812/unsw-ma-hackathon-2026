"""Summarise the wild cluster bootstrap (gaps C, G) and subgroup refits (gap B) for the deck.

Reads the Kaggle outputs in `reports/kaggle_experiments/inference/reports/` and the reviewed
equivalence screen, and writes `reports/evidence_sources/robustness_summary.json`:

- bootstrap: verdicts that change against the screen, bounded results that survive, and the
  smallest BH-adjusted bootstrap p for a nonzero association;
- subgroups: per specification and outcome, the equivalence verdict for each framing in each of
  the ten subgroups, the count of subgroups where each framing is bounded, the number of tests,
  and unadjusted p < 0.05 cells (exploratory hypotheses, not findings).

Exploratory: bounds were set after the estimates. Aggregates only.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KAGGLE = ROOT / 'reports/kaggle_experiments/inference/reports'
SCREEN = ROOT / 'reports/equivalence_screen_reviewed/equivalence_screen.csv'
OUTPUT = ROOT / 'reports/evidence_sources/robustness_summary.json'
ORDER = [('analysis_period', 'pre_pandemic'), ('analysis_period', 'pandemic_disruption'),
         ('analysis_period', 'post_pandemic'), ('loan_size_band', 'small'), ('loan_size_band', 'medium'),
         ('loan_size_band', 'large'), ('gender_classification', 'female'), ('gender_classification', 'male'),
         ('region', 'Asia'), ('region', 'Africa')]


def term(feature: str) -> str:
    return feature.replace('_mentions_per_100_words', '').replace('desc_sentiment_compound', 'sentiment')


def bootstrap_summary(wild: dict, screen: dict[tuple, bool]) -> dict:
    changed, total, bounded, survived = [], 0, 0, 0
    min_zero_bh = 1.0
    for key, block in wild['results'].items():
        spec, outcome = key.split('/')
        for row in block['rows']:
            before, after = screen[(spec, outcome, row['feature'])], row['equivalent_wcr']
            total += 1
            bounded += before
            survived += before and after
            if before != after:
                changed.append({'specification': spec, 'outcome': outcome, 'term': term(row['feature']),
                                'screen': before, 'bootstrap': after})
            min_zero_bh = min(min_zero_bh, row['wcr_p_zero_bh'])
    first = next(iter(wild['results'].values()))
    return {'verdicts': total, 'unchanged': total - len(changed), 'bounded_in_screen': bounded,
            'bounded_survive': survived, 'changed': changed, 'min_p_zero_bh': min_zero_bh,
            'draws': first['draws'], 'clusters': first['n_clusters'], 'weights': first['weights']}


def subgroup_summary(data: dict) -> dict:
    out: dict[str, dict] = {}
    for outcome in ('log_funding_speed', 'funded_within_24h'):
        cells = {(r['group'], r['level']): r for r in data['results'] if r['outcome'] == outcome}
        terms = [term(t['feature']) for t in cells[ORDER[0]]['terms']]
        grid = {name: [] for name in terms}
        hypotheses = []
        for group, level in ORDER:
            row = cells[(group, level)]
            for t in row['terms']:
                grid[term(t['feature'])].append(bool(t['equivalent']))
                if t['p_zero'] < 0.05:
                    hypotheses.append({'group': group, 'level': level, 'term': term(t['feature']),
                                       'estimate': t['estimate'], 'p_zero_unadjusted': t['p_zero']})
        out[outcome] = {'subgroups': [level for _, level in ORDER], 'grid': grid,
                        'bounded_count': {name: sum(v) for name, v in grid.items()},
                        'hypotheses_unadjusted': hypotheses}
    out['tests'] = sum(len(r['terms']) for r in data['results'])
    return out


def build(kaggle: Path = KAGGLE, screen_path: Path = SCREEN) -> dict:
    with screen_path.open() as handle:
        screen = {(r['specification'], r['outcome'], r['feature']): r['equivalent'] == 'True'
                  for r in csv.DictReader(handle)}
    wild = json.loads((kaggle / 'wild_cluster_bootstrap/wild_cluster.json').read_text())
    result = {'bootstrap': bootstrap_summary(wild, screen), 'subgroups': {}}
    for spec in ('programme_adjusted', 'expanded'):
        data = json.loads((kaggle / f'subgroup_inference/subgroup_{spec}.json').read_text())
        result['subgroups'][spec] = subgroup_summary(data)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
