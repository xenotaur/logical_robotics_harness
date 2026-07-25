---
execution_id: 2026_07_25_01_33_44_REFRESH_EXEC_SESSIONS_SCHEMA_GRAMMAR
prompt_id: PROMPT(AD_HOC:REFRESH_EXEC_SESSIONS_SCHEMA_GRAMMAR)[2026-07-25T01:30:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/420
commit: 7a78247a9891e046e9dfd42394556c67e77949d0
created_at: 2026-07-25T01:33:44-04:00
agent: claude_app
instruction_source: ad_hoc conversation — refresh WI-EXEC-SESSIONS-SCHEMA acceptance criteria for the backend-agnostic session pointer grammar (follows PR #411)
session_transcript: claude-app:4c3d03d6-6ebd-418a-86b2-6f4041feb9db
---

# Summary

Refresh the proposed work item `WI-EXEC-SESSIONS-SCHEMA` so its acceptance
criteria track the backend-agnostic session pointer grammar adopted in
PR #411, rather than the narrower Claude-only shape it was drafted against.

# Result

Edited `project/work_items/proposed/WI-EXEC-SESSIONS-SCHEMA.md` (planning
artifact only; no validator code):

- **`session_transcript` criteria:** now accept any `<backend>:<id>` scheme
  (`claude-app:`, `codex-cloud:`, `chatgpt:`) and the sentinels `pending`
  and `none` without warning; warn on absolute paths (privacy) and on
  non-sentinel values lacking a `<scheme>:` prefix (grammar). The stale
  "suggest the `claude-app:<id>` short form" text was corrected to
  `<backend>:<id>`.
- **`agent` criteria:** dropped the hard "unknown value" warning — the field
  is open-ended (`claude_app | codex_cloud | manual | <other>`) per
  PROP-LRH-EXECUTION-SESSIONS, so any non-empty value is accepted.
- **Test matrix:** widened to each scheme, both sentinels, absolute-path and
  bare-id warnings, and `<other>` agent values.
- **Stats:** corrected the stale "163 records / 2026-06-28" figures to the
  fresh count — 138 records carry these fields (134 claude-app/claude_app,
  4 none/codex_cloud from the #411 backfill, 0 pending).

Landed via the autonomous land-open-PR chain. Review landed with 3 comments
(1 Copilot, 2 codex) → 3 fixes in one confirm-fixes pass: trailing-colon
scheme examples, `session_transcript` sequence-form coverage, and an
`instruction_source` absolute-path check. Human merge gate approved; PR #420
squash-merged as `7a78247`.

CHAIN-NOTE: cycles=1; stops=0; gates=[merge]; friction=guessed-prompt-id-timestamp-in-fixes-commit-msg-before-minting; note="records carry the correct minted ID (01:55:48); commit msg blemish left un-force-pushed"

Opened as PR #420; WI stays `proposed`.

# Validation

- `lrh validate` — 0 errors (1 pre-existing unrelated warning:
  `WS-LRH-ASSISTANTS` no actionable leaf)
- `lrh work-items validate` — no warnings attributable to this WI
- `lrh work-items readiness WI-EXEC-SESSIONS-SCHEMA` — `prompt_ready: yes`
- Residual grep for old enum warning / "163" / stale suggestion text — none

# Follow-up

- Implementing the validator (Stage 2 of PROP-LRH-EXECUTION-SESSIONS) is a
  separate work item; this only refreshes the spec.
- `depends_on: WI-EXEC-SESSIONS-DOCS` unchanged; that docs WI's README half
  already shipped in #411 while the WI itself remains proposed.
