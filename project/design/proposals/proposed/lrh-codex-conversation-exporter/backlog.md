---
kind: codex_skill_adaptation_backlog
status: active
created_on: 2026-08-02
updated_on: 2026-08-02
parent: PROP-LRH-CODEX-CONVERSATION-EXPORTER
---

# Codex Skill Adaptation Backlog

This backlog records Codex-specific issues encountered while creating
`PROP-LRH-CODEX-CONVERSATION-EXPORTER` from the authoritative LRH skill source.

## Missing `.agents/skills` installation path

Codex did not have an `~/.agents/skills/` or project `.agents/skills/`
directory available in this worktree. The session used the authoritative repo
copy at `src/lrh/skills/lrh-proposal/SKILL.md` directly.

Impact: Codex can follow the skill manually, but slash-command discovery and
installation are not yet first-class.

## Claude-specific execution-record defaults

`lrh-proposal`'s execution-record reference still shows:

```yaml
agent: claude_app
session_transcript: pending
```

and final reporting text assumes the transcript will later become
`claude-app:<host-uuid-stem>`.

Impact: Codex sessions need a Codex-specific convention, likely
`agent: codex_app` or another open-ended value, and a `codex-app:<id>` /
`pending` / `none` transcript resolution path.

## Claude-specific skill availability checks

`lrh-proposal` Step 11 checks whether `/lrh-workstream` is listed in
`CLAUDE.md ## Skills`.

Impact: Codex needs an equivalent target-aware skill availability check that
can inspect Codex-discoverable skills or fall back to authoritative repo skill
sources.

## Network assumptions in idempotence checks

The proposal skill's cross-PR idempotence check assumes GitHub network access is
available. In this Codex session, `gh pr list` failed under the restricted
sandbox and required escalation.

Impact: Codex-friendly skills should explicitly describe sandbox/network
escalation behavior and graceful local-only fallback semantics.

## Environment preflight surfaced missing Pyright

`scripts/version tools` reported `Pyright not installed`.

Impact: This is likely environment setup/cache state rather than a proposal
design issue, but Codex-facing workflows should preserve the repo guidance that
tool-version mismatches are setup issues to reconcile before validation-focused
debugging.
