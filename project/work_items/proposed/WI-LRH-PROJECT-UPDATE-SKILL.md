---
id: "WI-LRH-PROJECT-UPDATE-SKILL"
title: "Add /lrh-project-update to bring a project's statusboard state up to date with the human"
type: "deliverable"
status: "proposed"
blocked: false
blocked_reason: null
resolution: null
owner: "anthony"
contributors:
- "anthony"
assigned_agents: []
parent_id: "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_focus: []
related_roadmap: []
related_workstreams:
- "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_design:
- "project/design/proposals/proposed/meta-operational-triage-semantics/00_proposal.md"
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
depends_on:
- "WI-LRH-CONSOLE-STATUSBOARD"
blocked_by: []
expected_actions:
- "create_file"
- "edit_file"
- "run_tests"
- "create_pr"
forbidden_actions:
- "force_push"
- "delete_branch"
- "merge_pr"
- "publish_package"
- "deploy_remote_service"
acceptance:
- "The skill reports, for one project or every registered project, its band, the evidence behind it, and the concrete records that put it there (for example, each blocked work item, missing checkout, or validation error)."
- "For each cause, it proposes a specific fix, such as setting a local checkout with lrh meta set, clearing a stale blocked flag, or fixing a validation error, and applies each fix only after the human confirms it."
- "It never edits another project's files without an explicit confirmation naming that project, and it never changes triage rules."
- "A run against the owner's registry moves the projects with discoverable checkouts out of Unknown, and the skill follows the LRH skill pattern, with tests or a dry-run fixture."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "src/lrh/skills/lrh-project-update/SKILL.md"
- "CLAUDE.md"
- "project/design/proposals/proposed/meta-operational-triage-semantics/00_proposal.md"
---

# /lrh-project-update

## Summary

Add a skill that looks at a registered project (or all of them) and works with the human to fix whatever puts it in Blocked, Needs attention, or Unknown on the statusboard, so that most projects show their true state.

## Problem / Context

Checking PR #805, the owner found that the statusboard is only as accurate as the records behind it:

- **Unknown:** five projects are there because they are registered without a local checkout, and an agent could help locate the checkouts.
- **Blocked:** Logical Robotics Harness shows as Blocked, though it has about 20 active threads of work. The cause is `derive_operational_status` (`src/lrh/ux/dashboard.py`): any single blocked work item makes the whole project Blocked.

Part of this is stale data, which a skill can fix with the human. Part of it is the triage rule, which is a design decision. This item records the rule question but does not change it.

### Duplication search

In-repo: `lrh meta set`, `lrh meta inspect`, and `lrh meta refresh` edit and inspect records; `/lrh-readiness` fixes thin work items; `/lrh-work-remains` reports remaining work. None of them reconciles a project's statusboard state. Recommendation: proceed, reusing those commands.

## Scope

- A new interactive skill that diagnoses and, with confirmation, fixes a project's statusboard state.
- A recorded open question about the Blocked rule.

## Required Changes

- A `/lrh-project-update` skill: diagnose (band, evidence, causes), propose fixes, confirm each one, apply it, and re-check the band.
- Add a note to `PROP-META-OPERATIONAL-TRIAGE-SEMANTICS` raising the rule question: should a project be Blocked only when nothing else can move? Leave the decision to the owner.

## Non-Goals

- No change to `derive_operational_status` or the band mapping.
- No scheduled or unattended runs.

## Acceptance Criteria

- The skill reports, for one project or every registered project, its band, the evidence behind it, and the concrete records that put it there (for example, each blocked work item, missing checkout, or validation error).
- For each cause, it proposes a specific fix, such as setting a local checkout with lrh meta set, clearing a stale blocked flag, or fixing a validation error, and applies each fix only after the human confirms it.
- It never edits another project's files without an explicit confirmation naming that project, and it never changes triage rules.
- A run against the owner's registry moves the projects with discoverable checkouts out of Unknown, and the skill follows the LRH skill pattern, with tests or a dry-run fixture.

## Validation

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- Dogfood the skill on the owner's registry with the owner.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-STATUSBOARD`.
- Related: the owner's planned design session on the focus construct (threads of work that cut across workstreams), which may change what a project's state means.

## Risk Notes

- The skill touches other repositories' control planes. Keep every write behind a per-project confirmation, and show the diff first.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/meta-operational-triage-semantics/00_proposal.md`
