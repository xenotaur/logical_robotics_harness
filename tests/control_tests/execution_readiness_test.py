import tempfile
import unittest
from pathlib import Path

from lrh import core_state
from lrh.control import execution_readiness
from lrh.control import loader as control_loader
from lrh.control import validator as control_validator


class ExecutionReadinessTest(unittest.TestCase):
    def test_ordinary_work_item_without_readiness_metadata_remains_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = _write_project(
                Path(tmp_dir),
                work_item_frontmatter="""---
id: WI-READY
title: Ordinary Item
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
related_focus:
  - FOCUS-1
required_evidence:
  - manual_review
---
""",
            )

            report = control_validator.validate_project(project_dir)
            loaded = control_loader.load_project(project_dir)
            state = core_state.load_core_project_state(project_dir)

            self.assertTrue(report.is_valid)
            self.assertIsNone(loaded.work_items_by_id["WI-READY"].execution_readiness)
            self.assertIsNone(state.work_items_by_id["WI-READY"].execution_readiness)

    def test_minimal_execution_ready_work_item_passes_and_is_typed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = _write_project(
                Path(tmp_dir),
                work_item_frontmatter=_ready_frontmatter(),
            )

            report = control_validator.validate_project(project_dir)
            loaded = control_loader.load_project(project_dir)
            state = core_state.load_core_project_state(project_dir)

            self.assertTrue(report.is_valid)
            readiness = loaded.work_items_by_id["WI-READY"].execution_readiness
            self.assertIsNotNone(readiness)
            self.assertEqual(readiness.allowed_paths, ("src/lrh/example/",))
            self.assertEqual(readiness.forbidden_paths, (".github/workflows/",))
            self.assertEqual(readiness.validation_commands, ("scripts/test",))
            self.assertTrue(readiness.requires_human_approval)
            self.assertTrue(readiness.requires_human_merge)
            self.assertTrue(readiness.requires_human_closeout)

            state_readiness = state.work_items_by_id["WI-READY"].execution_readiness
            self.assertIsNotNone(state_readiness)
            self.assertEqual(state_readiness.validation_commands, ("scripts/test",))
            self.assertEqual(state_readiness.allowed_paths, ("src/lrh/example/",))

    def test_missing_required_fields_are_deterministic_when_opted_in(self) -> None:
        issues = execution_readiness.validate_frontmatter(
            Path("project/work_items/active/WI-READY.md"),
            {"execution_ready": True},
        )

        self.assertEqual(
            [(issue.code, issue.message) for issue in issues],
            [
                (
                    "EXECUTION_READINESS_REQUIRED_FIELD_MISSING",
                    "missing execution-readiness field 'allowed_paths'",
                ),
                (
                    "EXECUTION_READINESS_REQUIRED_FIELD_MISSING",
                    "missing execution-readiness field 'autonomy_level'",
                ),
                (
                    "EXECUTION_READINESS_REQUIRED_FIELD_MISSING",
                    "missing execution-readiness field 'operation_risk'",
                ),
                (
                    "EXECUTION_READINESS_REQUIRED_FIELD_MISSING",
                    "missing execution-readiness field 'required_evidence'",
                ),
                (
                    "EXECUTION_READINESS_REQUIRED_FIELD_MISSING",
                    "missing execution-readiness field 'validation_commands'",
                ),
                (
                    "EXECUTION_READINESS_REQUIRED_LIST_EMPTY",
                    "allowed_paths must contain at least one string",
                ),
                (
                    "EXECUTION_READINESS_REQUIRED_LIST_EMPTY",
                    "required_evidence must contain at least one string",
                ),
                (
                    "EXECUTION_READINESS_REQUIRED_LIST_EMPTY",
                    "validation_commands must contain at least one string",
                ),
            ],
        )

    def test_require_ready_reports_unopted_work_item_as_not_ready(self) -> None:
        issues = execution_readiness.validate_frontmatter(
            Path("WI-PLANNING.md"),
            {},
            require_ready=True,
        )

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "EXECUTION_READINESS_NOT_READY")

    def test_human_gates_default_to_safe_values_in_representation(self) -> None:
        readiness = execution_readiness.from_frontmatter(
            {
                "execution_ready": True,
                "autonomy_level": "manual",
                "operation_risk": "read_only",
                "allowed_paths": ["project/"],
                "validation_commands": ["lrh validate"],
                "required_evidence": ["manual_review"],
            }
        )

        self.assertTrue(readiness.requires_human_approval)
        self.assertTrue(readiness.requires_human_merge)
        self.assertTrue(readiness.requires_human_closeout)


def _write_project(root: Path, *, work_item_frontmatter: str) -> Path:
    project_dir = root / "project"
    (project_dir / "focus").mkdir(parents=True)
    (project_dir / "work_items" / "active").mkdir(parents=True)
    (project_dir / "workstreams" / "active").mkdir(parents=True)
    _write(
        project_dir / "focus" / "current_focus.md",
        """---
id: FOCUS-1
title: Focus
status: active
---
""",
    )
    _write(
        project_dir / "work_items" / "active" / "WI-READY.md",
        work_item_frontmatter + "\nBody.\n",
    )
    _write(
        project_dir / "workstreams" / "active" / "WS-A.md",
        """---
id: WS-A
kind: planning_node
title: Active Stream
status: active
stage: executing
work_items:
  - WI-READY
---
""",
    )
    return project_dir


def _ready_frontmatter() -> str:
    return """---
id: WI-READY
title: Ready Item
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
related_focus:
  - FOCUS-1
execution_ready: true
autonomy_level: manual
operation_risk: read_only
allowed_paths:
  - src/lrh/example/
forbidden_paths:
  - .github/workflows/
validation_commands:
  - scripts/test
required_evidence:
  - manual_review
expected_artifacts:
  - code_diff
---
"""


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
