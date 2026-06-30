---
id: WS-PRIOR-ART-CHECK
kind: planning_node
title: Prior Art / Build-vs-Buy Check for Design and Work-Item Skills
status: proposed
stage: designed
origin: design_review
summary: Add a mandatory, non-blocking prior-art/build-vs-buy check to /lrh-design, /lrh-proposal, /lrh-workstream, /lrh-work-item, and /lrh-implement so new designs and code record whether an existing in-repo, sibling-repo, or library implementation was found before proceeding.
related_focus: []
related_roadmap: []
related_design: []
work_items: []
exit_criteria:
  - A canonical prior-art-check procedure exists at src/lrh/skills/_shared/prior-art-check.md, excluded from lrh skills install by its leading-underscore directory name
  - Each of lrh-design, lrh-proposal, lrh-workstream, lrh-work-item, and lrh-implement has its own references/prior-art-check.md copy carrying a header comment naming the _shared master
  - lrh-design, lrh-proposal, and lrh-workstream each gain a required Prior Art Check step/section in their workflow and body guide
  - lrh-work-item's existing duplicate-item check is extended to cover code/library duplication, with the verdict recorded in the work item body
  - lrh-implement gains a Step 1.5 that validates or performs the prior-art check before implementation begins
  - project/design/backlog.md exists with the deferred validator drift-check entry
  - lrh validate reports 0 errors across all changed skill and reference files
---

## Purpose

This workstream adds a structured "has this already been built?" check to the
LRH design and planning skills. It was prompted by a real incident in a
sibling repo (LCATS), where a new Anthropic library wrapper duplicated an
existing OpenAI wrapper for the same purpose, discovered only after the fact.
The workstream coordinates the design, authoring, and rollout of a shared
prior-art-check procedure across the five skills that create durable design
or code commitments.

## Scope

- Author the canonical prior-art-check procedure at `src/lrh/skills/_shared/prior-art-check.md`
- Copy it into each consuming skill's own `references/` directory with a
  "synced copy, see master" header comment (manual sync, not automated)
- Wire the check into `/lrh-design` (Step 3a), `/lrh-proposal` and
  `/lrh-workstream` (body guide `## Prior Art Check` section), `/lrh-work-item`
  (extend existing duplicate-item research step), and `/lrh-implement`
  (new Step 1.5)
- Add `project/design/backlog.md` recording the deferred validator
  drift-check idea

## Work Items

To be created via `/lrh-work-item`:

- **Shared reference + backlog entry** — create `_shared/prior-art-check.md`
  and `project/design/backlog.md`.
- **Wire into design-time skills** — update `lrh-design`, `lrh-proposal`,
  `lrh-workstream` to load and apply the check, with per-skill synced copies.
- **Wire into work-item and implementation skills** — update `lrh-work-item`
  and `lrh-implement` similarly.

## Exit Criteria

(see frontmatter `exit_criteria`)

## Non-Goals

- Does not add automated drift-checking between the `_shared/` master and its
  per-skill copies (e.g. via `lrh validate`) — sync is comment-only/manual
  for this workstream. Deferred; see
  `project/design/backlog.md#validator-drift-check-for-synced-skill-references`.
- Does not make the prior-art check a hard `lrh validate` gate — it is a
  judgment step the agent performs and records, warn-don't-block, matching
  the existing `lrh work-items readiness` precedent.
- Does not establish a hardcoded list of sibling repos to check (e.g. LCATS)
  — the interview question is asked explicitly each time rather than relying
  on a maintained list. (Open question below.)

## Background / Rationale

Design discussion for this workstream walked through and rejected: a root-level
`PRIOR_ART.md` (root is already crowded), `project/conventions/` (category
error — `project/` is control-plane artifacts, not skill instruction
content), `docs/` Diataxis placement (wrong audience — agent-executed
procedure, not human-readable documentation), and a plain `common/` directory
(would be picked up by `lrh skills install` as an installable skill, unlike
an underscore-prefixed directory, which `src/lrh/skills/installer.py:41`
already excludes).

## Open Questions

- Should sibling-repo names (e.g. LCATS) be tracked in a small
  `project/related-repos.md` so the interview question doesn't rely on the
  user remembering to name them each time? Deferred to work-item scoping.
