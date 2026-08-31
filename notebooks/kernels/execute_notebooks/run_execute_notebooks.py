"""Execute both analysis notebooks on Kaggle and keep the executed .ipynb.

Why this kernel exists: Kaggle's API returns only the LOG for a notebook
kernel's run - never the executed .ipynb with outputs - and the ~1-2 h
executions should not occupy a laptop. This script kernel re-executes the
two self-contained analysis notebooks (shipped in the private code
dataset's notebooks/ directory) with jupyter nbconvert and writes
1_full_dataset_eda_executed.ipynb and 2_full_dataset_modeling_executed.ipynb
to /kaggle/working, which IS retrievable via `kaggle kernels output`.
Those files feed the styled PDF renders (scratchpad render_notebook_pdfs.py).

The notebooks already resolve both mount-path layouts themselves
(/kaggle/input/kiva-loans-hackathon-data and
/kaggle/input/datasets/tuannm3812/...), so no path shimming is needed.
"""
import shutil
import subprocess
import sys
import time
from pathlib import Path

CODE_CANDIDATES = [
    Path("/kaggle/input/datasets/tuannm3812/kiva-hackathon-src"),
    Path("/kaggle/input/kiva-hackathon-src"),
]
WORK = Path("/kaggle/working")

code_root = next((p for p in CODE_CANDIDATES if p.exists()), None)
if code_root is None:
    raise FileNotFoundError(f"code dataset not mounted; tried {[str(c) for c in CODE_CANDIDATES]}")
nb_dir = code_root / "notebooks"
if not nb_dir.is_dir():
    raise FileNotFoundError(
        "notebooks/ missing from the code dataset - republish it with "
        "scripts/publish_kaggle_dataset.sh code version '...' (the publish "
        "script stages both analysis .ipynb files)"
    )

t0 = time.time()
for name in ("1_full_dataset_eda", "2_full_dataset_modeling"):
    src = nb_dir / f"{name}.ipynb"
    local = WORK / src.name
    shutil.copy2(src, local)
    out_name = f"{name}_executed"
    print(f"[{time.time() - t0:.0f}s] executing {src.name} ...", flush=True)
    subprocess.run(
        [sys.executable, "-m", "jupyter", "nbconvert",
         "--to", "notebook", "--execute", str(local),
         "--output", out_name, "--output-dir", str(WORK),
         "--ExecutePreprocessor.timeout=-1"],
        check=True,
    )
    local.unlink()  # keep only the executed copy in the output
    size = (WORK / f"{out_name}.ipynb").stat().st_size
    print(f"[{time.time() - t0:.0f}s] wrote {out_name}.ipynb ({size} bytes)", flush=True)
print(f"[{time.time() - t0:.0f}s] done:", sorted(p.name for p in WORK.iterdir()))
