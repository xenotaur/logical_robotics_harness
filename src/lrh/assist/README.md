# LRH Assist Request and Snapshot System

This directory provides assist workflows for request generation and context snapshots.

## Overview

The assist request system builds a **request document** by:

1. loading a template from package-owned resources under `src/lrh/assist/templates/request/` (installed as `lrh.assist.templates.request`)
2. computing or loading variable values (paths, file contents, identifiers, etc.)
3. rendering the template with those values

In practice, a “request” is the final filled-in markdown prompt you can hand to an AI coding assistant (for example, to improve test coverage, bootstrap a project control plane, or derive work items from an audit).

Template markdown files are bundled as package data in both editable installs (`pip install -e .`) and wheel installs (`pip install dist/*.whl`), so `lrh request ...` works outside a source checkout as long as LRH is installed.

Review/repair request templates keep a packaged protocol at `src/lrh/assist/templates/request/review_protocol.md` for install-time portability, while repository-root `REVIEWS.md` remains the maintenance source of truth.

## Key Concepts

- **Template**: A markdown file with placeholders like `{{TARGET_MODULE_GHA}}`.
- **Variables**: Values injected into placeholders. Some are computed (for example normalized target paths), others come from CLI flags or input files.
- **File input variables**: File-based inputs expose both path and content forms so templates can choose either concise references or inline bodies (for example `{{STYLE_GUIDE_PATH}}` and `{{STYLE_GUIDE_CONTENT}}`, while preserving legacy names like `{{STYLE_GUIDE_CONTEXT}}`).
- **Request generation**: Deterministic interpolation that replaces known placeholders and leaves unknown placeholders unchanged.
- **`RequestArgs`**: Planned typed argument model for Python callers.

## Template Override Resolution

Assist templates are resolved by logical POSIX-style names such as
`request/codex_prompt_from_work_item.md` and
`request/review_response.md`. LRH checks exact-name overrides only; it does not
merge templates, expand partials, or apply inheritance.

Resolution uses this deterministic precedence order:

1. an explicit template directory from `lrh request --template-dir` or Python
   callers
2. `LRH_TEMPLATE_DIR`, when set
3. project-local `.lrh/templates/` under the selected project root
4. user-global config templates under `$XDG_CONFIG_HOME/lrh/templates/`, or
   `~/.config/lrh/templates/` when `XDG_CONFIG_HOME` is unset
5. package-owned fallback templates under `lrh.assist.templates`

Filesystem overrides should mirror the package template layout. For example, a
project-local override for the review-response request template belongs at
`.lrh/templates/request/review_response.md`. To use an ad hoc override root for a
single command, run `lrh request --template-dir /path/to/templates ...`; that
directory should contain paths such as `request/review_response.md`. Package
fallback remains available when no override exists for the exact logical name.

Lightweight diagnostics are available without printing template contents:

```bash
lrh request templates list
lrh request templates where review_response
lrh request templates where request/review_response.md
lrh request templates --template-dir /path/to/templates where request/review_response.md
```

`list` shows each request template and the source LRH would use. `where` shows
the single selected source for a logical template name, distinguishing filesystem
overrides from package fallback.


### Semantic work-item audit template

`request/work_item_semantic_audit.md` is the conservative companion template for `lrh work-items audit`. The audit command reports deterministic lifecycle and traceability facts; the template asks a reviewer to compare those facts with work-item acceptance criteria, cite concrete repository evidence, and avoid optimistic closure when evidence is incomplete. Use it before resolving, abandoning, superseding, or splitting ambiguous proposed work items.

## Command Line Usage

### Preferred usage

Use the package CLI entry point:

```bash
lrh request <template_name> [target] [options]
```

Example after installation:

```bash
pip install lrh
cd /tmp
lrh request improve-coverage src/lrh/analysis/llm_extractor.py
```

Basic example:

