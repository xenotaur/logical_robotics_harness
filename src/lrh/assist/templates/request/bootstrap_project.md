# PR Request to Bootstrap LRH Project

Bootstrap an LRH `project/` directory for the target repository.

==================================================
OBJECTIVE
==================================================

You are an AI assistant tasked with creating an LRH `project/` directory for the target repository
so the repository can be interpreted and validated with the **Logical Robotics Harness** (LRH).

This request is used to generate a **pull request**, so all actions must be:
- safe
- targeted
- non-destructive
- clearly justified

Your job is to produce the **most complete standard LRH bootstrap scaffold that can be grounded in
available evidence**.

- If repository information is sufficient, create a full, useful LRH scaffold.
- If information is missing or unclear, create a minimum viable scaffold with explicit TODO/unknown
  markers rather than speculation.

This is a **bootstrap request**, not a repair or migration request.

If a `project/` directory already exists:
- DO NOT modify it
- classify it (`current_complete` / `current_incomplete` / `incompatible`)
- report findings
- DO NOT create or change any files

==================================================
INPUT CONTEXT
==================================================

REPOSITORY: {{REPO_NAME}}

PROJECT GOAL: {{PROJECT_GOAL}}

OPTIONAL BACKGROUND: {{BACKGROUND_CONTEXT}}

==================================================
CORE PRINCIPLES
==================================================

### 1. Non-Destructive Operation

- Only ADD files under: `project/`
- NEVER modify existing source code
- NEVER modify existing files under `project/`
- NEVER delete or rename files
- NEVER restructure existing directories
- NEVER overwrite existing files
- ONLY create standard LRH bootstrap artifacts when classification is `new`
- Clearly label uncertain inferences

When information is missing:
- prefer placeholders/TODO markers over invented detail
- state what is unknown and what evidence would resolve it

---

### 2. Repository Identity Verification

- Confirm the repository being modified matches `REPOSITORY`
- If mismatch or unresolved ambiguity:
  - STOP
  - report mismatch/ambiguity
  - DO NOT proceed

Verification should include:
- repository name/path
- README and/or top-level docs consistency
- project identity signals from structure/content

---

### 3. Authoritative vs Derived Artifacts

Authoritative artifacts (define intent, constraints, execution state, and truth):
- `principles/`
- `goal/`
- `roadmap/`
- `design/`
- `focus/`
- `work_items/`
- `contributors/`
- `guardrails/`
- `evidence/`
- `status/`
- `memory/`

Derived artifacts (summaries only):
- `context/humans.md`
- `context/agents.md`

Rules:
- Derived files MUST NOT introduce new commitments.
- `context/humans.md` summarizes authoritative artifacts and observed repository context for human readers.
- `context/agents.md` MUST be derived from `context/humans.md` as an agent-friendly operational summary.
- If details are uncertain, both context files must preserve uncertainty rather than inventing specifics.

---

### 4. Bootstrap Completeness Policy

For classification `new`, create as complete an LRH scaffold as can be responsibly grounded.

- Default to a full standard scaffold.
- If evidence is missing, still create the artifact with concise placeholders/TODOs.
- Do not omit standard artifacts merely because details are incomplete.
- Do not fabricate roadmap phases, contributors, or commitments.

==================================================
PHASE 1 — REPOSITORY INSPECTION
==================================================

Classify the repository:

A. `new`
- no `project/` directory exists

B. `current_complete`
- `project/` exists and appears structurally complete for LRH

C. `current_incomplete`
- `project/` exists but is missing expected LRH artifact categories/files

D. `incompatible`
- `project/` exists but structure or artifact roles conflict with LRH conventions

==================================================
PHASE 2 — ACTION POLICY
==================================================

### Case A — New Project

Create scaffold:

project/
  context/
    humans.md
    agents.md

  principles/
    principles.md

  goal/
    project_goal.md

  roadmap/
    roadmap.md

  design/
    design.md

  focus/
    current_focus.md

  work_items/
    WI-BOOTSTRAP-0001.md

  contributors/
    contributors.md

  guardrails/
    approvals.md
    safety.md
    cost.md
    optics.md

  evidence/
    EV-0001.md

  status/
    current_status.md

  memory/
    decision_log.md

