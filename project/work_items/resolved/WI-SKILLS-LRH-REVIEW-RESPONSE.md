---
resolution: Implemented and merged in PR #320 (a4618e5)
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-REVIEW-RESPONSE
title: Implement lrh-review-response Claude Code skill
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS
related_design:
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
  - project/design/proposals/adopted/lrh-project-local-skills/01_lrh_implement_skill.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_setup
  - merge_pr
  - resolve_github_comments
acceptance:
  - src/lrh/skills/lrh-review-response/SKILL.md exists with valid frontmatter
  - Both references/ files exist under both src/ and .claude/ locations
  - diff -r src/lrh/skills/lrh-review-response/ .claude/skills/lrh-review-response/ reports no differences
  - CLAUDE.md lists /lrh-review-response in the Skills section
  - lrh validate reports 0 errors
  - Skill exits cleanly with "Nothing to resolve" message when no open comments exist
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-review-response/SKILL.md
  - src/lrh/skills/lrh-review-response/references/review-response-workflow.md
  - src/lrh/skills/lrh-review-response/references/canonical-validation.md
  - .claude/skills/lrh-review-response/SKILL.md
  - .claude/skills/lrh-review-response/references/review-response-workflow.md
  - .claude/skills/lrh-review-response/references/canonical-validation.md
  - CLAUDE.md (Skills section updated with /lrh-review-response)
---

## Summary

Implement the `/lrh-review-response` Claude Code skill that addresses open PR
review comments in a structured, traceable way. Given a PR URL (or
auto-detected from the current branch), it fetches open comments via
`lrh request review_response`, displays them for confirmation, mints an AD_HOC
prompt ID for traceability, triages and addresses each comment following the
embedded protocol, validates, pushes fixes to the open PR, and creates an
execution record linked back to the original via `rerun_of`.

## Problem / Context

After `/lrh-implement` opens a PR, automated reviewers (Codex, Copilot) and
human reviewers post comments. Addressing these currently requires the user to
manually run `lrh request review_response <pr-url>`, copy the formatted output,
and paste it into the agent session that created the PR. This copy-paste step
breaks context continuity and is error-prone. `/lrh-review-response` closes
this gap by running the fetch, confirmation, execution, and traceability steps
inline — ideally in the same session that created the PR, preserving full
design context.

The full design for this skill was produced and agreed in the session that
implemented `WI-SKILLS-LRH-IMPLEMENT`. Key decisions are encoded in the
Required Changes section below.

## Scope

- Implement `src/lrh/skills/lrh-review-response/` (SKILL.md and two reference
  files) and mirror byte-for-byte to `.claude/skills/lrh-review-response/`
- Update `CLAUDE.md` to add `/lrh-review-response` to the Skills section
- Add `WI-SKILLS-LRH-REVIEW-RESPONSE` to the `work_items:` list in `WS-SKILLS.md`

## Required Changes

