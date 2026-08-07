---
execution_id: 2026_08_07_16_23_52_WI_SESSION_ARCHIVE_SYNC_RECONCILER_IMPL
prompt_id: PROMPT(WI-SESSION-ARCHIVE-SYNC-RECONCILER:WI_SESSION_ARCHIVE_SYNC_RECONCILER_IMPL)[2026-08-07T16:22:32+00:00]
work_item: WI-SESSION-ARCHIVE-SYNC-RECONCILER
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/509
commit: e36753013e9e6ae1c2800dd8ba0b8757a03c4f6c
created_at: 2026-08-07T16:23:52+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SESSION-ARCHIVE-SYNC-RECONCILER.md
session_transcript: claude-app:89d77fcc-6765-497c-a356-992be4e39b3f
---

# Summary

Implemented `WI-SESSION-ARCHIVE-SYNC-RECONCILER` (Stage 2 of
`PROP-LRH-SESSION-ARCHIVE-SYNC`): `lrh sessions sync`, `discover`, and
`link` — the archive reconciler closing the retroactive half of the
identity-mapping gap Stage 1 left open.

# Result

- New module `src/lrh/sessions_workflow.py` implements `lrh sessions
  sync` (raw-JSONL mirror with a hard never-shrink size floor; optional
  `/export` zip metadata harvest, identity fields only; line-level
  `sessionId` alias reconciliation for already-known hosts),
  `lrh sessions discover` (project-scoped transcript listing,
  cross-referenced against the index), and `lrh sessions link` (child-id
  promotion to a host-keyed `session_transcript` pointer, refusing to
  guess on unknown/ambiguous ids). Kept as a separate module from
  `prompt_workflow_sessions.py` to avoid a circular import.
- Core logic (mirroring, export-metadata harvest, alias collection/
  reconciliation, discover/link lookups) added to
  `src/lrh/prompt_workflow_sessions.py`, reusing Stage 1's
  `record_session_observation` merge primitive rather than duplicating
  index-write logic. `lrh sessions` wired as a new top-level `add_help=False`
  passthrough command in `src/lrh/cli/main.py`, matching the `prompt`/
  `match`/`search` precedent.
- Updated both skill mirrors' reference docs
  (`execution-session-reference.md`, `closeout-workflow.md`) to describe
  the new commands; `diff -r` clean on both `lrh-implement` and
  `lrh-closeout`.
- Added a `project/design/backlog.md` entry recording the deliberate
  choice not to default `--exports-dir` to any location.
- **Self-review before this PR opened** (diff-mode, per this repo's own
  dogfooding practice): a fresh cold-context sub-agent found two real
  HIGH-severity bugs, both independently re-verified by direct
  reproduction before fixing:
  1. `write_session_transcript_field` silently no-op'd — reported success
     and wrote nothing — on a record with no pre-existing
     `session_transcript:` field, because it omitted the
     `insert_after="commit"` anchor `update-execution` uses for the same
     field. Fixed with the anchor plus explicit post-write verification
     (raises `SessionTranscriptWriteError` if the field still isn't
     present, rather than silently succeeding).
  2. `mirror_transcript`'s never-shrink invariant could be defeated by a
     source that was smaller but had a newer mtime (e.g. a rewrite or
     truncation) — the size/mtime AND-condition let a newer-but-smaller
     source overwrite a larger archived copy. Fixed to a hard floor on
     size, independent of mtime.
  A third finding (child-id alias collection existed but was never wired
  into `sync`, so the PR #435 case wasn't actually closed end-to-end
  despite passing its own unit test) led to the new
  `reconcile_child_id_aliases` function and its wiring into `_run_sync` —
  verified against the exact PR #435 scenario (a child id appearing in no
  filename anywhere) both in a unit test and a live CLI smoke test.
  Two low-severity doc-accuracy findings were also fixed (overstated glob
  depth claim; missing `--project-path` flag documentation).
- **Process note:** `/lrh-implement`'s own Step 3 (mint the prompt ID)
  was not run before implementation began — it was minted retroactively,
  just before this record's own creation, rather than before Step 4's
  plan-confirm gate as the skill specifies. The implementation plan
  itself *was* shown and explicitly confirmed at `/lrh-work-item`'s own
  gate when this WI was filed (full Required Changes / Acceptance
  Criteria), and the user's instruction for this run ("go ahead, you can
  `/lrh-execute` it to landing") was broad authorization — but the
  mint-before-Step-4 ordering itself was not followed as specified.
  Flagging for transparency rather than treating it as compliant.
