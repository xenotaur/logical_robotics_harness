# Logical Robotics Harness (LRH)

## One-line Description
A repository-centered control plane for designing, executing, and evaluating structured, evidence-backed, agent-assisted work.

## Abstract
The Logical Robotics Harness (LRH) is an open-source framework that turns a Git repository into a **human-auditable, machine-interpretable project control system**. It enables projects to express intent (principles, goals, roadmap), execute work (focus, work items), and capture truth (evidence, status) in a structured, Markdown-first format.

LRH is designed for **AI-assisted engineering workflows**, where humans and agents collaborate through explicit artifacts rather than implicit context. By combining structured metadata (YAML frontmatter), validation, and a defined precedence model, LRH ensures that project state is both interpretable and enforceable.

The system begins by being able to **understand and validate itself** (self-hosting control plane), then evolves toward multiple repositories and agents. As part of that evolution, LRH can use a workspace/dashboard layer to help humans and tools discover, inspect, and coordinate active LRH projects, while each project's local `project/` directory remains authoritative.

## LRH in One Page

The Logical Robotics Harness (LRH) is both a **software system** and a **development philosophy**.

It augments a repository with structured Markdown + YAML metadata that makes project state:

- explicit  
- interpretable  
- actionable  

This enables both **humans and AI agents** to understand a project, decide what to do next, and execute work in a controlled and auditable way.

---

### What an LRH Project Looks Like

An LRH-compatible repository contains a `project/` directory:

- A set of Markdown files describing:
  - **intent** (principles, goal, roadmap)
  - **execution** (focus, work items)
  - **truth** (evidence, status)

Together, these form a **declarative model of the project**.

---

### What LRH Does Today

The LRH toolkit currently provides three core capabilities:

1. **Validate** → Is the project structurally and semantically correct?  
2. **Interpret** → What is actually happening in the project right now?  
3. **Guide** → What actions are valid and should happen next?  

These are driven by a deterministic interpretation of project state.

---

### What LRH Is Becoming

LRH is evolving toward a fully agent-capable control loop:

4. **Automate** → Execute the next valid actions  
5. **Evaluate** → Assess outcomes against goals and evidence  
6. **Control** → Iterate until objectives are satisfied  
7. **Enforce Safety** → Prevent unsafe or invalid actions  

---

### The Core Mechanism: Precedence

All interpretation and decision-making are governed by precedence:

```
principles > goal > roadmap > focus > work_items > guardrails > runtime
```

This ensures that:

- execution stays aligned with intent  
- lower-level actions cannot violate higher-level constraints  
- decisions are consistent and deterministic  

---

### The Big Idea

LRH turns a repository from:

> a collection of files and intentions  

into:

> a **declarative control system** that can guide its own execution  

---

### The End Goal

The long-term goal of LRH is to enable a **closed-loop development system**:

1. Define principles and goals  
2. Derive roadmap and focus  
3. Execute work via agents or humans  
4. Collect evidence and evaluate results  
5. Iterate safely until objectives are achieved  

This creates a workflow that is:

- explicit  
- auditable  
- reproducible  
- scalable to human–AI collaboration  

# Philosophy / Why LRH Exists

Modern software and research projects increasingly involve:

- multiple contributors (human and AI)
- complex, evolving goals
- implicit assumptions and hidden state
- difficulty in understanding “what is going on”

As systems grow, this leads to:

- ambiguity in decision-making  
- drift between intent and execution  
- lack of auditability  
- fragile collaboration between humans and AI agents  

---

## The Core Problem

Most projects lack a **clear, structured representation of their own state**.

Key questions become difficult to answer:

- What are we trying to do right now?
- Why are we doing it?
- What should happen next?
- How do we know if something is complete?
- What constraints apply?

These answers are often:

- scattered across documents  
- implicit in code  
- stored only in human memory  

This makes reliable automation—and even basic coordination—difficult.

---

## The LRH Approach

The Logical Robotics Harness (LRH) addresses this by treating a project as a **declarative control system**.

Instead of relying on:

- implicit knowledge  
- ad hoc processes  

LRH requires that all key elements be:

- explicit  
- structured  
- version-controlled  
- interpretable  

It introduces:

- **control planes** to separate kinds of information  
- a **precedence model** to resolve conflicts  
- a **validation model** to ensure correctness  
- an **interpretation (snapshot) model** to produce actionable state  

---

## Guiding Principles

LRH is built on a few core ideas:

### 1. Explicit State Over Implicit Knowledge

Everything that matters should be:

- written down  
- structured  
- inspectable  

---

### 2. Interpretation Over Assumption

The system should not assume meaning.

Instead, it should:

- interpret artifacts  
- derive state  
- justify conclusions  

---

### 3. Evidence Over Assertion

Claims such as “this is complete” must be supported by:

- concrete evidence  
- verifiable outputs  

---

### 4. Determinism Over Ambiguity

Given the same project state, LRH should:

- produce the same validation results  
- produce the same snapshot  

This enables:

- trust  
- reproducibility  
- automation  

---

### 5. Human–AI Symmetry

The system should be equally usable by:

- humans  
- AI agents  

This requires:

- clear structure  
- minimal hidden context  
- consistent interpretation  

---

## What LRH Enables

By making project state explicit and interpretable, LRH enables:

- **Reliable execution guidance**  
- **Auditable decision-making**  
- **Scalable collaboration**  
- **AI-assisted development without loss of control**  

---

## Key Insight

LRH is not just a tool—it is a **way of structuring work**.

It transforms a project from:

> a collection of files and intentions  

into:

> a coherent, interpretable system that can guide its own execution  

---

## Summary

LRH exists to solve a fundamental problem:

