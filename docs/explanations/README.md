# Explanations

Explanations describe LRH concepts, rationale, tradeoffs, and design background.

## What belongs here

- Conceptual overviews that help readers understand LRH's model.
- Rationale for accepted architecture and workflow choices.
- Comparisons, tradeoffs, and context that make reference and how-to material easier to apply.
- Links to authoritative decisions or proposals under [`../../project/`](../../project/) when design authority matters.

## What does not belong here

- Step-by-step task recipes.
- First-time guided exercises.
- Exact command catalogs, schemas, or file-format definitions.
- Duplicated project-control records, evidence, or active status.

## How to decide whether to add content here

Add content here when the reader is asking “why?”, “what does this mean?”, or “how should I think about this?”. If the content tells them exactly what to type or how to complete a task, use [how-to guides](../how-to/README.md). If it defines stable behavior, use [reference](../reference/README.md).

## Currently relevant docs

- [Why LRH exists](why-lrh.md) — rationale for a repository-native, evidence-backed harness.
- [Control-plane model](control-plane-model.md) — how principles, goals, roadmap, focus, work items, evidence, status, and guardrails fit together.
- [Precedence model](precedence-model.md) — how higher-authority control-plane layers constrain lower-authority execution context.
- [Evidence-backed status](evidence-backed-status.md) — why LRH status should be grounded in durable proof.
- [Repository state versus runtime state](repository-state-vs-runtime-state.md) — how committed project state differs from derived runtime objects and local tool state.
- [Prompt-driven workflow](prompt-driven-workflow.md) — how prompt IDs and execution records support traceability.
- [Why work-item validation, audit, readiness, and prompting are separate](work-item-lifecycle-boundaries.md) — explains the lifecycle boundaries that keep planning, execution, and evidence closeout distinct.
- [Workspace and meta model](workspace-and-meta-model.md) — how workspace catalogs coordinate multiple LRH-compatible repositories without replacing project-local authority.

Existing rationale in [`../../project/design/`](../../project/design/) and [`../../project/memory/`](../../project/memory/) remains authoritative project-control material. These explanations summarize and teach concepts; they do not replace or supersede the project control plane.
