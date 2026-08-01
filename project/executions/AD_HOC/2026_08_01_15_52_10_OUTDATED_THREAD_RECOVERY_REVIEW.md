---
execution_id: 2026_08_01_15_52_10_OUTDATED_THREAD_RECOVERY_REVIEW
prompt_id: PROMPT(AD_HOC:OUTDATED_THREAD_RECOVERY_REVIEW)[2026-08-01T15:51:23-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_01_12_28_08_OUTDATED_THREAD_RECOVERY
pr: https://github.com/xenotaur/logical_robotics_harness/pull/457
commit: 50ab976ca66e1d773a8de4f6d318301d7da7b8b8
created_at: 2026-08-01T15:52:10-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/457
session_transcript: claude-app:61881211-bfd7-40cb-8080-33938a265398
---

# Summary

Addresses review on PR #457 (planning artifacts: PROP-OUTDATED-THREAD-RECOVERY
+ 2 work items) across multiple rounds as Codex/Copilot progressively
found deeper issues in the recovery-path design itself. Each round's
findings were batched into a single push (not one push per finding), per
this session's own discussion about GitHub review credit consumption —
this record's per-round breakdown below documents each round's commit
and findings individually; see the record's `commit:` frontmatter field
for the latest.

# Result

Round 1 — one commit pushed to branch `xenotaur/feat/outdated-thread-recovery`:

- `4c1b856` — fixes all 6 findings plus the workstream fold.

**Issue A — Merge-gate invariant undefined for fix now/defer (Codex,
P1):** Fixed. Decision 2 didn't say how "fix now" or "defer" satisfy
`/lrh-land` Step 6's green-verdict requirement. Added explicit
disposition: "fix now" loops back through `/lrh-confirm-fixes` for a
fresh verdict before Step 6 is reachable; "defer" is a named, audited,
in-session override of the invariant, not a silent bypass. Propagated
the same language into WI-B's acceptance criteria and Required Changes.

**Issue B — Workstream traversal (Codex, P2, fabricated citation but
valid underlying claim):** Codex cited `AGENTS.md:L43-L49`, which does
not exist/say what was claimed — verified directly against
`src/lrh/control/planning_tree.py:315` instead, which confirmed the
substantive point: planning-tree traversal builds `children_by_parent_id`
from a workstream's `work_items:` list, not `related_workstreams`
(metadata-only). This reopened an earlier decision made in this same
session (leave the two WIs related-only) — surfaced the new technical
fact to the user rather than silently overriding or silently keeping the
old call. User chose to fold; added both WI IDs to
`WS-SKILLS-EXECUTE`'s `work_items:` list.

**Issues C-F — wording/terminology (Copilot x4):** Fixed. "supersedes/
closes" language in the proposal contradicted the backlog entry's own
"stays open until implemented" status (2 occurrences); normalized
"Problematic-resolution"/"Problematic-comment" to the taxonomy's actual
spelling ("Problematic resolution"/"Problematic comment", verified
against `src/lrh/skills/lrh-confirm-fixes/SKILL.md:164-165`) across
WI-B (9 occurrences); clarified WI-B's backlog-closure step timing
(link now, close only once both items are implemented).

