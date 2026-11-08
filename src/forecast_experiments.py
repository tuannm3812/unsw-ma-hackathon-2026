"""Summarise the stronger-forecaster and text-placebo experiments for the deck.

Reads the Kaggle outputs in `reports/kaggle_experiments/forecast/reports/` and writes
`reports/evidence_sources/forecast_experiments.json`:

- larger boosted tree: annual gain from adding full text (S to S+M+L+D) in MAE days and Brier
  score, 95% intervals resampling months and countries, and how often structure alone beats
  the benchmark-sized tree;
- text placebo (text shuffled within country, sector and month): the context part of the
  linear gain, the loan-specific remainder and their intervals.

Fixed-model resampling sensitivities, not causal or retraining intervals. Nothing here measures
an edit to a description. Aggregates only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORECAST = ROOT / 'reports/kaggle_experiments/forecast/reports'
OUTPUT = ROOT / 'reports/evidence_sources/forecast_experiments.json'
BASELINE, FULL_TEXT = 'S', 'S+M+L+D'


def _excludes_zero(interval: list[float]) -> bool:
    return interval[0] > 0 or interval[1] < 0


def tree_summary(large: dict, benchmark: dict) -> dict:
    """Annual full-text gains on the larger tree, and structure-only MAE against the benchmark tree."""
    rows = {(p['year'], p['metric'], p['resampling_unit']): p for p in large['paired']
            if p['baseline'] == BASELINE and p['candidate'] == FULL_TEXT}
    structure = {w['year']: w['mae_days'] for w in large['windows'] if w['arm'] == BASELINE}
    reference = {w['year']: w['mae_days'] for w in benchmark['windows'] if w['arm'] == BASELINE}
    years = {}
    for year in sorted({key[0] for key in rows}):
        month, country = rows[(year, 'mae_days', 'calendar_month')], rows[(year, 'mae_days', 'country')]
        years[str(year)] = {'mae_gain': month['gain'], 'month': month['interval_95'], 'country': country['interval_95'],
                            'brier_gain': rows[(year, 'brier', 'calendar_month')]['gain']}
    return {'years': years,
            'month_excludes_zero': sum(_excludes_zero(y['month']) for y in years.values()),
            'country_excludes_zero': sum(_excludes_zero(y['country']) for y in years.values()),
            'brier_positive_years': sum(y['brier_gain'] > 0 for y in years.values()),
            'structure_lower_error_years': sum(structure[y] < reference[y] for y in structure),
            'years_compared': len(structure)}


def placebo_summary(data: dict) -> dict:
    """Context part (shuffled text) and loan-specific remainder of the linear gain, per year."""
    years = {}
    for row in data['years']:
        context, real = row['gain_shuffled']['gain'], row['gain_real']['gain']
        specific = row['real_minus_shuffled']
        years[str(row['year'])] = {'real': real, 'context': context, 'context_share': context / real,
                                   'loan_specific': specific['gain'], 'month': specific['interval_95'],
                                   'country': row['real_minus_shuffled_country']['interval_95']}
    shares = [y['context_share'] for y in years.values()]
    specifics = [y['loan_specific'] for y in years.values()]
    return {'years': years, 'share_rows_moved': data['share_rows_moved'],
            'context_share_range': [min(shares), max(shares)], 'loan_specific_range': [min(specifics), max(specifics)],
            'month_excludes_zero': sum(_excludes_zero(y['month']) for y in years.values()),
            'country_excludes_zero': sum(_excludes_zero(y['country']) for y in years.values())}


def build(root: Path = FORECAST) -> dict:
    read = lambda path: json.loads((root / path).read_text())
    return {'larger_tree': tree_summary(read('strong_forecaster_large/strong_forecaster.json'),
                                        read('strong_forecaster_benchmark_tree/strong_forecaster.json')),
            'text_placebo': placebo_summary(read('text_placebo/text_placebo.json'))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
