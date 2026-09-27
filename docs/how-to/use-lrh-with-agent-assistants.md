# Use LRH with AI Agent Assistants

## Purpose

Use this guide to set up and operate Logical Robotics Harness (LRH) skills across different AI agent assistants, including **Claude Code**, the **Codex App**, **Google Antigravity**, and **ChatGPT Online**.

LRH maintains a single canonical skill source (`src/lrh/skills/`) that can be rendered or discovered across multiple agent environments.

## Prerequisites

- LRH installed so the `lrh` command is available.
- An LRH-managed project repository (or a repository configured with
  `project/agent_skills.yaml`). Use the `/lrh-config-skills` LRH skill to
  set this file up without hand-editing YAML (`lrh agent-skills status`
  inspects the current resolved defaults but does not write the file) —
  see the
  [agent skills config schema](../reference/schemas/agent-skills-config.md).

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

Project scope changes where LRH writes the rendered skills; it does not, by
itself, change which source tree LRH copies from. LRH maintainers checking this
repository's canonical source checkout should add `--source current-repo`, or
set the equivalent source default in `project/agent_skills.yaml`.

Restart Codex after creating `~/.agents/skills/` for the first time or after
updating global Codex skills so the app re-discovers the installed skills.

Use global installs when you want skills to appear across unrelated repositories
or worktrees. Use project-scope installs when you want a checkout-specific
destination; combine project scope with `--source current-repo` or repo config
when the installed copy should reflect that checkout's current source.

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

### 4. ChatGPT Online

ChatGPT online is a **hosted** assistant: there is no local skills directory to
install into, so `chatgpt` is not an `lrh skills install` target. Instead,
export upload bundles and upload them to ChatGPT yourself.

#### Export
Export one deterministic ZIP per skill into a directory of your choice:

```bash
# Export the default set (all public skills except manual-only ones)
lrh skills export --target chatgpt --out ./chatgpt-skills

# Export specific skills; repeat --skill as needed
lrh skills export --target chatgpt --out ./chatgpt-skills --skill lrh-design --skill lrh-work-item
```

Each `<skill-name>.zip` contains exactly one top-level `<skill-name>/` folder
with `SKILL.md` plus any `references/`, `scripts/`, and `assets/` from the
canonical source. `--source` works as it does for `install`. The export never
modifies canonical sources or local Claude, Codex, or Antigravity installs, and
the bundles are generated outputs, not a new source of truth.

#### Upload and Invocation
Upload each ZIP through ChatGPT's skills upload flow; see OpenAI's
[Skills in ChatGPT](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)
help article for the current steps. Once uploaded, invoke a skill explicitly
with `@skill-name` (for example `@lrh-design`), or let ChatGPT select it
automatically when your request matches the skill's `description`.

#### What changes in the bundle
- Frontmatter is reduced to portable fields (`name`, `description`, `license`,
  `compatibility`, `metadata`); agent-specific keys such as `argument-hint` and
  `when_to_use` are dropped and reported.
- Codex metadata (`agents/`) is not bundled.
- Skill instructions are exported unchanged.

#### Capability limits
Skill instructions do not grant tools. Most LRH workflows run local `git`, the
GitHub `gh` CLI, the `lrh` CLI, or other shell commands, which ChatGPT online
cannot run. The export reports these as notices rather than rewriting the
workflow; such skills remain useful for planning and drafting, but steps that
need local tools must be carried out elsewhere. Instruction-centric skills such
as `lrh-design`, `lrh-proposal`, and `lrh-work-item` are the best fit.

Manual-only skills (`lrh-land`, `lrh-execute`, `lrh-confirm-fixes`,
`lrh-self-review`, `lrh-codex-export`) are left out of the default export.
ChatGPT has no known equivalent of their explicit-only invocation policy, so an
uploaded copy could be selected automatically. Export one only by naming it
with `--skill`, which also prints a manual-only notice.

The export checks the upload limits documented by the OpenAI Skills API guide
(50 MB per ZIP, 500 files, 25 MB per uncompressed file); ChatGPT's own limits
may differ.

#### Updating
Bundles do not update themselves. When canonical skills change (for example
after upgrading LRH), re-run `lrh skills export` and re-upload the changed
bundles. On the same machine and toolchain, identical sources produce
byte-identical ZIPs, so an unchanged file means an unchanged skill.

---

### 5. Extending for Other Assistants

Because LRH decouples canonical skill sources (`src/lrh/skills/`) from
target-rendered copies, new assistants can be added cleanly: local assistants
that discover skills on disk get an `lrh skills install --target <name>`
target, while hosted assistants that take uploads get an
`lrh skills export --target <name>` target.

---

## Related Documentation

- [Keep skills up to date](keep-skills-up-to-date.md) — check status, diffs, and force-updates.
- [`lrh skills` CLI reference](../reference/cli/skills.md) — exact command behavior and target paths.
- [Agent skills config reference](../reference/schemas/agent-skills-config.md) — repository-local configuration schema (`project/agent_skills.yaml`).
- [Antigravity Interoperability Decision](../../project/memory/decisions/DEC-AGENT-SKILL-INTEROPERABILITY-ANTIGRAVITY.md) — architectural decision record.
