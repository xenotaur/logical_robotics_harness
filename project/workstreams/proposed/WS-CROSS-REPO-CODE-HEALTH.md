---
id: WS-CROSS-REPO-CODE-HEALTH
kind: planning_node
title: Cross-Repository Code Health
status: proposed
stage: conceived
origin: follow_up
summary: >
  Keep the LRH harness and its installed instances correct and consistent across
  the repositories that use it: control-plane schema gaps, skill-authoring
  defects that propagate to every install, evidence-discipline tooling, and the
  per-repository remediation those changes require.
related_design:
  - project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md
  - project/design/proposals/proposed/contributor-identity-contract/00_proposal.md
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-INVOCATION-AND-GATE-RESET
work_items:
  - WI-LRH-SEARCH-COUNT-PROVENANCE
  - WI-SKILLS-WORKTREE-SAFE-BRANCH-CREATION
  - WI-WORK-ITEM-BLOCKED-STATE-EXPRESSIVENESS
  - WI-SIBLING-REPO-VALIDATE-CI-AND-CONTRIBUTOR-IDS
  - WI-TAURCODE-PROMPT-AND-SKILL-SYNC
exit_criteria:
  - A repo-wide count or survey that feeds a decision can be produced with its own scope and exclusions stated, over a corpus that may be outside the current repository, and the AGENTS.md convention cross-references it
  - The eight skills that hard-code a default branch resolve it at runtime, guard a dirty working tree, and branch from a remote ref, with the guidance in one canonical place
  - A proposed work item can express that it must not be started, and readiness reports it as not ready, closing the gap where a chain runner selects work its own risk notes forbid
  - Every repository with an LRH control plane runs lrh validate in CI, and its contributor registry carries a decided id and a populated correlation key for human contributors
  - Taurcode's land and execute prompts and its vendored skills agree with the post-reset review and gate model, or document a deliberate divergence
  - Each item that changes installed skill behaviour is verified against the installed corpus, not only the source tree
---

## Purpose

This workstream owns the work that keeps LRH — and the repositories that install
it — internally consistent, as distinct from the work that adds capability.
Every item here originates the same way: something was found broken or
under-specified while doing other work, and it affects more than the repository
it was found in.

It exists now because five such items accumulated in a single session with no
workstream willing to own any of them, and because looking at them together
surfaced dependencies that were invisible item by item — including a direct file
collision with `WS-INVOCATION-AND-GATE-RESET` that neither workstream would have
caught alone.

## Scope

Five work items, in the order their dependencies suggest:

1. **`WI-LRH-SEARCH-COUNT-PROVENANCE`** — a scope-aware, provenance-emitting
   counter under `lrh search`, plus the `AGENTS.md` evidence convention it
   accelerates.
2. **`WI-SKILLS-WORKTREE-SAFE-BRANCH-CREATION`** — worktree-safe,
   default-branch-agnostic branch creation across eight skills, plus five
   non-compliant commit-message templates.
3. **`WI-WORK-ITEM-BLOCKED-STATE-EXPRESSIVENESS`** — let a proposed work item
   express that it must not be started, and by a non-work-item artifact.
4. **`WI-SIBLING-REPO-VALIDATE-CI-AND-CONTRIBUTOR-IDS`** — `lrh validate` in
   `velumin` and `replication_vector` CI, then their contributor ids.
5. **`WI-TAURCODE-PROMPT-AND-SKILL-SYNC`** — Taurcode's `:land`/`:execute`
   prompts and vendored skills, after the reset's Stages 1 and 2 land.

**Deliberately not swept in.** Ten other work items currently carry
`related_workstreams: []`, most predating this session — test-layout migration
(3), documentation (2), CLI wiring tests, work-audit and work-remains features,
template audit, and a doc-related-design repoint. They are unowned for their own
reasons and belong to feature or documentation concerns rather than harness
consistency. An earlier framing treated "four items with no workstream" as a
signal those four revealed a gap; the gap is older and wider than that, and this
workstream deliberately does not try to absorb it. Adopting an item here should
be a judgement about fit, not a way to clear a list.

## Prior Art Check

### Duplication search

- **In-repo:** No existing workstream covers harness consistency, cross-repository
  operations, or evidence discipline. `WS-INVOCATION-AND-GATE-RESET` is adjacent
  and shares files (see Collisions) but is scoped to one incident-driven program
  with a defined end state. `WS-LRH-CHAIN-DEFAULTS` owns a specific mechanism.
  `WS-SKILLS` is `resolved`.
- **Sibling repos:** None identified; by construction this workstream is the
  place cross-repository items land, and no sibling maintains an equivalent.
- **External libraries:** Not applicable.
- **Recommendation:** Proceed.

### Demand search

- **Work items:** the five above, each already written and validating clean.
- **Proposals:** `PROP-INVOCATION-AND-GATE-RESET` and
  `PROP-CONTRIBUTOR-IDENTITY-CONTRACT` supply items 4 and 5's governing design.
- **Backlog:** `project/design/backlog.md`'s "Validator drift-check for synced
  skill references" is adjacent to item 2 and should be linked when that item is
  implemented, not before.
- **Recommendation:** No action beyond adopting the five.

## Synergies

Looking at these together changes how three of them should be built.

**S1 — item 1 is the verification tool items 4 and 5 need, and should go
first.** `WI-LRH-SEARCH-COUNT-PROVENANCE`'s open design question is what corpus
a claim is about; its candidate corpora already include the installed skill
tree (`~/.claude/skills/` and per-repo `.claude/skills/`). Items 4 and 5 both
end with "verify against the installed corpus, not the source tree" — the exact
check that tool would provide. Built first, it makes those verifications
mechanical rather than manual; built last, both items hand-roll it.

