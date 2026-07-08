# Your first LRH project

This tutorial walks through the smallest useful LRH control-plane experience: create a tiny `project/` directory, validate it, and generate a readable project snapshot.

It is intentionally small. You will not build a full roadmap, work-item tree, evidence set, or status report yet.

## What you will build

You will create a temporary repository-like directory with this shape:

```text
my-first-lrh-project/
  project/
    focus/
      current_focus.md
```

That single focus file is enough to show the current implemented validation path and to produce a project snapshot. Other control-plane areas such as principles, goals, roadmap, work items, evidence, and status can be added later.

## Prerequisites

You need:

- Python and LRH installed so the `lrh` command is available.
- A shell where you can create a temporary directory.

Check that LRH is on your path:

```bash
lrh --version
```

If you are working inside the LRH repository checkout, the project documentation uses these validation setup conventions:

```bash
scripts/version tools
```

## Step 1: Create a tiny project directory

Create a clean directory and move into it:

```bash
mkdir -p /tmp/my-first-lrh-project
cd /tmp/my-first-lrh-project
```

Create the minimal `project/focus/` directory:

```bash
mkdir -p project/focus
```

## Step 2: Add a current focus file

Create `project/focus/current_focus.md`:

```bash
cat > project/focus/current_focus.md <<'EOF'
---
id: FOCUS-LEARN-LRH
title: Learn LRH validation
status: active
priority: medium
---

# Learn LRH validation

Keep the first project small enough to validate and inspect.
EOF
```

This file has YAML frontmatter followed by Markdown body text. The frontmatter gives LRH structured fields to validate and load. The body remains readable project documentation.

## Step 3: Validate the project control directory

Run:

```bash
lrh validate --project-dir project
```

A successful run should look like this:

```text
Validation completed: 0 error(s), 0 warning(s)
```

If validation reports that `focus/current_focus.md` is missing, confirm that you are in `/tmp/my-first-lrh-project` and that the file path is exactly `project/focus/current_focus.md`.

## Step 4: Generate a project snapshot

`lrh snapshot` is currently supported for this scenario. Generate a project-wide Markdown context packet:

```bash
lrh snapshot project --project-root .
```

You should see a `# Project Context Packet` document. The `Current Focus` section should include:

```text
- id: FOCUS-LEARN-LRH
- title: Learn LRH validation
- status: active
- priority: medium
```

The snapshot may also say that optional areas such as `project/principles`, `project/goal/project_goal.md`, and `project/roadmap/roadmap.md` are not found. That is expected in this minimal tutorial; those areas are useful next steps, not required for this first validation pass.

To save the snapshot instead of only printing it:

```bash
lrh snapshot project --project-root . --output /tmp/my-first-lrh-project-snapshot.md
```

## What success looks like

You have succeeded when:

- `lrh validate --project-dir project` reports zero errors.
- `lrh snapshot project --project-root .` renders a Markdown context packet.
- The snapshot includes your `FOCUS-LEARN-LRH` focus.

At this point you have seen LRH's core source-vs-runtime pattern: human-readable Markdown under `project/` is loaded into structured LRH behavior by commands such as `validate` and `snapshot`.

## Where to go next

Next, try adding one concept at a time:

- Add durable principles under `project/principles/`.
- Add a project goal at `project/goal/project_goal.md`.
- Add a roadmap at `project/roadmap/roadmap.md`.
- Add work items under `project/work_items/active/` after reading the work-item examples in this repository.
- Read the CLI reference for [`lrh validate`](../reference/cli/validate.md) and [`lrh snapshot`](../reference/cli/snapshot.md).
- Read the explanation of the [control-plane model](../explanations/control-plane-model.md) to understand how the pieces fit together.
- If you use Claude Code, see [Keep skills up to date](../how-to/keep-skills-up-to-date.md) — installed `/lrh-*` skills are a copy and do not update automatically when LRH is upgraded.
