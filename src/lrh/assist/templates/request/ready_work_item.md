# Ready Work Item Refinement Request

Render a conservative, human-reviewable patch proposal that refines one valid-but-thin LRH work item toward `lrh request prompt-from-work-item` readiness.

This request is **assistive and non-mutating**. Do not edit files automatically unless a human explicitly asks you to apply the proposed patch in a separate step.

## Target Work Item

- ID: `{{TARGET_WORK_ITEM_ID}}`
- Title: {{TARGET_WORK_ITEM_TITLE}}
- Path: `{{TARGET_WORK_ITEM_PATH}}`
- Status: `{{TARGET_WORK_ITEM_STATUS}}`
- Type: `{{TARGET_WORK_ITEM_TYPE}}`

## Current Readiness Diagnosis

Readiness status: **{{READINESS_STATUS}}**

{{READINESS_DIAGNOSTICS}}

## Referenced Context Discovered From Frontmatter

{{REFERENCED_CONTEXT}}

## Target Work Item Source

```markdown
{{WORK_ITEM_CONTENT}}
```

## Requested Output Sections

Propose work-item body content for these sections, preserving any existing source text when it is already adequate:

{{REQUESTED_SECTIONS}}

## Instructions

1. Read the target work item first.
2. Read referenced roadmap, focus, design, workstream, dependency, status, evidence, and execution-record files when available.
3. Compare the target item to the readiness diagnostics above.
4. Propose a patch that adds missing sections needed by `lrh request prompt-from-work-item`.
5. Identify which proposed content is directly grounded in repository artifacts, citing the source path or frontmatter relationship.
6. Add `Open Questions` instead of inventing requirements when context is insufficient or unresolved.
7. Avoid implementation work; this is a work-item refinement PR only.

## Guardrails

- Keep edits conservative, narrow, and reviewable.
- Distinguish source facts from inferred suggestions.
- Do not invent scope that is not grounded in the work item or referenced artifacts.
- Treat unresolved context as an open question, not permission to guess.
- Do not implement the target work item while refining it.
- Do not loosen `prompt-from-work-item` readiness gates to make a thin item pass.

## Expected Response Shape

Return a concise proposal with:

1. `## Grounded Facts` — facts copied or summarized from the target item and resolved context.
2. `## Proposed Work-Item Patch` — a Markdown patch or replacement body sections for human review.
3. `## Grounding Notes` — which proposal bullets came from which artifacts.
4. `## Open Questions` — unresolved references, missing validation specifics, or decisions requiring human review.
5. `## Non-Goals Confirmed` — implementation work intentionally left untouched.
