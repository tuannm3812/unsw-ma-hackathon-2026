"""Run the 2026-11-08 exploratory experiments on Kaggle's compute.

JOB below selects the batch; the two experiment kernels carry the same
script and differ only in that line.

  forecast   gap F (stronger forecaster: large tree and benchmark tree, each
             with a TF-IDF SVD arm) and gap D (text placebo), from a fresh
             benchmark feature cache built on the mounted data.
  inference  gap C/G (wild cluster bootstrap, both October specifications)
             and gap B (subgroup refits, programme-adjusted then expanded),
             from a fresh October inference frame.
  appendix   tuning of HistGradientBoosting and XGBoost, the flag on fixed and
             tuned models with block intervals, and the NMF theme table.
  review_fix  rerun of the wild cluster bootstrap and loan-detail fits after
             the 2026-11-08 Codex review, from a fresh inference frame.
  loan_details  experiment I: refit the October programme-adjusted model and
             save the loan-detail coefficients, from a fresh inference frame.

Private caches hold loan text and are deleted before the kernel ends; only
aggregate JSON reports and logs stay in /kaggle/working. Same mounting and
provenance rules as notebooks/kernels/full_dataset_pipeline.
"""
import hashlib
import json
import os
import platform
import shutil
import sys
import time
import zipfile
from pathlib import Path

JOB = "inference"

DATA_CANDIDATES = [Path("/kaggle/input/datasets/tuannm3812/kiva-loans-hackathon-data"),
                   Path("/kaggle/input/kiva-loans-hackathon-data")]
CODE_CANDIDATES = [Path("/kaggle/input/datasets/tuannm3812/kiva-hackathon-src"),
                   Path("/kaggle/input/kiva-hackathon-src")]
REPO = Path("/kaggle/working/repo")
OUT = Path("/kaggle/working/reports")
PRIVATE = Path("/kaggle/working/private")


def first_existing(candidates, label):
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"{label} dataset not mounted; tried {candidates}")


def materialise(code_root, name):
    target = REPO / name
    if target.exists():
        shutil.rmtree(target)
    if (code_root / name).is_dir():
        shutil.copytree(code_root / name, target)
    else:
        with zipfile.ZipFile(code_root / f"{name}.zip") as archive:
            names = archive.namelist()
            prefixed = all(n.startswith(f"{name}/") for n in names if n)
            archive.extractall(REPO if prefixed else target)


def stamp(label, t0):
    print(f"[{time.time() - t0:.0f}s] {label}", flush=True)


def main():
    t0 = time.time()
    data_root = first_existing(DATA_CANDIDATES, "data")
    code_root = first_existing(CODE_CANDIDATES, "code")
    REPO.mkdir(parents=True, exist_ok=True)
    materialise(code_root, "src")
    materialise(code_root, "resources")
    provenance = json.loads((code_root / "PROVENANCE.json").read_text())
    digests = [f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(REPO)}"
               for f in sorted((REPO / "src").rglob("*")) if f.is_file()]
    import numpy, pandas, scipy, sklearn, statsmodels
    record = {"job": JOB, "code_dataset_provenance": provenance,
              "mounted_src_sha256_of_file_digests":
                  hashlib.sha256(("\n".join(digests) + "\n").encode()).hexdigest(),
              "cpu_count": os.cpu_count(),
              "versions": {"python": platform.python_version(), "numpy": numpy.__version__,
                           "pandas": pandas.__version__, "scipy": scipy.__version__,
                           "sklearn": sklearn.__version__, "statsmodels": statsmodels.__version__}}
    print(json.dumps(record, indent=1), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    (OUT / f"kaggle_provenance_{JOB}.json").write_text(json.dumps(record, indent=1))
    os.chdir(REPO)
    sys.path.insert(0, str(REPO))
    data = data_root / "Kiva_Loans.pkl"
    try:
        if JOB == "forecast":
            from src.benchmark_cache import load_features
            cache = PRIVATE / "features.pkl"
            load_features(data, cache, [2021, 2022, 2023, 2024, 2025])
            stamp("benchmark feature cache built", t0)
            from src import strong_forecaster, text_placebo
            strong_forecaster.main(["--cache", str(cache), "--output", str(OUT / "strong_forecaster_large")])
            stamp("large tree done", t0)
            strong_forecaster.main(["--cache", str(cache), "--tree", "benchmark",
                                    "--output", str(OUT / "strong_forecaster_benchmark_tree")])
            stamp("benchmark tree done", t0)
            text_placebo.main(["--cache", str(cache), "--output", str(OUT / "text_placebo")])
            stamp("placebo done", t0)
        elif JOB == "inference":
            from src import inference_cache, subgroup_inference, wild_cluster
            frame = PRIVATE / "review_frame.pkl"
            inference_cache.main(["--data", str(data), "--output", str(frame)])
            stamp("inference frame built", t0)
            wild_cluster.main(["--frame", str(frame), "--output", str(OUT / "wild_cluster_bootstrap")])
            stamp("wild cluster done", t0)
            for spec in ("programme_adjusted", "expanded"):
                subgroup_inference.main(["--frame", str(frame), "--spec", spec,
                                         "--output", str(OUT / "subgroup_inference")])
                stamp(f"subgroups {spec} done", t0)
        elif JOB == "appendix":
            from src.benchmark_cache import load_features
            from src import appendix_experiments
            cache = PRIVATE / "features.pkl"
            load_features(data, cache, [2021, 2022, 2023, 2024, 2025])
            stamp("benchmark feature cache built", t0)
            appendix_experiments.main(["--cache", str(cache), "--data", str(data),
                                       "--output", str(OUT / "appendix_experiments"),
                                       "--threads", "4"])
            stamp("appendix experiments done", t0)
        elif JOB == "review_fix":
            from src import inference_cache, loan_detail_coefficients, wild_cluster
            frame = PRIVATE / "review_frame.pkl"
            inference_cache.main(["--data", str(data), "--output", str(frame)])
            stamp("inference frame built", t0)
            wild_cluster.main(["--frame", str(frame), "--output", str(OUT / "wild_cluster_bootstrap")])
            stamp("wild cluster done", t0)
            loan_detail_coefficients.main(["--frame", str(frame),
                                           "--output", str(OUT / "loan_detail_coefficients")])
            stamp("loan-detail fits done", t0)
        elif JOB == "loan_details":
            from src import inference_cache, loan_detail_coefficients
            frame = PRIVATE / "review_frame.pkl"
            inference_cache.main(["--data", str(data), "--output", str(frame)])
            stamp("inference frame built", t0)
            loan_detail_coefficients.main(["--frame", str(frame),
                                           "--output", str(OUT / "loan_detail_coefficients")])
            stamp("loan-detail fits done", t0)
        else:
            raise ValueError(JOB)
    finally:
        shutil.rmtree(PRIVATE, ignore_errors=True)
        shutil.rmtree(REPO, ignore_errors=True)
        stamp("private caches removed", t0)


if __name__ == "__main__":
    main()
