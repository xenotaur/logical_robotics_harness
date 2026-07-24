# LRH Assistants

This directory holds **LRH assistants** — a first-class artifact class defined
by [`PROP-LRH-ASSISTANTS`](../design/proposals/adopted/lrh-assistants/00_proposal.md).

An **assistant** is a persistent, backend-neutral organizational *role* that an
arbitrary capable agent (Claude, Codex, Jules, or a human) can instantiate. It
accepts a bounded workstream-management assignment, maintains planning
artifacts, supervises run trees, handles routine review under policy,
communicates with its human supervisor, and accumulates reviewed institutional
knowledge. It models **how an assigned manager operates** — an axis orthogonal
to the planning tree (what the project is doing), the run tree (execution), and
contributor records (who acted).

An assistant is **not** a contributor/actor record, a model session, a planning
node, a workstream, a run, an independent source of live project state, or an
unbounded autonomous process.

## Status

This is the **Stage 1** documentation-only convention. There is no Python,
loader, validation, or CLI yet — those arrive in later stages of
[`WS-LRH-ASSISTANTS`](../workstreams/active/WS-LRH-ASSISTANTS.md). Today the
package is read directly by any filesystem-capable human or agent.

## Layout

```
project/assistants/
  README.md              ← this file
  token-vocabulary.md    ← authoritative capability/permission/... token catalog
  <assistant-slug>/
    README.md              ← universal entry point + recommended read order
    assistant.md           ← canonical charter (frontmatter: id, kind, status, …)
    scope.md               ← what it manages vs. what it may inspect
    policy.md              ← capabilities, permission_ceiling, obligations, prohibitions, escalations
    preferences.md         ← ordered soft guidance (never overrides policy)
    communication-policy.md← semantic message model + cadence
    context-policy.md      ← how context is derived (never stored live)
    review-policy.md       ← review outcomes and the independent-verification obligation
    SKILL.md               ← portable operating entry point
    references/            ← loaded only as needed (progressive disclosure)
    memory/                ← proposed / accepted / retired reviewed knowledge
    evaluations/           ← behavioral and structural evaluation material
```

## What is authoritative

The assistant directory holds **stable role configuration only**. It is *not*
authoritative for any live state — current tasks, workstream stage, active work
items, branch/PR/CI/review state, awaited decisions, evidence, completion, or
closeout. Those live in workstreams, work items, runs, evidence, and status,
exactly as they do today. An assistant directory must never contain
`state.yaml`, `tasks/`, `current.md`, or `blockers.md`.

Lifecycle state lives in each package's `assistant.md` (`status:
active | inactive | deprecated`), **not** in directory buckets, so package
paths stay stable and skill references never break.

## Discovery

An assistant is exactly a directory containing an `assistant.md`
(`project/assistants/*/assistant.md`). Not every Markdown file here is an
assistant.

## Reading an assistant

Follow the package's own `README.md` read order (`assistant.md` → `scope.md` →
`policy.md` → … → `SKILL.md`). Once tooling exists (Stage 5), a derived,
provenance-rich view will be available via `lrh assistant context <ID> --view
current`; until then, inspect the files directly and the root workstream that
declares the assistant in `managed_by`.

## Authority, in one line

Capabilities describe what a role *knows how to do*; a `permission_ceiling`
caps what may *ever* be granted; the **active** grant comes from a workstream
binding and narrows monotonically
(`role ceiling ∩ binding grant ∩ work-item readiness ∩ run-packet authority ∩
backend capability`). Preferences and memory are advisory and can never expand
scope, grant authority, or bypass a gate. Until the
[constitutional sandbox envelope](../design/proposals/proposed/constitutional-sandbox-envelope/00_proposal.md)
enforces these, they are `prompt_enforced_only`, not hard runtime guarantees.
