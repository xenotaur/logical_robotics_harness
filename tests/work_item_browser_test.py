import tempfile
import unittest
from pathlib import Path

from lrh import core_state, work_item_browser
from lrh.control import roadmap


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _work_item(
    item_id: str,
    *,
    status: str = "proposed",
    item_type: str = "deliverable",
    roadmap_ids: tuple[str, ...] = (),
    extra: str = "",
) -> str:
    phases = "".join(f"  - {phase}\n" for phase in roadmap_ids)
    related = f"related_roadmap:\n{phases}" if phases else "related_roadmap: []\n"
    return (
        f"---\nid: {item_id}\ntitle: {item_id} title\ntype: {item_type}\n"
        f"status: {status}\nblocked: false\nblocked_reason: null\nresolution: null\n"
        f"{related}{extra}---\n\nBody.\n"
    )


READY_FIELDS = """execution_ready: true
autonomy_level: human_gated
operation_risk: read_only
allowed_paths:
  - src/
forbidden_paths:
  - .env
validation_commands:
  - scripts/test
required_evidence:
  - tests
expected_artifacts:
  - summary
requires_human_approval: true
requires_human_merge: true
requires_human_closeout: true
"""


def _write_project(root: Path) -> Path:
    project_dir = root / "project"
    _write(
        project_dir / "focus" / "current_focus.md",
        "---\nid: FOCUS-1\ntitle: Focus\nstatus: active\n---\nFocus.\n",
    )
    _write(
        project_dir / "workstreams" / "active" / "WS-ONE.md",
        "---\nid: WS-ONE\nkind: planning_node\ntitle: Stream one\nstatus: active\n"
        "stage: executing\nrelated_roadmap:\n  - PHASE-02\nwork_items:\n"
        "  - WI-A\n  - WI-B\n---\nBody.\n",
    )
    _write(
        project_dir / "work_items" / "proposed" / "WI-A.md",
        _work_item("WI-A", roadmap_ids=("PHASE-01",)),
    )
    _write(
        project_dir / "work_items" / "active" / "WI-B.md",
        _work_item("WI-B", status="active", item_type="operation"),
    )
    _write(
        project_dir / "work_items" / "resolved" / "WI-C.md",
        _work_item("WI-C", status="resolved").replace(
            "resolution: null", "resolution: 'Done.'"
        ),
    )
    _write(
        project_dir / "roadmap" / "roadmap.md",
        "---\nid: ROADMAP-CORE\ntitle: Roadmap\nstatus: active\n---\n",
    )
    for phase_id, order in (("PHASE-01", "1"), ("PHASE-02", "2")):
        _write(
            project_dir / "roadmap" / f"{phase_id}.md",
            f"---\nid: {phase_id}\ntitle: {phase_id} title\nstatus: proposed\n"
            f"parent: ROADMAP-CORE\norder: {order}\n---\n",
        )
    return project_dir