### Case B — Current Complete

- Make NO changes
- Report status as `current_complete`

### Case C — Current Incomplete

- Make NO changes
- Report missing categories/files

### Case D — Incompatible

- Make NO changes
- Report concrete incompatibilities

==================================================
PHASE 3 — CONTENT GENERATION RULES
==================================================

Use inputs to seed content:

`PROJECT GOAL`
- primary source for `goal/project_goal.md`

`OPTIONAL BACKGROUND`
- informs:
  - `design/design.md`
  - `focus/current_focus.md`
  - `context/humans.md`

Repository inspection (README, docs, module structure)
- informs:
  - design summary
  - current focus hypothesis
  - guardrail emphasis
  - initial evidence/status grounding

Rules:
- If background is missing, use minimal grounded placeholders.
- Link claims to observable repo signals when possible (paths, docs, commands).
- Never present uncertain inference as confirmed fact.

==================================================
CONTENT GUIDELINES
==================================================

Use concise Markdown. Include YAML frontmatter where useful for machine readability.

Align with LRH conventions:
- precedence shape: principles → goal → roadmap → focus → work_items → evidence → status
- guardrails constrain execution and approvals
- status is evidence-backed, not aspirational prose
- memory records decisions/assumptions with rationale

### `goal/project_goal.md`

Should clearly state:
- what the project is
- what outcome it intends to produce
- who it is for
- scope boundaries (in-scope/out-of-scope)

Ground this primarily in `PROJECT GOAL` plus repository evidence.

### `design/design.md`

Should capture:
- purpose and scope
- key conceptual layers/components
- precedence/interpretation model (at high level)
- current implementation boundary vs future extensions

Prefer architecture and artifact-role clarity over implementation minutiae.

### `focus/current_focus.md`

Should identify:
- what appears to be the current bounded priority
- why that priority appears current (repo evidence)
- non-goals to keep scope disciplined
- exit criteria/checkpoints

If unclear, state uncertainty explicitly and keep focus conservative.

### `status/current_status.md`

Should summarize:
- current maturity and health
- evidence basis used for status claims
- active priorities and key risks
- immediate recommended next actions

Do not claim completion without supporting evidence.

### `memory/decision_log.md`

Should record bootstrap decisions:
- what assumptions were made
- why those assumptions were made
- uncertainty/alternatives noted
- bootstrap-specific rationale and implications

Use dated entries; keep the log auditable.

### `context/humans.md`

Human-oriented derived summary:
- plain-language project overview
- concise synthesis of goal/design/focus/status
- known unknowns and open questions

Must be self-contained and readable, but non-authoritative.

### `context/agents.md`

Agent-oriented derived summary, created from `context/humans.md`:
- mission summary
- authoritative artifact map (what to read first)
- execution constraints and guardrails
- confidence/uncertainty notes

Must remain non-authoritative and must not add commitments.

==================================================
FILE TEMPLATES
==================================================

### `goal/project_goal.md`

---
id: GOAL-CORE
title: <Project Goal Title>
status: active
owner: <owner_or_team>
time_horizon: long
---

# Project Goal

## Objective
{{PROJECT_GOAL}}

## Intended Outcome
- <observable outcomes>

## Intended Users / Stakeholders
- <users>

## In Scope
- <scope bullets>

## Out of Scope (Initial)
- <non-goals>

## Success Direction
- <how success will be recognized>

---

### `design/design.md`

# Design

## Purpose
- <what system is being built>

## Scope
- <current scope boundary>

## Core Structure
- Intent layer: principles/goal/roadmap
- Execution layer: focus/work_items/contributors
- Constraint layer: guardrails
- Truth layer: evidence/status/memory

## Precedence and Interpretation Notes
- principles → goal → roadmap → focus → work_items → guardrails/runtime context

## Current Implementation Boundary
- <what exists now>

## Future Extensions (Non-binding)
- <later capabilities>

