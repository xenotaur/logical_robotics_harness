import tempfile
import unittest
from pathlib import Path

from lrh.control.loader import (
    load_project,
    load_workstreams,
    load_workstreams_from_project_dir_permissive,
)


class TestWorkstreamLoader(unittest.TestCase):
    def test_load_minimal_proposed_workstream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            workstream_path = root / "project" / "workstreams" / "proposed" / "WS-1.md"
            workstream_path.write_text(
                """---
id: WS-1
kind: planning_node
title: First Workstream
status: proposed
stage: conceived
---

# First Workstream
""",
                encoding="utf-8",
            )

            workstreams = load_workstreams(root)

            self.assertEqual(len(workstreams), 1)
            workstream = workstreams[0]
            self.assertEqual(workstream.id, "WS-1")
            self.assertEqual(workstream.kind, "planning_node")
            self.assertEqual(workstream.title, "First Workstream")
            self.assertEqual(workstream.status, "proposed")
            self.assertEqual(workstream.stage, "conceived")
            self.assertEqual(workstream.bucket, "proposed")
            self.assertEqual(workstream.path, workstream_path.resolve())
            self.assertEqual(workstream.children, ())
            self.assertEqual(workstream.work_items, ())
            self.assertIsNone(workstream.origin)
            self.assertIsNone(workstream.summary)

    def test_load_multiple_workstreams_across_buckets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            for bucket in ("proposed", "active", "resolved", "abandoned"):
                workstream_id = f"WS-{bucket.upper()}"
                (
                    root / "project" / "workstreams" / bucket / f"{workstream_id}.md"
                ).write_text(
                    f"""---
id: {workstream_id}
kind: planning_node
title: {bucket.title()} Workstream
status: {bucket}
stage: conceived
---
""",
                    encoding="utf-8",
                )

            state = load_project(root)

            self.assertEqual(
                [workstream.bucket for workstream in state.workstreams],
                ["proposed", "active", "resolved", "abandoned"],
            )
            self.assertEqual(
                set(state.workstreams_by_id),
                {"WS-PROPOSED", "WS-ACTIVE", "WS-RESOLVED", "WS-ABANDONED"},
            )

    def test_ignore_readme_and_placeholder_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            proposed = root / "project" / "workstreams" / "proposed"
            (proposed / "README.md").write_text("# Bucket readme\n", encoding="utf-8")
            (proposed / "placeholder.md").write_text(
                "Reserved for future workstreams.\n", encoding="utf-8"
            )
            (proposed / "notes.md").write_text(
                "Notes without workstream frontmatter.\n", encoding="utf-8"
            )
            (proposed / "WS-REAL.md").write_text(
                """---
id: WS-REAL
kind: planning_node
title: Real Workstream
status: proposed
stage: conceived
---
""",
                encoding="utf-8",
            )

            workstreams = load_workstreams(root)

            self.assertEqual([workstream.id for workstream in workstreams], ["WS-REAL"])

    def test_list_fields_load_as_tuples_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            (root / "project" / "workstreams" / "active" / "WS-LISTS.md").write_text(
                """---
id: WS-LISTS
kind: planning_node
title: List Workstream
status: active
stage: executing
children:
  - WS-CHILD
  - WI-1
related_focus:
  - FOCUS-1
related_roadmap: [ROADMAP-1]
work_items:
  - WI-1
execution_records:
  - project/executions/WI-1/run.md
evidence:
  - project/evidence/test.md
exit_criteria:
  - Tests pass
---
""",
                encoding="utf-8",
            )

            workstream = load_workstreams(root)[0]

            self.assertEqual(workstream.children, ("WS-CHILD", "WI-1"))
            self.assertEqual(workstream.related_focus, ("FOCUS-1",))
            self.assertEqual(workstream.related_roadmap, ("ROADMAP-1",))
            self.assertEqual(workstream.work_items, ("WI-1",))
            self.assertEqual(
                workstream.execution_records,
                ("project/executions/WI-1/run.md",),
            )
            self.assertEqual(workstream.evidence, ("project/evidence/test.md",))
            self.assertEqual(workstream.exit_criteria, ("Tests pass",))

    def test_permissive_loader_preserves_valid_workstreams_after_bad_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            (root / "project" / "workstreams" / "active" / "WS-GOOD.md").write_text(
                """---
id: WS-GOOD
kind: planning_node
title: Good Workstream
status: active
stage: executing
---
""",
                encoding="utf-8",
            )
            (root / "project" / "workstreams" / "proposed" / "WS-BAD.md").write_text(
                """---
id: WS-BAD
kind: planning_node
status: proposed
stage: conceived
---
""",
                encoding="utf-8",
            )

            workstreams, warnings = load_workstreams_from_project_dir_permissive(
                root / "project"
            )

            self.assertEqual([workstream.id for workstream in workstreams], ["WS-GOOD"])
            self.assertEqual(len(warnings), 1)
            self.assertIn("Skipped proposed/WS-BAD.md", warnings[0])
            self.assertIn("missing or invalid string field 'title'", warnings[0])


def _write_project_scaffold(root: Path) -> Path:
    (root / "project" / "focus").mkdir(parents=True)
    (root / "project" / "work_items" / "active").mkdir(parents=True)
    (root / "project" / "contributors").mkdir(parents=True)
    for bucket in ("proposed", "active", "resolved", "abandoned"):
        (root / "project" / "workstreams" / bucket).mkdir(parents=True)
    (root / "project" / "focus" / "current_focus.md").write_text(
        "---\nid: FOCUS-1\ntitle: Focus\nstatus: active\n---\n",
        encoding="utf-8",
    )
    (root / "project" / "work_items" / "active" / "WI-1.md").write_text(
        "---\nid: WI-1\ntitle: Task\ntype: deliverable\nstatus: active\n---\n",
        encoding="utf-8",
    )
    return root.resolve()


if __name__ == "__main__":
    unittest.main()
