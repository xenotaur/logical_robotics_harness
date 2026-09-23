---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-CLAUDE-SESSION
title: Add a metadata-only /lrh-claude-session skill and route Claude session-pointer resolution through it
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-SESSION-ARCHIVE-SYNC
related_design:
  - project/audits/2026-09-22-session-sync-export-ecosystem-audit.md
  - project/design/proposals/adopted/lrh-session-archive-sync/00_proposal.md
  - project/design/proposals/adopted/lrh-claude-conversation-exporter/00_proposal.md
  - project/work_items/resolved/WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER.md
  - project/work_items/resolved/WI-CODEX-SESSION-ID-RESOLVER.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - export_transcript_content
  - call_export_transcript_tool
  - commit_raw_transcript_data
  - change_session_transcript_schema
  - edit_gate_definition_blocks
acceptance:
  - "src/lrh/skills/lrh-claude-session/SKILL.md exists and reports `session_transcript: claude-app:<host-uuid-stem>` for the current window without reading, exporting, or printing transcript content"
  - "For the current window the skill resolves via `lrh conversation current-claude-session-id`, and falls back to reading CLAUDE_CODE_HOST_SESSION_ID directly (stripping local_) when the installed CLI lacks that subcommand"
  - "Where the session-management get_session tool is available the skill also reports title and branch; for another session it resolves via list_sessions by PR number, then branch or title, then a user pick from the list"
  - "/lrh-closeout Step 3, /lrh-land Step 3, and /lrh-implement's alias-capture step call /lrh-claude-session instead of restating the resolution order, and pass --title and --branch to record-session-alias where resolved"
  - "Claude, Codex, and Antigravity rendered targets are regenerated for every touched skill, CLAUDE.md indexes /lrh-claude-session, and lrh chain-defaults status reports stale: False"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-claude-session/SKILL.md
  - src/lrh/skills/lrh-claude-session/agents/openai.yaml
  - src/lrh/skills/lrh-closeout/SKILL.md
  - src/lrh/skills/lrh-closeout/references/closeout-workflow.md
  - src/lrh/skills/lrh-land/SKILL.md
  - src/lrh/skills/lrh-implement/SKILL.md
  - src/lrh/skills/lrh-implement/references/execution-session-reference.md
  - .claude/skills/lrh-claude-session/SKILL.md
  - .agents/skills/lrh-claude-session/SKILL.md
  - .gemini/plugins/lrh/skills/lrh-claude-session/SKILL.md
  - CLAUDE.md
  - docs/reference/cli/conversation.md
---

# WI-SKILLS-LRH-CLAUDE-SESSION: Add a metadata-only /lrh-claude-session skill

## Summary

Add a `/lrh-claude-session` skill, parallel to `/lrh-codex-session`, that
reports the Claude.app `session_transcript: claude-app:<host-uuid-stem>`
pointer plus the identity fields `record-session-alias` needs, without
exporting anything. Then make `/lrh-closeout`, `/lrh-land`, and
`/lrh-implement` call it instead of each restating the resolution steps.

## Problem / Context

The Claude desktop app (2.7032.0) no longer exposes View > Copy URL or
in-session `/export`. Those were the human ways to obtain a session's host
id. The audit
`project/audits/2026-09-22-session-sync-export-ecosystem-audit.md` records
this (findings A8 and A9, recommendation R7). A same-day doc fix already
replaced the dead Copy URL fallback, but that fix restates the resolution
order in three skills.

