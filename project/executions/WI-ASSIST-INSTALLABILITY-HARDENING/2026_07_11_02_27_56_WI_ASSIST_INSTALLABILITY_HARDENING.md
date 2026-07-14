---
execution_id: 2026_07_11_02_27_56_WI_ASSIST_INSTALLABILITY_HARDENING
prompt_id: PROMPT(WI-ASSIST-INSTALLABILITY-HARDENING:WI_ASSIST_INSTALLABILITY_HARDENING)[2026-07-10T19:56:18-04:00]
work_item: WI-ASSIST-INSTALLABILITY-HARDENING
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/387
commit: fd5d71b73642255b916bff0e886c8f2c442a80c1
agent: claude_app
instruction_source: project/work_items/proposed/WI-ASSIST-INSTALLABILITY-HARDENING.md
session_transcript: claude-app:fe9f132a-5c11-42e9-b404-36562a7b88ce
created_at: 2026-07-11T02:27:56-04:00
---

# Summary

Closed out `WI-ASSIST-INSTALLABILITY-HARDENING`: extended `scripts/release-smoke`
with real (non-`--help`) installed-wheel invocations proving package-resource
template resolution actually works, and filled in the WI's missing
Scope/Required Changes/Validation sections.

# Result

Investigated the WI's premise before implementing anything. Acceptance
criterion 1 ("template loading uses package resources rather than
source-tree-relative paths") was already fully satisfied by the
already-resolved `WI-ASSIST-TEMPLATES-PACKAGING`:
`src/lrh/assist/template_resolver.py`, `src/lrh/assist/request_templates.py`,
and `src/lrh/project/bootstrap.py` all already use `importlib.resources`, and
`pyproject.toml`'s `[tool.setuptools.package-data]` already declares the
assist/project-bootstrap/skills template directories as package data. No
source-tree-relative template path construction remained anywhere in `src/lrh`.

The real remaining gap was acceptance criterion 2: `scripts/release-smoke`
only ran `--help` for `lrh request`/`lrh snapshot`, which proves argparse
wiring but never exercises real template rendering from an installed wheel.
Fixed by:

- Adding `lrh request templates list` (run with `cwd` pinned to an isolated,
  override-free directory, since that subcommand discovers `project_root` by
  walking up from cwd rather than via a flag) and a new
  `_check_template_sources_are_package` helper that fails the smoke test if
  any resolved template does not report `source: package`.
- Adding `lrh project init --profile minimal --project-root <tmp>` followed
  by `lrh snapshot project --project-root <tmp> --stdout` as a real
  end-to-end sequence, exercising bootstrap-template package-resource
  loading (previously had zero real-invocation coverage anywhere).
- Updating `docs/how-to/run-a-release.md`'s smoke-test section to document
  this.

While validating, found and fixed an unrelated pre-existing bug:
`tests/dev_tests/` had no `__init__.py`, so `unittest discover -s tests -p
"*_test.py"` silently skipped the entire directory — 44 tests (all of
`release_smoke_test.py` and `versioning_test.py`) never actually ran under
`scripts/test`/CI. Added `tests/dev_tests/__init__.py`. Three more
directories (`integrations_tests`, `packaging_tests`, `work_items_tests`,
~40 more tests) have the same issue; flagged as a separate follow-up task
(spawned in-session) rather than bundled into this PR to keep scope narrow.

# Validation

- `scripts/version tools` — lrh 0.2.5.dev83+g40da6c798, ruff 0.15.12, black 26.3.1, Python 3.11.8
- `scripts/format --check --diff` — clean, 175 files unchanged
- `scripts/lint` — clean (ruff + black)
- `PYTHONPATH="$(pwd)/src" scripts/test` — 742 tests (698 + 44 newly-discovered
  via the `__init__.py` fix), 0 failures. Note: `PYTHONPATH` override was
  required in this worktree session because the active conda env's editable
  `lrh` install resolves to the main repo checkout path, not the worktree —
  without it, `scripts/test` silently validates stale code.
- `lrh validate` — 0 errors, 0 warnings
- `PYTHONPATH="$(pwd)/src" scripts/release-smoke` — full real run (build,
  wheel install, invocations, no mocks), exit 0. Confirmed via captured
  output that `lrh request templates list` reported `source: package` for
  every template when run from the installed wheel.

# Follow-up

- Once PR #387 merges, set `status: landed` and populate `commit:` with the
  merge SHA.
- `session_transcript` should be updated from `pending` to
  `claude-app:<session-id>` after this session ends.
- Separate follow-up task spawned in-session: add `__init__.py` to
  `tests/integrations_tests/`, `tests/packaging_tests/`, and
  `tests/work_items_tests/` (~40 more silently-skipped tests), verify they
  pass, and fix any real failures found.
