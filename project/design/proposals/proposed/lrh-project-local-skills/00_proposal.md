---
id: PROP-LRH-PROJECT-LOCAL-SKILLS
type: design_proposal
title: LRH Project-Local Skills — create-skill and lrh setup
status: proposed
created_on: 2026-06-21
updated_on: 2026-06-21
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
---

# LRH Project-Local Skills — `create-skill` and `lrh setup`

## Summary

This proposal introduces first-class support for distributing Claude Code
project-local skills through LRH. It proposes three coupled components:
(1) a `create-skill` Claude Code skill that guides users through creating
well-structured project-local skills following the LRH pattern; (2) a
`src/lrh/skills/` package directory that holds distributable LRH skills as
package data; and (3) a new `lrh setup` CLI command that installs LRH
skills to `~/.claude/skills/` so they are globally available in any project.

This proposal is documentation-only. No CLI implementation, packaging
change, or skill file is delivered in the proposal PR.

## Background and motivation

Claude Code (Anthropic's CLI for Claude) supports a filesystem-based skill
system: placing a `SKILL.md` file at `.claude/skills/<name>/SKILL.md` in a
project makes `/name` available as a slash command in any Claude Code session
rooted at or below that directory. Skills can carry domain knowledge in a
`references/` subdirectory, which Claude loads on demand. No manifest
registration or packaging step is needed for project-local use. Skills
committed to a repository are automatically shared with anyone who checks
out that repository and opens Claude Code.

This capability was validated in the prosoc social navigation scenario
repository (Francis et al., 2025), where a `new-scenario` skill was
implemented at `.claude/skills/new-scenario/` to guide Claude through
drafting P&G-compliant scenario cards. The skill ran successfully for the
Blind Corner scenario and was shipped in a PR. The session that produced
this experience also confirmed the following design constraints:

- Claude Code discovers skills from `.claude/skills/` automatically;
  no restart is needed unless the `.claude/skills/` directory itself is
  newly created in a session.
- A skill's `SKILL.md` body should be under ~500 lines; larger reference
  material belongs in `references/` subdirectory files, loaded on demand.
- The `disable-model-invocation: true` frontmatter key prevents Claude
  from auto-triggering a task skill when keywords appear in unrelated
  queries. It is required for skills whose invocation is intentional.
- Skills uploaded to the claude.ai Skills API must be packaged as `.skill`
  (zip) files and validated against stricter constraints (one SKILL.md per
  package, no nested SKILL.md files). Project-local skills bypass this;
  distribution via `lrh setup` also bypasses it.

LRH currently bootstraps projects via `lrh request bootstrap_project`, a
templated prompt that Claude follows to produce the `project/` directory
structure. That mechanism is the correct precedent for AI-assisted project
setup but does not address the skill distribution problem: skills live
outside any project's `project/` directory and require a separate
installation step to be globally available.

## Problem statement

Without a standard LRH mechanism:

- Each LRH project must independently invent and maintain skill structure
  and conventions, with no shared reference.
- Skills discovered in one project are not available in others without
  manual copying.
- There is no guided path for creating a new skill that follows LRH
  conventions (domain knowledge in `references/`, conservative
  confirm-before-write discipline, CLAUDE.md index entries).
- LRH cannot dogfood its own skill infrastructure because that
  infrastructure does not yet exist.

## Design goal

Define a minimal, conservative skill infrastructure that:

1. Provides a `create-skill` skill as the canonical way to add a new
   project-local skill to any LRH-managed project.
2. Establishes `src/lrh/skills/` as the home for distributable LRH skills.
3. Provides `lrh setup` as the one-time per-machine installation command
   that makes LRH skills globally available.
4. Follows LRH's own architectural principles: do less, preserve repository
   intent, explicit reporting over speculative modification.

## Proposed design

### Component 1: The `create-skill` skill

**Location in LRH:** `src/lrh/skills/create-skill/`

**Location after `lrh setup`:** `~/.claude/skills/create-skill/`

**Self-hosted copy:** `lrh/.claude/skills/create-skill/` (available when
working in the LRH repo itself, without needing `lrh setup`)

**File structure:**

```
create-skill/
├── SKILL.md
└── references/
    ├── lrh-skill-pattern.md    # the validated pattern from the prosoc session
    ├── frontmatter-guide.md    # official SKILL.md frontmatter fields and constraints
    └── worked-example.md       # new-scenario annotated as a reference implementation
```

**Frontmatter:**

```yaml
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
```

`disable-model-invocation: true` prevents Claude from auto-invoking this
skill when the user mentions "skill" in other contexts. Skill creation is
intentional.

**Execution steps (7-step):**

1. **Check for existing skill.** If `.claude/skills/<name>/` already exists,
   report and ask before proceeding. Never silently overwrite.

2. **Interview (5 questions):**
   - What should this skill do?
   - When should Claude invoke it automatically, if ever?
   - What arguments does the user pass?
   - Is there domain-specific knowledge that should live in `references/`?
   - Should it run inline or in a subagent (`context: fork`)?

3. **Research the project.** Read `CLAUDE.md`, existing skills, and
   relevant project files. Propose what domain knowledge to encode in
   `references/`. Show the proposed structure to the user before writing.

4. **User confirms.** If the user redirects or declines, adjust before
   writing. This gate is the key LRH addition relative to a generic skill
   creator.

5. **Write files.** `SKILL.md` + any `references/` files.

6. **Validate frontmatter.** Check that `name` is kebab-case, `description`
   is ≤1024 characters, no disallowed frontmatter keys are present, and
   `disable-model-invocation` is set appropriately.

7. **Update CLAUDE.md and report.** Add an index entry; note if
   `.claude/skills/` is newly created (Claude Code restart required for
   that session); offer handoff to `anthropic-skills:skill-creator` for
   evaluation and iteration.

**Relationship to `anthropic-skills:skill-creator`:** these are
complementary, not competing. `create-skill` handles initial structure
following LRH conventions. `skill-creator` handles evaluation, iteration,
and refinement once the first draft exists. Using both avoids duplicating
the evaluation/iteration logic inside `create-skill`.

### Component 2: `src/lrh/skills/` — distributable LRH skills

Skills intended for distribution through LRH live at `src/lrh/skills/`
inside the LRH package. This mirrors the established `src/lrh/assist/`
pattern for distributable templates and makes skills first-class package
assets.

Skills in `src/lrh/skills/` must be declared as package data in
`pyproject.toml` so `importlib.resources` can locate them after
`pipx install lrh`. The mechanism is the same one already used for
`src/lrh/assist/templates/`.

Skills for LRH's own development (self-hosting) live at
`lrh/.claude/skills/` and are auto-discovered by Claude Code when working
inside the LRH repository. They do not need to be installed.

The initial set contains only `create-skill`. Future skills (e.g., a
`lrh-work-item` skill for drafting work items, or a `lrh-proposal` skill
for drafting design proposals) may be added as separate proposals or work
items after `create-skill` is validated.

### Component 3: `lrh setup` — per-machine skill installation

**Purpose:** one-time initialization that makes LRH skills globally
available in any Claude Code project.

**What it does:**

```
lrh setup
  → Copies src/lrh/skills/* to ~/.claude/skills/
  → Reports what was installed / updated / skipped
  → Prints restart reminder if ~/.claude/skills/ was newly created
```

**Design principles:**

- **Idempotent.** Safe to rerun; updates existing skills, skips if
  identical. Running `lrh setup` after `pipx upgrade lrh` is the upgrade
  path for skills.
- **Non-destructive.** If `~/.claude/skills/<name>/` exists and differs
  from the LRH version (i.e., the user has customized it), report and ask
  before overwriting. In Phase 1, the simpler behavior is: skip with a
  warning that an update is available. `--force` overrides.
- **Transparent.** Prints exactly what it did: installed, updated,
  skipped, or warned.
- **Scoped.** Only installs skills from `src/lrh/skills/`. Does not touch
  other `~/.claude/` configuration.

**CLI surface:**

```bash
lrh setup              # install or update LRH skills globally
lrh setup --dry-run    # show what would be installed without writing
lrh setup --force      # overwrite even if user-modified
```

`--dry-run` follows the `lrh validate --dry-run` precedent in the codebase.

**Relationship to `lrh request bootstrap_project`:** these are distinct
operations. `bootstrap_project` creates the `project/` control-plane
directory structure inside a specific repository. `lrh setup` is a
per-machine global operation that installs skills to `~/.claude/skills/`.
Running `lrh setup` is the first step after `pipx install lrh`; running
`lrh request bootstrap_project` is the first step when setting up a new
project.

A future `lrh setup --project` variant could add a "LRH Skills" section to
the current project's `CLAUDE.md`, but that is explicitly deferred. Cross-
project CLAUDE.md mutation during a global setup command would violate the
harness/project separation.

## Design choices and tradeoffs

### Skill distribution: package data vs. separate package vs. download

| Option | Pro | Con |
|--------|-----|-----|
| Package data in `src/lrh/skills/` | Single install; versioned with package; same mechanism as templates | Skills bundled even if not used |
| Separate `lrh-skills` package | Decoupled versioning | Extra install step; fragmentation |
| Download on demand | Always current | Network dependency; fragile |

**Decision: package data.** Skills are small (a few KB each). Bundling them
with the package mirrors the `src/lrh/assist/templates/` precedent and
keeps the install surface minimal.

### Installation: copy vs. symlink

| Option | Pro | Con |
|--------|-----|-----|
| Copy to `~/.claude/skills/` | Simple; cross-platform; auditable | Updates require rerunning `lrh setup` |
| Symlink | Auto-updates on `pipx upgrade` | Breaks if package path changes; fragile on Windows |

**Decision: copy.** LRH targets cross-platform use including Windows, where
symlinks are more restricted. Copying is simple, auditable, and idempotent.
Users who want the latest skills after upgrading LRH run `lrh setup` again.

### On user-modified skills: overwrite vs. skip vs. warn

Phase 1 behavior: skip with a warning. A future phase may add diff-and-ask.
`--force` bypasses the check in all phases.

### Primary invocation: Claude Code skill vs. `lrh request` template

`create-skill` is primarily a Claude Code skill (`/create-skill`), not an
`lrh request` template. The skill has direct file system access, can read
the codebase, validate output, and update `CLAUDE.md` automatically — a
strict upgrade over a prompt template for this use case. An
`lrh request create-skill` template is not proposed; it would provide
lower-fidelity guidance without adding value over the skill.

## Staged implementation plan

This proposal is documentation-only. Implementation should proceed in
stages, each backed by a work item:

**Stage 1 — Core skill (`WI-SKILLS-CREATE-SKILL`)**

- `src/lrh/skills/create-skill/SKILL.md` + `references/` (3 files)
- `lrh/.claude/skills/create-skill/` — self-hosting copy
- `pyproject.toml` package data declaration for `src/lrh/skills/`

Stage 1 delivers immediate value with no new Python code and no new CLI
command. The skill is installable manually by copying to
`~/.claude/skills/` until Stage 2 ships.

**Stage 2 — `lrh setup` Phase 1 (`WI-SKILLS-LRH-SETUP`)**

- `src/lrh/cli/setup.py` — new CLI command
- `lrh setup`, `lrh setup --dry-run`, `lrh setup --force`
- Skip-with-warning behavior for user-modified skills
- Restart detection: prints reminder if `~/.claude/skills/` is newly created

**Stage 3 — Upgrade awareness (`WI-SKILLS-UPGRADE-AWARENESS`)**

- Installed version tracking
- Diff-and-ask on upgrade conflict
- `lrh skills status` subcommand

**Stage 4 — Project integration (deferred, `WI-SKILLS-PROJECT-INTEGRATION`)**

- `lrh setup --project` — add "LRH Skills" section to project `CLAUDE.md`
- Work item and skill index integration
- Scoped only to the current working project, not global

## Non-goals

- Do not force all LRH projects to use skills.
- Do not auto-install skills during `lrh request bootstrap_project`.
- Do not upload LRH skills to the claude.ai Skills API (cloud distribution
  adds API key requirements and is out of scope).
- Do not modify CLAUDE.md in any project during `lrh setup` (scoped to
  user-global `~/.claude/skills/` only in Phase 1).
- Do not implement skill evaluation or iteration logic in `create-skill`;
  defer to `anthropic-skills:skill-creator` for that.
- Do not add `lrh skills` as a top-level subcommand group in Stage 1 or 2;
  that surface may be introduced in Stage 3.

## Risks and mitigations

### Claude Code skill system changes

The skill filesystem discovery format is current as of Claude Code as used
in the 2026-06 prosoc session. If Anthropic changes the discovery mechanism,
`src/lrh/skills/` contents are still valid; only the `lrh setup` copy
target or the restart semantics may change.

Mitigation: Stage 1 (the skill itself) is independent of `lrh setup` and
remains valid regardless of how Anthropic evolves the distribution story.

### `create-skill` complexity growth

The risk is that `create-skill` accumulates logic for evaluation, testing,
and iteration that belongs in `skill-creator`.

Mitigation: the skill explicitly hands off to `anthropic-skills:skill-creator`
in Step 7. If a future `create-skill` version begins to duplicate that
tool's behavior, treat it as a signal to reduce `create-skill` scope.

### User confusion: project-local vs. global skills

Users may not understand why `/create-skill` is unavailable in a new
project where `lrh setup` has been run but the current project has no
`.claude/` directory.

Mitigation: `lrh setup` installs to `~/.claude/skills/`, which Claude Code
discovers globally. The skill is available in all projects after setup,
not just LRH projects.

## Acceptance criteria

This proposal can be considered effectively implemented when:

- `src/lrh/skills/create-skill/SKILL.md` and references exist and are
  valid (pass `quick_validate.py`);
- `lrh/.claude/skills/create-skill/` provides self-hosting access;
- `lrh setup` installs LRH skills to `~/.claude/skills/` idempotently;
- `lrh setup --dry-run` shows what would be installed without writing; and
- dogfooding confirms that `/create-skill` successfully guides creation of
  a second LRH skill (e.g., a `lrh-proposal` skill for drafting design
  proposals).

## Work items

Proposed work item seeds, if adopted:

- `WI-SKILLS-CREATE-SKILL` — implement `src/lrh/skills/create-skill/` and
  `lrh/.claude/skills/create-skill/` with package data declaration
- `WI-SKILLS-LRH-SETUP` — implement `lrh setup` Phase 1
- `WI-SKILLS-UPGRADE-AWARENESS` — Phase 2 upgrade-aware setup
- `WI-SKILLS-PROJECT-INTEGRATION` — Phase 3 project CLAUDE.md integration

## References

- Claude Code skills filesystem discovery: official Claude Code documentation
  (fetched 2026-06 session confirming auto-discovery from `.claude/skills/`).
- prosoc `new-scenario` skill: `xenotaur/prosoc` `.claude/skills/new-scenario/`
  — the reference implementation validated in the session that motivated
  this proposal.
- `bootstrap_project.md`: `src/lrh/assist/templates/request/bootstrap_project.md`
  — the closest LRH precedent for AI-assisted project setup and the
  conservative "do less, report explicitly" pattern this proposal adopts.
- `ci-capability-scaffolding.md`: nearest structural analog in the LRH
  proposal set — staged approach, human playbook before automation,
  deferred skill prototype.
- `safe-default-agentic-extra-packaging` (adopted): the packaging boundary
  and `lrh[agentic]` extra pattern that `lrh setup` must not cross.
  `lrh setup` installs skills to the user's Claude Code session, not into
  LRH's own execution model; it is a safe-default operation.
