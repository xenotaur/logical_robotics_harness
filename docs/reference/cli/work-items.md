# `lrh work-items`

## Command purpose

`lrh work-items` provides deterministic checks and reports for work-item source
files under `project/work_items/`. These commands read project-control files and
report structure, lifecycle, traceability, and prompt-readiness signals. They do
not perform semantic closeout, execute work, or mutate files unless an explicitly
mutating helper such as `organize --apply` is used.

## Organization

```bash
lrh work-items organize
lrh work-items organize --dry-run
lrh work-items organize --check
lrh work-items organize --apply
lrh work-items organize --project-root /path/to/repository --check
```

`organize` is a conservative status-bucket helper. By default, and with
`--dry-run`, it previews frontmatter or path changes that would make work-item
files match the status-bucket layout. `--check` exits non-zero when mechanical
organization changes are still needed and is appropriate for validation
contexts. `--apply` performs only those mechanical organization changes.

Use `organize` for bucket/frontmatter hygiene, not semantic lifecycle decisions.
It should not decide whether a work item is complete, abandoned, prompt-ready,
or evidence-closed.

## Validation

```bash
lrh work-items validate
lrh work-items validate --project-root /path/to/repository
```

`validate` checks work-item hygiene: parseable frontmatter, required identity and
status fields, filename and status-bucket consistency, duplicate IDs, terminal
resolution metadata, structured dependency references, selected metadata
references, and dependency cycles.

Use `validate` before interpreting lifecycle state, but do not use it as a
readiness gate for thin proposed items. A proposed work item can be valid even
when it is not detailed enough for implementation prompting.

## Lifecycle audit

```bash
lrh work-items audit --format md
lrh work-items audit --format json
lrh work-items audit --project-root /path/to/repository --format json
```

`audit` emits a non-mutating lifecycle report. The Markdown form is intended for
human review and prompt context; the JSON form is intended for tooling and saved
evidence artifacts. Audit combines validation diagnostics with deterministic
traceability signals, such as missing linkage metadata, terminal items lacking
resolution evidence, or execution records attached to non-terminal items.

Use `audit` to find stale or weakly linked work items. Do not treat audit output
as a semantic completion decision: acceptance criteria still need concrete code,
test, documentation, evidence, report, or review support before closeout.

## Readiness diagnosis

```bash
lrh work-items readiness
lrh work-items readiness --status proposed --format md
lrh work-items readiness --status proposed --format json
lrh work-items readiness WI-ASSIST-INSTALLABILITY-HARDENING
```

`readiness` diagnoses whether work items contain the execution-facing sections
needed for `lrh request prompt-from-work-item`, such as `Scope`, `Required
Changes`, `Acceptance Criteria`, and `Validation`. It also reports conservative
promptability blockers such as blocked or terminal lifecycle state.

Use `readiness` after validation and audit when choosing an item for
implementation prompting. It diagnoses missing details; it does not refine the
item, edit Markdown, dispatch an executor, or decide project closeout.

## Lifecycle checkpoint terms

- **Valid**: structural and referential work-item hygiene passes.
- **Audited**: deterministic lifecycle and traceability signals have been
  reported for review.
- **Ready**: implementation-facing sections are present and detailed enough for
  a bounded prompt.
- **Promptable**: readiness gates pass and no lifecycle blocker prevents prompt
  rendering.
- **Executed**: a human or agent has actually performed the implementation work.
- **Evidence-closed**: closeout is supported by validation results, artifacts,
  evidence records, reports, or review notes and has been reviewed by a human.

## Related request surfaces

- [`lrh request`](request.md) documents assistive renderers such as
  `ready-work-item`, `prompt-from-work-item`, `run-packet-from-work-item`, and
  `run-report-from-work-item`.
- [How to manage the work-item lifecycle](../../how-to/manage-work-item-lifecycle.md)
  shows how to combine validation, audit, readiness, prompting, and reporting.
