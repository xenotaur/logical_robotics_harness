---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-WORK-REMAINS
title: Implement lrh-work-remains Claude Code skill
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - modify_lrh_snapshot_cli
  - implement_taurcode_prompt_port
acceptance:
  - .claude/skills/lrh-work-remains/SKILL.md exists with valid frontmatter (name, description, disable-model-invocation: true)
  - .claude/skills/lrh-work-remains/ is an exact copy of src/lrh/skills/lrh-work-remains/
  - references/remains-checklist.md preserves the 18-item checklist verbatim (see this WI's "Checklist" section)
  - CLAUDE.md ## Skills has a /lrh-work-remains entry
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-work-remains/SKILL.md
  - src/lrh/skills/lrh-work-remains/references/remains-checklist.md
  - src/lrh/skills/lrh-work-remains/references/grounding-sources.md
  - .claude/skills/lrh-work-remains/SKILL.md
  - .claude/skills/lrh-work-remains/references/remains-checklist.md
  - .claude/skills/lrh-work-remains/references/grounding-sources.md
---

## Summary

Implement the `/lrh-work-remains` Claude Code skill: a strictly read-only,
session-scoped reporting skill that summarizes what a session accomplished
and surfaces what work remains, grounded in actual tracked repo state rather
than conversational recall. Applies the already-adopted project-local-skills
pattern; introduces no new architectural decision.

## Problem / Context

Users currently re-derive "what's left" manually at the end of a session, or
paste an ad hoc prompt (an Apple Notes snippet) that isn't grounded in tool
output and has no fixed checklist, so categories get silently skipped.
Taurcode's `:remains` prompt covers a narrower, PR-closure-specific case and
lives in the separate Taurcode repo (`prompts/taurcode/remains.md` there —
not a path in this repository).

**Prior art check:**
- *Duplication search:* no existing skill or script in `src/lrh/skills`,
  `.claude/skills`, or `project/design` performs this. `lrh snapshot
  current_focus` (`src/lrh/assist/snapshot_cli.py:61`) already grounds
  workstream/work-item/proposal state from disk and will be reused as a data
  source, not duplicated.
- *Demand search:* no open backlog entry, WI, or proposal requests this
  capability; all "remains" hits in `project/design/backlog.md` are
  incidental prose, not a tracked ask.

## Checklist (verbatim, source of truth for `references/remains-checklist.md`)

The implementation must copy this list into
`references/remains-checklist.md` without paraphrasing:

1. Incomplete work
2. Unanswered questions
3. Uncommitted files
4. Feature branches not pushed to main
5. Open PRs not yet merged
6. Unaddressed comments on PRs
7. Incomplete closeouts of PRs
8. Stray files
9. Stale branches
10. Unsaved memories
11. Untaken offers
12. Unaddressed issues
13. Control plane updates
14. Open work items
15. Unfinished workstreams
16. Documentation updates
17. Dogfooding of user-facing features
18. Other unfinished scope of work

(The source Apple Notes prompt bulleted 16 explicit items plus an "other"
catch-all; splitting "unanswered questions" and "control plane updates" out
as their own numbered lines above brings the count to 18 — no content was
dropped or added relative to the original text.)

## Scope

- `SKILL.md`: session-summary + fixed-checklist report flow — no
  confirm-before-write gate needed, since nothing is written.
- `references/remains-checklist.md`: the 18-item checklist above, copied
  verbatim from the source Apple Notes prompt.
- `references/grounding-sources.md`: which command(s) ground each category
  (git status/log, gh pr list/view, lrh snapshot current_focus --stdout,
  manual eyeball against the Claude Code session auto-memory index —
  `~/.claude/projects/<project>/memory/MEMORY.md`, outside this repo and
  distinct from this repo's own `project/memory/` control-plane files).
- `src/lrh/skills/lrh-work-remains/`: package source.
- `.claude/skills/lrh-work-remains/`: exact mirror for discovery.
- `CLAUDE.md ## Skills` index entry.

## Required Changes

1. Create `src/lrh/skills/lrh-work-remains/SKILL.md`
2. Create `src/lrh/skills/lrh-work-remains/references/remains-checklist.md`
3. Create `src/lrh/skills/lrh-work-remains/references/grounding-sources.md`
4. Copy `src/lrh/skills/lrh-work-remains/` to `.claude/skills/lrh-work-remains/` (byte-for-byte)
5. Add `/lrh-work-remains` entry to `CLAUDE.md ## Skills`
6. Verify `diff -r src/lrh/skills/lrh-work-remains/ .claude/skills/lrh-work-remains/` is empty

## Non-Goals

- Does not write files, run `lrh prompt` commands, or mutate git state — report only
- Does not implement automated cross-session ownership classification — flags candidates, asks the user to confirm
- Does not implement the Taurcode-repo prompt port-back (updating that
  repo's `prompts/taurcode/remains.md`, adding a new
  `prompts/lrh/lrh-remains.md` there) — those paths are in the separate
  Taurcode repo, not this one, and are tracked separately there
- Does not modify `src/lrh/assist/snapshot_cli.py` — consumes it as-is

## Acceptance Criteria

- `.claude/skills/lrh-work-remains/SKILL.md` exists with valid frontmatter
  (`name`, `description`, `disable-model-invocation: true`)
- `.claude/skills/lrh-work-remains/` is an exact copy of `src/lrh/skills/lrh-work-remains/`
- `references/remains-checklist.md` preserves all 18 checklist items verbatim
- `CLAUDE.md ## Skills` has a `/lrh-work-remains` entry
- `lrh validate` passes with 0 errors

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-work-remains/ .claude/skills/lrh-work-remains/`
