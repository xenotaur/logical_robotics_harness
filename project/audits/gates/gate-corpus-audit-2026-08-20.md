---
id: AUDIT-GATE-CORPUS-2026-08-20
type: audit
title: Gate Corpus Audit for Invocation and Gate Reset Stage 3
date: 2026-08-20
related_work_item: WI-GATE-POLICY-CASCADE-STAGE3
related_workstream: WS-INVOCATION-AND-GATE-RESET
---

# Gate Corpus Audit for Invocation and Gate Reset Stage 3

## Summary

This audit inventories the LRH-owned statements that govern human confirmation,
review substitution, chain continuation, and closeout/merge authorization for
`WI-GATE-POLICY-CASCADE-STAGE3`.

The audit found a large gate-bearing corpus rather than one local defect:
tracked-file search over LRH-owned skills, planning files, memory, and top-level
guidance at the pre-cascade baseline commit `1a54114a` found 315 files with
4,687 matching gate-related lines. Stage 3 should therefore define a canonical
policy and a statement-shaped cascade rule, then patch only current-state
assertions that would mislead future runs.

## Survey Commands

All counts below were derived with `git grep` against baseline commit
`1a54114a`, not recursive filesystem search, so nested worktrees and untracked
scratch files are excluded. The baseline is intentional: it records the corpus
Stage 3 audited before this cascade added its policy, decision, and guidance
files.

Broad corpus:

```bash
git grep -c -E "confirm|approval|authorization|gate|completion condition|stop-work|merge authorization|self-review|review-response|confirm-fixes|retrigger|skip_if_opted_in|chain_init_confirmation" 1a54114a -- src/lrh/skills .claude/skills .agents/skills project/design project/workstreams project/work_items project/memory AGENTS.md CLAUDE.md STYLE.md 2>/dev/null | awk -F: '{files+=1; lines+=$NF} END {printf "files=%d\nmatching_lines=%d\n", files, lines}'
```

Result: 315 files, 4,687 matching lines.

Manual retrigger corpus:

```bash
git grep -c -E "@codex review|add-reviewer @copilot|manual hosted review-bot retrigger|manual GitHub review-bot retrigger|retrigger_bot_review" 1a54114a -- src/lrh/skills .claude/skills .agents/skills project/design project/workstreams project/work_items project/memory AGENTS.md CLAUDE.md STYLE.md 2>/dev/null | awk -F: '{files+=1; lines+=$NF} END {printf "files=%d\nmatching_lines=%d\n", files, lines}'
```

Result: 16 files, 29 matching lines. Current live skill statements describe the
retired/rejected retrigger path or forbid it; historical resolved work items
still narrate the old behavior and should not be rewritten merely for history.

Chain-initiation corpus:

```bash
git grep -c -E "chain authorization|chain-authorization|completion condition|stop-work condition|chain_init_confirmation|skip_if_opted_in|confirmed_commit" 1a54114a -- src/lrh/skills .claude/skills .agents/skills project/design project/workstreams project/work_items project/memory AGENTS.md CLAUDE.md STYLE.md 2>/dev/null | awk -F: '{files+=1; lines+=$NF} END {printf "files=%d\nmatching_lines=%d\n", files, lines}'
```

Result: 49 files, 374 matching lines.

Merge/closeout corpus:

```bash
git grep -c -E "merge gate|merge authorization|gh pr merge|match-head-commit|closeout gate|closeout plan|closeout_with_merge" 1a54114a -- src/lrh/skills .claude/skills .agents/skills project/design project/workstreams project/work_items project/memory AGENTS.md CLAUDE.md STYLE.md 2>/dev/null | awk -F: '{files+=1; lines+=$NF} END {printf "files=%d\nmatching_lines=%d\n", files, lines}'
```

Result: 54 files, 183 matching lines.

Review-cycle corpus:

```bash
git grep -c -E "plan-confirm|confirm gate|confirmation gate|review-response|confirm-fixes|REVIEW-LANDED|self-review" 1a54114a -- src/lrh/skills .claude/skills .agents/skills project/design project/workstreams project/work_items project/memory AGENTS.md CLAUDE.md STYLE.md 2>/dev/null | awk -F: '{files+=1; lines+=$NF} END {printf "files=%d\nmatching_lines=%d\n", files, lines}'
```

