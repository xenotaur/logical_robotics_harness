---
execution_id: 2026_08_22_21_39_29_WI_SESSION_ARCHIVE_SYNC_SCHEDULED_CLOSEOUT_SYNC
prompt_id: PROMPT(WI-SESSION-ARCHIVE-SYNC-SCHEDULED-CLOSEOUT-SYNC:WI_SESSION_ARCHIVE_SYNC_SCHEDULED_CLOSEOUT_SYNC)[2026-08-22T21:13:20+00:00]
work_item: WI-SESSION-ARCHIVE-SYNC-SCHEDULED-CLOSEOUT-SYNC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/612
commit: 2711d2997ccf284c5d51fbe021e5baabdace6d48
created_at: 2026-08-22T21:39:29+00:00
agent: codex_app
instruction_source: project/work_items/proposed/WI-SESSION-ARCHIVE-SYNC-SCHEDULED-CLOSEOUT-SYNC.md
session_transcript: codex-app:019fc43f-e2d9-7503-88cb-9d9a8136c111
---

# Summary

Implemented Stage 4 of `WS-SESSION-ARCHIVE-SYNC`: closeout-triggered session
archive sync plus a documented weekly scheduled sync path.

# Result

- Added `lrh sessions closeout-sync`, a human-visible wrapper around the
  existing archive reconciler that prints a closeout heading/completion line,
  preserves `--dry-run`, and reports local sync errors without printing raw
  transcript bodies.
- Added `lrh sessions schedule`, which renders or writes an inspectable weekly
  launchd plist for `lrh sessions sync`. The generated job is explicit and
  human-controlled: LRH does not install, load, unload, or hide the job.
- Updated `docs/reference/cli/sessions.md` with closeout-sync and schedule
  reference docs, including setup, inspection, disable, and follow-up
  `lrh sessions report` guidance.
- Updated closeout and implementation skill instructions across source,
  `.claude`, and `.agents` targets so closeout runs the session archive sync
  path after confirmed control-plane actions and before validation.
- Added focused CLI tests for closeout-sync wrapping and launchd plist
  rendering/writing.

Prior-art check:

- Duplication: repository search found existing Stage 2/3 session archive
  commands and documentation, plus explicit statements that scheduled or
  closeout-triggered sync was not implemented yet. No duplicate Stage 4
  implementation was found.
- Demand: `project/work_items/proposed/WI-SESSION-ARCHIVE-SYNC-SCHEDULED-CLOSEOUT-SYNC.md`
  depends on `WI-SESSION-ARCHIVE-SYNC-REPORT`; its readiness check reported
  `prompt_ready: yes`.

Pre-push self-review:

- Ran a diff-mode `/lrh-self-review` substitute review. It found one P2 docs
  issue: the launchd examples used a basename-derived label while the generated
  default label is project-slug-derived. The invoking session independently
  reverified the finding, fixed the docs by passing an explicit
  `LRH_SESSIONS_LABEL`, and recorded the pass in
  `project/executions/AD_HOC/2026_08_22_21_38_13_WI_SESSION_ARCHIVE_SYNC_SCHEDULED_CLOSEOUT_SYNC_SELFREVIEW.md`.

# Validation

```bash
PATH=/Users/centaur/anaconda3/bin:$PATH scripts/version tools
PATH=/Users/centaur/anaconda3/bin:$PATH scripts/format --check --diff
PATH=/Users/centaur/anaconda3/bin:$PATH scripts/lint
PATH=/Users/centaur/anaconda3/bin:$PATH PYTHONPATH=src scripts/test
PATH=/Users/centaur/anaconda3/bin:$PATH PYTHONPATH=src lrh validate
PATH=/Users/centaur/anaconda3/bin:$PATH PYTHONPATH=src lrh skills check --target claude --local
PATH=/Users/centaur/anaconda3/bin:$PATH PYTHONPATH=src lrh skills status --target codex --local
PATH=/Users/centaur/anaconda3/bin:$PATH PYTHONPATH=src python -m unittest tests.cli_tests.sessions_test
git diff --check origin/main
```

The full test suite passed when run with escalation for loopback server tests.
An initial non-escalated run failed only in `serve` tests with
`PermissionError: [Errno 1] Operation not permitted` while binding loopback
sockets. An initial run without `PYTHONPATH=src` also revealed the local
installed `lrh` console script was importing a stale checkout outside this
worktree, so branch validation used `PYTHONPATH=src`.

Manual dogfood checks:

```bash
PATH=/Users/centaur/anaconda3/bin:$PATH PYTHONPATH=src lrh sessions closeout-sync --project-root . --claude-projects-root /private/tmp/lrh-no-such-claude-projects --archive-root /private/tmp/lrh-session-archive-dogfood --dry-run
PATH=/Users/centaur/anaconda3/bin:$PATH PYTHONPATH=src lrh sessions schedule --project-root . --lrh-command /Users/centaur/anaconda3/bin/lrh --archive-root /Users/centaur/Workspace/Promptspace/SessionArchive --weekday 1 --hour 9 --minute 0
```

`closeout-sync --dry-run` printed a visible start/completion path and no raw
transcript bodies. `schedule` emitted an inspectable plist with the expected
command, calendar interval, log paths, and working directory.

# Follow-up

The optional `SessionEnd` hook remains deferred by design; weekly sync and
closeout-triggered sync provide the retention guarantee for this stage.
