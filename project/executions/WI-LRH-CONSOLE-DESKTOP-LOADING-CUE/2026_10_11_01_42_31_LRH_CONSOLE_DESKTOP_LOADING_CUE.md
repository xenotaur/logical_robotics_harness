---
execution_id: 2026_10_11_01_42_31_LRH_CONSOLE_DESKTOP_LOADING_CUE
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-LOADING-CUE:LRH_CONSOLE_DESKTOP_LOADING_CUE)[2026-10-11T00:41:17+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-LOADING-CUE
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/821
commit:
created_at: 2026-10-11T01:42:31+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/821
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

`/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD` resolved to `WI-LRH-CONSOLE-DESKTOP-LOADING-CUE`, the first
`proposed` item in the workstream's order on `origin/main`:

- its dependency (PAGE-SPEED) was resolved;
- readiness was `prompt_ready: yes`;
- there was no prior record;
- no open PR overlaps it.

The owner approved the plan at the chain gate.

# Result

- **Diagnosis:**
  - The shell's `on_navigation` allows backend pages and never re-issues them, so the first
    hypothesis is ruled out.
  - wry 0.57 on macOS fires `PageLoadEvent::Started` only at `didCommitNavigation` (when the
    response arrives) and has no failed-load hook. Page-load events alone therefore cannot cover
    the server's work.
  - Whether WebKit stops drawing the old page during a provisional load, which would explain the
    missing page pill, is to be confirmed in the owner's check.
- **Cue:**
  - It starts from the navigation handler. After 300 ms the title becomes "LRH Console —
    Loading…".
  - It clears on `Finished`, on download, on the next navigation, or after 20 s.
  - Every check-and-set runs on the main thread, and giving up uses an atomic `end_if(token)`.
  - In-page jumps compare against the webview's live URL.
  - There are no capabilities and no injected script.
- **Pre-push cold review:**
  - It found 5 issues, all fixed in `ddc786e8`:
    - a race that could leave the cue stuck;
    - a give-up step that was not atomic;
    - a fragment check against a stale URL, which caught replaceState card selections;
    - a 60 s hold on a failed load, now 20 s;
    - idle timer threads, which now poll and exit early.
  - Accepted: a late `Finished` from an earlier load can hide a newer cue early. It fails safe.

# Validation

- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`, and `scripts/test --desktop`
  pass.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- An owner check in the branch build: the title cue on a slow first visit, a sidebar click, and
  View menu items, and whether the page itself dims (diagnosis evidence).
