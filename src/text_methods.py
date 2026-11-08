"""Inventory of the text methods behind the deck, read from the code that runs them.

Writes `reports/evidence_sources/text_methods.json`: entries in each framing word list, and the
settings for TF-IDF, the compressed text features and the exploratory topic model. An entry is a
top-level alternative in the pattern, so `child(?:ren)?` counts once.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.benchmark_models import default_config
from src.features import FRAMING_PATTERNS
from src.strong_forecaster import CONFIG as STRONG_CONFIG

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'reports/evidence_sources/text_methods.json'
# From notebooks/1_full_dataset_eda.py; tests/test_text_methods.py checks they still match.
TOPICS = {'method': 'NMF on TF-IDF', 'themes': 8, 'max_features': 1000, 'min_df': 5, 'sample': 20000,
          'status': 'exploratory; sample only'}
# From src/benchmark_models.py, where TfidfVectorizer fits on training rows only.
TFIDF_FIXED = {'ngram_range': [1, 2], 'sublinear_tf': True}


def entry_count(pattern: str) -> int:
    """Top-level alternatives in a `\\b(?:a|b|c)\\b` pattern."""
    depth, entries = 0, 1
    for char in pattern.removeprefix(r'\b(?:').removesuffix(r')\b'):
        depth += (char == '(') - (char == ')')
        entries += char == '|' and depth == 0
    return entries


def build() -> dict:
    config = default_config()
    return {'word_list_entries': {name: entry_count(pattern) for name, pattern in FRAMING_PATTERNS.items()},
            'sentiment': 'VADER compound score (NLTK, vendored lexicon)',
            'tfidf': {'max_features': config['max_text_features'], 'min_df': config['min_df'], **TFIDF_FIXED},
            'compressed_components': STRONG_CONFIG['svd_components'], 'topics': TOPICS}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
