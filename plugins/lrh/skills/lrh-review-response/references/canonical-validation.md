# Canonical Validation Sequence

The standard validation sequence for LRH implementation work. Run these
commands at Step 5 (after all fixes are applied) and record the output as
evidence in the execution record body.

---

## Full sequence

```bash
scripts/version tools          # confirm tool versions
scripts/format --check --diff  # check formatting (does not modify files)
scripts/lint                   # run ruff and black formatting check
scripts/test                   # run the full test suite
lrh validate                   # check all control-plane files
```

Run in this order. Fix any failure before proceeding to the next command.
Do not push with failing validation.

---

## Command details and failure handling

### `scripts/version tools`

Prints installed versions of Black, Ruff, Pylint, Python, and other tools.
Record the versions in the execution record so reviewers can reproduce the run.
If a required tool is missing, the output says so — treat this as an
environment issue, not a code regression.

### `scripts/format --check --diff`

Checks that all Python files match Black's formatting. Exits non-zero if any
file would be changed. **Does not modify files.**

On failure: run `scripts/format` (without `--check`) to apply formatting,
then re-run `scripts/format --check --diff` to confirm clean.

### `scripts/lint`

Runs Ruff then checks formatting with Black. Exits non-zero on any lint error.

On failure: fix the flagged issues and re-run. Do not suppress rules without
understanding why they fired.

### `scripts/test`

Runs `python -m unittest discover -s tests -p '*_test.py'`. Exits non-zero
if any test fails.

On failure: fix the underlying issue. Review responses that break existing
tests indicate a regression introduced by the fix — investigate before pushing.

### `lrh validate`

Checks all control-plane files (work items, proposals, execution records,
workstreams). Run after any control-plane file change (including after creating
the execution record stub in Step 7).

On failure: the error message names the specific file and field. Fix, re-run.

---

## For skills work items, also run

```bash
scripts/test tests/packaging_tests/skills_mirror_sync_test.py
```

This is not needed for review response commits unless the fixes touch skill
files. If they do, regenerate the `.claude/`, `.agents/`, and `.gemini/`
install targets from the edited source. An edited skill differs from its
targets, and without `--force` the installer skips it with a "local
modifications" warning instead of regenerating it, so use the forced path.
Preview it first; the preview is read-only and shows every skill it would
overwrite:

```bash
lrh skills install --local --target all --source current-repo --force --diff
lrh skills install --local --target all --source current-repo --force
```

If the preview lists skills the fixes did not touch, regenerate only the
edited skills with the one-skill scratch-source recipe in CONTRIBUTING.md's
"Claude Code skills" section instead. Then verify all three targets still
match `src/lrh/skills/` with the test above.

---

## Evidence to record in the execution record body

In the `## Validation` section, include:

```
scripts/version tools  — Black X.Y.Z, Ruff X.Y.Z confirmed
scripts/format --check --diff  — N files unchanged
scripts/lint  — all checks passed
scripts/test  — N tests OK
lrh validate  — 0 errors, 0 warnings
```

If any check was skipped (e.g., no Python changes so format/lint/test are
not strictly required), note that explicitly rather than omitting the line.
