# PR Review Against Work Item

Review a proposed change (PR or patch) against an approved LRH work item.

==================================================
INPUT CONTEXT
==================================================

STYLE GUIDE:
{{STYLE_GUIDE_CONTEXT}}

APPROVED WORK ITEM:
{{WORK_ITEM}}

PR / PATCH / DIFF:
{{PATCH}}

OPTIONAL BACKGROUND:
{{BACKGROUND_CONTEXT}}

==================================================
OBJECTIVE
==================================================

Evaluate whether the proposed change:

1. correctly implements the approved work item
2. stays strictly within scope
3. follows STYLE.md
4. maintains minimal, reviewable diffs
5. avoids unintended side effects

You are performing a **review**, not editing code.

Do NOT produce diffs.
Do NOT rewrite code.
Do NOT propose large refactors.

==================================================
AUTHORITATIVE CONSTRAINTS
==================================================

The following are binding:

- STYLE.md is the source of truth
- The approved work item defines scope
- Unrelated code must not be modified
- Changes must be minimal and reviewable
- Behavior must not change unless explicitly required

Violations of scope or STYLE.md are considered failures,
even if the code is technically correct.

==================================================
REVIEW CRITERIA
==================================================

Evaluate the PR across these dimensions:

## 1. Scope Adherence

- Does the change implement ONLY the approved work item?
- Are there unrelated edits?
- Are any required changes missing?

## 2. Correctness

- Does the implementation actually solve the stated problem?
- Are edge cases handled appropriately?
- Any regressions introduced?

## 3. Minimal Diff Discipline

- Are changes narrowly scoped?
- Any drive-by refactors?
- Any unnecessary formatting or renaming?

## 4. STYLE.md Compliance

Check specifically:

- module-level imports
- no unnecessary member imports
- typing consistency
- no mixing typing styles unnecessarily
- scripts remain thin (if touched)
- deterministic behavior preserved
- encoding rules respected
- no speculative refactors

## 5. Tests and Validation

- Are required tests present (if applicable)?
- Do tests appear deterministic?
- Are validation steps covered?

## 6. Risk Assessment

- Does this change introduce risk beyond its scope?
- Is behavior changed unintentionally?
- Are there hidden side effects?

## 7. Work Item Alignment

Compare directly against:

- Scope
- Out of scope
- Acceptance criteria
- Validation

==================================================
OUTPUT FORMAT
==================================================

# PR Review Report

## SUMMARY

- Overall result: PASS / PASS WITH MINOR ISSUES / FAIL
- Scope adherence: Strong / Partial / Violated
- Diff size: Appropriate / Slightly large / Too large
- Risk level: Low / Medium / High

## WORK ITEM ALIGNMENT

- **Implements stated problem:** Yes / Partial / No
- **Meets acceptance criteria:** Yes / Partial / No
- **Follows validation requirements:** Yes / Partial / No

## FINDINGS

For each issue:

### [SEVERITY] Short Title

- **Category:** Scope / Style / Correctness / Tests / Risk

- **Location:**
  file:line if possible, otherwise describe

- **Issue:**
  Clear explanation of the problem

- **Why it matters:**
  Reference STYLE.md or work item constraint

- **Suggested minimal fix:**
  Small, targeted correction (NOT rewrite)

Severity levels:

- CRITICAL: violates scope or correctness
- MAJOR: significant STYLE.md or design issue
- MINOR: small fix or polish
- NIT: low-priority style issue

## SCOPE VIOLATIONS

Explicitly list any:

- unrelated files modified
- unrelated refactors
- formatting-only changes outside scope
- type style changes outside scope

If none, state: "None detected"

## MISSING WORK

List anything required by the work item that was not implemented.

If none, state: "None"

## POSITIVE OBSERVATIONS

- What was done well
- Where the change adheres strongly to STYLE.md

## RECOMMENDED ACTION

Choose one:

- APPROVE
- APPROVE WITH MINOR FIXES
- REQUEST CHANGES

Provide a short rationale.

## SUGGESTED FOLLOW-UPS

If applicable:

- additional work items
- deferred refactors
- test improvements

==================================================
REVIEW PRINCIPLES
==================================================

- Prefer rejecting scope violations over accepting broad changes
- Prefer smaller follow-up work items over accepting overreach
- Do NOT reward “extra cleanup” outside scope
- Be precise and actionable
- Ground all claims in STYLE.md or the work item

==================================================
FAILURE CONDITIONS
==================================================

Automatically FAIL if:

- significant scope violations exist
- unrelated files are modified without justification
- behavior changes unintentionally
- required work is missing
- diff is unnecessarily large

==================================================
FINAL CHECK
==================================================

Before finishing:

1. Did you evaluate scope strictly?
2. Did you avoid suggesting large refactors?
3. Did you tie findings to STYLE.md or the work item?
4. Did you provide actionable, minimal fixes?
5. Did you clearly separate scope violations from minor issues?

If not, revise.

==================================================
BEGIN REVIEW
==================================================