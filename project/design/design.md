# LRH Design Document

## 1. Purpose

The Logical Robotics Harness (LRH) is a repository-centered control plane for designing, executing, and evaluating complex projects involving humans and AI agents.

This document defines the **current system design** for LRH, serving as a bridge between:
- project goals
- guiding principles
- implementation roadmap
- active work execution

It is a **living document** and should evolve alongside the project.

---

## 2. Scope

LRH is designed to support:

- human-led and agent-assisted project development
- structured workflows from ideation to execution
- auditable, evidence-based progress tracking
- multi-contributor coordination (humans + agents)
- repository-native operation (Git as source of truth)

Out of scope (for now):

- fully autonomous project execution
- heavy UI-first workflows (CLI + repo are primary)
- rigid process enforcement

---

## 3. Users and Stakeholders

### Primary Users
- Project creators (e.g., Anthony)
- Contributors (humans and AI agents)
- Reviewers / auditors

### Secondary Users
- Future collaborators
- Tooling systems (CLI, web UI, agents)

---

## 4. Core Concepts

LRH organizes a project into structured domains:

### Intent Layer
- `principles/`
- `goal/`
- `roadmap/`

Defines **why the project exists and where it is going**

### Design Layer
- `design/`

Defines **how the system is intended to work**

### Execution Layer
- `focus/`
- `work_items/`
- `contributors/`

Defines **what is happening now and who is doing it**

### Constraint Layer
- `guardrails/`

Defines **what must not go wrong**

### Truth Layer
- `evidence/`
- `status/`
- `memory/`

Defines **what has happened and what it means**

### Workflow Layer
- `workflow/`

Defines **how projects mature over time**

### Precedence Model

LRH resolves project state using both layer authority and artifact specificity.

From lowest to highest operational authority:

1. Principles
2. Project Goal
3. Roadmap
4. Current Focus
5. Work Items
6. Guardrails
7. Explicit runtime invocation

Interpretation rules:

- Higher layers define broader intent; lower layers define more specific execution.
- More specific artifacts refine broader artifacts.
- A specific work item takes precedence over general focus prose for execution.
- Current focus takes precedence over roadmap for current operational scope.
- Guardrails do not define work, but may restrict, block, or require approval for actions.
- Explicit runtime invocation may narrow scope for a run, but does not override guardrails.

If a lower-level artifact contradicts a higher-level artifact rather than refining it,
LRH should surface a consistency warning or error.

---

## 5. Workflow Model

A typical LRH project evolves through stages:

1. Mission / Intent Formation
2. Principles Definition
3. Goal Definition
4. Initial Roadmap Creation
5. Design Development
6. Refined Roadmap
7. Current Focus Selection
8. Work Item Execution
9. Evidence Collection
10. Status Evaluation
11. Memory / Learning Capture

This process is **iterative**, not strictly linear.

---

## 6. Data Model (Repository Structure)

The `project/` directory is the canonical data model:

- Each directory represents a **semantic role**
- Each file represents a **stateful artifact**
- Markdown is the primary representation format
- Optional YAML frontmatter may encode structured metadata

---

## 7. Work Model

### Focus
Defines the current high-level priorities.

### Work Items
- Atomic units of execution
- Should be independently completable
- May be assigned to humans or agents

### Contributors
- Humans and agents both modeled explicitly
- Ownership tracked at the work-item level

---

## 8. Evidence and Status

### Evidence
- Raw outputs, results, artifacts
- Must be attributable to work items

### Status
- Synthesized interpretation of evidence
- Answers: “Where are we now?”

### Memory
- Persistent learning
- Includes decisions, lessons, open questions

---

## 9. Design Principles for LRH Itself

1. **Repository as Source of Truth**
   - Authoritative shared state belongs in version-controlled repository artifacts.
   - Local runtime state (for caches, logs, transient sessions, or local secrets) may exist, but is non-authoritative and must not silently override repository artifacts.

2. **Human-Auditable**
   - All actions traceable via files and history

3. **Agent-Compatible**
   - Structure is machine-readable and predictable

4. **Minimal Process, Maximum Clarity**
   - Avoid unnecessary bureaucracy

5. **Separation of Concerns**
   - Intent, design, execution, and evaluation are distinct

---

## 10. Contributor Model

Contributors may include:

- Humans (developers, researchers)
- AI agents (coding, analysis, evaluation)

