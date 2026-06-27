# LRH Design Proposal — YAML Frontmatter Field Reference

This document is the field reference for LRH design proposal YAML frontmatter.
Derived from `project/design/proposals/README.md` and validated against
`src/lrh/control/validator.py` (`DESIGN_PROPOSAL_STATUS`,
`DESIGN_PROPOSAL_IMPLEMENTATION_STATUS`, `DESIGN_PROPOSAL_LIST_FIELDS`).
See `project/design/proposals/README.md` for authoritative lifecycle semantics.

---

## Required fields

These fields are checked by `lrh validate` and must be present on every
design proposal.

| Field | Type | Constraints |
|---|---|---|
| `id` | string | Stable, unique identifier for this proposal; LRH projects conventionally use `PROP-*` form, downstream projects may use other prefixes (e.g., `DP-*`). The schema does not enforce a specific prefix — follow the project's established convention. |
| `status` | string | See status vocabulary below |
| `type` | string | Must be exactly `design_proposal`; or use `kind: design_proposal` |

`title` is not schema-required but is expected on all well-formed proposals
and is used in listings and cross-references. Always include it.

---

## Status vocabulary (`DESIGN_PROPOSAL_STATUS`)

`status` answers whether the design decision governs the project.

| Value | Meaning |
|---|---|
| `proposed` | Drafted but not yet adopted; may still change substantially |
| `adopted` | Design decision is governing; edits go through new proposals or canonical doc updates |
| `accepted` | Legacy spelling for `adopted`; validator emits a warning — prefer `adopted` |
| `superseded` | Replaced by a later proposal; set `superseded_by:` to the replacement ID |
| `rejected` | Considered and explicitly declined; kept for history |

### Status → directory bucket

| `status` | Directory |
|---|---|
| `proposed` | `project/design/proposals/proposed/` |
| `adopted` or `accepted` | `project/design/proposals/adopted/` |
| `superseded` | `project/design/proposals/superseded/` |
| `rejected` | `project/design/proposals/rejected/` |

`lrh validate` reports a warning (not error) for bucket/status mismatches.
Use `lrh design organize --apply` to move files to their correct buckets.

---

## `implementation_status` vocabulary (`DESIGN_PROPOSAL_IMPLEMENTATION_STATUS`)

`implementation_status` answers whether the governed design has been delivered.
Required for `adopted` proposals (validator emits a warning if missing).
Recommended for all proposals as a convention.

| Value | Meaning |
|---|---|
| `not_started` | Implementation not yet begun |
| `partial` | Some slices delivered; others remain |
| `implemented` | Fully delivered; back with `implemented_by` and/or `evidence` |
| `deferred` | Implementation explicitly postponed |
| `obsolete` | No longer relevant to implement |

When `implementation_status: implemented`, at least one of `implemented_by`
or `evidence` should be set — `lrh validate` emits a warning otherwise.

---

## Traceability fields (`DESIGN_PROPOSAL_LIST_FIELDS`)

These fields must be lists when present.

| Field | Type | Notes |
|---|---|---|
| `implemented_by` | list of strings | `WI-*` IDs of implementing work items |
| `evidence` | list of strings | `EV-*` IDs or paths to evidence artifacts |
| `supersedes` | list of strings | `PROP-*` IDs this proposal replaces |

Additional non-list traceability fields:

| Field | Type | Notes |
|---|---|---|
| `superseded_by` | string or null | `PROP-*` ID of the replacement proposal |
| `parent` | string or null | `PROP-*` ID of the umbrella (for sub-proposals and appendices) |

---

## Conventional fields

Not validated by the schema but present on all well-formed proposals.

| Field | Type | Notes |
|---|---|---|
| `title` | string | Short human-readable title |
| `created_on` | date | ISO 8601 (`YYYY-MM-DD`); when the proposal was drafted |
| `updated_on` | date | ISO 8601; date of last substantive edit |
| `related_design` | list of strings | File paths to related design docs, workstream files, or prior proposals |

---

## Proposal-set conventions

A proposal set is a directory under a lifecycle bucket:

```
project/design/proposals/proposed/<slug>/
  00_proposal.md      ← umbrella; no parent: field
  01_<topic>.md       ← sub-proposal; has parent: PROP-<SLUG>
  appendix_<x>.md     ← appendix; has parent: PROP-<SLUG>
  README.md           ← reading-order index (not a proposal; ignored by validator)
```

The slug should be stable and descriptive (`workstream-execution-framework`,
not `proposal-001`). The umbrella `00_proposal.md` has no `parent:` field.
Plain `index.md` files are ignored by both validation and organization.

---

## Minimum valid frontmatter

```yaml
---
id: PROP-EXAMPLE
type: design_proposal
status: proposed
---
```

## Recommended new-proposal frontmatter

```yaml
---
id: PROP-EXAMPLE
type: design_proposal
title: Short descriptive title
status: proposed
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design: []
---
```

## Full example (from an existing proposal)

```yaml
---
id: PROP-LRH-EXECUTION-SESSIONS
type: design_proposal
title: LRH Execution Sessions — Three-Phase Model and Claude.app Session Traceability
status: proposed
created_on: 2026-06-23
updated_on: 2026-06-23
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - PROMPTS.md
  - project/executions/README.md
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
  - project/design/proposals/proposed/workstream-execution-framework/00_proposal.md
---
```
