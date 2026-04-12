# Codex Implementation Prompt from Work Item

Create a tightly scoped Codex implementation prompt for one approved LRH work item.

==================================================
INPUT CONTEXT
==================================================

STYLE GUIDE:
{{STYLE_GUIDE_CONTEXT}}

APPROVED WORK ITEM:
{{WORK_ITEM}}

OPTIONAL BACKGROUND:
{{BACKGROUND_CONTEXT}}

==================================================
OBJECTIVE
==================================================

Generate a Codex prompt that will implement exactly one approved work item.

The generated prompt should be:

- narrow in scope
- conservative
- easy to review
- aligned with STYLE.md
- explicit about what is in scope and out of scope
- explicit about validation steps

This template produces a **prompt for implementation**, not implementation itself.

Do NOT write code changes.
Do NOT write diffs.
Do NOT invent work beyond the work item.

==================================================
AUTHORITATIVE CONSTRAINTS
==================================================

The generated Codex prompt must treat the following as binding:

- STYLE.md is the source of truth
- the approved work item defines the allowed scope
- unrelated code must not be modified
- behavior must not change unless the work item explicitly requires it
- style-only cleanup must not be mixed with unrelated functional edits
- changes must remain small and reviewable

If the work item is ambiguous, the generated prompt must tell Codex to stay conservative and report uncertainty rather than guessing.

==================================================
WHAT THE GENERATED PROMPT MUST DO
==================================================

The generated prompt must instruct Codex to:

1. Implement only the approved work item
2. Keep the diff minimal
3. Avoid unrelated cleanup
4. Preserve comments unless a change requires updating them
5. Preserve local file style where possible
6. Follow STYLE.md rules on:
   - imports
   - type annotations
   - testing
   - formatting
   - AI-assisted development constraints
7. Run or report relevant validation commands
8. Summarize what changed and what was intentionally not changed

==================================================
WHAT THE GENERATED PROMPT MUST NOT DO
==================================================

The generated prompt must explicitly forbid Codex from:

- changing files outside the work item scope without necessity
- performing drive-by refactors
- reformatting unrelated files
- changing unrelated type annotation styles
- broad cleanup
- speculative redesign
- inventing missing requirements
- silently expanding scope

==================================================
PROMPT SHAPE REQUIREMENTS
==================================================

The generated Codex prompt should contain these sections:

1. ROLE
2. AUTHORITATIVE REFERENCES
3. OBJECTIVE
4. STRICT SCOPE
5. REQUIRED CHANGES
6. DO NOT
7. EDGE CASE RULES
8. VALIDATION
9. OUTPUT REQUIREMENTS
10. SUCCESS CRITERIA
11. FINAL CHECK
12. BEGIN

The generated prompt should read like a direct instruction to Codex.

==================================================
OUTPUT FORMAT
==================================================

Produce exactly one implementation prompt in the following structure:

# ROLE

You are a senior Python engineer making a single, tightly scoped repository change.

# AUTHORITATIVE REFERENCES

- STYLE.md
- the approved work item below

# OBJECTIVE

<clear implementation objective derived from the work item>

# STRICT SCOPE

<exact scope derived from the work item>

# REQUIRED CHANGES

<bullet list of required implementation actions>

# DO NOT

<bullet list of prohibited expansions or unrelated edits>

# EDGE CASE RULES

<what to do if ambiguity or uncertainty arises>

# VALIDATION

<commands to run, such as scripts/test and scripts/lint, if appropriate>

# OUTPUT REQUIREMENTS

<what Codex should report after making changes>

# SUCCESS CRITERIA

<what makes the change acceptable>

# FINAL CHECK

<a short pre-submit checklist>

# BEGIN

==================================================
MAPPING RULES
==================================================

When converting a work item into an implementation prompt:

- Turn “Problem” into the implementation objective
- Turn “Scope” into strict in-scope boundaries
- Turn “Out of scope” into explicit “DO NOT” bullets
- Turn “Likely files” into allowed target files
- Turn “Acceptance criteria” into success criteria
- Turn “Validation” into command/check instructions
- Turn “Risk level” into caution language
- Turn “Execution suitability” into tone:
  - if Codex-suitable: proceed directly
  - if Human-suitable: say implementation should be deferred for human handling
  - if Human design review first: do not generate an implementation prompt; instead return a short notice explaining why

==================================================
SPECIAL HANDLING RULES
==================================================

Apply these defaults unless the work item says otherwise:

- Import normalization:
  - keep changes mechanical
  - do not mix with refactors
  - do not change unrelated annotations

- Script interface changes:
  - limit changes to named scripts
  - do not move logic unless the work item explicitly includes it

- Determinism fixes:
  - preserve external behavior unless explicitly intended
  - separate clock/default changes from unrelated serialization work

- Test additions:
  - add only the tests needed for the work item
  - do not opportunistically expand unrelated coverage

- Refactor work:
  - require stronger caution language
  - emphasize not changing behavior
  - prefer reporting uncertainty over guessing

==================================================
FAILURE POLICY
==================================================

If the work item is too broad, ambiguous, or explicitly marked as requiring human design review first, do NOT generate a normal implementation prompt.

Instead, output:

- a short explanation of why the item is not ready for Codex
- the missing clarification or design decision needed
- a recommendation to split or refine the work item

==================================================
QUALITY BAR
==================================================

A good result:

- produces a prompt Codex can execute safely
- preserves LRH’s minimal-diff philosophy
- is specific about scope and boundaries
- includes concrete validation steps
- avoids accidental scope creep

A bad result:

- turns one work item into a broad cleanup
- omits validation
- leaves scope ambiguous
- ignores STYLE.md constraints
- assumes unstated implementation details

==================================================
FINAL CHECK
==================================================

Before finishing, verify:

1. Does the generated prompt implement only one approved work item?
2. Is the scope narrow and explicit?
3. Are out-of-scope items clearly forbidden?
4. Are validation steps included?
5. Does the prompt tell Codex to report uncertainty rather than guess?
6. Does it reflect STYLE.md’s minimal-diff and no-noise philosophy?

If not, revise.

==================================================
BEGIN
==================================================