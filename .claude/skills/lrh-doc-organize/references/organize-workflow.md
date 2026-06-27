# Documentation Organize Workflow Context

Where `/lrh-doc-organize` fits in the documentation workflow lifecycle, how
execution records are created, and what comes next. Read before Step 5
(confirm gate) and Step 10 (execution record).

---

## Lifecycle placement

```
/lrh-doc-audit                        ← produces audit artifact
    │  Discovers docs, classifies by Diataxis, identifies gaps,
    │  writes project/audits/docs/docs-audit-YYYY-MM-DD.md
    │
    ▼
/lrh-doc-organize [audit-path] [--phase N]   ← THIS SKILL
    │  Reads "Proposed first PR scope" (phase 1) or phase N
    │  Confirms scope with user
    │  Implements one phase: moves, stubs, README updates
    │  Opens a reviewable PR
    │
    ▼
(repeat /lrh-doc-organize for each subsequent phase)
    │
    ▼
/lrh-doc-work <PR-URL | WI-ID | WS-ID>  ← update docs after new work lands
    │  Identifies which docs are affected by completed work
    │  Classifies needed updates by Diataxis quadrant
    │  Implements updates in a reviewable PR
```

---

## Relationship to `/lrh-doc-audit`

`/lrh-doc-audit` is designed to be run before `/lrh-doc-organize`. The audit
artifact's "Proposed first PR scope" section is the primary scope source for
this skill. Without an audit:

- The skill falls back to a small discovery pass (discovery mode).
- Discovery-mode scope is conservative and may miss systemic issues.
- The skill flags discovery mode at the confirm gate and recommends running
  the audit first.

The audit artifact's "Recommended phased PRs" section maps multi-phase
reorganizations. Each phase becomes one `/lrh-doc-organize` invocation.
Phases should be run in order — later phases may depend on earlier ones.

---

## Relationship to `/lrh-doc-work`

`/lrh-doc-work` handles a different trigger: it updates docs after new code
or design work lands (a merged PR, a resolved work item, a closed workstream).
`/lrh-doc-organize` handles structural layout; `/lrh-doc-work` handles content
currency. They are complementary and typically run at different points:

- Run `/lrh-doc-organize` to improve the structure of existing docs.
- Run `/lrh-doc-work` after a feature ships to ensure new docs are written
  and stale docs are updated.

A typical project cadence: audit → organize (phases 1–N) → ongoing
`/lrh-doc-work` after each feature lands.

---

## Execution record convention

`/lrh-doc-organize` creates an AD_HOC execution record (not a WI-* record)
because each organize run is a one-off operation, not a predefined work item.

### Slug derivation

Use `doc-organize-phase-<N>-<YYYY-MM-DD>` as the slug:

```
doc-organize-phase-1-2026-06-27
doc-organize-phase-2-2026-06-28
```

This makes multiple organize runs on the same audit distinguishable.

### Required fields

```yaml
agent: claude_app
instruction_source: <path-to-audit-artifact or "discovery mode — no audit available">
session_transcript: pending
```

Update `session_transcript` from `pending` to `claude-app:<session-id>` after
the session ends.

### rerun_of

`/lrh-doc-organize` does not have a primary work item execution record to link
back to (it is always AD_HOC). Leave `rerun_of:` empty.

---

## After the PR lands

1. Update the execution record: set `status: landed`, `pr:`, `commit:`,
   and `session_transcript:` (if still `pending`).
2. Run `lrh validate` to confirm the record is valid.
3. Commit the updated record directly to main.
4. If the audit has more phases, run `/lrh-doc-organize` again for phase N+1.
5. Once all phases are complete, the audit artifact can be considered consumed.
   Consider archiving it (move to `project/audits/docs/archive/`) to signal
   that the reorganization is complete.
