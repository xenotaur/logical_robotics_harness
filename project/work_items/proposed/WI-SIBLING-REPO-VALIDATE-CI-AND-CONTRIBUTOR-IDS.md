---
resolution: null
blocked_reason: null
blocked: false
id: WI-SIBLING-REPO-VALIDATE-CI-AND-CONTRIBUTOR-IDS
title: Add lrh validate to velumin and replication_vector CI, then remediate their contributor ids
type: operation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/proposed/contributor-identity-contract/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - rename_ids_before_ci_lands
acceptance:
  - velumin and replication_vector each run lrh validate as part of scripts/validate, following the availability-guard pattern LRH's own scripts/validate uses
  - Both repositories are confirmed green on lrh validate in CI before any contributor id is renamed
  - Each registry populates github for its human contributor, so the cross-repo correlation key exists
  - The spaced id "project maintainers" is replaced with a slug-shaped id in both repositories, and every owner and contributors reference is updated in the same change
  - lrh validate reports 0 errors in both repositories after the rename
  - A quiet window is confirmed by the documented precondition check before the rename lands, not assumed
---

# Add `lrh validate` to velumin and replication_vector CI, then remediate their contributor ids

## Summary

Two sibling repositories carry LRH control planes that no CI checks, and both
use a placeholder contributor id containing a space with no GitHub correlation
key. Add `lrh validate` to their existing validation scripts first, confirm
green, then remediate the ids — in that order, so the safety net exists before
the change that relies on it.

## Problem / Context

`PROP-CONTRIBUTOR-IDENTITY-CONTRACT`'s fleet survey found `velumin` and
`replication_vector` sharing two defects. Both were re-measured with `git grep`
per `AGENTS.md`'s evidence convention:

| Repository | `owner:` refs | list refs | Total | Registry |
|---|---|---|---|---|
| `velumin` | 35 | 4 | **39** | `id: project maintainers`, `github:` empty |
| `replication_vector` | 18 | 0 | **18** | `id: project maintainers`, `github:` empty |

Two distinct problems:

1. **The id is not slug-shaped.** `project maintainers` contains a space. An id
   is referenced from `owner:` and `contributors:` in YAML frontmatter, where an
   unquoted value containing a space is fragile, and it is a poor key for any
   future join.
2. **No correlation key.** `github:` is empty in both, so neither repository can
   be correlated to the same person in LRH, `taurcode`, or `taurworks` — the
   defect `PROP-CONTRIBUTOR-IDENTITY-CONTRACT` Decision 1 exists to fix.

### The CI gap, and why it must be fixed first

**The gap is narrower than "no CI" — both repositories already have
`.github/workflows/validate.yml` running `scripts/validate`. What that script
does not run is `lrh validate`.** Verified: both scripts execute
`version → format → lint → test → baseline`, with no control-plane step. So
their `project/` trees are entirely unchecked, and both currently report
`0 errors, 0 warnings` only because someone runs the command by hand.

This matters for sequencing. An id rename is normally safe *because* it is
atomic and self-checking: `owner:` is cross-validated against contributor ids
(`src/lrh/control/validator.py:1371-1403`), so an incomplete rename fails
loudly. **In these two repositories that net does not exist in CI**, so the
rename would be verified only by remembering to run the command locally, in
repositories that are otherwise rarely touched. Adding the step first converts
the rename from hopeful to checkable.

LRH's own `scripts/validate` is the reference pattern: it guards on the CLI
being available (`command -v lrh`) before running `lrh validate`, so the step
fails with a clear message rather than a confusing one when the environment is
incomplete.

### Prior Art Check

**Duplication search**

- In-repo: No work item covers sibling-repo CI or contributor remediation.
  `PROP-CONTRIBUTOR-IDENTITY-CONTRACT` specifies the remediation as its step 4
  but does not scope the CI prerequisite; this work item is that step plus the
  prerequisite the review surfaced.
- Sibling repos: Neither target repository has an existing work item for this;
  both control planes are small and unattended.
- External libraries: Not applicable.
- Recommendation: Proceed.

**Demand search**

- Work items: None.
- Proposals: `PROP-CONTRIBUTOR-IDENTITY-CONTRACT` Decision 4 and 5 are the
  governing design. This work item implements its step 4 for these two
  repositories only.
