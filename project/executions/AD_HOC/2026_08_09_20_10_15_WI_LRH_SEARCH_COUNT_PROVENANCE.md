---
execution_id: 2026_08_09_20_10_15_WI_LRH_SEARCH_COUNT_PROVENANCE
prompt_id: PROMPT(AD_HOC:WI_LRH_SEARCH_COUNT_PROVENANCE)[2026-08-09T20:09:10+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-08-09T20:10:15+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-SEARCH-COUNT-PROVENANCE.md
session_transcript: claude-app:3c4e404b-8420-4a62-9c3f-f5dcccfa5400
---

# Summary

Create `WI-LRH-SEARCH-COUNT-PROVENANCE` for a scope-aware, provenance-emitting
counting mode under `lrh search`, complementing the `AGENTS.md` `git grep`
convention that landed earlier in this session.

# Result

Created `project/work_items/proposed/WI-LRH-SEARCH-COUNT-PROVENANCE.md`
(`type: deliverable`, `status: proposed`).

The author proposed a helper alongside the convention, arguing that encoding the
policy in code lets it evolve — to other version-control systems,
project-specific asset layouts, and edge cases not yet encountered. That
argument is recorded and is what justifies the version-control seam.

**A stronger justification was identified during the assessment and became the
work item's primary framing: provenance, not evolution.** Neither a convention
nor a thin wrapper enforces anything; both depend on recall, and recall
demonstrably failed three times in one session — including once while drafting
the recommendation to fix the first two instances. What a helper can uniquely
provide is output that states its own scope, so a count written into an artifact
carries citable evidence. This addresses the actual worst error of the session:
an execution record certifying that worktrees were excluded from a survey when
that was true of only half of it.

The work item is explicit that the helper **cannot fix the failure it is named
for** — a command that must be remembered is subject to the same lapse as a rule
that must be remembered. Its contribution is making counts checkable after the
fact, which is how these errors were actually caught (independent review). Sold
otherwise, it would be a false assurance.

**Placement decided from repo state rather than preference.** `lrh search`
already exists — "Search local LRH project records", with an `executions`
subcommand for "Exploratory substring search over execution records"
(`src/lrh/prompt_workflow_search.py:167-191`) — so a top-level `lrh grep` would
create a second competing search surface. The subparser registration at `:175`
is the pattern to follow, and
`src/lrh/integrations/github/gh_client.py:10` (`run_gh_json`) is the existing
precedent for wrapping an external CLI via subprocess.

Three risks recorded: the helper cannot enforce the convention; "named scopes"
could creep into a query language and should stay grounded in cases that have
actually occurred; and a wrapper diverging from `git grep` semantics (globs,
`-c` aggregation, exit codes) would create a new confusion class.

The convention is explicitly not replaced. Counts were taken this session in
LCATS, `velumin`, and `replication_vector`; the latter two do not run
`lrh validate` in CI at all, so LRH tooling availability across the fleet is
uneven. The convention covers every repository; the helper accelerates those
with LRH installed.

# Validation

- `lrh prompt check-execution --slug wi-lrh-search-count-provenance
  --work-item AD_HOC` → exit 0, no prior record.
- `lrh validate` → 0 errors, 1 warning (pre-existing, unrelated).
- `lrh work-items readiness WI-LRH-SEARCH-COUNT-PROVENANCE` →
  `prompt_ready: yes`.
- Placement grounded by inspecting the existing `lrh search` surface and its
  subparser registration, and by confirming the subprocess-wrapper precedent in
  `gh_client.py`, rather than assuming either.

# Follow-up

No PR opened; the branch is pushed without one, so no automatic bot review
fires.

`related_workstreams:` left empty — no workstream covers CLI tooling or evidence
discipline. This is the third work item in this packet with no workstream home
(alongside `WI-WORK-ITEM-BLOCKED-STATE-EXPRESSIVENESS` and
`WI-SIBLING-REPO-VALIDATE-CI-AND-CONTRIBUTOR-IDS`), which may itself be a signal
worth acting on later.

**Updated 2026-08-09:** adopted by `WS-CROSS-REPO-CODE-HEALTH` later in the same session; the item is no longer unowned.

The convention half of `PROP-CONTRIBUTOR-IDENTITY-CONTRACT` Open Question 5 is
already landed in `AGENTS.md`; this work item is the remaining half, so that
open question can be considered answered once this lands.
