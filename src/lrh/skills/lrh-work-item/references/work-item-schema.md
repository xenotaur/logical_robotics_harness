# LRH Work Item — YAML Frontmatter Field Reference

This document is the authoritative field reference for LRH work item YAML
frontmatter. Validated against `src/lrh/control/validator.py` and the
project work-items README (June 2026).

---

## Required fields

These fields are required by `lrh validate` and must be present on every
work item.

### Schema-required (`WORK_ITEM_REQUIRED_FIELDS` in `validator.py`)

| Field | Type | Constraints |
|---|---|---|
| `id` | string | SCREAMING-KEBAB-CASE; must match the filename stem exactly |
| `title` | string | Short human-readable title; used in listings and prompts |
| `type` | string | See type vocabulary below; `lrh validate` also validates against allowed values |
| `status` | string | `proposed`, `active`, `resolved`, or `abandoned` |

### Policy-required (enforced via `_validate_work_item_policy_required_fields`)

| Field | Type | Constraints |
|---|---|---|
| `blocked` | boolean | `true` or `false`; `true` only valid when `status: active` |
| `blocked_reason` | string or null | `null` unless `blocked: true` |
| `resolution` | string or null | `null` unless status is terminal (`resolved` or `abandoned`) |

### Status → directory bucket mapping

The file must live in the directory that matches its `status` value:

| `status` | Directory |
|---|---|
| `proposed` | `project/work_items/proposed/` |
| `active` | `project/work_items/active/` (create if needed) |
| `resolved` | `project/work_items/resolved/` |
| `abandoned` | `project/work_items/abandoned/` |

`lrh validate` fails if the file is in the wrong bucket.

---

## Conventional fields

These fields are not enforced as required by the schema but are present on
all well-formed work items and expected by downstream prompts such as
`lrh request prompt-from-work-item`.

### Identity

| Field | Type | Notes |
|---|---|---|
| `owner` | string | GitHub handle or name of the responsible person |
| `contributors` | list of strings | Other contributors beyond the owner |
| `assigned_agents` | list | Usually `[]`; populated only when an agent has been assigned |

### Relationships

| Field | Type | Notes |
|---|---|---|
| `related_focus` | list of strings | `FOCUS-*` IDs from `project/focus/` |
| `related_roadmap` | list of strings | `ROADMAP-*` IDs from `project/roadmap/` |
| `related_workstreams` | list of strings | `WS-*` IDs from `project/workstreams/` |
| `related_design` | list of strings | File paths to relevant design docs |
| `depends_on` | list of strings | `WI-*` IDs this item cannot start before |
| `blocked_by` | list of strings | `WI-*` IDs currently blocking this item |

### Execution guidance

| Field | Type | Notes |
|---|---|---|
| `expected_actions` | list of strings | Actions the implementation agent is expected to take (see vocabulary below) |
| `forbidden_actions` | list of strings | Actions the implementation agent must never take (see vocabulary below) |
| `acceptance` | list of strings | One-line verifiable acceptance conditions; mirrors `## Acceptance Criteria` body section |
| `required_evidence` | list of strings | Evidence types needed before closing (see vocabulary below) |
| `artifacts_expected` | list of strings | File paths or descriptions of expected outputs |

---

## Type vocabulary

Use the value that best describes what the work item produces. `lrh validate`
validates `type` against this allowed-value list.

| Value | Use when |
|---|---|
| `deliverable` | The item produces files: code, docs, config, skills, or schema |
| `operation` | The item performs a maintenance task: tidy, organize, migrate, reconcile |
| `investigation` | The item explores or surveys: research, spike, sourcetree audit |
| `evaluation` | The item measures or audits: benchmark, readiness check, assessment |

---

## Action vocabulary

Common values for `expected_actions` and `forbidden_actions`:

**expected_actions:** `create_file`, `edit_file`, `delete_file`, `run_tests`,
`create_pr`, `write_docs`, `create_report`, `add_cli_command`

**forbidden_actions:** `force_push`, `delete_branch`, `implement_<next_stage>`,
`merge_pr`, `publish_package`, `run_lrh_agentic`, `modify_ci_pipeline`

---

## Evidence vocabulary

Common values for `required_evidence`:

| Value | Meaning |
|---|---|
| `manual_review` | A human has reviewed the output |
| `lrh_validate` | `lrh validate` passed with 0 errors |
| `test_output` | Automated test suite output |
| `validation_output` | Output from a domain-specific validator |

---

## Blocking rules

Blocking is only valid for `active` work items:

```yaml
status: active
blocked: true
blocked_reason: "Waiting for WI-SKILLS-LRH-SETUP to land"
```

For all `proposed` items, the canonical unblocked state is:

```yaml
blocked: false
blocked_reason: null
```

---

## Minimum valid frontmatter

```yaml
---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXAMPLE
title: Short descriptive title
type: deliverable
status: proposed
---
```

## Full example

```yaml
---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-WORK-ITEM
title: Implement lrh-work-item Claude Code skill
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS
related_design:
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
depends_on:
  - WI-SKILLS-CREATE-SKILL
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_setup
acceptance:
  - src/lrh/skills/lrh-work-item/SKILL.md exists with valid frontmatter
  - .claude/skills/lrh-work-item/ is an exact copy of src/lrh/skills/lrh-work-item/
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-work-item/SKILL.md
  - src/lrh/skills/lrh-work-item/references/work-item-schema.md
  - src/lrh/skills/lrh-work-item/references/work-item-body-guide.md
  - src/lrh/skills/lrh-work-item/references/lrh-work-item-workflow.md
  - .claude/skills/lrh-work-item/SKILL.md
---
```