- Backlog: No matching entries.
- Recommendation: Link to the proposal; nothing to close.

## Scope

`velumin` and `replication_vector` only: their `scripts/validate`, their
`project/contributors/` registries, and their `owner:`/`contributors:`
references.

Out of scope: `LCATS`, `prosocial`, `taurcode`, and `taurworks-safety`, which
have different defects and are covered separately by
`PROP-CONTRIBUTOR-IDENTITY-CONTRACT` Decision 4. Also out of scope: adding
`lrh validate` to repositories that already run it.

## Required Changes

1. Add an `lrh validate` step to `scripts/validate` in both repositories,
   following LRH's own availability-guard pattern.
2. Land that change and **confirm both repositories are green in CI** before
   touching any id. If either is already failing, fix that first — a
   pre-existing failure would mask a rename error.
3. Populate `github:` for the human contributor in each registry.
4. Rename the id from `project maintainers` to a slug-shaped value, updating the
   registry and every `owner:`/`contributors:` reference in the same commit, so
   validation either passes or fails as a unit. Use anchored patterns
   (`^owner: `, `^  - `) so nothing else is touched.
5. Confirm `lrh validate` reports 0 errors in both repositories afterward.

**Value for the new id is deliberately not fixed here.**
`PROP-CONTRIBUTOR-IDENTITY-CONTRACT` Open Question 2 offers `xenotaur`, a
slugged `project-maintainers`, or replacing the placeholder with a real
registry. Any is compatible with this work item; the choice should be made when
the contract is adopted, not pre-empted by an operations task.

## Non-Goals

- Does not rename ids before the CI step lands and is confirmed green. That
  ordering is the point of this work item, not an incidental preference.
- Does not decide the replacement id value — see above.
- Does not add `lrh validate` to any other repository.
- Does not change `scripts/validate`'s other steps, or restructure CI.
- Does not touch the other repositories named in
  `PROP-CONTRIBUTOR-IDENTITY-CONTRACT` Decision 4.

## Acceptance Criteria

- Both repositories run `lrh validate` from `scripts/validate`, with an
  availability guard.
- Both are confirmed green in CI **before** any id is renamed.
- Each registry populates `github:` for its human contributor.
- The spaced id is replaced with a slug-shaped id, with all 57 references
  (39 velumin, 18 replication_vector) updated in the same change.
- `lrh validate` reports 0 errors in both repositories afterward.
- The quiet-window precondition below is checked and recorded, not assumed.

## Validation

- `lrh validate` in each repository reports 0 errors
- `git grep -n "project maintainers"` returns no matches in either repository
- `git grep -c "^owner: <new-id>" -- '*.md'` matches the pre-change reference count in each repository
- CI green on both repositories after the `scripts/validate` change and again after the rename
- Quiet-window precondition re-checked immediately before the rename lands

## Risk Notes

**Sequencing is the whole risk.** Renaming before the CI step lands reproduces
the exact pattern this session repeatedly caught: relying on a verification
that was assumed rather than performed. If only one of the two changes can
land, it must be the CI step.

**Quiet-window precondition.** These are low-frequency, single-threaded
repositories, so a window can be created deliberately rather than waited for.
Confirm immediately before the rename, per repository:

```bash
gh pr list --state open --json number --jq 'length'   # expect 0
git status --porcelain                                # expect empty (ignore untracked build output)
git worktree list                                     # confirm no worktree branch holds unmerged planning-artifact work
lrh validate                                          # expect 0 errors
```

At the time of writing both repositories satisfied every condition: 0 open PRs
each, clean trees apart from untracked build output in one velumin worktree,
and `0 errors, 0 warnings` from `lrh validate`.

**Counting discipline.** The reference counts above come from `git grep`. An
earlier filesystem `grep -r` reported 75 rather than 57 for the same two
repositories, because it walked `.claude/worktrees/` copies — the error class
`AGENTS.md`'s evidence convention now prohibits. Re-verify with `git grep`
before and after the rename rather than trusting these figures.

**Sequenced late deliberately.** Nothing depends on this and nothing is broken
today — both repositories validate clean. It belongs near the end of the
current program, when attention is not competing with the invocation-and-gate
reset.
