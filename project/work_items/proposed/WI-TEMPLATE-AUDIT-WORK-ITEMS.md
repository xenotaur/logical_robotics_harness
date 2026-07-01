---
resolution: null
blocked_reason: null
blocked: false
id: WI-TEMPLATE-AUDIT-WORK-ITEMS
title: Implement lrh request audit-work-items template
type: deliverable
status: proposed
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
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - mutate_work_items
  - mutate_execution_records
  - invoke_lrh_closeout
  - implement_lrh_work_audit_skill
acceptance:
  - src/lrh/assist/templates/request/audit_work_items.md exists
  - template has a Skill reference comment pointing to src/lrh/skills/lrh-work-audit/SKILL.md
  - lrh request audit-work-items renders without error
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - validation_output
artifacts_expected:
  - src/lrh/assist/templates/request/audit_work_items.md
---

## Summary

Create a `lrh request audit-work-items` template that surfaces the work-item
audit workflow to agents that consume LRH request surfaces but do not natively
execute Claude Code skills — such as OpenAI ChatGPT (Codex) and Google Jules.

## Problem / Context

The `/lrh-work-audit` Claude Code skill (WI-SKILLS-LRH-WORK-AUDIT) encapsulates
the survey-open-work workflow for Claude sessions. However, other agents that the
project uses (Codex, Jules) cannot discover or invoke Claude Code skills. The LRH
request template surface (`lrh request <template>`) provides a portable way to
expose the same workflow as a rendered prompt that any agent can consume.

The precedent is `lrh request audit_docs` ↔ the `/lrh-doc-audit` skill: each
cross-references the other, and the template is the agent-neutral entry point
while the skill is the Claude-native entry point.

## Scope

Create `src/lrh/assist/templates/request/audit_work_items.md`. The template
renders a work-item audit prompt that an agent can execute without needing to
understand the Claude skill format. Do not modify the skill created in
WI-SKILLS-LRH-WORK-AUDIT or any Python source files unless a new Jinja/template
variable is required by the renderer.

## Required Changes

- Create `src/lrh/assist/templates/request/audit_work_items.md` with:
  - A `<!-- Skill reference: .claude/skills/lrh-work-audit/SKILL.md -->` comment
    at the top (matching the cross-reference convention from `audit_docs.md`).
  - A `Target agent:` and `Prompt ID:` header block.
  - An `## Inputs` section listing `repo_root`, `project_root`, and the
    suggested output artifact path.
  - A `## Task` section describing the three audit outputs: drift table,
    priority ranking, and orphaned-PR forensics.
  - A `## Constraints` section matching the "prompt-generating only, no
    mutations" invariant of other request templates.
  - A `## Output` section specifying the artifact format and path convention
    (`project/audits/<slug>.md`).
- Verify that `lrh request audit-work-items` renders the template without error
  (template variable substitution, no broken references).

## Acceptance Criteria

- `src/lrh/assist/templates/request/audit_work_items.md` exists.
- The template header contains a `<!-- Skill reference -->` comment pointing to
  `src/lrh/skills/lrh-work-audit/SKILL.md`.
- `lrh request audit-work-items` renders without error when called from the
  repository root.
- `lrh validate` passes with 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh request audit-work-items` (renders without error)
- `lrh validate`

## Non-Goals

- Do not implement or modify the `/lrh-work-audit` Claude Code skill (that is
  WI-SKILLS-LRH-WORK-AUDIT).
- Do not add new Python renderer code unless the existing template engine
  requires it for a new variable.
- Do not create a workstream; both WS-SKILLS and WS-SKILLS-DOC are closed.

## Dependencies / Order

Depends on WI-SKILLS-LRH-WORK-AUDIT: the skill SKILL.md must exist before the
template's `<!-- Skill reference -->` comment has a valid target to point to.
Both can be implemented in a single PR if convenient, but the skill WI is the
logical prerequisite.
