# Work Item Proposals from Audit

Convert an audit report into a small set of proposed work items for LRH.

==================================================
INPUT CONTEXT
==================================================

STYLE GUIDE:
{{STYLE_GUIDE_CONTEXT}}

AUDIT REPORT:
{{AUDIT_REPORT}}

OPTIONAL BACKGROUND:
{{BACKGROUND_CONTEXT}}

==================================================
OBJECTIVE
==================================================

Read the audit report and propose a set of **small, reviewable, independent work items**
that would address the findings.

These are planning artifacts only.

Do NOT write code.
Do NOT write diffs.
Do NOT rewrite files.
Do NOT collapse multiple unrelated findings into one large work item.

The goal is to turn an audit into a queue of candidate tasks that a human can review,
select, and then convert into implementation prompts or GitHub issues.

==================================================
AUTHORITATIVE CONSTRAINTS
==================================================

Follow the LRH style guide as the source of truth.

In particular:

- prefer small, scoped changes
- avoid unrelated edits
- avoid broad refactors unless explicitly required
- preserve existing behavior unless a change is intentionally behavioral
- separate mechanical fixes from design-sensitive fixes
- keep work items narrow enough for clean PRs

If the audit suggests a fix that would violate these principles, split it into smaller
work items or mark it as requiring human design review.

==================================================
REQUIRED BEHAVIOR
==================================================

1. Read the audit carefully.
2. Identify distinct fixable issues or coherent groups of issues.
3. Split work by **change type**, **risk**, and **scope**.
4. Prefer one work item per:
   - mechanical fix class
   - script interface improvement
   - determinism/design fix
   - test coverage addition
   - refactor requiring human judgment
5. Clearly distinguish:
   - safe mechanical work
   - moderate-risk work
   - design-sensitive work
6. If an issue is too broad, split it.
7. If an issue is ambiguous, say so explicitly.
8. If a proposed work item should probably NOT be delegated to Codex directly,
   say that clearly.

==================================================
DO NOT
==================================================

- Do NOT propose one giant cleanup item
- Do NOT produce implementation code
- Do NOT generate diffs
- Do NOT merge unrelated audit findings into one task for convenience
- Do NOT silently invent missing requirements
- Do NOT over-specify solutions where the audit is uncertain
- Do NOT hide dependencies between work items

==================================================
WORK ITEM DESIGN RULES
==================================================

A good work item should be:

- small enough for a narrow PR
- coherent enough to review as one change
- explicit about affected files or likely files
- explicit about risk
- explicit about validation steps
- explicit about whether it is:
  - Codex-suitable
  - human-suitable
  - needs design review first

Work items should generally be grouped by one of these patterns:

- import normalization
- script interface improvements
- typing/style cleanup
- deterministic behavior fixes
- serialization/schema fixes
- direct unit test additions
- refactor-to-thin-wrapper changes
- CI/tooling alignment

==================================================
OUTPUT FORMAT
==================================================

# Proposed Work Items from Audit

## Summary

- Total proposed work items: <N>
- High-priority items: <count>
- Items suitable for Codex: <count>
- Items requiring human design review first: <count>

## Proposed Work Items

For each work item, use this exact structure:

### WI-XXXX: <Short Title>

- **Source audit finding(s):**
  - Quote or summarize the relevant finding title(s)

- **Problem:**
  - What issue this work item addresses

- **Why it matters:**
  - Why this should be fixed
  - Tie back to STYLE.md or project constraints

- **Scope:**
  - What this work item should include
  - Keep this narrow and concrete

- **Out of scope:**
  - What this work item must NOT include

- **Likely files:**
  - Specific files if known
  - Otherwise say "Unclear from audit"

- **Risk level:**
  - Low / Medium / High

- **Execution suitability:**
  - Codex-suitable
  - Human-suitable
  - Human design review first

- **Dependencies:**
  - None
  - or list prerequisite work items

- **Acceptance criteria:**
  - A short checklist of what must be true when done

- **Validation:**
  - Commands or checks to run
  - Example:
    - `scripts/test`
    - `scripts/lint`

- **Suggested PR title:**
  - A short, review-friendly PR title

## Suggested Execution Order

Provide the recommended sequence for these work items.

Group them into:

1. High-impact, low-risk
2. Medium-risk / moderate design judgment
3. Design-sensitive or refactor-heavy

## Notes on Splitting / Combining

Briefly explain any cases where:
- one audit finding was split into multiple work items
- multiple findings were merged into one work item
- an item was deferred because it is too ambiguous or broad

==================================================
WORK ITEM QUALITY BAR
==================================================

A good result:

- produces several narrow work items instead of one large one
- respects LRH’s minimal-diff philosophy
- separates mechanical fixes from design-sensitive changes
- makes execution order obvious
- gives a human enough information to choose the next task

A bad result:

- creates overbroad work items
- mixes unrelated changes
- assumes implementation details not grounded in the audit
- turns the audit directly into a refactor plan
- ignores uncertainty

==================================================
SPECIAL HANDLING RULES
==================================================

Use these defaults unless the audit strongly suggests otherwise:

- Import cleanup should usually be its own work item
- Script `--help` support should usually be separate from `--check` / `--dry-run`
- Determinism fixes should usually be separate from serialization/schema fixes
- Test additions should usually be separate from behavioral refactors
- Refactors to move script logic into library code should usually be deferred until after
  simpler fixes are done

If the audit already includes priority hints, use them, but still split work conservatively.

==================================================
FINAL CHECK
==================================================

Before finishing, verify:

1. Are the work items small enough for clean PRs?
2. Did you avoid mixing unrelated changes?
3. Did you separate mechanical and design-sensitive work?
4. Did you make uncertainty explicit?
5. Did you avoid producing implementation details or diffs?

If not, revise.

==================================================
BEGIN
==================================================