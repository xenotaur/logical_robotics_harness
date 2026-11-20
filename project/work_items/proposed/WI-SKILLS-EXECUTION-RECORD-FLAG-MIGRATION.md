---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-EXECUTION-RECORD-FLAG-MIGRATION
title: "Migrate LRH skills to pass the execution-record field flags instead of hand-editing"
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
  - project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md
depends_on:
  - WI-EXECUTION-RECORD-AGENT-FIELDS
blocked_by: []
expected_actions:
  - edit_file
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - modify_ci_pipeline
  - hand_edit_rendered_mirrors
acceptance:
  - "Every skill step that creates an execution record passes --agent, --instruction-source, and --session-transcript to lrh prompt record-execution instead of instructing a post-hoc hand-edit, including lrh-self-review, which currently sets none of them"
  - "All three rendered mirrors (.claude/skills, .agents/skills, .gemini/plugins/lrh/skills) are regenerated with the installer and tests/packaging_tests/skills_mirror_sync_test.py passes"
  - "The guidance for session_transcript states it is a claude-app:<host-uuid-stem> style pointer or the sentinel pending, never an absolute path"
  - "lrh-land's land-workflow reference tells a second-PR closeout to use the <primary-slug>-closeout-note slug"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - "src/lrh/skills/ edits in lrh-implement, lrh-work-item, lrh-review-response, lrh-confirm-fixes, lrh-proposal, lrh-workstream, lrh-doc-work, lrh-doc-organize, lrh-self-review, and lrh-land"
  - "Regenerated mirrors under .claude/skills, .agents/skills, and .gemini/plugins/lrh/skills"
---

# WI-SKILLS-EXECUTION-RECORD-FLAG-MIGRATION

## Summary

Make the LRH skills create execution records with `--agent`,
`--instruction-source`, and `--session-transcript` on
`lrh prompt record-execution`, instead of generating a record and telling the
agent to hand-edit it afterward. `lrh-self-review` gets the flags for the first
time.

## Problem / Context

WI-EXECUTION-RECORD-AGENT-FIELDS (PR #794, merge 7d2d7363) added the optional
flags. It left the skill text alone, because rendering every change into four
copies makes a large mechanical diff that is best reviewed on its own. As of
`main` at f94852c0, 13 canonical files under `src/lrh/skills` still carry the
"Immediately edit the generated file" step: `lrh-implement`, `lrh-work-item`,
`lrh-review-response`, `lrh-confirm-fixes`, `lrh-proposal`, `lrh-workstream`,
`lrh-doc-work`, and `lrh-doc-organize`. `lrh-self-review` Step 6 runs
`record-execution` and sets none of the three fields, which is the cause of the
three self-review records in the original LCATS report that motivated the CLI
change. The same run also showed that a second PR for one work item collides on
the bare `-closeout-note` slug: the pre-mint slug check blocks, and a bare slug
makes `/lrh-land`'s primary-versus-side-record provenance check ambiguous.

### Duplication search
- In-repo: Related, not a duplicate: WI-IMPLEMENT-SELFREVIEW-PR-BACKFILL (PR #808) fixed the PR-linking half of `/lrh-implement`'s records only; no work item migrates the skills to the new flags (grep over `src/`, `project/design/proposals/`, `project/workstreams/`, `project/work_items/` for the flag names finds only the resolved WI-EXECUTION-RECORD-AGENT-FIELDS)
- Sibling repos: LCATS consumes these skills and has no fix
- External libraries: None identified; this is LRH-specific skill text
- Recommendation: Proceed

### Demand search
- Work items: None found requesting this; the resolved WI-EXECUTION-RECORD-AGENT-FIELDS names it as the deferred follow-up
- Proposals: None found
- Backlog: No matching entries
- Recommendation: No action

## Scope

- Switch every execution-record creation step in the listed skills to the flags
- Cover `lrh-self-review` and its `self-review-workflow.md` reference
- Regenerate the mirrors with the installer
- Add the closeout-note slug guidance to `lrh-land`

## Required Changes

1. Read `src/lrh/skills/_shared` and the skills named in Scope to find every "immediately edit" step.
2. Replace each with a `record-execution` call that passes the three flags. `instruction_source` is a repo-relative path, a URL, or a short description, and `session_transcript` is `claude-app:<host-uuid-stem>` or `pending`.
3. Add the three flags to `lrh-self-review` Step 6 and to `references/self-review-workflow.md`.
4. Add the closeout-note slug rule to `src/lrh/skills/lrh-land/references/land-workflow.md`.
5. Regenerate the mirrors following the "Sync requirement" section of `CONTRIBUTING.md`, previewing with `--force --diff` first and never hand-copying.
6. Run the mirror-sync test and `lrh validate`.

## Non-Goals

- Do not change the CLI; the flags exist and are tested.
- Do not change existing execution records.
- Do not make the fields required, or give `--agent` a default.
- Do not teach `lrh validate` to warn on missing fields; that is a separate validator stage.

## Acceptance Criteria

- Every skill step that creates an execution record passes the three flags instead of instructing a hand-edit, including `lrh-self-review`.
- All three rendered mirrors are regenerated with the installer and `tests/packaging_tests/skills_mirror_sync_test.py` passes.
- The `session_transcript` guidance states it is a `claude-app:<host-uuid-stem>` style pointer or `pending`, never an absolute path.
- `lrh-land`'s `land-workflow.md` tells a second-PR closeout to use the `<primary-slug>-closeout-note` slug.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh skills check --local --target all --source current-repo`

## Risk Notes

- Open PRs #854 and #856 touch `src/lrh/skills` or the `.claude/skills` mirrors, so conflicts are likely. Land them first or rebase before executing. PR #824 touched the same area and has since merged.
- A skill that passes the new flags would fail against an older installed `lrh`. Skills install alongside their own `lrh`, but a stale editable install can lag `main`; check `lrh prompt record-execution --help` first.
- `--session-transcript` must never receive an absolute path, because that leaks the local layout.
