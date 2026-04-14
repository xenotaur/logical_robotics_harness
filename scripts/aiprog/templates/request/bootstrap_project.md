# PR Request to Bootstrap LRH Project

Bootstrap an LRH `project/` directory for the target repository.

==================================================
INPUT CONTEXT
==================================================

REPOSITORY: {{REPO_NAME}}

PROJECT GOAL: {{PROJECT_GOAL}}

OPTIONAL BACKGROUND:
{{BACKGROUND_CONTEXT}}

==================================================
OBJECTIVE
==================================================

Create a **minimal bootstrap subset** of LRH `project/` artifacts (not the full LRH scaffold) for a repository that is clearly new to LRH.

The bootstrap output must:

- reflect current repository purpose
- align with LRH structure and precedence conventions
- remain conservative, auditable, and evidence-aware
- clearly distinguish fact vs inference

Do NOT over-engineer or speculate unnecessarily.

==================================================
REPOSITORY CLASSIFICATION & ATOMIC POLICY (STRICT)
==================================================

Before creating any files, classify repository state:

- `new`: no meaningful LRH `project/` control plane exists yet
- `existing`: a meaningful LRH `project/` directory already exists
- `uncertain`: cannot confidently determine whether LRH control artifacts already exist

Atomic bootstrap rule:

- Only create files if classification is **clearly `new`**.
- If classification is `existing` or `uncertain`, create **no files**, make **no edits**, and report findings only.

Repository identity verification:

- Confirm the repository inspected matches `{{REPO_NAME}}`.
- If identity cannot be verified, classify as `uncertain` and do not create files.

==================================================
CONSTRAINTS (STRICT)
==================================================

- Do NOT modify existing source code
- Do NOT modify existing files under `project/`
- Do NOT delete or rewrite existing documentation
- If and only if classification is `new`, only ADD files under `project/`
- Preserve authoritative vs derived artifact roles
- Clearly label uncertain inferences
- Prefer minimal viable bootstrap structure over completeness

==================================================
REQUIRED OUTPUT STRUCTURE
==================================================

## If classification is `new`

Create this minimal bootstrap subset:

- `project/goal/project_goal.md`
- `project/design/design.md`
- `project/focus/current_focus.md`
- `project/work_items/WI-BOOTSTRAP-0001.md`
- `project/guardrails/safety.md`
- `project/status/current_status.md`
- `project/memory/decision_log.md`
- `project/context/humans.md`

Optional derived context artifact:

- `project/context/agents.md` only when grounded repository evidence is sufficient to summarize agent usage or expected agent roles responsibly.
- If that evidence is insufficient, omit `project/context/agents.md`.

Do not create `project/evidence/` artifacts during bootstrap unless concrete, attributable evidence already exists in the repository and can be cited without fabrication.

## If classification is `existing` or `uncertain`

Create no files. Return only classification, rationale, and a no-change report.

==================================================
CONTENT GUIDELINES
==================================================

General:

- Prefer concise Markdown with optional YAML frontmatter when useful.
- Distinguish observed facts from inferred interpretations.
- Avoid placeholder claims that cannot be tied to repository evidence.

Authoritative artifacts (define intent, constraints, and current declared state):

### `project/goal/project_goal.md`

- One clear mission statement aligned with `{{PROJECT_GOAL}}`.
- Scope boundaries (in/out of scope).
- Near-term success criteria that are observable.
- Explicit assumptions/unknowns.

### `project/design/design.md`

- Purpose and current scope of the system.
- Core components/modules and interactions visible in repo.
- Current architecture constraints and tradeoffs.
- Explicit “open design questions” section when uncertainty exists.

### `project/focus/current_focus.md`

- Current operational focus for the next bounded increment.
- 3-6 concrete priorities tied to repo reality.
- Immediate non-goals to prevent scope creep.
- Exit criteria / definition of done for this focus snapshot.

### `project/work_items/WI-BOOTSTRAP-0001.md`

- Work item describing bootstrap artifact creation.
- Include owner (or `TBD`), status, and completion criteria.
- List created artifacts and why each is needed.
- Capture explicit uncertainties and follow-up validation tasks.

### `project/guardrails/safety.md`

- Hard safety and change-control constraints for agents/contributors.
- Required escalation/approval conditions when applicable.
- Explicit prohibited actions (e.g., destructive or out-of-scope edits).

### `project/status/current_status.md`

- Snapshot of current maturity and what is implemented now.
- Clear distinction between present facts and planned intent.
- Key risks/blockers and confidence level.
- Immediate next checkpoint that is evidence-seeking.

