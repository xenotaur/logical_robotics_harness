---
resolution: landed
blocked_reason: null
blocked: false
id: WI-DUAL-CLEAN-LOG-HYGIENE-AND-TAG-FLOOD-PREVENTION
title: Implement Dual-Clean log redirection and Markdown fencing hygiene
type: deliverable
status: resolved
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
  - scripts/test streams standard output by default, and redirects to tmp/logs/ with a compact 1-line summary when passed --log or when LRH_LOG_REDIRECT=1 is set
  - scripts/validate streams standard output by default, and redirects to tmp/logs/ with a compact 1-line summary when passed --log or when LRH_LOG_REDIRECT=1 is set
  - .claude/skills/lrh-execute/SKILL.md and .claude/skills/lrh-self-review/SKILL.md include log hygiene code-fencing rules and --log invocation instructions
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

Implement the Dual-Clean Pattern in LRH helper scripts (`scripts/test`, `scripts/validate`) and skill templates (`.claude/skills/`) to eliminate XML/HTML tag cascades in agent UI renderers without altering standard interactive terminal behavior for human maintainers or breaking tool interfaces.

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

- Update `scripts/test` and `scripts/validate` to support an opt-in `--log` flag and `LRH_LOG_REDIRECT=1` environment variable. By default, scripts preserve 100% standard streaming stdout/stderr for human maintainers. When `--log` or `LRH_LOG_REDIRECT=1` is passed, raw subprocess stdout/stderr is redirected to `tmp/logs/` while echoing a compact 1-line summary and log path to stdout.
- Update `.claude/skills/lrh-execute/SKILL.md` and `.claude/skills/lrh-self-review/SKILL.md` to add a Formatting & Log Hygiene section directing agents to fence raw log quotes and XML tag references inside Markdown code blocks (` ``` `), and to invoke validation scripts with `--log`.

## Required Changes

### `scripts/test`
- Preserve default streaming output to standard output when run interactively.
- Add `--log` flag (and check `LRH_LOG_REDIRECT=1`) to redirect stdout/stderr from `python -m unittest` to `tmp/logs/test_<timestamp>.log`.
- In `--log` mode, echo a concise status line containing test count, pass/fail result, and log file path while strictly preserving the subprocess exit code (`exit_code=$?`).

### `scripts/validate`
- Preserve default streaming output to standard output.
- Add `--log` flag (and check `LRH_LOG_REDIRECT=1`) to redirect `lrh validate` stdout/stderr to `tmp/logs/validate_<timestamp>.log` and output a concise status line, preserving exit code.

### `.claude/skills/`
- Update `.claude/skills/lrh-implement/references/canonical-validation.md` and related skill files to specify running `scripts/test --log` and `scripts/validate --log` during agent-driven validation steps.
- Add explicit Markdown Log Hygiene guidelines instructing agents to wrap all XML/HTML tag literals and log excerpts in fenced code blocks (` ``` `).

## Non-Goals

- Modifying core Python modules under `src/lrh/` to add custom stream filtering.
- Forcing `pytest -q` or hiding tracebacks from log files.
- Hardcoding vendor-specific environment variable checks in shell scripts.

## Acceptance Criteria

- `scripts/test` streams standard output by default, and redirects to `tmp/logs/` with a compact 1-line summary when passed `--log` or when `LRH_LOG_REDIRECT=1` is set.
- `scripts/validate` streams standard output by default, and redirects to `tmp/logs/` with a compact 1-line summary when passed `--log` or when `LRH_LOG_REDIRECT=1` is set.
- Subprocess exit codes are strictly preserved in both default and `--log` modes.
- `.claude/skills/lrh-execute/SKILL.md` and `.claude/skills/lrh-self-review/SKILL.md` contain explicit Markdown code-fencing rules and `--log` invocation instructions.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/test`
- `scripts/validate`
- `lrh validate`

## Risk Notes

- Low risk: Shell script redirection uses standard POSIX syntax. Log files are saved in `tmp/`, which is already in `.gitignore`.
