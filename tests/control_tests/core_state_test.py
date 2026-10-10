import os
import tempfile
import threading
import time
import unittest
import unittest.mock
from collections.abc import Callable
from pathlib import Path
from types import MappingProxyType

from lrh import core_state
from lrh.control import validator


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

    def test_blocked_flag_and_reason_project_through_with_empty_blocked_by(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write_representative_project(root)
            _write(
                root / "project" / "work_items" / "active" / "WI-A.md",
                """---
id: WI-A
title: Alpha
type: investigation
status: active
blocked: true
blocked_reason: waiting on an external decision
resolution: null
related_focus:
  - FOCUS-1
depends_on:
  - WI-B
---
""",
            )

            state = core_state.load_core_project_state(root)
            item = state.work_items_by_id["WI-A"]

            self.assertTrue(item.blocked)
            self.assertEqual(item.blocked_reason, "waiting on an external decision")
            self.assertEqual(item.blocked_by, ())

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

    def test_dependency_map_view_errors_do_not_blank_planning_state(self) -> None:
        views = {
            "broken.md": '---\nid: "broken"\ntitle: "Broken"\n---\n',
            "stale.md": (
                '---\nid: "stale"\ntitle: "Stale"\nlanes:\n- workstream: "WS-GONE"\n'
                'phases:\n- id: "one"\n  title: "One"\n  work_items: ["WI-GONE"]\n'
                "---\n"
            ),
        }
        for name, text in views.items():
            with self.subTest(view=name), tempfile.TemporaryDirectory() as tmp_dir:
                root = Path(tmp_dir)
                _write_representative_project(root)
                _write_view(root, name, text)

                state = core_state.load_core_project_state(root)

                # The view problem still fails validation and is reported...
                self.assertFalse(state.validation.is_valid)
                self.assertGreater(state.validation.error_count, 0)
                codes = {d.code for d in state.validation.diagnostics}
                self.assertTrue(codes & validator.DEPENDENCY_MAP_VIEW_ISSUE_CODES)
                self.assertFalse(state.prompt_inputs.validation_is_valid)
                # ...but no longer hides the planning state it does not affect.
                self.assertEqual(set(state.work_items_by_id), {"WI-A", "WI-B"})
                self.assertIsNotNone(state.current_focus)
                self.assertEqual(state.current_focus.id, "FOCUS-1")
                self.assertEqual(
                    state.prompt_inputs.active_leaf_work_item_ids, ("WI-A", "WI-B")
                )

    def test_planning_errors_still_blank_state_alongside_view_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write_representative_project(root, duplicate_work_item=True)
            _write_view(root, "broken.md", '---\nid: "broken"\ntitle: "Broken"\n---\n')

            state = core_state.load_core_project_state(root)

            self.assertEqual(state.work_items, ())
            self.assertIsNone(state.current_focus)

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


class TestProjectStateCache(unittest.TestCase):
    """The cache reuses a value only while the control files are unchanged."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        _write_representative_project(self.root)
        self.project_dir = self.root / "project"
        self.cache = core_state.ProjectStateCache()
        self.calls = 0

    def _get(self) -> int:
        def compute() -> int:
            self.calls += 1
            return self.calls

        return self.cache.get("value", self.project_dir, compute)

    def _work_item(self) -> Path:
        return self.project_dir / "work_items" / "active" / "WI-A.md"

    def test_an_unchanged_project_is_computed_once(self) -> None:
        self.assertEqual([self._get(), self._get(), self._get()], [1, 1, 1])

    def test_every_kind_of_file_change_invalidates(self) -> None:
        path = self._work_item()
        changes = {
            "edit, same size": lambda: (
                path.write_text(path.read_text().replace("WI-A", "WI-Z", 1)),
                os.utime(path, ns=(1_000_000_000, 1_000_000_000)),
            ),
            "edit, new size": lambda: path.write_text(path.read_text() + "\nmore\n"),
            "add": lambda: _write(path.with_name("NOTES.md"), "notes\n"),
            "rename": lambda: path.with_name("NOTES.md").rename(
                path.with_name("NOTES2.md")
            ),
            "delete": lambda: path.with_name("NOTES2.md").unlink(),
            "atomic replace": lambda: (
                _write(path.with_name("tmp.md"), path.read_text()),
                os.replace(path.with_name("tmp.md"), path),
            ),
        }
        expected = self._get()
        for name, change in changes.items():
            with self.subTest(change=name):
                change()
                expected += 1
                self.assertEqual(self._get(), expected)
                self.assertEqual(self._get(), expected, "and is cached again")

    def test_changes_inside_a_symlinked_directory_invalidate(self) -> None:
        with tempfile.TemporaryDirectory() as archive_dir:
            archive = Path(archive_dir)
            _write(archive / "RECORD.md", "one\n")
            (self.project_dir / "archive").symlink_to(archive, target_is_directory=True)
            # A link back up must not loop the walk.
            (archive / "loop").symlink_to(self.project_dir, target_is_directory=True)
            first = self._get()
            self.assertEqual(self._get(), first)
            _write(archive / "RECORD.md", "one, edited\n")
            self.assertEqual(self._get(), first + 1)

    def _flight_waiters(self, name: str) -> int:
        key = (name, str(self.project_dir.resolve()))
        with self.cache._lock:
            flight = self.cache._flights.get(key)
            return flight.waiters if flight is not None else -1

    def _wait_for_waiters(self, name: str, count: int) -> None:
        deadline = time.monotonic() + 5
        while self._flight_waiters(name) < count:
            self.assertLess(time.monotonic(), deadline, "waiters never blocked")
            time.sleep(0.005)

    def _start(self, target: Callable[[], None]) -> threading.Thread:
        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        return thread

    def _join(self, *threads: threading.Thread) -> None:
        for thread in threads:
            thread.join(5)
            self.assertFalse(thread.is_alive(), "a cache caller hung")

    def test_concurrent_misses_share_one_computation(self) -> None:
        release = threading.Event()
        calls: list[str] = []
        results: list[str] = []

        def slow() -> str:
            calls.append("compute")
            release.wait(5)
            return "shared"

        def call() -> None:
            results.append(self.cache.get("v", self.project_dir, slow))

        owner = self._start(call)
        self._wait_for_waiters("v", 0)
        waiters = [self._start(call) for _ in range(4)]
        # Every waiter is blocked on the owner's build before it finishes.
        self._wait_for_waiters("v", 4)
        release.set()
        self._join(owner, *waiters)
        self.assertEqual(calls, ["compute"])
        self.assertEqual(results, ["shared"] * 5)

    def test_a_waiter_on_a_failed_build_computes_for_itself(self) -> None:
        release = threading.Event()
        errors: list[Exception] = []
        waited: list[str] = []

        def failing() -> str:
            release.wait(5)
            raise ValueError("boom")

        def own() -> None:
            try:
                self.cache.get("v", self.project_dir, failing)
            except ValueError as error:
                errors.append(error)

        owner = self._start(own)
        self._wait_for_waiters("v", 0)
        waiter = self._start(
            lambda: waited.append(self.cache.get("v", self.project_dir, lambda: "own"))
        )
        self._wait_for_waiters("v", 1)
        release.set()
        self._join(owner, waiter)
        self.assertEqual(len(errors), 1)
        self.assertEqual(waited, ["own"])
        # The fallback build was published: the next caller hits the cache.
        self.assertEqual(self.cache.get("v", self.project_dir, lambda: "new"), "own")

    def test_a_stalled_build_does_not_block_waiters_forever(self) -> None:
        release = threading.Event()
        self.addCleanup(release.set)
        waited: list[str] = []

        owner = self._start(
            lambda: self.cache.get("v", self.project_dir, lambda: release.wait(5))
        )
        self._wait_for_waiters("v", 0)
        with unittest.mock.patch.object(core_state, "_FLIGHT_WAIT_SECONDS", 0.05):
            waiter = self._start(
                lambda: waited.append(
                    self.cache.get("v", self.project_dir, lambda: "own")
                )
            )
            self._join(waiter)
        release.set()
        self._join(owner)
        self.assertEqual(waited, ["own"])

    def test_errors_are_not_cached(self) -> None:
        def fail() -> int:
            raise ValueError("boom")

        with self.assertRaises(ValueError):
            self.cache.get("value", self.project_dir, fail)
        self.assertEqual(self._get(), 1)

    def test_names_and_projects_are_separate_entries(self) -> None:
        self.cache.get("a", self.project_dir, lambda: "a")
        self.assertEqual(self.cache.get("b", self.project_dir, lambda: "b"), "b")
        with tempfile.TemporaryDirectory() as other:
            other_dir = Path(other) / "project"
            _write_representative_project(Path(other))
            self.assertEqual(self.cache.get("a", other_dir, lambda: "other"), "other")
        self.assertEqual(self.cache.get("a", self.project_dir, lambda: "x"), "a")

    def test_reserve_grows_capacity_and_never_shrinks_it(self) -> None:
        cache = core_state.ProjectStateCache(max_entries=1)
        cache.reserve(3)
        cache.reserve(2)
        for name in ("a", "b", "c"):
            cache.get(name, self.project_dir, lambda name=name: name)
        self.assertEqual(
            [cache.get(n, self.project_dir, lambda: "new") for n in ("a", "b", "c")],
            ["a", "b", "c"],
        )

    def test_the_oldest_entries_are_evicted(self) -> None:
        cache = core_state.ProjectStateCache(max_entries=2)
        for name in ("a", "b", "c"):
            cache.get(name, self.project_dir, lambda name=name: name)
        self.assertEqual(cache.get("a", self.project_dir, lambda: "new"), "new")
        self.assertEqual(cache.get("c", self.project_dir, lambda: "new"), "c")

    def test_concurrent_readers_share_one_cache(self) -> None:
        results: list[int] = []
        lock = threading.Lock()

        def read() -> None:
            value = self._get()
            with lock:
                results.append(value)

        self._get()
        threads = [threading.Thread(target=read) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(results, [1] * 8)

    def test_cached_core_state_equals_an_uncached_load(self) -> None:
        cached = core_state.load_core_project_state(self.root, cache=self.cache)

        self.assertEqual(cached, core_state.load_core_project_state(self.root))
        self.assertIs(
            core_state.load_core_project_state(self.root, cache=self.cache), cached
        )
        path = self._work_item()
        path.write_text(path.read_text().replace("status: active", "status: blocked"))
        reloaded = core_state.load_core_project_state(self.root, cache=self.cache)
        self.assertIsNot(reloaded, cached)
        self.assertEqual(reloaded, core_state.load_core_project_state(self.root))


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


def _write_view(root: Path, name: str, text: str) -> None:
    views_dir = root / "project" / "views" / "dependency_maps"
    views_dir.mkdir(parents=True, exist_ok=True)
    _write(views_dir / name, text)


if __name__ == "__main__":
    unittest.main()
