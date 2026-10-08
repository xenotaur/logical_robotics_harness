"""Tests for ``lrh dependency-map snapshot``."""

from __future__ import annotations

import json
import pathlib
import tempfile
import unittest
import unittest.mock

from lrh.cli import main as cli_main
from lrh.dependency_maps import snapshot
from tests import testing_support

_VIEW = (
    '---\nid: "main"\ntitle: "Main"\nlanes:\n- workstream: "WS-A"\nphases:\n'
    '- id: "one"\n  title: "One"\n  work_items: ["WI-A"]\n---\nBody.\n'
)


def _write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _project(root: pathlib.Path) -> None:
    _write(
        root / "project" / "focus" / "current_focus.md",
        "---\nid: FOCUS-1\ntitle: Focus\nstatus: active\n---\nBody.\n",
    )
    _write(
        root / "project" / "work_items" / "proposed" / "WI-A.md",
        "---\nid: WI-A\ntitle: Alpha\ntype: deliverable\nstatus: proposed\n"
        "blocked: false\nblocked_reason: null\nresolution: null\n---\nBody.\n",
    )
    _write(
        root / "project" / "workstreams" / "active" / "WS-A.md",
        "---\nid: WS-A\nkind: planning_node\ntitle: Stream\nstatus: active\n"
        "stage: executing\nwork_items:\n  - WI-A\n---\nBody.\n",
    )
    _write(root / "project" / "views" / "dependency_maps" / "main.md", _VIEW)


class DependencyMapCliTest(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str, str]:
        with unittest.mock.patch("sys.argv", ["lrh", "dependency-map", *args]):
            with testing_support.capture_output(capture_stderr=True) as captured:
                with self.assertRaises(SystemExit) as err_ctx:
                    cli_main.main()
        return (
            err_ctx.exception.code,
            captured.stdout.getvalue(),
            captured.stderr.getvalue(),
        )

    def test_snapshot_prints_the_versioned_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _project(root)
            code, stdout, stderr = self.run_cli(
                "snapshot", "main", "--project-root", tmp_dir
            )
            expected = json.loads(snapshot.build_snapshot(root, "main").to_json())

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        payload = json.loads(stdout)
        self.assertEqual(payload["schema_version"], snapshot.SCHEMA_VERSION)
        payload.pop("generated_at")
        expected.pop("generated_at")
        self.assertEqual(payload, expected)

    def test_unknown_or_invalid_views_exit_non_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _project(root)
            _write(
                root / "project" / "views" / "dependency_maps" / "bad.md",
                '---\nid: "bad"\n---\n',
            )
            for view_id, message in (
                ("missing", "no dependency-map view named 'missing'"),
                ("bad", "title must be a non-empty string"),
            ):
                with self.subTest(view=view_id):
                    code, stdout, stderr = self.run_cli(
                        "snapshot", view_id, "--project-root", tmp_dir
                    )
                    self.assertEqual(code, 1)
                    self.assertEqual(stdout, "")
                    self.assertIn(message, stderr)


if __name__ == "__main__":
    unittest.main()
