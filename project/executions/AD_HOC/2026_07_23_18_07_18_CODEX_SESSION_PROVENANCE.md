---
execution_id: 2026_07_23_18_07_18_CODEX_SESSION_PROVENANCE
prompt_id: PROMPT(AD_HOC:CODEX_SESSION_PROVENANCE)[2026-07-23T18:02:03-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/411
commit: 4908ca5
created_at: 2026-07-23T18:07:18-04:00
agent: claude_app
instruction_source: ad_hoc conversation — multi-agent session provenance design discussion following PRs #409 and #410
session_transcript: claude-app:4c3d03d6-6ebd-418a-86b2-6f4041feb9db
---

# Summary

Record the backend-agnostic session pointer grammar as a decision, align the
schema documentation with it, and retire the last four Codex-era execution
records that had no correct value to hold.

# Result

**Investigation.** Three records (PRs #260/#264/#268) had held
`session_transcript: pending` since May. Evidence from the user's prompt
archive established they were Codex Cloud executions, not Claude sessions:
`lrh_readiness_prompt_package.zip` contains four prompt files whose first
lines are those records' exact prompt IDs, each titled "Codex Cloud Prompt",
and every May-era merge branch is named `codex/…`. `pending` was therefore
unresolvable by construction — it described complete records as unfinished.

**Decision.** Added a 2026-07-23 decision-log entry, "Backend-Agnostic
Session Pointer Grammar": `session_transcript` takes a scheme-prefixed scalar
`<backend>:<id>`; `pending` and `none` are distinct sentinels (to-do vs.
terminal); `instruction_source` gains `promptspace:` for out-of-repo
artifacts; the field is scalar-or-sequence so the deferred multi-backend case
(Risk 3 in `PROP-LRH-EXECUTION-SESSIONS`) needs no record rewrite later; the
`lrh://` conversations ledger is the stated endpoint. Chosen because all 121
existing values already conform — a documentation fix rather than a
migration. Alternatives (structured object, sequence-only, ledger-URI-now)
recorded with trade-offs.

**Documentation.** `project/executions/README.md` had never documented
`agent`, `instruction_source`, or `session_transcript` despite 121 records
carrying them; added all three plus the value table.
`execution-session-reference.md` (both mirrors) generalized from Claude-only,
with an explicit warning against writing `pending` for backends that have no
retrievable session. Added a missing `### Status: Accepted` to the
transcripts entry landed in #409.

**Backfill.** Four records updated to `agent: codex_cloud`,
`instruction_source: promptspace:…`, `session_transcript: none`. The fourth
(`2026_05_18_22_47_49_DOCUMENT_WORKFLOW`) was additionally an unfinished
closeout — `in_progress` with empty `pr:`/`commit:` while its work item sat
in `resolved/`. The WI's `resolution:` named PR #354, but `git show`
confirmed #354 is separate later work (merged June 30, own execution
records); PR #275 (merged 2026-05-18, `7ff7ee3`) is the PR that introduced
this record file and matches its Summary. Transitioned via
`lrh prompt update-execution`. Its body's stale "populate pr and commit"
follow-up was left intact per the README's rule against rewriting historical
record bodies.

Zero `session_transcript: pending` records now remain repo-wide; `agent`
distribution is 118 `claude_app` / 4 `codex_cloud`, the first non-Claude
records in the repository.

# Validation

- `scripts/format --check --diff` — clean (179 files unchanged)
- `scripts/lint` — clean
- `scripts/test` — 796 tests, OK
- `lrh validate` — 0 errors, 0 warnings
- `diff -r src/lrh/skills .claude/skills` — no new drift
- Post-edit greps: 0 `^session_transcript: pending` repo-wide

# Follow-up

- No `lrh validate` rule enforces the new grammar; `PROP-LRH-EXECUTION-SESSIONS`
  Stage 2 specifies one (warn on absolute paths) and it remains unimplemented.
- ChatGPT-era sessions in the prompt archive carry no share links, so
  recovering them requires manual title-matching; Codex Cloud session
  recoverability is unverified.
- `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP` remains `not_started`; this
  decision is designed to converge on it without further record migration.
