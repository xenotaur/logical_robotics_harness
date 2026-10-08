"""Tests for dependency-map view declarations and snapshots."""

from __future__ import annotations

import datetime
import json
import pathlib
import tempfile
import unittest

from lrh.control import validate_project
from lrh.dependency_maps import snapshot
from lrh.dependency_maps import view as view_module

_AT = datetime.datetime(2026, 10, 8, 12, 0, tzinfo=datetime.UTC)


def _write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _list(name: str, values: list[str]) -> str:
    if not values:
        return f"{name}: []\n"
    return f"{name}:\n" + "".join(f'  - "{value}"\n' for value in values)


def _work_item(
    root: pathlib.Path,
    item_id: str,
    status: str = "proposed",
    *,
    depends_on: list[str] | None = None,
    blocked_by: list[str] | None = None,
    blocked: bool = False,
    blocked_reason: str | None = None,
    parent_id: str | None = None,
) -> None:
    reason = f'"{blocked_reason}"' if blocked_reason else "null"
    parent = f'parent_id: "{parent_id}"\n' if parent_id else ""
    _write(
        root / "project" / "work_items" / status / f"{item_id}.md",
        f"---\nid: {item_id}\ntitle: {item_id} title\ntype: deliverable\n"
        f"status: {status}\nblocked: {'true' if blocked else 'false'}\n"
        f"blocked_reason: {reason}\nresolution: null\n{parent}"
        + _list("depends_on", depends_on or [])
        + _list("blocked_by", blocked_by or [])
        + "---\nBody.\n",
    )


def _workstream(root: pathlib.Path, ws_id: str, work_items: list[str]) -> None:
    _write(
        root / "project" / "workstreams" / "active" / f"{ws_id}.md",
        f"---\nid: {ws_id}\nkind: planning_node\ntitle: {ws_id} title\n"
        "status: active\nstage: executing\n"
        + _list("work_items", work_items)
        + "---\nBody.\n",
    )


def _view(root: pathlib.Path, text: str, name: str = "main") -> None:
    _write(root / "project" / "views" / "dependency_maps" / f"{name}.md", text)


_MAIN_VIEW = """---
id: "main"
title: "Main"
lanes:
- workstream: "WS-A"
- workstream: "WS-B"
phases:
- id: "one"
  title: "One"
  work_items: ["WI-DONE", "WI-WAIT", "WI-FREE"]
- id: "two"
  title: "Two"
  work_items: ["WI-FLAG", "WI-BLOCKED", "WI-RUN", "WI-DROP"]
---
Body.
"""


