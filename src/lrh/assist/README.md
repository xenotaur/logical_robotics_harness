# LRH Assist Request and Snapshot System

This directory provides assist workflows for request generation and project-context snapshots.

## Overview

The assist request system builds a **request document** by:

1. loading a template from `scripts/aiprog/templates/request/`
2. computing or loading variable values (paths, file contents, identifiers, etc.)
3. rendering the template with those values

In practice, a “request” is the final filled-in markdown prompt you can hand to an AI coding assistant (for example, to improve test coverage, bootstrap a project control plane, or derive work items from an audit).

## Key Concepts

- **Template**: A markdown file with placeholders like `{{TARGET_MODULE_GHA}}`.
- **Variables**: Values injected into placeholders. Some are computed (for example normalized target paths), others come from CLI flags or input files.
- **Request generation**: Deterministic interpolation that replaces known placeholders and leaves unknown placeholders unchanged.
- **`RequestArgs`**: Planned typed argument model for Python callers.

## Command Line Usage

### Preferred usage

Use the package CLI entry point:

```bash
lrh request <template_name> [target] [options]
```

Basic example:

```bash
lrh request improve_coverage src/lrh/analysis/llm_extractor.py
```

You can inspect supported options with:

```bash
lrh request --help
```

### Compatibility usage

The script interface is still supported as a **legacy compatibility path**:

```bash
python scripts/aiprog/request.py <template_name> [target] [options]
```

Prefer `lrh request ...` for normal usage. The legacy script path may be removed in a future cleanup after migration.

### Snapshot preferred usage

Use the package CLI entry point:

```bash
lrh snapshot <project|current_focus|work_item> [options]
```

Basic example:

```bash
lrh snapshot project --project-root .
```

You can inspect supported options with:

```bash
lrh snapshot --help
```

### Snapshot compatibility usage

The script interface is still supported as a **legacy compatibility path**:

```bash
python scripts/aiprog/snapshot.py <project|current_focus|work_item> [options]
```

Prefer `lrh snapshot ...` for normal usage. The legacy script path may be removed in a future cleanup after migration.

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

## Validation Notes

- Some templates require specific arguments (for example `work_items_from_audit` requires both `--audit-file` and `--style-file`).
- Invalid argument combinations are reported as CLI errors with non-zero exit status.
- Missing input/template files are reported as file errors.

## Design Notes

- The CLI script is intentionally thin.
- Core request behavior belongs in `src/lrh/assist/`.
- Templates define most request behavior and output structure.

## Status / Roadmap

- **Current preferred request CLI**: `lrh request ...`
- **Current preferred snapshot CLI**: `lrh snapshot ...`
- **Legacy compatibility request CLI**: `python scripts/aiprog/request.py ...`
- **Legacy compatibility snapshot CLI**: `python scripts/aiprog/snapshot.py ...`
- **Deprecation guidance**: migrate scripted usage to `lrh request ...` / `lrh snapshot ...` before legacy script removal.
- **Planned request API**: first-class Python API (`RequestArgs` + `generate_request(...)`).
