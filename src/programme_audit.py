"""Aggregate audit of whySpecial as an unvalidated programme-text proxy.

No category text or borrower-level data is exported. This describes coverage
and dependence; it cannot identify field partners or establish causality.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.data_loader import load_kiva_pickle, prepare_analysis_data, validate_schema


def audit_programme_proxy(
    df: pd.DataFrame, *, min_group_size: int = 1000
) -> dict[str, object]:
    """Summarise valid-duration records; blank labels count as missing.

    Single-country nesting is certified only for levels whose country is
    observed for every row. Raw labels are matched after trimming whitespace;
    their identity is not interpreted as a partner or programme identifier.
    """
    if min_group_size < 1:
        raise ValueError("min_group_size must be positive")
    validate_schema(df, ["whySpecial", "country_iso", "description"])
    prepared = prepare_analysis_data(df)
    valid = prepared.loc[prepared["valid_completed_outcome"]].copy()
    labels = valid["whySpecial"].astype("string").str.strip()
    observed = labels.notna() & labels.ne("")
    groups = pd.DataFrame({
        "label": labels[observed],
        "country": valid.loc[observed, "country_iso"].astype("string")
        .str.strip().replace("", pd.NA),
        "days": valid.loc[observed, "funding_speed_days"],
    })
    by_label = groups.groupby("label", observed=True).agg(
        loans=("days", "size"), mean_days=("days", "mean"),
        countries=("country", "nunique"), known_country_rows=("country", "count"),
    )
    complete = by_label["known_country_rows"].eq(by_label["loans"])
    single = complete & by_label["countries"].eq(1)
    populated = by_label.loc[by_label["loans"].ge(min_group_size)]
    descriptions = valid.loc[observed, "description"].astype("string").str.strip()
    descriptions = descriptions[descriptions.notna() & descriptions.ne("")]
    observed_rows = int(observed.sum())
    return {
        "input_rows": int(len(df)),
        "valid_rows": int(len(valid)),
        "excluded_rows": int(len(df) - len(valid)),
        "missing_programme_rows": int((~observed).sum()),
        "observed_programme_rows": observed_rows,
        "observed_programme_levels": int(len(by_label)),
        "fully_observed_country_levels": int(complete.sum()),
        "single_country_levels": int(single.sum()),
        "single_country_level_share": (
            float(single.sum() / complete.sum()) if complete.any() else None
        ),
        "single_country_loan_share_among_observed_programmes": (
            float(by_label.loc[single, "loans"].sum() / observed_rows)
            if observed_rows else None
        ),
        "min_group_size": min_group_size,
        "well_populated_levels": int(len(populated)),
        "well_populated_rows": int(populated["loans"].sum()),
        "well_populated_mean_days_range": (
            [float(populated["mean_days"].min()),
             float(populated["mean_days"].max())]
            if len(populated) else None
        ),
        "rows_in_repeated_descriptions_among_observed_programmes": int(
            descriptions.duplicated(keep=False).sum()
        ),
        "observed_nonblank_description_rows": int(len(descriptions)),
        "interpretation": (
            "Exact programme-text groups are candidate controls, not verified "
            "field-partner identifiers. Descriptive mean gaps are unadjusted "
            "associations among completed-duration records. Repeated text "
            "alone does not prove partner authorship."
        ),
    }


def file_sha256(path: Path) -> str:
    """Hash large inputs in chunks rather than retaining another full copy."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--min-group-size", type=int, default=1000)
    args = parser.parse_args(argv)
    if args.output_dir.exists():
        raise FileExistsError("Choose a new output directory to preserve prior runs")
    root = Path(__file__).resolve().parents[1]
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
        text=True, check=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, capture_output=True,
        text=True, check=True,
    ).stdout
    provenance = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_revision": revision,
        "git_tree_dirty": bool(status.strip()),
        "data_filename": args.data.name,
        "data_sha256": file_sha256(args.data),
        "data_size_bytes": args.data.stat().st_size,
        "source_hashes": {
            str(path.relative_to(root)): file_sha256(path)
            for path in [Path(__file__).resolve(), root / "src/data_loader.py"]
        },
        "software_versions": {"python": platform.python_version(), "pandas": pd.__version__},
        "configuration": {"min_group_size": args.min_group_size},
    }
    audit = audit_programme_proxy(
        load_kiva_pickle(str(args.data)), min_group_size=args.min_group_size
    )
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "programme_audit.json").write_text(
        json.dumps({"analysis_scope": "exploratory_programme_proxy_audit",
                    "provenance": provenance, "audit": audit},
                   indent=2, allow_nan=False) + "\n", encoding="utf-8",
    )
    print(json.dumps(audit, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
