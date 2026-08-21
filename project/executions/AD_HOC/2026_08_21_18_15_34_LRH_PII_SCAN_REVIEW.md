---
execution_id: 2026_08_21_18_15_34_LRH_PII_SCAN_REVIEW
prompt_id: PROMPT(AD_HOC:LRH_PII_SCAN_REVIEW)[2026-08-21T18:10:29+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_21_17_55_09_LRH_PII_SCAN
pr: https://github.com/xenotaur/logical_robotics_harness/pull/591
commit: 5318da98
created_at: 2026-08-21T18:15:34+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/591
session_transcript: "claude-app:cf93c405-ed0f-409d-946f-7451a1cb2f7c"
---

# Summary

Addressed four open review comments from `chatgpt-codex-connector` on
PR #591 (`PROP-LRH-PII-SCAN`), all P1, via `/lrh-land`'s inlined
`/lrh-review-response` protocol.

# Result

Triaged four comments:

1. **Layer 2 never scans ordinary files** (discussion_r3832504971) —
   valid design gap. Amended Decision 2: `.lrh-pii.toml` gains an opt-in
   `content_scan_scope` setting (`"flagged"` default, `"all-text"`
   opt-in), preserving the deliberate default (avoids the CODEOWNERS-email
   false-positive case) while closing the coverage gap for repos willing
   to trade precision for recall.
2. **Content fetch only at the add commit** (discussion_r3832504974) —
   valid gap. Amended Decision 3: content-layer fetching now enumerates
   every commit touching a Layer-1-flagged path, not only its `--diff-filter=A`
   add commit, so a later modification's sensitive content is inspected.
3. **Allowlist fingerprint has no content identity** (discussion_r3832504992)
   — valid gap. Amended Decision 6: fingerprint becomes
   `sha256(path + rule_id + content_digest)`; Decision 7's output schema
   gains a `content_digest` field (git blob SHA for Layer 1, hash of the
   matched substring for Layer 2) to support it. `first_seen_commit`
   renamed to `commit` since a path can now surface multiple
   per-commit findings.
4. **Missing execution record** (discussion_r3832504998) — presence check
   failed (already resolved): the comment was posted against commit
   `15b33583` (proposal + doc only); the execution record was added in
   the very next commit, `83bc229a`, under its correctly self-stamped
   filename (`project/executions/AD_HOC/2026_08_21_17_55_09_LRH_PII_SCAN.md`)
   rather than the prompt-mint timestamp mentioned in chat. No further
   action needed.

Pushed as commit `5318da98` to the open PR branch.

# Validation

- `lrh validate` — 0 errors, 0 warnings.
- No Python files changed (proposal markdown only) — `scripts/format`,
  `scripts/lint`, `scripts/test` not applicable to this change; ruff
  0.15.12 / black 26.3.1 / Python 3.11.8 confirmed via `scripts/version tools`
  for completeness.
- Confirmed PR/branch/SHA identity against `gh pr view` before making any
  change.

# Follow-up

- Run `/lrh-confirm-fixes` against PR #591 to verify these fixes against
  the current diff and resolve the review threads.
- The three amended decisions introduce new implementation surface
  (`content_scan_scope` config, per-commit content enumeration,
  content-bound allowlist fingerprint) that the eventual implementing
  work items (listed in the proposal's Implementation Plan) should
  account for — not a new follow-up item on its own, since those work
  items don't exist yet by this session's own deliberate design.
