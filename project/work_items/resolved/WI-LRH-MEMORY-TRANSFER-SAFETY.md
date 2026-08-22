---
resolution: "Implemented and merged in PR #597 (commit 8f40e33a) -- fixed silent path misresolution in transfer's --from/--to and added a force+snapshot overwrite guard (same-agent and legacy no-authored_by destinations) to transfer/import."
blocked_reason: null
blocked: false
id: WI-LRH-MEMORY-TRANSFER-SAFETY
title: Fix silent path misresolution and unsafe overwrite in lrh memory transfer/import
type: deliverable
status: resolved
owner: null
contributors: []
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-LRH-MEMORY-COMMAND
related_design:
  - project/design/proposals/adopted/lrh-memory-command/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - implement_hub_and_spoke_consolidation
  - redesign_transfer_public_api
acceptance:
  - "lrh memory transfer --from <bare-relative-dir> --to <bare-relative-dir> either resolves the path as intended or fails loudly -- never silently reports 0 written / 0 errors when source records existed"
  - "lrh memory transfer/import require --force (or otherwise surface a clear warning) before overwriting a destination memory whose authored_by matches the incoming record's or is absent (a legacy pre-authored_by record), and preserve the prior content (e.g. a history/ snapshot) before it is overwritten"
  - "write_memory's own same-agent overwrite-on-purpose behavior (a session revising its own memory via repeated lrh memory write) is unchanged -- this fix is scoped to transfer/import's call sites only"
  - "Existing transfer/import behavior for genuine cross-agent conflicts and for an already-existing literal slug is unchanged"
  - "import --force's and transfer --force's CLI help text accurately describes the new overwrite semantics"
  - "lrh validate reports 0 errors; new regression tests reproduce both original defects, the legacy-record case, and confirm the fix"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/prompt_workflow_memory.py
  - src/lrh/memory_workflow.py
  - tests/assist_tests/prompt_workflow_memory_test.py
  - tests/cli_tests/memory_test.py
---

# Fix silent path misresolution and unsafe overwrite in lrh memory transfer/import

## Summary

Fix two correctness bugs in `lrh memory transfer`/`import`: a bare relative
directory name silently misresolves as a literal corpus slug instead of a
path (silent no-op with no error), and a same-agent destination overwrite
happens unconditionally with no snapshot -- unlike `lrh memory sync`'s
snapshot-before-overwrite invariant.

## Problem / Context

