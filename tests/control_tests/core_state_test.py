import tempfile
import unittest
from pathlib import Path

from lrh import core_state


class TestCoreState(unittest.TestCase):
    def test_loads_shared_state_from_representative_project_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write_representative_project(root)

            state = core_state.load_core_project_state(root)

            self.assertEqual(state.identity.project_name, root.name)
            self.assertEqual(state.current_focus.id, "FOCUS-1")
            self.assertEqual(state.validation.error_count, 0)
            self.assertTrue(state.validation.is_valid)
            self.assertEqual(
                state.prompt_inputs.active_leaf_work_item_ids,
                ("WI-A", "WI-B"),
            )
            self.assertEqual(state.prompt_inputs.active_workstream_ids, ("WS-A",))
            self.assertEqual(state.workstreams_by_id["WS-A"].child_ids, ("WI-A",))
            self.assertEqual(state.work_items_by_id["WI-A"].parent_ids, ("WS-A",))
            self.assertEqual(
                state.evidence_links,
                (
                    core_state.EvidenceLink(
                        source_id="WI-B",
                        source_kind="work_item",
                        field="required_evidence",
                        target="EV-2",
                    ),
                    core_state.EvidenceLink(
                        source_id="WS-A",
                        source_kind="workstream",
                        field="evidence",
                        target="EV-WS",
                    ),
                ),
            )

    def test_summary_collections_are_ordered_by_stable_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write_representative_project(root)

            state = core_state.load_core_project_state(root)

            self.assertEqual([item.id for item in state.work_items], ["WI-A", "WI-B"])
            self.assertEqual(
                [item.id for item in state.active_leaf_work_items],
                ["WI-A", "WI-B"],
            )
            self.assertEqual(
                [workstream.id for workstream in state.workstreams],
                ["WS-A", "WS-B"],
            )

    def test_typed_summary_preserves_source_runtime_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write_representative_project(root)

            state = core_state.load_core_project_state(root)
            item = state.work_items_by_id["WI-B"]

            self.assertEqual(item.title, "Beta")
            self.assertIn("required_evidence", item.frontmatter_keys)
            self.assertEqual(
                state.loaded_project.work_items_by_id["WI-B"].body, "Body text.\n"
            )
            self.assertEqual(
                state.loaded_project.work_items_by_id["WI-B"].frontmatter[
                    "required_evidence"
                ],
                ["EV-2"],
            )

    def test_incomplete_optional_planning_relationships_are_reported_read_only(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write_representative_project(root, unknown_parent=True)

            state = core_state.load_core_project_state(root)

            self.assertFalse(state.validation.is_valid)
            self.assertIn(
                "PLANNING_UNKNOWN_PARENT_ID",
                [diagnostic.code for diagnostic in state.validation.diagnostics],
            )
            self.assertIn(
                "PLANNING_UNKNOWN_PARENT_ID",
                [diagnostic.code for diagnostic in state.planning.diagnostics],
            )
            self.assertEqual(
                state.prompt_inputs.active_leaf_work_item_ids, ("WI-A", "WI-B")
            )


def _write_representative_project(root: Path, *, unknown_parent: bool = False) -> None:
    project_dir = root / "project"
    (project_dir / "focus").mkdir(parents=True)
    (project_dir / "work_items" / "active").mkdir(parents=True)
    (project_dir / "workstreams" / "active").mkdir(parents=True)
    (project_dir / "workstreams" / "proposed").mkdir(parents=True)
    (project_dir / "evidence").mkdir(parents=True)

    _write(
        project_dir / "focus" / "current_focus.md",
        """---
id: FOCUS-1
title: Current Focus
status: active
priority: high
owner: anthony
related_principles:
  - P-2
  - P-1
---
Focus body.
""",
    )
    _write(
        project_dir / "work_items" / "active" / "WI-B.md",
        """---
id: WI-B
title: Beta
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
related_focus:
  - FOCUS-1
required_evidence:
  - EV-2
---
Body text.
""",
    )
    _write(
        project_dir / "work_items" / "active" / "WI-A.md",
        """---
id: WI-A
title: Alpha
type: investigation
status: active
blocked: false
blocked_reason: null
resolution: null
related_focus:
  - FOCUS-1
depends_on:
  - WI-B
---
""",
    )
    parent_line = "parent_id: WS-MISSING\n" if unknown_parent else ""
    _write(
        project_dir / "workstreams" / "active" / "WS-A.md",
        f"""---
id: WS-A
kind: planning_node
title: Active Stream
status: active
stage: executing
{parent_line}work_items:
  - WI-A
evidence:
  - EV-WS
---
""",
    )
    _write(
        project_dir / "workstreams" / "proposed" / "WS-B.md",
        """---
id: WS-B
kind: planning_node
title: Proposed Stream
status: proposed
stage: conceived
---
""",
    )
    _write(
        project_dir / "evidence" / "EV-2.md",
        """---
id: EV-2
title: Evidence Two
---
""",
    )
    _write(
        project_dir / "evidence" / "EV-WS.md",
        """---
id: EV-WS
title: Workstream Evidence
---
""",
    )


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
