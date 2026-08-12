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
 (~/.claude/skills/)          (~/.agents/skills/)    (~/.gemini/.../lrh/)
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

Check whether the rendered Codex install is current:

```bash
lrh skills status --scope user --target codex
lrh skills status --scope project --target codex
```

LRH maintainers checking this repository's canonical source checkout can add
`--source current-repo`.

Restart Codex after creating `~/.agents/skills/` for the first time or after
updating global Codex skills so the app re-discovers the installed skills.

Use global installs when you want skills to appear across unrelated repositories
or worktrees. Use project-scope installs when you want a checkout-specific copy
rendered from that repository's current source.

#### Usage in Session
Once Codex discovers the skills, invoke LRH workflows by naming the skill
directly, such as `lrh-work-item`, `lrh-implement`, or `lrh-land`. The rendered
skill prose includes backend-aware execution-record and session-transcript
guidance for Codex app sessions.

#### Multi-Target Install
To update skills for Claude Code, Codex, and Antigravity simultaneously:

```bash
lrh skills install --target all
```

---

### 3. Google Antigravity

Antigravity supports both **Direct In-Repo Discovery** (zero-install via project rules) and **Native Plugin Installation**.

#### Pattern A: Direct In-Repo Discovery (Zero-Install / Rules-Based)
Antigravity automatically loads workspace `AGENTS.md` and user-level `~/.gemini/GEMINI.md` files as system rules (`<user_rules>`).

*Note on Skill Discovery*: In downstream repositories where LRH is installed as a package, agent skills live in project-local skills directories (installed via `lrh skills install --local`) or in the repository's source tree. Direct in-repo discovery reads these local skill files when present in the workspace.

1. **Project-Wide Rules (`AGENTS.md`)**: Add the following directive to your project's `AGENTS.md`:
   ```markdown
   ## Agent Skill Rules
   When asked to perform workflow tasks (e.g. lrh-work-item, lrh-implement, lrh-land), inspect and read the corresponding `SKILL.md` in `.claude/skills/`, `.agents/skills/`, `.gemini/plugins/lrh/skills/`, or `src/*/skills/` before proceeding.
   ```

2. **Global Rules (`~/.gemini/GEMINI.md`)**: To enable this discovery across all repositories on your system, add to `~/.gemini/GEMINI.md`:
   ```markdown
   # Global Agent Skill Rules
   If the current workspace contains an `src/*/skills/`, `.claude/skills/`, `.agents/skills/`, or `.gemini/plugins/lrh/skills/` directory, actively discover and utilize those skills by inspecting their `SKILL.md` files.
   ```

#### Pattern B: Native Plugin Installation
For ambient prompt indexing via plugin manifests (`plugin.json`), install the
Antigravity target:

```bash
# Global user-scope install (~/.gemini/config/plugins/lrh/)
lrh skills install --target antigravity

# Project-scope install (./.gemini/plugins/lrh/)
lrh skills install --local --target antigravity
```

This renders skills to `~/.gemini/config/plugins/lrh/skills/` or
`./.gemini/plugins/lrh/skills/` alongside a generated `plugin.json` at the
plugin root. The Antigravity renderer strips Claude-only frontmatter such as
`disable-model-invocation` and `argument-hint`.

Use the global Antigravity install when you want LRH skills available across
worktrees. Project-scope installs are intentionally checkout-local, so another
worktree will not see them unless it also has a project-scope install or the
global plugin is installed.

---

### 4. Extending for Other Assistants

Because LRH decouples canonical skill sources (`src/lrh/skills/`) from target-rendered copies, new agent targets (such as ChatGPT Skills or emerging open standards) can be added cleanly via the `lrh skills install --target <name>` CLI interface.

---

## Related Documentation

- [Keep skills up to date](keep-skills-up-to-date.md) — check status, diffs, and force-updates.
- [`lrh skills` CLI reference](../reference/cli/skills.md) — exact command behavior and target paths.
- [Agent skills config reference](../reference/schemas/agent-skills-config.md) — repository-local configuration schema (`project/agent_skills.yaml`).
- [Antigravity Interoperability Decision](../../project/memory/decisions/DEC-AGENT-SKILL-INTEROPERABILITY-ANTIGRAVITY.md) — architectural decision record.
