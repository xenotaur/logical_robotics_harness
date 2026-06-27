<!-- Skill reference: .claude/skills/lrh-doc-organize/references/ -->
# PR Request: Organize Documentation (one scoped PR)

Target agent: {{REQUEST_TARGET_AGENT}}

Prompt ID: PROMPT(AD_HOC:REQUEST_ORGANIZE_DOCS)[YYYY-MM-DDThh:mm:ss±hh:mm]

## Request inputs

- `repo_root`: `{{REQUEST_REPO_ROOT}}`
- `project_root`: `{{REQUEST_PROJECT_ROOT}}`
- `docs_root`: `{{REQUEST_DOCS_ROOT}}`
- `control_root`: `{{REQUEST_CONTROL_ROOT}}`
- `audit`: `{{AUDIT_PATH}}`
- `phase`: `{{REQUEST_ORGANIZE_DOCS_PHASE}}`

## Task

Implement exactly one scoped documentation-organization PR. This request generates a downstream implementation prompt; it does not directly reorganize docs by itself.

1. Follow the target repository's `AGENTS.md`, `STYLE.md`, and `PROMPTS.md` if present.
2. If the target repository uses LRH prompt records, run exact prompt-id soft-idempotence lookup before edits and follow repository rerun rules.
3. Keep changes to one scoped PR and one phase unless this prompt explicitly asks otherwise.
4. Avoid broad rewrites, drive-by refactors, and formatting churn.

## Scope source

- When `audit` is provided: read the docs audit artifact first and treat its "Proposed first PR scope" as the default implementation scope.
- When `audit` is not provided: run a small discovery pass before editing and do not make broad moves based on assumptions.

## Required constraints for the downstream PR

1. Preserve or stub moved paths when needed so existing links/usages are not silently broken.
2. Update affected `README.md` files in touched folders.
3. Keep Diátaxis categories distinct:
   - tutorials teach guided learning paths
   - how-to guides solve specific tasks
   - reference describes exact commands, schemas, formats, and behavior
   - explanations describe rationale and concepts
4. Preserve the project/docs boundary:
   - `project/` remains authoritative project-control-plane state
   - `docs/` remains the human-facing learning, task, reference, and explanation layer
5. Avoid presenting planned behavior as implemented behavior.
6. Run appropriate validation for changed docs/commands.
7. Create or update a prompt execution record if the target project uses LRH prompt records.

## Output expectations

- Open one small, reviewable PR implementing only the scoped phase.
- Summarize what was changed, what was intentionally deferred, and validation run results.
