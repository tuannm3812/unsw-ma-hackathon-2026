"""Split the HC3-versus-clustered sensitivity check into text terms and control terms.

Reads the saved primary run's `association_summary.txt` (Cluster-Robust Sensitivity Check)
and counts, per model, the terms significant under HC3 and those whose conclusion changes
under country-clustered errors.

Rule: a term is a text term when any part of it is a description-derived feature (framing
rates, sentiment, description form, length or specificity), including its interactions with
control variables. Every other term is a control term. Aggregates only.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TEXT = re.compile(r'mentions_per_100_words|sentiment|desc_|description|number_token|age_pattern|years_in_business')
LINE = re.compile(r'^\s+- (?P<term>.+?): HC3 p=(?P<hc3>[\d.]+) \((?P<hc3_sig>significant|not significant)\); '
                  r'clustered p=(?P<cl>[\d.]+) \((?P<cl_sig>significant|not significant)\)')


def split(text: str) -> dict:
    section = text.split('Cluster-Robust Sensitivity Check', 1)[1].split('Average Within-Region', 1)[0]
    models, current = {}, None
    for raw in section.splitlines():
        if raw and not raw.startswith(' ') and raw.rstrip().endswith(':'):
            current = raw.rstrip(':').strip()
            models[current] = []
            continue
        m = LINE.match(raw)
        if m and current:
            models[current].append(m.groupdict())
    result = {'rule': 'text term = any term containing a description-derived feature, including interactions',
              'models': {}}
    totals = {'text': {'tested': 0, 'significant': 0, 'lost': 0}, 'control': {'tested': 0, 'significant': 0, 'lost': 0}}
    for name, rows in models.items():
        counts = {'text': {'tested': 0, 'significant': 0, 'lost': 0}, 'control': {'tested': 0, 'significant': 0, 'lost': 0}}
        for row in rows:
            kind = 'text' if TEXT.search(row['term']) else 'control'
            counts[kind]['tested'] += 1
            if row['hc3_sig'] == 'significant':
                counts[kind]['significant'] += 1
                if row['cl_sig'] == 'not significant':
                    counts[kind]['lost'] += 1
        result['models'][name] = counts
        for kind in counts:
            for key in counts[kind]:
                totals[kind][key] += counts[kind][key]
    result['total'] = totals
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, default=Path('reports/generated_full_dataset/association_summary.txt'))
    parser.add_argument('--output', type=Path, default=Path('reports/evidence_sources/clustering_split.json'))
    args = parser.parse_args(argv)
    args.output.write_text(json.dumps(split(args.summary.read_text()), indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
