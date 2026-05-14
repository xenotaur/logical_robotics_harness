# Request Command Naming Design and Audit

## Purpose

This document audits the current `lrh request` naming surface and defines a
compatibility-preserving roadmap for clearer request command names. It is a
design record only: it does not rename packaged templates, change CLI behavior,
add grouped subcommands, or introduce short aliases.

Dogfooding showed that names such as `codex-prompt-from-work-item` and
`pr-against-work-item` are long, unevenly verb-oriented, and not easy to scan.
The near-term goal is to establish stable canonical names before any migration
implementation.

## Current request-template inventory

The package-owned request templates currently live under
`src/lrh/assist/templates/request/`. The template discovery surface exposes file
stems as request template names, while one structured compatibility command
currently exposes a kebab-case wrapper for the work-item prompt path.

| Template file | Current template name | Current direct command surface | Notes |
| --- | --- | --- | --- |
| `assessment.md` | `assessment` | `lrh request assessment --scope ...` | Repository, focus, or work-item assessment prompt. |
| `bootstrap_project.md` | `bootstrap_project` | `lrh request bootstrap_project ...` | Bootstrap an LRH `project/` directory. |
| `ci_assess_status.md` | `ci_assess_status` | `lrh request ci_assess_status ...` | Read-only CI feasibility/status assessment. |
| `ci_implement_workflow.md` | `ci_implement_workflow` | `lrh request ci_implement_workflow ...` | CI workflow implementation request. |
| `codex_prompt_from_work_item.md` | `codex_prompt_from_work_item` | `lrh request codex_prompt_from_work_item ...`; structured wrapper: `lrh request codex-prompt-from-work-item ...` | Generates a Codex Cloud-ready prompt from a work item. |
| `improve_coverage.md` | `improve_coverage` | `lrh request improve_coverage ...` | Targeted test coverage improvement request. |
| `pr_against_work_item.md` | `pr_against_work_item` | `lrh request pr_against_work_item ...` | Review a patch or pull-request-style change against a work item. |
| `review_protocol.md` | `review_protocol` | `lrh request review_protocol ...`; primarily included by `review_response` | Packaged review guidance helper; not expected to become a normal user-facing task command. |
| `review_response.md` | `review_response` | `lrh request review_response ...` | Resolve or respond to pull-request review feedback. |
| `work_items_from_audit.md` | `work_items_from_audit` | `lrh request work_items_from_audit ...` | Convert an audit report into proposed work items. |

## Canonical naming convention

Future canonical request names should follow these rules:

1. Use lowercase kebab-case in CLI-visible names.
2. Prefer verb-oriented, task-shaped names that describe the user outcome.
3. Avoid acronyms in canonical names when a clear non-acronym name is practical.
4. Keep names stable once promoted to canonical status.
5. Keep template filenames and internal logical paths decoupled from CLI command
   names so packaged resources can migrate safely.
6. Treat short aliases as optional power-user conveniences only after canonical
   names are stable; short aliases must not become the documented canonical
   vocabulary.

The acronym rule should be applied strictly for new canonical names.
Project-specific brand names or ecosystem labels may remain in descriptions,
help text, and legacy aliases, but canonical request names should not require
users to understand an acronym when a concise plain-English verb phrase is
available.

## Proposed canonical mappings

| Current / legacy name | Proposed canonical name | Category | Rationale |
| --- | --- | --- | --- |
| `codex_prompt_from_work_item`; `codex-prompt-from-work-item` | `prompt-from-work-item` | `generate` | Focuses on the generated artifact instead of the vendor or execution environment. |
| `pr_against_work_item`; `pr-against-work-item`; candidate transitional alias `review-pr-against-work-item` | `review-pull-request-against-work-item` | `review` | Makes the review action explicit, expands the acronym, and preserves the work-item comparison target. |
| `work_items_from_audit`; `work-items-from-audit` | `work-items-from-audit` | `propose` | Already clear and task-shaped; canonical form should be kebab-case. |
| `assessment` | `assess-repository` | `assess` | Replaces a noun with a verb phrase and clarifies the default repository-level task. Scope flags can still narrow to current focus or a work item. |
| `bootstrap_project`; `bootstrap-project` | `bootstrap-project` | `generate` | Existing intent is clear; canonical form should be kebab-case. |
| `ci_assess_status`; `ci-assess-status`; candidate transitional alias `assess-ci-status` | `assess-continuous-integration-status` | `assess` | Moves the verb first and expands the acronym in the canonical name. |
| `ci_implement_workflow`; `ci-implement-workflow`; candidate transitional alias `implement-ci-workflow` | `implement-continuous-integration-workflow` | `implement` | Moves the implementation verb first, describes the concrete output, and expands the acronym in the canonical name. |
| `improve_coverage`; `improve-coverage` | `improve-coverage` | `implement` | Existing verb phrase is suitable; canonical form should be kebab-case. |
| `review_response`; `review-response` | `review-response` | `review` | Existing verb phrase is suitable; canonical form should be kebab-case. |
| `review_protocol`; `review-protocol` | No normal task command; keep as packaged helper or diagnostic-only template | `generic` | This is support material for review prompts, not a primary user task. |

