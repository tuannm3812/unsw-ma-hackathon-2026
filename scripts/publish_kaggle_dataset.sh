#!/usr/bin/env bash
# Publish this project's private Kaggle Dataset (compute backend, not
# public distribution - see README.md's "Kaggle Workflow" section):
# data/Kiva_Loans.pkl, data/Kiva_Loans_Sample.pkl, and the data
# dictionary - the raw inputs the Kaggle notebooks read from
# /kaggle/input/kiva-loans-hackathon-data/.
#
# There is deliberately no matching "code" dataset: the Kaggle notebooks
# (notebooks/1_full_dataset_eda.ipynb, 2_full_dataset_modeling.ipynb) are
# self-contained, using only standard public packages (pandas,
# scikit-learn, statsmodels, nltk) - not this repo's own src/ package -
# so there is no private code to publish or keep in sync here.
#
# Usage: scripts/publish_kaggle_dataset.sh <create|version> ["message"]
#
# `create` only works once (Kaggle rejects a second `create` on an id
# that already exists) - use `version` for every update after that.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <create|version> [\"version message\"]" >&2
  exit 1
fi

ACTION="$1"
MESSAGE="${2:-Update data dataset}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE_DIR="$(mktemp -d)"
trap 'rm -rf "${STAGE_DIR}"' EXIT

if command -v kaggle >/dev/null 2>&1; then
  KAGGLE=kaggle
elif [ -x "/Users/tuannm3812/.local/bin/kaggle" ]; then
  KAGGLE="/Users/tuannm3812/.local/bin/kaggle"
else
  echo "kaggle CLI not found on PATH or at the known local install path." >&2
  exit 1
fi

cp "${REPO_ROOT}/data/Kiva_Loans.pkl" "${STAGE_DIR}/"
cp "${REPO_ROOT}/data/Kiva_Loans_Sample.pkl" "${STAGE_DIR}/"
cp "${REPO_ROOT}/data/Kiva Data Dictionary.xlsx" "${STAGE_DIR}/"
cat > "${STAGE_DIR}/dataset-metadata.json" << 'EOF'
{
  "title": "Kiva Loans - MA Hackathon 2026 Data",
  "id": "tuannm3812/kiva-loans-hackathon-data",
  "licenses": [{"name": "unknown"}]
}
EOF

case "${ACTION}" in
  create)
    "${KAGGLE}" datasets create -p "${STAGE_DIR}" --dir-mode zip
    ;;
  version)
    "${KAGGLE}" datasets version -p "${STAGE_DIR}" --dir-mode zip -m "${MESSAGE}"
    ;;
  *)
    echo "Unknown action: ${ACTION} (expected create|version)" >&2
    exit 1
    ;;
esac
