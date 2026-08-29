---
name: lrh-config-skills
description: 'Inspect and set project/agent_skills.yaml install policy (sources, targets,
  scope) for lrh skills install. Presents whether the file exists, each editable field''s
  resolved effective value and provenance (from-config vs. conventional-default),
  and install.overwrite''s raw configured value (read-only, no conventional default)
  -- all in one read, via `lrh agent-skills status` -- before asking anything. May
  create project/agent_skills.yaml from scratch when absent, since no other mechanism
  in the codebase ever creates it. Use instead of manually reading the raw YAML and
  re-deriving CLI-over-config-over- default precedence by hand.

  '
---

# lrh-config-skills Skill

A thin, CLI-backed skill: `lrh agent-skills status` computes the full
read (see `src/lrh/agent_skills_status.py`), reusing
`src/lrh/skills/installer.py`'s existing `load_agent_skills_config`/
`resolve_agent_skills_install_plan` functions rather than
re-implementing their CLI-over-config-over-default precedence logic;
this skill presents that state and elicits confirmed changes to the 3
editable fields.

This is architecture Option C from `WI-SKILLS-LRH-CONFIG-GATES`
(`chain_defaults_status.py` / `lrh chain-defaults status` /
`/lrh-config-gates`), applied here to a different, already-built config
mechanism (`WI-SKILLS-REPO-CONFIG`) that never got a human-facing
status/confirm layer.

---

## Inputs

```
/lrh-config-skills
/lrh-config-skills --project-root <path>
```

`--project-root` defaults to the current directory. There is no other
argument -- this skill always starts from a full status read.

---

## Execution Steps

### Step 1 — Read status

```bash
lrh agent-skills status --project-root <project-root> --format json
```

Parse the structured output. Do not read `project/agent_skills.yaml`
directly or re-derive CLI-over-config-over-default precedence by hand --
`compute_status` already computed all of this in one read
(`src/lrh/agent_skills_status.py`), reusing `installer.py`'s own
functions rather than duplicating their logic.

### Step 2 — Present the full status table

<!-- GATE-DEFINITION -->
Before asking anything, show one table covering the entire status read:

- **Whether `project/agent_skills.yaml` exists** (`profile_exists`).
- **Editable fields** (`sources`, `targets`, `scope`): each field's
  effective resolved value and its provenance -- `from-config` (the file
  supplied this value) or `conventional-default` (no file, or the file
  didn't set this key).
- **Read-only field** (`install_overwrite`): its raw configured value, or
  `null`/`None` meaning "not set." Label this explicitly as read-only and
  explain why: `docs/reference/schemas/agent-skills-config.md` documents
  no conventional default for this field (unlike the other three), and
  `installer.py`'s data model doesn't expose a resolved value for it --
  only its raw configured value is ever shown, never an effective value.
  Never present this as something the user can change here.

This presentation itself is not a question -- it is shown in full before
Step 3 asks anything, matching the "propose, then confirm" shape every
other gate in this codebase follows.
<!-- /GATE-DEFINITION -->

### Step 3 — Offer field-value changes (its own confirm)

Ask the user whether they want to change any of the 3 editable fields
(`sources`, `targets`, `scope`). If not, stop -- there is nothing else
this skill does.

If yes, collect the desired new value(s). Valid values (per
`docs/reference/schemas/agent-skills-config.md`):

- `sources`: exactly one of `lrh-package`, `current-repo`, or a
  filesystem path
- `targets`: `all`, or one or more of `claude`, `codex`, `antigravity`
- `scope`: `user` or `project`

`install.overwrite` is never offered here or anywhere else in this
skill -- it is display-only (Step 2). A human who wants to set it edits
`project/agent_skills.yaml` by hand.

<!-- GATE-DEFINITION -->
**Confirm gate.** Show the proposed diff (old value → new value, per
field, or "creating project/agent_skills.yaml" if it doesn't exist yet)
and wait for explicit confirmation before writing anything. Never write
`project/agent_skills.yaml` on an inferred or assumed "yes."
<!-- /GATE-DEFINITION -->

Once confirmed, write `<project-root>/project/agent_skills.yaml` with
only the confirmed field changes. **Always write under `<project-root>`,
never a bare relative path** -- `<project-root>` may differ from the
current directory. If the file does not yet exist, create it fresh with
`schema_version: 1` plus only the confirmed fields -- do not invent
values for fields the user didn't confirm; an omitted field falls back
to its conventional default, which is the correct behavior per
`docs/reference/schemas/agent-skills-config.md`'s own precedence rules.
If it already exists, edit only the confirmed keys, leaving everything
else (including any `install.overwrite` value already present)
untouched. Then:

```bash
lrh validate --project-dir <project-root>/project
```

(`lrh validate` takes `--project-dir`, not `--project-root` -- point it
at `<project-root>/project`, not the bare repo root.)

Fix any error before proceeding to Step 4's commit.

### Step 4 — Commit and push

Determine the current branch, scoped to `<project-root>`:

```bash
git -C <project-root> branch --show-current
```

**If on a feature branch already tied to an open PR:** commit and push as
an additional commit to that branch -- `git -C <project-root> add ...`,
`git -C <project-root> commit ...`, `git -C <project-root> push`.

**If on `main` (or no open PR context):** pushing directly to `main`
always requires its own explicit confirmation, even for a small change --
this is a standing project constraint, not specific to this skill. Use
the main-worktree-lock tmp-branch workaround this codebase's other skills
use when the primary worktree has `main` checked out elsewhere, every
command scoped to `<project-root>`:

```bash
git -C <project-root> fetch origin main --quiet
git -C <project-root> checkout -b tmp-config-skills-<slug> origin/main
# edit + commit here, still under <project-root>
git -C <project-root> push origin tmp-config-skills-<slug>:main
git -C <project-root> checkout <original-branch>
```

State the exact commit(s) about to be pushed and wait for explicit
confirmation before the push, whichever path applies.

### Step 5 — Report

Report to the user:

- The full status table as it now stands (re-read after any change).
- Which fields changed, if any, and whether `project/agent_skills.yaml`
  was created fresh or edited.
- The commit(s) pushed, if any.

---

## What This Skill Does Not Do

- Does not change `lrh skills install`'s own precedence or loading logic
  -- `WI-SKILLS-REPO-CONFIG` already built and validated that; this skill
  only adds a read/confirm-write presentation layer on top.
- Does not let `install.overwrite` be edited through this skill at all,
  destructive or not -- it is display-only. A human who wants to set it
  edits `project/agent_skills.yaml` by hand. `--force` for an actual
  destructive install remains CLI-only.
- Does not decide this repo's own `agent_skills.yaml` policy on the
  user's behalf -- every change is proposed and confirmed, never inferred
  or applied by default.
- Does not require the file to already exist -- unlike `/lrh-config-gates`
  and `chain-defaults.yaml` (which is always created by the chain-
  authorization gate's own first-encounter flow), no other mechanism in
  this codebase ever creates `project/agent_skills.yaml`, so this skill
  is the one place a human can bring it into existence.
