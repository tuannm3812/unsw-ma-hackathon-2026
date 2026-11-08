"""Rows for the deck's "framings against loan details" chart, from Experiment I.

Reads `reports/experiments_2026_11_08/loan_detail_coefficients.json` and writes
`reports/evidence_sources/loan_detail_summary.json`: the percentage change in (1 + days), with its
95% interval, for four loan details and the nine text terms in the programme-adjusted model.

Size-band rows are left out: amount per doubling is already within a band. Associations among
completed loans. This module deliberately computes no ratio and no ranking. Exploratory, and not
yet independently reviewed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'reports/experiments_2026_11_08/loan_detail_coefficients.json'
OUTPUT = ROOT / 'reports/evidence_sources/loan_detail_summary.json'
ROW_ORDER = {'loan_details': ['log_loan_amount', 'lenderRepaymentTerm', 'gender_classification__male', 'borrowerCount'],
             'framing': ['family_mentions_per_100_words', 'business_mentions_per_100_words',
                         'basic_needs_mentions_per_100_words', 'agency_mentions_per_100_words',
                         'gratitude_mentions_per_100_words', 'urgency_mentions_per_100_words',
                         'first_person_mentions_per_100_words', 'third_person_mentions_per_100_words',
                         'desc_sentiment_compound']}


def summarise(data: dict) -> dict:
    """The chart's rows in display order, plus the largest mention-rate point estimate."""
    outcome = data['outcomes']['log_funding_speed']
    rows = {r['term']: {'term': r['term'], 'unit': r['unit'], 'pct': r['pct_change_in_1_plus_days'], 'ci95': r['pct_ci95']}
            for block in ('framing', 'numeric', 'categories') for r in outcome[block]}
    picked = {group: [rows[term] for term in terms] for group, terms in ROW_ORDER.items()}
    mentions = [abs(r['pct']) for r in picked['framing'] if r['term'] != 'desc_sentiment_compound']
    return {**picked, 'largest_mention_rate_estimate': max(mentions)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(summarise(json.loads(SOURCE.read_text())), indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
