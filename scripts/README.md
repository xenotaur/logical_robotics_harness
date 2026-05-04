# LRH Development Scripts

This directory contains utility scripts for development, testing, and maintenance of the LRH 
package. All scripts are designed to be executed from the repository root of the 
logical_robotics_harness project.

## Usage

Execute any script from the repository root:
```bash
scripts/<script_name>
```

## Available Scripts

### Build & Distribution

#### `build`
Builds the LRH package using Python's build module.

```bash
scripts/build
```

**Requirements:**
- run `scripts/develop` so development dependencies (including the `build` frontend) are installed

**Output:** Creates distribution files in `dist/` directory.

#### `clean`
Removes conservative packaging build artifacts to ensure a clean state.

```bash
scripts/clean
scripts/clean --dry-run
scripts/clean --help
```

**Removes:**
- `build/` directory
- `dist/` directory
- `lrh.egg-info/` directory

#### `release-smoke`
Builds LRH from a clean artifact state and validates installed-wheel behavior in an isolated temporary venv.

```bash
scripts/release-smoke
scripts/release-smoke v0.2.2
scripts/release-smoke --preserve v0.2.2
scripts/release-smoke v0.2.2 --diagnose
```

**Checks:**
- runs `scripts/clean`
- runs `scripts/build`
- installs exactly one wheel from `dist/`
- validates installed `lrh --version`
- validates installed `lrh snapshot --help`

Use `--diagnose` (for example, `scripts/release-smoke v0.2.2 --diagnose`) to print pre-install temporary-venv isolation diagnostics when investigating release-smoke package-visibility warnings. Diagnostic mode does not change default pass/fail behavior.

Use `scripts/sandbox` for HOME/XDG workspace isolation. Use `scripts/release-smoke` for installed-wheel release validation.

#### `publish`
Publishes the LRH package to PyPI using twine.

```bash
scripts/publish
```

**Requirements:**
- `pip install twine`
- Must run `scripts/build` first

**Note:** Currently disabled for safety until LRH is more thoroughly tested.

### Development

#### `adapters/github`
Fetches GitHub pull request review feedback through the GitHub CLI.

```bash
scripts/adapters/github unresolved https://github.com/OWNER/REPO/pull/123
scripts/adapters/github pull threads --state all OWNER/REPO 123
scripts/adapters/github pull comments --state unresolved OWNER/REPO 123
scripts/adapters/github pull reviews OWNER/REPO 123
```

Review feedback defaults to `--state unresolved` for `threads` and `comments`.
Use `--state all` when you need a complete dump. `comments` combines top-level
issue comments with review comments whose thread state matches the selected
filter; submitted review summaries are available as `reviews`. The older
`submitted` spelling remains accepted as an alias for `reviews`.

#### `sandbox`
Runs LRH commands in an **isolated developer sandbox** with temporary HOME/XDG/TMP paths.
This is for behavioral testing and reproducibility, **not** OS-level security sandboxing.

Interactive mode (preserved by default for inspection):

```bash
scripts/sandbox
```

Non-interactive command passthrough (recommended for CI/agent smoke checks):

```bash
scripts/sandbox --cleanup -- python -m lrh.cli.main meta init --mode hybrid
scripts/sandbox --cleanup -- python -m lrh.cli.main meta where
```

Cleanup/preserve behavior:
- default: preserve sandbox directory and print its path
- `--cleanup`: remove sandbox directory on exit
- `--preserve`: explicitly preserve sandbox directory on exit

#### `develop`
Installs LRH in development mode for active development.

```bash
scripts/develop
```

This is the canonical LRH editable development install entrypoint. It installs the package in editable mode with constrained development dependencies so source changes are reflected without reinstalling while standard development tools are available.

#### `update`
Updates the conda environment specification file.

```bash
scripts/update
```

**Output:** Updates `environment.yml` with current conda environment dependencies (excludes name and prefix).

#### `version`
Provides LRH version and release workflow helpers.