---

### `focus/current_focus.md`

---
id: FOCUS-BOOTSTRAP
title: Initial project bootstrap focus
status: active
priority: high
owner: <owner_or_team>
---

# Current Focus

## Active Priority
- Establish an initial LRH control plane with grounded artifacts.

## Why This Appears Current
- <repo evidence>

## Priorities
1. <priority 1>
2. <priority 2>

## Non-Goals
- <bounded exclusions>

## Exit Criteria
- <conditions indicating this focus is complete>

---

### `status/current_status.md`

---
id: STATUS-CURRENT
title: Current Project Status
scope: project
status: active
health: yellow
---

# Current Status

## Summary
- <overall state>

## Evidence Basis
- <docs/files/signals used>

## Current Health
- <green/yellow/red with rationale>

## Active Priorities
- <priority bullets>

## Risks
- <risk bullets>

## Recommended Next Actions
1. <next action>
2. <next action>

---

### `memory/decision_log.md`

# Decision Log

## <YYYY-MM-DD>: Bootstrap decision

### Summary
- <decision summary>

### Decisions
- <what was decided>

### Rationale
- <why>

### Uncertainty / Follow-ups
- <unknowns and validation needed>

### Status
- Accepted (Bootstrap Phase)

---

### `context/humans.md`

# Project Context (Human-Oriented)

## One-line Description
- <plain-language description>

## Overview
- <what the repository appears to do>

## Goals and Direction
- Goal: <from project_goal>
- Near-term focus: <from current_focus>

## Design Snapshot
- <key architecture/control-plane points>

## Current Status Snapshot
- <health + immediate state>

## Known Unknowns
- <explicit uncertainties>

## Notes
- Derived summary only (non-authoritative).

==================================================
PROCESS (REQUIRED)
==================================================

Follow this strict order:

1. Verify repository identity against `REPOSITORY`.
   - If mismatch/ambiguity remains, STOP and report.
2. Check for `project/` directory.
   - If present: classify and STOP (no file changes).
3. If classification is `new`, inspect repository evidence:
   - README and top-level docs
   - key modules/directories
   - implementation signals relevant to goal/design/focus
4. Infer conservative initial control-plane content.
5. Create bootstrap artifacts under `project/` only.
6. Derive `context/humans.md` from authoritative artifacts.
7. Derive `context/agents.md` from `context/humans.md` (agent-friendly summary).
8. Generate PR description.

==================================================
PR DESCRIPTION REQUIREMENTS
==================================================

Include:
- summary of repository understanding
- classification result and action taken
- list of files created (if any)
- key assumptions
- explicit uncertainties / follow-up questions
- rationale for structure choices

==================================================
FAILURE POLICY
==================================================

Bootstrap must be atomic:

- If repository classification is not clearly `new`:
  - DO NOT create files
  - DO NOT perform partial bootstrap

Content must be grounded:

- If repository intent is unclear:
  - create minimum viable scaffold
  - annotate uncertainty in relevant artifacts
- If conflicting signals exist:
  - do not silently resolve conflict
  - document both interpretations and confidence

==================================================
ACCEPTANCE CRITERIA
==================================================

- If classification is `new`, `project/` contains the standard LRH bootstrap scaffold.
- If classification is not `new`, no files are created or changed.
- No existing files are modified.
- Content is coherent, grounded in repo evidence, and explicit about uncertainty.
- `context/agents.md` is derived from `context/humans.md` and remains non-authoritative.
- PR is narrow, auditable, and bootstrap-only.

==================================================
REQUIRED OUTPUT STRUCTURE
==================================================

Provide:

1. Repository identity verification summary
2. Classification (`new` / `current_complete` / `current_incomplete` / `incompatible`)
3. Action summary (created scaffold vs no-op classification)
4. Files created (if any)
5. Missing/Conflict report (for non-`new` classifications)
6. Assumptions and uncertainty report

==================================================
FINAL RULE
==================================================

When in doubt:

→ Do less
→ Preserve repository intent
→ Prefer explicit reporting over speculative modification


# BEGIN
