---
resolution: "Implemented and merged in PR #586 (creation, commit 76d837a2) and PR #588 (implementation, commit 7b15d948)."
blocked_reason: null
blocked: false
id: WI-EXECUTE-STEP1-5-SLUG-IDEMPOTENCE
title: Add slug-based pre-mint idempotence check to lrh-execute Step 1.5
type: operation
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - merge_pr
acceptance:
  - src/lrh/skills/lrh-execute/SKILL.md Step 1.5 point 4 runs a slug-based lrh prompt check-execution --slug ... --work-item <WI-ID> pre-mint check before lrh prompt label, matching lrh-work-item Step 4's pattern, before the existing post-mint --prompt-id check
  - The added text explains why the post-mint --prompt-id check alone is insufficient (lrh prompt label always mints a fresh timestamped ID, so a --prompt-id check on it can never find a prior record)
  - Mirrored to .claude/skills/lrh-execute/SKILL.md, .agents/skills/lrh-execute/SKILL.md, and .gemini/plugins/lrh/skills/lrh-execute/SKILL.md via lrh skills install --local --target all --source current-repo --force
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-execute/SKILL.md
  - .claude/skills/lrh-execute/SKILL.md
  - .agents/skills/lrh-execute/SKILL.md
  - .gemini/plugins/lrh/skills/lrh-execute/SKILL.md
---

## Summary

Fix `/lrh-execute` Step 1.5 point 4 ("Mint the prompt ID and run
idempotence"), which only runs `lrh prompt check-execution --prompt-id`
on the freshly-minted prompt ID — a check that can never find a prior
record, since `lrh prompt label` always mints a fresh, unique,
timestamped ID. The step needs a slug-based pre-mint check first, the
same pattern `/lrh-work-item` Step 4 already documents and follows
correctly.

## Problem / Context

Flagged by `copilot-pull-request-reviewer` on Taurcode PR #82 (a
mechanical `lrh skills install --local --force` resync of this project's
own skill package into the Taurcode repo, unrelated to this bug's
origin). The comment was initially, incorrectly, dispositioned as
"already resolved by this diff" in that PR's own triage — the person
checking it verified `/lrh-work-item`'s Instruction phase (which is
correct) instead of the file the comment actually anchors to,
`.claude/skills/lrh-execute/SKILL.md:178`. Caught and corrected during a
later confirm-fixes round on that same PR, which re-verified against the
right file.

Read directly against this repo's current source
(`src/lrh/skills/lrh-execute/SKILL.md:173-178`):

```bash
lrh prompt label --slug <slug> --work-item <WI-ID>
lrh prompt check-execution --prompt-id "<id>" --project-root .
```

`lrh prompt label` mints a brand-new, uniquely-timestamped prompt ID on
every call. Passing that freshly-minted ID to `check-execution
--prompt-id` can therefore never find a match — no prior record was ever
recorded under an ID that didn't exist until this call created it. The
check is a no-op for its stated purpose (idempotence — detecting a rerun
of the same logical work).

`/lrh-work-item` Step 4 (`src/lrh/skills/lrh-work-item/SKILL.md:158-215`)
documents and follows the correct two-check pattern: a slug-based
pre-mint check (`lrh prompt check-execution --slug <slug> --work-item
<bucket>`, which matches by stable slug across the local checkout and
open PRs) *before* minting, interpreting its exit code per
`DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT`, followed by the same post-mint
`--prompt-id` check `/lrh-execute` already has. `/lrh-execute` is missing
only the first half.

**Prior art check:**
- *Duplication search:* grepped `project/work_items/` and
  `project/design/backlog.md` for "execute" + "idempotence" and "slug" —
  no existing work item or backlog entry addresses this specific gap in
  `/lrh-execute` Step 1.5.
- *Demand search:* grepped `project/workstreams/` and `project/design/`
  for the same terms — no existing request found.

## Scope

- `src/lrh/skills/lrh-execute/SKILL.md` Step 1.5 point 4: add the
  slug-based pre-mint check before `lrh prompt label`, mirroring
  `/lrh-work-item` Step 4's exact pattern (derive `<slug>` from the WI
  ID, run `check-execution --slug`, interpret the exit code the same
  way, then proceed to the existing mint + post-mint check).
- Mirror the change to every checked-in skill target this repo renders
  to (`.claude/skills/`, `.agents/skills/`, `.gemini/plugins/lrh/skills/`).

## Non-Goals

- Does not change `/lrh-implement` Step 3, which has the same
  post-mint-only pattern — that is a separate, broader question (whether
  `/lrh-implement`'s own idempotence relies on a different mechanism,
  e.g. its Step 1 readiness check) not raised by this comment and out of
  scope here.
- Does not change the WS-ID branch's own existing in-progress/landed
  execution-record check (Step 1) — that check already exists and is
  correct for its purpose; this WI only adds the missing slug-based
  pre-mint check to Step 1.5.

## Required Changes

1. Edit `src/lrh/skills/lrh-execute/SKILL.md` Step 1.5 point 4: insert a
   slug-based `lrh prompt check-execution --slug <slug> --work-item
   <WI-ID>` pre-mint check before `lrh prompt label`, with the exit-code
   interpretation matching `/lrh-work-item` Step 4's pattern, and a short
   note explaining why the existing post-mint `--prompt-id` check alone
   is insufficient.
2. Render the edited file to `.claude/skills/`, `.agents/skills/`, and
   `.gemini/plugins/lrh/skills/` via `lrh skills install --local --target
   all --source current-repo --force`.

## Acceptance Criteria

- Step 1.5 point 4 runs the slug-based pre-mint check before minting.
- The added text explains the insufficiency of a post-mint-only check.
- All three mirror targets report up to date via `lrh skills
  check`/`status --source current-repo`.
- `lrh validate` reports 0 errors.

## Validation

- lrh validate
- lrh skills check --target claude --local --source current-repo
- lrh skills status --target codex --local --source current-repo
- lrh skills status --target antigravity --local --source current-repo

## Risk Notes

Low risk — documentation/instruction-wording fix to an agent-facing skill
file; no code or CLI behavior changes. The added slug-based check reuses
an existing, already-implemented CLI feature (`check-execution --slug`),
not new functionality.
