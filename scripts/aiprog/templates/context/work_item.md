# Work Item Context Template

Use this template to generate a **work-item-specific context packet** for a human contributor or agent.

This document should be the most task-focused of the three context templates.

---

## Purpose

Summarize the exact context needed to execute or review a specific work item so that a contributor or agent can:

- understand the task
- understand why it matters
- understand required constraints
- understand dependencies and required evidence
- act with minimal extra context

This template is appropriate for:

- assigning a work item to an agent
- parallel execution threads
- focused implementation/review sessions
- validating whether a work item is ready to be done

---

## Inputs

Use information from:

- `project/goal/project_goal.md` (briefly)
- `project/design/design.md` (only the relevant parts)
- `project/focus/current_focus.md`
- the target `project/work_items/WI-XXXX.md`
- any referenced dependencies
- relevant `project/guardrails/`
- `project/contributors/`
- relevant `project/status/current_status.md`
- relevant `project/evidence/` if needed

Prioritize the target work item above all else.

---

## Output Structure

# Work Item Context

## Project Identity
- Project name:
- Repository:
- Current date:
- Context scope: work_item
- Work item ID:

## Brief Project Purpose
Give a short one-paragraph summary of the project sufficient to orient the reader.

## Current Focus Summary
Summarize the current focus only to the extent needed to explain why this work item exists.

## Work Item Summary
Provide:
- ID
- title
- type
- status
- owner
- contributors
- assigned agents
- priority

Then explain in prose:
- what the work item is
- why it matters
- what “done” means

## Acceptance Criteria
List the work item’s acceptance criteria clearly.

## Required Evidence
List required evidence clearly.

## Expected and Forbidden Actions
Summarize:
- expected actions
- forbidden actions
- relevant action/guardrail implications

## Dependencies
Summarize:
- what this work item depends on
- what may block it
- whether it unblocks later work

## Relevant Design Context
Include only the design details needed to complete this specific item.

Examples:
- schema conventions
- ownership semantics
- validation expectations
- path/layout conventions
- contributor/agent rules

## Relevant Guardrails
Summarize the exact guardrails that matter for this work item.

Examples:
- avoid unrelated wording changes
- do not refactor unrelated code
- preserve minimal-diff discipline
- do not introduce new architecture unless explicitly requested

## Current Status and Evidence
State:
- whether the work item appears ready
- what evidence already exists
- what is still missing
- any known risks or ambiguities

## Suggested Execution Approach
Provide a short, concrete plan for how a contributor or agent should approach the item.

## Recommended Next Step
State the single next best action for this work item.

---

## Style Guidance

The generated output should be:

- highly specific
- low-noise
- scoped to one work item
- explicit about constraints
- suitable for immediate handoff to an agent

---

## Minimal-Diff Rule for Future Use

If generated automatically, do not include unrelated project prose. The work-item context should be optimized for execution, not broad orientation.
