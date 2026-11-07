"""Execute the historical self-contained EDA notebook on private Kaggle compute.

The maintained modelling notebook now requires the repository and reviewed
benchmark bundle; execute it locally. This runner no longer executes the
retired self-contained modelling workflow.
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
for name in ("1_full_dataset_eda",):
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
