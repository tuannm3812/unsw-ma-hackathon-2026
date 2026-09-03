# Coding Standards

## Baseline

This project follows the shared `coding-standards/coding_standards.md` at
the GitHub root (`/Users/tuannm3812/Documents/GitHub/coding-standards`) as
its baseline. That file is the fallback for anything not overridden below.
Everything here is either a project-specific addition or an explicit,
reasoned override of the shared baseline - this project predates the
shared standard (it grew out of a 10-task, Codex-reviewed engagement
before the finalist round), so several conventions were already
established in practice before this doc existed; this file records what's
actually true, not a retroactive rewrite of working history.

## Repository Scope

**Deviates from the baseline's notebook-first default.** This is not a
Kaggle competition project - it's a research/analytics submission with a
tested, leakage-safe pipeline as its authoritative artifact:

- `src/` - the tested, CLI-driven pipeline (`python3 -m src.run_analysis`).
  This is the project's actual source of truth for any number that goes
  into the proposal or the final slides, not a "shared logic reused across
  notebooks" convenience module. It exists because the analysis itself
  (chronological validation, HC3 robust inference, an explicit predictor
  allowlist, leakage guards) is complex enough to need real test coverage,
  not because notebooks needed a helper.
- `tests/` - 95 tests covering `src/` against synthetic fixtures (never
  the real dataset - see Git Hygiene) plus notebook/README contract checks.
- `notebooks/` - `0_starter_eda` (local pipeline demonstration, imports
  `src/`) and `1_full_dataset_eda`/`2_full_dataset_modeling` (self-contained
  Kaggle kernels, no `src/` import - see Kaggle Workflow in README.md and
  Notebook Naming below).
- `docs/superpowers/` - plans, specs, and the collaboration log (see
  Document Naming below).
- `proposal/`, `reports/`, `data/` - the submitted proposal, committed
  result snapshots, and gitignored raw data respectively; all documented
  in their own `README.md`s.

## Document Naming

**Deviates from the baseline's numbered `docs/0_..., 1_..., ...` scheme.**
This project uses `docs/superpowers/{plans,specs,collab-logs}/` instead -
an established convention from the Superpowers skill workflow this project
was built with, already containing a full, reviewed history (10 tasks,
multiple Codex rounds each) before this coding-standards doc was written.
Renaming/restructuring that history now would cost real effort for no
reader benefit this close to the 2026-09-03 deadline. This file
(`docs/0_coding_standards.md`) is the one exception, added to match the
baseline's expected filename so it's where a future contributor - or a
fresh Claude/Codex session - looks for it first.

## Notebook Naming

`0_starter_eda`, `1_full_dataset_eda`, `2_full_dataset_modeling` -
single-digit, not zero-padded. **This is a deliberate override** of the
baseline's zero-padded example (`01_eda.ipynb`, `02_...`): the user
explicitly requested single-digit numbering over zero-padding for this
project. Otherwise the baseline's naming rules hold: numbers are reserved
for promoted, project-owned workflows (not parameter variants), and names
describe the actual workflow, not just a step.

## Python Style

