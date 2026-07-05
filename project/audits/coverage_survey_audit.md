# Coverage Survey Audit

**Date:** 2026-06-29
**Objective:** Survey the existing Python code in `src/lrh/` to assess which modules have the most and the least coverage provided by tests in `tests/`, as a first step toward improving codebase coverage.

## 1. Methodology

The coverage data was collected following the project conventions:
1. Environment setup and installation via `scripts/develop`.
2. Unit tests execution via `scripts/test`.
3. Coverage measurement and reporting via `scripts/coverage`.

The results highlight areas of the codebase with missing test coverage, alongside areas that are well-tested, conforming to the deterministic and hermetic unit testing policies described in `AGENTS.md` and `STYLE.md`.

## 2. Least Covered Modules

The following modules in `src/lrh/` exhibit the lowest unit test coverage:

| Module | Coverage | Statements | Missed |
|--------|----------|------------|--------|
| `src/lrh/dev/clean.py` | 0% | 33 | 33 |
| `src/lrh/prompt_workflow.py` | 18% | 158 | 129 |
| `src/lrh/project/bootstrap.py` | 31% | 77 | 53 |
| `src/lrh/project/doctor.py` | 34% | 59 | 39 |
| `src/lrh/integrations/github/gh_client.py` | 38% | 21 | 13 |
| `src/lrh/cli/main.py` | 46% | 469 | 251 |
| `src/lrh/integrations/github/pull_reviews.py` | 47% | 70 | 37 |
| `src/lrh/prompt_workflow_search.py` | 65% | 131 | 46 |
| `src/lrh/assist/snapshot_cli.py` | 71% | 415 | 121 |
| `src/lrh/assist/sourcetree_surveyor.py` | 71% | 235 | 69 |

### Insights

* **Development Scripts (`src/lrh/dev/*`):** While most development scripts are well-tested (e.g. `release_smoke.py` and `versioning.py`), `clean.py` remains entirely untested. Testing this module likely requires smoke tests under `tests/smoke/` rather than standard unit tests, per the hermetic principles in `AGENTS.md`.
* **External Integrations (`src/lrh/integrations/github/*`):** Coverage remains low (38-47%) due to the policy of avoiding network access in standard unit tests. To improve coverage here without violating `STYLE.md`, we must use fakes, stubs, or mocks at the external boundary.
* **CLI and Workflows (`src/lrh/cli/main.py`, `src/lrh/prompt_workflow.py`, `src/lrh/assist/snapshot_cli.py`):** These contain significant application logic and orchestration but lack robust coverage, representing a primary risk surface for regressions.

## 3. Most Covered Modules

The following modules demonstrate excellent test coverage, approaching or hitting 100%:

| Module | Coverage | Statements | Missed |
|--------|----------|------------|--------|
| `src/lrh/skills/installer.py` | 99% | 97 | 1 |
| `src/lrh/ux/dashboard.py` | 99% | 222 | 1 |
| `src/lrh/conversations/sensitivity.py` | 98% | 93 | 2 |
| `src/lrh/core_state.py` | 98% | 207 | 5 |
| `src/lrh/assist/request_catalog.py` | 97% | 34 | 1 |
| `src/lrh/assist/run_packet.py` | 97% | 147 | 5 |
| `src/lrh/assist/template_resolver.py` | 97% | 119 | 4 |
| `src/lrh/control/planning_tree.py` | 97% | 241 | 8 |
| `src/lrh/meta/local_state_model.py` | 97% | 94 | 3 |
| `src/lrh/assist/run_report.py` | 95% | 213 | 11 |

*(Note: Numerous pure data-model files and `__init__.py` files achieve 100% coverage by nature of having purely declarative logic, and are omitted from this top-10 list).*

### Insights

* **Core Control Plane:** Modules like `planning_tree.py` and `local_state_model.py` are heavily tested, aligning with the project's foundational mission to prioritize the reliability of the control plane and validation structures.
* **Assist Module (`src/lrh/assist/*`):** These modules exhibit high coverage (95%+), demonstrating strict adherence to testability and functional determinism.

## 4. Recommendations for Improving Coverage

To methodically improve codebase coverage in alignment with LRH conventions, the following steps are recommended:

1. **Implement Fakes/Mocks for External Boundaries:** Address the `integrations/github` and `project/bootstrap.py` gaps by constructing hermetic fakes that simulate network and filesystem interactions.
2. **Expand Smoke Tests:** Address the `dev/` module gap by writing realistic integration tests in `tests/smoke/` and executing them via `scripts/smoke`, preserving the fast, deterministic nature of the `scripts/test` path.
3. **Target Core CLI Logic:** Increase test coverage for `src/lrh/cli/main.py` using `unittest.mock` to simulate CLI invocations. This will validate the integration points between CLI commands and the well-tested underlying control plane logic.
