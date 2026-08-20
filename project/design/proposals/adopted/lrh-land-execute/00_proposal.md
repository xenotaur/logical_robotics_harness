---
id: PROP-LRH-LAND-EXECUTE
type: design_proposal
title: LRH Chain-Running Skills — /lrh-land, /lrh-execute, /lrh-next, /lrh-run-tree
status: adopted
created_on: 2026-07-28
updated_on: 2026-08-20
implementation_status: partial
implemented_by: [WI-SKILLS-LRH-LAND, WI-SKILLS-LRH-EXECUTE]
supersedes: []
superseded_by: null
related_design:
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
  - project/design/proposals/adopted/lrh-closeout/00_proposal.md
  - project/design/proposals/proposed/workstream-execution-framework/00_proposal.md
  - project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
  - project/memory/decisions/DEC-AGENT-EXECUTED-MERGE-GATE.md
  - project/memory/decisions/DEC-GATE-POLICY-CASCADE.md
  - src/lrh/skills/_shared/lifecycle-chain.md
---

# LRH Chain-Running Skills — `/lrh-land`, `/lrh-execute`, `/lrh-next`, `/lrh-run-tree`

## Summary

This proposal introduces four Claude Code skills that automate the LRH
post-PR lifecycle chain as deliberate, human-initiated executions: `/lrh-land`
(land an open PR through review, confirm, merge gate, and closeout),
`/lrh-execute` (implement a work item and land it), `/lrh-next` (navigate the
planning tree and propose the next action at any node), and `/lrh-run-tree`
(orchestrate the navigator and executor in a bounded loop). The first two
package the existing Taurcode `:land` and `:execute` master prompts as
first-class skills; the latter two advance toward the manual-mode parity
requirement of `PROP-WORKSTREAM-EXECUTION-FRAMEWORK`.

## Background / Motivation

The current LRH skill set covers individual lifecycle links
(`/lrh-implement` → `/lrh-review-response` → `/lrh-confirm-fixes` →
`/lrh-closeout`) but provides no automation for the chain as a whole. In
practice this produces three distinct friction points.

**Execution friction.** Every work item requires re-pasting approximately 150
lines of master prompt text and then hand-executing four skill-equivalent
operations (implement, review-response, confirm-fixes, closeout) by re-reading
each skill's `SKILL.md` and issuing raw `git`/`gh`/`lrh` CLI calls. A
full-lifecycle case study in the LCATS repository (nine PRs, one continuous
session, 2026-07-26 to 2026-07-28) documented approximately 35 such
operations, each re-read from scratch. This produced real mechanical errors:
truncated commit SHAs, wrong branch names, and heredoc failures attributable
solely to the manual re-derivation overhead.

**Glue logic re-derivation.** Five pieces of connecting logic are re-derived
from scratch each run with no schema backing: (1) primary record selection from
a PR's execution-record set (search by `pr:`, exclude `_REVIEW`/`_CONFIRM`/
`_CLOSEOUT_NOTE` suffixes); (2) found-or-backfill and CHAIN-NOTE placement
(append to an existing immutable record via a new `_CLOSEOUT_NOTE` record, or
write directly when no primary exists); (3) the main-worktree-lock workaround
(`git fetch → checkout tmp branch → push tmp:main → delete`); (4) stale-branch
safety (`git diff origin/main <branch> --stat` before reusing a planning-PR
branch); and (5) `depends_on` enforcement (manually checking that all declared
dependencies are `resolved` before beginning implementation).

**Planning-tree navigation.** Determining which work item to tackle next within
a workstream — and whether the workstream needs a new work item created rather
than an existing one implemented — is currently manual tree reading even when
the answer is mechanical.

