import tempfile
import unittest
from pathlib import Path

from lrh.control import planning_tree
from lrh.control.loader import load_project
from lrh.control.validator import validate_project


class TestPlanningTreeRelationships(unittest.TestCase):
    def test_workstream_with_child_work_item(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_workstream(root, "WS-PARENT", work_items=("WI-CHILD",))
            _write_work_item(root, "WI-CHILD")

            index = planning_tree.build_planning_tree(load_project(root))

            self.assertEqual(index.children_of("WS-PARENT"), ("WI-CHILD",))
            self.assertEqual(index.parents_of("WI-CHILD"), ("WS-PARENT",))
            self.assertEqual(index.diagnostics, ())

    def test_workstream_with_child_workstream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_workstream(root, "WS-PARENT", children=("WS-CHILD",))
            _write_workstream(root, "WS-CHILD")

            index = planning_tree.build_planning_tree(load_project(root))

            self.assertEqual(index.children_of("WS-PARENT"), ("WS-CHILD",))
            self.assertEqual(index.parents_of("WS-CHILD"), ("WS-PARENT",))
            self.assertEqual(index.roots(), ("WS-PARENT",))

    def test_parent_id_based_relationship(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_workstream(root, "WS-PARENT")
            _write_workstream(root, "WS-CHILD", parent_id="WS-PARENT")
            _write_work_item(root, "WI-CHILD", parent_id="WS-PARENT")

            index = planning_tree.build_planning_tree(load_project(root))

            self.assertEqual(index.children_of("WS-PARENT"), ("WS-CHILD", "WI-CHILD"))
            self.assertEqual(index.parents_of("WS-CHILD"), ("WS-PARENT",))
            self.assertEqual(index.parents_of("WI-CHILD"), ("WS-PARENT",))

    def test_children_based_relationship(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_workstream(root, "WS-PARENT", children=("WS-CHILD", "WI-CHILD"))
            _write_workstream(root, "WS-CHILD")
            _write_work_item(root, "WI-CHILD")

            index = planning_tree.build_planning_tree(load_project(root))

            self.assertEqual(index.children_of("WS-PARENT"), ("WS-CHILD", "WI-CHILD"))
            self.assertEqual(index.parents_of("WS-CHILD"), ("WS-PARENT",))
            self.assertEqual(index.parents_of("WI-CHILD"), ("WS-PARENT",))

    def test_missing_parent_id_reference_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_workstream(root, "WS-CHILD", parent_id="WS-MISSING")

            report = validate_project(root / "project")

            self.assertTrue(
                any(
                    issue.code == "PLANNING_UNKNOWN_PARENT_ID"
                    and issue.severity == "error"
                    for issue in report.errors
                )
            )

    def test_missing_child_reference_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_workstream(root, "WS-PARENT", children=("WS-MISSING",))

            report = validate_project(root / "project")

            self.assertTrue(
                any(
                    issue.code == "PLANNING_UNKNOWN_CHILD_ID"
                    and issue.severity == "error"
                    for issue in report.errors
                )
            )

    def test_cycle_among_workstreams_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_workstream(root, "WS-A", children=("WS-B",))
            _write_workstream(root, "WS-B", children=("WS-A",))

            report = validate_project(root / "project")

            self.assertTrue(
                any(issue.code == "PLANNING_NODE_CYCLE" for issue in report.errors)
            )

    def test_no_path_based_relationship_dependence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            nested = root / "project" / "workstreams" / "active" / "nested"
            nested.mkdir()
            _write_workstream(root, "WS-PARENT", bucket="active")
            _write(
                nested / "WS-NESTED.md",
                _workstream_text("WS-NESTED", status="active", stage="executing"),
            )
            _write_workstream(root, "WS-CHILD", bucket="active")

            index = planning_tree.build_planning_tree(load_project(root))

            self.assertNotIn("WS-NESTED", index.artifacts_by_id)
            self.assertEqual(index.children_of("WS-PARENT"), ())
            self.assertEqual(set(index.roots()), {"WS-PARENT", "WS-CHILD"})

    def test_readme_and_placeholder_files_remain_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            proposed = root / "project" / "workstreams" / "proposed"
            _write(proposed / "README.md", "# Proposed\n")
            _write(proposed / "placeholder.md", "placeholder\n")
            _write_workstream(root, "WS-REAL")

            index = planning_tree.build_planning_tree(load_project(root))

            self.assertEqual(tuple(index.artifacts_by_id), ("WS-REAL",))
            self.assertEqual(index.diagnostics, ())

    def test_duplicate_id_across_workstream_and_work_item_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write(
                root / "project" / "workstreams" / "proposed" / "WS-DUP.md",
                _workstream_text("WI-SAME", status="proposed", stage="conceived"),
            )
            _write_work_item(root, "WI-SAME")

            report = validate_project(root / "project")

            self.assertTrue(
                any(issue.code == "PLANNING_DUPLICATE_ID" for issue in report.errors)
            )

    def test_parent_child_mismatch_is_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_workstream(root, "WS-A", children=("WS-CHILD",))
            _write_workstream(root, "WS-B")
            _write_workstream(root, "WS-CHILD", parent_id="WS-B")

            report = validate_project(root / "project")

            self.assertTrue(
                any(
                    issue.code == "PLANNING_PARENT_CHILD_MISMATCH"
                    for issue in report.warnings
                )
            )


def _write_project_scaffold(root: Path) -> Path:
    (root / "project" / "focus").mkdir(parents=True)
    (root / "project" / "work_items" / "active").mkdir(parents=True)
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
    workstream_id: str,
    *,
    bucket: str = "proposed",
    parent_id: str | None = None,
    children: tuple[str, ...] = (),
    work_items: tuple[str, ...] = (),
) -> None:
    _write(
        root / "project" / "workstreams" / bucket / f"{workstream_id}.md",
        _workstream_text(
            workstream_id,
            status=bucket,
            stage="conceived" if bucket == "proposed" else "executing",
            parent_id=parent_id,
            children=children,
            work_items=work_items,
        ),
    )


def _workstream_text(
    workstream_id: str,
    *,
    status: str,
    stage: str,
    parent_id: str | None = None,
    children: tuple[str, ...] = (),
    work_items: tuple[str, ...] = (),
) -> str:
    fields = [
        "---",
        f"id: {workstream_id}",
        "kind: planning_node",
        f"title: {workstream_id} Workstream",
        f"status: {status}",
        f"stage: {stage}",
    ]
    if parent_id:
        fields.append(f"parent_id: {parent_id}")
    fields.extend(_list_field("children", children))
    fields.extend(_list_field("work_items", work_items))
    fields.extend(["---", ""])
    return "\n".join(fields)


def _write_work_item(
    root: Path,
    work_item_id: str,
    *,
    parent_id: str | None = None,
) -> None:
    fields = [
        "---",
        f"id: {work_item_id}",
        f"title: {work_item_id} Task",
        "type: deliverable",
        "status: active",
        "blocked: false",
        "blocked_reason: null",
        "resolution: null",
    ]
    if parent_id:
        fields.append(f"parent_id: {parent_id}")
    fields.extend(["---", ""])
    _write(
        root / "project" / "work_items" / "active" / f"{work_item_id}.md",
        "\n".join(fields),
    )


def _list_field(name: str, values: tuple[str, ...]) -> list[str]:
    if not values:
        return []
    lines = [f"{name}:"]
    lines.extend(f"  - {value}" for value in values)
    return lines


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
