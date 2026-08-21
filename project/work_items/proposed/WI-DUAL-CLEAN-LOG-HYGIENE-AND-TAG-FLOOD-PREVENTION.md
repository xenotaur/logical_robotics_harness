---
resolution: null
blocked_reason: null
blocked: false
id: WI-DUAL-CLEAN-LOG-HYGIENE-AND-TAG-FLOOD-PREVENTION
title: Implement Dual-Clean log redirection and Markdown fencing hygiene
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
  - run_tests
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - scripts/test writes execution logs to tmp/logs/ and outputs a compact status line
  - scripts/validate writes execution logs to tmp/logs/ and outputs a compact status line
  - .claude/skills/lrh-execute/SKILL.md and .claude/skills/lrh-self-review/SKILL.md include log hygiene code-fencing rules
  - lrh validate passes with 0 errors
required_evidence:
  - lrh_validate
  - test_output
  - manual_review
artifacts_expected:
  - scripts/test
  - scripts/validate
  - .claude/skills/lrh-execute/SKILL.md
  - .claude/skills/lrh-self-review/SKILL.md
---

## Summary

Implement the Dual-Clean Pattern in LRH helper scripts (`scripts/test`, `scripts/validate`) and skill templates (`.claude/skills/`) to eliminate `<SYSTEM_MESSAGE>` XML/HTML tag cascades in agent UI renderers (such as Antigravity) without hiding diagnostic logs or adding platform-specific coupling to core Python modules.

## Problem / Context

Background test runs (`scripts/test`) and validation checks (`scripts/validate`) stream stdout/stderr into system message transport wrappers (`<SYSTEM_MESSAGE>...</SYSTEM_MESSAGE>`). When output text or test logs contain unescaped `<SYSTEM_MESSAGE>` tags or massive multi-hundred-line dumps, UI renderers fail to parse nested tags, causing repeated `</SYSTEM_MESSAGE>` tag cascades in the session transcript.

Crucially, suppressing test output (`pytest -q`) degrades diagnostic visibility and violates LRH evidence policy (`AGENTS.md:69-72`), while building custom stream-parsing code inside `src/lrh/` adds unnecessary maintenance overhead for a vendor-specific rendering quirk (`AGENTS.md:17-27`).

### Prior Art Check

#### Duplication search
- **In-repo**: No existing implementation found in `src/`, `project/`, or `.claude/skills/`.
- **Sibling repos**: None identified.
- **External libraries**: None identified (standard POSIX shell redirection & Markdown rules).
- **Verdict**: Proceed.

#### Demand search
- **Work items**: None found in `project/work_items/` proposed or active.
- **Proposals**: None found in `project/design/proposals/`.
- **Backlog**: No matching entries in `project/design/backlog.md`.
- **Verdict**: Proceed with creating this work item.

## Scope

- Update `scripts/test` and `scripts/validate` to redirect raw subprocess stdout/stderr to `tmp/logs/` while echoing a compact 1-line summary and log path to stdout.
- Update `.claude/skills/lrh-execute/SKILL.md` and `.claude/skills/lrh-self-review/SKILL.md` to add a Formatting & Log Hygiene section directing agents to fence raw log quotes and XML tag references inside Markdown code blocks.

## Required Changes

### `scripts/test`
- Create `tmp/logs/` if missing.
- Redirect stdout and stderr from `python -m unittest` to `tmp/logs/test_<timestamp>.log`.
- On success, echo concise pass status and log location.
- On failure, echo concise fail status, exit code, and log location for inspection via `view_file`.

### `scripts/validate`
- Redirect `lrh validate` stdout/stderr to `tmp/logs/validate_<timestamp>.log`.
- Output concise status line and log path.

### `.claude/skills/lrh-execute/SKILL.md` & `.claude/skills/lrh-self-review/SKILL.md`
- Add explicit Formatting & Log Hygiene guidelines instructing agents to wrap all XML/HTML tag literals and raw log quotes in fenced code blocks (` ``` `).

## Non-Goals

- Modifying core Python modules under `src/lrh/` to add custom stream filtering.
- Forcing `pytest -q` or hiding tracebacks from log files.
- Hardcoding vendor-specific environment variable checks in shell scripts.

## Acceptance Criteria

- `scripts/test` writes full execution logs to `tmp/logs/` and outputs a compact status line.
- `scripts/validate` writes full execution logs to `tmp/logs/` and outputs a compact status line.
- `.claude/skills/lrh-execute/SKILL.md` and `.claude/skills/lrh-self-review/SKILL.md` contain explicit Markdown code-fencing rules for tag literals and log output.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/test`
- `scripts/validate`
- `lrh validate`

## Risk Notes

- Low risk: Shell script redirection uses standard POSIX syntax. Log files are saved in `tmp/`, which is already in `.gitignore`.
