# Coverage Survey Audit

**Date:** 2026-06-29
**Objective:** Survey the existing Python code in `src/lrh/` to assess which modules have the most and the least coverage provided by tests in `tests/`, as a first step toward improving codebase coverage.

## 1. Methodology

The coverage data was collected following the project conventions:
1. Environment setup and installation via `scripts/develop`.
2. Unit tests execution via `scripts/test`.
3. Coverage measurement and reporting via `scripts/coverage`.

The results highlight areas of the codebase with missing test coverage, alongside areas that are well-tested, conforming to the deterministic and hermetic unit testing policies described in `AGENTS.md` and `STYLE.md`.

*Note:* The canonical `scripts/coverage` job measures coverage with `--source=src/lrh` and currently misses existing test directories that are not importable packages. Therefore, the audit does not measure all unit tests under `tests/` and some modules reported as 0% may actually have tests that are missed by the coverage tool's discovery.

## 2. Least Covered Modules

The following modules in `src/lrh/` exhibit the lowest unit test coverage:

| Module | Coverage | Statements | Missed |
|--------|----------|------------|--------|
| `src/lrh/dev/clean.py` | 0% | 33 | 33 |
| `src/lrh/dev/release_smoke.py` | 0% | 252 | 252 |
| `src/lrh/dev/versioning.py` | 0% | 224 | 224 |
| `src/lrh/integrations/github/pull_reviews.py` | 10% | 70 | 63 |
| `src/lrh/prompt_workflow.py` | 18% | 158 | 129 |
| `src/lrh/integrations/github/gh_client.py` | 19% | 21 | 17 |
| `src/lrh/project/bootstrap.py` | 31% | 77 | 53 |
| `src/lrh/project/doctor.py` | 34% | 59 | 39 |
| `src/lrh/cli/main.py` | 46% | 469 | 251 |
| `src/lrh/work_items/organize.py` | 62% | 173 | 65 |

### Insights

* **Development Scripts (`src/lrh/dev/*`):** These modules are reported with 0% unit test coverage. However, `tests/dev_tests/release_smoke_test.py` and `tests/dev_tests/versioning_test.py` exist and contain active tests. The canonical coverage job currently has a discovery gap that misses non-importable test directories, so this 0% figure is an artifact of the coverage configuration rather than a true absence of tests. Addressing the discovery gap is needed before determining whether more tests are required.
* **External Integrations (`src/lrh/integrations/github/*`):** Coverage is extremely low (10-19%). This stems from the policy of avoiding network access in standard unit tests. To improve coverage here without violating `STYLE.md`, we must use fakes, stubs, or mocks at the external boundary.
* **CLI and Workflows (`src/lrh/cli/main.py`, `src/lrh/prompt_workflow.py`):** These contain significant application logic and orchestration but lack robust coverage, representing a primary risk surface for regressions.

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
