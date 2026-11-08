"""Summarise the triage-value check (gap H) for the deck and claims register.

Reads `reports/triage_value/triage_value.json` (written by `src/triage_value.py` from the saved
November benchmark predictions) and writes `reports/evidence_sources/triage_summary.json`:
for each model and arm, the per-year precision and lift when flagging the top 10% of predicted
slow loans, against the slowest 20% of each test year; the text-minus-structure precision
difference with its month-block interval; and the within-country precision spread across the
ten largest countries.

Retrospective, completed loans only; aggregates only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'reports/triage_value/triage_value.json'
OUTPUT = ROOT / 'reports/evidence_sources/triage_summary.json'


def span(values: list[float]) -> list[float]:
    return [min(values), max(values)]


def summarise(data: dict) -> dict:
    models: dict[str, dict] = {}
    for year in data['years']:
        for model, arms in year['models'].items():
            entry = models.setdefault(model, {})
            for arm in ('structure', 'structure_text'):
                top = arms[arm]['top_10']
                country = arms[arm]['top10_countries_within_country_precision_top_10']
                row = entry.setdefault(arm, {'precision': {}, 'lift': {}, 'country_median': {},
                                             'country_min': {}, 'country_max': {}})
                row['precision'][year['year']] = top['precision']
                row['lift'][year['year']] = top['lift']
                row['country_median'][year['year']] = country['median']
                row['country_min'][year['year']] = country['min']
                row['country_max'][year['year']] = country['max']
            diff = arms['text_minus_structure_precision_top_10']
            entry.setdefault('text_gain', {})[year['year']] = {'difference': diff['difference'],
                                                               'month_block_95': diff['month_block_95']}
    result = {'target': data['target'], 'population': data['population'], 'models': {}}
    for model, entry in models.items():
        out = {}
        for arm in ('structure', 'structure_text'):
            row = entry[arm]
            out[arm] = {
                'precision_by_year': row['precision'],
                'lift_by_year': row['lift'],
                'precision_range': span(list(row['precision'].values())),
                'lift_range': span(list(row['lift'].values())),
                'country_median_range': span(list(row['country_median'].values())),
                'country_range': [min(row['country_min'].values()), max(row['country_max'].values())],
            }
        gains = entry['text_gain']
        out['text_gain'] = {
            'by_year': gains,
            'difference_range': span([g['difference'] for g in gains.values()]),
            'years_interval_includes_zero': sum(g['month_block_95'][0] <= 0 <= g['month_block_95'][1]
                                                for g in gains.values()),
        }
        result['models'][model] = out
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(summarise(json.loads(args.source.read_text())), indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