> How do we make complex projects understandable, controllable, and automatable?

Its answer is:

- make everything explicit  
- validate it rigorously  
- interpret it deterministically  

and use that to drive execution.

---

# Core Concepts

The Logical Robotics Harness (LRH) organizes a project into a set of **control planes**: 

- Intent Plane
  - Principles
  - Project Goal
  - Roadmap
- Execution Plane
  - Current Focus
  - Work Items
  - Context
- Truth Plane
  - Evidence
  - Status
- Consequences Plane
  - Safety
  - Cost
  - Optics

Each plane represents a different *kind of information* and a different *role in decision-making*. This separation is critical: it allows LRH to distinguish between:

- what we *intend*
- what we are *doing*
- what is *actually true*
- what the *consequences* are

These planes are not independent—they are evaluated together through the **precedence model**, which determines how conflicts are resolved and how project state is interpreted.

---

## Control Planes

### Intent Plane

The Intent Plane defines **why the project exists and what it is trying to achieve**.  
It provides the highest-level guidance and is the most stable part of the system.

It answers questions like:

- What are we building?
- What does success look like?
- What principles constrain our decisions?

The Intent Plane consists of:

#### Principles

Principles are **normative constraints** on the system.

They define:
- what is allowed
- what is forbidden
- what tradeoffs are acceptable

Examples:
- “The system must be auditable”
- “Validation must be deterministic”
- “Human-readable artifacts are first-class”

Principles are:
- **global** (apply everywhere)
- **long-lived**
- **high precedence**

They are not implementation details—they are **design invariants**.

---

#### Project Goal

The Project Goal defines **the desired end state of the project**.

It is more concrete than principles, but still high-level. It typically includes:

- a description of the system’s purpose
- success criteria
- scope boundaries

For LRH, an example goal might be:

> “Create a control-plane-driven system that can validate and interpret its own project state and guide execution.”

The goal acts as:
- a **target for evaluation**
- a **constraint on roadmap decisions**
- a **reference point for resolving ambiguity**

---

#### Roadmap

The Roadmap defines **how the project intends to reach its goal over time**.

It introduces:
- phases
- sequencing
- prioritization at a coarse level

The roadmap is:
- more flexible than the goal
- allowed to evolve
- structured but not overly rigid

Importantly, the roadmap does **not** directly control execution.  
Instead, it informs the **Current Focus**, which is the active slice of work.

---

### Execution Plane

The Execution Plane defines **what is actively being worked on right now**.

It translates intent into **concrete, actionable units of work**.

It answers questions like:

- What should be done next?
- What is currently in scope?
- What constitutes completion?

The Execution Plane consists of:

---

#### Current Focus

The Current Focus defines the **active scope of work**.

It is the *bridge* between the roadmap and the work items.

A focus typically includes:

- a description of the current effort
- explicit priorities
- exit criteria (how we know we are done)

Key properties:

- Only **one focus should be active at a time**
- It is **narrow and testable**
- It is **temporary**

The focus acts as a **filter**:
- It determines which work items are relevant
- It constrains what agents should work on

---

#### Work Items

Work Items are the **atomic units of execution**.

Each work item represents:

- a specific task
- with clear acceptance criteria
- and expected outputs

They are:

- **small** (relative to the focus)
- **testable**
- **composable**

Work items may include:

- dependencies
- required evidence
- expected actions
- constraints on behavior

Crucially, work items are **not all active at once**.

They become active only when:
- they are consistent with the current focus
- and allowed by higher-precedence constraints

---

#### Context

Context is an execution-adjacent interface artifact. It supports contributors in understanding and
acting on the project, but does not itself define authoritative project state. In cases where
LRH's execution model is not sufficient, such as bootstrapping, it helps contributors proceed.

Particlarly, sometimes we need to prompt a system outside the LRH flow. The context documents can
serve to seed the project before goals, designs, roadmaps or the current focus are settled; they
can also serve as a snapshot of the overall system state through the current focus.

There are generally at least two elements of context:

- humans.md describes the project in detail for a human contributor
- agents.md summarizes humans.md in a tight packet suitable as part of an agent prompt.

Generally, the humans.md can be iteratively worked on by contributors and agents and should be
updated as the goals, design, roadmap or focus change.

The agents.md should ideally be derived from humans.md and other authoritative project artifacts
using a standardized process, and should remain reviewable and version-controlled.

Context items are:
- **global** to the project
- **derived** from project goals, design, roadmap and focus
- **informative** rather than authoritative
- **outside** the preference hierachy

Before the rest of the project exists, the humans.md can be used as a project proposal,
which is then used to help seed the rest of the project.

---

### Truth Plane

The Truth Plane represents **what is actually known to be true about the system**.

It is the grounding layer that prevents the system from becoming purely speculative or declarative.

It answers:

- What has actually been done?
- What evidence supports that?
- What is the current state of the system?

The Truth Plane consists of:

---

#### Evidence

Evidence is **verifiable output produced by execution**.

Examples include:

- test results
- logs
- generated artifacts
- reports

Evidence must be:

- **concrete**
- **inspectable**
- **reproducible (ideally)**

Evidence is used to:
- validate that work items are complete
- support claims about system state
- enable auditing

---

#### Status

Status is the **interpreted state of the project**, derived from:

- intent
- execution
- evidence

It is not just a label like “done” or “in progress”—it is a **reasoned conclusion**.

For example:

- A work item may be “complete” only if:
  - acceptance criteria are satisfied
  - required evidence exists
- A focus may be “complete” only if:
  - exit criteria are met

Status is therefore:

- **derived**, not declared
- **dependent on evidence**
- **subject to validation**

---

### Consequences Plane

