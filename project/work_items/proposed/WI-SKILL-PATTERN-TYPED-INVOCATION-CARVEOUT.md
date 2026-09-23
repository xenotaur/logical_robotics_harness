---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILL-PATTERN-TYPED-INVOCATION-CARVEOUT
title: Document the typed-invocation carve-out to the confirm-before-write gate
type: deliverable
status: proposed
owner: null
contributors: []
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - change_lrh_export_claude_skill
  - retrofit_other_skills
acceptance:
  - "lrh-skill-pattern.md's confirm-before-write gate section documents that a literal, user-typed slash-command invocation satisfies the gate on its own, distinct from a model-initiated invocation"
  - "The doc states this carve-out is opt-in per skill, not a default: a skill must explicitly implement the typed/model-initiated distinction to use it, citing lrh-export-claude/SKILL.md Step 3 as the worked example"
  - "The doc describes how to distinguish a typed invocation from a model-initiated one (the <command-name>/<command-message> tag signal) and requires treating an unreadable signal as model-initiated, never guessing typed"
  - "The doc states that a skill using this carve-out may still name specific flags or parameters that always require confirmation regardless of typed/model status, citing --force in lrh-export-claude as the example"
  - "The three rendered installs of lrh-skill-pattern.md match the source and no unrelated file changed"
  - "lrh validate reports 0 errors and introduces no new warnings"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-create-skill/references/lrh-skill-pattern.md
  - .claude/skills/lrh-create-skill/references/lrh-skill-pattern.md
  - .agents/skills/lrh-create-skill/references/lrh-skill-pattern.md
  - .gemini/plugins/lrh/skills/lrh-create-skill/references/lrh-skill-pattern.md
---

# WI-SKILL-PATTERN-TYPED-INVOCATION-CARVEOUT: Document the typed-invocation carve-out to the confirm-before-write gate

## Summary

Add an explicit, scoped exception to `lrh-skill-pattern.md`'s confirm-before-write
gate section: a literal, user-typed slash-command invocation may satisfy the
gate on its own, without a separate confirmation step, when a skill
explicitly implements and documents that distinction.

## Problem / Context

`lrh-skill-pattern.md`'s confirm-before-write gate section states an
unconditional rule — every file-writing skill "must always include a
mandatory user-confirmation step before writing" — with no documented
exception. `WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT` (PR #703,
merged) implemented exactly such an exception for `/lrh-export-claude`: a
user-typed invocation states the resolved session and destination and
proceeds without waiting, while a model-initiated invocation still confirms,
per a decision recorded 2026-09-20 and directly reaffirmed by the repo owner.

This was flagged during that PR's review (Copilot finding, thread `km9-g`):
the behavior conflicts with the pattern doc's own unconditional wording.
The finding was deliberately deferred rather than fixed inline — the
underlying behavior is intentional and already approved, but formalizing the
exception in the shared, repo-wide pattern doc is a separate, cross-cutting
change outside that WI's own file scope (its `artifacts_expected` covered
only the `lrh-export-claude` skill and `CLAUDE.md`).

### Duplication search
- In-repo: `WI-DELIBERATE-MODEL-INVOCATION` (resolved) and
  `WI-CODEX-EXPORT-INVOCATION-FLAG-REMOVAL` (resolved) both address
  model-vs-user invocation, but for the `disable-model-invocation`
  frontmatter flag (a platform-level invocation block), not the
  confirm-before-write gate's own prose. No existing item documents this
  specific carve-out.
- Sibling repos: none identified.
- External libraries: not applicable.
- Recommendation: Proceed.

### Demand search
- Work items: none open on this doc gap; raised only as a deferred review
  finding on PR #703, not yet tracked as its own item.
- Proposals: `project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md`
  established the confirm-before-write gate; does not anticipate this
  exception.
- Backlog: no matching entry.
- Recommendation: No action; this item is the tracking artifact.

## Scope

- Edit `src/lrh/skills/lrh-create-skill/references/lrh-skill-pattern.md`'s
  confirm-before-write gate section and re-render its three installed copies.
- Document the carve-out as an opt-in pattern, not a default — it changes
  what a skill *may* implement, not the baseline gate every skill gets
  without asking.

## Required Changes

1. In the confirm-before-write gate section, add a subsection documenting
   the carve-out: a literal user-typed slash-command invocation is itself
   the explicit human decision the gate exists to require, so a skill may
   treat it as satisfying the gate without a further wait.
2. State explicitly that this is opt-in: a skill must implement the
   typed/model-initiated distinction itself (detection, both branches, the
   ambiguous fallback) to use it — it is not implied by the general pattern.
   Cite `src/lrh/skills/lrh-export-claude/SKILL.md` Step 3 as the worked
   reference implementation.
3. Document the detection mechanism in general terms: a typed invocation
   surfaces as `<command-message>`/`<command-name>` tags (or the equivalent
   explicit textual invocation signal the current platform provides) naming
   the skill, in the same turn. When this signal cannot be confidently read,
   treat the invocation as model-initiated — never guess typed.
4. Document that a skill using this carve-out may still name specific
   "dangerous" flags or parameters that always require confirmation
   regardless of typed/model status, as a static, explicit list rather than
   a computed judgment. Cite `--force` in `lrh-export-claude` as the example,
   and the rationale recorded there: a static check avoids duplicating
   another command's own logic (e.g. a destination-path formula) inside
   skill prose, which is a demonstrated defect class in this project.
5. Re-render the three installed copies
   (`.claude/skills`, `.agents/skills`, `.gemini/plugins/lrh/skills`) for
   `lrh-create-skill` only. Verify with `git status` that only
   `lrh-skill-pattern.md`'s three copies changed.

## Non-Goals

- Does not modify `lrh-export-claude/SKILL.md` or any other skill — this
  item documents the pattern; it does not apply it anywhere new.
- Does not make the carve-out a default for skills that don't explicitly
  implement it.
- Does not change `disable-model-invocation` frontmatter handling — that is
  a separate, already-resolved mechanism (`WI-DELIBERATE-MODEL-INVOCATION`).

## Acceptance Criteria

- The confirm-before-write gate section documents the typed-invocation
  carve-out, scoped as opt-in per skill.
- The doc describes the detection signal and the ambiguous-defaults-to-model
  fallback.
- The doc describes the dangerous-flag exception pattern, citing `--force`
  in `lrh-export-claude` as the example.
- The three rendered installs match the source and no unrelated file changed.
- `lrh validate` reports 0 errors and introduces no new warnings.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh skills check --target claude --local --source current-repo`
- `lrh skills check --target codex --local --source current-repo`
- `lrh skills check --target antigravity --local --source current-repo`
