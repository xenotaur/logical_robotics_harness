# Control-plane model

LRH's control plane is the repository-native project state that tells humans and tools what the
project is trying to do, what is active, what constraints apply, and what evidence supports status.

The short form is:

```text
Principles → Project Goal → Roadmap → Current Focus → Work Items → Evidence → Status
```

The broader architecture also describes guardrails as a consequences plane that constrains action
selection and review.

## `project/` is authoritative

For any LRH-compatible repository, the `project/` directory is the authoritative project control
plane. It contains human-readable Markdown documents with YAML frontmatter. Those files are meant
to be reviewed in Git, discussed by maintainers, loaded by LRH, and validated for consistency.

The `docs/` directory has a different job: it teaches, explains, and guides people. Documentation
may summarize project-plane ideas, but it must not silently fork the authoritative state. If a
reader needs the current plan, current focus, accepted decision, or current evidence, link them
back to `project/`.

## The main layers

### Principles

Principles capture durable norms and constraints: engineering expectations, evaluation standards,
and project values. They sit at the broadest layer because they shape every lower layer.

### Project goal

The project goal defines what the repository is for and what success should mean. It translates
principles into a project-specific destination.

### Roadmap

The roadmap organizes medium-term phases, milestones, and workstreams. It should explain how the
project expects to move from the current state toward the goal.

### Current focus

Current focus is the near-term operating charter. It narrows the roadmap into what maintainers are
actively trying to advance now.

### Work items

Work items are typed units of work. LRH preserves these categories at minimum:

- `deliverable`
- `investigation`
- `evaluation`
- `operation`

Work items can be proposed, active, resolved, or abandoned. Their metadata is authoritative; path
buckets are a human-readable organization that validation can check against metadata.

### Evidence

Evidence is the proof layer: tests, logs, reports, screenshots, review notes, metrics, release
checks, or other artifacts that support claims about what happened.

### Status

Status should be synthesized from the current focus, work state, and evidence. It should not be an
optimistic narrative detached from proof.

### Guardrails

Guardrails describe safety, cost, optics, and approval constraints. They are consequences-plane
constraints used to block or narrow action, not positive plans by themselves.

## Source documents and runtime objects

LRH intentionally separates source documents from runtime objects:

- source Markdown lives under `project/`;
- runtime structured objects live inside `src/lrh/` when LRH loads and validates a project.

This keeps the project state reviewable by humans while still giving the harness typed data to
validate and operate on. Raw dictionaries may appear at parsing boundaries, but the long-term API
should be typed and explicit where a control-plane model is appropriate.

## Current implementation priority

The implementation priority remains the smallest useful end-to-end path:

1. core control-model classes;
2. Markdown/frontmatter parsing;
3. project directory loading;
4. precedence resolution and validation checks;
5. `lrh validate`.

Deeper orchestration and integration should not outrun this foundation.

## Authoritative sources

For authoritative definitions and current details, see:

- [architecture design](../../project/design/architecture.md);
- [repository specification](../../project/design/repository_spec.md);
- [principles](../../project/principles/principles.md);
- [project goal](../../project/goal/project_goal.md);
- [roadmap](../../project/roadmap/roadmap.md);
- [current focus](../../project/focus/current_focus.md);
- [work item README](../../project/work_items/README.md).
