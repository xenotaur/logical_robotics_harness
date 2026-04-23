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
- `pip install build`

**Output:** Creates distribution files in `dist/` directory.

#### `clean`
Removes all build artifacts to ensure a clean state.

```bash
scripts/clean
```

**Removes:**
- `build/` directory
- `dist/` directory  
- `lrh.egg-info/` directory

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

This installs the package with `pip install -e ".[dev]"`, allowing you to make changes to the source code that are immediately reflected without reinstalling while also installing standard development tools.

#### `update`
Updates the conda environment specification file.

```bash
scripts/update
```

**Output:** Updates `environment.yml` with current conda environment dependencies (excludes name and prefix).

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
```

## Notes

- Runtime assist templates are package-owned under `src/lrh/assist/templates/`; `scripts/aiprog/` no longer hosts runtime request/context templates.
- All scripts assume execution from the repository root
- Scripts use `set -x` for verbose output during execution
- Scripts with `set -euo pipefail` will exit on any error
- The publish script is currently disabled as a safety measure during development

## Dependencies

Make sure you have the following tools installed for full functionality:

- **Build:** `pip install build`
- **Publish:** `pip install twine` 
- **Format/Lint:** Installed by `scripts/develop` via `pip install -e ".[dev]"` (includes Black and Ruff)
- **Coverage:** `pip install coverage`
- **Environment:** conda (for environment export)
