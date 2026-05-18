# Use request templates

## Purpose

Use `lrh request` to render assistant-facing request prompts from cataloged request names or legacy template names. Use `lrh request list`, `describe`, and `templates` diagnostics to discover what is available before rendering.

Request rendering prints the generated prompt to stdout unless a structured request-specific subcommand provides an `--out` option.

## Prerequisites

- Run in a repository context when a request needs project files, work-item lookup, style guide defaults, or GitHub metadata.
- Prepare any input files required by the selected request, such as an audit report, work-item file, style guide, or patch.
- Prefer canonical flat request names shown by `lrh request list` for new usage.

## Commands

List cataloged requests:

```bash
lrh request list
```

Filter cataloged requests by category:

```bash
lrh request list --category review
```

Describe one canonical or legacy request name:

```bash
lrh request describe prompt-from-work-item
```

Render a prompt from one work item:

```bash
lrh request prompt-from-work-item --work-item-file project/work_items/active/WI-EXAMPLE.md
```

Render a bootstrap-oriented request:

```bash
lrh request bootstrap-project --repo-name example-repo --project-goal "Adopt LRH project control files."
```

Inspect template override resolution:

```bash
lrh request templates list
lrh request templates where review-response
```

Use a filesystem template override root:

```bash
lrh request --template-dir .lrh/templates review-response https://github.com/owner/repo/pull/123
```

Use module invocation when needed:

```bash
python -m lrh.cli.main request list
```

## Expected output or success criteria

- `lrh request list` prints request names grouped by category.
- `lrh request describe <name>` prints canonical metadata, legacy names, template source, implementation target, and usage.
- Render commands print the generated prompt text to stdout and exit `0` on success.
- Template diagnostics print the selected template source and origin.

## Common troubleshooting notes

- `list` and `describe` are reserved catalog commands, not renderable request names.
- `templates` is also a diagnostics namespace. Use `lrh request templates list` or `lrh request templates where <name>`.
- `--template-dir` expects a root containing logical paths such as `request/review_response.md`; pass it more than once only when you need explicit override precedence.
- Some requests validate their inputs. For example, a work-item prompt needs a resolvable work-item file or identifier.

## Related reference

- [CLI reference: `request`](../reference/cli/request.md)
- [How to validate a project](validate-a-project.md)