The Consequences Plane captures **what happens as a result of decisions and actions**.

It ensures that the system is not only correct, but also:

- safe
- efficient
- appropriate in context

It answers:

- What risks are introduced?
- What costs are incurred?
- How will this be perceived?

This plane becomes increasingly important as the system scales or interacts with real-world stakeholders.

It consists of:

---

#### Safety

Safety addresses:

- correctness risks
- system integrity
- unintended harmful behavior

Examples:

- invalid state transitions
- unsafe automation
- destructive actions without safeguards

Safety constraints may:

- block execution
- trigger warnings
- require additional validation

---

#### Cost

Cost includes:

- computational cost
- human effort
- time
- resource usage

LRH does not assume cost is negligible.

Instead, it enables reasoning such as:

- “Is this work item worth executing now?”
- “Should we defer this due to cost?”

---

#### Optics

Optics refers to:

- how decisions appear to stakeholders
- clarity of communication
- auditability and transparency

Examples:

- Is the system understandable?
- Can decisions be explained?
- Are outputs interpretable?

This is especially important for:

- collaboration
- governance
- AI-assisted workflows

---

## Why the Planes Matter

These planes allow LRH to:

1. Separate **intent from execution**
2. Ground decisions in **evidence**
3. Evaluate outcomes in terms of **consequences**
4. Resolve conflicts using **precedence**

Without this structure:

- systems become ambiguous
- decisions become ad hoc
- validation becomes shallow

With it:

- the project becomes **interpretable**
- execution becomes **guided**
- the system becomes **auditable and extensible**

---

## Relationship to the Precedence Model

All planes are evaluated together through the precedence model:

```
principles > goal > roadmap > focus > work_items > guardrails > runtime
```

This ensures that:

- lower-level decisions cannot violate higher-level intent
- execution remains aligned with goals
- interpretation is consistent and deterministic
---

# Precedence Model

The Logical Robotics Harness (LRH) determines what is *true*, *active*, and *allowed* in a project through a structured **precedence model**. This precedence model resolves project state using:

- Authority (low → high)
  1. Principles
  2. Project Goal
  3. Roadmap
  4. Current Focus
  5. Work Items
  6. Guardrails
  7. Runtime invocation
- Rules
  - Lower layers refine higher layers
  - Work items override focus for execution
  - Focus overrides roadmap for current work
  - Guardrails constrain but do not define work
  - Runtime invocation narrows scope but respects guardrails

This model defines how different sources of information—principles, goals, roadmap, focus, work items, and runtime inputs—interact when they overlap or conflict.

Without a precedence model, a system of declarative files becomes ambiguous.  
With it, LRH becomes a **deterministic interpreter of project state**.

---

## Purpose of the Precedence Model

The precedence model answers questions such as:

- Which work items are actually in scope right now?
- What should be done next?
- What constraints apply to a given action?
- What happens if two sources of truth disagree?

It ensures that:

- higher-level intent is never violated by lower-level execution
- ambiguity is resolved consistently
- the system can be interpreted by both humans and AI agents

---

## Authority Ordering (Low → High)

The precedence model is defined as a strict ordering of authority:

1. Principles  
2. Project Goal  
3. Roadmap  
4. Current Focus  
5. Work Items  
6. Guardrails  
7. Runtime Invocation  

Higher levels take precedence over lower levels when conflicts arise.

---

## Layer Definitions and Roles

### 1. Principles

**Role:** Global invariants and constraints

Principles define what is fundamentally allowed or disallowed in the system.  
They are the highest authority and cannot be overridden.

They constrain:
- goals
- roadmap decisions
- execution behavior

If a lower layer violates a principle, it is **invalid**, regardless of intent.

---

### 2. Project Goal

**Role:** Defines success and scope boundaries

The project goal specifies what the system is trying to achieve.

It constrains:
- roadmap structure
- acceptable focus areas
- valid work items

A goal cannot violate principles, but it may refine or interpret them.

---

### 3. Roadmap

**Role:** Strategic sequencing and phase structure

The roadmap defines how the project intends to reach the goal over time.

It introduces:
- phases
- ordering of efforts
- coarse prioritization

The roadmap guides focus selection, but does not directly control execution.

---

### 4. Current Focus

**Role:** Active scope of work

The current focus defines what the system is working on *right now*.

It:
- selects a subset of roadmap intent
- activates relevant work items
- defines exit criteria

Focus overrides roadmap for immediate execution decisions.

---

### 5. Work Items

**Role:** Concrete executable tasks

Work items define specific units of work.

They:
- operationalize the focus
- provide acceptance criteria
- generate evidence

Work items override focus in terms of *how work is performed*, but not *what is allowed*.

---

### 6. Guardrails

**Role:** Dynamic constraints on execution

Guardrails define safety, cost, or policy constraints that apply during execution.

They:
- restrict actions
- enforce safety conditions
- may block or modify execution

Guardrails do not define what work should be done—they constrain *how* it is done.

---

### 7. Runtime Invocation

**Role:** Immediate execution context

Runtime invocation includes:

- CLI arguments (e.g., `lrh validate`, `lrh snapshot`)
- agent-specific context
- user instructions

It narrows scope for a specific execution, but must respect all higher-level constraints.

---

## Core Rules of Precedence

### Rule 1: Higher Layers Constrain Lower Layers

Each layer must be consistent with all higher layers.

- A work item must respect the focus, roadmap, goal, and principles
- A focus must respect the roadmap, goal, and principles

Violations result in:
- validation errors
- or exclusion from active interpretation

---

### Rule 2: Lower Layers Refine Higher Layers

Lower layers provide increasing specificity.

