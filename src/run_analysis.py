"""
Reproducible, auditable CLI orchestration for the full Kiva funding-speed
analysis.

This module wires together the three modeling stages already built by
earlier tasks - the leakage-safe chronological baseline+Ridge evaluation
(`src/modeling.py`, Task 4), the robust explanatory association models
(`src/statistical_analysis.py`, Task 5), and the nonlinear benchmark
(`src/advanced_modeling.py`, Task 6) - against one loaded dataset, and
writes the results out as two auditable reports:

  - `analysis_summary.json`: a machine-readable, JSON-serializable summary
    (dataset audit trail, all three stages' metrics, software versions).
  - `association_summary.txt`: a human-readable association-language
    report (same audit trail, plus the full explanatory-model narrative
    from `format_association_summary`).

This module deliberately introduces no new modeling logic of its own -
every number in these reports comes from calling the three modules above
exactly as they document. Its job is orchestration, auditability (record
dataset size, date range, exclusion counts, split boundary, and software
versions, so a report can be traced back to the run that produced it), and
resilience: a too-small chronological split degrades that one section of
the report to a diagnostic string instead of crashing the entire run, the
same "catch, record a diagnostic, keep going" pattern
`src/statistical_analysis.py` already applies per-model (see
`fit_explanatory_models`'s `duration_error`/`binary_error`). Since the
baseline+Ridge evaluation (Task 4) and the nonlinear benchmark (Task 6)
both build their chronological train/holdout split via the same
`prepare_chronological_matrices` helper and the same
`MIN_SPLIT_OBSERVATIONS` floor, a `holdout_start` that is too aggressive
for one is too aggressive for the other - so both stages, not just the
nonlinear benchmark, are attempted defensively here. Only
`src.validation.InsufficientDataError` is caught for this, though - a
narrower net than "any `ValueError`" - so a genuinely different bug (e.g.
a misconfigured predictor allowlist) still fails loudly instead of being
silently downgraded into a report that merely looks like "sample too
small."
"""

import argparse
import json
import os
import platform
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import statsmodels

try:
    from src.advanced_modeling import evaluate_boosted_model
    from src.data_loader import load_kiva_pickle, prepare_analysis_data
    from src.modeling import evaluate_chronological_models
    from src.statistical_analysis import fit_explanatory_models, format_association_summary
    from src.validation import InsufficientDataError
except ModuleNotFoundError:
    from advanced_modeling import evaluate_boosted_model
    from data_loader import load_kiva_pickle, prepare_analysis_data
    from modeling import evaluate_chronological_models
    from statistical_analysis import fit_explanatory_models, format_association_summary
    from validation import InsufficientDataError


def _json_default(obj):
    """
    Fallback encoder for `json.dump`, converting any stray numpy scalar
    (e.g. `numpy.int64` from a pandas `.value_counts()`/`.to_dict()`) to its
    native Python equivalent via `.item()`. Everything this module
    deliberately puts into the report dict is already a plain Python type,
    so this is a safety net, not the primary conversion path.
    """
    if hasattr(obj, "item"):
        return obj.item()
    return str(obj)


