"""Tests for dependency-map view declarations and snapshots."""

from __future__ import annotations

import datetime
import json
import pathlib
import tempfile
import unittest
import unittest.mock

from lrh.control import validate_project
from lrh.dependency_maps import snapshot
from lrh.dependency_maps import view as view_module
from lrh.work_items import readiness

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
        report = readiness.evaluate_readiness(project_root=self.root)
        expected = {item.work_item_id: item.prompt_ready for item in report.items}
        self.assertEqual(node.prompt_ready, expected["WI-FREE"])

    def test_unblocked_without_prerequisites_says_so(self) -> None:
        _work_item(self.root, "WI-FREE")

        node = self.nodes()["WI-FREE"]

        self.assertEqual(node.state, "unblocked")
        self.assertEqual(
            node.state_reasons, (snapshot.StateReason(kind="no_prerequisites"),)
        )

    def test_an_unmet_blocker_outranks_in_progress(self) -> None:
        _work_item(self.root, "WI-RUN", "active", blocked_by=["WI-WAIT"])

        self.assertEqual(self.nodes()["WI-RUN"].state, "blocked")

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
            ["blocked_by cycle among WI-B", "depends_on cycle among WI-A, WI-B"],
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

    def test_unavailable_readiness_is_a_partial_source(self) -> None:
        _work_item(self.root, "WI-A")
        _workstream(self.root, "WS-A", ["WI-A"])
        _view(self.root, _simple_view(["WI-A"]))

        with unittest.mock.patch.object(
            readiness,
            "evaluate_readiness",
            side_effect=readiness.WorkItemReadinessError("boom"),
        ):
            built = self.build()

        self.assertIn("partial_source", self.codes(built))
        self.assertIsNone(built.nodes[0].prompt_ready)

    def test_parent_id_places_an_item_in_its_lane(self) -> None:
        _work_item(self.root, "WI-CHILD", parent_id="WS-A")
        _workstream(self.root, "WS-A", [])
        _view(self.root, _simple_view(["WI-CHILD"]))

        node = self.build().nodes[0]

        self.assertEqual((node.lane, node.lane_source), ("WS-A", "workstream"))

    def test_offscreen_blockers_and_their_cycles_are_shown(self) -> None:
        _work_item(self.root, "WI-A", blocked_by=["WI-X"], depends_on=["WI-X"])
        _work_item(self.root, "WI-X", depends_on=["WI-Y"])
        _work_item(self.root, "WI-Y", depends_on=["WI-X"])
        _workstream(self.root, "WS-A", ["WI-A"])
        _view(self.root, _simple_view(["WI-A"]))

        built = self.build()
        nodes = {node.id: node for node in built.nodes}

        self.assertEqual(nodes["WI-A"].state, "blocked")
        self.assertEqual(nodes["WI-A"].offscreen_predecessors, 1)
        self.assertTrue(nodes["WI-X"].offscreen)
        self.assertIn(
            "depends_on cycle among WI-X, WI-Y",
            [item.message for item in built.diagnostics],
        )

    def test_a_repeated_item_in_one_phase_is_not_ambiguous(self) -> None:
        _work_item(self.root, "WI-A")
        _workstream(self.root, "WS-A", ["WI-A"])
        _view(self.root, _simple_view(["WI-A", "WI-A"]))

        built = self.build()

        self.assertEqual(built.nodes[0].phase, "one")
        self.assertNotIn("ambiguous_phase", self.codes(built))

    def test_an_override_for_an_item_outside_the_view_is_reported(self) -> None:
        _work_item(self.root, "WI-A")
        _work_item(self.root, "WI-OUT")
        _workstream(self.root, "WS-A", ["WI-A"])
        _view(
            self.root,
            _simple_view(
                ["WI-A"],
                extra=(
                    'lane_overrides:\n- work_item: "WI-OUT"\n  lane: "WS-A"\n'
                    '  reason: "x"\n'
                ),
            ),
        )

        self.assertIn("unused_lane_override", self.codes(self.build()))

    def test_unknown_lifecycles_are_never_eligible(self) -> None:
        _work_item(self.root, "WI-A")
        path = self.root / "project/work_items/proposed/WI-A.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "status: proposed", "status: typo"
            ),
            encoding="utf-8",
        )
        _workstream(self.root, "WS-A", ["WI-A"])
        _view(self.root, _simple_view(["WI-A"]))

        built = self.build()

        self.assertEqual(built.nodes[0].state, "unknown")
        self.assertIn("invalid_lifecycle", self.codes(built))

    def test_freshness_accepts_the_project_directory(self) -> None:
        _work_item(self.root, "WI-A")
        _workstream(self.root, "WS-A", ["WI-A"])
        _view(self.root, _simple_view(["WI-A"]))

        built = snapshot.build_snapshot(self.root / "project", "main", now=_AT)

        self.assertEqual(
            snapshot.freshness_diagnostics(built, self.root / "project"), ()
        )

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

    def test_duplicate_lane_overrides_are_rejected(self) -> None:
        override = '- work_item: "WI-A"\n  lane: "WS-A"\n  reason: "x"\n'
        _view(
            self.root,
            _simple_view(["WI-A"], extra="lane_overrides:\n" + override + override),
        )

        with self.assertRaises(view_module.ViewDeclarationError) as err_ctx:
            view_module.load_view(self.root, "main")

        self.assertIn(
            "must not repeat a work item", " ".join(err_ctx.exception.problems)
        )

    def test_the_project_directory_also_works_as_the_root(self) -> None:
        _work_item(self.root, "WI-A")
        _workstream(self.root, "WS-A", ["WI-A"])
        _view(self.root, _simple_view(["WI-A"]))

        built = snapshot.build_snapshot(self.root / "project", "main", now=_AT)

        self.assertEqual([node.id for node in built.nodes], ["WI-A"])

    def test_from_dict_rejects_malformed_data_with_value_error(self) -> None:
        with self.assertRaises(ValueError):
            snapshot.DependencyMapSnapshot.from_dict({"schema_version": 1})

    def test_from_dict_checks_field_types_and_allowed_values(self) -> None:
        _work_item(self.root, "WI-A", depends_on=["WI-B"])
        _work_item(self.root, "WI-B")
        _workstream(self.root, "WS-A", ["WI-A", "WI-B"])
        _view(self.root, _simple_view(["WI-A", "WI-B"]))
        good = json.loads(self.build().to_json())

        def broken(change) -> dict:
            data = json.loads(json.dumps(good))
            change(data)
            return data

        for label, change in (
            ("view_id type", lambda d: d.update(view_id=1)),
            ("edge resolved type", lambda d: d["edges"][0].update(resolved="false")),
            ("state value", lambda d: d["nodes"][0].update(state="bogus")),
            ("edge kind", lambda d: d["edges"][0].update(kind="relates_to")),
            ("extra field", lambda d: d["project"].update(path="/x")),
            ("nested shape", lambda d: d.update(lanes=["WS-A"])),
            ("schema version type", lambda d: d.update(schema_version=True)),
        ):
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    snapshot.DependencyMapSnapshot.from_dict(broken(change))

    def test_view_read_errors_are_snapshot_errors(self) -> None:
        _work_item(self.root, "WI-A")
        _workstream(self.root, "WS-A", ["WI-A"])
        _view(self.root, _simple_view(["WI-A"]))

        with unittest.mock.patch.object(
            view_module, "parse_markdown_file", side_effect=PermissionError("denied")
        ):
            with self.assertRaises(snapshot.SnapshotError):
                self.build()

    def test_file_names_outside_the_id_grammar_are_rejected(self) -> None:
        _work_item(self.root, "WI-A")
        _workstream(self.root, "WS-A", ["WI-A"])
        _view(self.root, _simple_view(["WI-A"]).replace('"main"', '"Bad"'), name="Bad")

        with self.assertRaises(view_module.ViewDeclarationError) as err_ctx:
            view_module.parse_view(
                self.root / "project/views/dependency_maps/Bad.md", self.root
            )
        self.assertIn("file name", " ".join(err_ctx.exception.problems))
        codes = {
            issue.code
            for issue in validate_project(self.root / "project").issues
            if issue.file.startswith("views/")
        }
        self.assertEqual(codes, {"DEPENDENCY_MAP_VIEW_INVALID"})

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
