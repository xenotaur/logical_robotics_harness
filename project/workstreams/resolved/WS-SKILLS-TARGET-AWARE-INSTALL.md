---
id: WS-SKILLS-TARGET-AWARE-INSTALL
kind: planning_node
title: Target-Aware LRH Skills Install for Codex
status: resolved
stage: closed
origin: proposal
summary: >
  Govern staged implementation of target-aware `lrh skills install`, making
  Codex's `.agents/skills/` directories first-class install targets alongside
  Claude's `.claude/skills/` directories while preserving LRH's canonical skill
  source model.
related_design:
  - project/design/proposals/adopted/lrh-skills-target-aware-install/00_proposal.md
  - project/design/proposals/adopted/lrh-skills-target-aware-install/backlog.md
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
  - src/lrh/skills/installer.py
  - docs/how-to/keep-skills-up-to-date.md
work_items:
  - WI-SKILLS-TARGET-AWARE-INSTALL
  - WI-SKILLS-SOURCE-ABSTRACTION
  - WI-SKILLS-REPO-CONFIG
  - WI-SKILLS-RENDER-ADAPTERS
  - WI-SKILLS-STATUS-CHECK
  - WI-SKILLS-ANTIGRAVITY-TARGET
  - WI-SKILLS-BODY-PROSE-NEUTRALIZATION
exit_criteria:
  - `lrh skills install --target claude|codex|all` implemented with existing Claude behavior preserved by default
  - Codex user and project installs write to `~/.agents/skills/` and `./.agents/skills/` respectively
  - Target-aware install planning, conflict handling, dry-run, force, and diff behavior covered by tests
  - Source abstraction, repo config, render adapters, and status/check command stages either resolved or explicitly deferred with follow-up work items
  - Codex render adapter preserves manual-only invocation semantics through `agents/openai.yaml` policy output
  - Proposal-local Codex compatibility backlog exists and captures session-observed Claude-specific skill friction
  - PROP-LRH-SKILLS-TARGET-AWARE-INSTALL adopted or superseded with implementation status updated
---

## Purpose

This workstream governs implementation of
`PROP-LRH-SKILLS-TARGET-AWARE-INSTALL`, which expands LRH skill installation
from a Claude-only copy operation into a target-aware installer that can place
LRH skills into Claude and Codex local skill directories.

The immediate motivation is to make Codex a first-class LRH execution target:
Codex should be able to discover project-local or user-local LRH skills from
`.agents/skills/`, while LRH continues to treat `src/lrh/skills/` as the
canonical source of truth and treats `.claude/skills/` and `.agents/skills/`
as generated install targets.

## Scope

- Add `--target claude|codex|all` to `lrh skills install`, preserving the
  current Claude default behavior.
- Install Codex skills to the correct user and project target directories:
  `~/.agents/skills/` and `./.agents/skills/`.
- Extend existing install safety behavior across all targets, including
  dry-run, force, diff, user-modified detection, symlink safety, and no script
  execution during install.
- Introduce internal source, target, install-plan, result, and renderer
  concepts incrementally so later stages can add source abstraction and render
  adapters without replacing the installer again.
- Add repository-local skill configuration through `project/agent_skills.yaml`
  after the first target-aware install slice.
- Add Claude and Codex render adapters, including Codex `agents/openai.yaml`
  output for invocation policy.
- Add status/check commands for installed skill targets.
- Maintain a proposal-local Codex compatibility backlog for issues discovered
  when Claude-authored LRH skills are dogfooded in Codex.
- Track body-prose neutralization as explicit follow-on work rather than
  assuming direct copies are fully agent-neutral.

## Prior Art Check

### Duplication search

- **In-repo:** `WS-SKILLS` resolved the original Claude Code skills
  infrastructure and installer mirror, but it does not cover Codex targets,
  target-aware CLI flags, render adapters, or `.agents/skills/`. No existing
  `WS-SKILLS-TARGET-AWARE-INSTALL` or `WI-SKILLS-TARGET-AWARE-INSTALL` was
  found.
- **Related proposed work:** `WS-SKILLS-EXECUTE` governs chain-running LRH
  skills (`/lrh-land`, `/lrh-execute`, `/lrh-next`, `/lrh-run-tree`). It uses
  the skills infrastructure but does not implement multi-target installation.
- **Design source:** `PROP-LRH-SKILLS-TARGET-AWARE-INSTALL` is the governing
  proposal and explicitly recommends a workstream because the implementation is
  multi-stage.
- **Recommendation:** Proceed with a new workstream.

### Demand search

- **Proposal demand:** `PROP-LRH-SKILLS-TARGET-AWARE-INSTALL` identifies the
  concrete demand: Codex needs first-class access to LRH skills through
  `.agents/skills/`, while ChatGPT export remains blocked on separate research.
