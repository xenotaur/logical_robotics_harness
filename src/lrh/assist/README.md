# LRH Assist Request and Snapshot System

This directory provides assist workflows for request generation and context snapshots.

## Overview

The assist request system builds a **request document** by:

1. loading a template from package-owned resources under `src/lrh/assist/templates/request/` (installed as `lrh.assist.templates.request`)
2. computing or loading variable values (paths, file contents, identifiers, etc.)
3. rendering the template with those values

In practice, a “request” is the final filled-in markdown prompt you can hand to an AI coding assistant (for example, to improve test coverage, bootstrap a project control plane, or derive work items from an audit).

Template markdown files are bundled as package data in both editable installs (`pip install -e .`) and wheel installs (`pip install dist/*.whl`), so `lrh request ...` works outside a source checkout as long as LRH is installed.

## Key Concepts

- **Template**: A markdown file with placeholders like `{{TARGET_MODULE_GHA}}`.
- **Variables**: Values injected into placeholders. Some are computed (for example normalized target paths), others come from CLI flags or input files.
- **File input variables**: File-based inputs expose both path and content forms so templates can choose either concise references or inline bodies (for example `{{STYLE_GUIDE_PATH}}` and `{{STYLE_GUIDE_CONTENT}}`, while preserving legacy names like `{{STYLE_GUIDE_CONTEXT}}`).
- **Request generation**: Deterministic interpolation that replaces known placeholders and leaves unknown placeholders unchanged.
- **`RequestArgs`**: Planned typed argument model for Python callers.

## Command Line Usage

### Preferred usage

Use the package CLI entry point:

```bash
lrh request <template_name> [target] [options]
```

Example after installation:

```bash
pip install logical-robotics-harness
cd /tmp
lrh request improve_coverage src/lrh/analysis/llm_extractor.py
```

Basic example:

```bash
lrh request improve_coverage src/lrh/analysis/llm_extractor.py
```

You can inspect supported options with:

```bash
lrh request --help
```

### Snapshot preferred usage

Use the package CLI entry point:

```bash
lrh snapshot <project|current_focus|work_item> [options]
```

Basic example:

```bash
lrh snapshot project --project-root .
```

Example from outside a repository root:

```bash
cd /tmp
lrh snapshot project --project-root /path/to/repository
```

You can inspect supported options with:

```bash
lrh snapshot --help
```

## Quick Usage Examples

```bash
lrh request --help
lrh request assessment --scope project
lrh request assessment --scope current_focus
lrh request assessment --scope work_item --target WI-0003
lrh snapshot --help
lrh snapshot work_item WI-0003 --project-root .
lrh survey --help
lrh survey src/lrh/assist --tests-root tests/assist_tests --format md
lrh survey src/lrh/assist --tests-root tests/assist_tests --format json
```

`lrh survey --format json` returns a stable machine-readable structure
(`schema_version: "1.0"`) intended as an audit precursor. It includes:

- survey/test roots (with tests-root inference flag)
- discovered Python source files and test files
- `pyproject.toml` presence and console script names (when present)
- README/Markdown docs under the scanned root
- per-file symbol inventory reports
- cross-platform CLI candidate detection for nested `cli.py` modules

## Golden Path Example: From Audit to Reviewed Change

This example shows one small end-to-end LRH-assisted flow:
starting from an audit, proposing work items, selecting one work item,
generating a Codex implementation prompt, then reviewing the resulting change.

### Step 1 — Start with an audit

Use an existing audit report (for example from your normal repo audit process).
In this flow, we assume you already have:

- `path/to/audit.md`
- `STYLE.md`

### Step 2 — Generate proposed work items

Render a work-item proposal request from the audit:

```bash
lrh request work_items_from_audit \
  --audit-file path/to/audit.md \
  --style-file STYLE.md > path/to/work_item_proposals_request.md
```

Submit the rendered request to your AI assistant and save the response as
`path/to/proposed_work_items.md`.

### Step 3 — Choose one work item (human decision)

A human reviewer selects one candidate item from `path/to/proposed_work_items.md`
and saves it as `path/to/work_item.md`.

This step is intentionally manual: LRH expects human judgment when prioritizing
and approving work.

### Step 4 — Generate a Codex implementation prompt

Render an implementation prompt request for the selected work item:

```bash
lrh request codex_prompt_from_work_item WI-ASSIST-TEMPLATES-PACKAGING \
  > path/to/codex_prompt_request.md
```

Equivalent explicit form:

```bash
lrh request codex_prompt_from_work_item \
  --work-item-file path/to/work_item.md \
  --style-file STYLE.md > path/to/codex_prompt_request.md
```

Submit `path/to/codex_prompt_request.md` to Codex (or another coding assistant)
to produce and execute the implementation prompt.

### Step 5 — Review the resulting patch against the work item

After implementation, review the proposed change against the same work item:

