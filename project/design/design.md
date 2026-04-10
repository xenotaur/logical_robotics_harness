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
   - No hidden state outside version control

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

---

## 11. Future Extensions

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
