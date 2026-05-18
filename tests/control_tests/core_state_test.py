import tempfile
import unittest
from pathlib import Path
from types import MappingProxyType

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
            self.assertEqual(state.planning.active_leaf_ids, ("WI-A", "WI-B"))
            self.assertEqual(
                state.planning.status_counts_by_kind,
                {
                    "work_item": {"active": 2},
                    "workstream": {"active": 1, "proposed": 1},
                },
            )
            self.assertEqual(
                state.evidence_links,
                (
                    core_state.EvidenceLink(
                        source_id="DP-A",
                        source_kind="design_proposal",
                        field="evidence",
                        target="EV-DP",
                    ),
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
            self.assertEqual(
                [
                    relationship.child_id
                    for relationship in state.planning.relationships
                ],
                ["WI-A"],
            )

    def test_typed_summary_preserves_source_runtime_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write_representative_project(root)

            state = core_state.load_core_project_state(root)
            item = state.work_items_by_id["WI-B"]

            self.assertEqual(item.title, "Beta")
            self.assertIn("required_evidence", item.frontmatter_keys)
            self.assertFalse(hasattr(item, "frontmatter"))
            self.assertIn("required_evidence", item.path.read_text(encoding="utf-8"))

    def test_indexes_are_read_only_and_precomputed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write_representative_project(root)

            state = core_state.load_core_project_state(root)

            self.assertIsInstance(state.work_items_by_id, MappingProxyType)
            self.assertIs(state.work_items_by_id, state.work_items_by_id)
            with self.assertRaises(TypeError):
                state.work_items_by_id["WI-Z"] = state.work_items_by_id["WI-A"]

    def test_validation_errors_return_summary_without_strict_loader_raise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write_representative_project(root, duplicate_work_item=True)

            state = core_state.load_core_project_state(root)

            self.assertFalse(state.validation.is_valid)
            self.assertIn(
                "WORK_ITEM_ID_DUPLICATE",
                [diagnostic.code for diagnostic in state.validation.diagnostics],
            )
            self.assertIsNone(state.current_focus)
            self.assertEqual(state.work_items, ())
            self.assertEqual(state.prompt_inputs.active_leaf_work_item_ids, ())

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
            self.assertEqual(state.planning.diagnostics, ())
            self.assertEqual(state.prompt_inputs.active_leaf_work_item_ids, ())


def _write_representative_project(
    root: Path,
    *,
    unknown_parent: bool = False,
    duplicate_work_item: bool = False,
) -> None:
    project_dir = root / "project"
    (project_dir / "focus").mkdir(parents=True)
    (project_dir / "work_items" / "active").mkdir(parents=True)
    (project_dir / "workstreams" / "active").mkdir(parents=True)
    (project_dir / "workstreams" / "proposed").mkdir(parents=True)
    (project_dir / "design" / "proposals" / "proposed").mkdir(parents=True)
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
    if duplicate_work_item:
        _write(
            project_dir / "work_items" / "active" / "WI-DUP.md",
            """---
id: WI-A
title: Duplicate Alpha
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
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
        project_dir / "design" / "proposals" / "proposed" / "DP-A.md",
        """---
id: DP-A
type: design_proposal
title: Proposal A
status: proposed
evidence:
  - EV-DP
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
    _write(
        project_dir / "evidence" / "EV-DP.md",
        """---
id: EV-DP
title: Design Proposal Evidence
---
""",
    )


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