- Principles define invariants
- Goals define targets
- Roadmaps define structure
- Focus defines current scope
- Work items define execution

This creates a progression from **abstract → concrete**.

---

### Rule 3: Focus Overrides Roadmap for Execution

The roadmap defines *possible* work.  
The focus defines *current* work.

If a work item is consistent with the roadmap but not the current focus:

→ it is **not active**

---

### Rule 4: Work Items Define Execution Details

The focus determines *what to work on*,  
but work items determine *how to do it*.

Work items may:

- specify actions
- define required evidence
- constrain execution details

However, they cannot violate higher-level constraints.

---

### Rule 5: Guardrails Constrain, Not Define

Guardrails do not introduce new work.

They:

- restrict execution
- enforce policies
- add safety or cost considerations

If a work item violates a guardrail:

→ it must be modified, deferred, or rejected

---

### Rule 6: Runtime Invocation Narrows Scope

Runtime inputs (e.g., CLI commands) define what operation is being performed.

Examples:

- `lrh validate` → structural validation
- `lrh snapshot` → interpret project state

Runtime invocation:

- selects a *view* or *operation*
- does not override constraints from other layers

---

## Conflict Resolution

When two layers appear to disagree:

1. Identify the layers involved
2. Apply precedence ordering
3. Discard or flag the lower-precedence interpretation

Example:

- A work item suggests an action
- A guardrail forbids it

→ The action is invalid

---

## Determinism Requirement

The precedence model must be:

- deterministic
- reproducible
- explainable

Given the same project state, LRH must always produce the same interpretation.

This is critical for:

- testing
- auditing
- AI agent reliability

---

## Relationship to Validation and Interpretation

The precedence model underlies both:

### Validation

Validation checks:

- structural correctness
- consistency across layers

Example:
- A work item outside the current focus may trigger a warning

---

### Interpretation

Interpretation determines:

- active work items
- current focus
- system status

This is exposed via:

- `lrh snapshot`
- internal resolution logic

---

## Example

Given:

- Roadmap includes Phase 1 and Phase 2
- Current focus is Phase 1
- Work item belongs to Phase 2

Result:

- Work item is valid (roadmap-consistent)
- But not active (focus-inconsistent)

---

## Why This Matters

The precedence model transforms LRH from:

- a collection of files

into:

- a **coherent, interpretable control system**

It enables:

- reliable automation
- explainable decisions
- alignment between intent and execution

---

# Repository Structure

The Logical Robotics Harness (LRH) organizes all project-relevant information inside a standardized `project/` directory with the following top-level layout:

```
project/
  context/
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

Each artifact is written in **Markdown**, optionally containing **YAML frontmatter** for structured data.

This structure is not merely organizational—it is **semantic**. Each directory corresponds to a role in the control-plane model and participates in validation, interpretation, and precedence resolution.

---

## Design Philosophy

The repository structure is designed to satisfy several key goals:

### 1. Human Readability

All artifacts should be understandable as plain Markdown:
- readable in GitHub
- editable without special tooling
- suitable for discussion and review

### 2. Machine Interpretability

The same files must also be:
- parseable
- validatable
- interpretable by LRH

This is achieved through:
- optional YAML frontmatter
- consistent schemas
- predictable locations

---

### 3. Separation of Concerns

Each directory corresponds to a **distinct conceptual role**:

- Intent (why)
- Execution (what now)
- Truth (what is true)
- Consequences (what matters)

This enables:
- clean validation
- deterministic interpretation
- composable tooling

---

### 4. Auditable State

All project state is:
- explicit
- version-controlled
- inspectable

There is no hidden state.

---

## Directory Breakdown

### context/

Defines derived, human- and agent-facing context for the project.

Contents:
- humans.md documenting the project for people
- agents.md which can serve as a seed for a prompt.

Properties:
- global to the project
- derived, not a source of truth
- informative, not authoritative
- not factored into the preference hierarchy
- should be regenerated or reviewed whenever authoritative project artifacts such as goal, design,
  roadmap, focus, or work items change.
- can serve as a seed for the project or as prompt background

### principles/

Defines **global invariants** and constraints.

Contents:
- high-level rules
- normative constraints
- design philosophy

Properties:
- highest precedence
- rarely changed
- applies globally

---

### goal/

Defines the **project’s objective**.

Contents:
- project_goal.md

Includes:
- purpose
- success criteria
- scope boundaries

---

### roadmap/

Defines **long-term sequencing**.

Contents:
- phases
- milestones
- coarse priorities

Notes:
- informs focus
- not directly executable

---

### design/

Defines **system architecture and concepts**.

Contents:
- design.md
- supporting design docs

Includes:
- control planes
- precedence model
- validation model

---

### focus/

Defines the **current active effort**.

Contents:
- current_focus.md
- optionally archived focuses

Includes:
- priorities
- exit criteria
- scope definition

Key constraint:
- only one active focus

---

### work_items/

Defines **atomic units of execution**.

Each file:
- represents a task
- includes acceptance criteria
- may include dependencies

Work items are:
- activated by focus
- validated via evidence

---

### evidence/

Stores **outputs of execution**.

Examples:
- test results
- logs
- generated artifacts

Properties:
- concrete
- inspectable
- supports validation

---

### status/

Represents **interpreted project state**.

Derived from:
- intent
- execution
- evidence

May include:
- reports
- summaries
- computed state

---

### contributors/

Defines **agents and roles**.

Examples:
- humans
- AI agents

Includes:
- responsibilities
- capabilities
- assignments (optional)

---

### guardrails/

Defines **constraints on execution**.

Examples:
- safety constraints
- forbidden actions
- operational limits

Properties:
- constrain behavior
- do not define goals

---

### memory/

Stores **historical and contextual information**.

Examples:
- past focuses
- decision logs
- archived work

Purpose:
- provide continuity
- support reasoning over time

---

## Artifact Format

Each file is:

- Markdown for human readability
- optionally includes YAML frontmatter for structure

Example:

```markdown
---
id: WI-EXAMPLE
status: proposed
---

