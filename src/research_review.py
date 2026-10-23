"""Reviewed expanded inference, with an exploratory programme-text control.

This reruns explanatory sensitivity only. It does not rerun primary models
or chronological prediction. Results are saved in a new directory per run.
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn
import statsmodels

from src.data_loader import load_kiva_pickle
from src.feature_sensitivity import (
    EXPANDED_NARRATIVE_FEATURES,
    NARRATIVE_FEATURE_FAMILIES,
    RICH_CATEGORICAL_CONTROLS,
    RICH_NUMERIC_CONTROLS,
    build_sensitivity_frame,
    fit_clustered_partial_regression,
    write_sensitivity_outputs,
)
from src.programme_audit import file_sha256


def build_review_frame(df: pd.DataFrame, *, chunk_size: int = 25000) -> pd.DataFrame:
    """Bound text-scoring memory while preserving all used inference inputs.

    Only unused region/sector grouping thresholds depend on chunk composition.
    Programme labels are encoded over the entire input and never exported.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    columns = list(dict.fromkeys(
        ["valid_completed_outcome", "log_funding_speed", "funded_within_24h",
         "country_name"] + EXPANDED_NARRATIVE_FEATURES +
        RICH_NUMERIC_CONTROLS + RICH_CATEGORICAL_CONTROLS
    ))
    pieces = []
    for start in range(0, len(df), chunk_size):
        piece = build_sensitivity_frame(df.iloc[start:start + chunk_size])
        pieces.append(piece[columns])
        print(f"Features: {min(start + chunk_size, len(df)):,}/{len(df):,}", flush=True)
    if not pieces:
        raise ValueError("Cannot review an empty dataset")
    result = pd.concat(pieces)
    labels = df["whySpecial"].astype("string").str.strip()
    labels = labels.mask(labels.eq(""))
    result["programme_proxy"] = pd.factorize(labels, sort=True)[0].astype(str)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--chunk-size", type=int, default=25000)
    args = parser.parse_args(argv)
    if args.output_dir.exists():
        raise FileExistsError("Choose a new output directory; prior runs are preserved")
    root = Path(__file__).resolve().parents[1]
    source_files = sorted((root / "src").glob("*.py"))
    source_hashes = {str(p.relative_to(root)): file_sha256(p) for p in source_files}
    provenance = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "git_tree_dirty": bool(subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=root, text=True).strip()),
        "source_hashes": source_hashes,
        "data_filename": args.data.name,
        "data_sha256": file_sha256(args.data),
        "data_size_bytes": args.data.stat().st_size,
        "software_versions": {"python": platform.python_version(),
                              "pandas": pd.__version__, "numpy": np.__version__,
                              "scipy": scipy.__version__, "sklearn": sklearn.__version__,
                              "statsmodels": statsmodels.__version__},
        "configuration": {"chunk_size": args.chunk_size,
                          "country_clustering": "country_name",
                          "programme_proxy": "trimmed whySpecial; missing is a separate level",
                          "prediction_rerun": False},
    }
    data = load_kiva_pickle(str(args.data))
    input_rows = len(data)
    frame = build_review_frame(data, chunk_size=args.chunk_size)
    del data
    valid = frame.loc[frame["valid_completed_outcome"]].copy()
    del frame
    provenance["input_rows"] = input_rows
    provenance["valid_duration_rows"] = len(valid)
    provenance["excluded_invalid_duration_rows"] = input_rows - len(valid)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    for scenario, additional_controls in [
        ("expanded", []), ("programme_adjusted", ["programme_proxy"])
    ]:
        inference = {}
        for outcome in ["log_funding_speed", "funded_within_24h"]:
            print(f"Fitting {scenario}: {outcome}", flush=True)
            inference[outcome] = fit_clustered_partial_regression(
                valid, outcome=outcome,
                narrative_features=EXPANDED_NARRATIVE_FEATURES,
                numeric_controls=RICH_NUMERIC_CONTROLS,
                categorical_controls=RICH_CATEGORICAL_CONTROLS + additional_controls,
                cluster_col="country_name", feature_families=NARRATIVE_FEATURE_FAMILIES,
            )
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "analysis_scope": f"reviewed_{scenario}_inference_not_primary_specification",
            "prediction": {}, "inference": inference,
            "interpretation": (
                "Explanatory sensitivity among valid completed durations only. "
                "Programme text is an unvalidated proxy, not field-partner identity. "
                "No causal effect, primary-model rerun or predictive rerun is claimed."
            ),
            "provenance": provenance,
        }
        write_sensitivity_outputs(payload, args.output_dir / scenario)
    changed = [str(p.relative_to(root)) for p in source_files
               if source_hashes[str(p.relative_to(root))] != file_sha256(p)]
    provenance["source_changed_during_run"] = changed
    provenance["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    (args.output_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    if changed:
        raise RuntimeError("Source changed during run; results require provenance review")
    print("Reviewed inference complete; primary snapshot unchanged.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