```bash
scripts/version
scripts/version tools
scripts/version verify [tag]
scripts/version tag <tag>
scripts/version push <tag>
```

LRH package versions are derived from Git tags via `setuptools-scm`; use `vMAJOR.MINOR.PATCH` tags (for example, `v0.2.2`).

Subcommands:
- default (`scripts/version`): prints `lrh <version>` from package metadata
- `tools`: prints versions for LRH CLI, Python, lint/format tools, and environment managers
- `verify [tag]`: validates an optional tag name, requires a clean working tree, and runs:
  - `scripts/lint`
  - `scripts/format --check`
  - `scripts/test`
- `tag <tag>`: idempotently creates a local tag at `HEAD` after verification
- `push <tag>`: idempotently and safely pushes an existing local tag to `origin`

#### `check-workflows`
Validates YAML syntax for GitHub Actions workflow files under `.github/workflows/`.

```bash
scripts/check-workflows
```

Prints `OK: <path>` for valid workflow files and `ERROR: <path>: <message>` for parse failures, then exits nonzero if any file is invalid.

Deeper GitHub Actions semantic linting (for example `actionlint`) is intentionally deferred.

### Code Quality

#### `format`
Formats Python code using the Black formatter.

```bash
scripts/format
```

**Applies formatting to:**
- `src/lrh/` directory
- `tests/` directory
- `scripts/aiprog/` directory

---

#### `lint`
Runs linting and formatting checks.

```bash
scripts/lint [--fix] [--extra] [paths...]
```

By default, this is a **fast check** intended for frequent use during development and CI.

**Default checks:**
- Ruff linting (base rule set)
- Black formatting (check-only, no modifications)

**Targets (default):**
- `src/lrh/`
- `tests/`
- `scripts/aiprog/`

You may optionally specify paths:

```bash
scripts/lint src/lrh/gatherers/downloaders.py
```

---

#### `--fix`
Automatically fixes issues where possible.

```bash
scripts/lint --fix
```

**Applies:**
- Ruff auto-fixes (`ruff check --fix`)
- Black formatting (in-place)

---

#### `--extra`
Runs additional, more comprehensive checks.

```bash
scripts/lint --extra
```

**Adds:**
- Extended Ruff rule set (including docstrings, bugbear, simplifications, etc.)
- Pylint checks
- Pyright static analysis (type checking, import resolution)

These checks are **slower and more strict**, and are recommended for:
- Pre-PR validation
- Deep code quality review
- Investigating editor warnings (VS Code / Pylance / Pylint)

---

#### Combined usage

```bash
scripts/lint --fix --extra
```

- Fixes what can be fixed
- Runs extended checks (reported but do not block fixes)

---

#### Notes

- The default `lint` command is designed to be **fast and quiet when clean**.
- `--extra` enables checks similar to those surfaced in VS Code (Pylance, Pylint).
- Ruff remains the primary linter; Pylint and Pyright provide additional perspectives.
- Black is the sole source of truth for formatting.


### Prompt workflow helpers

#### `prompts/label-prompt`
Generates a prompt ID and suggested execution-record path.

```bash
scripts/prompts/label-prompt --work-item WI-META-CLI-MVP --slug register-implementation
scripts/prompts/label-prompt --slug register-audit
```

#### `prompts/record-execution`
Generates an execution-record Markdown file under `project/executions/` (or an alternate output root).

```bash
scripts/prompts/record-execution \
  --prompt-id "PROMPT(AD_HOC:REGISTER_AUDIT)[2026-04-24T16:30:00-04:00]" \
  --slug register-audit \
  --status planned
```

See `PROMPTS.md` and `scripts/prompts/README.md` for details.

### Testing

#### `test`
Runs the test suite using Python's `unittest` framework.

```bash
scripts/test [target]
```

**Default behavior (no arguments):**
- Discovers and runs all tests in the `tests/` directory
- Matches files with pattern `*_test.py`

```bash
scripts/test
```

