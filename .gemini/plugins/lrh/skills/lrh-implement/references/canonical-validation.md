# Canonical Validation Sequence

The standard validation sequence for LRH implementation work items. Run these
commands at Step 7 (validate) and record the output as evidence in the
execution record.

---

## Full sequence

```bash
scripts/version tools          # confirm tool versions
scripts/format --check --diff  # check formatting (does not modify files)
scripts/lint                   # run ruff and black formatting check
scripts/test                   # run the full test suite
```

Run in this order. Fix any failure before proceeding to the next command.

---

## Command details and failure handling

### `scripts/version tools`

Prints installed versions of Black, Ruff, Pylint, Python, and other tools
declared in the project. No failure mode — if a required tool is missing, the
output says so. Record the versions in the execution record so reviewers can
reproduce the run.

### `scripts/format --check --diff`

Checks that all Python files match Black's formatting. Exits non-zero if any
file would be changed. **Does not modify files.**

On failure: run `scripts/format` (without `--check`) to apply formatting,
then re-run `scripts/format --check --diff` to confirm clean before
continuing.

### `scripts/lint`

Runs Ruff (fast linter) and then checks formatting with Black. Exits non-zero
on any lint error.

On failure: fix the flagged issues, then re-run `scripts/lint`. Do not
suppress rules without understanding why they fired.

### `scripts/test`

Runs `python -m unittest discover -s tests -p '*_test.py'`. Exits non-zero
if any test fails.

On failure: fix the underlying issue — do not skip or mark tests as expected
failures unless the test itself is the bug and a separate work item is opened
for the fix.

---

## Item-specific additional checks

For skills work items, also run:

```bash
lrh validate
lrh skills check --target claude --local
lrh skills status --target codex --local
```

`lrh validate` checks all control-plane files (work items, proposals,
execution records, workstreams). Run it after any control-plane file change.

The skills checks confirm the canonical sources render cleanly for the selected
local targets. Claude installs preserve canonical bytes; Codex installs may
strip Claude-only frontmatter and add `agents/openai.yaml`, so Codex validation
should use `lrh skills status --target codex --local` rather than a raw byte
diff against `src/`.

---

## Evidence to record in the execution record

In the `## Validation` section of the execution record body, include:

- Tool versions from `scripts/version tools`
- Number of tests run and result (`Ran N tests ... OK`)
- Output of `lrh validate` (error/warning count)
- Output of the relevant `lrh skills` target checks for skill items

Example:

```
scripts/version tools  — Black 26.3.1, Ruff 0.15.12 confirmed
scripts/format --check --diff  — N files unchanged
scripts/lint  — all checks passed
scripts/test  — N tests OK
lrh validate  — 0 errors, 0 warnings
lrh skills check --target claude --local  — all installed skills up to date
lrh skills status --target codex --local  — all installed skills up to date
```