## Summary

Example work item.
```

---

## How LRH Uses This Structure

LRH performs three key operations:

### 1. Validation

Checks:
- schema compliance
- required fields
- structural consistency

---

### 2. Interpretation

Determines:
- current focus
- active work items
- system state

---

### 3. Resolution

Applies precedence to:
- resolve conflicts
- determine valid actions
- guide execution

---

## Minimal Viable Structure

A minimal working LRH project requires:

```
project/
  goal/
  design/
  focus/
  work_items/
```

With:

- valid Markdown files
- coherent relationships
- successful validation

---

## Summary

The repository structure is:

- a **data model**
- a **control system**
- an **interface between humans and AI**

It is the foundation on which all LRH behavior is built.

---

# Workflow

The Logical Robotics Harness (LRH) defines a structured, iterative workflow that transforms high-level intent into validated, evidence-backed execution. A typical lifecycle includes:

1. Principles defined
2. Project Goal established
3. Roadmap created
4. Design developed
5. Current Focus selected
6. Work Items executed
7. Evidence collected
8. Status updated

This workflow is not strictly linear; in practice this process should be:

- iterative
- self-correcting
- grounded in validation and interpretation

The goal is to create a framework for a **controlled loop** in which each stage informs and constrains the others through the precedence model.

---

## Detailed Workflow Stages

### 1. Principles Defined

The workflow begins by establishing **principles**, which act as global invariants.

These define:
- what is allowed
- what is forbidden
- what tradeoffs are acceptable

This step is foundational because:

- all future decisions must comply with principles
- violations at lower levels must be detected and rejected

Principles are rarely modified once established.

---

### 2. Project Goal Established

Next, the **project goal** defines the desired outcome.

This includes:
- purpose
- success criteria
- scope boundaries

The goal translates abstract principles into a **target state**.

All roadmap decisions and execution choices should be evaluated relative to this goal.

---

### 3. Roadmap Created

The roadmap defines a **coarse-grained plan** for reaching the goal.

It introduces:
- phases
- sequencing
- high-level priorities

Important characteristics:

- It is directional, not prescriptive
- It may evolve as new information is discovered
- It does not directly drive execution

Instead, it informs the selection of the **Current Focus**.

---

### 4. Design Developed

The design specifies **how the system works**.

This includes:
- architecture
- control planes
- precedence model
- validation rules

The design serves two roles:

1. A **human explanation** of the system  
2. A **reference for implementation and validation**

Design is expected to evolve, especially early in the project.

---

### 5. Current Focus Selected

The **Current Focus** defines the active scope of work.

It is derived from:
- roadmap priorities
- project needs
- current system state

A focus includes:
- a clear objective
- priorities
- exit criteria

Key constraint:

> Only one focus should be active at a time.

This ensures:
- clarity
- bounded scope
- testability

---

### 6. Work Items Executed

Work items are selected and executed within the constraints of the current focus.

Each work item:
- represents a specific task
- has acceptance criteria
- produces expected outputs

Execution may be performed by:
- human contributors
- AI agents

During execution:

- precedence rules must be respected
- guardrails must not be violated
- actions must align with focus and goal

---

### 7. Evidence Collected

Execution produces **evidence**, which is required to support claims of completion.

Examples:

- test results
- logs
- generated artifacts
- reports

Evidence must be:

- concrete
- inspectable
- relevant to acceptance criteria

Without evidence, completion is not considered valid.

---

### 8. Status Updated

Status is derived from:

- work item definitions
- collected evidence
- validation rules

Status is not manually declared—it is **interpreted**.

Examples:

- A work item is complete if:
  - acceptance criteria are satisfied
  - required evidence exists

- A focus is complete if:
  - exit criteria are met

Status updates may:

- advance the workflow
- trigger new focus selection
- reveal inconsistencies

---

## The Workflow Loop

After status is updated, the system evaluates:

- Are focus exit criteria satisfied?
- Are there remaining in-scope work items?
- Does the roadmap need adjustment?

This leads to:

- continuing the current focus  
or  
- selecting a new focus  

Thus, the workflow forms a loop:

```
focus → work → evidence → status → (re-evaluate focus)
```

---

## Role of LRH Commands

The workflow is operationalized through LRH tooling:

### Validation

```
lrh validate
```

Ensures:
- structural correctness
- schema compliance
- internal consistency

---

### Snapshot / Interpretation

```
lrh snapshot
```

Produces:
- current focus
- active work items
- interpreted status
- warnings or inconsistencies

This is the **primary interface** for both humans and AI agents.

---

## Key Properties of the Workflow

### 1. Declarative

Users describe:
- intent
- structure
- constraints

LRH determines:
- what is valid
- what is active
- what should happen next

---

### 2. Evidence-Driven

Progress is based on:
- verifiable outputs
- not assumptions or intent alone

---

### 3. Precedence-Governed

All stages are interpreted through the precedence model.

This ensures:
- alignment with goals
- consistency across decisions
- deterministic behavior

---

### 4. Iterative

The workflow is designed to:
- adapt to new information
- refine understanding
- improve over time

---

## Summary

The LRH workflow transforms:

- high-level intent  
into  
- structured execution  
into  
- validated, evidence-backed state  

It provides a disciplined, interpretable process that enables both humans and AI agents to collaborate effectively within a shared, auditable system.

---

# Validation Model

The Logical Robotics Harness (LRH) defines validation as the process of determining whether a project is **structurally correct, internally consistent, and semantically meaningful**.

Validation is not limited to syntax or schema checking. Instead, it is a **multi-layered process** that ensures the project can be reliably interpreted and executed.

---

## Overview

Validation in LRH answers three progressively deeper questions:

1. **Structural Validity** — Are the files well-formed and parseable?
2. **Schema Validity** — Do the artifacts conform to expected structures?
3. **Semantic Validity** — Does the project make sense as a coherent system?

A project is considered fully valid only if it satisfies all three levels.

---

## 1. Structural Validation

Structural validation ensures that all project artifacts can be **read and parsed correctly**.

This includes:

- Valid Markdown formatting
- Correct YAML frontmatter syntax (if present)
- Proper file placement within the repository structure

### Examples of Structural Errors

- Invalid YAML (e.g., indentation errors)
- Missing required files (e.g., no `current_focus.md`)
- Files in incorrect directories

### Properties

Structural validation is:

- **deterministic**
- **fast**
- **binary** (valid or invalid)

Failure at this level prevents further validation.

---

## 2. Schema Validation

Schema validation ensures that artifacts conform to **expected data structures**.

Each artifact type (e.g., work item, focus, goal) has an implicit or explicit schema.

### Examples

A work item might require:

- `id`
- `status`
- `acceptance`
- `expected_actions`

A focus might require:

- `title`
- `priorities`
- `exit_criteria`

### What Schema Validation Checks

- Required fields are present
- Field types are correct
- Values fall within expected ranges (when applicable)

### Properties

Schema validation is:

- **deterministic**
- **extensible**
- **type-oriented**

It ensures that LRH can reliably interpret artifacts.

---

## 3. Semantic Validation

Semantic validation ensures that the project is **coherent and meaningful as a system**.

This is the most important and most complex layer.

It answers questions such as:

- Does the current focus reference valid work items?
- Do work item dependencies form a valid graph?
- Are acceptance criteria satisfiable?
- Is there evidence for completed work?

### Examples of Semantic Issues

- A work item marked “complete” without evidence
- A focus with no achievable exit criteria
- Conflicting definitions between roadmap and focus
- Circular dependencies between work items

### Properties

Semantic validation is:

- **interpretive**
- **context-dependent**
- **based on relationships between artifacts**

---

## Validation Outputs

Validation produces a structured result:

```
Validation completed: N error(s), M warning(s)
```

### Errors

Errors indicate:

- violations that prevent correct interpretation
- conditions that must be fixed

Examples:

- invalid schema
- missing required fields
- broken dependencies

---

### Warnings

Warnings indicate:

- potential issues
- suboptimal or ambiguous configurations

Examples:

- unused work items
- unclear priorities
- weak or unverifiable acceptance criteria

---

## Validation as a Gatekeeper

Validation acts as a **gatekeeper** for all LRH operations.

Before:

- execution
- interpretation
- snapshot generation

the project should pass validation.

This ensures:

- reliability
- consistency
- trustworthiness

---

## Relationship to Precedence

Validation does not resolve precedence, but it ensures that:

- all inputs to the precedence model are valid
- no contradictions violate higher-level constraints

For example:

- A work item cannot contradict a principle
- A focus cannot violate the project goal

These checks require both:

- schema validation (structure)
- semantic validation (meaning)

---

## Relationship to Evidence

Validation enforces that:

- claims must be supported by evidence
- completion must be justified

This creates a strong link between:

- execution (what was done)
- truth (what is provably true)

---

## Incremental Validation

Validation can be applied at different stages:

### Local Validation

- Validate a single file or artifact
- Used during editing

---

### Project Validation

- Validate the entire `project/` directory
- Used in CI and before commits

---

### Continuous Validation

- Automatically run validation during development
- Prevent invalid states from persisting

---

## Minimal Validation Success Criteria

A minimally valid LRH project must:

- pass structural validation
- pass schema validation
- have no critical semantic errors

This enables:

- meaningful interpretation
- reliable execution guidance

---

## Design Goals of the Validation Model

The validation model is designed to be:

### Deterministic

Given the same inputs, validation produces the same results.

---

### Transparent

Errors and warnings are:

- clearly explained
- traceable to source artifacts

---

### Extensible

New artifact types and rules can be added without breaking existing validation.

---

### Actionable

Validation results should:

- guide fixes
- improve project quality
- support both humans and AI agents

---

## Summary

Validation in LRH is not just about correctness—it is about **ensuring that the project can be trusted as a control system**.

It guarantees that:

- structure is sound
- data is well-formed
- meaning is coherent

This forms the foundation for interpretation, execution, and automation.


---
# Interpretation / Snapshot Model

The Logical Robotics Harness (LRH) does not stop at validation.  
Its primary purpose is to **interpret a valid project and produce a coherent, actionable view of its current state**.

This process is called **interpretation**, and its primary output is the **snapshot**.

---

## Overview

Interpretation answers the question:

> “Given this project, what is actually going on right now, and what should happen next?”

The snapshot is the **materialized result** of this interpretation.

It transforms:

- static files  
into  
- a resolved, dynamic project state  

---

## Core Responsibilities of Interpretation

Interpretation performs three key functions:

1. **Selection** — determine what is relevant  
2. **Resolution** — apply precedence and constraints  
3. **Synthesis** — produce a coherent, human- and machine-readable state  

---

## 1. Selection

The first step is to identify **which artifacts are active and relevant**.

This includes:

- the current focus
- in-scope work items
- applicable guardrails
- relevant contributors (if defined)

### Current Focus Selection

LRH identifies the active focus from:

```
project/focus/current_focus.md
```

Constraints:

- exactly one focus should be active
- it must be structurally and semantically valid

---

### Work Item Selection

From all work items, LRH selects those that are:

- consistent with the current focus
- not blocked by dependencies
- not already complete (unless needed for context)

This produces the set of **active work items**.

---

### Guardrail Selection

Guardrails are always in scope, but interpretation determines:

- which guardrails apply to the current context
- whether any constraints are triggered

---

## 2. Resolution

Once relevant artifacts are selected, LRH applies the **precedence model** to resolve conflicts and determine valid interpretations.

### Precedence Application

The system evaluates:

```
principles > goal > roadmap > focus > work_items > guardrails > runtime
```

This ensures:

- lower-level artifacts cannot violate higher-level constraints
- execution remains aligned with intent

---

### Conflict Resolution

Examples:

- A work item that violates a principle → invalid
- A focus that contradicts the goal → invalid or warning
- A runtime request outside focus → rejected or constrained

---

### Dependency Resolution

Work items may depend on each other.

LRH determines:

- which work items are unblocked
- which are ready for execution
- which are pending

---

### Status Resolution

LRH evaluates:

- which work items are complete
- which are in progress
- which are pending

This is based on:

- acceptance criteria
- available evidence

---

## 3. Synthesis

After selection and resolution, LRH produces a **snapshot**.

The snapshot is a structured representation of the project’s current state.

---

## Snapshot Contents

A typical snapshot includes:

### 1. Current Focus

- title
- priorities
- exit criteria
- completion status (if determinable)

---

### 2. Active Work Items

For each work item:

- id
- summary
- status (derived)
- readiness (blocked / ready)
- dependencies

---

### 3. Evidence Summary

- available evidence
- mapping to work items
- missing or incomplete evidence

---

### 4. Constraint Summary

- active guardrails
- violations or risks
- relevant constraints from principles

---

### 5. Warnings and Issues

- validation warnings
- semantic inconsistencies
- unresolved ambiguities

---

### 6. Suggested Next Actions

Based on interpretation, LRH may suggest:

- which work item to execute next
- what dependencies must be resolved
- what issues must be fixed

These suggestions are:

- non-binding
- derived from system state

---

## Snapshot as Interface

The snapshot is the **primary interface** for:

- human contributors
- AI agents
- automation systems

Instead of reading many files, a user or agent can:

1. run:
   ```
   lrh snapshot
   ```
2. receive a coherent project state
3. act accordingly

---

## Relationship to Validation

Interpretation assumes that the project is valid.

Validation ensures:

- structure is correct
- schemas are satisfied
- semantics are coherent

Interpretation then:

- uses this valid input
- produces a meaningful state

If validation fails, interpretation may be:

- incomplete
- unreliable
- blocked

---

## Determinism and Reproducibility

Interpretation should be:

- **deterministic** — same inputs produce same snapshot  
- **reproducible** — snapshot can be regenerated at any time  

This ensures:

- consistency across environments
- trust in automated agents
- auditability

---

## Snapshot Granularity

Snapshots can vary in detail:

### Minimal Snapshot

- current focus
- active work items

---

### Full Snapshot

- all sections listed above
- full reasoning context

---

## Interpretation as a Control System

Interpretation transforms LRH from:

- a static specification  

into  

- a **dynamic control system**

It enables:

- guided execution
- real-time understanding
- adaptive decision-making

---

## Summary

The Interpretation / Snapshot Model is the **operational core of LRH**.

It:

- selects relevant information  
- resolves it through precedence  
- synthesizes it into a usable state  

This allows both humans and AI agents to:

- understand the project  
- make correct decisions  
- execute work effectively  

without hidden context or ambiguity.

---

## How to Use LRH in Practice

This section describes how a developer or AI agent should use the Logical Robotics Harness (LRH) in a real workflow.

The goal is to make LRH not just a specification, but a **practical control system** for organizing and executing work.

---

### 1. Initialize a Project

Create a `project/` directory at the root of your repository:


```
project/
goal/
project_goal.md
design/
design.md
roadmap/
roadmap.md
focus/
current_focus.md
work_items/
WI-*.md
```

Each file contains:
- human-readable Markdown
- structured YAML frontmatter

---

### 2. Define the Goal and Design

- `goal/project_goal.md` defines **what success means**
- `design/design.md` defines **how the system is structured**

These are **global constraints** in the precedence model:
- They should change infrequently
- They guide all downstream decisions

---

### 3. Set the Current Focus

Edit:

```
project/focus/current_focus.md
```


This defines:
- the **active scope of work**
- the **exit criteria**
- the **current priorities**

Only one focus should be active at a time.

---

### 4. Create Work Items

Add files to:
```
project/work_items/
```

Each work item should:
- be small and testable
- include acceptance criteria
- declare dependencies if needed

Work items are:
- **activated by focus**
- **interpreted through precedence**

---

### 5. Run Validation

Validate the project structure:

```
scripts/validate
```

or

```
lrh validate
```

This checks:
- YAML structure correctness
- schema compliance
- internal consistency

Expected result:

```
Validation completed: N error(s), M warning(s)
```


---

### 6. Interpret the Project State

LRH is not just parsing files—it is **interpreting them**.

A correct system should be able to answer:

- What is the current focus?
- What work items are in scope?
- What should be done next?

This is driven by the **precedence model**:

```
principles > goal > roadmap > focus > work_items > guardrails > runtime
```


---

### 7. Use Snapshot (Recommended)

Generate a resolved project view:

```
lrh snapshot
```


This should produce a **coherent state description**, including:

- active focus
- relevant work items
- contributors (if defined)
- warnings or inconsistencies

This is the **primary interface for humans and AI agents**.

---

### 8. Execute Work

A human or AI agent should:

1. Read the snapshot
2. Select an in-scope work item
3. Perform the expected actions
4. Produce required evidence
5. Update the repository

---

### 9. Close the Loop

When exit criteria are met:

- Update or archive `current_focus.md`
- Move to the next focus
- Update roadmap if needed

---

## Example Workflow

A typical session:

1. Run:

```
lrh snapshot
```


2. Observe:
- Current focus: control-plane semantics
- Active work item: precedence resolver

3. Execute:
- Implement resolver
- add tests

4. Validate:

```
lrh validate
```


5. Commit results

---

## Key Principles of Use

### LRH is Declarative

You describe:
- goals
- structure
- intent

LRH determines:
- what is active
- what is valid
- what should happen next

---

### LRH is Interpreted

Correctness is not just:
- “files exist”

But:
- “the system understands them correctly”

---

### LRH is Auditable

At any point, you should be able to answer:

- Why is this work item active?
- Why is this decision valid?
- What constraints apply?

---

### LRH is AI-Compatible

This structure is designed so that:

- an LLM can read `snapshot`
- interpret the project
- take valid next actions

without hidden context

---

## Minimal Success Criterion

A fully functional LRH project should support:

```
lrh validate
lrh snapshot
```

Where:

- `validate` ensures structural correctness
- `snapshot` produces meaningful interpretation

---

## Future Extensions

This workflow is intentionally minimal.

Future capabilities may include:

- multi-focus support
- agent assignment and tracking
- automated planning
- workspace/dashboard cataloging across LRH-compatible repositories (informative/coordinating, not authoritative over project precedence)
- integration with external tools

# End-to-End Example

This section demonstrates a complete LRH workflow from initial setup to execution and interpretation.

The goal is to show how all components—control planes, precedence, validation, and interpretation—work together in practice.

---

## Scenario

We are developing a simple feature:

> Implement a working `lrh validate` command that validates the project structure.

---

## Step 1: Define Intent

### principles/principles.md

```markdown
---
id: PRINCIPLES-CORE
---

