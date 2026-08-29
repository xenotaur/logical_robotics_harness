---
execution_id: 2026_08_29_07_14_04_FIX_GATE_STALENESS_INSTALLED_TARGET_SELFREVIEW
prompt_id: PROMPT(AD_HOC:FIX_GATE_STALENESS_INSTALLED_TARGET_SELFREVIEW)[2026-08-29T07:13:59+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr:
commit:
created_at: 2026-08-29T07:14:04+00:00
agent: claude_app
instruction_source: WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT
session_transcript: claude-app:23a15fdd-6d6c-4d84-a7be-960a54769157
---

# Summary

`/lrh-self-review` diff-mode pass (Step 7.5 of `/lrh-implement`, inlined
via `/lrh-execute`) on the working-tree diff implementing
`WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT`, before the PR's first
push. Reviewed `git diff origin/main` (not `git diff main` -- this
worktree's local `main` ref was stale relative to `origin/main`, verified
via `git rev-parse main origin/main HEAD` before diffing, same pattern as
this session's earlier PR #639/#648 work).

# Result

Dispatched a cold `general-purpose` subagent with the diff and WI
orientation context. It reported 2 P2 findings and 2 P3 findings, no P1s.

Independently re-verified the top (P2) finding directly: the new
`test_unresolvable_target_fails_closed` fixture wrote a YAML key `target:`
(singular) into `project/agent_skills.yaml`, but
`installer._config_target` (`src/lrh/skills/installer.py:371`) only reads
the plural `targets:` key -- confirmed by reading the function directly.
The malformed key was silently ignored, so the test passed for the wrong
reason (via the "no persisted fingerprint" fail-closed branch, not the
`kind="unresolved"` branch it was meant to cover). Fixed: the fixture now
uses `targets: [not-a-valid-target]` (a genuinely invalid value under the
real key), and the test now asserts `"could not be resolved"` appears in
every stale reason, so it can no longer pass via the wrong branch. Re-ran
`tests/gate_staleness_test.py` after the fix: 26/26 pass, including this
one now genuinely exercising the `kind="unresolved"` dispatch path.

Second P2 (design/scope), accepted as-is, not fixed in this diff: the
WI's acceptance criteria describe the untracked-target fingerprint as
"persisted at consent-grant time," but no `skip_if_opted_in` consent-grant
call site exists anywhere in this repo yet (no `lrh chain-defaults
grant`/`confirm` CLI command -- consent today is a direct file edit per
the skill-level `chain-defaults.md` flow). `record_fingerprints` is new,
correct plumbing, but nothing calls it, so a real user-scope install will
always fail closed until a follow-up wires the call site in. This matches
the WI's own `artifacts_expected` scope (`gate_staleness.py` +
`tests/gate_staleness_test.py` only) and fail-closed is the safe default
in the interim, so left as a Follow-up rather than expanded in-scope.

Two P3 nits (a redundant `SkillSourceError` in an exception tuple already
covered by `ValueError`; the placeholder execution record's TODOs, which
this Step 9 record fills separately) -- not worth churning, noted and
accepted.

# Validation

- `python3 -m unittest tests.gate_staleness_test -v`: 26/26 pass (after
  the fixture fix)
- `scripts/format --check --diff`, `scripts/lint`: clean
- `lrh validate`: 0 errors (1 pre-existing, unrelated warning on the WI
  file's own frontmatter, not touched by this diff)

# Follow-up

- Wire `record_fingerprints` into the real `skip_if_opted_in`
  consent-grant call site once one exists in this repo (out of this WI's
  own stated scope) -- until then, every user-scope/untracked install
  correctly fails closed rather than silently passing.
- `/lrh-implement` Step 8 (commit + PR) proceeds next regardless of these
  findings, per this skill's Decision 4 -- no skip path exists.
