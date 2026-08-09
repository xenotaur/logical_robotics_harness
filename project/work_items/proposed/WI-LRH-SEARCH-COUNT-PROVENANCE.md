---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-SEARCH-COUNT-PROVENANCE
title: Add lrh search count -- a scope-aware, provenance-emitting counter for decision-feeding surveys
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-CROSS-REPO-CODE-HEALTH
related_design:
  - project/design/proposals/proposed/contributor-identity-contract/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - replace_the_agents_md_convention
acceptance:
  - lrh search count reports a match count together with the scope it used and what it excluded, in a form that can be pasted into an artifact as evidence
  - Scope is selectable by name rather than by the caller reconstructing glob and exclusion flags
  - The implementation isolates version-control specifics behind one seam, so a non-git backend can be added without changing the CLI surface or the output contract
  - The command lives under the existing lrh search subcommand rather than as a new top-level command
  - The AGENTS.md git grep convention remains authoritative and is not replaced -- the helper is an accelerant for repositories with LRH tooling installed
  - New Python carries unit tests, including a worktree case that would have produced the 10x inflation this work item exists to prevent
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_new_python
artifacts_expected:
  - src/lrh/prompt_workflow_search.py
  - src/lrh/cli/main.py
  - tests/cli_tests/
  - AGENTS.md
---

# Add `lrh search count` — a scope-aware, provenance-emitting counter for decision-feeding surveys

## Summary

Add a counting mode to `lrh search` that reports not just a number but the scope
it counted over and what it excluded, so a count written into a planning artifact
carries its own evidence. The `AGENTS.md` convention requiring `git grep` for
decision-feeding counts stays authoritative; this makes the correct thing
convenient and self-documenting, and gives the scope rules a single home that can
evolve.

## Problem / Context

Repository-wide counts feed real decisions in this project: a proposal's
reference count, a work item's scope estimate, an audit's file tally. In a single
session, three such counts were wrong, all from the same cause — filesystem
`grep -r` walking `.claude/worktrees/` checkouts and untracked files:

| Reported | Actual (tracked) | Cause |
|---|---|---|
| LCATS 180 contributor-id refs | 18 | 9 worktrees × 9 files + 9 real |
| `prosocial` has an orphan `owner:` ref | zero tracked | untracked file in a worktree |
| 75 spaced-id refs across two repos | 57 | worktree copies |

The third occurred *while drafting the recommendation to fix the first two*. That
is the load-bearing evidence for this work item: the failure is habitual, not
informational. `AGENTS.md`'s `### Evidence` section now carries the convention,
but a rule that must be remembered was already forgotten once by the person
writing it.

### Why a helper, and why this shape

A thin `git grep` alias would not have prevented any of the three errors — it
would have to be remembered exactly as the convention does, and it adds a CLI
surface with no behavioural gain. The value is in two things a wrapper alone does
not provide:

**Provenance in the output.** The most damaging error was not using the wrong
command; it was an execution record certifying "Fleet survey run … excluding
`.claude/worktrees/` copies to avoid double-counting" when that was true of half
the survey. A command that reports its own scope produces a line an artifact can
cite and a reviewer can check. "I ran `git grep`" is unfalsifiable prose.

**The failure is broader than worktrees, and that is the design discussion this
work item should carry.** Every wrong claim in the originating session came from
the same shape of mistake — *checking a narrower surface than the claim
covered* — and only the first instance was a worktree problem:

| Claim made | Surface actually checked | Surface the claim covered |
|---|---|---|
| LCATS has 180 refs | filesystem `grep -r` | tracked files only |
| `prosocial` has an orphan `owner:` | filesystem, incl. untracked | tracked files |
| Neither sibling repo runs `lrh validate` in CI | `.github/workflows/` | the `scripts/validate` those workflows call |
| The `github:` addition is safe standalone | registry frontmatter | the registry **body**, which documented the placeholder as deliberate |
| Retriggers are removed | `src/` and `.claude/` in this repo | **`~/.claude/skills/`**, the user-level install every repo loads from |

The last is the sharpest: the retrigger commands were verified absent from the
repository and still present in the copy that actually executes. A worktree-aware
`git grep` would not have caught it, because the relevant corpus was not this
repository at all.

So the scope question is not "which files in this repo" but "**what is the
corpus this claim is about**" — and the answer is sometimes outside the
repository. That is the design discussion this work item owns. Candidate corpora
observed so far: tracked files here; the user-level `~/.claude/skills/` install;
sibling repositories' installed copies; a file's body rather than its
frontmatter; a script a CI workflow calls rather than the workflow itself. Not
all are greppable the same way, and some may not belong in a search tool at all
— resolving that is part of the work, not a precondition to it.

**A home for the non-obvious part.** *How* to grep is obvious; *what to count
over* is not, and it varies:

- tracked files in the active checkout (today's default, and the right answer for
  most surveys);
- deliberately including other worktrees, when asking "is anyone else editing
  this";
- excluding `project/executions/`, when counting current usage rather than
  historical mentions — a real distinction no single `git grep` invocation
  expresses;
- **the installed skill corpus rather than the source one** — `~/.claude/skills/`
  and any per-repo `.claude/skills/`, which is what actually executes and which
  can be arbitrarily stale relative to `main`;
