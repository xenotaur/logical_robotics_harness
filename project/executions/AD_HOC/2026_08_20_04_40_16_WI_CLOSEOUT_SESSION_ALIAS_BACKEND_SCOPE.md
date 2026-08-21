---
execution_id: 2026_08_20_04_40_16_WI_CLOSEOUT_SESSION_ALIAS_BACKEND_SCOPE
prompt_id: PROMPT(AD_HOC:WI_CLOSEOUT_SESSION_ALIAS_BACKEND_SCOPE)[2026-08-20T04:38:35+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/572
commit: 
created_at: 2026-08-20T04:40:16+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CLOSEOUT-SESSION-ALIAS-BACKEND-SCOPE.md
session_transcript: pending
---

# Summary

Created work item `WI-CLOSEOUT-SESSION-ALIAS-BACKEND-SCOPE`, one of three
skill-content bugs surfaced while triaging Taurcode PR #82 (a mechanical
`lrh skills install --local --force` resync of this project's own skill
package). `/lrh-closeout` Step 5 tells the agent to run
`record-session-alias --host-id <...>` "for every record, regardless of
which Step 3 path resolved the host id" — but Step 3's `codex_app`,
`codex_cloud`, `manual`, and other-non-Claude branches never resolve a
usable host-uuid-stem, only `codex-app:<id>`, `codex-cloud:<id>`, `pending`,
or `none`.

# Result

Wrote `project/work_items/proposed/WI-CLOSEOUT-SESSION-ALIAS-BACKEND-SCOPE.md`
scoping the fix: reword Step 5 to only run session-alias capture for records
where Step 3 resolved a confirmed Claude host id (paths 1/2/3), and
explicitly skip it for non-Claude backend records, matching the scoping
`references/closeout-workflow.md`'s own "Session identity capture" section
already documents. Opened PR #572 from branch
`xenotaur/chore/wi-closeout-session-alias-backend-scope`. This record covers
the planning phase only (work item creation); implementation of the actual
SKILL.md edit is a separate execution record, to be created when the fix is
implemented.

# Validation

- `lrh validate` — 0 errors, 0 warnings.

# Follow-up

- Implement the fix described in the work item (edit
  `src/lrh/skills/lrh-closeout/SKILL.md` Step 5 and mirror to
  `.claude/skills/lrh-closeout/SKILL.md`).
- Update `session_transcript` from `pending` to the durable session pointer
  once available.

## Review-response round 1

One `chatgpt-codex-connector` P2 finding: register this WI in
`WS-SESSION-ARCHIVE-SYNC`'s `work_items:` list so `/lrh-execute` and
`/lrh-closeout` can discover it through the workstream, since
`related_workstreams`-only cross-references aren't consulted by planning-tree
traversal (`lrh serve`, `/lrh-next`, etc. — confirmed navigability gap,
not a false claim).

**Declined, not fixed.** A workstream's `work_items:` list is an ownership
child list, not a loose cross-reference — anything on it gates that
workstream's closeout (every listed item must resolve before the WS can
close). `WS-SESSION-ARCHIVE-SYNC` already has its own four leaves;
folding this standalone bugfix in would make an unrelated skill-content
correction a precondition for that workstream's closure, which isn't the
intent here. `related_workstreams` (already set) is this project's
established non-owning cross-reference for exactly this "related but not
owned" relationship. The navigability cost Codex raises (discoverable only
by direct ID/search, not via workstream traversal tools) is real and
acknowledged, but the closeout-gating cost of folding it in is worse for a
standalone fix like this one — weighing the tradeoff, `related_workstreams`
stays correct.

No file changes from this finding; `lrh validate` unaffected.