```bash
lrh request improve-coverage src/lrh/analysis/llm_extractor.py
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

Project snapshots also include a compact `Design Proposals` section that
groups adopted (including legacy `accepted`) proposals by implementation
status, lists superseded proposals with their replacement IDs, and shows
concise `implemented_by` and `evidence` IDs for partial or implemented
designs. Snapshot reporting is best-effort: malformed files under
`project/design/proposals/` are reported in this section instead of aborting
the whole project snapshot.

Snapshot context packets include additive harness metadata in the Scope section
under a `Harness metadata:` label:

```text
Harness metadata:
harness:
  name: lrh
  version: <installed package version or unknown>
```

## Quick Usage Examples

```bash
lrh request --help
lrh request assess-repository --scope project
lrh request assess-repository --scope current_focus
lrh request assess-repository --scope work_item --target WI-0003
lrh request assess-continuous-integration-status --background-text "Assess CI feasibility for this repository."
lrh request implement-continuous-integration-workflow --background-file ci_assessment.md
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
lrh request work-items-from-audit \
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
lrh request prompt-from-work-item \
  --work-item project/work_items/active/WI-ASSIST-TEMPLATES-PACKAGING.md \
  --slug implement-wi-assist-templates-packaging \
  --out path/to/codex_prompt_request.md
```

Equivalent explicit form using the compatibility template name:

```bash
lrh request codex_prompt_from_work_item \
  --work-item-file path/to/work_item.md \
  --style-file STYLE.md > path/to/codex_prompt_request.md
```

Submit `path/to/codex_prompt_request.md` to Codex (or another coding assistant)
to produce and execute the implementation prompt.

Workflow summary:

```text
Work item Markdown
  -> lrh request prompt-from-work-item
  -> Codex Cloud prompt
  -> PR
  -> execution record
```

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

After opening the PR, create/update an execution record for traceability:

```bash
lrh prompt record-execution \
  --prompt-id "<PROMPT_ID>" \
  --work-item <WORK_ITEM_ID> \
  --slug <slug> \
  --status in_progress \
  --pr <pr_reference> \
  --commit <head_sha>
```

Fallback behavior for non-bootstrapped repositories:

- If `lrh` is unavailable but `PROMPTS.md` and `project/executions/` exist, write the execution record manually using repository conventions.
- If prompt workflow scaffolding is absent, report that execution recording was skipped because the repository is not bootstrapped yet.

### Notes

- Keep each selected work item small and independently reviewable.
- Keep human review in the loop at work-item selection and pre-merge review.
- If review finds scope drift, revise the work item or split into smaller follow-ups.

### 6) `review_response`

**Purpose**: Generate a Codex-style repair prompt for unresolved PR review comments.

**Inputs**:

- `template_name`: `review_response`
- `target`: PR URL (for example `https://github.com/octo/repo/pull/7`)

Behavior:

- Prepends a fixed repair preamble and separator line.
- Appends unresolved review threads in `lrh github unresolved` review format (including PR header and unresolved thread records).

Example:

```bash
lrh request review_response https://github.com/octo/repo/pull/7
```

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

## Request catalog and naming

`lrh request` resolves names through the package request catalog in
`src/lrh/assist/request_catalog.py`. Canonical user-facing request names are
hyphenated and verb-oriented. Existing template-oriented names remain supported
as compatibility aliases, so existing scripts can keep using names such as
`improve_coverage`, `assessment`, and `codex-prompt-from-work-item`.

Canonical mappings:

| Canonical name | Compatibility aliases | Template target |
| --- | --- | --- |
| `prompt-from-work-item` | `codex-prompt-from-work-item`, `codex_prompt_from_work_item` | `codex_prompt_from_work_item` |
| `review-pull-request-against-work-item` | `review-pr-against-work-item`, `pr-against-work-item`, `pr_against_work_item` | `pr_against_work_item` |
| `work-items-from-audit` | `work_items_from_audit` | `work_items_from_audit` |
| `assess-repository` | `assessment` | `assessment` |
| `bootstrap-project` | `bootstrap_project` | `bootstrap_project` |
| `assess-continuous-integration-status` | `assess-ci-status`, `ci-assess-status`, `ci_assess_status` | `ci_assess_status` |
| `implement-continuous-integration-workflow` | `implement-ci-workflow`, `ci-implement-workflow`, `ci_implement_workflow` | `ci_implement_workflow` |
| `improve-coverage` | `improve_coverage` | `improve_coverage` |
| `review-response` | `review_response` | `review_response` |

