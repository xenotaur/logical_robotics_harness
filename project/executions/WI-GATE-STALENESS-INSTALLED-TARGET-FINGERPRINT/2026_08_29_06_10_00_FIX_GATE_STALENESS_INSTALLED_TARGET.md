---
execution_id: 2026_08_29_06_10_00_FIX_GATE_STALENESS_INSTALLED_TARGET
prompt_id: PROMPT(WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT:FIX_GATE_STALENESS_INSTALLED_TARGET)[2026-08-29T06:09:39+00:00]
work_item: WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/649
commit: cf41c76686a4992bfeebb819aca93dd83e2b8570
created_at: 2026-08-29T06:10:00+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT.md
session_transcript: claude-app:23a15fdd-6d6c-4d84-a7be-960a54769157
---

# Summary

Implements `WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT`: fixes
`src/lrh/gate_staleness.py`'s installed-client-repo false negative, where
every hardcoded `src/lrh/skills/...` watch path was absent at both
commits in a client repo with no such tree, and the check silently
reported `stale=False` unconditionally.

# Result

- `resolve_watch_targets(project_root)`: preserves the harness repo's own
  self-check unchanged when `src/lrh/skills/` exists; otherwise resolves
  the actually-installed skill target via `lrh.skills.installer`'s own
  target-resolution logic and classifies each gate-bearing skill as
  `"git"` (inside `project_root`'s working tree -- reuses the existing
  marker-scoped `git show`-based comparison), `"fingerprint"` (outside it,
  e.g. the default user-scope `~/.claude/skills/` install -- compared
  against a persisted SHA-256 content fingerprint instead), or
  `"unresolved"` (target can't be resolved).
- `record_fingerprints`/`load_fingerprints`: compute and persist/read
  content fingerprints, stored at
  `project/config/chain-defaults-fingerprints.json`.
- Every new failure/absence path fails closed (`stale=True`) --
  unresolvable target, missing/unreadable fingerprint, or a
  resolved-but-missing installed file never silently reports
  `stale=False`. Distinguished from the pre-existing harness self-check's
  own "absent at both commits" branch, which is unchanged and correctly
  stays `stale=False` there (a path genuinely never tracked in this
  repo's own history is not part of that check).
- 6 new unit tests (`ResolveWatchTargetsInstalledTargetTest`): project-
  local git-tracked target detects/doesn't-falsely-detect staleness;
  untracked target missing/matching/changed fingerprint; unresolvable
  target fails closed on every canonical skill. Fixtures deliberately do
  not commit the installed path for the untracked case, per the WI's own
  requirement.
- `/lrh-self-review` diff-mode pass (Step 7.5) before this PR's first
  push: caught and fixed a genuine bug in the "unresolvable target" test
  fixture (wrote the wrong YAML key, so it was passing for the wrong
  reason). See
  `project/executions/AD_HOC/2026_08_29_07_14_04_FIX_GATE_STALENESS_INSTALLED_TARGET_SELFREVIEW.md`.

# Validation

- `python3 -m unittest tests.gate_staleness_test tests.chain_defaults_status_test -v`: 36/36 pass
- `scripts/test` (full canonical suite): 1488/1488 pass
- `scripts/lint`, `scripts/format --check --diff`: clean
- `lrh validate`: 0 errors (1 pre-existing, unrelated warning on the WI
  file's own frontmatter)

# Follow-up

- `record_fingerprints` is new plumbing but nothing yet calls it at
  `skip_if_opted_in` consent-grant time -- no `lrh chain-defaults
  grant`/`confirm` CLI command exists in this repo yet. Until that wiring
  lands (out of this WI's own stated scope), a real user-scope install
  will always fail closed, which is safe but not yet the full end-to-end
  behavior the WI's acceptance criteria describe.
