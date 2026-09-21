---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT
title: Make /lrh-export-claude default to the current session and accept grown-source verification
type: deliverable
status: proposed
owner: null
contributors: []
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-claude-conversation-exporter/00_proposal.md
depends_on:
  - WI-INSPECT-EXPORT-APPEND-ONLY-SOURCE-VERIFY
  - WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER
blocked_by: []
expected_actions:
  - edit_file
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - change_codex_export_skill
  - change_antigravity_export_skill
acceptance:
  - "With no discovery flag, /lrh-export-claude exports the current session and does not ask which discovery flag to use"
  - "A user-typed /lrh-export-claude counts as an explicit request: the skill states the resolved session and destination but does not wait for confirmation; a model-initiated invocation still requires an explicit confirmation before writing"
  - "A bare user-typed /lrh-export-claude asks no questions: it resolves the current session, writes to the default durable archive path (<archive_root>/claude/exports/<YYYY>/<MM>/<session-id>.md), and states both as information; --out remains an optional override and is never prompted for"
  - "Step 1 resolves the session and transcript path with the read-only current-claude-session-id resolver, without invoking the exporting command and without writing any file, so the model-initiated confirmation gate still precedes every write; Step 5 takes its --source path from the Source transcript line the Step 4 export prints"
  - "Step 5 treats Source hash match and match_source_grew as verified, reports how many bytes the source grew, and treats mismatch as a failed verification"
  - "The skill states that a live-session export is a snapshot up to the moment of export"
  - "The three rendered installs match the source skill and no unrelated installed skill was modified"
  - "The updated skill was run end to end against the live session that implements this change, and the metadata-only result is recorded in the execution record"
  - "lrh validate reports 0 errors and introduces no new warnings"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/lrh-export-claude/SKILL.md
  - .claude/skills/lrh-export-claude/SKILL.md
  - .agents/skills/lrh-export-claude/SKILL.md
  - .gemini/plugins/lrh/skills/lrh-export-claude/SKILL.md
  - CLAUDE.md
---

# WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT: Make /lrh-export-claude default to the current session and accept grown-source verification

## Summary

Update the `/lrh-export-claude` skill so that exporting the current session is the
default and needs no flag, a user-typed invocation is treated as the explicit request it
is, and verification works for a session that is still being written. This item is the
skill layer of a three-part fix and depends on the two infrastructure items.

## Problem / Context

The skill was dogfooded for the first time only after all three tranches had merged.
Findings that belong to the skill layer:

- **A bare invocation forces a question.** With no argument the skill must ask which of
  `--transcript-path`, `--session-id`, or `--latest` to use, because Claude Code sessions
  have no ambient default. The Codex skill defaults to `CODEX_THREAD_ID`. The normal use is
  exporting the session you are in, so that should be the default.
- **A bare invocation also prompts about the destination.** In a later observed run the
  skill asked which discovery flag to use and also invited the user to supply an `--out`
  path, while stressing that the default archive is permanent. The default destination is
  already the expected one, the standard archive path with datestamped directories
  (`<archive_root>/claude/exports/<YYYY>/<MM>/<session-id>.md`), so nothing should be asked
  about it on a typed invocation.
- **The confirm gate does not distinguish who invoked the skill.** The gate exists to catch
  auto-invocation, since the archive write is durable. A user who types `/lrh-export-claude`
  has made an explicit request by construction. Decision recorded 2026-09-20: a typed
  invocation counts as explicit; the wait-for-confirmation stays for model-initiated
  invocation.
- **Step 1 duplicates the exporter's resolution rules in prose.** The replacement must not be
  the exporter itself: `export-claude-session` prints its `Source transcript:` line only after
  it has written the artifact, so calling it in Step 1 would create the durable file before a
  model-initiated run reaches the confirmation gate, and Step 4 would then export a second
  time. Step 1 must use the read-only resolver (`current-claude-session-id`, which reports the
  transcript path) instead. Step 5 assumes
  `Source hash: match`, which cannot hold for a live session (see
  `WI-INSPECT-EXPORT-APPEND-ONLY-SOURCE-VERIFY`). The dogfood run needed a manual snapshot
  workaround at the wrong layer to get a verified export.

