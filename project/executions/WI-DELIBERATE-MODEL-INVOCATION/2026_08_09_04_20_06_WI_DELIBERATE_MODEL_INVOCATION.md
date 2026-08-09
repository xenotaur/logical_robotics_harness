---
execution_id: 2026_08_09_04_20_06_WI_DELIBERATE_MODEL_INVOCATION
prompt_id: PROMPT(WI-DELIBERATE-MODEL-INVOCATION:WI_DELIBERATE_MODEL_INVOCATION)[2026-08-09T03:55:48+00:00]
work_item: WI-DELIBERATE-MODEL-INVOCATION
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/533
commit: 
agent: claude_app
instruction_source: project/work_items/proposed/WI-DELIBERATE-MODEL-INVOCATION.md
session_transcript: pending
created_at: 2026-08-09T04:20:06+00:00
---

# Summary

Implements `WI-DELIBERATE-MODEL-INVOCATION`'s Required Changes: removes
`disable-model-invocation` from the 9 tier-1/2/3 skills whose gate
placement was audited and confirmed sufficient, adding a tiered
`when_to_use` to each; leaves the 4 excluded skills (`lrh-self-review`,
`lrh-confirm-fixes`, `lrh-land`, `lrh-execute`) untouched, each for a
specific tracked gap; cascades the resolution into `_shared/lifecycle-chain.md`,
`lrh-create-skill`'s authoring guidance, and `project/executions/README.md`.

# Result

- Removed `disable-model-invocation: true` and added a tiered `when_to_use`
  in both `src/lrh/skills/` and `.claude/skills/` for: `lrh-closeout`,
  `lrh-create-skill`, `lrh-design`, `lrh-doc-audit`, `lrh-doc-organize`,
  `lrh-doc-work`, `lrh-implement`, `lrh-readiness`, `lrh-review-response`.
  Each `when_to_use` cites the skill's actual confirm-gate step number,
  cross-checked against the skill's own `### Step N` heading.
- Did not touch `lrh-self-review`, `lrh-confirm-fixes`, `lrh-land`,
  `lrh-execute` — each keeps the flag per the WI's tier 2a/2b/3a exclusions.
- `_shared/lifecycle-chain.md`: replaced the now-false "most skills carry
  the flag" claim and the "flag blocks invoking them" inlining rationale
  with the tiered resolution, cross-linked to
  `DEC-DELIBERATE-CHAIN-INITIATION.md`'s dated 2026-08-08 Consequences entry.
- Rewrote `lrh-create-skill/references/{lrh-skill-pattern.md,frontmatter-guide.md,worked-example.md}`
  so new skills don't default to the flag for "high-consequence" work —
  including fixing `worked-example.md`'s own contrast table, which had
  cited `lrh-create-skill` itself as needing the flag (now stale, since
  this PR removes it from `lrh-create-skill`).
- Added a CHAIN-NOTE placement / find-or-backfill section to
  `project/executions/README.md`, cross-referencing
  `lrh-land/references/land-workflow.md`'s canonical format tables rather
  than duplicating them.
- `installer.py`: verified no code change needed — its Codex-side
  `agents/openai.yaml` rendering derives entirely from the
  `disable-model-invocation` frontmatter value already (no separate
  preload-eligibility switch to update), and its own tests
  (`tests/skills_installer_test.py`) use synthetic fixtures independent of
  real skill content, so this change doesn't affect them.

# Validation

- `lrh validate` — 0 errors (1 pre-existing, unrelated warning)
- `lrh work-items validate` — no findings
- `scripts/test` — 1065 tests, OK
- `scripts/format --check --diff`, `scripts/lint` — clean (2 pre-existing,
  unrelated lint errors in `tests/conversations_tests/antigravity_export_test.py`,
  confirmed present on `main` before this branch via `git stash`)
- `diff -r src/lrh/skills/<name>/ .claude/skills/<name>/` — clean for all
  9 edited skills and the 3 edited `lrh-create-skill` reference files
- `/lrh-self-review` diff-mode pass (Step 7.5, before push) — cold-context
  subagent found no defects across 6 specific checks (flag-removal scope,
  `when_to_use` quality, mirror byte-identity, `lifecycle-chain.md`
  accuracy, authoring-guidance consistency, step-number citations);
  independently re-verified the flag-removal-scope claim directly
  (`grep -l disable-model-invocation: true src/lrh/skills/*/SKILL.md`)

# Follow-up

- Not this WI (tracked separately): add a diff-mode confirm gate to
  `lrh-self-review` before its flag can be removed; add a confirm step to
  `lrh-confirm-fixes`'s empty-thread fast path before its flag can be
  removed; design a way to verify a genuine human-typed slash-command
  invocation (or restrict `skip_if_opted_in`) before `lrh-land`/`lrh-execute`
  can drop theirs.
- `session_transcript: pending` should be updated to
  `claude-app:<host-uuid-stem>` after the session ends.
