#!/usr/bin/env bash
# Publish this project's private Kaggle Datasets (compute backend, not
# public distribution - see README.md's "Kaggle Workflow" section).
#
#   data  data/Kiva_Loans.pkl, data/Kiva_Loans_Sample.pkl and the data
#         dictionary - the raw inputs every Kaggle kernel reads from
#         /kaggle/input/kiva-loans-hackathon-data/.
#   code  this repo's src/ package, resources/nltk_data/ (the vendored
#         VADER lexicon) and the requirements files, so the authoritative
#         pipeline itself can run on Kaggle's compute via
#         notebooks/kernels/full_dataset_pipeline/ - the ~2 h regeneration
#         of reports/generated_full_dataset/ no longer needs a laptop.
#         The two analysis notebooks stay self-contained (public packages
#         only) and do not use this dataset.
#
# Usage: scripts/publish_kaggle_dataset.sh <data|code> <create|version> ["message"]
#
# `create` only works once per id (Kaggle rejects a second `create`) -
# use `version` for every update after that. Re-publish `code` after any
# src/ change you want the Kaggle pipeline run to pick up.

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
    # The directory layout must survive the round trip: src/features.py
    # locates the vendored lexicon at ../resources/nltk_data relative to
    # its own file. `--dir-mode zip` uploads each directory as a zip, and
    # Kaggle does not reliably auto-extract those at mount time, so the
    # runner kernel rebuilds src/ and resources/ as siblings itself (see
    # notebooks/kernels/full_dataset_pipeline/run_full_pipeline.py).
    rsync -a --exclude '__pycache__' "${REPO_ROOT}/src" "${STAGE_DIR}/"
    rsync -a "${REPO_ROOT}/resources" "${STAGE_DIR}/"
    cp "${REPO_ROOT}/requirements.txt" "${REPO_ROOT}/requirements-lock.txt" "${STAGE_DIR}/"
    # The two analysis notebooks ride along so the execute_notebooks kernel
    # can re-execute them on Kaggle and expose the executed .ipynb files
    # (with outputs) as downloadable kernel output - the Kaggle API never
    # returns a notebook kernel's own executed notebook.
    mkdir -p "${STAGE_DIR}/notebooks"
    cp "${REPO_ROOT}/notebooks/1_full_dataset_eda.ipynb" \
       "${REPO_ROOT}/notebooks/2_full_dataset_modeling.ipynb" "${STAGE_DIR}/notebooks/"
    # Immutable provenance for any snapshot later generated from this
    # upload: the git commit (plus a dirty flag - an upload from an
    # uncommitted tree is recorded as exactly that) and a content hash of
    # the staged src/ tree. The Kaggle runner refuses to run without this
    # file, re-hashes what it actually mounted, and copies the record into
    # its output so a committed reports/ snapshot names the code that
    # produced it (Codex review: bind snapshots to immutable provenance).
    GIT_COMMIT="$(git -C "${REPO_ROOT}" rev-parse HEAD)"
    GIT_DIRTY="$(git -C "${REPO_ROOT}" status --porcelain -- src resources requirements.txt requirements-lock.txt | head -c1)"
    SRC_SHA="$(cd "${STAGE_DIR}" && find src -type f | LC_ALL=C sort | xargs shasum -a 256 | shasum -a 256 | cut -d' ' -f1)"
    cat > "${STAGE_DIR}/PROVENANCE.json" << EOF2
{
  "git_commit": "${GIT_COMMIT}",
  "git_tree_dirty": $([ -n "${GIT_DIRTY}" ] && echo true || echo false),
  "src_tree_sha256": "${SRC_SHA}",
  "published_at_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "publish_message": "${MESSAGE}"
}
EOF2
    cat > "${STAGE_DIR}/dataset-metadata.json" << 'EOF'
{
  "title": "Kiva Hackathon - Source Pipeline",
  "id": "tuannm3812/kiva-hackathon-src",
  "licenses": [{"name": "unknown"}]
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
