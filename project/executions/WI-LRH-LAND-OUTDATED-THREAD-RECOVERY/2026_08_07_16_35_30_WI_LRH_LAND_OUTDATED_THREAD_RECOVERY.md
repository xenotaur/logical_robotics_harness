---
execution_id: 2026_08_07_16_35_30_WI_LRH_LAND_OUTDATED_THREAD_RECOVERY
prompt_id: PROMPT(WI-LRH-LAND-OUTDATED-THREAD-RECOVERY:WI_LRH_LAND_OUTDATED_THREAD_RECOVERY)[2026-08-07T16:27:48+00:00]
work_item: WI-LRH-LAND-OUTDATED-THREAD-RECOVERY
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/511
commit: ffabbe901c1bcae5321d2e14983ff6c0371d53d8
created_at: 2026-08-07T16:35:30+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-LAND-OUTDATED-THREAD-RECOVERY.md
session_transcript: claude-app:61881211-bfd7-40cb-8080-33938a265398
---

# Summary

Implement `WI-LRH-LAND-OUTDATED-THREAD-RECOVERY`: port the governed
three-way-gated (fix now / defer / stop) outdated-thread recovery path
from `PROP-OUTDATED-THREAD-RECOVERY` into `/lrh-land` Step 5, built on
`WI-REVIEW-RESPONSE-INCLUDE-THREAD`'s `--include-thread` flag
(`WI-REVIEW-RESPONSE-INCLUDE-THREAD`, PR #497). Replaces PR #453's
reverted prose-only attempt at the same mechanism.

# Result

Edited `src/lrh/skills/lrh-land/SKILL.md` and its `.claude/` mirror:
Step 5 gained an "Exception" section with a stop-work-condition
precondition check ahead of the gate, hard bucket-scoping
(Unaddressed/Partial/Problematic resolution only — Ambiguous and
Problematic comment explicitly excluded), the `--include-thread <id>`
propagation into `/lrh-review-response`'s own Step 2 fetch command, a
"fix now" loop-back through `/lrh-confirm-fixes` for a fresh verdict,
and a "defer" path that is an explicit, named-thread-scoped override
recorded in Step 6's summary without weakening any other required-green
check. Step 4 now cross-references the new Step 5 path. Edited
`src/lrh/skills/lrh-review-response/SKILL.md` and its `.claude/` mirror:
Step 3 gained a same-`/lrh-land`-run continuation carve-out so the
recovery path's loop-back doesn't trip the idempotence check.

**Process note:** this implementation initially began without going
through `/lrh-implement`'s own Step 3 (mint + idempotence check) or
Step 4 (confirm-plan gate), and on the wrong (stale, prior-WI) branch.
Caught before anything was committed or pushed. The uncommitted diff
was saved, the working tree reset, a correct branch created fresh from
`origin/main`, and the diff reapplied — one hunk
(`lrh-review-response/SKILL.md`) required hand redoing because upstream
had since replaced the prose-based idempotence check this hunk targeted
with a newer CLI exit-code-based `check-execution` flow
(`WI-SLUG-IDEMPOTENCE-CLI-TOOLING`, landed on `main` in the interim).
The prompt ID above was then minted (retroactively, before any commit)
and the confirm-plan gate was presented and explicitly approved by the
user before proceeding to commit/push/PR.

**Deferred, not part of this PR:** the WI's Required Change #5 (closing
`project/design/backlog.md`'s related entry). The entry's own condition
is "both work items implemented and resolved" — this WI isn't resolved
until this PR merges and closeout runs, so the backlog entry closes at
that point instead.

# Validation

- `scripts/version tools` — lrh 0.2.5.dev1397+g7b1cf7454.d20260807,
  Python 3.11.8, ruff 0.15.12, black 26.3.1 (after `scripts/develop`
  resolved a Black version-pin drift found mid-run)
- `scripts/format --check --diff` — clean, 190 files unchanged
- `scripts/lint` — all checks passed (ruff + black)
- `scripts/test` — 1004 tests, OK
- `lrh validate` — 0 errors, 0 warnings
- `diff -r src/lrh/skills/lrh-land/ .claude/skills/lrh-land/` — clean
- `diff -r src/lrh/skills/lrh-review-response/ .claude/skills/lrh-review-response/` — clean
- Cold-context self-review subagent (diff-mode, pre-`gh pr create`, per
  `/lrh-self-review`) — no findings; independently re-verified governance
  scoping, cross-references, `--include-thread` existence, mirror
  consistency, and dependency resolution against live repo state

# Follow-up

- Close `project/design/backlog.md`'s "`lrh request review_response`
  cannot surface a specific outdated-but-unresolved thread" entry once
  this WI resolves at closeout.
- Watch for review findings via `/lrh-review-response` /
  `/lrh-confirm-fixes`, then merge and run `/lrh-closeout`.