```bash
lrh request pr_against_work_item \
  --work-item-file path/to/work_item.md \
  --patch-file path/to/patch.diff \
  --style-file STYLE.md > path/to/pr_review_request.md
```

Submit `path/to/pr_review_request.md` to your reviewer assistant and use the
result to decide whether to merge, request fixes, or split follow-up work.

### Notes

- Keep each selected work item small and independently reviewable.
- Keep human review in the loop at work-item selection and pre-merge review.
- If review finds scope drift, revise the work item or split into smaller follow-ups.

## Python API Usage

`RequestArgs` and `generate_request(...)` are the intended end-user Python API for this module, but they are not yet implemented in the current codebase.

Planned usage shape:

```python
from lrh.assist.request_models import RequestArgs
from lrh.assist.request_service import generate_request

args = RequestArgs(
    template_name="improve_coverage",
    target="src/lrh/analysis/llm_extractor.py",
)

result = generate_request(args)
print(result)
```

The package CLI (`lrh request ...`) is preferred for interactive use.

## Examples

### 1) `improve_coverage`

**Purpose**: Generate a tests-focused request for one module.

**Inputs**:

- `template_name`: `improve_coverage`
- `target`: module path (for example `src/lrh/analysis/llm_extractor.py`)

Example:

```bash
lrh request improve_coverage src/lrh/analysis/llm_extractor.py
```

### 2) `bootstrap_project`

**Purpose**: Generate a project bootstrap request for a repository.

**Inputs**:

- `template_name`: `bootstrap_project`
- `--repo-name` (or target value)
- optional `--project-goal`, `--background-file`, `--project-type`, `--bootstrap-mode`

Example:

```bash
lrh request bootstrap_project \
  --repo-name logical_robotics_harness \
  --project-goal "Bootstrap LRH control files"
```

### 3) `work_items_from_audit`

**Purpose**: Turn an audit report into proposed work items.

**Inputs**:

- `template_name`: `work_items_from_audit`
- `--audit-file` (required)
- `--style-file` (required)
- optional `--background-file` or `--background-text`

Example:

```bash
lrh request work_items_from_audit \
  --audit-file audits/style_audit_2026_04_10.md \
  --style-file STYLE.md
```

### 4) `codex_prompt_from_work_item`

**Purpose**: Render an implementation prompt request for one approved work item.

**Inputs**:

- `template_name`: `codex_prompt_from_work_item`
- positional `target` (required unless `--work-item-file` is passed):
  - direct file path, or
  - work-item `id` from frontmatter, or
  - work-item filename stem in `project/work_items/{proposed,active,resolved,abandoned}/`
- `--style-file` (optional; defaults to `STYLE.md` when omitted)
- `--work-item-file` (optional explicit override; takes precedence over positional `target`)
- `--prompt-id` (optional explicit prompt ID; when omitted, LRH generates one from the
  work item ID + current timestamp)

Examples:

```bash
lrh request codex_prompt_from_work_item WI-ASSIST-TEMPLATES-PACKAGING
lrh request codex_prompt_from_work_item project/work_items/proposed/WI-EXAMPLE.md
lrh request codex_prompt_from_work_item \
  --work-item-file project/work_items/proposed/WI-EXAMPLE.md \
  --style-file STYLE.md
```

## Validation Notes

- Some templates require specific arguments (for example `work_items_from_audit` requires both `--audit-file` and `--style-file`).
- `codex_prompt_from_work_item` resolves a positional target only within work-item buckets (`proposed`, `active`, `resolved`, `abandoned`) and fails closed on ambiguous matches; use `--work-item-file` to disambiguate.
- Path-like positional targets for `codex_prompt_from_work_item` (for example `project/work_items/active/WI-EXAMPLE.md`) are treated as authoritative file paths and fail fast if the file does not exist.
- Invalid argument combinations are reported as CLI errors with a non-zero exit status.
- Missing input/template files are reported as file errors with a non-zero exit status.

## Design Notes

- The `lrh` CLI commands are intentionally thin wrappers around assist modules.
- Core request behavior belongs in `src/lrh/assist/`.
- Core sourcetree survey behavior belongs in `src/lrh/assist/sourcetree_surveyor.py`.
- Templates define most request behavior and output structure.

## Status / Roadmap

- **Request CLI**: `lrh request ...`
- **Snapshot CLI**: `lrh snapshot ...`
- **Survey CLI**: `lrh survey ...` (delegates to `src/lrh/assist/sourcetree_surveyor.py`)
- **Survey JSON contract**: stable structured inventory output for audit/context follow-on tooling.
- **Package sourcetree module**: also runnable with `python -m lrh.assist.sourcetree_surveyor --help`.
- **Planned request API**: first-class Python API (`RequestArgs` + `generate_request(...)`).
- **Packaging/install smoke checks**: use `scripts/smoke_assist_install` to validate installed `lrh request` and `lrh snapshot` behavior from a non-repo working directory.
- **Next follow-on item**: handle sourcetree capability expansion separately.