- **Session demand:** During Codex dogfooding of `/lrh-workstream`, we observed
  Claude-specific execution-record provenance, slash-command framing, and
  metadata assumptions that should be tracked as Codex compatibility backlog
  items before they become implementation surprises.
- **Recommendation:** File the workstream and keep the proposal-local backlog
  open as an input to later burn-down work.

## Work Items

Delivery follows the staged implementation plan in
`PROP-LRH-SKILLS-TARGET-AWARE-INSTALL`:

- **WI-SKILLS-TARGET-AWARE-INSTALL** — First implementation slice. Add
  `--target claude|codex|all`; preserve current Claude default behavior;
  support Codex user and project installs through `~/.agents/skills/` and
  `./.agents/skills/`; carry existing `--dry-run`, `--force`, and `--diff`
  behavior across targets; direct-copy current skill bodies with the known
  Claude-prose caveat; add focused tests and docs.

- **WI-SKILLS-SOURCE-ABSTRACTION** — Add source resolution for package,
  current-repo, and explicit-path skill sources. Keep canonical source
  directories authoritative and target directories generated.

- **WI-SKILLS-REPO-CONFIG** — Add `project/agent_skills.yaml` parsing and
  precedence rules. This work item must address the proposal's parser
  constraint by using a real YAML parser or adding regression coverage for
  quoted list elements if the existing simple parser is reused.

- **WI-SKILLS-RENDER-ADAPTERS** — Split target rendering into Claude and Codex
  renderers. The Codex renderer must emit or preserve `agents/openai.yaml`
  where needed and translate Claude manual-only invocation metadata into
  Codex's invocation-policy mechanism.

- **WI-SKILLS-STATUS-CHECK** — Add `lrh skills check` and `lrh skills status`
  so maintainers can inspect canonical/target drift, unsupported metadata,
  local modifications, and per-target install state before writing.

- **WI-SKILLS-BODY-PROSE-NEUTRALIZATION** — Burn down Claude-specific body
  prose across LRH skills. Use the proposal-local backlog to identify concrete
  cases where a Claude-authored skill creates friction for Codex.

ChatGPT Skills export is intentionally not scheduled in this workstream until
the hosted upload/registration contract is researched and confirmed. If that
research becomes actionable, file a separate proposal or extend this workstream
with an explicit work item.

## Exit Criteria

- `lrh skills install` accepts `--target claude|codex|all`.
- Existing `lrh skills install` behavior remains Claude-compatible by default.
- `--local --target codex` installs to `./.agents/skills/`; user-scope Codex
  installs write to `~/.agents/skills/`.
- Dry-run, diff, force, local-modification, and symlink-safety behavior are
  tested for both Claude and Codex targets.
- Installer internals expose enough source/target/plan/result structure for
  follow-on source abstraction and rendering stages without another wholesale
  rewrite.
- Codex render adapter work preserves explicit/manual invocation policy instead
  of silently changing formerly manual-only LRH skills.
- `lrh skills check` and `lrh skills status` report target drift and
  compatibility issues in a human-readable form.
- `project/design/proposals/proposed/lrh-skills-target-aware-install/backlog.md`
  exists and is used to track Codex-specific skill compatibility issues found
  during dogfooding.
- `PROP-LRH-SKILLS-TARGET-AWARE-INSTALL` is adopted or otherwise updated to
  reflect the implemented state.

## Non-Goals

- Does not make `.claude/skills/` or `.agents/skills/` authoritative sources.
- Does not implement ChatGPT Skills export until the hosted API/upload contract
  is researched.
- Does not rewrite every LRH skill body as part of the first target-aware
  install work item.
- Does not build a marketplace, registry, plugin manager, or remote skill
  downloader.
- Does not change `lrh request` template rendering beyond any documentation
  needed to explain the shared source/target pattern.
- Does not require every LRH-managed repository to use LRH skills.

## Relationship to Design

- Governing proposal:
  `project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md`
- Codex compatibility backlog:
  `project/design/proposals/proposed/lrh-skills-target-aware-install/backlog.md`
- Prior skills installer design:
  `project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md`
- Current installer implementation:
  `src/lrh/skills/installer.py`
- User-facing installer docs:
  `docs/how-to/keep-skills-up-to-date.md`

## Open Questions

- Should Codex-specific `agents/openai.yaml` data be authored in canonical
  skill source directories, generated from canonical metadata, or both?
- Which proposal-local backlog entries should become formal work items during
  body-prose neutralization, and which are better handled by render adapters?
- How much of `project/agent_skills.yaml` should be accepted in the first repo
  config work item versus held for later extensibility?
- What public or private contract is sufficient to unblock ChatGPT Skills
  export design?