- The system must be auditable
- Validation must be deterministic
- All project state must be explicit
```

---

### goal/project_goal.md

```markdown
---
id: GOAL-LRH
---

## Goal

Create a system that can validate and interpret its own project state.
```

---

### roadmap/roadmap.md

```markdown
---
id: ROADMAP-PHASE-01
---

## Phase 1

- Implement validation
- Implement interpretation
```

---

## Step 2: Define Design

### design/design.md

```markdown
## Design

The system uses:
- control planes
- precedence model
- validation + interpretation
```

---

## Step 3: Set Current Focus

### focus/current_focus.md

```markdown
---
id: FOCUS-VALIDATION
---

## Focus

Implement validation system.

### Priorities

- Build validator
- Add schema checks

### Exit Criteria

- `lrh validate` runs successfully
- Reports errors and warnings correctly
```

---

## Step 4: Create Work Items

### work_items/WI-VALIDATOR.md

```markdown
---
id: WI-VALIDATOR
status: proposed
---

## Summary

Implement validation command.

## Acceptance

- Command exists
- Validates project structure
```

---

### work_items/WI-SCHEMA.md

```markdown
---
id: WI-SCHEMA
status: proposed
depends_on:
  - WI-VALIDATOR
---

## Summary

Add schema validation.

## Acceptance

