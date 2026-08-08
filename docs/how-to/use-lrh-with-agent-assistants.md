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

Antigravity supports both **Direct In-Repo Discovery** (zero-install via project/workspace rules) and **Native Plugin Installation**.

#### Pattern A: Direct In-Repo Discovery (Zero-Install / Rules-Based)
Antigravity automatically loads workspace `AGENTS.md` and user-level `~/.gemini/GEMINI.md` files into `<user_rules>` during CLI session initialization. For IDE workspace configurations, rules can also be placed under `.agents/rules/` or `.gemini/rules/`.

*Note on Skill Discovery*: In downstream repositories where LRH is installed as a package, agent skills live in project-local skills directories (installed via `lrh skills install --local`) or in the repository's source tree. Direct in-repo discovery reads these local skill files when present in the workspace.

1. **Project-Wide CLI / System Rules (`AGENTS.md`)**: Add the following directive to your project's `AGENTS.md`:
   ```markdown
   ## Agent Skill Rules
   When asked to perform workflow tasks (e.g. lrh-work-item, lrh-implement, lrh-land), inspect and read the corresponding `SKILL.md` in `.claude/skills/`, `.agents/skills/`, or `src/*/skills/` before proceeding.
   ```

2. **Global System Rules (`~/.gemini/GEMINI.md`)**: To enable this discovery across all repositories on your system, add to `~/.gemini/GEMINI.md`:
   ```markdown
   # Global Agent Skill Rules
   If the current workspace contains an `src/*/skills/`, `.claude/skills/`, or `.agents/skills/` directory, actively discover and utilize those skills by inspecting their `SKILL.md` files.
   ```

3. **IDE Workspace Rules (`.agents/rules/` or `.gemini/rules/`)**: For IDE rule enforcement, place rule instructions under `.agents/rules/lrh-skills.md` or `.gemini/rules/lrh-skills.md`.

#### Pattern B: Native Plugin Installation
For ambient prompt indexing via plugin manifests (`plugin.json`), install LRH skills directly as an Antigravity plugin:

```bash
# Global user-scope plugin install (~/.gemini/config/plugins/lrh/)
lrh skills install --target antigravity

# Project-scope plugin install (./.gemini/plugins/lrh/)
lrh skills install --local --target antigravity

# Install all targets (Claude Code, Codex, and Antigravity)
lrh skills install --target all
```

This renders skills to `~/.gemini/config/plugins/lrh/skills/` (or `./.gemini/plugins/lrh/skills/`) alongside a generated `plugin.json`.

---

### 4. Extending for Other Assistants

Because LRH decouples canonical skill sources (`src/lrh/skills/`) from target-rendered copies, new agent targets (such as ChatGPT Skills or emerging open standards) can be added cleanly via the `lrh skills install --target <name>` CLI interface.

---

## Related Documentation

- [Keep skills up to date](keep-skills-up-to-date.md) — check status, diffs, and force-updates.
- [Agent skills config reference](../reference/schemas/agent-skills-config.md) — repository-local configuration schema (`project/agent_skills.yaml`).
- [Antigravity Interoperability Decision](../../project/memory/decisions/DEC-AGENT-SKILL-INTEROPERABILITY-ANTIGRAVITY.md) — architectural decision record.
