---
name: create-skill
description: >
  Create a new project-local Claude Code skill following the LRH pattern.
  Use when the user wants to add a skill to this project, automate a
  recurring workflow, capture domain knowledge for reuse, or asks
  "can we make a skill for X?" Produces SKILL.md and references/ under
  .claude/skills/<name>/ and adds an index entry to CLAUDE.md.
disable-model-invocation: true
argument-hint: [skill-name]
---

# create-skill Skill

This skill creates a new project-local Claude Code skill following LRH
conventions: structured frontmatter, numbered execution steps, domain
knowledge in `references/`, a quality checklist, and a mandatory
confirm-before-write gate. All output is shown to the user for review
before any files are written.

---

## Inputs

The user provides a skill name as the argument to `/create-skill`. Example:

```
/create-skill lrh-work-item
```

The name must be kebab-case (lowercase letters, digits, and hyphens only).
If the name is not provided, ask for it before proceeding.

---

## Reference Knowledge

Load these before running any step:

1. **`references/lrh-skill-pattern.md`** — LRH skill structure pattern:
   required frontmatter, recommended body sections, size constraints,
   `disable-model-invocation` guidance, and the confirm-before-write rule.
   Read this to understand what a well-formed LRH skill looks like.

2. **`references/frontmatter-guide.md`** — Official SKILL.md frontmatter
   field reference. Read this to know which fields are valid, their types,
   and their constraints (especially the 1024-character description limit).

3. **`references/worked-example.md`** — The `new-scenario` skill from the
   prosoc project, annotated as a reference implementation. Read this to
   see how the LRH pattern applies in a real skill.

---

## Execution Steps

Work through these steps in order. Do not skip the confirmation gate (Step 4).

### 1. Check for existing skill

List `.claude/skills/` to see whether `<name>/` already exists.

If the directory exists:
- Report this to the user.
- Ask whether to overwrite, extend, or abort.
- Do not silently overwrite existing work.

If `.claude/skills/` does not exist, note that it will be created and that
a Claude Code session restart will be needed to discover skills in the
current session.

### 2. Interview

Ask the user these five questions. Collect all answers before proceeding.

1. **Purpose:** What should this skill do? Describe it in one sentence
   suitable for the frontmatter `description` field.

2. **Invocation:** Should Claude invoke this skill automatically when
   relevant keywords appear in conversation, or should it only run when
   the user explicitly types `/<name>`?
   (Answer determines whether `disable-model-invocation: true` is needed.)

3. **Arguments:** What arguments does the user pass when invoking the skill?
   Include a usage example.

4. **Reference knowledge:** What domain-specific knowledge should live in
   `references/`? Name each file and describe its purpose. If the skill is
   simple enough to need no references, say so.

5. **Execution context:** Should the skill run inline in the current
   conversation, or in a subagent with an isolated context (`context: fork`)?
   Use `fork` when the skill performs many file reads that would pollute the
   main conversation context.

### 3. Research the project

Read the following before proposing the skill structure:

- `CLAUDE.md` (if it exists) — understand existing conventions and the
  current skills index.
- `.claude/skills/` contents — note naming patterns and any similar skills
  that this new skill should complement or supersede.
- Any project files directly relevant to the skill's domain (e.g., schema
  files, template files, style guides).

Then propose:

- The exact frontmatter (name, description, disable-model-invocation,
  argument-hint, context if needed).
- The body section outline (Inputs, Reference Knowledge, Execution Steps,
  Quality Checklist, What This Skill Does Not Do).
- The list of `references/` files, each with a one-line description of
  its purpose.

Present this proposed structure to the user before writing anything.

### 4. User confirms

Show the user the proposed structure from Step 3 in a readable summary.

Wait for explicit confirmation before writing any files.

If the user redirects or declines, adjust the proposal and show it again.
Do not skip this gate — it is the key LRH addition that prevents
over-specified or incorrectly-scoped skills from being written to disk.

### 5. Write files

Create the following under `.claude/skills/<name>/`:

- **`SKILL.md`** — frontmatter from Step 4, body following the LRH pattern
  from `references/lrh-skill-pattern.md`. Each execution step should have
  a numbered heading and concrete instructions. End with a quality checklist
  and a "What This Skill Does Not Do" section.

- **`references/<file>.md`** — one file per reference item from Step 4.
  Keep reference files factual and load-on-demand; do not repeat content
  that is already in `SKILL.md`.

If `.claude/skills/` or `.claude/skills/<name>/` do not exist, create them.

### 6. Validate frontmatter

After writing, check these conditions. Fix any failure before proceeding.

- `name` matches the directory name and is kebab-case.
- `description` is ≤ 1024 characters (count them).
- `disable-model-invocation` is present and reflects the answer from Step 2.
- `argument-hint` is present when the skill takes arguments.
- No unknown keys are present (valid keys: `name`, `description`,
  `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`,
  `user-invocable`, `allowed-tools`, `disallowed-tools`, `model`, `effort`,
  `context`, `agent`, `hooks`, `paths`, `shell`).

### 7. Update CLAUDE.md and report

**CLAUDE.md update:**

- If `CLAUDE.md` exists: add or update a `## Skills` section with a bullet
  for the new skill: `` - `/<name>` — one-line description ``.
- If `CLAUDE.md` does not exist: create a minimal stub containing only a
  `## Skills` section with the new skill entry. Do not invent other content.

**Report to the user:**

- What files were created and where.
- What each `references/` file contains and when it will be loaded.
- Whether `.claude/skills/` was newly created (restart required).
- Any caveats or judgment calls made during generation.
- Whether the user would like to invoke `anthropic-skills:skill-creator`
  to evaluate and iterate on the new skill.

---

## Quality Checklist

Before reporting completion, verify:

- [ ] `.claude/skills/<name>/SKILL.md` exists with valid YAML frontmatter
- [ ] `name` is kebab-case and matches the directory name
- [ ] `description` is ≤ 1024 characters
- [ ] `disable-model-invocation` reflects the intended invocation mode
- [ ] All proposed `references/` files exist and contain substantive content
- [ ] The skill body includes: Inputs, Reference Knowledge, Execution Steps,
      Quality Checklist, What This Skill Does Not Do
- [ ] The confirm-before-write gate (Step 4) was honoured
- [ ] `CLAUDE.md` has been updated with a skills index entry

---

## What This Skill Does Not Do

- Does not evaluate skill quality or run evals — hand off to
  `anthropic-skills:skill-creator` for evaluation and iteration.
- Does not install skills globally to `~/.claude/skills/` — that requires
  `lrh setup` (not yet implemented).
- Does not create `src/lrh/skills/` package copies — those must be added
  manually as a separate step for LRH distribution (see `CONTRIBUTING.md`).
- Does not modify existing skills — only creates new ones.
- Does not create a full `CLAUDE.md` — only adds or updates the `## Skills`
  section; broader project CLAUDE.md content is a separate concern.