Follows the baseline's PEP 8 / type-hint requirements throughout `src/`.
**One deliberate deviation**: docstrings on `src/`'s internal helpers are
prose explaining *why* (a non-obvious constraint, a caveat about a
caller's assumptions, a decision and its alternative) rather than the
baseline's Google-style `Args:`/`Returns:` template - matching this
project's own governing instruction that comments/docstrings should carry
non-obvious reasoning, not restate a signature the type hints already
make clear. Google-style `Args:`/`Returns:` remains the right choice for a
function whose *parameters themselves* need explaining (units, valid
ranges, shape) rather than its rationale - use judgment per function
rather than one template for all of `src/`.

## Notebook Style

`1_full_dataset_eda.ipynb`/`2_full_dataset_modeling.ipynb` already follow
the baseline's checklist: a config block near the top (`DATA_PATH`
resolution, `HOLDOUT_START`), deterministic seeding (`random_state=42`
throughout), platform path auto-detection (no hardcoded username - see the
"Dynamic File Path Resolution" note below for the one place this differs
from the baseline's literal recommendation), Markdown insight cells after
every printed table/plot (added this round - see the collab log's
finalist-round entry), numbered `##` sections, and a closing "Key
takeaways for the deck" section. `0_starter_eda.ipynb` is lighter-weight
by design - it's a pipeline demonstration on a 100-row sample, not a
findings notebook, so it skips insight cells and a takeaways section in
favor of just proving `src/` runs end-to-end.

**Outputs policy** (matches `kaggle-rsna-knee-abnormality-detection`'s
exact policy, now enforced by
`tests/test_notebook_contract.py::test_kaggle_notebook_committed_copy_stays_output_free`):
`1_full_dataset_eda.ipynb`/`2_full_dataset_modeling.ipynb` stay
output-free in the repository, always - a trusted Kaggle run's real
numbers get transcribed into the notebook's own Markdown insight cells
(verified against the run's log, not from memory - see the collab log),
never left as stored cell output. This avoids baking a Kaggle container's
absolute paths or a since-superseded run's numbers into git history every
time the notebook is edited and re-pushed. `0_starter_eda.ipynb` is the
opposite by design: it's re-executed for real after every edit (13/13
cells, local, seconds) and keeps its genuine output, because "does the
tested pipeline actually run" is the thing it exists to prove.

**Offline-safety - deliberate override.** The baseline says final/
submission notebooks shouldn't depend on internet access. Both Kaggle
notebooks here run with `enable_internet: true`, but scoped to exactly
two one-time fetches: `nltk.download("vader_lexicon")` (guarded by a
`LookupError` check, so it's a no-op once cached) and a `pip install shap`
fallback for the rare environment where Kaggle's stock image doesn't
already have it. No other network access happens. This is acceptable here
because these are **private compute-backend kernels for a team, not a
Code Competition submission** re-executed against a hidden test set - the
baseline's reasoning (reproducibility under someone else's re-run) doesn't
apply the same way to a kernel only this team ever runs.

## Feature Engineering & Leakage Prevention

Exceeds the baseline here rather than deviating from it - see
`README.md`'s "Chronological Validation and Leakage Protections" section
for the full detail: chronological (not random) train/holdout split
shared by all three models, an explicit predictor **allowlist** (not a
blocklist), fit-on-train-only transforms, and a dedicated
`InsufficientDataError` so a too-small split degrades to a labeled
diagnostic instead of a misleading number.

## Plot Style

Viridis, per the baseline - applied this round to every plot in
`1_full_dataset_eda.ipynb` (`sns.set_theme(..., palette="viridis")` plus
explicit `plt.cm.viridis(...)` sampling for the two single-series
histograms and the period bar chart) and `2_full_dataset_modeling.ipynb`'s
SHAP importance chart. Verified with a local smoke test against the
100-row sample and a visual check of the rendered PNGs before committing -
a pure color-parameter change doesn't need a fresh ~20-minute Kaggle round
to trust, unlike a logic change.

## Documentation Style

Already matches the baseline's intent: `README.md` carries the broad
narrative (status, getting started, results, limitations) and
`docs/superpowers/` carries the detailed evidence trail (design specs,
plans, the full collaboration log) - see Document Naming above for why
the detail lives there instead of numbered `docs/` files. Facts that can
change (the 2026-09-03 5pm Sydney deadline, judging-criteria weights) are
timestamped or dated at the point they're recorded.

## Git Hygiene

Already compliant: `data/*.pkl` and the Kaggle notebooks' regenerated
kernel copies (`notebooks/kernels/*/*.ipynb`) are gitignored; no
credentials, checkpoints, or generated artifacts are committed. `reports/
generated_full_dataset/` is a deliberate exception - see `reports/
README.md`'s own stated policy for committing a specific, labeled
snapshot of a trusted run.

## Commit Message Convention

**Adopting `type(scope): summary` going forward.** Existing history
mostly uses `type: summary` (no parenthesized scope, e.g. `fix: correct
overclaims...`) - close to the baseline's Conventional Commits format but
not identical. Not rewriting history for this; new commits from this
point should include a scope (`docs(notebooks): ...`,
`test(contract): ...`) per the baseline.

## Pre-Commit / Pre-Push Workflow

Exceeds the baseline's checklist in practice: every notebook or `src/`
change in this project's history has been verified with fresh command
output before being reported as done (full local test suite, and for the
Kaggle notebooks specifically, a real `kaggle kernels status` /
`kaggle kernels output` round-trip confirming the pushed kernel actually
completed and printed the claimed numbers - not just that it uploaded).
Continue that practice: proportional verification per §10 of the baseline
means a pure-markdown or pure-color change gets a local smoke test, and a
logic change to a Kaggle notebook gets a real Kaggle re-run before its
numbers are trusted.

## Kaggle Private Deployment Standards

Checked against the baseline's §12 checklist:

- **Pre-upload validation gate**: `tests/test_notebook_contract.py` scans
  for absolute paths and (for `0_starter_eda`) borrower-identifying
  columns before anything is pushed; extended this round to cover
  `1_full_dataset_eda.py`/`2_full_dataset_modeling.py`'s source and both
  notebooks' committed (output-free) copies.
- **Dynamic file path resolution - a deliberate, documented deviation.**
  The baseline recommends `os.walk`/`rglob`-based discovery over a
  hardcoded mount path, precisely to avoid guessing wrong about how
  Kaggle mounts a dataset. This project's notebooks use a fixed
  two-candidate check (`/kaggle/input/datasets/tuannm3812/kiva-loans-
  hackathon-data`, falling back to `/kaggle/input/kiva-loans-hackathon-
  data`) instead. That's not an oversight: the real mount path was already
  empirically diagnosed via a dedicated diagnostic kernel earlier in the
  Kaggle migration (`os.walk('/kaggle/input')` run for real, not assumed -
  see the collab log's finalist-round entry), and the fixed check has
  since been re-confirmed working across four consecutive real Kaggle
  runs. A dynamic search would add complexity this project doesn't
  currently need, and risks silently resolving to an unintended dataset
  if a second one is ever attached to these kernels - a real, if unlikely,
  failure mode the fixed check doesn't have.
- **Kernel metadata**: handled by `jupytext`'s notebook generation: every
  push includes a standard `kernelspec`/`language_info`, confirmed by four
  successful real Kaggle runs.
- **Plot/warning compatibility**: not currently a live issue - nothing in
  either notebook uses a matplotlib API with known recent deprecations.
  Revisit if a future Kaggle image bump introduces a warning.
- **Visibility and collaborators**: both kernels are `is_private: true`,
  CPU-only (`enable_gpu: false` - nothing in either pipeline benefits from
  a GPU), and have no collaborators added.

## Kaggle Submission Method

Not applicable - this project has no competition leaderboard or submission
step. The Kaggle kernels here are a private compute backend for the team
(see README's "Kaggle Workflow"), not a scored entry.

---

## Numbered reference docs

Top-level documents in `docs/` are numbered so the reading order is explicit:

- `0_coding_standards.md` — this file: conventions the code follows.
- `1_data_dictionary.md` — every raw field: official definition, real coverage,
  and how this project used it (generated by `scripts/build_data_dictionary.py`).

Sub-directories keep their own naming: `docs/presentation/` (deck brief, Q&A pack,
slide mirror, chart and asset READMEs), `docs/pdf/` (rendered review PDFs), and
`docs/superpowers/` (plans, specs, and the external-review collaboration log).
