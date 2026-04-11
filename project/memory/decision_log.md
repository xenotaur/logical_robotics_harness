# Decision Log

## 2026-04-11: Decision: Contributor and Assignment Validation Model

### Summary

Defined the formal validation model for contributor records, work-item ownership, and agent assignment.

### Decisions

- LRH validates contributor alignment in four passes:
  1. parsing
  2. per-file schema validation
  3. cross-reference validation
  4. semantic policy validation

- Contributor records under `contributors/` must define:
  - `id`
  - `type`
  - `roles`
  - `display_name`
  - `status`

- `owner` must reference a human contributor.
- `contributors` may reference both human and agent contributors.
- `assigned_agents` must reference agent contributors only.

- Agent contributors may define an `execution_mode`, including:
  - `human_orchestrated`
  - `autonomous`
  - `disabled`

- Human-orchestrated agents may exist in the system without being actively assigned to work items.

### Rationale

- Turns contributor and ownership semantics into enforceable validation behavior
- Preserves auditability by requiring human accountability for work-item ownership
- Separates participation from execution responsibility
- Supports a bootstrap phase where AI assistance exists before autonomous agent orchestration

### Implications

- LRH can automatically evaluate the alignment of `contributors/` and `work_items/`
- Validation tooling can distinguish hard failures from warnings
- Future UI, CI, and orchestration layers can rely on stable contributor/assignment semantics
- Bootstrap-style agents can be modeled cleanly without being treated as autonomous workers

### Status

Accepted (Bootstrap Phase)

## 2026-04-11: Decision: Contributor and Ownership Semantics

### Summary

Defined clear semantics for contributor representation and work-item ownership.

### Decisions

- `owner` refers to the **accountable human** responsible for a work item.
- `contributors` includes all humans and agents materially contributing.
- `assigned_agents` lists agents currently authorized or expected to execute work autonomously.

- Contributors are defined as separate artifacts under `contributors/`.
- Contributors have:
  - stable project-local `id`
  - `type` (`human` or `agent`)
  - one or more `roles` (e.g., `admin`, `editor`, `reviewer`, `viewer`)

- Agents are modeled as contributors and may have execution modes such as:
  - human-orchestrated (e.g., bootstrap phase)
  - autonomous (future)

### Rationale

- Separates accountability (owner) from participation (contributors) and execution (assigned_agents)
- Improves auditability and clarity of responsibility
- Aligns with repository-based workflows and future multi-agent coordination
- Avoids ambiguity introduced by using `owner: agent`

### Implications

- All work items should use human identifiers for `owner`
- Contributor identities must be defined in `contributors/`
- Future tooling (validation, UI, agents) can rely on these semantics
- Enables gradual evolution toward autonomous agent assignment without breaking model

### Status

Accepted (Bootstrap Phase)

## 2026-04-03: Decision: Top-Level Schema Definition
Adopted the top-level schema:

Principles → Project Goal → Roadmap → Current Focus → Work Items → Actions → Evidence → Status (+ Guardrails)

Reason:
This separates intent, execution, and truth more clearly than a milestone/sprint/task-only model.

## 2026-04-03: Decision: Defining Top-Level Control as project/s
Renamed `control/` to `project/`.

Reason:
This is friendlier for humans and fits better in client repositories.
