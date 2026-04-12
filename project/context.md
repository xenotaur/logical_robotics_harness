# Logical Robotics Harness (LRH)

## One-line Description
A repository-centered control plane for designing, executing, and evaluating structured, evidence-backed, agent-assisted work.

## Abstract
The Logical Robotics Harness (LRH) is an open-source framework that turns a Git repository into a **human-auditable, machine-interpretable project control system**. It enables projects to express intent (principles, goals, roadmap), execute work (focus, work items), and capture truth (evidence, status) in a structured, Markdown-first format.

LRH is designed for **AI-assisted engineering workflows**, where humans and agents collaborate through explicit artifacts rather than implicit context. By combining structured metadata (YAML frontmatter), validation, and a defined precedence model, LRH ensures that project state is both interpretable and enforceable.

The system begins by being able to **understand and validate itself** (self-hosting control plane), then evolves toward orchestrating multiple repositories and agents.

---

# Core Concepts

## Control Planes

### Intent Plane
- Principles
- Project Goal
- Roadmap

### Execution Plane
- Current Focus
- Work Items

### Truth Plane
- Evidence
- Status

### Consequences Plane
- Safety
- Cost
- Optics

---

# Precedence Model

LRH resolves project state using:

## Authority (low → high)
1. Principles
2. Project Goal
3. Roadmap
4. Current Focus
5. Work Items
6. Guardrails
7. Runtime invocation

## Rules
- Lower layers refine higher layers
- Work items override focus for execution
- Focus overrides roadmap for current work
- Guardrails constrain but do not define work
- Runtime invocation narrows scope but respects guardrails

---

# Repository Structure

```
project/
  principles/
  goal/
  roadmap/
  design/
  focus/
  work_items/
  evidence/
  status/
  contributors/
  guardrails/
  memory/
```

Each artifact is Markdown with optional YAML frontmatter.

---

# Workflow

A typical lifecycle:

1. Principles defined
2. Project Goal established
3. Roadmap created
4. Design developed
5. Current Focus selected
6. Work Items executed
7. Evidence collected
8. Status updated

---

# Roadmap

## Phase 1 — Control Plane
- Define schema
- Implement parser and validator
- Establish precedence model
- Validate LRH against itself

## Phase 2 — Runtime & Workspace
- External project support
- Workspace abstraction

## Phase 3 — Execution & Evidence
- Work item execution
- Evidence capture

## Phase 4 — Agent Integration
- Multi-agent workflows
- MCP integration

---

# Current State (as of conversation)

LRH can:
- Parse and validate its own project directory
- Represent structured project state
- Define precedence model
- Generate project snapshots

Remaining Phase 1 work:
- Implement precedence resolver
- Validate semantic interpretation
- Harden YAML parsing
- Upgrade snapshot to resolved context

---

# Design Principles

## 1. Repository as Control Plane
The repository is the source of truth.

## 2. Human-Auditable, Machine-Readable
All artifacts must be readable by humans and interpretable by machines.

## 3. Explicit Structure
Avoid implicit state; prefer explicit metadata.

## 4. Separation of Concerns
Intent, execution, truth, and consequences are separated.

## 5. Incremental Evolution
Start with validation; expand to orchestration.

---

# Evaluation Criteria

LRH must demonstrate it can:
- Parse project structure
- Resolve precedence
- Identify current focus
- Interpret work items
- Track evidence and status

---

# Future Directions

- Multi-repo orchestration
- Agent-to-agent communication
- Web-based visualization
- Automated workflow execution

---

# Summary

LRH transforms project management into a **structured, verifiable, and agent-compatible system**. It bridges human intent and machine execution through explicit artifacts, enabling scalable and auditable AI-assisted development.
