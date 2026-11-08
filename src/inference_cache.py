"""Private cache of the October reviewed inference frame, plus subgroup keys.

Rebuilds the frame `src.research_review.build_review_frame` fits (same
25,000-row chunked feature build, same programme proxy) and keeps extra
grouping columns needed for subgroup checks. Written under
`reports/inference_private/`, which `.gitignore` excludes. Not for sharing.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.data_loader import load_kiva_pickle
from src.feature_sensitivity import (
    EXPANDED_NARRATIVE_FEATURES, RICH_CATEGORICAL_CONTROLS, RICH_NUMERIC_CONTROLS,
    build_sensitivity_frame,
)

EXTRA = ["analysis_period", "region", "gender_classification", "sector", "fundraisingDate"]


def build(df: pd.DataFrame, chunk_size: int = 25000) -> pd.DataFrame:
    columns = list(dict.fromkeys(
        ["valid_completed_outcome", "log_funding_speed", "funded_within_24h",
         "funding_speed_days", "country_name"] + EXPANDED_NARRATIVE_FEATURES
        + RICH_NUMERIC_CONTROLS + RICH_CATEGORICAL_CONTROLS + EXTRA))
    pieces = []
    for start in range(0, len(df), chunk_size):
        piece = build_sensitivity_frame(df.iloc[start:start + chunk_size])
        pieces.append(piece[[c for c in columns if c in piece.columns]])
        if start % 250000 == 0:
            print(f"Features: {min(start + chunk_size, len(df)):,}/{len(df):,}", flush=True)
    result = pd.concat(pieces)
    labels = df["whySpecial"].astype("string").str.strip()
    labels = labels.mask(labels.eq(""))
    result["programme_proxy"] = pd.factorize(labels, sort=True)[0].astype(str)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=Path("data/Kiva_Loans.pkl"))
    parser.add_argument("--output", type=Path,
                        default=Path("reports/inference_private/review_frame.pkl"))
    args = parser.parse_args(argv)
    frame = build(load_kiva_pickle(str(args.data)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.loc[frame["valid_completed_outcome"]].to_pickle(args.output)
    print(f"Wrote {args.output}: {list(frame.columns)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