class _RepoMixin:
    """A temporary repository with a focus file; mixed into each TestCase."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)
        _write(
            self.root / "project" / "focus" / "current_focus.md",
            "---\nid: FOCUS-1\ntitle: Focus\nstatus: active\n---\nBody.\n",
        )

    def build(self, name: str = "main") -> snapshot.DependencyMapSnapshot:
        return snapshot.build_snapshot(self.root, name, now=_AT)


class StructuralStateTest(_RepoMixin, unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        _work_item(self.root, "WI-DONE", "resolved")
        _work_item(self.root, "WI-DROP", "abandoned")
        _work_item(self.root, "WI-WAIT", depends_on=["WI-DROP"])
        _work_item(self.root, "WI-FREE", depends_on=["WI-DONE"])
        _work_item(
            self.root,
            "WI-FLAG",
            "active",
            blocked=True,
            blocked_reason="waiting on ops",
        )
        _work_item(self.root, "WI-BLOCKED", blocked_by=["WI-WAIT"])
        _work_item(self.root, "WI-RUN", "active", depends_on=["WI-WAIT"])
        _workstream(
            self.root,
            "WS-A",
            ["WI-DONE", "WI-DROP", "WI-WAIT", "WI-FREE", "WI-FLAG", "WI-BLOCKED"],
        )
        _workstream(self.root, "WS-B", ["WI-RUN"])
        _view(self.root, _MAIN_VIEW)

    def nodes(self) -> dict[str, snapshot.Node]:
        return {node.id: node for node in self.build().nodes}

    def test_states_follow_the_revision_2_precedence(self) -> None:
        states = {node_id: node.state for node_id, node in self.nodes().items()}

        self.assertEqual(
            states,
            {
                "WI-DONE": "done",
                "WI-DROP": "abandoned",
                "WI-WAIT": "waiting",
                "WI-FREE": "unblocked",
                "WI-FLAG": "blocked",
                "WI-BLOCKED": "blocked",
                "WI-RUN": "in_progress",
            },
        )

    def test_reasons_explain_each_state(self) -> None:
        nodes = self.nodes()

        self.assertEqual(
            nodes["WI-FLAG"].state_reasons,
            (snapshot.StateReason(kind="blocked_flag", detail="waiting on ops"),),
        )
        self.assertEqual(
            nodes["WI-WAIT"].state_reasons,
            (
                snapshot.StateReason(
                    kind="depends_on", target="WI-DROP", target_lifecycle="abandoned"
                ),
            ),
        )
        self.assertEqual(nodes["WI-BLOCKED"].state_reasons[0].kind, "blocked_by")

    def test_layers_stay_separate(self) -> None:
        node = self.nodes()["WI-FREE"]

        self.assertEqual(node.lifecycle, "proposed")
        self.assertEqual(node.authorization, "not_derived")
        self.assertEqual(node.prompt_ready_source, "lrh work-items readiness")
        self.assertIn(node.prompt_ready, (True, False))

    def test_placement_records_its_source(self) -> None:
        nodes = self.nodes()

        self.assertEqual(
            (nodes["WI-RUN"].lane, nodes["WI-RUN"].lane_source), ("WS-B", "workstream")
        )
        self.assertEqual(
            (nodes["WI-FLAG"].phase, nodes["WI-FLAG"].phase_source), ("two", "declared")
        )

    def test_snapshot_identity_has_no_absolute_paths(self) -> None:
        text = self.build().to_json()

        self.assertNotIn(str(self.root.resolve()), text)
        self.assertNotIn(self._tmp.name, text)
        data = json.loads(text)
        self.assertEqual(data["schema_version"], snapshot.SCHEMA_VERSION)
        self.assertEqual(data["generated_at"], "2026-10-08T12:00:00+00:00")
        self.assertTrue(data["project"]["checkout_id"].startswith("local:"))
        self.assertTrue(data["source_fingerprint"].startswith("sha256:"))

    def test_serialization_round_trips(self) -> None:
        built = self.build()

        self.assertEqual(
            snapshot.DependencyMapSnapshot.from_dict(json.loads(built.to_json())), built
        )
        with self.assertRaises(ValueError):
            snapshot.DependencyMapSnapshot.from_dict({"schema_version": 99})

    def test_rows_include_a_visible_unplaced_phase(self) -> None:
        built = self.build()

        self.assertEqual([row.id for row in built.phases], ["one", "two", "unplaced"])
        self.assertTrue(built.phases[-1].unplaced)
        self.assertEqual([row.id for row in built.lanes], ["WS-A", "WS-B"])


class DiagnosticsTest(_RepoMixin, unittest.TestCase):
    def codes(self, built: snapshot.DependencyMapSnapshot) -> list[str]:
        return [item.code for item in built.diagnostics]

    def test_missing_references_are_reported_and_never_count_as_done(self) -> None:
        _work_item(self.root, "WI-A", depends_on=["WI-GONE"])
        _workstream(self.root, "WS-A", ["WI-A"])
        _view(self.root, _simple_view(["WI-A"]))

        built = self.build()

        self.assertIn("missing_reference", self.codes(built))
        self.assertEqual(built.nodes[0].state, "waiting")
        self.assertFalse(built.edges[0].resolved)

    def test_cycles_are_reported_per_edge_type(self) -> None:
        _work_item(self.root, "WI-A", depends_on=["WI-B"])
        _work_item(self.root, "WI-B", depends_on=["WI-A"], blocked_by=["WI-B"])
        _workstream(self.root, "WS-A", ["WI-A", "WI-B"])
        _view(self.root, _simple_view(["WI-A", "WI-B"]))

        cycles = [item for item in self.build().diagnostics if item.code == "cycle"]

        self.assertEqual(
            sorted(item.message for item in cycles),
            ["blocked_by cycle: WI-B", "depends_on cycle: WI-A -> WI-B"],
        )

    def test_ambiguous_lane_needs_an_override(self) -> None:
        _work_item(self.root, "WI-A")
        _workstream(self.root, "WS-A", ["WI-A"])
        _workstream(self.root, "WS-B", ["WI-A"])
        _view(self.root, _simple_view(["WI-A"], lanes=["WS-A", "WS-B"]))

        built = self.build()
        self.assertIn("ambiguous_lane", self.codes(built))
        self.assertIsNone(built.nodes[0].lane)

        _view(
            self.root,
            _simple_view(
                ["WI-A"],
                lanes=["WS-A", "WS-B"],
                extra=(
                    'lane_overrides:\n- work_item: "WI-A"\n  lane: "WS-B"\n'
                    '  reason: "Owned by B"\n'
                ),
            ),
        )
        node = self.build().nodes[0]
        self.assertEqual(
            (node.lane, node.lane_source, node.lane_reason),
            ("WS-B", "override", "Owned by B"),
        )

    def test_unplaced_and_ambiguous_phases_use_the_unplaced_row(self) -> None:
        _work_item(self.root, "WI-A")
        _work_item(self.root, "WI-B")
        _workstream(self.root, "WS-A", ["WI-A", "WI-B"])
        _view(
            self.root,
            """---
id: "main"
title: "Main"
lanes:
- workstream: "WS-A"
phases:
- id: "one"
  title: "One"
  work_items: ["WI-B"]
