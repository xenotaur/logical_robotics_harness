# Use LRH with AI Agent Assistants

## Purpose

Use this guide to set up and operate Logical Robotics Harness (LRH) skills across different AI agent assistants, including **Claude Code**, the **Codex App**, and **Google Antigravity**.

LRH maintains a single canonical skill source (`src/lrh/skills/`) that can be rendered or discovered across multiple agent environments.

## Prerequisites

- LRH installed so the `lrh` command is available.
- An LRH-managed project repository (or a repository configured with `project/agent_skills.yaml`).

## Agent Assistant Setup & Usage Patterns

```
                               CANONICAL SOURCE
                              (src/lrh/skills/*)
                                      │
           ┌──────────────────────────┼──────────────────────────┐
           ▼                          ▼                          ▼
    CLAUDE CODE                   CODEX APP                 ANTIGRAVITY
 (~/.claude/skills/)          (~/.agents/skills/)      (AGENTS.md / .gemini)
```

---

### 1. Claude Code

Claude Code discovers skills placed in its local filesystem skills directories (`~/.claude/skills/` or `./.claude/skills/`).

#### Installation
To install or update LRH skills for Claude Code:

```bash
# Global user-scope install (~/.claude/skills/)
lrh skills install --target claude

# Project-scope install (./.claude/skills/)
lrh skills install --local --target claude
```

#### Usage in Session
Once installed, Claude Code automatically indexes skills. You can trigger them via slash commands (e.g., `/lrh-work-item`, `/lrh-implement`, `/lrh-land`) or ask Claude to execute a workflow step.

---

### 2. Codex App

Codex discovers Agent Skills located in `.agents/skills/` (user-scope `~/.agents/skills/` or project-scope `./.agents/skills/`).

#### Installation
LRH renders skills for Codex by stripping Claude-only frontmatter (e.g. `argument-hint`) and translating invocation rules into a sibling `agents/openai.yaml` file:

```bash
# Global user-scope install (~/.agents/skills/)
lrh skills install --target codex

# Project-scope install (./.agents/skills/)
lrh skills install --local --target codex
```

#### Multi-Target Install
To update skills for both Claude Code and Codex simultaneously:

```bash
lrh skills install --target all
```

---

### 3. Google Antigravity

Antigravity supports both **Direct In-Repo Discovery** (zero-install via project rules) and **Native Plugin Installation**.

#### Pattern A: Direct In-Repo Discovery (Recommended / Zero-Install)
Antigravity automatically loads workspace `AGENTS.md` and user-level `~/.gemini/GEMINI.md` files as system rules (`<user_rules>`).

1. **Project-Wide Rules (`AGENTS.md`)**: Add the following directive to your project's `AGENTS.md`:
   ```markdown
   ## Agent Skill Rules
   When asked to perform workflow tasks (e.g. lrh-work-item, lrh-implement, lrh-land), use `view_file` to read the corresponding `SKILL.md` in `src/lrh/skills/` or `.claude/skills/` before proceeding.
   ```

2. **Global Rules (`~/.gemini/GEMINI.md`)**: To enable this discovery across all repositories on your system, add to `~/.gemini/GEMINI.md`:
   ```markdown
   # Global Agent Skill Rules
   If the current workspace contains an `src/*/skills/`, `.claude/skills/`, or `.agents/skills/` directory, actively discover and utilize those skills by inspecting `SKILL.md` files.
   ```

#### Pattern B: Native Plugin Installation
For ambient prompt indexing via plugin manifests (`plugin.json`), future releases of LRH will support:

```bash
lrh skills install --target antigravity
```

This renders skills to `~/.gemini/config/plugins/lrh/skills/` alongside a generated `plugin.json`.

---

### 4. Extending for Other Assistants

Because LRH decouples canonical skill sources (`src/lrh/skills/`) from target-rendered copies, new agent targets (such as ChatGPT Skills or emerging open standards) can be added cleanly via the `lrh skills install --target <name>` CLI interface.

---

## Related Documentation

- [Keep skills up to date](keep-skills-up-to-date.md) — check status, diffs, and force-updates.
- [Agent skills config reference](../reference/schemas/agent-skills-config.md) — repository-local configuration schema (`project/agent_skills.yaml`).
- [Antigravity Interoperability Decision](../../project/memory/decisions/DEC-AGENT-SKILL-INTEROPERABILITY-ANTIGRAVITY.md) — architectural decision record.
