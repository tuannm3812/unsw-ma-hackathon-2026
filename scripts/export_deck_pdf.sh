#!/usr/bin/env bash
# Render docs/presentation/slides_draft.pptx to PDF via Keynote (the one
# slide renderer on this machine). Run after every deck rebuild so the
# rendered result - real fonts, real layout - can be inspected page by
# page. Output: docs/presentation/slides_draft.pdf
# Note: Keynote's import is an approximation of PowerPoint's rendering;
# the submission-machine PowerPoint check still stands.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IN="${REPO_ROOT}/docs/presentation/slides_draft.pptx"
OUT="${REPO_ROOT}/docs/presentation/slides_draft.pdf"
rm -f "${OUT}"
open -ga Keynote
sleep 3
osascript - "$IN" "$OUT" << 'OSA'
on run argv
    set inPath to POSIX file (item 1 of argv)
    set outPath to POSIX file (item 2 of argv)
    with timeout of 600 seconds
        tell application "Keynote"
            activate
            set theDoc to open inPath
            delay 3
            export theDoc to outPath as PDF
            close theDoc saving no
        end tell
    end timeout
end run
OSA
ls -la "${OUT}"
