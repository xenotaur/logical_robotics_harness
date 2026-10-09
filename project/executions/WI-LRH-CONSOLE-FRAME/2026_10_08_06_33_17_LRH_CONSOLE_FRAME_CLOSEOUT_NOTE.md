---
execution_id: 2026_10_08_06_33_17_LRH_CONSOLE_FRAME_CLOSEOUT_NOTE
prompt_id: PROMPT(WI-LRH-CONSOLE-FRAME:LRH_CONSOLE_FRAME_CLOSEOUT_NOTE)[2026-10-08T06:33:17+00:00]
work_item: WI-LRH-CONSOLE-FRAME
status: landed
rerun_of: 2026_10_08_06_02_54_LRH_CONSOLE_FRAME
pr: https://github.com/xenotaur/logical_robotics_harness/pull/792
commit: bf4f8f248e15e2319d6adce9c777c3f54db105f3
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/792"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-08T06:33:17+00:00
---


# Summary

This is the closeout note for PR #792, which implemented `WI-LRH-CONSOLE-FRAME` through
`/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD`. The primary record's body is immutable, so the chain
note lives here instead.

# Result

CHAIN-NOTE: `cycles=1; stops=0; gates=[execute-chain, land-chain, review-response, merge]; friction=owner-check-needed-build; self_review_rounds=2; bot_rounds=1; note="This added the script-free LRH Console frame to every Serve page, applied at response time: top bar, Meta-registry scope switcher with a CSS icon rail, an ?item= drawer, packaged icon, Montserrat (OFL) and Lucide (ISC) assets, an allowlisted /static, a /settings about page, and a CSP adding only same-origin images and fonts. The LRH Console gear opens native Settings with no new capability. Browser checks caught sideways scrolling and a missing viewport tag. The pre-push review caught nested main landmarks, plus six should-fixes, all applied. Copilot found one valid issue (unloadable projects dropped from the switcher), which was fixed. The owner could not check the gear without a build, so the agent built and launched this branch's app, and the check passed. CI went 7/7 green, and the merge was SHA-locked."`

PR #792 merged as `bf4f8f248e15e2319d6adce9c777c3f54db105f3`, using
`--match-head-commit a461c660`, after authorization in this session. Three records landed with
that commit, through `lrh prompt update-execution`: the primary, `_REVIEW`, and `_CONFIRM`.

`WI-LRH-CONSOLE-FRAME` moved to `resolved/` with a resolution note.
`WS-LRH-CONSOLE-LOCAL-DOGFOOD` stays active.

# Validation

- `lrh validate` was run after these closeout edits. See the closeout commit.

# Follow-up

- `WI-LRH-CONSOLE-MAP-SNAPSHOT` is next in the workstream. `WI-LRH-CONSOLE-STATUSBOARD` is now
  unblocked, but needs the owner's band-set decision first.
- A separate session is fixing the pre-existing crash in the design and workstream detail
  routes when no Meta workspace exists.
- Process note: owner checks of desktop shell changes need this branch's app built and
  launched (`apps/desktop/scripts/run bundle`, then `launch`). Offer that up front.
