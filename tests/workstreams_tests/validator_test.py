import tempfile
import unittest
from pathlib import Path

from lrh.control.validator import validate_project


class TestWorkstreamValidator(unittest.TestCase):
    def test_valid_minimal_workstream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_workstream(root, "proposed", "WS-VALID", "proposed", "conceived")

            report = validate_project(root / "project")

            self.assertEqual(report.errors, [])
            self.assertEqual(report.warnings, [])

    def test_missing_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write(
                root / "project" / "workstreams" / "proposed" / "WS-MISSING.md",
                """---
id: WS-MISSING
kind: planning_node
status: proposed
---
""",
            )

            report = validate_project(root / "project")

            missing_fields = {
                issue.message
                for issue in report.errors
                if issue.code == "MISSING_REQUIRED_FIELD"
            }
            self.assertIn("missing required field 'stage'", missing_fields)
            self.assertIn("missing required field 'title'", missing_fields)

    def test_invalid_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_workstream(
                root,
                "proposed",
                "WS-INVALID-KIND",
                "proposed",
                "conceived",
                kind="initiative",
            )

            report = validate_project(root / "project")

            self.assertTrue(
                any(issue.code == "WORKSTREAM_KIND_INVALID" for issue in report.errors)
            )

    def test_invalid_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_workstream(
                root, "proposed", "WS-INVALID-STATUS", "paused", "conceived"
            )

            report = validate_project(root / "project")

            self.assertTrue(
                any(
                    issue.code == "WORKSTREAM_STATUS_INVALID" for issue in report.errors
                )
            )

    def test_invalid_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_workstream(root, "active", "WS-INVALID-STAGE", "active", "shipping")

            report = validate_project(root / "project")

            self.assertTrue(
                any(issue.code == "WORKSTREAM_STAGE_INVALID" for issue in report.errors)
            )

    def test_duplicate_workstream_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_workstream(root, "proposed", "WS-DUPLICATE", "proposed", "conceived")
            _write_workstream(root, "active", "WS-DUPLICATE", "active", "executing")

            report = validate_project(root / "project")

            self.assertTrue(
                any(issue.code == "DUPLICATE_WORKSTREAM_ID" for issue in report.errors)
            )

    def test_bucket_status_mismatch_is_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_workstream(root, "active", "WS-DRIFT", "resolved", "closed")

            report = validate_project(root / "project")

            self.assertEqual(report.errors, [])
            self.assertTrue(report.is_valid)
            self.assertTrue(
                any(
                    issue.code == "WORKSTREAM_BUCKET_STATUS_MISMATCH"
                    for issue in report.warnings
                )
            )

    def test_readme_and_placeholder_files_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            proposed = root / "project" / "workstreams" / "proposed"
            _write(proposed / "README.md", "# Proposed workstreams\n")
            _write(proposed / "placeholder.md", "Reserved for future workstreams.\n")
            _write(proposed / "notes.md", "Notes without workstream frontmatter.\n")

            report = validate_project(root / "project")

            self.assertEqual(report.errors, [])
            self.assertEqual(report.warnings, [])


def _write_project_scaffold(root: Path) -> Path:
    (root / "project" / "focus").mkdir(parents=True)
    (root / "project" / "work_items").mkdir(parents=True)
    (root / "project" / "contributors").mkdir(parents=True)
    for bucket in ("proposed", "active", "resolved", "abandoned"):
        (root / "project" / "workstreams" / bucket).mkdir(parents=True)
    _write(
        root / "project" / "focus" / "current_focus.md",
        "---\nid: FOCUS-1\ntitle: Focus\nstatus: active\n---\n",
    )
    return root.resolve()


def _write_workstream(
    root: Path,
    bucket: str,
    workstream_id: str,
    status: str,
    stage: str,
    *,
    kind: str = "planning_node",
) -> None:
    _write(
        root / "project" / "workstreams" / bucket / f"{workstream_id}.md",
        f"""---
id: {workstream_id}
kind: {kind}
title: {workstream_id} Workstream
status: {status}
stage: {stage}
---

# {workstream_id} Workstream
""",
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
