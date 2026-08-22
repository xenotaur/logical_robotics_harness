---
execution_id: 2026_08_22_04_24_27_REPLICATIONVECTOR_CHECKLIST_MEMORY_SCOPE_REVIEW
prompt_id: PROMPT(AD_HOC:REPLICATIONVECTOR_CHECKLIST_MEMORY_SCOPE_REVIEW)[2026-08-22T04:24:20+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/599
commit: e52fcb55b7253eac77db81d4f6839599cc663eec
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/599
session_transcript: claude-app:dcf660e9-d89f-41e7-a220-edcede420919
created_at: 2026-08-22T04:24:27+00:00
---

# Summary

Address four open review comments on PR #599: two Copilot, two Codex (one
pair — Copilot + Codex — was the same substantive finding). All four
passed presence/validity/feasibility triage; none conflicted with a
design decision, but one required correcting in the *opposite* direction
from what was literally requested, after empirical verification showed
the requested wording would have introduced a real inaccuracy.

`rerun_of` is empty: no primary implementation record exists for this
hand-authored PR.

# Result

**Copilot + Codex — `project_slug_for_path` resolves symlinks, contradicting
the scope note's "literal path string" claim (fixed, but not as
requested).** Presence: confirmed — `project_slug_for_path`
(`src/lrh/prompt_workflow_sessions.py:565-582`) does call
`.expanduser().resolve()` before slugging. Validity of the code
observation: correct. Validity of the *inference* the comments drew from
it ("so two symlinked paths may map to the same bucket," and the
requested rewrite to "resolved absolute path"): **empirically false**,
verified directly — LRH's own real, on-disk buckets include both
`-Users-centaur-Workspace-LogicalRoboticsHarness-logical-robotics-harness`
(old symlinked path) and
`-Users-centaur-Tempspace-Projects-LogicalRoboticsHarness-logical-robotics-harness`
(new real path) as two genuinely separate, independently-populated
buckets — Claude Code's actual bucketing does not resolve symlinks the
way `project_slug_for_path()`'s code does. Accepting the literal
requested wording change would have made the document state something
false. Feasibility: fixed by strengthening the scope note instead —
cited the empirical two-bucket evidence as authoritative, then flagged
`project_slug_for_path`'s `.resolve()` call as a genuine discrepancy
from Claude Code's observed behavior (not a documentation nuance),
noting the sibling `bucketlib.slugify` in the same `experimental/`
directory does *not* resolve and matches reality — `project_slug_for_path`
is the outlier. This is a real, out-of-scope-for-this-PR bug worth its
own fix; flagged separately rather than silently left for someone to
rediscover.

**Copilot — `git-scm.com/docs/git-worktree` citation in a code span
won't render as a link (fixed).** Trivial: converted to a real Markdown
link.

**Codex — "being designed separately as hub-and-spoke" overclaims tracked
status (fixed).** Presence: confirmed — no hub/spoke-named artifact
exists anywhere in `project/design/proposals/` or `project/work_items/`
as of this PR. Validity: confirmed valid — the adopted
`PROP-LRH-MEMORY-COMMAND` proposal explicitly chose the
already-shipped, operator-initiated `transfer` command and lists
automatic propagation as a deferred, not-yet-scheduled idea, not active
tracked work. Feasibility: trivial wording fix — reworded to "a separate,
in-progress investigation (not yet a tracked artifact in this repo as of
this writing)," named the actually-shipped `transfer` mechanism
explicitly, and added an explicit caution against assuming a hub is
already being built just because an investigation is underway.

Nothing skipped.

# Validation

`lrh validate` — 0 errors, 0 warnings.

# Follow-up

- The `project_slug_for_path` vs. `bucketlib.slugify` resolve-behavior
  discrepancy is a real bug candidate, out of scope for this
  documentation-only PR — flagged for a follow-up fix separately (any
  `lrh` command relying on `project_slug_for_path` to resolve a
  symlinked path would silently target the wrong bucket).
- `session_transcript` resolved directly (same Claude host session that
  opened PR #599, no `pending` needed).
