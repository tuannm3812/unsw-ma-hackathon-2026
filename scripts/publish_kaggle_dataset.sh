#!/usr/bin/env bash
# Publish this project's private Kaggle Datasets (compute backend, not
# public distribution - see README.md's "Kaggle Workflow" section).
#
# "data": data/Kiva_Loans.pkl, data/Kiva_Loans_Sample.pkl, and the data
#   dictionary - the raw inputs Kaggle kernels read from
#   /kaggle/input/kiva-loans-hackathon-data/.
# "code": src/, requirements.txt, and resources/nltk_data/ (the vendored
#   VADER lexicon - required since kernels run with enable_internet=false)
#   - lets a kernel `sys.path.insert(0, "/kaggle/input/kiva-hackathon-src/src")`
#   and import the real pipeline instead of reimplementing any of it
#   inline, mirroring ../2. Kaggle/kaggle-rsna-knee-abnormality-detection's
#   scripts/publish_code_dataset.sh pattern.
#
# Usage: scripts/publish_kaggle_dataset.sh <data|code> <create|version> ["message"]
#
# `create` only works once per dataset id (Kaggle rejects a second
# `create` on an id that already exists) - use `version` for every update
# after the first successful `create`.

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <data|code> <create|version> [\"version message\"]" >&2
  exit 1
fi

TARGET="$1"
ACTION="$2"
MESSAGE="${3:-Update ${TARGET} dataset}"

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

case "${TARGET}" in
  data)
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
    ;;
  code)
    cp -R "${REPO_ROOT}/src" "${STAGE_DIR}/src"
    cp -R "${REPO_ROOT}/resources" "${STAGE_DIR}/resources"
    cp "${REPO_ROOT}/requirements.txt" "${STAGE_DIR}/requirements.txt"
    find "${STAGE_DIR}/src" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    cat > "${STAGE_DIR}/dataset-metadata.json" << 'EOF'
{
  "title": "Kiva Hackathon - Source Pipeline",
  "id": "tuannm3812/kiva-hackathon-src",
  "licenses": [{"name": "MIT"}]
}
EOF
    ;;
  *)
    echo "Unknown target: ${TARGET} (expected data|code)" >&2
    exit 1
    ;;
esac

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
