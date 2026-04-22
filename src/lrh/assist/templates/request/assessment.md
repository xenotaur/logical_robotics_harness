# Repository Assessment Request

Generate a concise, evidence-backed assessment of this repository.

==================================================
ASSESSMENT CONTEXT
==================================================

SCOPE: {{ASSESSMENT_SCOPE}}

TARGET (if scope=work_item): {{ASSESSMENT_TARGET}}

OPTIONAL BACKGROUND:
{{BACKGROUND_CONTEXT}}

==================================================
OBJECTIVE
==================================================

Inspect the repository and compare current implementation/repo state against declared
state in `project/` artifacts.

Your report should identify:

- alignment between implementation and declared project intent
- drift, blockers, or inconsistencies
- missing evidence/status support
- the best next actionable step

==================================================
SCOPE GUIDANCE
==================================================

If SCOPE is `project`, assess the repository as a whole against:

- project goal
- design
- roadmap
- current focus
- status/evidence

If SCOPE is `current_focus`, assess progress on current focus against:

- `project/focus/current_focus.md`
- relevant work items
- relevant status/evidence
- applicable design constraints and guardrails

If SCOPE is `work_item`, assess the specific work item against:

- work item definition
- dependencies/predecessors
- expected evidence
- current focus alignment
- relevant design constraints and guardrails

==================================================
REQUIRED REVIEW LENS
==================================================

While assessing, explicitly distinguish:

1. what is implemented in code/docs now
2. what is declared in `project/`
3. what appears missing, inconsistent, or stale

Also consider:

- project purpose
- design constraints
- guardrails
- contributor/ownership semantics when visible
- evidence-backed status quality

==================================================
OUTPUT FORMAT
==================================================

# Assessment Report

## Scope

- Scope: <project | current_focus | work_item>
- Target: <work item ID or N/A>

## Repo Reality (Observed)

- concise bullets of observed implementation/repo state

## Declared Project State

- concise bullets from `project/` artifacts relevant to scope

## Alignment and Drift

- **Aligned:** <what matches>
- **Drift / Gaps:** <what does not match or is missing>
- **Blockers / Risks:** <key blockers or risks>

## Evidence and Status Quality

- what evidence exists
- what evidence is missing
- confidence level in current status claims

## Recommended Next Action

- one best next action, narrowly scoped and reviewable
- why this should be next

## Notes and Uncertainty

- explicit assumptions and unknowns
