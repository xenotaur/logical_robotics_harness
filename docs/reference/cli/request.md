# `lrh request`

## Command purpose

`lrh request` renders assistant-facing request prompts from LRH package templates, filesystem template overrides, and structured request renderers. It also exposes catalog and template-resolution diagnostics.

## Canonical invocation patterns

```bash
lrh request list
lrh request list --category review
lrh request describe prompt-from-work-item
lrh request describe codex_prompt_from_work_item
lrh request prompt-from-work-item --work-item-file project/work_items/active/WI-EXAMPLE.md
lrh request bootstrap-project --repo-name example --project-goal "Adopt LRH control files."
lrh request templates list
lrh request templates where review-response
lrh request templates --template-dir .lrh/templates list
lrh request templates --template-dir .lrh/templates where review-response
python -m lrh.cli.main request list
```

Work-item helper invocations include both stdout-only renderers and structured helpers with explicit output support:

```bash
lrh request ready-work-item WI-ASSIST-INSTALLABILITY-HARDENING > /tmp/ready-work-item.md
lrh request prompt-from-work-item WI-EXAMPLE > /tmp/prompt.md
lrh request run-packet-from-work-item WI-EXAMPLE --out /tmp/run-packet.md
lrh request run-report-from-work-item WI-EXAMPLE --outcome success --out /tmp/run-report.md
lrh request codex-prompt-from-work-item --work-item project/work_items/active/WI-EXAMPLE.md --slug implement-example --out /tmp/prompt.md
```

Work-item request surfaces have different responsibilities:

- `ready-work-item` renders a non-mutating refinement request for a valid but thin work item.
- `prompt-from-work-item` renders an implementation prompt after readiness issues are resolved.
- `run-packet-from-work-item` renders a non-mutating dry-run/manual run packet for an execution-ready item.
- `run-report-from-work-item` renders a manual/dry-run report from explicitly supplied outcomes, validation results, evidence, artifacts, risks, and review tasks.

These commands print Markdown to stdout unless a structured renderer supports `--out`. They do not edit work-item files, dispatch agents, run validation commands, create pull requests, merge branches, publish releases, or close lifecycle records.

## Important options and arguments

General renderer:

- `template_name`: request name. Prefer canonical names from `lrh request list`; legacy names remain supported.
- `target`: optional target path or identifier for request types that use one.
- `--target TARGET_OPTION`: named target path or identifier.
- `--template-dir TEMPLATE_DIR`: template override root containing logical paths such as `request/review_response.md`.
- `--scope {project,current_focus,work_item}`: scope for assessment request generation.
- `--repo-name REPO_NAME`, `--project-goal PROJECT_GOAL`, `--project-type PROJECT_TYPE`, `--bootstrap-mode {minimal,full}`: bootstrap-oriented inputs.
- `--background-file BACKGROUND_FILE` or `--background-text BACKGROUND_TEXT`: background context inputs. These options are mutually exclusive.
- `--audit-file AUDIT_FILE`, `--work-item-file WORK_ITEM_FILE`, `--style-file STYLE_FILE`, `--patch-file PATCH_FILE`: file inputs injected into templates that need them.
- `--force`: for `review_response`, emit the full prompt even when no unresolved review threads are found.
- `--show-vars`: print computed variables to stderr for debugging.
- `--prompt-id PROMPT_ID`: explicit prompt ID for `codex_prompt_from_work_item`; otherwise one is generated.

Catalog and template diagnostics:

- `lrh request list [--category CATEGORY]`: list cataloged requests grouped by category.
- `lrh request describe REQUEST_NAME`: show canonical metadata for a canonical or legacy name.
- `lrh request templates [--template-dir DIR] list`: show request templates and selected source.
- `lrh request templates [--template-dir DIR] where NAME`: show the selected source for one request template.
- Place `--template-dir` before `list` or `where`; the option belongs to the `templates` parent parser.

## Current behavior and limitations

- Rendered prompts are printed to stdout for the general renderer.
- `list` and `describe` are reserved catalog commands, not request template names.
- `templates` is a diagnostics namespace, not a renderable template name.
- Template override roots use logical paths such as `request/review_response.md`. Earlier `--template-dir` values have higher precedence for template diagnostics.
- Some requests are backed by structured renderers rather than plain Markdown templates.
- Completion is optional via argcomplete; use `scripts/install-completion` for setup guidance when working in this repository.

## Related how-to pages

- [Use request templates](../../how-to/use-request-templates.md)
- [Validate a project control directory](../../how-to/validate-a-project.md)


## organize-docs

`lrh request organize-docs` generates a downstream-agent prompt for one scoped documentation-organization PR. It does not reorganize documentation directly.
