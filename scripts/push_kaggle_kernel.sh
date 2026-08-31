#!/usr/bin/env bash
# Push a notebook to its private Kaggle kernel.
#
# Copies the source notebook (the single source of truth, in notebooks/)
# into its kernel-metadata.json folder under notebooks/kernels/, then runs
# `kaggle kernels push`. The copied .ipynb is gitignored and regenerated
# every run, so notebooks/ never has two versions to keep in sync by hand.
#
# Usage: scripts/push_kaggle_kernel.sh <eda|modeling|pipeline>
#
# Only 1_full_dataset_eda and 2_full_dataset_modeling run on Kaggle -
# both are self-contained (standard public packages only: pandas,
# scikit-learn, statsmodels, nltk - no import of this repo's own src/
# package, deliberately; see README.md's "Kaggle Workflow" section). 0_starter_eda stays local-only:
# its whole purpose is to demonstrate the tested src/ pipeline runs
# correctly, so it inherently needs that package, and it runs in seconds
# on the 100-row sample anyway - it never needed Kaggle's compute.
#
# `pipeline` is different: a script kernel (notebooks/kernels/
# full_dataset_pipeline/run_full_pipeline.py) that runs the authoritative
# src/ pipeline on Kaggle's compute against the private data + code
# datasets (see scripts/publish_kaggle_dataset.sh) and writes
# reports/generated_full_dataset/'s two files to /kaggle/working. Retrieve
# them with `kaggle kernels output <id> -p <dir>` and copy into
# reports/generated_full_dataset/. Nothing is copied into that kernel
# folder - its script is committed as-is.
#
# All kernels are private - a hosted compute backend for the team, not
# public notebooks. After pushing, check status with:
#   kaggle kernels status <id-from-kernel-metadata.json>

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NOTEBOOKS_DIR="$REPO_ROOT/notebooks"

case "${1:-}" in
  eda)
    NOTEBOOK="1_full_dataset_eda.ipynb"
    KERNEL_DIR="$NOTEBOOKS_DIR/kernels/full_dataset_eda"
    ;;
  modeling)
    NOTEBOOK="2_full_dataset_modeling.ipynb"
    KERNEL_DIR="$NOTEBOOKS_DIR/kernels/full_dataset_modeling"
    ;;
  pipeline)
    NOTEBOOK=""
    KERNEL_DIR="$NOTEBOOKS_DIR/kernels/full_dataset_pipeline"
    ;;
  *)
    echo "Usage: $0 <eda|modeling|pipeline>" >&2
    exit 1
    ;;
esac

if command -v kaggle >/dev/null 2>&1; then
  KAGGLE=kaggle
elif [ -x "/Users/tuannm3812/.local/bin/kaggle" ]; then
  KAGGLE="/Users/tuannm3812/.local/bin/kaggle"
else
  echo "kaggle CLI not found on PATH or at the known local install path." >&2
  exit 1
fi

if [ -n "$NOTEBOOK" ]; then
  cp "$NOTEBOOKS_DIR/$NOTEBOOK" "$KERNEL_DIR/$NOTEBOOK"
fi
"$KAGGLE" kernels push -p "$KERNEL_DIR"