**Round 2 (commit `3380a17`): Issue G — same closure-timing bug, missed
in WI-A (Codex P2 + Copilot suppressed, same root cause independently
caught by both):** The round-1 fix only corrected WI-B's and the
proposal's closure-timing wording; WI-A's own Demand-search section had
the identical bug ("Close the backlog entry once this item ... are
filed" — filed, not implemented). Fixed to match the same
link-now/close-on-implementation language used everywhere else.

**Round 3 (commit `60ddfaf`): three findings.** Issue H — Codex P1,
"Reconcile the dependency gate with single-PR delivery": the
Implementation Plan's "single implementation PR" claim structurally
conflicts with `/lrh-execute`'s own `depends_on` gate (verified against
`PROP-LRH-LAND-EXECUTE` Decision 4: "enforce `depends_on` — all entries
must be `resolved`; stop and report if not," in
`project/design/proposals/proposed/lrh-land-execute/00_proposal.md:218`)
— WI-B's `depends_on: [WI-REVIEW-RESPONSE-INCLUDE-THREAD]` means WI-A
must already be resolved before WI-B is selectable through the governed
path, making single-PR delivery structurally undeliverable regardless of
diff-meaningfulness reasoning. Switched the Implementation Plan (and the
matching prose in WI-B) to standard sequential two-PR delivery — the
already-well-supported `depends_on` pattern, not a special case. Issue I
— Codex P2, a race condition where a named thread could be resolved
between confirm-fixes' classification and `review_response`'s fetch:
added an explicit `isResolved` check to WI-A's design before
force-including a thread, with a distinct clear result instead of a
silent no-op. Issue J — Copilot (suppressed): WI-A's plan called the
private `_collect_threads` helper across a module boundary; changed to
introduce a small public helper instead. Verified against
`src/lrh/integrations/github/formatters.py:18` (`_collect_threads` has
no public export) before applying the fix.

**Round 4: four findings, including a direct echo of PR #453's own
governance failure.** Issue K — Codex **P1**, "Enforce the approved
stop-work condition before recovery": the three-way gate was presented
unconditionally, without first checking whether the newly-surfaced
finding already fell within the run's own Step-2-approved stop-work
condition — the exact class of failure (silently continuing past a
human-set halt condition) that got PR #453's original automatic
exception reverted, reached here through a different path (an
unconditional gate rather than an unconditional non-stop). Added an
explicit precondition check before the gate is presented: if the finding
matches the stop-work condition, halt-and-report per that condition;
continuing requires an explicit amendment, not just an answer to the
gate. Issue L — Codex P1, "Preserve all non-thread readiness gates when
deferring": "defer" was written broadly enough to read as overriding the
*entire* green-verdict invariant rather than only the one named thread.
Scoped it explicitly: CI, REVIEW-LANDED, and every other exception must
still independently be green or cleared. Issue M — Codex P2, "Pass the
included thread through review-response Step 2": Decision 4's "route
through the full protocol" language didn't say the recovery flow must
explicitly carry `--include-thread <id>` into review-response's own Step
2 fetch command — without that explicit propagation, Step 2 still runs
unflagged and exits on `Nothing to resolve:`, reproducing PR #453's
original bug one layer down. Made the propagation explicit in Decision 4
and WI-B's Required Changes/Acceptance Criteria. Issue N — Copilot
(suppressed): this record's own Round 1 Summary claimed a "single
commit" while the record already documented Rounds 2-3 — an internal
inconsistency in the record's own framing, not the design. Rewrote the
Summary to describe the multi-round structure accurately.

# Validation

scripts/version tools -- Black 26.3.1, Ruff 0.15.12 confirmed
scripts/format --check --diff -- 179 files unchanged
lrh validate -- 0 errors, 1 pre-existing unrelated warning
grep -n "^def _matches_state" -A 12 src/lrh/integrations/github/formatters.py -- confirmed line 31-40 citation still accurate against current main
grep -n "Problematic" src/lrh/skills/lrh-confirm-fixes/SKILL.md -- confirmed exact taxonomy spelling before applying the fix
grep -n "work_items\|parent_id" src/lrh/control/planning_tree.py -- confirmed Codex's underlying traversal claim before triaging it as valid, independent of its fabricated citation

# Follow-up

- Round-cap ceiling (3) reached for PR #457 after round 3's retrigger;
  present the three-way round-cap gate to the human before retriggering
  a 4th batch for round 4's fixes.
- Retrigger both reviewers on the round-4 commit once authorized, and
  verify all remaining threads resolve against the pushed diff.
- Update `session_transcript` to the final host session id if it differs
  after the session ends.