**S2 — items 4 and 5 share a procedure and a third repository.**
Both refresh vendored skills in another repository and verify the result.
Additionally, Taurcode has **no `scripts/validate` at all** and none of its seven
workflows runs `lrh validate` — the same CI gap item 4 fixes for `velumin` and
`replication_vector`. So the CI half generalizes from two repositories to three,
and should be written once rather than twice. Whether to widen item 4's scope or
have item 5 reuse its pattern is an implementation choice; doing neither means
writing it twice.

**S3 — item 2's output needs the same propagation step as the reset.** Fixing
branch creation in eight skills changes nothing until `lrh skills install` runs
and the installed copies are verified — the propagation requirement
`PROP-INVOCATION-AND-GATE-RESET` Stages 1 and 2 now carry. Item 2 should adopt
the same step rather than inventing one.

## Collisions

**C1 — direct file collision with `WS-INVOCATION-AND-GATE-RESET`.** Item 2
declares `src/lrh/skills/lrh-land/SKILL.md` and
`src/lrh/skills/lrh-land/references/land-workflow.md` in `artifacts_expected`.
The reset's Stages 1 and 2 modify **both of those same files**, verified against
the exploration branch. Neither workstream's artifacts mention the other's claim
on them.

*Resolution:* item 2 must not land between the reset's Stage 1 and Stage 2, and
should land after Stage 2 unless someone has confirmed the diffs are disjoint.
This is the clearest argument for this workstream existing: the collision is
invisible from inside either work item.

**That ordering is currently unenforced, and this workstream's `work_items:`
exposes it.** `WI-SKILLS-WORKTREE-SAFE-BRANCH-CREATION` has `depends_on: []`
and reports `prompt_ready: yes`, so `/lrh-execute WS-CROSS-REPO-CODE-HEALTH`
would select it once item 1 resolves — regardless of whether reset Stage 2 has
landed. The prose above is not part of readiness evaluation.

The blocker is a workstream stage, not a work item, so `depends_on:` cannot
name it — the same expressiveness gap item 3 exists to close. Until then this
ordering depends on a human reading this section before dispatching, which is
recorded here as a known weakness rather than presented as a control. Anyone
running `/lrh-execute` against this workstream should confirm reset Stage 2 has
landed first.

**C2 — item 2 cites a snippet the reset deletes.** Its Required Change 2 reuses
`round-cap-gate.md`'s hardened default-branch resolution, which Stage 1 removes
when it reduces that file from 749 to ~59 lines. The work item already carries a
recovery note; recorded here because it is a sequencing fact between two
workstreams, not an internal detail of one.

**C3 — item 3 changes readiness semantics that `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3`
currently works around.** That work item (owned by `WS-LRH-CHAIN-DEFAULTS`)
carries a prose "DO NOT START" banner precisely because a proposed item cannot
be marked blocked. When item 3 lands, that banner should be replaced by real
frontmatter and deleted. Nothing currently schedules that follow-through, and
`WS-LRH-CHAIN-DEFAULTS` has no reason to notice item 3 landing.

## Work Items

| # | Work item | Type | Notes |
|---|---|---|---|
| 1 | `WI-LRH-SEARCH-COUNT-PROVENANCE` | deliverable | Build first — S1 |
| 2 | `WI-SKILLS-WORKTREE-SAFE-BRANCH-CREATION` | deliverable | After reset Stage 2 — C1, C2 |
| 3 | `WI-WORK-ITEM-BLOCKED-STATE-EXPRESSIVENESS` | deliverable | Triggers a follow-through in `WS-LRH-CHAIN-DEFAULTS` — C3 |
| 4 | `WI-SIBLING-REPO-VALIDATE-CI-AND-CONTRIBUTOR-IDS` | operation | Consider widening to Taurcode — S2 |
| 5 | `WI-TAURCODE-PROMPT-AND-SKILL-SYNC` | operation | After reset Stages 1–2 |

Items 1 and 3 are independent of everything else and can start immediately.
Items 2, 4, and 5 all wait on the reset or on item 1.

## Exit Criteria

- A repo-wide count or survey feeding a decision can be produced with its own
  scope and exclusions stated, over a corpus that may lie outside the current
  repository, and `AGENTS.md`'s convention cross-references it.
- The eight skills that hard-code a default branch resolve it at runtime, guard
  a dirty working tree, and branch from a remote ref, with the guidance in one
  canonical place.
- A proposed work item can express that it must not be started, and readiness
  reports it as not ready.
- Every repository with an LRH control plane runs `lrh validate` in CI, and its
  contributor registry carries a decided id plus a populated correlation key for
  human contributors.
- Taurcode's `:land`/`:execute` prompts and vendored skills agree with the
  post-reset review and gate model, or document a deliberate divergence.
- Each item that changes installed skill behaviour is verified against the
  installed corpus, not only the source tree.

## Non-Goals

- **Does not absorb every unowned work item.** See Scope; ten others are
  deliberately left alone.
- **Does not own the invocation-and-gate reset.** That is
  `WS-INVOCATION-AND-GATE-RESET`. This workstream records the collisions between
  them but does not sequence the reset's own stages.
- **Does not own the chain-defaults mechanism.** That is
  `WS-LRH-CHAIN-DEFAULTS`; C3 is a hand-off note, not a claim.
- Does not execute changes in repositories LRH does not govern. Items 4 and 5
  specify per-repository work carried out by hand.
- Does not become a catch-all for maintenance. An item belongs here if it is
  harness consistency that crosses repository or install boundaries; a bug in a
  single feature does not.
