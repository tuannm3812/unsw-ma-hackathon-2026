"""Read the model comparison and loan-purpose contrasts for the deck's appendix.

Writes `reports/evidence_sources/appendix_summary.json`:

- forecast MAE per test year and the 24-hour ROC AUC range for the fixed models in the November
  benchmark and the larger boosted tree;
- sector and activity contrasts on (1 + days) from Experiment I, ranked among activities with at
  least 1,000 loans, and the toilets and sanitation activity.

Associations among completed loans; retrospective forecasts. Aggregates only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / 'reports/text_benchmark_reviewed/benchmark.json'
LARGE = ROOT / 'reports/kaggle_experiments/forecast/reports/strong_forecaster_large/strong_forecaster.json'
DETAILS = ROOT / 'reports/experiments_2026_11_08/loan_detail_coefficients.json'
OUTPUT = ROOT / 'reports/evidence_sources/appendix_summary.json'
MODELS = (('Median only', 'baseline', 'B0'), ('Historical lookup', 'baseline', 'B1'),
          ('Linear, loan details', 'linear', 'S'), ('Linear, with text', 'linear', 'S+M+L+R'),
          ('Boosted tree, loan details', 'histogram_boosting', 'S'))
EXTRA_MODELS = (('Linear, text only', 'linear', 'T'), ('Linear, programme text', 'linear', 'S+P'),
                ('Linear, programme and text', 'linear', 'S+P+M+L+R'), ('Boosted tree, programme text', 'histogram_boosting', 'S+P'),
                ('Tree, programme and text', 'histogram_boosting', 'S+P+M+L'))
SANITATION = 'Toilets & Sanitation Systems'


def _row(name: str, windows: list[dict]) -> dict:
    aucs = [w['auc'] for w in windows]
    return {'name': name, 'mae': {str(w['year']): w['mae'] for w in windows}, 'auc_range': [min(aucs), max(aucs)]}


def model_rows(benchmark: dict, large: dict, models=MODELS, extras=()) -> list[dict]:
    """One row per model in display order: the named models, the larger boosted tree, then any extras."""
    def rows_for(entries) -> list[dict]:
        out = []
        for name, family, arm in entries:
            windows = [{'year': m['year'], 'mae': m['metrics']['mae_days'], 'auc': m['metrics']['roc_auc']}
                       for m in benchmark['models'] if (m['family'], m['arm']) == (family, arm)]
            out.append(_row(name, windows))
        return out

    windows = [{'year': w['year'], 'mae': w['mae_days'], 'auc': w['roc_auc']} for w in large['windows'] if w['arm'] == 'S']
    return rows_for(models) + [_row('Larger boosted tree', windows)] + rows_for(extras)


def purpose_contrasts(outcome: dict, keep: int = 5, min_records: int = 1000) -> dict:
    """Sector contrasts in order, the fastest and slowest large activities, and the sanitation activity."""
    def brief(row: dict) -> dict:
        return {'level': row['level'], 'records': row['records'], 'pct': row['pct_change_in_1_plus_days'],
                'ci95': row['pct_ci95'], 'p_t47': row['p_t47']}

    activities = [r for r in outcome['categories'] if r['group'] == 'activity']
    large = sorted((r for r in activities if r['records'] >= min_records), key=lambda r: r['pct_change_in_1_plus_days'])
    sectors = sorted(outcome['sector_contrasts'], key=lambda r: r['pct_change_in_1_plus_days'])
    return {'sectors': [{'sector': s['sector'], 'records': s['records'], 'pct': s['pct_change_in_1_plus_days'], 'ci95': s['pct_ci95']}
                        for s in sectors],
            'fastest': [brief(r) for r in large[:keep]], 'slowest': [brief(r) for r in reversed(large[-keep:])],
            'sanitation': brief(next(r for r in activities if r['level'] == SANITATION)), 'activities_ranked': len(large)}


def sector_same_day(outcome: dict, sector: str) -> dict:
    """A sector's 24-hour contrast against the average loan, in percentage points."""
    row = next(r for r in outcome['sector_contrasts'] if r['sector'] == sector)
    return {'sector': sector, 'records': row['records'], 'pp': row['estimate'] * 100, 'ci95_pp': [v * 100 for v in row['ci95']]}


def build() -> dict:
    read = lambda path: json.loads(Path(path).read_text())
    details = read(DETAILS)['outcomes']
    return {'models': model_rows(read(BENCHMARK), read(LARGE), MODELS, EXTRA_MODELS), 'purpose': purpose_contrasts(details['log_funding_speed']),
            'sanitation_same_day': sector_same_day(details['funded_within_24h'], 'Sanitation & Hygiene')}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
