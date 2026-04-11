# Project Context Template

Use this template to generate a **project-wide context packet** for a human contributor or agent.

This document should summarize the project at the broadest useful level. It should be concise, high-signal, and grounded in the current `project/` control plane.

---

## Purpose

Summarize the project as a whole so that a contributor or agent can:

- understand what the project is for
- understand how the project is structured
- understand the current architectural and workflow model
- understand major constraints and guardrails
- understand the current project state at a high level

This template is appropriate for:

- onboarding a new contributor
- opening a new parallel agent thread
- providing broad context before a task-specific prompt

---

## Inputs

Use information from:

- `project/principles/`
- `project/goal/project_goal.md`
- `project/design/design.md`
- `project/roadmap/roadmap.md`
- `project/focus/current_focus.md`
- `project/guardrails/`
- `project/contributors/`
- `project/status/current_status.md`
- other highly relevant files only if needed

Do **not** dump all source text verbatim. Summarize.

---

## Output Structure

# Project Context

## Project Identity
- Project name:
- Repository:
- Current date:
- Context scope: project

## Project Purpose
Summarize:
- what the project is
- why it exists
- who it is for
- what success looks like

## Core Principles
Summarize the most important project principles and norms.

Include:
- engineering norms
- evaluation norms
- any key project-specific philosophical constraints

## Current Design Summary
Summarize the current design at a high level.

Include:
- major architectural concepts
- key data/control model concepts
- current understanding of the system structure

## Workflow Model
Summarize how work flows through the system.

Include:
- how projects move from goal/roadmap to focus/work_items
- how evidence and status fit in
- how guardrails and contributors fit in

## Roadmap Summary
Summarize:
- major roadmap phases
- current phase
- major next phases

## Current Focus
Summarize the current focus.

Include:
- what is active now
- what success looks like
- what is explicitly not in scope right now

## Contributor Model
Summarize:
- key contributors
- role model
- ownership semantics
- any active or expected agent roles

## Guardrails Summary
Summarize key:
- safety guardrails
- cost guardrails
- optics guardrails
- approval expectations

## Current Status
Summarize the current state of the project.

Include:
- major progress
- current blockers or risks
- what evidence supports the status

## What a Contributor or Agent Should Know Before Acting
Provide a concise operational summary of:
- what to preserve
- what to avoid
- where to look next
- how to avoid causing drift or confusion

## Recommended Next Step
State the most useful next step at the project level.

---

## Style Guidance

The generated output should be:

- concise but not skeletal
- accurate to the current repo state
- explicit about uncertainty
- focused on orientation, not implementation detail
- suitable for handing to a contributor or agent as context

---

## Minimal-Diff Rule for Future Use

If this context is generated automatically, it should reflect the current project state without inventing missing facts or silently expanding scope.