- **Self-review after this PR opened** (PR-mode, cold-context sub-agent,
  triggered by ~2 minutes of GitHub-bot silence per this repo's
  bot-is-expensive guidance): confirmed all headline claims and all gates
  green, no `forbidden_actions` violated, and found 7 new findings.
  1. **MEDIUM-HIGH, fixed:** `project_slug_for_path`'s regex replaced `/`
     and `_`, but Claude Code's real rule replaces `/` and `.` — `_` is
     preserved. Verified conclusively against every real directory under
     `~/.claude/projects/` on this machine (a `replication_vector` repo
     keeps its underscore; a `.claude/worktrees/...` segment becomes
     `-claude-worktrees-...`). This broke `discover`/`link` resolution on
     every path containing a dot, which includes every
     `.claude/worktrees/` agent worktree — this project's own dominant
     working pattern — so fixed before merge rather than deferring as a
     fast follow.
  2. MEDIUM, not fixed, deferred (see Follow-up): sequence-form
     `session_transcript` YAML lists can be corrupted by
     `_replace_or_insert_frontmatter_field`'s line-based regex when
     `lrh sessions link` writes to them — a pre-existing bug in a helper
     shared with `update-execution`, newly reachable via this PR.
  3. LOW, not fixed, deferred: `write_session_transcript_field`'s
     post-write success guard checks the whole file text rather than
     scoping to the frontmatter block.
  4. LOW, not fixed, deferred: `--dry-run` in `lrh sessions sync` doesn't
     report alias-reconciliation activity (the `continue` happens before
     the reconcile call).
  5. LOW/perf, not fixed, deferred: `_run_sync` reconciles every
     transcript on every run with no batching or short-circuiting.
  6. NIT: already effectively addressed by the first self-review's
     glob-depth doc fix.
  7. NIT: already acknowledged above (the `prNumber`-without-`prs[]` gap).
  Sub-agent's verdict was "safe to merge as-is, with finding 1 filed as a
  fast follow"; judgment call made here to fix finding 1 immediately
  instead, given its real-world impact on this project's own usage
  pattern, and to defer findings 2-5 to Follow-up as genuinely
  lower-severity and non-merge-blocking.

# Validation

- `scripts/version tools`, `scripts/format --check --diff`, `scripts/lint`:
  clean (after resyncing the local toolchain via `scripts/develop`,
  needed repeatedly this session due to environment drift).
- `scripts/test`: 1051 tests passed (49 new: 42 in
  `prompt_workflow_sessions_test.py`, 7 in `sessions_test.py`; plus 3 more
  in `prompt_workflow_test.py` for the `link` fix).
- `lrh validate`: 0 errors, 0 warnings.
- `diff -r src/lrh/skills/lrh-implement/ .claude/skills/lrh-implement/`
  and the `lrh-closeout` equivalent: both exit 0.
- Manual end-to-end smoke tests: mirrored and re-mirrored a growing
  transcript (append-safety verified live); harvested a real
  `session-export-*.zip` from disk (host/child/branch/title/both PR URLs
  extracted correctly, only identity fields persisted); `link` promoted a
  harvested child id to its host pointer and failed cleanly on an unknown
  one; reproduced PR #435's exact alias case (`f1e9c968.jsonl` containing
  in-file `aff3efd3`) end-to-end via the CLI after the wiring fix.

# Follow-up

- Stage 3 (index enrichment + `lrh sessions report`) and Stage 4 (weekly
  scheduled sync + `/lrh-closeout`-triggered sync) remain unfiled.
- `project/design/backlog.md`'s new entry: `lrh sessions sync` has no
  default `/export` zip location, deferred pending the archive-root
  open question.
- Low-severity, not fixed (out of the WI's explicit field-list scope):
  an `/export` `metadata.json` with `prNumber` but an empty/absent
  `prs[]` records no PR at all, since the WI's Required Changes #2
  explicitly lists only `prs[]` (not `prUrl`) as the field to extract.
- From the second self-review round, deferred as non-merge-blocking:
  - `_replace_or_insert_frontmatter_field`'s line-based regex can
    corrupt a sequence-form `session_transcript:` YAML list when
    `lrh sessions link` writes to it (pre-existing shared-helper bug,
    newly reachable here).
  - `write_session_transcript_field`'s post-write success guard checks
    the whole file text, not just the frontmatter block.
  - `lrh sessions sync --dry-run` doesn't report alias-reconciliation
    activity, since the dry-run `continue` happens before the reconcile
    call.
  - `_run_sync` reconciles every transcript on every run with no
    batching/short-circuiting (reads full JSONLs and reloads the index
    repeatedly).
