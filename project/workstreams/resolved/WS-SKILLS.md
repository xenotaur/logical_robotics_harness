---
id: WS-SKILLS
kind: planning_node
title: Claude Code Skills Infrastructure
status: resolved
stage: closed
origin: ad_hoc
summary: >
  Establish first-class Claude Code skill support in LRH: the lrh-create-skill
  skill, src/lrh/skills/ package directory, lrh setup installer, and
  subsequent workflow skills (lrh-work-item, lrh-workstream, lrh-assess).
related_design:
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
work_items:
  - WI-SKILLS-CREATE-SKILL
  - WI-SKILLS-LRH-WORK-ITEM
  - WI-SKILLS-LRH-IMPLEMENT
  - WI-SKILLS-LRH-SETUP
  - WI-SKILLS-LRH-REVIEW-RESPONSE
exit_criteria:
  - lrh-create-skill skill is available in .claude/skills/ and src/lrh/skills/
  - lrh setup installs LRH skills to ~/.claude/skills/ idempotently
  - at least one workflow skill (lrh-work-item) is implemented and dogfooded
---

## Summary

LRH's structured workflow steps (assess, design, create workstream, create
work item) are currently driven by prompts stored in Apple Notes and pasted
manually into chat sessions. This workstream moves that knowledge into
versioned, project-aware Claude Code skills committed to the repository.

## Stages

**Stage 1 — Core skill infrastructure (WI-SKILLS-CREATE-SKILL)**
Implement `lrh-create-skill`: the self-bootstrapping skill that creates new
project-local skills. Establishes `src/lrh/skills/`, `.claude/skills/`,
and `pyproject.toml` package-data declaration.

**Stage 2 — Global installer (WI-SKILLS-LRH-SETUP)**
Implement `lrh setup` to copy skills from `src/lrh/skills/` to
`~/.claude/skills/`, making LRH skills available in any project on the
machine.

**Stage 3 — Workflow skills**
Use the Stage 1 infrastructure to add `/lrh-work-item`, `/lrh-workstream`,
and `/lrh-assess` skills. Each is a separate work item.

## Non-Goals

- Do not upload skills to the claude.ai Skills API.
- Do not auto-install skills during `lrh request bootstrap_project`.
- Do not implement `lrh run` or any autonomous execution in this workstream.

## Closeout

All five work items resolved and all exit criteria met as of 2026-06-25.

Delivered:
- `src/lrh/skills/` package with four distributable skills: `lrh-create-skill`,
  `lrh-work-item`, `lrh-implement`, `lrh-review-response`
- `lrh setup` CLI command (idempotent, `--dry-run`, `--force`) with 13 unit tests
- `.claude/skills/` self-hosted copies of all four skills for LRH repo sessions
- `CLAUDE.md` skill index entries for all four skills
- `pyproject.toml` package-data declaration for `lrh.skills`

PRs: #316 (create-skill), #317 (lrh-work-item), #319 (lrh-implement),
     #321 (lrh-review-response), #325 (lrh-setup)
