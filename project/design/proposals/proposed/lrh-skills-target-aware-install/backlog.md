---
id: BACKLOG-LRH-SKILLS-TARGET-AWARE-INSTALL
type: design_backlog
title: Codex Skills Compatibility Backlog
status: open
created_on: 2026-08-02
updated_on: 2026-08-02
related_design:
  - project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md
  - project/workstreams/proposed/WS-SKILLS-TARGET-AWARE-INSTALL.md
---

# Codex Skills Compatibility Backlog

Lightweight list of Claude-to-Codex skill compatibility issues discovered while
dogfooding LRH skills in Codex. Each entry should record what was observed, why
it matters for Codex, and where it came from so a future burn-down pass can
decide whether to fix it in a render adapter, canonical skill prose, or
supporting LRH tooling.

---

## Planning skills hard-code Claude execution-record provenance

**Noted:** 2026-08-02, while running `/lrh-workstream` from a Codex app
session for `PROP-LRH-SKILLS-TARGET-AWARE-INSTALL`.

**Issue:** The planning skills instruct the operator to create execution
records with Claude-specific provenance, including `agent: claude_app`,
`session_transcript: claude-app:<host-uuid-stem>`, and references to
`CLAUDE_CODE_HOST_SESSION_ID`. That is appropriate for Claude Code sessions but
not for Codex app sessions, where the durable transcript identifier and agent
label are different.

**Idea:** Define Codex execution-record provenance values, such as
`agent: codex_app` and a Codex task/thread transcript reference, then update the
skill instructions or target renderer so Codex-installed skills do not tell
Codex to record itself as Claude.

**Status:** Tracked, not yet implemented.

**Related:** `src/lrh/skills/lrh-workstream/SKILL.md`;
`src/lrh/skills/lrh-workstream/references/execution-record.md`;
`src/lrh/skills/lrh-work-item/SKILL.md`;
`src/lrh/skills/lrh-work-item/references/execution-record.md`;
`src/lrh/skills/lrh-proposal/SKILL.md`;
`src/lrh/skills/lrh-proposal/references/execution-record.md`;
`src/lrh/skills/lrh-implement/SKILL.md`;
`src/lrh/skills/lrh-land/SKILL.md`.

---

## Slash-command and argument-hint framing leaks into Codex installs

**Noted:** 2026-08-02, while applying a Claude-authored `/lrh-workstream`
skill manually in Codex.

**Issue:** LRH skill bodies and frontmatter frequently describe invocation as
Claude slash commands (`/lrh-workstream`, `/lrh-work-item`, `/lrh-land`) and use
Claude UI metadata such as `argument-hint`. Codex can still process the
procedural content when the user names the skill, but the installed Codex copy
would present Claude-specific command syntax and unsupported UI hints.

**Idea:** Make canonical skill prose more agent-neutral, or have the Codex
renderer remove/translate Claude-only invocation metadata and examples where
that can be done mechanically. Keep concrete command names only where the LRH
workflow itself requires them as historical or user-facing identifiers.

**Status:** Tracked, not yet implemented.

**Related:** `src/lrh/skills/lrh-workstream/SKILL.md`;
`src/lrh/skills/lrh-work-item/SKILL.md`;
`src/lrh/skills/lrh-proposal/SKILL.md`;
`src/lrh/skills/lrh-implement/SKILL.md`;
`src/lrh/skills/lrh-land/SKILL.md`;
`project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md`
Decision 2 and Decision 4.

---

## Manual-only invocation metadata needs Codex policy translation

**Noted:** 2026-08-02, while reviewing which Claude skill metadata would behave
incorrectly if copied directly into `.agents/skills/`.

**Issue:** Several LRH skills rely on Claude's `disable-model-invocation: true`
metadata to prevent implicit use of manual-only workflows. Codex does not use
that frontmatter field directly; the proposal identifies `agents/openai.yaml`
as the Codex-side policy location. Direct copying without translation can make
the Codex skill discoverable while failing to preserve the intended invocation
policy.

**Idea:** Treat this as a renderer acceptance criterion: Claude
`disable-model-invocation: true` must become Codex
`policy.allow_implicit_invocation: false` in `agents/openai.yaml`, or an
equivalent Codex-supported policy mechanism if the platform contract changes.

**Status:** Tracked, not yet implemented.

**Related:** `src/lrh/skills/lrh-implement/SKILL.md`;
`src/lrh/skills/lrh-land/SKILL.md`;
`project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md`
Decision 2.

---

## Skill references assume `.claude/skills/` mirrors as the installed target

**Noted:** 2026-08-02, while reading LRH skill authoring and validation
guidance before creating this workstream.

**Issue:** Some skill instructions and references describe installation,
mirroring, or validation in terms of `src/lrh/skills/` and `.claude/skills/`.
That was correct when Claude was the only local target, but it is incomplete
once `.agents/skills/` becomes a first-class Codex install target.

**Idea:** Update skill authoring and closeout guidance to talk about canonical
sources and selected install targets, then make validation or status tooling
show both Claude and Codex mirror state when relevant.

**Status:** Tracked, not yet implemented.

**Related:** `src/lrh/skills/lrh-work-item/references/work-item-body-guide.md`;
`src/lrh/skills/lrh-workstream/SKILL.md`;
`project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md`
Decision 1, Decision 3, and Decision 4.
