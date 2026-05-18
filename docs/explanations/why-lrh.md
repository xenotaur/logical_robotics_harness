# Why LRH exists

Logical Robotics Harness (LRH) exists to make AI-assisted repository work structured,
inspectable, and evidence-backed instead of conversationally ad hoc.

LRH treats a repository as more than source code. A project also needs durable answers to
questions such as:

- What principles constrain the work?
- What goal is the project trying to reach?
- What roadmap and current focus should guide near-term choices?
- What work items are active, proposed, resolved, or abandoned?
- What evidence supports claims about progress?
- What is actually true about project status right now?

The repository's `project/` directory is where those answers live. LRH then provides reusable
harness code that can load, validate, summarize, and eventually help operate against that
control-plane state.

## The problem LRH is trying to solve

AI-assisted development can move quickly, but speed alone creates failure modes:

- decisions are buried in chat history instead of committed project artifacts;
- agents act from incomplete or stale context;
- status summaries become optimistic prose rather than evidence-backed statements;
- follow-up work loses the reasoning that produced previous changes;
- each repository invents its own lightweight process from scratch.

LRH addresses those problems by making project intent, execution scope, evidence, and status
repository-native. The goal is not to remove human judgment. The goal is to give humans and
assistive agents the same durable map of what is allowed, what is active, and what has been
verified.

## Harness, not client project

LRH is intentionally reusable. The harness code lives in `src/lrh/` in this repository, but it
should not be hard-coded to this repository. A downstream project can have its own `project/`
control plane, and LRH should be able to operate against that target repository as a client.

This LRH repository is self-hosting at the control-plane level: its own `project/` directory
describes LRH's principles, goals, roadmap, focus, work items, evidence, and status. That makes
LRH a test subject for its own model, but it does not make LRH's project state part of the
reusable package API.

## What LRH is now

At the current stage, LRH is centered on the control-plane slice: Markdown plus frontmatter
control files, typed runtime models, project loading, precedence, validation, assist request
surfaces, snapshots, and safe-default local viewing. The first important command remains the
validation path:

```bash
lrh validate
```

That command is valuable because it checks whether the repository's human-authored control plane
is coherent enough to support later workflows.

## What LRH is not

LRH is not currently a fully autonomous engineering organization, a replacement for project
maintainers, or a security sandbox. Future agentic capabilities are expected to remain explicit
and bounded. The safe-default package and CLI should remain useful without autonomous dispatch,
branch mutation, PR creation, or merge/publish automation.

## Authoritative sources

This page explains the rationale in human-facing language. It does not supersede the control-plane
artifacts. For authority, see:

- [root README](../../README.md) for the repository overview;
- [architecture design](../../project/design/architecture.md) for the current architectural model;
- [repository specification](../../project/design/repository_spec.md) for the expected project layout;
- [project goal](../../project/goal/project_goal.md) for LRH's own goal;
- [current status](../../project/status/current_status.md) for current project state.
