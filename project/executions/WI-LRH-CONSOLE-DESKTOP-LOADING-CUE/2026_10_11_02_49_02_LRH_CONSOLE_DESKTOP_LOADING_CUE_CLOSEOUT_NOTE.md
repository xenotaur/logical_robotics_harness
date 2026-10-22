---
execution_id: 2026_10_11_02_49_02_LRH_CONSOLE_DESKTOP_LOADING_CUE_CLOSEOUT_NOTE
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-LOADING-CUE:LRH_CONSOLE_DESKTOP_LOADING_CUE_CLOSEOUT_NOTE)[2026-10-11T02:49:02+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-LOADING-CUE
status: landed
rerun_of: 2026_10_11_01_42_31_LRH_CONSOLE_DESKTOP_LOADING_CUE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/821
commit: 781e8871bedee22bef67617c3d1c65735ee3c51d
created_at: 2026-10-11T02:49:02+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/821
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This is the closeout note for PR #821, which implemented `WI-LRH-CONSOLE-DESKTOP-LOADING-CUE` through
`/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD`. The primary record's body is immutable, so the chain
note lives here instead.

# Result

CHAIN-NOTE: `cycles=1; stops=0; gates=[execute-chain, land-chain, owner-check, review-response, confirm-fixes-waiver, merge]; friction=diagnosis-partly-unreproducible; self_review_rounds=2; bot_rounds=1; note="This added a native title cue: LRH Console shows Loading after 300 ms of a navigation and resets on Finished, on download, on the next navigation, or after 20 s. It starts from the navigation handler because wry on macOS fires Started only at didCommitNavigation, after the server work. All cue checks run on the main thread, give-up uses an atomic end_if, in-page jumps are checked against the live URL, and Reload is marked. The shell re-issuing navigations was ruled out as the cause of the missing page pill. Restart is confirmed in the app, the View menu is explained from code, and the sidebar case was unreproducible after warm-up; the owner waived it (option A). The pre-push review found 5 issues, all fixed. Of the bot threads, 1 Copilot was fixed, 1 Copilot owner-check was recorded, and 1 Codex fragment-removal was declined per HTML same-document rules. Confirm-fixes added a Reload-with-fragment fix and honest acceptance wording. The owner checked it in the app: the title cue works and never sticks. CI went 7/7 green on every head, and the merge was SHA-locked."`

PR #821 merged as `781e8871bedee22bef67617c3d1c65735ee3c51d`, using
`--match-head-commit 8441f9e9`, after authorization in this session. Three records landed with
that commit, through `lrh prompt update-execution`: the primary, `_REVIEW`, and `_CONFIRM`.

`WI-LRH-CONSOLE-DESKTOP-LOADING-CUE` moved to `resolved/`. Its resolution note records acceptance
criterion 1 as partly met, under the owner's waiver. `WS-LRH-CONSOLE-LOCAL-DOGFOOD` stays active.

# Validation

- `lrh validate` was run after these closeout edits. See the closeout commit.

# Follow-up

- Next ready in the workstream: `WI-LRH-CONSOLE-DESKTOP-WINDOW-STATE`, then
  `WI-LRH-CONSOLE-L1-DOGFOOD`, `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT`, `WI-LRH-CONSOLE-STATUS-SHAPES`,
  and `WI-LRH-PROJECT-UPDATE-SKILL`.
- Open question, waived: whether WebKit stops painting the old page during a provisional load.