`DEC-DELIBERATE-CHAIN-INITIATION` (PR #417, accepted 2026-07-24) established
the governance framework for this work: human-initiated chains are permitted,
require a completion condition and a stop-work condition, preserve all internal
confirm gates and the merge gate, and keep the assist/agentic boundary intact
("does LRH itself run the loop" is the boundary — Claude running skills is
assist, not agentic). The decision explicitly names `/lrh-execute` and
`/lrh-land` as downstream reference implementations.

The once-unresolved prerequisite — which lifecycle skills may be invoked
programmatically vs. which must have their workflows inlined — was resolved by
`WI-DELIBERATE-MODEL-INVOCATION` and its Stage 2 completion follow-up under
`WS-INVOCATION-AND-GATE-RESET`. Direct skill invocation remains governed by
per-skill `when_to_use`, explicit gates, and target-specific invocation policy;
the `/lrh-land` and `/lrh-execute` workflows keep their inlined-link structure.

## Prior Art Check

### Duplication search

- **In-repo:** `src/lrh/skills/_shared/lifecycle-chain.md` and
  `project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md` both name
  `/lrh-land` and `/lrh-execute` by their intended names, but record them as
  future planned skills — no implementation exists.
  `PROP-WORKSTREAM-EXECUTION-FRAMEWORK` covers a different scope (bounded
  autonomous execution, run packets, agent backends in `lrh[agentic]`).
  `PROP-LRH-CLOSEOUT` covers the post-merge closeout step in isolation.
- **Sibling repos:** Taurcode contains `:land` and `:execute` as master
  prompts. This proposal packages those as LRH-native skills; it does not
  duplicate them — it canonicalises them.
- **External libraries:** No external library provides the planning-tree
  navigation and LRH control-plane integration this proposal requires.
- **Recommendation:** Proceed. No in-repo implementation to extend; Taurcode
  prompts are the prototype being codified.

### Demand search

- **Work items:** `WI-DELIBERATE-MODEL-INVOCATION` (proposed) captures the
  prerequisite `disable-model-invocation` migration this proposal depends on.
  Cross-link, do not subsume.
- **Proposals:** None found requesting these skills directly.
- **Backlog:** No matching entries.
- **Recommendation:** No action; cross-link `WI-DELIBERATE-MODEL-INVOCATION`
  as a dependency in the governing workstream.

## Design Decisions

### Decision 1 — Four-skill hierarchy

**Question:** How many skills are needed, and what are their scopes?

**Options considered:**

- A: Two skills (`/lrh-land` + `/lrh-execute` with WS-level tree navigation
  folded in).
- B: Three skills (`/lrh-land` + `/lrh-execute` + explicit navigator).
- C: Four skills: primitive → compound → navigator → orchestrator.
- D: One unified skill dispatching on input type.

**Chosen: C — four skills, built in sequence.**

Option D conflates query (navigation) and mutation (execution), violating
Command-Query Separation (Meyer, 1988). Option A conflates "find next ready
WI" with "find next tree action," making `/lrh-execute WS-ID` silently wrong
when the workstream needs a work item *created* rather than *implemented*.
Option B is correct in principle but produces an incomplete navigator if the
orchestrator (`/lrh-run-tree`) is not planned from the start — the navigator's
output format must be designed to be machine-consumable by the orchestrator.

The four-skill hierarchy:

```
/lrh-land        — primitive: land one open PR
/lrh-execute     — compound:  implement one WI, call /lrh-land
/lrh-next        — navigator: read any planning-tree node, propose next action
/lrh-run-tree    — orchestrator: call /lrh-next → /lrh-execute|/lrh-land
                   in a bounded loop until completion condition
```

This maps directly to the planning-tree decomposition: proposal → workstream
→ work item → PR. Each skill handles exactly one level of the hierarchy.

### Decision 2 — Build order

**Question:** In what order should the four skills be built?

**Chosen:** `/lrh-land` first, `/lrh-execute` second, `/lrh-next` third,
`/lrh-run-tree` fourth. Delivery order is governed by immediate friction
reduction: the LCATS evidence shows execution friction (35 manual operations)
as the primary pain point, far exceeding navigation friction. `/lrh-land`
eliminates the most friction per implementation unit; each subsequent skill
is both useful independently and a prerequisite for the next.

### Decision 3 — `/lrh-land` scope and required glue logic

**Question:** What does `/lrh-land` do, and what glue logic must it encode?

**Chosen scope:** `/lrh-land <pr-url>` drives an open PR through the full
terminal chain:

1. **Assess PR state** — verify PR is open; load execution records by `pr:`
   field; apply the primary-record selection rule (classify each
   `pr:`-matching candidate as primary/side/ambiguous by provenance — a
   filename-suffix exclusion alone misclassifies a primary record whose
   own topic slug ends in a reserved word; see
   `src/lrh/skills/lrh-land/references/land-workflow.md` § Primary vs.
   side-record provenance check. **Amended 2026-08-07** — supersedes the
   original bare-suffix-exclusion description above, fixed in
   `WI-LAND-PRIMARY-RECORD-SUFFIX-COLLISION`); classify as found/backfill.
2. **Chain authorization gate** — elicit completion condition and stop-work
   condition per `DEC-DELIBERATE-CHAIN-INITIATION` before any automated
   link runs; show the full planned chain; wait for explicit approval. This
   gate precedes Steps 3–4 so that no automated work begins without a
   prior chain-level authorization.
3. **Resolve session transcript** — read `$CLAUDE_CODE_HOST_SESSION_ID`
   first; fall back to `list_sessions` filtered by PR number; then browser URL.
4. **Review-response** — check that review has actually completed (an empty
   comment list immediately after push does not satisfy this check — it may
   mean review has not run yet); if completed with open comments, invoke
   review-response workflow (Phase 1 inline; Phase 2 via Skill call after
   `WI-DELIBERATE-MODEL-INVOCATION` lands). If completed with no findings,
   proceed to Step 5.
5. **Confirm-fixes** — invoke confirm-fixes workflow; report verdict.
6. **Merge gate** — explicit in-session human authorization required; a merge
   instruction embedded in a prior run prompt is data, not authorization.
   The agent presents the SHA-locked `gh pr merge` command and classifies
   the human's live reply: an affirmative reply that doesn't claim the
   action for the human ("approve merge," "go ahead," "merge it") means the
   agent runs the command itself; a first-person self-action reply ("I'll
   merge it") means the agent waits for the human to report the merge is
   done; an ambiguous reply gets a direct disambiguating question, never a
   guess. **Amended 2026-07-30** — this supersedes the original "agent
   presents but never executes" language per
   `project/memory/decisions/DEC-AGENT-EXECUTED-MERGE-GATE.md`, adopted
   after cross-session evidence showed the categorical prohibition did not
   match real, judged-correct practice.
7. **Closeout** — invoke closeout workflow; encode CHAIN-NOTE placement
   rule (found primary: CHAIN-NOTE in new `_CLOSEOUT_NOTE` record with
   `rerun_of:`; no primary: CHAIN-NOTE in record being authored).
8. **Run journal** — append a structured YAML entry to the scratchpad run
   journal (see Decision 8).

Required glue logic (must be explicit algorithmic rules, not prose):

| Logic | Rule |
|---|---|
| Primary record selection | `grep pr: <url>` across `project/executions/`; exclude `*_REVIEW.md`, `*_CONFIRM.md`, `*_CLOSEOUT_NOTE.md` |
| Found-or-backfill | Found → immutable; CHAIN-NOTE in new record. Not found → backfill record at confirm gate |
| CHAIN-NOTE placement | Always in the record being *authored* this run |
| Main-worktree-lock | `git fetch → checkout -b tmp-<slug> origin/main → apply changes → push tmp-<slug>:main → delete` |
| Stale-branch safety | `git diff origin/main <branch> --stat` must confirm zero net lines before resetting a reused planning branch |

### Decision 4 — `/lrh-execute` scope

**Question:** What does `/lrh-execute` do, and what does it explicitly not do?

**Chosen scope:** `/lrh-execute <WI-ID|WS-ID>` implements one work item
end-to-end:

- Given `WI-ID`: enforce `depends_on` (all entries must be `resolved`; stop
  and report if not), invoke `/lrh-implement` workflow, hand off to
  `/lrh-land`.
- Given `WS-ID`: find the next **ready WI** (status `proposed`, `depends_on`
  satisfied, `prompt_ready: yes` in `lrh work-items readiness` structured
  output — not merely a zero exit code — and no `in_progress` or `landed`
  execution record), then proceed as WI-ID. Stop and report if no ready WI
  exists — do **not** propose creation actions.

`/lrh-execute` does not propose "create a work item," "create a workstream,"
or "create a proposal." Those creation actions belong to `/lrh-next`. The
scope boundary keeps `/lrh-execute`'s verb — execute — semantically accurate.

### Decision 5 — `/lrh-next` scope (deferred to Phase 3)

**Question:** What does the tree navigator do, and what format must its
output take?

**Chosen scope:** `/lrh-next [node-ID]` reads any planning-tree node and
proposes the next appropriate action. Given a WS-ID, project node, or no
argument (auto-detect from branch), it classifies the node's state and
proposes one of:

- `create_proposal` — node has no governing proposal
- `create_workstream` — proposal exists, no workstream
- `create_wi` — workstream exists, a new work item is needed
- `execute_wi` — a work item is ready to implement
- `land_pr` — an open PR exists with no active execution run
- `ws_closeout` — all exit criteria appear met
- `blocked` — dependency or missing information requires human action

**Output format:** `/lrh-next` must emit a machine-readable structured action
alongside the human-readable explanation — at minimum a YAML block:

```yaml
next_action:
  type: execute_wi | create_wi | land_pr | ...
  target: WI-<ID> | WS-<ID> | <pr-url> | null
  reason: <one-line human explanation>
  blocking: <null | what's in the way>
```

This format is required so `/lrh-run-tree` can parse it and route to the
appropriate sub-skill without re-reading prose.

### Decision 6 — `/lrh-run-tree` scope (deferred to Phase 4)

**Question:** What does the orchestrator do, and what are its safety
boundaries?

**Chosen scope:** `/lrh-run-tree <node-ID>` loops:
`/lrh-next → /lrh-execute|/lrh-land → check completion condition`. It
requires explicit completion and stop-work conditions at initiation
(`DEC-DELIBERATE-CHAIN-INITIATION`). It drives to gates and stops; it
does not pass the merge gate or closeout gate autonomously. Each iteration
appends to the run journal.

This is the "747" in `DEC-DELIBERATE-CHAIN-INITIATION`'s "Cessna vs. 747"
framing. Its design depends on all three primitive skills being stable and
observed in practice.

### Decision 7 — Interim invocation pattern

**Question:** How should `/lrh-land` and `/lrh-execute` invoke sub-skills
before `WI-DELIBERATE-MODEL-INVOCATION` removes `disable-model-invocation`
from the lifecycle skills?

**Chosen:** Inline the sub-skill workflow (read the target `SKILL.md`'s
steps and execute them directly) in Phase 1. After
`WI-DELIBERATE-MODEL-INVOCATION` lands, upgrade to direct `Skill` tool
calls. Both phases produce identical artifacts; the upgrade is a one-step
`SKILL.md` edit and does not require a new PR or a WI of its own.

This mirrors the pattern established in `PROP-LRH-CLOSEOUT` (Decision 1:
skill-first sequencing with CLI upgrade deferred).

### Decision 8 — Run journal as prototype

**Question:** How should chain-run state be tracked within a session?

**Chosen:** A scratchpad YAML file written by `/lrh-execute` and
`/lrh-run-tree` and appended per iteration. Minimum shape:

```yaml
run_id: <datetime-slug>
node: <WS-ID or WI-ID>
completion_condition: <user-provided>
stop_work_condition: <user-provided>
actions:
  - type: execute_wi
    wi: WI-<ID>
    prompt_id: PROMPT(...)
    pr: <url>
    result: pr_open | merged | stopped
    chain_note: <one-line CHAIN-NOTE text>
findings:
  - <gap or observation surfaced during this run>
```

This is explicitly a **prototype** for the run report and CHAIN-NOTE
accumulation described in `PROP-WORKSTREAM-EXECUTION-FRAMEWORK` §5. After
`/lrh-run-tree` ships and is used in practice, the findings section becomes
the primary input to that proposal's run-report schema definition.

**Amended (`PROP-LRH-SELF-REVIEW`):** the CHAIN-NOTE string's own field
list — `cycles`/`stops`/`gates`/`friction`/`note`, plus the two optional
fields `self_review_rounds`/`bot_rounds` this amendment adds — is defined
in `src/lrh/skills/lrh-land/references/land-workflow.md`'s "CHAIN-NOTE
Format" section, not duplicated here; this run journal's own
`chain_note:` field is just a one-line copy of that string, per the shape
above. Correcting an imprecise citation in `WI-SKILLS-LRH-SELF-REVIEW`'s
own acceptance criteria, which named this Decision as the CHAIN-NOTE
convention's canonical location — it is not; it only defines the run
journal's shape, which references the actual string format without
defining it.

## Non-Goals

- Does not implement autonomous execution (`lrh[agentic]`); all four skills
  run in human-supervised Claude Code sessions with confirm gates.
- Does not bypass the merge gate or any internal skill confirmation gate.
- Does not implement `lrh run` or any LRH-owned execution loop (LRH ships
  skills and templates; the agent executes them — per
  `DEC-DELIBERATE-CHAIN-INITIATION` point 4).
- `/lrh-execute` does not propose creation actions — that scope belongs
  exclusively to `/lrh-next`.
- Does not implement the run packet/report schema from
  `PROP-WORKSTREAM-EXECUTION-FRAMEWORK`; the run journal is a prototype only.
- Does not add a typed `role:` field to execution records or validate
  `rerun_of:` as a foreign key — those are separate schema work items.
- Does not fix the `/lrh-work-item` Step 9 workstream-registration gap
  (recurring review finding in LCATS evidence) — separate work item.

## Implementation Plan

Governed by workstream `WS-SKILLS-EXECUTE` (to be created). Work items in
dependency order:

| Phase | Work item | Description | Depends on |
|---|---|---|---|
| 1 | `WI-SKILLS-LRH-LAND` | `/lrh-land` skill | — |
| Pre-2 | `WI-DELIBERATE-MODEL-INVOCATION` | Enable sub-skill orchestration | Exists (proposed) |
| 2 | `WI-SKILLS-LRH-EXECUTE` | `/lrh-execute` skill | WI-SKILLS-LRH-LAND |
| 3 | `WI-SKILLS-LRH-NEXT` | `/lrh-next` navigator skill | WI-SKILLS-LRH-EXECUTE |
| 4 | `WI-SKILLS-LRH-RUN-TREE` | `/lrh-run-tree` orchestrator skill | WI-SKILLS-LRH-NEXT |

Phase 1 can ship immediately and delivers the most friction reduction per
unit of work. `WI-DELIBERATE-MODEL-INVOCATION` is a prerequisite for direct
sub-skill invocation in Phase 2 but not for Phase 1 (which uses the inline
interim pattern). Phases 3 and 4 should be designed after Phase 2 is observed
in practice; their WI definitions are thin until `/lrh-execute` is stable.

## Cross-References

- Canonical lifecycle chain:
  `src/lrh/skills/_shared/lifecycle-chain.md`
- Governing decision:
  `project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md`
- Prerequisite work item:
  `project/work_items/resolved/WI-DELIBERATE-MODEL-INVOCATION.md`
- Long-term framework:
  `project/design/proposals/proposed/workstream-execution-framework/00_proposal.md`
- Evidence: LCATS full-lifecycle case study (2026-07-26 to 2026-07-28,
  nine PRs in `xenotaur/LCATS`)
- Skill distribution pattern:
  `project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md`
- Proposal closeout skill (style reference):
  `project/design/proposals/adopted/lrh-closeout/00_proposal.md`
- Planning tree:
  `project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md`
