import pathlib
import subprocess
import tempfile
import unittest

from lrh import gate_staleness


def _run(args: list[str], cwd: pathlib.Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo(root: pathlib.Path) -> None:
    _run(["git", "init", "-q"], root)
    _run(["git", "config", "user.email", "test@example.com"], root)
    _run(["git", "config", "user.name", "Test"], root)


def _commit(root: pathlib.Path, message: str) -> str:
    _run(["git", "add", "-A"], root)
    _run(["git", "commit", "-q", "-m", message], root)
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


class ExtractMarkerRangesTest(unittest.TestCase):
    def test_no_markers(self) -> None:
        ranges = gate_staleness.extract_marker_ranges("line one\nline two\n")
        self.assertEqual(ranges, ())

    def test_single_region(self) -> None:
        text = (
            "before\n<!-- GATE-DEFINITION -->\nbody\n"
            "<!-- /GATE-DEFINITION -->\nafter\n"
        )
        ranges = gate_staleness.extract_marker_ranges(text)
        self.assertEqual(ranges, (gate_staleness.LineRange(start=2, end=4),))

    def test_multiple_regions(self) -> None:
        text = (
            "<!-- GATE-DEFINITION -->\na\n<!-- /GATE-DEFINITION -->\n"
            "gap\n"
            "<!-- GATE-DEFINITION -->\nb\n<!-- /GATE-DEFINITION -->\n"
        )
        ranges = gate_staleness.extract_marker_ranges(text)
        self.assertEqual(
            ranges,
            (
                gate_staleness.LineRange(start=1, end=3),
                gate_staleness.LineRange(start=5, end=7),
            ),
        )

    def test_unclosed_marker_raises(self) -> None:
        with self.assertRaises(gate_staleness.GateStalenessError):
            gate_staleness.extract_marker_ranges("<!-- GATE-DEFINITION -->\nbody\n")

    def test_orphan_closer_raises(self) -> None:
        with self.assertRaises(gate_staleness.GateStalenessError):
            gate_staleness.extract_marker_ranges("body\n<!-- /GATE-DEFINITION -->\n")

    def test_nested_marker_raises(self) -> None:
        with self.assertRaises(gate_staleness.GateStalenessError):
            gate_staleness.extract_marker_ranges(
                "<!-- GATE-DEFINITION -->\n<!-- GATE-DEFINITION -->\nbody\n"
                "<!-- /GATE-DEFINITION -->\n<!-- /GATE-DEFINITION -->\n"
            )


class ParseUnifiedDiffHunksTest(unittest.TestCase):
    def test_full_form(self) -> None:
        diff = "@@ -10,3 +10,5 @@\n context\n"
        hunks = gate_staleness.parse_unified_diff_hunks(diff)
        expected = gate_staleness.DiffHunk(
            old_start=10, old_count=3, new_start=10, new_count=5
        )
        self.assertEqual(hunks, (expected,))

    def test_abbreviated_single_line_form(self) -> None:
        diff = "@@ -7 +7 @@\n"
        hunks = gate_staleness.parse_unified_diff_hunks(diff)
        expected = gate_staleness.DiffHunk(
            old_start=7, old_count=1, new_start=7, new_count=1
        )
        self.assertEqual(hunks, (expected,))

    def test_multiple_hunks(self) -> None:
        diff = "@@ -1,2 +1,2 @@\nx\n@@ -20,0 +21,3 @@\ny\n"
        hunks = gate_staleness.parse_unified_diff_hunks(diff)
        self.assertEqual(len(hunks), 2)
        self.assertEqual(hunks[1].old_count, 0)

    def test_no_hunks(self) -> None:
        hunks = gate_staleness.parse_unified_diff_hunks("no hunks here\n")
        self.assertEqual(hunks, ())


class HunksTouchMarkedRegionsTest(unittest.TestCase):
    def test_no_overlap(self) -> None:
        hunks = (
            gate_staleness.DiffHunk(
                old_start=1, old_count=1, new_start=1, new_count=1
            ),
        )
        regions = (gate_staleness.LineRange(start=10, end=20),)
        touched = gate_staleness.hunks_touch_marked_regions(hunks, regions, regions)
        self.assertFalse(touched)

    def test_new_range_overlap(self) -> None:
        hunks = (
            gate_staleness.DiffHunk(
                old_start=1, old_count=1, new_start=15, new_count=1
            ),
        )
        new_regions = (gate_staleness.LineRange(start=10, end=20),)
        touched = gate_staleness.hunks_touch_marked_regions(hunks, (), new_regions)
        self.assertTrue(touched)

    def test_old_range_overlap(self) -> None:
        hunks = (
            gate_staleness.DiffHunk(
                old_start=15, old_count=1, new_start=1, new_count=1
            ),
        )
        old_regions = (gate_staleness.LineRange(start=10, end=20),)
        touched = gate_staleness.hunks_touch_marked_regions(hunks, old_regions, ())
        self.assertTrue(touched)

    def test_zero_count_never_overlaps(self) -> None:
        hunks = (
            gate_staleness.DiffHunk(
                old_start=15, old_count=0, new_start=15, new_count=0
            ),
        )
        regions = (gate_staleness.LineRange(start=10, end=20),)
        touched = gate_staleness.hunks_touch_marked_regions(hunks, regions, regions)
        self.assertFalse(touched)


class CheckGateStalenessIntegrationTest(unittest.TestCase):
    """The exact acceptance-criteria case: typo outside a marker must not
    invalidate; an edit inside a marker must."""

    def _write_skill(
        self, root: pathlib.Path, body_line: str, typo_line: str
    ) -> None:
        content = (
            "# Some Skill\n\n"
            f"{typo_line}\n\n"
            "<!-- GATE-DEFINITION -->\n"
            "### Step 4 -- Confirm gate\n\n"
            f"{body_line}\n"
            "<!-- /GATE-DEFINITION -->\n\n"
            "## Quality Checklist\n"
        )
        path = root / "src/lrh/skills/lrh-confirm-fixes/SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def test_typo_only_edit_does_not_invalidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            self._write_skill(root, "Wait for explicit confirmation.", "Introducton")
            confirmed_commit = _commit(root, "initial")

            self._write_skill(root, "Wait for explicit confirmation.", "Introduction")
            _commit(root, "fix typo outside gate definition")

            result = gate_staleness.check_gate_staleness(
                project_root=root,
                confirmed_commit=confirmed_commit,
                watched_files=("src/lrh/skills/lrh-confirm-fixes/SKILL.md",),
            )
            self.assertFalse(result.stale)

    def test_gate_definition_edit_invalidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            self._write_skill(root, "Wait for explicit confirmation.", "Introduction")
            confirmed_commit = _commit(root, "initial")

            self._write_skill(
                root, "Proceed automatically without asking.", "Introduction"
            )
            _commit(root, "change gate behavior")

            result = gate_staleness.check_gate_staleness(
                project_root=root,
                confirmed_commit=confirmed_commit,
                watched_files=("src/lrh/skills/lrh-confirm-fixes/SKILL.md",),
            )
            self.assertTrue(result.stale)
            self.assertEqual(len(result.stale_files), 1)
            self.assertIn("GATE-DEFINITION", result.stale_files[0].reason)

    def test_new_watched_file_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "README.md").write_text("placeholder\n")
            confirmed_commit = _commit(root, "initial")

            self._write_skill(root, "Wait for explicit confirmation.", "Introduction")
            _commit(root, "add new gate-bearing skill")

            result = gate_staleness.check_gate_staleness(
                project_root=root,
                confirmed_commit=confirmed_commit,
                watched_files=("src/lrh/skills/lrh-confirm-fixes/SKILL.md",),
            )
            self.assertTrue(result.stale)
            reason = result.stale_files[0].reason
            self.assertIn("added since confirmation", reason)

    def test_null_confirmed_commit_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "README.md").write_text("placeholder\n")
            _commit(root, "initial")
            with self.assertRaises(gate_staleness.GateStalenessError):
                gate_staleness.check_gate_staleness(
                    project_root=root, confirmed_commit="null"
                )

    def test_unwatched_file_change_does_not_invalidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            self._write_skill(root, "Wait for explicit confirmation.", "Introduction")
            (root / "README.md").write_text("v1\n")
            confirmed_commit = _commit(root, "initial")

            (root / "README.md").write_text("v2, totally different content\n")
            _commit(root, "edit unwatched file")

            result = gate_staleness.check_gate_staleness(
                project_root=root,
                confirmed_commit=confirmed_commit,
                watched_files=("src/lrh/skills/lrh-confirm-fixes/SKILL.md",),
            )
            self.assertFalse(result.stale)


if __name__ == "__main__":
    unittest.main()
