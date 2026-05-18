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
python -m lrh.cli.main request list
```

Structured work-item helpers with explicit output support are also implemented:

```bash
lrh request run-packet-from-work-item WI-EXAMPLE --out /tmp/run-packet.md
lrh request run-report-from-work-item WI-EXAMPLE --outcome success --out /tmp/run-report.md
lrh request codex-prompt-from-work-item --work-item project/work_items/active/WI-EXAMPLE.md --slug implement-example --out /tmp/prompt.md
```

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
- `lrh request templates list [--template-dir DIR]`: show request templates and selected source.
- `lrh request templates where NAME [--template-dir DIR]`: show the selected source for one request template.

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