## Examples

### 1) `improve-coverage`

**Purpose**: Generate a tests-focused request for one module.

**Inputs**:

- request name: `improve-coverage` (legacy: `improve_coverage`)
- `target`: module path (for example `src/lrh/analysis/llm_extractor.py`)

Example:

```bash
lrh request improve-coverage src/lrh/analysis/llm_extractor.py
```

### 2) `bootstrap-project`

**Purpose**: Generate a project bootstrap request for a repository.

**Inputs**:

- request name: `bootstrap-project` (legacy: `bootstrap_project`)
- `--repo-name` (or target value)
- optional `--project-goal`, `--background-file`, `--project-type`, `--bootstrap-mode`

Example:

```bash
lrh request bootstrap-project \
  --repo-name lrh \
  --project-goal "Bootstrap LRH control files"
```

### 3) `work-items-from-audit`

**Purpose**: Turn an audit report into proposed work items.

**Inputs**:

- request name: `work-items-from-audit` (legacy: `work_items_from_audit`)
- `--audit-file` (required)
- `--style-file` (required)
- optional `--background-file` or `--background-text`

Example:

```bash
lrh request work-items-from-audit \
  --audit-file audits/style_audit_2026_04_10.md \
  --style-file STYLE.md
```

### 4) `prompt-from-work-item`

**Purpose**: Render an implementation prompt request for one approved work item.

**Inputs**:

- request name: `prompt-from-work-item` (legacy: `codex-prompt-from-work-item`, `codex_prompt_from_work_item`)
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
lrh request prompt-from-work-item \
  project/work_items/active/WI-ASSIST-TEMPLATES-PACKAGING.md \
  --style-file STYLE.md \
  --prompt-id "PROMPT(WI-ASSIST-TEMPLATES-PACKAGING:IMPLEMENT)[2026-05-14T00:00:00+00:00]" \
  > path/to/codex_prompt_request.md
lrh request codex_prompt_from_work_item project/work_items/proposed/WI-EXAMPLE.md
lrh request codex_prompt_from_work_item \
  --work-item-file project/work_items/proposed/WI-EXAMPLE.md \
  --style-file STYLE.md
```

### 5) `assess-continuous-integration-status`

**Purpose**: Produce a read-only CI feasibility assessment before migration.

**Inputs**:

- request name: `assess-continuous-integration-status` (legacy: `assess-ci-status`, `ci-assess-status`, `ci_assess_status`)
- optional `--background-file` or `--background-text`

Example:

```bash
lrh request assess-continuous-integration-status \
  --background-text "Assess whether this repository should get LRH-style Python CI."
```

### 6) `implement-continuous-integration-workflow`

**Purpose**: Produce an assessment-gated implementation request for CI migration.

**Inputs**:

- request name: `implement-continuous-integration-workflow` (legacy: `implement-ci-workflow`, `ci-implement-workflow`, `ci_implement_workflow`)
- optional `--background-file` or `--background-text`

Example:

```bash
lrh request implement-continuous-integration-workflow --background-file ci_assessment.md
```

## Validation Notes

- Some templates require specific arguments (for example `work-items-from-audit` requires both `--audit-file` and `--style-file`).
- `prompt-from-work-item` resolves a positional target only within work-item buckets (`proposed`, `active`, `resolved`, `abandoned`) and fails closed on ambiguous matches; use `--work-item-file` to disambiguate.
- Path-like positional targets for `prompt-from-work-item` (for example `project/work_items/active/WI-EXAMPLE.md`) are treated as authoritative file paths and fail fast if the file does not exist.
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
