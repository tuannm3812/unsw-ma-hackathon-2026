"""Month and country intervals for the forecast text gain, for slide 12.

Reads the reviewed November benchmark (`reports/text_benchmark_reviewed/benchmark.json`) and
the loss-alignment extension (`reports/loss_alignment_2025/loss_alignment*.json`) and writes
`reports/evidence_sources/gain_intervals.json`:

- linear S → S+M+L+R and tree S → S+M+L MAE gains per year, with 95% intervals that
  resample calendar months and countries;
- the capped-forecast diagnostic (log1p target capped at the training maximum) with its
  country interval;
- how many years each country interval includes zero.

Fixed-model resampling sensitivities, not causal or retraining intervals. Aggregates only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / 'reports/text_benchmark_reviewed/benchmark.json'
ALIGNMENT = ROOT / 'reports/loss_alignment_2025'
OUTPUT = ROOT / 'reports/evidence_sources/gain_intervals.json'
ARMS = {'linear': 'S+M+L+R', 'histogram_boosting': 'S+M+L'}


def paired_intervals(comparisons: list[dict]) -> dict:
    """{family: {year: {'gain', 'month', 'country'}}} for the full text arm against S, MAE in days."""
    result: dict[str, dict[int, dict]] = {}
    for row in comparisons:
        if row['metric'] != 'mae_days' or row['baseline'] != 'S' or ARMS.get(row['family']) != row['candidate']:
            continue
        unit = {'calendar_month': 'month', 'country': 'country'}[row['resampling_unit']]
        entry = result.setdefault(row['family'], {}).setdefault(row['year'], {'gain': row['gain']})
        entry[unit] = row['interval_95']
    return result


def includes_zero(interval: list[float]) -> bool:
    return interval[0] <= 0 <= interval[1]


def capped(alignment_dir: Path = ALIGNMENT) -> dict[int, dict]:
    result = {}
    for path in sorted(alignment_dir.glob('loss_alignment*.json')):
        data = json.loads(path.read_text())
        year = data.get('year') or int(path.stem.rsplit('_', 1)[1])
        block = data['estimators']['log1p_capped']
        result[int(year)] = {'gain': block['text_gain']['mae_days'],
                             'country': block['text_gain_mae_intervals']['country']['interval_95']}
    return result


def build(benchmark: Path = BENCHMARK, alignment_dir: Path = ALIGNMENT) -> dict:
    intervals = paired_intervals(json.loads(benchmark.read_text())['paired_comparisons'])
    caps = capped(alignment_dir)
    linear = intervals['linear']
    return {
        'unit': 'MAE gain in days, positive = text lowers error; 95% intervals, 1,000 resamples',
        'linear': {str(y): v for y, v in sorted(linear.items())},
        'tree': {str(y): v for y, v in sorted(intervals['histogram_boosting'].items())},
        'linear_capped': {str(y): v for y, v in sorted(caps.items())},
        'country_includes_zero': {
            'linear': sum(includes_zero(v['country']) for v in linear.values()),
            'linear_capped': sum(includes_zero(v['country']) for v in caps.values()),
            'tree': sum(includes_zero(v['country']) for v in intervals['histogram_boosting'].values()),
        },
        'month_includes_zero': {'linear': sum(includes_zero(v['month']) for v in linear.values())},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
