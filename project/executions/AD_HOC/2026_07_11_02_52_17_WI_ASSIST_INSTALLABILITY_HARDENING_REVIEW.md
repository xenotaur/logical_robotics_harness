---
execution_id: 2026_07_11_02_52_17_WI_ASSIST_INSTALLABILITY_HARDENING_REVIEW
prompt_id: PROMPT(AD_HOC:WI_ASSIST_INSTALLABILITY_HARDENING_REVIEW)[2026-07-11T02:44:04-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_07_11_02_27_56_WI_ASSIST_INSTALLABILITY_HARDENING
pr: https://github.com/xenotaur/logical_robotics_harness/pull/387
commit: a5d18f02f669abba8a724aa13cff5d18d4b10ec4
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/387
session_transcript: pending
created_at: 2026-07-11T02:52:17-04:00
---

# Summary

Addressed one review comment on PR #387: the new `_check_template_sources_are_package`
smoke check pinned `cwd` but not environment, so a maintainer's local
`LRH_TEMPLATE_DIR`/`XDG_CONFIG_HOME` overrides could produce a false smoke
failure.

# Result

**Comment 1** (`#discussion_r3563447173`, P2, `chatgpt-codex-connector`) —
Confirmed valid: `TemplateResolver._filesystem_sources()` consults
`LRH_TEMPLATE_DIR` and the `XDG_CONFIG_HOME`/`HOME`-derived user template
directory in addition to project-root overrides, and
`_venv_command_environment()` only strips `PYTHONPATH`, not those. Pinning
`cwd` alone was insufficient. Fixed by adding a new
`_override_free_environment` helper (strips `LRH_TEMPLATE_DIR`/
`XDG_CONFIG_HOME`, overrides `HOME` to the isolated `template-list-cwd`
directory) and wiring it into the `lrh request templates list` invocation in
`src/lrh/dev/release_smoke.py`.

While validating the fix, found and fixed a real pre-existing test-harness
bug it exposed: in `tests/dev_tests/release_smoke_test.py`'s comprehensive
test, the `_run_twine_check` mock's `side_effect` appended to the `commands`
list but never to the parallel `command_envs` list, silently desynchronizing
the two by one element. This never surfaced before because every earlier
`_run` call shared the identical `venv_command_env` object, so the resulting
off-by-one `command_envs` lookups happened to still satisfy the (trivial)
existing assertions. My new environment-specific assertion was the first one
precise enough to expose it. Fixed by making the twine-check fake append to
both lists in lockstep.

# Validation

- `git rev-parse HEAD` — `f1288d5fc89215e868a0090ccd44057ba71fbdcb` (before this fix)
- `scripts/format --check --diff` — clean, 176 files unchanged
- `scripts/lint` — clean (ruff + black)
- `PYTHONPATH="$(pwd)/src" scripts/test` — 744 tests (742 + 2 new:
  `_override_free_environment` accept/no-mutate cases), 0 failures
- `lrh validate` — 0 errors, 0 warnings
- `LRH_TEMPLATE_DIR=/tmp/fake-maintainer-overrides PYTHONPATH="$(pwd)/src"
  scripts/release-smoke` — real, unmocked run reproducing the reviewer's
  exact scenario (a maintainer-local override env var set); exit 0, all
  templates still resolved with `source: package` from the installed wheel,
  confirming the fix.

# Follow-up

- Once PR #387 merges, set `status: landed` and populate `commit:` with the
  merge SHA.
- `session_transcript` should be updated from `pending` to
  `claude-app:<session-id>` after this session ends.