Open design point to settle during implementation: how the skill reliably distinguishes a
user-typed slash invocation from a model-initiated one. In the observed dogfood run the
user-typed invocation arrived as `<command-message>` and `<command-name>` tags in the
conversation, whereas a model-initiated invocation appears as a tool launch. If that signal
proves unreliable, fall back to a single yes/no confirmation instead of skipping it, rather
than guessing.

Rendered installs live in three places and `lrh skills install --force` is target-wide: it
overwrites every locally modified skill for that target, not just this one. Use `--dry-run`
first, once per target, and check `git status` afterwards.

### Duplication search
- In-repo: `src/lrh/skills/lrh-export-claude/SKILL.md` already exists and is what this item modifies. `lrh-codex-export` is the precedent for defaulting to an ambient session id; its confirm gate wording is the one being refined here for the Claude skill only.
- Sibling repos: none identified.
- External libraries: not applicable.
- Recommendation: Proceed.

### Demand search
- Work items: the two infrastructure items in this batch are the prerequisites; nothing else open touches this skill.
- Proposals: `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` Decisions 6 and 7 set the durable-by-default archive and the confirm gate; this item keeps the gate for model-initiated runs.
- Backlog: no matching entry.
- Recommendation: No action; this item is the tracking artifact.

## Scope

- Edit `src/lrh/skills/lrh-export-claude/SKILL.md` and re-render its three installed copies.
- Update the `/lrh-export-claude` line in `CLAUDE.md` if the description changes.

## Required Changes

1. With no discovery flag, export the current session by way of the resolver and `--current` from `WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER`. Ask only if the resolver reports the session cannot be resolved.
2. Refine Step 3: a user-typed invocation states the resolved session and destination as information and proceeds without waiting; a model-initiated invocation waits for explicit confirmation as today. Update `when_to_use` to match. Resolve the open design point above, and document how the two cases are told apart.
3. A bare user-typed invocation must ask no questions: no discovery-flag question and no `--out` prompt. State the resolved session and the default archive path as information. The note that the archive is durable and not self-cleaning appears once in that statement (and in the confirmation text for model-initiated runs), not as a question. `--out` stays an optional override.
4. Replace the Step 1 prose glob rules with a call to the read-only `lrh conversation current-claude-session-id` resolver, taking the transcript path from its output. Do not call `export-claude-session` in Step 1: it writes the artifact before the confirmation gate. Use the `Source transcript:` line printed by the Step 4 export only for the Step 5 `--source` argument.
5. Update Step 5: `Source hash: match` and `match_source_grew` both count as verified, and the report notes how many bytes the source grew; `mismatch` is a failed verification.
6. Add a short note that a live-session export is a snapshot up to the moment of export and excludes anything written afterwards.
7. Re-render the three installs (`.claude/skills`, `.agents/skills`, `.gemini/plugins/lrh/skills`) for this skill only. Run one explicit dry-run per target first (`lrh skills install --dry-run --local --target claude`, then `--target codex`, then `--target antigravity`) and confirm each names no unrelated skill before any `--force`, which must also be run once per explicit target; verify with `git status` that only this skill's files changed.
8. Run the updated skill end to end against the live session that implements this change. Record the metadata-only result (artifact path, source id, hash status, sensitivity, warning count) in the execution record, without transcript content.

## Non-Goals

- Does not change the Codex or Antigravity skills. Applying the same typed-invocation rule to the Codex skill is a possible follow-up.
- Does not change the exporter CLI, the manifest, or the inspector.
- Does not add a Claude session resolver to `/lrh-closeout`.

## Acceptance Criteria

- A bare `/lrh-export-claude` exports the current session without asking which flag to use.
- A bare typed invocation asks no questions and writes to the default archive path, stating it.
- A user-typed invocation is treated as explicit; a model-initiated invocation still requires confirmation.
- Step 1 uses the read-only resolver and never invokes the exporter before the confirmation gate, and Step 5 accepts `match` and `match_source_grew`.
- The live-session snapshot note is present.
- The three rendered installs match the source and no unrelated installed skill changed.
- The end-to-end run on a live session is recorded in the execution record.
- `lrh validate` reports 0 errors and introduces no new warnings.

## Validation

- `lrh skills check --target claude --local --source current-repo`
- `lrh skills check --target codex --local --source current-repo`
- `lrh skills check --target antigravity --local --source current-repo`
- `PYTHONPATH=src scripts/test`
- `scripts/lint`
- `scripts/format --check --diff`
- `lrh validate`