Each work item should specify:

- owner
- contributors
- assigned agents (optional)

### Ownership Semantics

- `owner` refers to the **accountable human** responsible for the work item.
- `contributors` includes all humans and agents materially contributing to the work.
- `assigned_agents` lists agents currently authorized or expected to execute work autonomously.

Notes:
- `owner` should generally be a human contributor for accountability.
- `assigned_agents` may be empty when no autonomous agent is currently working on the item.

### Contributor Representation

Contributors are defined as separate artifacts under `contributors/`.

Each contributor has:
- a stable `id` (project-local identifier)
- a `type` (e.g., `human`, `agent`)
- one or more `roles` (e.g., `admin`, `editor`, `reviewer`, `viewer`)
- optional metadata (e.g., GitHub username, email, display name)

Contributor roles define capabilities and permissions, and are distinct from work-item relationships such as `owner`.

### Agent Execution Model

Agents are modeled as contributors with additional metadata describing their execution characteristics.

Key distinctions:
- Agents may be **human-orchestrated** (e.g., bootstrap phase)
- Agents may be **autonomously assigned** via `assigned_agents`

An agent may exist in the system without being actively assigned to any work item.

---

## 11. Future Extensions

### Workspace / Meta-Control Layer
- LRH's primary unit remains a single repository with a local `project/` control plane.
- LRH may also operate with a workspace/dashboard repository that catalogs and coordinates multiple LRH-compatible repositories.
- This workspace/meta layer is informative/coordinating relative to project-local authoritative state and does not participate in a project's precedence chain.

### Viewing Layer
- CLI summaries
- Local web UI
- Hosted project dashboards

### Automation
- Agent-driven updates
- Status synthesis
- Work item generation

### Integration
- MCP (Model Context Protocol)
- External tools (GitHub, CI/CD)

---

## 12. Open Questions

- How structured should metadata become (YAML vs freeform)?
- How to balance flexibility vs enforceability?
- What is the minimal viable viewer?
- How to manage large-scale multi-agent coordination?

---

## 13. Relationship to Other Documents

- `goal/` → defines purpose
- `principles/` → defines constraints and norms
- `roadmap/` → defines planned evolution
- `design/` → defines current system understanding (this document)
- `work_items/` → defines execution units
- `status/` → defines current state

---

## 14. Revision Policy

- This document should be updated when:
  - system structure changes
  - workflow changes
  - contributor model evolves
  - major architectural decisions are made

- Significant changes should be reflected in:
  - `memory/decision_log.md`


---

## 15. Structured Metadata Model

LRH uses Markdown as its primary human-readable format. For operational artifacts—especially `focus/` and `work_items/`—LRH uses **lightweight YAML frontmatter** to provide machine-readable metadata.
For LRH's own control plane, `focus/current_focus.md` and `work_items/WI-*.md` should include this frontmatter.

Frontmatter is intended to expose the minimum structured state needed for:

- validation
- linking and dependency resolution
- filtering and prioritization
- contributor assignment
- action planning
- evidence requirements
- status synthesis

The Markdown body remains the primary place for explanation, rationale, and discussion.
Contributors referenced in frontmatter should correspond to entries in `contributors/`.

### 15.1 Focus Schema

A focus document defines the active near-term operational charter for the project.

#### Required fields
- `id`
- `title`
- `status`

#### Recommended fields
- `owner`
- `related_roadmap`
- `start_date`
- `review_date`
- `success_criteria`
- `active_contributors`
- `priority`

#### Allowed status values
- `proposed`
- `active`
- `paused`
- `blocked`
- `completed`
- `abandoned`

#### Example

```yaml
---
id: FOCUS-BOOTSTRAP
title: Bootstrap the control plane
status: active
owner: anthony
related_roadmap:
  - ROADMAP-PHASE-01
success_criteria:
  - core schema exists
  - validation CLI works
active_contributors:
  - anthony
priority: high
---
```

---

### 15.2 Work Item Schema

A work item defines a bounded, executable unit of work.

#### Required fields
- `id`
- `title`
- `type`
- `status`

#### Recommended fields
- `priority`
- `owner`
- `contributors`
- `assigned_agents`
- `related_focus`
- `related_roadmap`
- `depends_on`
- `blocked_by`
- `expected_actions`
- `forbidden_actions`
- `acceptance`
- `required_evidence`
- `artifacts_expected`

