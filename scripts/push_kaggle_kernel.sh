#!/usr/bin/env bash
# Push a notebook to its private Kaggle kernel.
#
# Copies the source notebook (the single source of truth, in notebooks/)
# into its kernel-metadata.json folder under notebooks/kernels/, then runs
# `kaggle kernels push`. The copied .ipynb is gitignored and regenerated
# every run, so notebooks/ never has two versions to keep in sync by hand.
#
# Usage: scripts/push_kaggle_kernel.sh <starter_eda|eda|modeling>
#
# All three kernels are private (see README.md's "Kaggle Workflow"
# section) - this is a hosted compute backend for the team, not a public
# notebook. After pushing, check status with:
#   kaggle kernels status <id-from-kernel-metadata.json>

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NOTEBOOKS_DIR="$REPO_ROOT/notebooks"

case "${1:-}" in
  starter_eda)
    NOTEBOOK="00_starter_eda.ipynb"
    KERNEL_DIR="$NOTEBOOKS_DIR/kernels/starter_eda"
    ;;
  eda)
    NOTEBOOK="01_full_dataset_eda.ipynb"
    KERNEL_DIR="$NOTEBOOKS_DIR/kernels/full_dataset_eda"
    ;;
  modeling)
    NOTEBOOK="02_full_dataset_modeling.ipynb"
    KERNEL_DIR="$NOTEBOOKS_DIR/kernels/full_dataset_modeling"
    ;;
  *)
    echo "Usage: $0 <starter_eda|eda|modeling>" >&2
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

cp "$NOTEBOOKS_DIR/$NOTEBOOK" "$KERNEL_DIR/$NOTEBOOK"
"$KAGGLE" kernels push -p "$KERNEL_DIR"