The command-line half already landed: `lrh conversation
current-claude-session-id` (`WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER`, PR
#698). Its Non-Goals explicitly deferred moving `/lrh-closeout` Step 3 onto
the resolver as "a natural follow-up", but that follow-up was never filed.

Separately, none of the three callers passes `--title` to
`record-session-alias`, and `/lrh-closeout` also omits `--branch`. As a
result, 0 of 30 rows in `project/sessions/index.jsonl` have a title. A
single resolver skill that also reports title and branch fixes both
problems in one place.

Two caveats for the implementer:
- Installed CLIs can lag the skills. On one audited machine, the `lrh` on
  PATH lacked `current-claude-session-id`, so the skill needs a direct
  env-var fallback.
- `/lrh-codex-session` (`WI-CODEX-SESSION-ID-RESOLVER`, PR #611) is the
  template for shape, safety rules, and rendered targets.

### Duplication search
- In-repo: Related: `src/lrh/conversations/claude_session.py` (CLI resolver,
  reused rather than duplicated); `src/lrh/skills/lrh-codex-session/`
  (template). No Claude skill wrapper exists.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: Found `WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER`
  (resolved), whose Non-Goals defer exactly this migration. No open item
  covers it.
- Proposals: None found.
- Backlog: No matching entries.
- Recommendation: No action; this item fulfils that deferred follow-up. The
  audit's proposed `WI-CLOSEOUT-SESSION-IDENTITY-TITLE-BRANCH` is subsumed
  by this item's `--title`/`--branch` pass-through.

## Scope

- Create the `/lrh-claude-session` skill (canonical plus rendered targets)
  and index it in `CLAUDE.md`.
- Route Claude host-id resolution in `/lrh-closeout` Step 3, `/lrh-land`
  Step 3, and `/lrh-implement`'s alias capture through the skill.
- Pass `--title` and `--branch` to `record-session-alias` wherever the skill
  resolved them.

## Required Changes

1. Create `src/lrh/skills/lrh-claude-session/SKILL.md`, modelled on
   `lrh-codex-session`. It should:
   - accept an optional argument: a session id or a PR number/URL;
   - **current window:** run `lrh conversation current-claude-session-id
     --format json`. If that subcommand is missing or fails, read
     `CLAUDE_CODE_HOST_SESSION_ID`/`CLAUDE_CODE_SESSION_ID` directly and
     strip `local_`;
   - **enrichment:** where the session-management `get_session` tool exists,
     call it with `"self"` and report title and branch;
   - **other session:** use `list_sessions` matched by `prNumber`, then
     branch or title, then a user pick from the listed candidates (with
     `include_archived` when needed); report no child id in this case;
   - report `Session ID`, `session_transcript: claude-app:<stem>`, title,
     branch, PR, and whether a child-id alias may be paired (current window
     only);
   - include Safety Rules mirroring `/lrh-codex-session`: no transcript
     reads, no exports, never call `export_transcript`, and never use
     JSONL-filename (child) ids as the pointer.
2. Add `src/lrh/skills/lrh-claude-session/agents/openai.yaml` matching
   `lrh-codex-session`.
3. `src/lrh/skills/lrh-closeout/SKILL.md` Step 3 (Claude.app branch) and
   `references/closeout-workflow.md` "Resolution order": replace the
   restated paths with "run `/lrh-claude-session`", keeping the confirmation
   and the path-1-only child-alias rule. Step 5: pass `--title`/`--branch`
   when resolved. Do not edit inside `<!-- GATE-DEFINITION -->` blocks.
4. `src/lrh/skills/lrh-land/SKILL.md` Step 3: point the `claude_app` bullet
   at `/lrh-claude-session`.
5. `src/lrh/skills/lrh-implement/SKILL.md` alias capture and
   `references/execution-session-reference.md`: obtain the host id, title,
   and branch from `/lrh-claude-session` and add `--title`.
6. Regenerate `.claude/skills/`, `.agents/skills/`, and
   `.gemini/plugins/lrh/skills/` for the new skill and every touched skill
   (`lrh skills install --local --target <t> --source current-repo`).
7. Add a `/lrh-claude-session` line to `CLAUDE.md`'s Skills index. Add a
   cross-reference from the `current-claude-session-id` section of
   `docs/reference/cli/conversation.md`.

## Non-Goals

- Do not change `lrh conversation current-claude-session-id` or any Python
  code. The skill wraps the existing CLI.
- Do not export, archive, or read transcripts, and do not call the
  `export_transcript` tool. `/lrh-export-claude` remains the explicit
  export path.
- Do not implement raw-JSONL identity extraction in `lrh sessions sync`
  (audit R1 source 2), skill-drift detection (R4), or scope disclosure (R5).
  Those are separate audit follow-ups.
- Do not change the `session_transcript` grammar or the
  `project/sessions/index.jsonl` schema.
- Do not edit `<!-- GATE-DEFINITION -->` blocks.

## Acceptance Criteria

- `src/lrh/skills/lrh-claude-session/SKILL.md` reports
  `session_transcript: claude-app:<host-uuid-stem>` for the current window
  and never reads, exports, or prints transcript content.
- Current-window resolution uses `lrh conversation
  current-claude-session-id`, and falls back to the env vars when the
  installed CLI lacks it.
- With `get_session`/`list_sessions` available, the skill reports title
  and branch, and resolves another session by PR, then branch or title,
  then a user pick.
- `/lrh-closeout` Step 3, `/lrh-land` Step 3, and `/lrh-implement` call the
  skill rather than restating the resolution order, and pass `--title` and
  `--branch` to `record-session-alias` where resolved.
- Rendered targets are regenerated for every touched skill. `CLAUDE.md`
  indexes the new skill. `lrh chain-defaults status` reports `stale: False`.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`
- `lrh skills check --target claude --local --source current-repo`
- `lrh skills status --target codex --local --source current-repo`
- `lrh skills status --target antigravity --local --source current-repo`
- `lrh chain-defaults status`
- `grep -rn "Copy URL" src/lrh/skills` (only "no longer exposes" notes remain)

## Risk Notes

- The session-management tools (`get_session`, `list_sessions`) exist only
  in the Claude desktop app. In CLI-only sessions the skill must degrade to
  the env var alone and say that title and branch are unavailable.
- The Codex renderer flags `argument-hint` as having no Codex equivalent.
  Keep the same frontmatter shape `lrh-codex-session` uses, so the Codex
  target is no worse than today.
- The Codex and Antigravity rendered targets already differ from source for
  several skills. Regenerating touched skills may pull in unrelated
  upstream text. Review the diff rather than assuming it is scoped to this
  item.
- Routing the resolution order through a skill makes closeout depend on the
  new skill being installed. The callers should keep a one-line inline
  fallback (the env var) for machines where it is missing.