## Category taxonomy

Categories describe intent and can later inform help text, command grouping, and
flag organization. They are not a request-catalog implementation plan by
themselves.

- `generate`: create a prompt, scaffold, report input, or other artifact without
  necessarily changing target project behavior.
- `review`: evaluate a response, patch, pull request, or review thread against
  declared criteria.
- `propose`: convert analysis into candidate planning artifacts for human review.
- `assess`: inspect repository state and produce an evidence-backed assessment
  without modifying files.
- `implement`: request a bounded code or configuration change.
- `render` or `generic`: reserved for low-level template rendering, diagnostics,
  and packaged helper material that should not be promoted as a primary task.

## Grouped subcommand decision criteria

Grouped subcommands such as `lrh request generate ...`, `lrh request review ...`,
`lrh request propose ...`, and `lrh request assess ...` may improve discoverability,
but they add parser surface area and migration cost. They should be added only if
most of the following criteria are met:

1. The request catalog is large enough that a flat list is hard to scan in help
   output or shell completion.
2. Several commands in a category share flags, validation rules, or target
   semantics that would be clearer under a category-specific parser.
3. User documentation benefits from teaching task groups rather than individual
   template names alone.
4. The grouped form can coexist with flat canonical names without ambiguous
   parsing or surprising precedence.
5. Template override diagnostics remain simple; users can still determine which
   packaged or overridden template backs a command.
6. The implementation can preserve legacy aliases without creating two unrelated
   code paths for request rendering.

Until those criteria are met, prefer a flat canonical surface:

```text
lrh request prompt-from-work-item ...
lrh request review-pull-request-against-work-item ...
lrh request assess-repository ...
lrh request assess-continuous-integration-status ...
```

If grouping is adopted later, grouped names should be additive discoverability
wrappers first, not replacements for the flat canonical names:

```text
lrh request generate prompt-from-work-item ...
lrh request review pull-request-against-work-item ...
lrh request assess repository ...
```

## Compatibility policy

Compatibility should be conservative because users may have existing scripts,
prompt-generation workflows, and template overrides.

1. Existing snake_case template names remain supported as legacy aliases during
   the migration.
2. Existing kebab-case compatibility wrappers, including
   `codex-prompt-from-work-item`, remain supported as legacy aliases during the
   migration.
3. Legacy aliases should render the same packaged or overridden template as the
   canonical name unless a future explicit migration document says otherwise.
4. Documentation should prefer canonical names once they are implemented, while
   mentioning legacy names only where needed for migration.
5. Any future removal of a legacy name requires a separate explicit deprecation
   plan, including warning behavior, release notes, and a minimum support window.
6. Short aliases, if introduced, are optional conveniences. They must not be used
   in canonical docs, execution records, or generated prompts unless a user
   explicitly requests them.

## Recommended migration sequence

1. Land this audit and naming roadmap with no broad CLI behavior changes.
2. Add a request catalog layer that maps canonical command names, legacy aliases,
   categories, template logical names, and request-specific validation metadata.
3. Teach `lrh request templates list` or a new diagnostic command to show
   canonical names and legacy aliases without hiding template logical paths.
4. Add canonical kebab-case command names while keeping all current names working.
5. Update user-facing help and documentation to prefer canonical names.
6. Add tests that prove canonical names and legacy aliases resolve to the same
   request behavior.
7. Reassess grouped subcommands using the criteria above after the canonical flat
   surface has been used in practice.
8. Consider short aliases only after canonical names and any grouped structure are
   stable.
9. If legacy-name removal is ever desired, create a separate deprecation plan and
   PR; do not bundle removal with canonical-name introduction.

## Non-goals for this design step

- Do not implement the request catalog in this PR.
- Do not rename packaged template files in this PR.
- Do not add grouped subcommands in this PR.
- Do not add short aliases in this PR.
- Do not remove or warn on legacy names in this PR.
