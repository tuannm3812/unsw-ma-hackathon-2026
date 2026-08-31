"""Run this project's authoritative `src/` pipeline on Kaggle's compute.

Regenerates the committed `reports/generated_full_dataset/` snapshot
(analysis_summary.json + association_summary.txt) with the exact flags
README.md documents, so a laptop never has to run the ~2 h job:

    python3 -m src.run_analysis --data data/Kiva_Loans.pkl \
        --output-dir reports/generated_full_dataset \
        --extra-interaction 'family_mentions_per_100_words:C(sector_group)' \
        --cluster-sensitivity-column country_name

Inputs are two private Kaggle Datasets mounted read-only:
  - tuannm3812/kiva-loans-hackathon-data  -> Kiva_Loans.pkl
  - tuannm3812/kiva-hackathon-src         -> src/, resources/, requirements*.txt
The code dataset is uploaded with `--dir-mode zip`, and Kaggle does not
reliably auto-extract zipped directories at mount time, so this script
rebuilds the repo layout under /kaggle/working/repo itself - copying
directories if they arrived extracted, unzipping them if not. That layout
matters: src/features.py finds the vendored VADER lexicon relative to its
own file (../resources/nltk_data), so `src/` and `resources/` must be
siblings exactly as in the repository. No network access is needed.

Outputs land in /kaggle/working/generated_full_dataset/ and are retrieved
with `kaggle kernels output tuannm3812/kiva-hackathon-full-dataset-pipeline`.
"""
import hashlib
import json
import shutil
import sys
import time
import zipfile
from pathlib import Path

DATA_CANDIDATES = [
    Path("/kaggle/input/datasets/tuannm3812/kiva-loans-hackathon-data"),
    Path("/kaggle/input/kiva-loans-hackathon-data"),
]
CODE_CANDIDATES = [
    Path("/kaggle/input/datasets/tuannm3812/kiva-hackathon-src"),
    Path("/kaggle/input/kiva-hackathon-src"),
]
REPO = Path("/kaggle/working/repo")
OUTPUT_DIR = Path("/kaggle/working/generated_full_dataset")


def first_existing(candidates, label):
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"{label} dataset not mounted; tried {[str(c) for c in candidates]}")


def materialise(code_root: Path, name: str) -> None:
    """Place `name/` under REPO whether the dataset shipped it as a directory or a zip."""
    target = REPO / name
    if target.exists():
        shutil.rmtree(target)
    as_dir = code_root / name
    as_zip = code_root / f"{name}.zip"
    if as_dir.is_dir():
        shutil.copytree(as_dir, target)
        print(f"copied {as_dir} -> {target}")
    elif as_zip.is_file():
        with zipfile.ZipFile(as_zip) as archive:
            names = archive.namelist()
            # Zips made by the Kaggle CLI may or may not carry the top-level
            # directory prefix; normalise either way.
            prefixed = all(n.startswith(f"{name}/") for n in names if n)
            archive.extractall(REPO if prefixed else target)
        print(f"extracted {as_zip} -> {target} (prefixed={prefixed})")
    else:
        raise FileNotFoundError(f"neither {as_dir} nor {as_zip} exists in the code dataset")


def main() -> None:
    t0 = time.time()
    data_root = first_existing(DATA_CANDIDATES, "data")
    code_root = first_existing(CODE_CANDIDATES, "code")
    print("data dataset:", data_root, "| code dataset:", code_root)
    print("code dataset contents:", sorted(p.name for p in code_root.iterdir()))

    REPO.mkdir(parents=True, exist_ok=True)
    materialise(code_root, "src")
    materialise(code_root, "resources")
    assert (REPO / "src" / "run_analysis.py").is_file(), "src/run_analysis.py missing after materialise"
    sentiment_dir = REPO / "resources" / "nltk_data" / "sentiment"
    assert any(sentiment_dir.rglob("vader_lexicon*")), f"vendored VADER lexicon missing under {sentiment_dir}"

    # Immutable provenance (Codex review): the code dataset must carry the
    # PROVENANCE.json the publish script stamps (git commit + dirty flag +
    # src tree hash). Refuse to produce an evidence snapshot without it,
    # re-hash what was actually mounted, and copy the whole record into the
    # output directory so the committed snapshot names its exact inputs.
    prov_path = code_root / "PROVENANCE.json"
    if not prov_path.is_file():
        raise FileNotFoundError(
            "PROVENANCE.json missing from the code dataset - republish with "
            "scripts/publish_kaggle_dataset.sh code version '...' before running"
        )
    provenance = json.loads(prov_path.read_text(encoding="utf-8"))
    hasher_lines = []
    for f in sorted((REPO / "src").rglob("*")):
        if f.is_file():
            hasher_lines.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(REPO)}")
    mounted_src_sha = hashlib.sha256(("\n".join(hasher_lines) + "\n").encode()).hexdigest()
    provenance_out = {
        "code_dataset_provenance": provenance,
        "mounted_src_files_hashed": len(hasher_lines),
        "mounted_src_sha256_of_file_digests": mounted_src_sha,
        "data_dataset_mount": str(data_root),
        "code_dataset_mount": str(code_root),
    }
    print("provenance:", json.dumps(provenance_out, indent=2))

    sys.path.insert(0, str(REPO))
    from src.run_analysis import run_analysis  # noqa: E402

    data_path = data_root / "Kiva_Loans.pkl"
    print(f"[{time.time() - t0:.0f}s] starting run_analysis on {data_path}", flush=True)
    summary = run_analysis(
        data_path,
        OUTPUT_DIR,
        holdout_start="2024-01-01",
        extra_interactions=["family_mentions_per_100_words:C(sector_group)"],
        cluster_sensitivity_col="country_name",
    )
    print(f"[{time.time() - t0:.0f}s] done", flush=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "provenance.json").write_text(
        json.dumps(provenance_out, indent=2) + "\n", encoding="utf-8"
    )
    print("explanatory status:", summary["explanatory"].get("status"))
    print("outputs:", sorted(p.name for p in OUTPUT_DIR.iterdir()))
    report = (OUTPUT_DIR / "association_summary.txt").read_text(encoding="utf-8")
    for marker in ("Cluster-Robust Sensitivity Check", "Average Within-Region Family-Framing Slopes", "few-cluster t("):
        print(f"report contains {marker!r}:", marker in report)


if __name__ == "__main__":
    main()
