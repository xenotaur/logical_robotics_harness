# SKILL.md Frontmatter Field Reference

This document is a factual reference for the official SKILL.md frontmatter
fields recognised by Claude Code. Validated against the Claude Code skills
documentation (June 2026) and the prosoc `new-scenario` skill session.

---

## `name`

**Type:** string  
**Required:** no (defaults to the directory name under `.claude/skills/`)  

The display name shown in skill listings. For skills under `.claude/skills/<dir>/`,
the slash command comes from the **directory name**, not this field. `name` only
sets the command name for plugin root `SKILL.md` files.

Convention in this project: set `name` equal to the directory name for
clarity, even though it is not required.

```yaml
name: create-skill
```

---

## `description`

**Type:** string (scalar or block scalar `>`)  
**Required:** recommended  

Claude uses `description` to decide whether to auto-invoke the skill when
relevant content appears in a conversation — unless `disable-model-invocation`
is set. The combined `description` + `when_to_use` text is truncated at
1,536 characters in the skill listing. Write the description as a specific
summary of what the skill does and when to use it; put the key use case first.

```yaml
description: >
  Create a new project-local Claude Code skill following the LRH pattern.
  Use when the user wants to add a skill to this project...
```

---

## `when_to_use`

**Type:** string  
**Required:** no  

Additional context for when Claude should invoke the skill, such as trigger
phrases or example requests. Appended to `description` in the skill listing
and counts toward the 1,536-character combined cap.

```yaml
when_to_use: >
  Invoke when the user says "can we make a skill for X?" or asks to automate
  a recurring task.
```

---

## `argument-hint`

**Type:** string or list of strings  
**Required:** no  

Displayed to the user as a hint when they type `/<name>` in the Claude Code
interface. Use to communicate what arguments the skill expects.

```yaml
argument-hint: [skill-name]
# or
argument-hint: "<scenario-name> [--paper <path>]"
```

---

## `arguments`

**Type:** space-separated string or YAML list  
**Required:** no  

Named positional arguments for `$name` substitution in the skill content.
Names map to argument positions in order.

```yaml
arguments: [issue branch]
# $issue expands to the first argument, $branch to the second
```

---

## `disable-model-invocation`

**Type:** boolean  
**Required:** no (default: `false`)  

When `true`, the skill is never auto-invoked by Claude based on conversation
content. The user must explicitly type `/<name>` to run it. Also prevents
the skill from being preloaded into subagents.

When `false` or absent, Claude may invoke the skill automatically if the
conversation matches the `description`.

Use `true` for skills that write files, modify control-plane artifacts, or
should only run on explicit user intent.

```yaml
disable-model-invocation: true
```

---

## `user-invocable`

**Type:** boolean  
**Required:** no (default: `true`)  

When `false`, the skill is hidden from the `/` menu. Claude can still invoke
it automatically. Use for background knowledge that users should not run
directly (e.g. a `legacy-system-context` reference skill).

```yaml
user-invocable: false
```

---

## `allowed-tools`

**Type:** space- or comma-separated string, or YAML list  
**Required:** no  

Tools Claude can use without asking permission when this skill is active.
Does not restrict which tools are available — all tools remain callable.

```yaml
allowed-tools: Bash(git add *) Bash(git commit *) Bash(git status *)
```

---

## `disallowed-tools`

**Type:** space- or comma-separated string, or YAML list  
**Required:** no  

Tools removed from Claude's available pool while this skill is active.
The restriction clears when the user sends their next message.

```yaml
disallowed-tools: AskUserQuestion
```

---

## `model`

**Type:** string  
**Required:** no  

Model to use when this skill is active. The override applies for the rest of
the current turn only and is not saved to settings. Accepts the same values
as `/model`, or `inherit` to keep the active model.

```yaml
model: claude-opus-4-8
```

---

## `effort`

**Type:** string  
**Required:** no (default: inherits from session)  

Effort level when this skill is active. Options: `low`, `medium`, `high`,
`xhigh`, `max`; available levels depend on the model.

```yaml
effort: high
```

---

## `context`

**Type:** string  
**Required:** no  
**Valid values:** `fork`  

When set to `fork`, the skill runs in an isolated subagent context with its
own context window, separate from the main session history.

Use `fork` when:
- The skill performs many file reads that would pollute the main context.
- Skill execution is long-running and should not block the main session.

```yaml
context: fork
```

---

## `agent`

**Type:** string  
**Required:** no  

Which subagent type to use when `context: fork` is set. Specifies the agent
profile from the available subagent types list.

```yaml
context: fork
agent: claude-code-guide
```

---

## `hooks`

**Type:** mapping  
**Required:** no  

Hooks scoped to this skill's lifecycle. See the Claude Code hooks
documentation for the configuration format.

```yaml
hooks:
  PostToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "echo 'tool used'"
```

---

## `paths`

**Type:** comma-separated string or YAML list  
**Required:** no  

Glob patterns that limit when this skill is automatically activated. When set,
Claude loads the skill only when working with files matching the patterns.

```yaml
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
```

---

## `shell`

**Type:** string  
**Required:** no (default: `bash`)  

Shell to use for inline `` !`command` `` and ` ```! ` blocks in this skill.
Accepts `bash` or `powershell`. The `powershell` option requires
`CLAUDE_CODE_USE_POWERSHELL_TOOL=1`.

```yaml
shell: bash
```

---

## Unknown keys

Unknown frontmatter keys are silently ignored by Claude Code. For clarity and
forward-compatibility, do not add non-standard keys to SKILL.md frontmatter.
If you need to document metadata about a skill, put it in the body or in a
`references/` file.

---

## Minimum valid frontmatter

```yaml
---
name: my-skill
description: One sentence describing what this skill does and when to use it.
---
```

## Full frontmatter example

```yaml
---
name: create-skill
description: >
  Create a new project-local Claude Code skill following the LRH pattern.
  Use when the user wants to add a skill to this project, automate a
  recurring workflow, or capture domain knowledge for reuse.
disable-model-invocation: true
argument-hint: [skill-name]
---
```
