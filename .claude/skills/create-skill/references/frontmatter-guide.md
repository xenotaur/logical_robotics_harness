# SKILL.md Frontmatter Field Reference

This document is a factual reference for the official SKILL.md frontmatter
fields recognised by Claude Code. Validated against Claude Code as used in
the prosoc `new-scenario` skill session (June 2026).

---

## `name`

**Type:** string  
**Required:** yes  
**Constraints:** kebab-case (lowercase letters `a-z`, digits `0-9`, hyphens `-`).
No spaces, underscores, or uppercase letters.

The value of `name` becomes the slash command. A skill with `name: my-skill`
is invoked as `/my-skill`.

The `name` must match the directory name under `.claude/skills/`. Mismatches
cause discovery failures.

```yaml
name: create-skill
```

---

## `description`

**Type:** string (scalar or block scalar `>`)  
**Required:** yes  
**Constraints:** ≤ 1024 characters total (including whitespace after YAML
processing). Longer descriptions are silently truncated or cause errors.

Claude uses `description` to decide whether to auto-invoke the skill when
relevant content appears in a conversation — unless `disable-model-invocation`
is set. Write the description as a specific, one-paragraph summary of what
the skill does and when to use it.

```yaml
description: >
  Create a new project-local Claude Code skill following the LRH pattern.
  Use when the user wants to add a skill to this project...
```

---

## `disable-model-invocation`

**Type:** boolean  
**Required:** no (default: `false`)

When `true`, the skill is never auto-invoked by Claude based on conversation
content. The user must explicitly type `/<name>` to run it.

When `false` or absent, Claude may invoke the skill automatically if the
conversation matches the `description`.

Use `true` for skills that write files, modify control-plane artifacts, or
should only run on explicit user intent.

```yaml
disable-model-invocation: true
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

## `context`

**Type:** string  
**Required:** no  
**Valid values:** `fork`

When set to `fork`, the skill runs in an isolated subagent context. The
subagent has its own context window and does not share conversation history
with the main session.

Use `fork` when:
- The skill performs many file reads that would pollute the main context.
- Skill execution is long-running and should not block the main session.
- The skill's intermediate steps should not be visible in the main transcript.

```yaml
context: fork
```

---

## Unknown keys

Unknown frontmatter keys are silently ignored by Claude Code. However, for
clarity and forward-compatibility, do not add non-standard keys to SKILL.md
frontmatter. If you need to document metadata about a skill, put it in the
body or in a `references/` file.

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