Result: 187 files, 1,922 matching lines.

## Gate-Bearing Statement Classes

The audit classifies statements by what they assert, not by the status bucket of
the artifact that contains them:

| Class | Current policy |
|---|---|
| Chain-initiation gates | A human-initiated chain requires completion and stop-work conditions. `always_confirm` requires a live reply. `skip_if_opted_in` may only skip the condition-confirmation reply under the user-local, value-bound consent model and special-condition checks in `DEC-CHAIN-INIT-SKIP-CONSENT`. |
| Restatement gates | A downstream gate may be satisfied without a second live reply only when an upstream gate already presented the concrete downstream plan and the downstream step mechanically verifies no material divergence. This is governed by `DEC-SINGLE-ASK-RUN-GATES`. |
| Review-cycle gates | `/lrh-confirm-fixes` remains the review verdict gate. Manual hosted review-bot retriggering is retired; substitute `/lrh-self-review` rounds are the fallback review signal, bounded by the provisional no-progress cap. |
| Merge authorization | Merge still requires a fresh, live, in-session reply to a SHA-locked command. The agent may execute only when the reply is unambiguous under `DEC-AGENT-EXECUTED-MERGE-GATE`. |
| Closeout | Closeout still happens after merge, when the merge commit exists. The merge and closeout questions may be one ask only when the actual closeout plan is presented before merge and post-merge divergence is treated as a new condition. |
| Recursion guards | `/lrh-self-review` uses `disallowed-tools: Skill` as the verified platform-enforced recursion guard, with advisory prompt text retained as defense in depth. |

## Superseded or Provisional Statement Classes

The following statement classes are not current policy and should not be copied
into new guidance:

- Manual hosted review-bot retrigger instructions such as posting `@codex review`
  or requesting `@copilot`.
- Claims that the old bot-retrigger round cap is still the review stabilization
  mechanism. The live cap is a no-progress cap over substitute self-review
  rounds.
- Blanket claims that chain initiation can never satisfy any internal gate. The
  current rule is narrower: independently load-bearing gates still fire, while
  restatement gates may use the single-ask/no-material-divergence pattern.
- Claims that `WI-DELIBERATE-MODEL-INVOCATION` is owned by
  `WS-EXECUTION-FRAMEWORK`. It was resolved under
  `WS-INVOCATION-AND-GATE-RESET`; older current-state ownership claims must be
  corrected even when they sit inside resolved artifacts.
- Advisory-only recursion guard descriptions for `/lrh-self-review`. The
  governing control is the verified platform guard recorded in
  `DEC-SELF-REVIEW-RECURSION-GUARD`.

## Required Cascade

The Stage 3 cascade should update:

- `src/lrh/skills/_shared/chain-defaults.md` and the inlined
  `src/lrh/skills/lrh-land/references/land-workflow.md` copy so the staleness
  check watches gate-definition surfaces rather than only the original
  chain-runner files.
- `.claude/skills/` and `.agents/skills/` local mirrors after source edits.
- The known stale ownership claims in `project/workstreams/resolved/WS-SKILLS-EXECUTE.md`,
  `project/work_items/resolved/WI-SKILLS-LRH-EXECUTE.md`, and the same statement
  shape found in `project/design/proposals/adopted/lrh-land-execute/00_proposal.md`.
- `WS-INVOCATION-AND-GATE-RESET` and `PROP-INVOCATION-AND-GATE-RESET` metadata
  that still describes `WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE` as
  proposed after PR #560 resolved it.
- `WI-CHAIN-DEFAULTS-ACTIVATION-STAGE3-5` so Stage 3.5 checks the named
  compensating control rather than accepting an assertion that one exists.

## Out of Scope

This audit does not activate `chain_init_confirmation: skip_if_opted_in`, does
not implement Stage 4 `confirm_fixes_batch` or `closeout_with_merge` fields, and
does not edit sibling repositories such as Taurcode. Cross-repository memory or
prompt corrections should be recorded as handoffs.