class TestWorkItemBrowserPayload(unittest.TestCase):
    def setUp(self) -> None:
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        root = Path(tmp_dir.name)
        project_dir = _write_project(root)
        self.state = core_state.load_core_project_state(root)
        self.roadmap = roadmap.load_roadmap(project_dir)

    def _payload(self, **filters: str) -> dict[str, object]:
        return work_item_browser.browser_payload(
            self.state, self.roadmap, "main", work_item_browser.parse_filters(filters)
        )

    @staticmethod
    def _ids(payload: dict[str, object]) -> dict[str, list[str]]:
        return {
            str(group["id"]): [str(item["id"]) for item in group["work_items"]]
            for group in payload["groups"]
        }

    def test_groups_by_parent_workstream_with_unparented_last(self) -> None:
        payload = self._payload()

        self.assertEqual(
            self._ids(payload),
            {"WS-ONE": ["WI-B", "WI-A"], "Unparented": ["WI-C"]},
        )
        self.assertEqual(list(self._ids(payload))[-1], "Unparented")
        self.assertEqual((payload["total"], payload["shown"]), (3, 3))
        # Open work comes first: active WI-B before proposed WI-A.
        first = payload["groups"][0]["work_items"][1]
        self.assertEqual(first["detail_url"], "/project/main/work-items/WI-A")
        self.assertEqual(first["prompt_url"], "/project/main/work-items/WI-A/prompt")

    def test_roadmap_matches_own_phase_or_through_the_workstream(self) -> None:
        rows = {
            item["id"]: item["roadmap"]
            for group in self._payload()["groups"]
            for item in group["work_items"]
        }

        self.assertEqual(
            rows["WI-A"],
            [
                {"phase": "PHASE-01", "via": None},
                {"phase": "PHASE-02", "via": "WS-ONE"},
            ],
        )
        self.assertEqual(rows["WI-B"], [{"phase": "PHASE-02", "via": "WS-ONE"}])
        self.assertEqual(rows["WI-C"], [])
        self.assertEqual(
            self._ids(self._payload(roadmap="PHASE-02")), {"WS-ONE": ["WI-B", "WI-A"]}
        )
        phases = self._payload()["roadmap"]
        self.assertEqual(
            [(phase["id"], phase["work_items"]) for phase in phases["phases"]],
            [("PHASE-01", 1), ("PHASE-02", 2)],
        )
        self.assertEqual(phases["unlinked_work_items"], 1)
        self.assertEqual(phases["diagnostics"], [])

    def test_filters_combine_with_and(self) -> None:
        self.assertEqual(
            self._ids(self._payload(status="active")), {"WS-ONE": ["WI-B"]}
        )
        self.assertEqual(
            self._ids(self._payload(status="proposed", type="operation")), {}
        )
        self.assertEqual(
            self._ids(self._payload(workstream="Unparented")), {"Unparented": ["WI-C"]}
        )
        self.assertEqual(
            self._ids(self._payload(active="no", workstream="WS-ONE")),
            {"WS-ONE": ["WI-B", "WI-A"]},
        )
        self.assertEqual(self._ids(self._payload(ready="yes")), {})

    def test_child_workstream_follows_its_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_dir = _write_project(root)
            parent = project_dir / "workstreams" / "active" / "WS-ONE.md"
            parent.write_text(
                parent.read_text(encoding="utf-8").replace(
                    "related_roadmap:", "children:\n  - WS-AAA\nrelated_roadmap:"
                ),
                encoding="utf-8",
            )
            _write(
                project_dir / "workstreams" / "active" / "WS-AAA.md",
                "---\nid: WS-AAA\nkind: planning_node\ntitle: Child stream\n"
                "status: active\nstage: executing\nparent_id: WS-ONE\n"
                "work_items:\n  - WI-E\n---\nBody.\n",
            )
            _write(
                project_dir / "work_items" / "proposed" / "WI-E.md", _work_item("WI-E")
            )
            state = core_state.load_core_project_state(root)

        payload = work_item_browser.browser_payload(state, self.roadmap, "main", {})
        page = work_item_browser.render_page(payload, "")

        self.assertTrue(state.validation.is_valid)
        self.assertEqual(
            [(group["id"], group["parent"]) for group in payload["groups"]],
            [("WS-ONE", None), ("WS-AAA", "WS-ONE"), ("Unparented", None)],
        )
        self.assertIn("Part of WS-ONE. 1 work item", page)

    def test_ready_filter_reads_the_flag_and_blocked_shows_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_dir = _write_project(root)
            _write(
                project_dir / "work_items" / "active" / "WI-R.md",
                _work_item(
                    "WI-R",
                    status="active",
                    extra=READY_FIELDS,
                ).replace(
                    "blocked: false\nblocked_reason: null",
                    "blocked: true\n" "blocked_reason: 'Waiting on review.'",
                ),
            )
            state = core_state.load_core_project_state(root)

        payload = work_item_browser.browser_payload(
            state, self.roadmap, "main", {"ready": "yes"}
        )
        page = work_item_browser.render_page(payload, "")

        self.assertEqual(self._ids(payload), {"Unparented": ["WI-R"]})
        self.assertIn("Execution-ready flag set", page)
        self.assertIn("✕</span> Blocked", page)

    def test_set_workstream_filter_gets_an_any_link(self) -> None:
        page = work_item_browser.render_page(
            self._payload(workstream="WS-ONE", status="active"), ""
        )

        self.assertIn('aria-label="Filter by workstream"', page)
        self.assertIn('href="/project/main/work-items?status=active">Any</a>', page)
        # Every type stays offered even when other filters hide it.
        self.assertIn(">deliverable</a>", page)

    def test_unknown_flag_values_match_nothing(self) -> None:
        for key in ("ready", "active"):
            with self.subTest(key=key):
                payload = self._payload(**{key: "maybe"})

                self.assertEqual(payload["groups"], [])
                self.assertEqual(payload["shown"], 0)
                self.assertEqual(
                    payload["diagnostics"], [f"No work item matches {key} 'maybe'."]
                )

    def test_validation_note_matches_what_loaded(self) -> None:
        payload = dict(self._payload())
        payload["validation"] = {"is_valid": False, "error_count": 1}

        page = work_item_browser.render_page(payload, "")

        # Work items still loaded (as for dependency-map view errors).
        self.assertIn("the list below may be incomplete", page)
        self.assertNotIn("cannot be listed", page)
        self.assertIn("WI-A", page)

    def test_unknown_value_gives_empty_result_and_diagnostic(self) -> None:
        payload = self._payload(type="spaceship", other="ignored")

        self.assertEqual(payload["groups"], [])
        self.assertEqual(payload["filters"], {"type": "spaceship"})
        self.assertEqual(
            payload["diagnostics"], ["No work item matches type 'spaceship'."]
        )

    def test_invalid_project_says_why_the_list_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_dir = _write_project(root)
            _write(
                project_dir / "work_items" / "resolved" / "WI-D.md",
                _work_item("WI-D", status="resolved"),
            )
            state = core_state.load_core_project_state(root)

        payload = work_item_browser.browser_payload(state, self.roadmap, "main", {})
        page = work_item_browser.render_page(payload, "")

        self.assertFalse(payload["validation"]["is_valid"])
        self.assertIn("lrh validate", page)

    def test_rendered_page_escapes_hostile_filter_values(self) -> None:
        hostile = '"><script>alert(1)</script>'
        payload = self._payload(status=hostile, workstream=hostile)

        page = work_item_browser.render_page(payload, "")

        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)
        # Filter links carry the value URL-encoded, never raw.
        self.assertNotIn('href="/project/main/work-items?status="', page)

    def test_rendered_page_pairs_every_status_with_glyph_and_text(self) -> None:
        page = work_item_browser.render_page(self._payload(), "")

        for label, glyph in (("Proposed", "○"), ("Active", "▶"), ("Resolved", "✓")):
            self.assertIn(f'<span aria-hidden="true">{glyph}</span> {label}', page)
        self.assertIn("PHASE-02 (via WS-ONE)", page)
        self.assertIn("No phase", page)
        self.assertNotIn("<form", page)


if __name__ == "__main__":
    unittest.main()