- Schema rules enforced
```

---

## Step 5: Run Validation

Command:

```
lrh validate
```

Output:

```
Validation completed: 0 error(s), 0 warning(s)
```

This confirms:
- structure is valid
- schemas are satisfied
- system is interpretable

---

## Step 6: Interpret Snapshot

Command:

```
lrh snapshot
```

Example output:

```yaml
focus: FOCUS-VALIDATION

active_work_items:
  - WI-VALIDATOR (ready)
  - WI-SCHEMA (blocked: depends_on WI-VALIDATOR)

suggested_next:
  - Execute WI-VALIDATOR
```

---

## Step 7: Execute Work

Developer or agent:

- implements `lrh validate`
- adds validation logic

---

## Step 8: Add Evidence

### evidence/validator_test.txt

```
Validation completed: 0 error(s), 0 warning(s)
```

---

## Step 9: Update Status

Interpretation now determines:

- WI-VALIDATOR → complete
- WI-SCHEMA → now unblocked

---

## Step 10: Re-run Snapshot

```yaml
focus: FOCUS-VALIDATION

active_work_items:
  - WI-SCHEMA (ready)

completed_work_items:
  - WI-VALIDATOR

suggested_next:
  - Execute WI-SCHEMA
```

---

## Step 11: Complete Focus

Once all work items are complete and exit criteria are satisfied:

- focus is considered complete
- workflow returns to roadmap level

---

## What This Demonstrates

This example shows:

### 1. Intent Drives Execution

- goal and roadmap define direction
- focus selects active scope

---

### 2. Execution Produces Evidence

- work items generate outputs
- evidence supports completion

---

### 3. Validation Ensures Correctness

- structure and semantics are enforced
- invalid states are prevented

---

### 4. Interpretation Produces Guidance

- snapshot identifies next actions
- system becomes self-describing

---

## Key Takeaway

LRH transforms:

```
static files → validated structure → interpreted state → guided execution
```

This allows both humans and AI agents to operate:

- consistently
- transparently
- effectively

within a shared control system.

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
Authoritative shared state belongs in version-controlled repository artifacts.
Local runtime state may exist (for caches, logs, transient sessions, and local secrets), but it is non-authoritative and must not silently override repository artifacts.

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