- project-specific asset layouts, where the interesting corpus is not "tracked
  markdown";
- version-control systems other than git, where `git grep` is simply unavailable.

Encoding those as named scopes puts the judgement in one testable place instead
of in each caller's flags.

### Prior art

`lrh search` already exists and is described as "Search local LRH project
records", with an `executions` subcommand for "Exploratory substring search over
execution records" (`src/lrh/prompt_workflow_search.py:167-191`). That makes it
the natural home: a new top-level `lrh grep` would create a second, competing
search surface. The subparser registration at `:175` is the pattern to follow.

`src/lrh/integrations/github/gh_client.py:10` (`run_gh_json`) is the precedent
for wrapping an external CLI via subprocess, so shelling out to `git grep` fits
the existing architecture rather than introducing a new one.

**Duplication search.** In-repo: no existing counting or survey command;
`lrh search executions` is adjacent but searches record *content*, not
repository-wide counts. Sibling repos: none identified. External libraries:
`ripgrep` and similar solve fast searching, not scope policy or provenance
reporting — adopting one would not address either motivating problem.
Recommendation: proceed.

**Demand search.** No work item, proposal, or backlog entry requests this.
`PROP-CONTRIBUTOR-IDENTITY-CONTRACT` Open Question 5 raised the convention-vs-helper
question; this work item is the helper half. Recommendation: link that proposal;
nothing to close.

## Scope

A counting mode under `lrh search`, its scope definitions, its output contract,
and the version-control seam behind it. Plus an `AGENTS.md` cross-reference
pointing at the helper from the existing convention.

Out of scope: replacing the convention (see Non-Goals), changing
`lrh search executions`, and adding non-git backends — the seam must exist, but
implementing a second backend is speculative until a repository needs one.

## Required Changes

1. Add a counting subcommand under `lrh search`, following the subparser pattern
   at `prompt_workflow_search.py:175`.
2. Emit a count together with its scope and exclusions, in a single line
   designed to be pasted into an artifact as evidence — for example:
   `57 matches in 12 tracked files (scope: tracked; excluded 9 worktree
   checkouts, 2 untracked)`. The exclusion counts must be real, not asserted:
   if the command cannot determine them, it must say so rather than print zero.
3. Provide named scopes rather than raw flags. `tracked` is the default; the
   remaining set should be chosen from the cases listed above and kept small.
4. Isolate version-control specifics behind one function or class, so the CLI
   surface and output contract do not change when a non-git backend is added.
   Do not implement a second backend.
5. Cross-reference the helper from `AGENTS.md`'s `### Evidence` convention,
   keeping `git grep` as the portable baseline for repositories without LRH
   tooling.
6. Add unit tests, including a fixture with a worktree checkout that reproduces
   the multiplication effect — a test that would have caught the 10× error.

## Non-Goals

- **Does not replace the `AGENTS.md` convention.** The helper only works where
  `lrh` is installed. Counts were taken this session in LCATS, `velumin`, and
  `replication_vector`; the latter two do not even run `lrh validate` in CI, so
  tooling availability across the fleet is uneven. The convention covers every
  repository; the helper accelerates the ones with LRH installed.
- Does not implement a non-git version-control backend — only the seam.
- Does not attempt to enforce the convention. Verifying mechanically that a
  number in prose came from a particular command is not possible; a tool that
  reports its own scope is the achievable form of assurance.
- Does not change `lrh search executions` or add a top-level `lrh grep`.
- Does not optimize for speed. `git grep` is already fast; the value here is
  correctness and provenance.

## Acceptance Criteria

- `lrh search count` reports a match count with the scope used and what was
  excluded, in a form citable in an artifact.
- Scope is selectable by name, not reconstructed from flags by the caller.
- Version-control specifics sit behind one seam; adding a non-git backend would
  not change the CLI surface or output contract.
- The command lives under `lrh search`, not as a new top-level command.
- The `AGENTS.md` convention remains authoritative and cross-references the
  helper.
- Unit tests cover the scopes, including a worktree fixture reproducing the
  inflation case.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `scripts/test` passes, including the new worktree-fixture cases
- Manual: run the counter against a repository with active worktrees and confirm the reported count matches `git grep -c` and the excluded-worktree count is accurate
- Manual: confirm the output line reads sensibly when pasted into a planning artifact as evidence
- Regression: `lrh search executions` behaviour unchanged

## Risk Notes

**The helper cannot fix the failure it is named for, and should not be sold as
if it can.** All three miscounts came from reaching for `grep -r` by habit; a
command that must be remembered is subject to the same lapse. Its real
contribution is making a count *checkable after the fact* — which is what
actually caught these errors, via independent review. Expect the convention plus
review to remain the primary defence, with the helper reducing the cost of doing
it right.

**Scope creep is the design risk.** "Named scopes" could grow into a query
language. Keep the set small and grounded in cases that have actually occurred;
add a scope when a real survey needs it, not in anticipation.

**A wrapper that diverges from `git grep` semantics would create a new confusion
class** — glob handling, `-c` aggregation across files, and exit codes all have
established meanings. Either match them or document the difference prominently;
do not silently differ.
