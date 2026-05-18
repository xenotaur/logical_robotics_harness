# Repository state versus runtime state

LRH separates durable repository state from runtime state so that project authority remains
inspectable, reviewable, and portable.

## Repository state

Repository state is committed to Git. It includes:

- source code;
- tests;
- reusable harness code in `src/lrh/`;
- human-facing documentation in `docs/`;
- project-control artifacts in `project/`;
- maintainer scripts in `scripts/`.

For LRH-compatible projects, `project/` is the authoritative control-plane source. It should remain
human-readable and stable enough for review.

## Runtime state

Runtime state is produced or selected while LRH is running. It may include:

- parsed control-plane objects;
- validation diagnostics;
- resolved workspace context;
- generated prompt previews;
- run packets or run reports;
- local logs, cache, temporary files, and private state;
- command-line flags and environment variables.

Runtime state can be useful, but it is not automatically authoritative. Some runtime outputs may be
promoted into evidence or committed control-plane updates after human review. Other runtime data is
disposable.

## Source Markdown and structured models

The source-of-truth form for project-control files is Markdown with YAML frontmatter under
`project/`. LRH then loads that source into structured runtime objects inside the package.

This split gives LRH two benefits:

- humans can review durable project intent in ordinary Markdown files;
- code can operate on typed, validated objects instead of treating raw dictionaries as the main
  internal API.

## Why the distinction matters

Without a boundary, a tool can accidentally turn temporary observations into project truth. LRH
tries to prevent that by asking:

- Is this committed project-control state?
- Is this derived from committed state?
- Is this local runtime/cache data?
- Is this evidence that should be preserved?
- Is this merely a preview or recommendation?

Those questions matter especially for status. A local preview or generated summary should not be
reported as completed work unless it is backed by evidence.

## Safe-default local viewer boundary

The safe-default `lrh serve` viewer/workbench exposes local read-only project summaries and preview
surfaces. Its previews are not execution evidence and do not imply that rendered content has been
run. It should not be confused with an autonomous runner.

## Promotion path

A healthy LRH workflow can move information across boundaries deliberately:

1. load committed `project/` source;
2. produce runtime diagnostics, previews, or reports;
3. run human-approved work or validation;
4. save durable evidence when appropriate;
5. update work items or status based on that evidence;
6. commit reviewed repository changes.

The promotion is explicit. Runtime output does not become project truth merely because a tool
printed it.

## Authoritative sources

- [architecture design](../../project/design/architecture.md);
- [repository specification](../../project/design/repository_spec.md);
- [safe-default serve work item](../../project/work_items/resolved/WI-LRH-SERVE-SAFE-DEFAULT-MVP.md);
- [current status](../../project/status/current_status.md).
