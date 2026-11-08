"""Summarise the wild cluster bootstrap (gaps C, G) and subgroup refits (gap B) for the deck.

Reads the Kaggle outputs in `reports/kaggle_experiments/inference/reports/` and the reviewed
equivalence screen, and writes `reports/evidence_sources/robustness_summary.json`:

- bootstrap: verdicts that change against the screen, bounded results that survive, and the
  smallest BH-adjusted bootstrap p for a nonzero association;
- subgroups: per specification and outcome, the equivalence verdict for each framing in each of
  the ten subgroups, the count of subgroups where each framing is bounded, the number of tests,
  and unadjusted p < 0.05 cells (exploratory hypotheses, not findings);
- evidence funnel: tests passing the clustered t(47), the bootstrap and the BH-adjusted bootstrap;
- third-person and business estimates in real units, with the shrink under programme controls.

Exploratory: bounds were set after the estimates. Aggregates only.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from src.bound_ladder import MEDIAN_DAYS

ROOT = Path(__file__).resolve().parents[1]
KAGGLE = ROOT / 'reports/kaggle_experiments/inference/reports'
# Corrected bootstrap rerun after the 2026-11-08 review; see reports/experiments_2026_11_08/README.md.
WILD = ROOT / 'reports/kaggle_experiments/review_fix/reports/wild_cluster_bootstrap/wild_cluster.json'
SCREEN = ROOT / 'reports/equivalence_screen_reviewed/equivalence_screen.csv'
OUTPUT = ROOT / 'reports/evidence_sources/robustness_summary.json'
DISTRIBUTION = ROOT / 'reports/equivalence_screen_reviewed/feature_distribution.json'
MINUTES_PER_DAY = 1440
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


def evidence_funnel(wild: dict, threshold: float = 0.05) -> dict:
    """How many term-by-model tests pass at each stage: clustered t(47), bootstrap, BH-adjusted bootstrap."""
    rows = [row for block in wild['results'].values() for row in block['rows']]
    return {'tests': len(rows), 'clustered': sum(r['p_t47'] < threshold for r in rows),
            'bootstrap': sum(r['wcr_p_zero'] < threshold for r in rows),
            'adjusted': sum(r['wcr_p_zero_bh'] < threshold for r in rows)}


def adjusted_passes(wild: dict, threshold: float = 0.05) -> dict:
    """Tests passing after BH, their programme-adjusted counterpart, and the lowest BH p among the rest."""
    def match(outcome: str, feature: str) -> dict | None:
        block = wild['results'].get(f'programme_adjusted/{outcome}', {'rows': []})
        return next((r for r in block['rows'] if r['feature'] == feature), None)

    passes, others = [], []
    for key, block in wild['results'].items():
        spec, outcome = key.split('/')
        for row in block['rows']:
            if row['wcr_p_zero_bh'] >= threshold:
                others.append(row['wcr_p_zero_bh'])
                continue
            twin = match(outcome, row['feature'])
            passes.append({'specification': spec, 'outcome': outcome, 'term': term(row['feature']), 'estimate': row['estimate'],
                           'pct_change_in_1_plus_days': (math.exp(row['estimate']) - 1) * 100, 'p_zero': row['wcr_p_zero'],
                           'p_zero_bh': row['wcr_p_zero_bh'],
                           'programme_adjusted_p_zero': twin and twin['wcr_p_zero'],
                           'programme_adjusted_p_zero_bh': twin and twin['wcr_p_zero_bh']})
    return {'passes': passes, 'lowest_other_p_zero_bh': min(others)}


def framing_in_real_units(wild: dict, distribution: dict, median_days: float = MEDIAN_DAYS) -> dict:
    """Third-person and business estimates in real units, their shrink under programme controls, and how common each is.

    Minutes are the change in funding time per extra mention per 100 words at the median loan;
    the outcome is log(1 + days). Associations only: nothing here measures an edit.
    """
    def estimate(spec: str, outcome: str, feature: str) -> float:
        return next(r['estimate'] for r in wild['results'][f'{spec}/{outcome}']['rows'] if r['feature'] == feature)

    third, business = 'third_person_mentions_per_100_words', 'business_mentions_per_100_words'
    minutes = lambda beta: (1 + median_days) * (1 - math.exp(beta)) * MINUTES_PER_DAY
    t_expanded = estimate('expanded', 'log_funding_speed', third)
    t_adjusted = estimate('programme_adjusted', 'log_funding_speed', third)
    b_expanded = estimate('expanded', 'funded_within_24h', business)
    b_adjusted = estimate('programme_adjusted', 'funded_within_24h', business)
    return {'median_days': median_days,
            'third_person': {'estimate_expanded': t_expanded, 'estimate_programme_adjusted': t_adjusted,
                             'minutes_expanded': minutes(t_expanded), 'minutes_programme_adjusted': minutes(t_adjusted),
                             'shrink_share': 1 - t_adjusted / t_expanded,
                             'share_with_mention': 1 - distribution[third]['share_zero']},
            'business': {'pp_expanded': b_expanded * 100, 'pp_programme_adjusted': b_adjusted * 100,
                         'shrink_share': 1 - b_adjusted / b_expanded,
                         'share_with_mention': 1 - distribution[business]['share_zero']}}


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
    wild = json.loads(WILD.read_text())
    distribution = json.loads(DISTRIBUTION.read_text())['features']
    result = {'bootstrap': bootstrap_summary(wild, screen), 'evidence_funnel': evidence_funnel(wild), 'adjusted_passes': adjusted_passes(wild),
              'framing_real_units': framing_in_real_units(wild, distribution), 'subgroups': {}}
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
