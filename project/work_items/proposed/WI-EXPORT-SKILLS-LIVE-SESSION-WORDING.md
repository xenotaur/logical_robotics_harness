---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXPORT-SKILLS-LIVE-SESSION-WORDING
title: Clarify live-session, PATH, overwrite and sensitivity wording in the transcript-export skills
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - weaken_human_gate
  - print_transcript_text
acceptance:
  - lrh-export-claude and lrh-antigravity-export state that inspect-export's `match_source_grew` status (exit 0) means the source grew after the export but its recorded prefix still matches, that this is expected for a still-growing live session, and that a true `mismatch` (an earlier byte changed, or the source shrank) is the only failure signal to act on
  - lrh-export-claude, lrh-antigravity-export and lrh-codex-export each document an "lrh not on PATH" fallback (PYTHONPATH=src python3 -m lrh.cli.main conversation ...) and note that a worktree's editable install may point at another checkout
  - "lrh-export-claude and lrh-antigravity-export state what to do when the destination already exists (same-session re-export needs --force), and their confirm-before-write text states that --force overwrites the existing file; no new gate is added and no confirm-before-write semantics change"
  - "lrh-codex-export does not receive the --force/overwrite note: its Step 4 always calls archive-codex-thread, which has no --force option and always allocates a fresh, uniquely-suffixed export directory rather than overwriting (src/lrh/conversations/codex_archive.py's _reserve_export_directory); the wording pass states this explicitly instead of applying an inapplicable criterion"
  - Each skill's reporting step states that a sensitivity status of potential means review before sharing, not that the export failed, and that unscanned means no scan was run
  - The lrh-codex-export skill does not receive the `match_source_grew` wording, because it verifies against a frozen raw capture with no live-growth case; the wording pass notes this explicitly
  - The missing .gemini/plugins/lrh/skills/lrh-antigravity-export mirror is reported as a finding, with the reason found or stated as unknown, and is not silently added or ignored
  - docs/reference/cli/conversation.md is updated only where its wording must match the skills
  - .claude/skills mirrors are byte-identical to src/lrh/skills; .agents/skills and .gemini/plugins/lrh/skills are regenerated via lrh skills install without overwriting unrelated locally modified skills
  - No transcript text is printed or committed while implementing or testing
  - scripts/test, scripts/lint, scripts/format --check --diff and lrh validate are all clean
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/lrh-export-claude/SKILL.md
  - src/lrh/skills/lrh-antigravity-export/SKILL.md
  - src/lrh/skills/lrh-codex-export/SKILL.md
  - docs/reference/cli/conversation.md
  - .claude/skills/lrh-export-claude/
  - .claude/skills/lrh-antigravity-export/
  - .claude/skills/lrh-codex-export/
  - .agents/skills/
  - .gemini/plugins/lrh/skills/
---

## Summary

Clarify four things in the transcript-export skill family that caused friction
when exporting live sessions: how to verify a still-growing transcript, what
to do when `lrh` is not on PATH, what happens when the destination already
exists, and what a `potential` sensitivity result means.

## Problem / Context

Evidence gathered in a live session on 2026-09-20/21:

1. **Live-transcript hash race.** Exporting the current Claude Code session
   succeeded, but a later `lrh conversation inspect-export --source
   <transcript>` reported `Source hash: mismatch`; the transcript had grown
   between calls (468,843 to 480,051 bytes). Re-running with `--force`,
   export and inspect in one shell call, gave `Valid: yes` and a hash match.
   Both exporters hash the bytes they read once at export time
   (`src/lrh/conversations/claude_export.py:58-62`,
   `src/lrh/conversations/antigravity_export.py:57-61`) and the inspector
   recomputes the hash later (`src/lrh/conversations/export_inspector.py:365`),
   so the code behaves as designed; the skills split export and inspect into
   separate steps (`lrh-export-claude/SKILL.md` Steps 4 and 5) and never say
   the verification is as-of-export.
2. **Antigravity run, same pattern**, inferred from a command log only; the
   cause of the first failure (destination exists or hash mismatch) is
   unconfirmed, so the destination-exists note below covers both causes.
3. **`lrh` not on PATH in Antigravity.** The agent fell back to
   `PYTHONPATH=src python3 -m lrh.cli.main conversation ...`; none of the
   export skills document this. The only "lrh not on PATH" mention in the
   skills is a reporting condition in `lrh-work-remains/SKILL.md`.
