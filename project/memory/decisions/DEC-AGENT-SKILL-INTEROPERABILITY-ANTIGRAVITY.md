---
id: DEC-AGENT-SKILL-INTEROPERABILITY-ANTIGRAVITY
---

# Agent Skill Interoperability — Antigravity Integration & Discovery Semantics

Status: accepted
Date: 2026-08-07

## Summary

This decision defines how LRH models and integrates Google Antigravity as an agent execution environment alongside Claude Code and the Codex App. Antigravity discovers and executes skills via two distinct mechanisms: (1) native plugin manifests (`~/.gemini/config/plugins/<plugin>/plugin.json` for user scope, or `./.gemini/plugins/<plugin>/plugin.json` for project scope) for ambient system-prompt indexing, and (2) on-demand direct file inspection of canonical in-repo `SKILL.md` files (in `src/lrh/skills/`, `.claude/skills/`, or `.agents/skills/`) guided by CLI system rules (`AGENTS.md` / `~/.gemini/GEMINI.md`) or IDE workspace rules (`.agents/rules/` / `.gemini/rules/`).

## Context

- LRH is a reusable harness for structured, evidence-backed, agent-assisted workflows across multiple independent project repositories (`AGENTS.md`).
- Target-aware installer work (`PROP-LRH-SKILLS-TARGET-AWARE-INSTALL`) established `.claude/skills/` (Claude Code) and `.agents/skills/` (Codex App) as first-class local install targets rendered from canonical skill sources in `src/lrh/skills/`.
- Antigravity uses a plugin/skill architecture where skills center around `SKILL.md` (YAML frontmatter + Markdown body prose) housed under `~/.gemini/config/plugins/<plugin>/skills/<skill>/SKILL.md` (user scope) or `./.gemini/plugins/<plugin>/skills/<skill>/SKILL.md` (project scope).
- Antigravity also parses workspace `AGENTS.md` and user-level `~/.gemini/GEMINI.md` files into `<user_rules>` at CLI session initialization, while IDE workspace rule settings live in `.agents/rules/` or `.gemini/rules/`.

## Decision

1. **Dual-Tier Interoperability Strategy for Antigravity**:
   - **Tier 1 (Direct In-Repo Discovery via Rules)**: Recommend repo-level (`AGENTS.md`) or user-level (`~/.gemini/GEMINI.md`) skill-discovery rules for immediate, zero-install use of LRH skills in Antigravity CLI sessions, or `.agents/rules/` for IDE workspace rule configurations. When instructed, Antigravity directly reads project skill files (`.claude/skills/`, `.agents/skills/`, or `src/*/skills/`) via file-viewing capabilities.
   - **Tier 2 (Target Exporter Extension)**: Extend `lrh skills install` (`src/lrh/skills/installer.py`) with an explicit `--target antigravity` option, rendering skills into user scope (`~/.gemini/config/plugins/lrh/skills/`) or project scope (`./.gemini/plugins/lrh/skills/`) and generating `plugin.json`.

2. **Metadata & Framing Semantics**:
   - Antigravity render adapters must strip Claude-specific frontmatter (`disable-model-invocation`, `argument-hint`) and emit a valid plugin manifest (`plugin.json`).
   - Skill body prose neutralization remains a shared follow-on cost across Codex and Antigravity, replacing tool-specific slash commands (`/lrh-*`) and runner names (`Claude Code`) with agent-neutral phrasing.

## Rationale

- Avoids fragmenting skill sources while ensuring Antigravity can operate as a first-class agent assistant within LRH repositories.
- Preserves the canonical-source principle: `src/lrh/skills/` remains the authoritative skill tree; target directories are rendered outputs.
- Adheres to Diátaxis documentation principles for user guidance while preserving architectural precedence in `project/memory/decisions/`.

## Consequences

- Documentation in `docs/how-to/use-lrh-with-agent-assistants.md` provides side-by-side setup instructions for Claude Code, Codex App, and Antigravity.
- `PROP-LRH-SKILLS-TARGET-AWARE-INSTALL` can incorporate `antigravity` as an explicit installer target alongside `claude` and `codex`.
