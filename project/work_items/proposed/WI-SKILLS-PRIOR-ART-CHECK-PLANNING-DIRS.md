---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-PRIOR-ART-CHECK-PLANNING-DIRS
title: Fix prior-art-check duplication search to cover planning-artifact directories
type: operation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-PRIOR-ART-CHECK
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance:
  - the canonical src/lrh/skills/_shared/prior-art-check.md duplication-search command includes project/workstreams/ and project/work_items/ alongside project/design/proposals/, src/, and .claude/skills/
  - all 10 synced copies (5 skills x {src/lrh/skills, .claude/skills}) are updated identically to the canonical master
  - diff -r confirms each skill's src/lrh/skills/<skill>/references/prior-art-check.md matches its .claude/skills/<skill>/references/prior-art-check.md mirror byte-for-byte
  - lrh validate reports 0 errors
  - no other skill content is modified
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - documentation
---

## Summary

The shared prior-art-check procedure used by `/lrh-proposal`, `/lrh-workstream`,
`/lrh-work-item`, `/lrh-design`, and `/lrh-implement` scopes its duplication
search to `src/`, `project/design/proposals/`, and `.claude/skills/` only. It
never searches `project/workstreams/` or `project/work_items/` — so a new
workstream or work item can duplicate an existing sibling artifact of the same
kind without the check ever surfacing it.

## Problem / Context

Discovered on PR #466: `/lrh-workstream` was used to create
`WS-LRH-SESSION-ARCHIVE-SYNC`, duplicating an already-more-developed
`WS-SESSION-ARCHIVE-SYNC` (different ID prefix, same governing proposal, same
four-stage plan) that a concurrent session had already built — complete with a
filed work item, a resolved open question, and an addressed review round. The
skill's own Step 1 (exact-filename existing-workstream check) could not catch
this by design — it matches only the *exact* ID about to be created, not a
same-topic sibling under different wording. The Prior Art Check step (Step 3)
*should* have caught it, but its duplication search — `grep -rl "<key-term>"
src/ project/design/proposals/ .claude/skills/` — never looks at
`project/workstreams/` at all. The duplication was found only by external
GitHub bot review (Copilot and Codex, independently) during review-response,
not by the skill's own procedure. PR #466 was closed unmerged as a result.

### Prior Art Check

**Duplication search:**
- In-repo: No existing fix for this gap. `WS-PRIOR-ART-CHECK` (resolved)
  authored the current procedure but its Non-Goals address only automated
  drift-checking between the shared master and its synced copies — a
  different concern from the search-location content gap this work item
  fixes.
- Sibling repos: None identified.
- External libraries: N/A — this is a fix to LRH's own skill instructions.
- Recommendation: Proceed.

**Demand search:**
- Work items: None found requesting this specific fix.
- Proposals: None found.
- Backlog: One related entry (`project/design/backlog.md`, "Validator
  drift-check for synced skill references") — a different, already-deferred
  concern (automated drift detection, not search-location content). No
  action needed; not a match.
- Recommendation: No action.

## Scope

- `src/lrh/skills/_shared/prior-art-check.md` (canonical source)
- Its 10 synced copies:
  - `src/lrh/skills/{lrh-proposal,lrh-workstream,lrh-work-item,lrh-design,lrh-implement}/references/prior-art-check.md`
  - `.claude/skills/{lrh-proposal,lrh-workstream,lrh-work-item,lrh-design,lrh-implement}/references/prior-art-check.md`

## Required Changes

1. In the canonical file's Sub-search 1 (Duplication search) location list,
   change:
   ```
   grep -rl "<key-term>" src/ project/design/proposals/ .claude/skills/ 2>/dev/null
   ```
   to:
   ```
   grep -rl "<key-term>" src/ project/design/proposals/ project/workstreams/ project/work_items/ .claude/skills/ 2>/dev/null
   ```
2. Add a sentence to the "In-repo" search bullet noting that a sibling
   planning artifact of the same kind about to be created is exactly the
   highest-risk duplicate, so this search must not rely solely on the
   proposal/design-doc surface.
3. Note explicitly (in the same section) that a governing proposal's own
   cross-references cannot be trusted as an exhaustive map of what already
   exists — a concurrently created sibling artifact has no reason to be
   linked back into an earlier proposal's text.
4. Propagate the identical change to all 10 synced copies, byte-for-byte
   except each copy's own pre-existing header-comment wording
   (`CANONICAL SOURCE` vs `SYNCED COPY`), which is intentionally different
   and must not be changed.

## Non-Goals

- Does not add automated drift-checking between the master and its copies
  — already deferred in `project/design/backlog.md`; out of scope here.
- Does not change Sub-search 2 (Demand search) — its location list already
  covers `project/work_items/proposed/` and `project/design/proposals/proposed/`.
- Does not change `/lrh-workstream`'s Step 1 exact-filename existing-check —
  that check has a different, narrower purpose (ID-collision prevention, not
  topic-duplication detection) and is working as designed.
- Does not modify any skill file outside the 11 `prior-art-check.md` files
  listed in Scope.

## Acceptance Criteria

See the `acceptance` frontmatter. In short: the canonical duplication search
covers all three planning-artifact directories, all 10 copies match the
canonical file identically, and `lrh validate` stays green.

## Validation

- `lrh validate`
- `diff -r src/lrh/skills/lrh-proposal/references/ .claude/skills/lrh-proposal/references/` (and the same for workstream, work-item, design, implement)