- id: "two"
  title: "Two"
  work_items: ["WI-B"]
---
""",
        )

        built = self.build()
        nodes = {node.id: node for node in built.nodes}

        self.assertEqual(
            (nodes["WI-A"].phase, nodes["WI-A"].phase_source), ("unplaced", "none")
        )
        self.assertEqual(
            (nodes["WI-B"].phase, nodes["WI-B"].phase_source), ("unplaced", "ambiguous")
        )
        self.assertIn("unplaced_phase", self.codes(built))
        self.assertIn("ambiguous_phase", self.codes(built))

    def test_items_in_no_lane_are_unplaced(self) -> None:
        _work_item(self.root, "WI-A")
        _work_item(self.root, "WI-LOOSE")
        _workstream(self.root, "WS-A", ["WI-A"])
        _view(self.root, _simple_view(["WI-A", "WI-LOOSE"]))

        built = self.build()

        self.assertIn("unplaced_lane", self.codes(built))
        self.assertEqual(built.lanes[-1].id, "unplaced")

    def test_offscreen_predecessors_are_kept_and_counted(self) -> None:
        _work_item(self.root, "WI-A", depends_on=["WI-ELSEWHERE"])
        _work_item(self.root, "WI-ELSEWHERE", "active")
        _workstream(self.root, "WS-A", ["WI-A"])
        _view(self.root, _simple_view(["WI-A"]))

        nodes = {node.id: node for node in self.build().nodes}

        self.assertEqual(nodes["WI-A"].offscreen_predecessors, 1)
        self.assertEqual(nodes["WI-A"].state, "waiting")
        self.assertTrue(nodes["WI-ELSEWHERE"].offscreen)
        self.assertEqual(nodes["WI-ELSEWHERE"].lane_source, "offscreen")

    def test_unknown_view_references_are_diagnosed(self) -> None:
        _work_item(self.root, "WI-A")
        _workstream(self.root, "WS-A", ["WI-A"])
        _view(self.root, _simple_view(["WI-A", "WI-NOPE"], lanes=["WS-A", "WS-NOPE"]))

        built = self.build()

        self.assertEqual(self.codes(built).count("unknown_view_reference"), 2)

    def test_changed_sources_make_a_snapshot_stale(self) -> None:
        _work_item(self.root, "WI-A")
        _workstream(self.root, "WS-A", ["WI-A"])
        _view(self.root, _simple_view(["WI-A"]))
        built = self.build()
        self.assertEqual(snapshot.freshness_diagnostics(built, self.root), ())

        _work_item(self.root, "WI-A", depends_on=["WI-B"])

        stale = snapshot.freshness_diagnostics(built, self.root)
        self.assertEqual([item.code for item in stale], ["stale_snapshot"])


class ViewDeclarationTest(_RepoMixin, unittest.TestCase):
    def test_unknown_and_unsafe_views_are_rejected(self) -> None:
        with self.assertRaises(FileNotFoundError):
            view_module.load_view(self.root, "missing")
        with self.assertRaises(view_module.ViewDeclarationError):
            view_module.load_view(self.root, "../escape")

    def test_malformed_declarations_list_every_problem(self) -> None:
        _view(
            self.root,
            '---\nid: "other"\ntitle: ""\nlanes: []\nphases:\n- id: "unplaced"\n'
            '  title: "x"\n  work_items: []\nextra: 1\n---\n',
        )

        with self.assertRaises(view_module.ViewDeclarationError) as err_ctx:
            view_module.load_view(self.root, "main")

        problems = " ".join(err_ctx.exception.problems)
        for expected in ("id must be", "title", "lanes", "reserved", "unknown fields"):
            self.assertIn(expected, problems)

    def test_lrh_validate_reports_invalid_and_unknown_views(self) -> None:
        _work_item(self.root, "WI-A")
        _workstream(self.root, "WS-A", ["WI-A"])
        _view(self.root, _simple_view(["WI-NOPE"]), name="main")
        _view(self.root, '---\nid: "wrong"\ntitle: "Bad"\n---\n', name="bad")

        codes = {
            issue.code
            for issue in validate_project(self.root / "project").issues
            if issue.file.startswith("views/")
        }

        self.assertEqual(
            codes,
            {"DEPENDENCY_MAP_VIEW_INVALID", "DEPENDENCY_MAP_VIEW_UNKNOWN_REFERENCE"},
        )


def _simple_view(
    work_items: list[str], *, lanes: list[str] | None = None, extra: str = ""
) -> str:
    lane_lines = "".join(f'- workstream: "{lane}"\n' for lane in lanes or ["WS-A"])
    items = ", ".join(f'"{item}"' for item in work_items)
    return (
        f'---\nid: "main"\ntitle: "Main"\nlanes:\n{lane_lines}phases:\n'
        f'- id: "one"\n  title: "One"\n  work_items: [{items}]\n{extra}---\nBody.\n'
    )


if __name__ == "__main__":
    unittest.main()