Both bugs were found live while evaluating whether a hub-and-spoke
memory-consolidation workflow (multiple session corpora feeding one "hub,"
periodically refreshed back out to "spokes") was reasonable to build on top
of `WI-LRH-MEMORY-PORTABILITY`'s existing `export`/`import`/`transfer`
primitives (PR #589). Both are defects in already-merged, already-shipped
behavior, independent of whether the hub-and-spoke feature itself is ever
built.

**Bug 1 -- silent no-op on a bare relative path.**
```
$ lrh memory transfer --from spoke1 --to hub --agent claude
import complete: 0 written, 0 errors
```
No error, no warning, looks successful. `--from spoke1` (the natural way to
reference a sibling directory) gets treated as a literal corpus slug by
`_resolve_memory_dir` rather than resolved relative to the caller's cwd,
because it contains no path separator. `--from ./spoke1` or an absolute path
works correctly -- confirmed by direct comparison in the same session.

**Bug 2 -- unconditional, unsnapshotted same-agent overwrite.**
```
$ lrh memory read feedback-x --project-root spoke1   # before
spoke1's LOCALLY EDITED version, not yet pushed anywhere
$ lrh memory transfer --from hub --to spoke1 --name feedback-x
import complete: 1 written, 0 errors
$ lrh memory read feedback-x --project-root spoke1   # after
hub's canonical version
```
No `--force` was required (same-agent overwrites are unconditional in
`_write_memory_into_dir`), and no `history/` snapshot was kept -- spoke1's
local edit was destroyed irrecoverably.

### Duplication search
- In-repo: No existing implementation addresses either defect.
  `mirror_file_with_snapshot` (`src/lrh/prompt_workflow_sessions.py`,
  generalized during `WI-LRH-MEMORY-ARCHIVE-SIDE`) already implements a
  snapshot-before-overwrite invariant for a *different* code path
  (`sync`, not `transfer`/`import`) -- the closest existing pattern to
  draw on for Bug 2, not a duplicate of this WI's own scope.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found.
- Proposals: Found -- `PROP-LRH-MEMORY-COMMAND` (adopted; the design this
  work item's `transfer`/`import` behavior is built under) -- but its Open
  Questions section does not anticipate either of this WI's two specific
  failure modes, so it names no remediation for them.
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Fix `_resolve_memory_dir`'s path-vs-slug ambiguity for `transfer`'s
  `--from`/`--to` so a bare relative directory name either resolves as the
  caller intended or fails loudly -- never silently no-ops.
- Add a safety check before `transfer`/`import` silently overwrite a
  same-agent or legacy (no `authored_by`) destination memory, so a local
  edit cannot be irrecoverably destroyed with no `--force` and no history.
- Do not implement the hub-and-spoke consolidation/refresh feature itself
  -- that is separate design work, tracked outside this WI.

## Required Changes

1. In `src/lrh/prompt_workflow_memory.py`'s `_resolve_memory_dir`, resolve
   the path-vs-slug ambiguity for a bare relative-looking value. Candidate
   approaches (not prescribed -- implementor's judgment): reject an
   ambiguous bare relative name with a clear error rather than silently
   picking slug-interpretation; require an explicit `./` prefix (or a
   leading `.`/`..`) to force path-interpretation; or split `--from`/`--to`
   into separate path and slug flags. Whichever is chosen, a value that
   resolves to zero records at the source must never report a bare
   `0 written, 0 errors` -- that must be distinguishable from "genuinely
   empty after filtering."
2. In `transfer`/`import`'s call sites into `_write_memory_into_dir`
   (`src/lrh/prompt_workflow_memory.py`), add a same-agent overwrite
   safety check: require `--force` (reusing the existing flag) or an
   equivalent explicit signal before overwriting a same-agent destination
   memory, and preserve the destination's prior content before overwrite
   (e.g. a `history/`-style snapshot, following `sync`'s existing
   pattern) once permitted. `write_memory`'s own direct-write path (a
   session revising its own memory) must remain unconditional --
   requiring `--force` there would break normal editing; the guard
   belongs at `transfer`/`import`'s call sites only, not inside
   `_write_memory_into_dir` itself if that would affect `write`.
   The same guard must also cover a destination memory with **no**
   `authored_by` at all -- `_write_memory_into_dir`'s existing
   cross-agent check only fires `if existing_authored_by and
   existing_authored_by != agent` (`prompt_workflow_memory.py:304`), so
   an absent `authored_by` currently bypasses the check entirely.
   `PROP-LRH-MEMORY-COMMAND` treats the ~440 pre-schema memories lacking
   this field as valid, reachable "legacy" records, not malformed ones
   (`00_proposal.md:79`), so `transfer`/`import` overwriting one
   unconditionally is the same silent-destruction risk as the same-agent
   case this WI already targets -- require `--force`/an equivalent signal
   and a prior-content snapshot there too.
3. Update `import --force`'s and `transfer --force`'s CLI help text in
   `src/lrh/memory_workflow.py` (currently: "overwrite even if
   authored_by differs from the bundled/transferred record" --
   `memory_workflow.py:147`, `:185`), which becomes inaccurate once
   `--force` is also required for a same-agent or legacy-record
   overwrite. Add a test assertion on the updated help text (not just
   `lrh memory transfer --help`'s manual invocation in Validation) so a
   future regression is caught automatically.
4. Add regression tests reproducing both original defects (the exact
   repro transcripts above), the legacy-record (no `authored_by`) case,
   and confirming the fix, in `tests/assist_tests/prompt_workflow_memory_test.py`
   and `tests/cli_tests/memory_test.py`.

## Non-Goals

- Does not implement the hub-and-spoke memory-consolidation/refresh
  feature -- that requires its own design proposal.
- Does not change `write`'s or `export`'s own existing behavior.
- Does not add an incremental/diff-based transfer mechanism ("what's new
  since last refresh") -- out of scope for a bugfix.

## Acceptance Criteria

- `lrh memory transfer --from <bare-relative-dir> --to <bare-relative-dir>`
  either resolves correctly or fails loudly -- never a silent no-op.
- `transfer`/`import` require `--force` (or an equivalent explicit signal)
  before a same-agent or legacy (no `authored_by`) overwrite, and
  preserve prior content first.
- `write_memory`'s own same-agent overwrite-on-purpose behavior is
  unchanged.
- Existing cross-agent-conflict and existing-literal-slug behavior is
  unchanged.
- `import --force`'s and `transfer --force`'s CLI help text accurately
  describes the new overwrite semantics.
- `lrh validate` reports 0 errors; new regression tests reproduce both
  original defects, the legacy-record case, and confirm the fix.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh memory transfer --help`

## Risk Notes

- Bug 1's fix touches `_resolve_memory_dir`'s public contract for
  `transfer`'s `--from`/`--to` -- verify no other in-repo caller depends
  on the current silent-slug-preference behavior before changing it.
- Bug 2's fix must not affect `write_memory`'s own same-agent overwrite
  semantics (see Required Change #2) -- a regression there would break
  the normal "revise my own memory" editing workflow every other WI in
  this workstream relies on.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-LRH-MEMORY-COMMAND.md`
- Design: `project/design/proposals/adopted/lrh-memory-command/00_proposal.md`
