# Current Focus Context Template

Use this template to generate a **focus-level context packet** for a human contributor or agent.

This document should summarize the project through the lens of the **current focus**.

---

## Purpose

Summarize the project state that is relevant to the currently active focus so that a contributor or agent can:

- understand what is being worked on now
- understand why it matters
- understand what work items belong to it
- understand relevant constraints and guardrails
- act without needing the entire project history

This template is appropriate for:

- parallel threads working on the same focus
- agent task kickoff within the current focus
- focus-level planning and review

---

## Inputs

Use information from:

- `project/goal/project_goal.md`
- `project/design/design.md`
- `project/roadmap/roadmap.md`
- `project/focus/current_focus.md`
- relevant `project/work_items/`
- `project/guardrails/`
- `project/contributors/`
- `project/status/current_status.md`
- relevant `project/evidence/` if needed

Focus on what matters for the **active focus**.

---

## Output Structure

# Current Focus Context

## Project Identity
- Project name:
- Repository:
- Current date:
- Context scope: current_focus

## Brief Project Purpose
Provide a short project-level summary sufficient to orient the reader.

## Current Focus Summary
Summarize:
- the current focus title
- why it is active now
- what success looks like
- what is not in scope

## Relationship to Roadmap
Explain:
- which roadmap phase(s) this focus supports
- how the focus advances the broader plan
- whether this focus is bootstrap, execution, evaluation, or refinement oriented

## Relevant Design Context
Summarize only the parts of the design most relevant to this focus.

Examples:
- control plane structure
- contributor/ownership semantics
- frontmatter schema
- action/guardrail model
- validation expectations

## Active Work Items
List and summarize the work items that are part of this focus.

For each relevant work item, include:
- ID
- title
- type
- status
- owner
- short description

## Dependencies and Coordination Needs
Summarize:
- dependencies between work items
- whether work can proceed in parallel
- where coordination is needed
- who is involved

## Relevant Contributors
Summarize:
- accountable owner(s)
- active contributors
- assigned or expected agents
- any review expectations

## Relevant Guardrails
Include only the guardrails that matter to this focus.

Examples:
- no unrelated restructuring
- keep schema changes minimal
- preserve semantics
- avoid cost-heavy or destructive actions

## Evidence and Status Relevant to This Focus
Summarize:
- relevant evidence
- current status of the focus
- blockers, if any
- confidence level

## What a Contributor or Agent Should Do Next
State what kinds of next actions are appropriate inside this focus.

## Recommended Next Step
State the single most useful next step at the focus level.

---

## Style Guidance

The generated output should be:

- narrower than project context
- strongly focused on current work
- explicit about dependencies and blockers
- suitable for handing to an agent that will work within the active focus

---

## Minimal-Diff Rule for Future Use

If generated automatically, include only the context that materially affects the current focus. Avoid dumping unrelated project state.