### `project/memory/decision_log.md`

- Bootstrap-time decisions made and rationale.
- Assumptions, alternatives considered, and unresolved questions.
- References to files/repo signals used for each decision.

Derived context artifacts (summaries; not authoritative directives):

### `project/context/humans.md`

- Known human stakeholders/contributors and observed roles.
- Source-backed notes only; unknowns clearly marked.
- Avoid invented ownership or permissions.

### `project/context/agents.md` (optional)

- Include only if grounded evidence supports agent-role summary.
- Describe known agent usage patterns, constraints, and unknowns.
- If evidence is weak or absent, omit this file.

==================================================
FILE TEMPLATES
==================================================

Use concise, high-signal templates.

### `project/goal/project_goal.md`

```markdown
---
artifact_type: project_goal
status: draft
---

# Project Goal

## Mission
<one clear sentence aligned with {{PROJECT_GOAL}}>

## Problem and Outcome
- Problem:
- Intended outcome:

## Scope Boundaries
- In scope:
- Out of scope:

## Success Criteria (Near Term)
- [ ] <observable criterion>

## Assumptions and Unknowns
- Assumption:
- Unknown:
```

### `project/design/design.md`

```markdown
---
artifact_type: design
status: draft
---

# Design

## Purpose and Scope
<what the system does now>

## Current Architecture
- Component/module:
- Responsibility:
- Interaction:

## Constraints and Tradeoffs
- Constraint:
- Tradeoff:

## Open Design Questions
- Question:
- Why unresolved:
```

### `project/focus/current_focus.md`

```markdown
---
artifact_type: current_focus
status: active
---

# Current Focus

## Focus Statement
<bounded near-term focus>

## Priorities
- [ ] Priority 1
- [ ] Priority 2
- [ ] Priority 3

## Non-Goals (For This Focus Window)
- Non-goal:

## Exit Criteria
- [ ] <evidence-seeking completion condition>
```

### `project/status/current_status.md`

```markdown
---
artifact_type: current_status
status: active
---

# Current Status

## Snapshot
- Repository maturity:
- Implemented today:

## Facts vs Inference
- Fact:
- Inference:

## Risks and Blockers
- Risk/blocker:

## Confidence
- Level: <low|medium|high>
- Why:

## Next Checkpoint
- Next evidence-seeking checkpoint:
```

### `project/memory/decision_log.md`

```markdown
---
artifact_type: decision_log
status: active
---

# Decision Log

## Decision 0001
- Date:
- Context:
- Decision:
- Rationale:
- Alternatives considered:
- Consequences:
- Follow-up:
```

### `project/context/humans.md`

```markdown
---
artifact_type: human_context
status: draft
---

# Human Context

## Known Humans
- Name/Handle:
- Observed role:
- Evidence/source:

## Responsibilities (Observed)
- Responsibility:
- Confidence:

## Unknowns
- Unknown:
```

==================================================
PROCESS (REQUIRED)
==================================================

1. Verify repository identity against `{{REPO_NAME}}`.
2. Inspect repository evidence (README, structure, key modules/docs, contribution metadata if present).
3. Classify repository state (`new`, `existing`, `uncertain`) with short rationale.
4. Apply atomic policy:
   - if `new`: create only required bootstrap subset
   - otherwise: no changes
5. For any created content, annotate uncertainty explicitly with phrases such as:
   - "Likely"
   - "Appears to"
   - "Unclear from repository evidence"

==================================================
PR DESCRIPTION REQUIREMENTS
==================================================

Include:

- Repository classification (`new` / `existing` / `uncertain`) and why
- Repository understanding summary
- File creation summary (or explicit no-change statement)
- Key assumptions and uncertainties
- Rationale for minimal bootstrap subset choice

==================================================
FAILURE POLICY
==================================================

- If repository intent is unclear:
  - classify as `uncertain`
  - create no files
  - document uncertainty and what evidence is missing
- If conflicting signals exist:
  - do NOT resolve silently
  - document both interpretations and classify conservatively

==================================================
ACCEPTANCE CRITERIA
==================================================

- Template remains bootstrap-only (not repair/migration)
- Atomic behavior preserved:
  - no files created unless classification is clearly `new`
- If created, scaffold is the defined **minimal bootstrap subset**, not a full LRH scaffold
- No existing files modified
- Content is coherent, grounded in repo evidence, and explicit about uncertainty
- Authoritative artifacts remain distinct from derived context artifacts
- PR is clean and narrowly scoped