#### Allowed types
- `deliverable`
- `investigation`
- `evaluation`
- `operation`

#### Allowed status values
- `proposed`
- `ready`
- `in_progress`
- `blocked`
- `needs_review`
- `done`
- `abandoned`

#### Example

```yaml
---
id: WI-0001
title: Implement core models
type: deliverable
status: ready
priority: high
owner: anthony
related_focus:
  - FOCUS-BOOTSTRAP
acceptance:
  - models exist
required_evidence:
  - test_result
---
```

---

### 15.3 Action Awareness

Work items may include:

- `expected_actions`
- `forbidden_actions`

These fields help connect execution planning to guardrails, but do not override guardrail enforcement.

---

### 15.4 Validation Expectations

Initial LRH validation should ensure:

- required fields are present
- IDs are unique
- references resolve (focus, roadmap, dependencies)
- enums are valid
- list fields are properly structured

Validation should be strict enough to ensure consistency, but not so strict that it blocks iteration.

---

### 15.5 Contributor and Assignment Validation

LRH should validate contributor and assignment metadata in layered passes:

1. **Parsing**
   - YAML frontmatter parses successfully
   - required metadata fields are present
   - field types are correct

2. **Per-file schema validation**
   - contributor records have valid required fields
   - work items have valid required fields
   - enum values are valid

3. **Cross-reference validation**
   - contributor IDs are unique
   - `owner` references an existing contributor
   - `contributors` entries reference existing contributors
   - `assigned_agents` entries reference existing contributors

4. **Semantic policy validation**
   - `owner` must reference a human contributor
   - `contributors` may reference humans and agents
   - `assigned_agents` must reference agent contributors
   - `owner` should normally also appear in `contributors`
   - agents may exist without active assignment
   - human-orchestrated agents are distinct from autonomously assigned agents

#### Contributor Schema Expectations

Contributor artifacts under `contributors/` should support the following fields:

##### Required fields
- `id`
- `type`
- `roles`
- `display_name`
- `status`

##### Allowed contributor types
- `human`
- `agent`

##### Allowed contributor status values
- `active`
- `inactive`
- `archived`

##### Allowed contributor roles
- `admin`
- `editor`
- `reviewer`
- `viewer`

##### Recommended optional fields
- `email`
- `github`
- `execution_mode`
- `description`

#### Agent Metadata Expectations

If a contributor has `type: agent`, the contributor may also define an execution mode.

Recommended execution modes:
- `human_orchestrated`
- `autonomous`
- `disabled`

An agent may exist in the system without being actively assigned to any work item.

#### Work Item Ownership and Assignment Rules

The following validation rules should apply to contributor-related work item metadata:

- `owner` is required and must reference a contributor of type `human`
- `contributors`, if present, must be a list of contributor IDs
- `assigned_agents`, if present, must be a list of contributor IDs of type `agent`
- a contributor referenced in `assigned_agents` should normally have a role that permits execution (for example, `editor`)
- a contributor referenced as `owner` should normally have a role that permits ownership and initiation of work (for example, `editor` or `admin`)
- an agent with `execution_mode: human_orchestrated` may exist as a contributor but should not normally appear in `assigned_agents` without an explicit warning

#### Validation Severity Model

Validation results should be classified into at least three levels:

- `error` — invalid and should fail validation
- `warning` — suspicious or incomplete but still loadable
- `info` — notable but acceptable

Recommended `error` cases:
- invalid YAML
- missing required fields
- duplicate contributor IDs
- unknown `owner`
- unknown contributor in `contributors`
- unknown contributor in `assigned_agents`
- `owner` references a non-human contributor
- `assigned_agents` contains a non-agent contributor

Recommended `warning` cases:
- `owner` is not listed in `contributors`
- an agent contributor is missing `execution_mode`
- an assigned agent is `inactive`
- an assigned agent has `execution_mode: human_orchestrated`
- an owner lacks a role normally associated with owning work
- an assigned agent lacks a role normally associated with execution

#### Bootstrap-Phase Interpretation

During bootstrap, LRH may include agent contributors that are defined but not autonomously assigned.

For example:
- a bootstrap agent may exist as a contributor artifact
- it may be referenced in `contributors`
- it may remain absent from `assigned_agents`
- this should validate cleanly

This allows LRH to model human-orchestrated AI assistance before introducing autonomous agent assignment.
