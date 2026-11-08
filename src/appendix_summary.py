"""Read the model comparison and loan-purpose contrasts for the deck's appendix.

Writes `reports/evidence_sources/appendix_summary.json`:

- forecast MAE per test year and the 24-hour ROC AUC range for the fixed models in the November
  benchmark and the larger boosted tree;
- sector and activity contrasts on (1 + days) from Experiment I, ranked among activities with at
  least 1,000 loans, and the toilets and sanitation activity;
- from the Kaggle appendix run, exploratory tuned boosted tree and XGBoost scores, text gains, the
  flag's margin over the lookup, and the eight-theme chart from the 20,000-description sample.

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
EXPERIMENTS = ROOT / 'reports/experiments_2026_11_08/appendix_experiments.json'
TUNED_MODELS = (('Tuned tree, loan details', 'hgb_tuned_S'), ('Tuned tree, full text', 'hgb_tuned_S+M+L+D'),
                ('Tuned XGBoost, loan details', 'xgb_tuned_S'), ('Tuned XGBoost, full text', 'xgb_tuned_S+M+L+D'))
FULL_TEXT = 'S+M+L+D'
FLAG_MODEL = 'compact_fixed_S'
THEME_LABELS = {'pigs': 'Pig raising', 'business': 'Business and family', 'sanitary': 'Sanitary and toilets',
                'water': 'Water and filters', 'store': 'General store', 'farm': 'Farm inputs', 'group': 'Group solar and farms'}
PHILIPPINES_THEME = 'Philippines business'


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


def larger_tree_with_text(large: dict) -> dict:
    """The fixed larger boosted tree with full text, in the same row shape as `model_rows`."""
    windows = [{'year': w['year'], 'mae': w['mae_days'], 'auc': w['roc_auc']} for w in large['windows'] if w['arm'] == FULL_TEXT]
    return _row('Larger tree, full text', windows)


def tuned_summary(experiments: dict) -> dict:
    """Tuned rows by year, fixed against tuned on loan details, and the tuned trees' full-text gains."""
    years = experiments['years']
    rows = [{'name': name, 'mae': {str(y['year']): y['mae'][key] for y in years}} for name, key in TUNED_MODELS]
    versus, gains = [], []
    for y in years:
        mae = y['mae']
        fixed, tuned = min(mae['compact_fixed_S'], mae['large_fixed_S']), min(mae['hgb_tuned_S'], mae['xgb_tuned_S'])
        versus.append({'year': y['year'], 'best_fixed': fixed, 'best_tuned': tuned, 'tuned_lower_by': fixed - tuned,
                       'xgb_below_tuned_tree': mae['xgb_tuned_S'] < mae['hgb_tuned_S']})
        for family in ('hgb', 'xgb'):
            pair = {g['unit']: g for g in y['text_gain'] if g['family'] == family and g['candidate'] == FULL_TEXT}
            gains.append({'year': y['year'], 'family': family, 'gain': pair['month']['gain'],
                          'month_95': pair['month']['interval_95'], 'country_95': pair['country']['interval_95']})
    return {'rows': rows, 'versus_fixed': versus, 'text_gains': gains, 'test_rows': {str(y['year']): y['test_rows'] for y in years},
            'settings': {str(y['year']): {k: y['tuning'][k]['params'] for k in ('hgb', 'xgb')} for y in years},
            'trials_per_family': len(years[0]['tuning']['hgb_trials']), 'xgboost_version': experiments['xgboost_version']}


def flag_margin(experiments: dict, model: str = FLAG_MODEL) -> list[dict]:
    """The flag's lift and within-country precision, with 95% ranges for its margin over the lookup.

    The country bootstrap is reported for lift only, as the experiment labels it.
    """
    out = []
    for y in experiments['years']:
        scored, margin = y['triage']['models'][model], y['triage']['minus_lookup_95']
        out.append({'year': y['year'], 'lift': scored['top_10']['lift'], 'precision': scored['top_10']['precision'],
                    'within': scored['within_country_median_precision_top_10'],
                    'lift_margin_month_95': margin['month_block'][model]['lift'],
                    'within_margin_month_95': margin['month_block'][model]['within'],
                    'lift_margin_country_95': margin['country_block_lift_only'][model]['lift']})
    return out


def theme_rows(themes: dict) -> list[dict]:
    """The eight sample themes, fastest raw mean first, with adjusted contrasts."""
    def label(words: list[str]) -> str:
        return PHILIPPINES_THEME if 'philippines' in words[:3] else THEME_LABELS[words[0]]

    def brief(row: dict) -> dict:
        return {'pct': row['pct_change_in_1_plus_days'], 'ci95': row['pct_ci95'], 'p': row['p']}

    rows = [{'label': label(t['top_words']), 'top_words': t['top_words'], 'n': t['n'], 'mean_days': t['mean_days'],
             'median_days': t['median_days'], 'adjusted': brief(t['adjusted_loan_details']),
             'adjusted_plus_activity': brief(t['adjusted_plus_activity'])} for t in themes['themes']]
    return sorted(rows, key=lambda r: r['mean_days'])


def build() -> dict:
    read = lambda path: json.loads(Path(path).read_text())
    details = read(DETAILS)['outcomes']
    large, experiments = read(LARGE), read(EXPERIMENTS)
    return {'models': model_rows(read(BENCHMARK), large, MODELS, EXTRA_MODELS), 'purpose': purpose_contrasts(details['log_funding_speed']),
            'sanitation_same_day': sector_same_day(details['funded_within_24h'], 'Sanitation & Hygiene'),
            'larger_tree_with_text': larger_tree_with_text(large), 'tuned': tuned_summary(experiments),
            'flag_margin': flag_margin(experiments), 'themes': {'sample_rows': experiments['themes']['sample_rows'],
                                                                'clusters': experiments['themes']['clusters'],
                                                                'rows': theme_rows(experiments['themes'])}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
