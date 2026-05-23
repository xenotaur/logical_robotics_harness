# Documentation Audit Request (Prompt-Generating Only)

Target agent: {{REQUEST_TARGET_AGENT}}

Prompt ID: PROMPT(AD_HOC:REQUEST_AUDIT_DOCS)[YYYY-MM-DDThh:mm:ss±hh:mm]

## Inputs

- `repo_root`: `{{REQUEST_REPO_ROOT}}`
- `project_root`: `{{REQUEST_PROJECT_ROOT}}`
- `docs_root`: `{{REQUEST_DOCS_ROOT}}`
- `control_root`: `{{REQUEST_CONTROL_ROOT}}`
- `package_root` values:
{{REQUEST_PACKAGE_ROOTS}}
- suggested audit artifact path: `{{REQUEST_AUDIT_OUTPUT}}`

## Task

Perform a documentation audit of the target repository's current reality. This request must generate a docs-audit artifact and must not reorganize docs in this PR.

### Requirements

1. Follow repository instructions from `AGENTS.md`, `STYLE.md`, and `PROMPTS.md` when present.
2. If LRH prompt workflow is used, check prior execution records for this exact prompt ID and apply soft-idempotence rules before changes.
3. Discover the real repository layout instead of assuming fixed paths:
   - do not assume `repo_root == project_root`
   - do not assume `docs_root == repo_root/docs`
   - do not assume `control_root == repo_root/project`
   - do not assume `package_root == repo_root/src/<package>`
4. Inspect existing docs, top-level and package READMEs, control-plane artifacts, module/package layout, and relevant tests/scripts/examples/notebooks/CLI help.
5. Identify stale links, moved paths, and navigation gaps.
6. Classify documentation needs using Diátaxis:
   - tutorials
   - how-to guides
   - reference
   - explanations
7. Distinguish implemented behavior from planned behavior.
8. Identify docs/control-plane boundary issues and accuracy mismatches.
9. Recommend a target documentation structure and phased PR plan.
10. Write the docs audit artifact at `{{REQUEST_AUDIT_OUTPUT}}` (or an explicitly justified alternative).
11. If the target repository uses LRH execution records, create/update the execution record for this prompt run.

### Guardrails

- Do **not** reorganize documentation in this audit request PR.
- Allow only tiny, clearly necessary README/link adjustments when explicitly justified in the audit notes.
- Keep recommendations evidence-backed with concrete file/path references.