1. Create `src/lrh/skills/lrh-review-response/SKILL.md` — 7-step skill body
   with `disable-model-invocation: true` and `argument-hint: "[pr-url]"`.

   The seven steps:
   - **Step 1 — Detect PR and verify branch:** if `<pr-url>` given, verify
     current branch matches via `gh pr view <url> --json headRefName`; if
     omitted, auto-detect via `gh pr view --json url,headRefName`. Stop if
     branch doesn't match or PR is not open.
   - **Step 2 — Fetch open comments:** run `lrh request review_response
     <pr-url>`. If output begins with `"Nothing to resolve:"`, report and exit
     cleanly. Store the full output for Step 5.
   - **Step 3 — Display comments and mint prompt ID:** display the comment-data
     section (after the security separator) to the user. Derive slug from
     current branch name (strip `<username>/<type>/` prefix, append `-review`).
     Run `lrh prompt label --slug <slug>` and `lrh prompt check-execution
     --prompt-id "<id>" --project-root .`. Stop if a prior landed/in_progress
     record exists unless user explicitly requests rerun.
   - **Step 4 — Confirm gate:** show PR URL, comment count, each comment
     summary, minted prompt ID, and expected scope. Wait for explicit
     confirmation. Record any user directives (e.g., "skip comment X").
   - **Step 5 — Execute review response protocol:** follow the full
     `lrh request review_response` output (protocol preamble + `REVIEWS.md`
     overrides). For each comment: Presence → Validity → Feasibility → fix if
     applicable. Run canonical validation per
     `references/canonical-validation.md`.
   - **Step 6 — Commit and push:** stage and commit all changes with the
     prompt ID in the commit message. Push to the existing open PR branch.
   - **Step 7 — Create execution record and report:** run
     `lrh prompt record-execution --prompt-id "<id>" --work-item AD_HOC
     --slug <slug> --status in_progress --project-root .`. Populate
     `agent: claude_app`, `instruction_source: <pr-url>`,
     `session_transcript: pending`. Search for the original execution ID via
     `find project/executions/ -name "*<branch-slug>*.md"` and populate
     `rerun_of:` if found. Commit record and push as additional commit.
     Report: what was fixed/skipped per comment, validation evidence.

2. Create `src/lrh/skills/lrh-review-response/references/review-response-workflow.md`
   — lifecycle placement (sits after `/lrh-implement` opens the PR; before
   merge and work-item closeout), `rerun_of` field convention, edge cases (no
   comments, closed PR, design-decision conflicts, invoking from a fresh session
   without design context).

3. Create `src/lrh/skills/lrh-review-response/references/canonical-validation.md`
   — the `scripts/` validation sequence, per-command failure handling, and
   evidence format for the execution record body.

4. Mirror all three files to `.claude/skills/lrh-review-response/`
   (byte-for-byte identical, verified with `diff -r`).

5. Update `CLAUDE.md` — add `/lrh-review-response` to the `## Skills` section.

6. Add `WI-SKILLS-LRH-REVIEW-RESPONSE` to the `work_items:` list in
   `project/workstreams/proposed/WS-SKILLS.md`.

## Non-Goals

- Do not automatically resolve GitHub review conversations — that is a human
  decision made after reviewing the fixes.
- Do not create a new branch — review response commits go on the existing PR
  branch.
- Do not implement multiple PR responses in one invocation.
- Do not implement `lrh setup` — that is `WI-SKILLS-LRH-SETUP`.
- Do not add CI diff enforcement between the two skill copies — Stage 3 item.
- Do not modify `lrh request review_response` or its template — the skill
  consumes the command's output as-is.

## Acceptance Criteria

- `src/lrh/skills/lrh-review-response/SKILL.md` exists with valid YAML
  frontmatter (`name: lrh-review-response`, `disable-model-invocation: true`).
- Both `references/` files exist under both `src/lrh/skills/lrh-review-response/`
  and `.claude/skills/lrh-review-response/`.
- `diff -r src/lrh/skills/lrh-review-response/ .claude/skills/lrh-review-response/`
  reports no differences.
- `CLAUDE.md` lists `/lrh-review-response` in the Skills section.
- `lrh validate` reports 0 errors.
- When invoked on a PR with no open comments, the skill outputs "Nothing to
  resolve" and exits without touching any files.

## Validation

- `scripts/version tools`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-review-response/ .claude/skills/lrh-review-response/`

## Risk Notes

- **Prompt injection boundary**: the `lrh request review_response` output
  already embeds a security separator between the protocol and reviewer
  content. The skill must pass the full output to the model as a unit — not
  re-emit reviewer comments in a separate context that could elevate them
  above the boundary.
- **Fresh-session context gap**: the skill works best in the same session that
  created the PR (full design context). When invoked in a fresh session, the
  user may need to supply additional context about intentional design decisions
  before the triage step.
- **Two copies must stay in sync** manually until Stage 3 adds CI enforcement,
  as documented in `CONTRIBUTING.md`.