4. **Destination exists.** `--force` is described in each skill but no skill
   says what to do on a same-session re-export.
5. **Sensitivity reporting.** A Claude export of a long session reported 16
   `potential` findings; the reporting tables list `potential` without saying
   it means review before sharing.

Mirror finding: `.claude/skills` matches the source for all three skills;
`.agents/skills` matches only for `lrh-antigravity-export`; and
`.gemini/plugins/lrh/skills` has no `lrh-antigravity-export` at all.

**Superseded scope.** This work item originally proposed a companion item,
`WI-CONVERSATION-EXPORT-SOURCE-PREFIX-VERIFICATION`, to fix the live-transcript
hash race in code. While this PR was under review, a separate, parallel effort
landed exactly that fix on `main`: `WI-INSPECT-EXPORT-APPEND-ONLY-SOURCE-VERIFY`
(resolved, PR #692, commit `0da9ceee`) added an optional `source_byte_count` to
the manifest, has both the Claude and Antigravity exporters record it, and gives
`inspect-export` a `match_source_grew` status (exit 0) for a grown but
prefix-matching source, while still reporting `mismatch` for an earlier-byte
change or a whole-file mismatch with no recorded byte count. The companion item
was dropped as a duplicate (review findings, PR #689). This wording item's
point (a) now describes that shipped `match_source_grew` behavior directly,
rather than the single-call workaround originally proposed, since the code fix
makes the workaround unnecessary for a routine live-session export (a single
call remains useful only to avoid a large, but not necessarily append-only,
gap between export and inspect). See also `WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT`
(proposed, depends on the resolved item above), which covers the Claude skill's
own Step 5 treatment of `match_source_grew` as part of a broader current-session
default; this item's wording only needs to be consistent with it, not duplicate it.

Prior art check:

- **Duplication:** the live-transcript verification *mechanism* is already
  built (see above); this item's remaining scope (PATH fallback, destination-exists
  wording scoped correctly per skill, sensitivity-status wording, the mirror
  finding) is not covered by any existing or resolved work item.
- **Demand:** no existing work item requests the remaining scope.

## Scope

- Wording only, in the three export skills and, where needed,
  `docs/reference/cli/conversation.md`.
- Mirror sync and regeneration.

## Required Changes

- Describe the shipped `match_source_grew` verification behavior in the
  Claude and Antigravity skills' reporting steps, and state that a live-session
  export is a snapshot as of the moment it ran; the Codex source is a frozen
  raw capture and does not receive this wording.
- Add the PATH fallback line to all three skills.
- Add the destination-exists and `--force` overwrite note to `lrh-export-claude`
  and `lrh-antigravity-export` only, inside their confirm-before-write step;
  state in `lrh-codex-export` that no such note applies, since
  `archive-codex-thread` always allocates a fresh directory.
- Add the sensitivity-status explanation to each reporting step.
- Report the missing `.gemini` Antigravity mirror as a finding.
- Sync mirrors byte-identically for `.claude/` and regenerate the others.

## Non-Goals

- No new gate and no change to confirm-before-write semantics (the Antigravity
  gate question is `WI-ANTIGRAVITY-EXPORT-CONFIRM-GATE-ASSESSMENT`).
- No exporter or inspector code change; that verification mechanism is
  already shipped (`WI-INSPECT-EXPORT-APPEND-ONLY-SOURCE-VERIFY`, resolved).
- No change to `lrh-export-claude`'s discovery-flag or current-session
  defaults; that is `WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT`.
- Never print or preview transcript text.

## Acceptance Criteria

- The wording changes listed above, per skill.
- The mirror finding is reported.
- Mirrors are in sync and validation commands are clean.

## Validation

- scripts/test
- scripts/lint
- scripts/format --check --diff
- lrh validate
- diff -r src/lrh/skills/lrh-export-claude .claude/skills/lrh-export-claude
- diff -r src/lrh/skills/lrh-antigravity-export .claude/skills/lrh-antigravity-export
- diff -r src/lrh/skills/lrh-codex-export .claude/skills/lrh-codex-export

## Risk Notes

- `lrh skills install --force` overwrites every locally modified skill for the
  target; run `--dry-run` first and confirm only the export skills change.
- Another open PR may regenerate the same mirrors; sequence installs so one
  does not clobber the other.
- The PATH fallback is duplicated across skills by design (skills are
  self-contained), so it can drift; keep the wording identical.