**Targeted test execution:**

The `test` script also supports running a subset of tests by passing a target. The target can be:

- A **directory**
- A **test file**
- A **dotted module path**
- A **specific test class or method**

**Examples:**

_Run all tests in a subdirectory:_
```bash
scripts/test tests/gatherers
```

_Run a single test file:_
```bash
scripts/test tests/gatherers/downloaders_test.py
```

_Run a module (dotted path):_
```bash
scripts/test tests.gatherers.downloaders_test
```

_Run a specific test class:_
```bash
scripts/test tests.gatherers.downloaders_test.TestDownloader
```

_Run a single test method:_
```bash
scripts/test tests.gatherers.downloaders_test.TestDownloader.test_detect_encoding
```

**Test Discovery:**

- Directory targets use `unittest discover` under the specified path.
- File paths are automatically converted to module paths.
- Dotted paths provide the most precise and reliable way to target individual tests.
- If no target is provided, full test discovery is used.

The default `scripts/test` discovery pattern is `*_test.py`, so smoke tests should
not use that suffix.

#### `smoke`
Runs heavyweight smoke checks using Python's `unittest` framework.

```bash
scripts/smoke
```

This script discovers tests only under `tests/smoke/` with pattern
`*_smoke.py`.

Install/package smoke tests should live in this tier so `scripts/test` stays fast
and hermetic.

> Note: install smoke tests under `tests/smoke/` may run pip in non-interactive
> mode (`--no-input`) with bounded subprocess timeouts so the suite fails fast
> instead of hanging when package index credentials/network access are unavailable.

#### `smoke_assist_install`
Runs a lightweight packaging/install smoke check for assist CLI behavior.

```bash
scripts/smoke_assist_install
```

This script:
- builds a wheel from the current checkout
- creates an isolated virtual environment
- installs the wheel into that environment
- verifies installed `lrh request` and `lrh snapshot` commands from a non-repo working directory

#### Installed prompt CLI smoke test
Run the installed prompt CLI smoke path with:

```bash
python -m unittest tests.smoke.prompt_cli_install_smoke
```

This smoke test builds an isolated virtual environment, installs LRH from the current checkout, and validates `lrh --help`, `lrh prompt label --slug example`, and `lrh prompt record-execution --dry-run ...` from a temporary non-repo working directory.


#### `coverage`
Runs test coverage analysis and generates reports.

```bash
scripts/coverage [--html]
```

**Options:**
- No arguments: Displays coverage report in terminal with missing lines
- `--html`: Generates HTML coverage report in `htmlcov/index.html`

**Process:**
1. Erases previous coverage data
2. Runs tests with coverage tracking
3. Generates coverage report

## Development Workflow

### Initial Setup
```bash
scripts/develop    # Install in development mode with standard dev tools
```

### Regular Development
```bash
scripts/format     # Format code
scripts/lint       # Check for issues
scripts/test       # Run tests
scripts/coverage   # Check coverage
```

### Build & Release Workflow
```bash
scripts/clean      # Clean previous builds
scripts/build      # Build distribution
scripts/publish    # Publish to PyPI (when enabled)
```

### Environment Management
```bash
scripts/update     # Update environment.yml when dependencies change
scripts/version    # Check installed tool versions
```

## Notes

- Runtime assist templates are package-owned under `src/lrh/assist/templates/`; `scripts/aiprog/` no longer hosts runtime request/context templates.
- All scripts assume execution from the repository root
- Scripts use `set -x` for verbose output during execution
- Scripts with `set -euo pipefail` will exit on any error
- The publish script is currently disabled as a safety measure during development

## Dependencies

Make sure you have the following tools installed for full functionality:

- **Build:** Installed by `scripts/develop` as part of the dev extra
- **Publish:** `pip install twine` 
- **Format/Lint:** Installed by `scripts/develop` (includes Black and Ruff)
- **Coverage:** Installed by `scripts/develop` as part of the dev extra
- **Environment:** conda (for environment export)