def _atomic_write_text(path: Path, content: str) -> None:
    """
    Write `content` to `path` atomically: write to a temp file in the same
    directory, then `os.replace` it into place. A crash or interruption
    mid-write leaves either the old file (if any) or nothing at `path` -
    never a truncated/partial file - because `os.replace` is a single
    filesystem rename, not a byte-by-byte copy.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_name, str(path))
    except BaseException:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def _software_versions() -> dict:
    return {
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
        "statsmodels": statsmodels.__version__,
    }


def _describe_dataset(df: pd.DataFrame, prepared: pd.DataFrame, holdout_start: str, source_path: Path) -> dict:
    """
    Build the audit-trail section of the report: row counts, valid-outcome
    counts, exclusion reasons, date range, per-period counts, and the
    24-hour funding share - everything `prepare_analysis_data` derived,
    summarized so a reader can sanity-check the report against the source
    file without re-running anything.
    """
    n_rows = int(len(df))
    valid_mask = prepared["valid_completed_outcome"]
    n_valid = int(valid_mask.sum())

    exclusion_reasons = {}
    if n_valid < n_rows:
        reasons = prepared.loc[~valid_mask, "outcome_issue"]
        counts = reasons[reasons != ""].value_counts()
        exclusion_reasons = {str(reason): int(count) for reason, count in counts.items()}

    dates = prepared["fundraisingDate"].dropna()
    if dates.empty:
        raise ValueError(
            "Cannot build a date-range audit trail: no row has a parseable "
            "fundraisingDate"
        )
    date_min = dates.min().isoformat()
    date_max = dates.max().isoformat()

    period_counts_raw = prepared["analysis_period"].value_counts(dropna=False)
    period_counts = {}
    for label, count in period_counts_raw.items():
        key = "missing" if pd.isna(label) else str(label)
        period_counts[key] = int(count)

    binary_outcomes = prepared.loc[valid_mask, "funded_within_24h"].dropna()
    funded_within_24h_share = (
        float(binary_outcomes.astype(int).mean()) if len(binary_outcomes) else None
    )

    return {
        "source_path": str(source_path),
        "n_rows": n_rows,
        "n_valid_completed_outcome": n_valid,
        "n_excluded": n_rows - n_valid,
        "exclusion_reasons": exclusion_reasons,
        "date_min": date_min,
        "date_max": date_max,
        "holdout_start": holdout_start,
        "period_counts": period_counts,
        "funded_within_24h_share": funded_within_24h_share,
    }


def _run_baseline_ridge(df: pd.DataFrame, holdout_start: str, n_topics: int) -> dict:
    """
    Run the leakage-safe chronological baseline+Ridge evaluation (Task 4),
    stripped of `_artifacts`. Catches only `InsufficientDataError`
    (raised when the chronological split itself is too small or
    unusable) - not every `ValueError`, since e.g. a misconfigured
    predictor allowlist also raises `ValueError` and that is a
    programming bug that must fail loudly, not get silently downgraded
    into a report that merely looks like "sample too small." It shares
    its split logic with the nonlinear benchmark below, so a
    `holdout_start` too aggressive for one is too aggressive for the
    other.
    """
    try:
        results = evaluate_chronological_models(df, holdout_start=holdout_start, n_topics=n_topics)
        results.pop("_artifacts", None)
        results["attempted"] = True
        results["succeeded"] = True
        results["error"] = None
        return results
    except InsufficientDataError as error:
        return {
            "attempted": True,
            "succeeded": False,
            "error": str(error),
        }


def _run_nonlinear_benchmark(df: pd.DataFrame, holdout_start: str, n_topics: int, random_state: int) -> dict:
    """
    Attempt the nonlinear (gradient-boosted) benchmark (Task 6), recording
    a clear diagnostic instead of crashing if the chronological split is
    too small - the failure mode `prepare_chronological_matrices` raises
    via `InsufficientDataError` when either partition has fewer than
    `MIN_SPLIT_OBSERVATIONS` valid rows. Only that specific error is
    caught; an unrelated `ValueError` (a real bug elsewhere in the
    pipeline) is left to propagate.
    """
    try:
        results = evaluate_boosted_model(
            df, holdout_start=holdout_start, n_topics=n_topics, random_state=random_state
        )
        results.pop("_artifacts", None)
        importance = results.pop("importance")
        results["importance"] = [
            {"feature": str(row["feature"]), "permutation_importance": float(row["permutation_importance"])}
            for row in importance.to_dict(orient="records")
        ]
        results["attempted"] = True
        results["succeeded"] = True
        results["error"] = None
        return results
    except InsufficientDataError as error:
        return {
            "attempted": True,
            "succeeded": False,
            "error": str(error),
        }


def _run_explanatory(df: pd.DataFrame) -> dict:
    """
    Run the robust explanatory (association) models (Task 5). Each of the
    duration/binary sub-models already degrades independently to a
    diagnostic inside `fit_explanatory_models` (see `duration_error`/
    `binary_error`); `fit_explanatory_models` itself only raises
    `InsufficientDataError` if the data can't support fitting anything at
    all (no valid-outcome rows, no usable predictors after pruning, or
    neither model could be fit) - caught here so that edge case degrades
    this section of the report too, rather than crashing the whole run.
    Only `InsufficientDataError` is caught, not every `ValueError`, for
    the same reason as the chronological stages above: an unrelated bug
    (e.g. in feature extraction or formula construction) must still fail
    loudly.
    """
    try:
        results = fit_explanatory_models(df)
        return {
            "attempted": True,
            "succeeded": True,
            "error": None,
            "n_duration": results["n_duration"],
            "n_binary": results["n_binary"],
            "duration_fitted": results["duration"] is not None,
            "binary_fitted": results["binary"] is not None,
            "duration_error": results["duration_error"],
            "binary_error": results["binary_error"],
            "duration_formula": results["duration_formula"],
            "binary_formula": results["binary_formula"],
            "duration_dropped_terms": results["duration_dropped_terms"],
            "binary_dropped_terms": results["binary_dropped_terms"],
        }, results
    except InsufficientDataError as error:
        return {
            "attempted": True,
            "succeeded": False,
            "error": str(error),
            "n_duration": None,
            "n_binary": None,
            "duration_fitted": False,
            "binary_fitted": False,
            "duration_error": str(error),
            "binary_error": str(error),
            "duration_formula": None,
            "binary_formula": None,
            "duration_dropped_terms": None,
            "binary_dropped_terms": None,
        }, None


def _format_audit_header(data_section: dict, versions: dict) -> "list[str]":
    lines = [
        "Audit trail",
        "-" * 62,
        f"Source file: {data_section['source_path']}",
        f"Rows loaded: {data_section['n_rows']}",
        f"Rows with a valid completed outcome: {data_section['n_valid_completed_outcome']}",
        f"Rows excluded: {data_section['n_excluded']} ({data_section['exclusion_reasons']})",
        f"fundraisingDate range: {data_section['date_min']} to {data_section['date_max']}",
        f"Chronological holdout boundary: {data_section['holdout_start']}",
        f"Period counts: {data_section['period_counts']}",
        f"Funded-within-24h share (valid outcomes): {data_section['funded_within_24h_share']}",
        "Software versions: " + ", ".join(f"{name}={version}" for name, version in versions.items()),
        "",
    ]
    return lines


def run_analysis(data_path, output_dir, holdout_start: str = "2024-01-01", n_topics: int = 5) -> dict:
    """
    Run the full Kiva funding-speed analysis (chronological baseline+Ridge,
    robust explanatory models, nonlinear benchmark) against the pickle at
    `data_path`, and write `analysis_summary.json` and
    `association_summary.txt` into `output_dir`.

    `data_path`/`output_dir` are resolved via `pathlib.Path(...).resolve()`
    so a relative path is interpreted relative to the caller's current
    working directory - not to this module's location or any assumed repo
    root - exactly like a normal CLI tool.

    Returns the same JSON-serializable dict that is written to
    `analysis_summary.json` (no `_artifacts` key anywhere, including
    nested).
    """
    data_path = Path(data_path).resolve()
    output_dir = Path(output_dir).resolve()

    print(f"Loading data from {data_path}...")
    df = load_kiva_pickle(str(data_path))
    prepared = prepare_analysis_data(df)

    data_section = _describe_dataset(df, prepared, holdout_start, data_path)
    versions = _software_versions()

    print(f"Running chronological baseline + Ridge evaluation (holdout_start={holdout_start})...")
    baseline_ridge = _run_baseline_ridge(df, holdout_start, n_topics)

    print("Fitting robust explanatory association models...")
    explanatory_section, explanatory_raw = _run_explanatory(df)

    print("Attempting the nonlinear (gradient-boosted) benchmark...")
    nonlinear_benchmark = _run_nonlinear_benchmark(df, holdout_start, n_topics, random_state=42)

    summary = {
        "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "software_versions": versions,
        "data": data_section,
        "baseline_ridge": baseline_ridge,
        "nonlinear_benchmark": nonlinear_benchmark,
        "explanatory": explanatory_section,
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "analysis_summary.json"
    _atomic_write_text(json_path, json.dumps(summary, indent=2, default=_json_default) + "\n")

    text_lines = [
        "UNSW Marketing Analytics Hackathon 2026 - Reproducible Analysis Report",
        "=" * 72,
        "",
    ]
    text_lines.extend(_format_audit_header(data_section, versions))
    if explanatory_raw is not None:
        text_lines.append(format_association_summary(explanatory_raw))
    else:
        text_lines.append(
            "Explanatory Association Summary (robust HC3 standard errors)\n"
            + "=" * 62
            + "\n\nNeither the duration nor the 24-hour funding explanatory model "
            f"could be reliably fit on this sample: {explanatory_section['error']}"
        )
    text_lines.append("")
    association_path = output_dir / "association_summary.txt"
    _atomic_write_text(association_path, "\n".join(text_lines) + "\n")

    print(f"Wrote {json_path}")
    print(f"Wrote {association_path}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Run the full leakage-safe Kiva funding-speed analysis "
            "(chronological baseline+Ridge, robust explanatory models, and "
            "a nonlinear benchmark) and write auditable reports."
        )
    )
    parser.add_argument("--data", required=True, help="Path to the raw Kiva loans pickle file.")
    parser.add_argument(
        "--output-dir", required=True, help="Directory to write analysis_summary.json and association_summary.txt into."
    )
    parser.add_argument(
        "--holdout-start",
        default="2024-01-01",
        help="Chronological holdout boundary (ISO date), default 2024-01-01.",
    )
    args = parser.parse_args()

    run_analysis(args.data, args.output_dir, holdout_start=args.holdout_start)
