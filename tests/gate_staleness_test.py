import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

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
            gate_staleness.DiffHunk(old_start=1, old_count=1, new_start=1, new_count=1),
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

    def _write_skill(self, root: pathlib.Path, body_line: str, typo_line: str) -> None:
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

    def test_invalid_confirmed_commit_raises_not_stale(self) -> None:
        """Regression test: an unresolvable confirmed_commit must raise,
        never be silently read as 'every watched file was added since
        confirmation' (copilot-pull-request-reviewer finding on PR #623)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            self._write_skill(root, "Wait for explicit confirmation.", "Introduction")
            _commit(root, "initial")

            with self.assertRaises(gate_staleness.GateStalenessError):
                gate_staleness.check_gate_staleness(
                    project_root=root,
                    confirmed_commit="deadbeef1234567890abcdef1234567890abcdef",
                    watched_files=("src/lrh/skills/lrh-confirm-fixes/SKILL.md",),
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


class ResolveWatchTargetsInstalledTargetTest(unittest.TestCase):
    """`resolve_watch_targets`/`check_gate_staleness` for a client repo with
    no `src/lrh/skills/` tree -- LRH installed as a package. Fixtures here
    deliberately do NOT create `src/lrh/skills/`, and the untracked-target
    fixture deliberately does NOT commit the installed path into the repo,
    since a fixture that does would hide the exact gap the PR #648 review
    caught in an earlier draft of this work item."""

    def _write_gate_file(
        self, path: pathlib.Path, body_line: str = "Wait for explicit confirmation."
    ) -> None:
        content = (
            "# Some Skill\n\n"
            "<!-- GATE-DEFINITION -->\n"
            "### Step 4 -- Confirm gate\n\n"
            f"{body_line}\n"
            "<!-- /GATE-DEFINITION -->\n\n"
            "## Quality Checklist\n"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def test_project_local_git_tracked_target_detects_staleness(self) -> None:
        one_name = gate_staleness.INSTALLED_CANONICAL_SKILL_NAMES[0]
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "project").mkdir()
            (root / "project" / "agent_skills.yaml").write_text(
                "targets:\n  - claude\nscope: project\n"
            )
            self._write_gate_file(root / ".claude" / "skills" / one_name)
            confirmed_commit = _commit(root, "initial")

            self._write_gate_file(
                root / ".claude" / "skills" / one_name,
                "Proceed automatically without asking.",
            )
            _commit(root, "change gate behavior in installed target")

            result = gate_staleness.check_gate_staleness(
                project_root=root, confirmed_commit=confirmed_commit
            )
            self.assertTrue(result.stale)
            stale_paths = {f.path for f in result.stale_files}
            self.assertIn(f".claude/skills/{one_name}", stale_paths)

    def test_project_local_git_tracked_target_typo_not_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "project").mkdir()
            (root / "project" / "agent_skills.yaml").write_text(
                "targets:\n  - claude\nscope: project\n"
            )
            for name in gate_staleness.INSTALLED_CANONICAL_SKILL_NAMES:
                self._write_gate_file(root / ".claude" / "skills" / name)
            confirmed_commit = _commit(root, "initial")
            (root / "README.md").write_text("unrelated change\n")
            _commit(root, "unrelated change")

            result = gate_staleness.check_gate_staleness(
                project_root=root, confirmed_commit=confirmed_commit
            )
            self.assertFalse(result.stale)

    def test_untracked_target_missing_fingerprint_fails_closed(self) -> None:
        with (
            tempfile.TemporaryDirectory() as tmp,
            tempfile.TemporaryDirectory() as home,
        ):
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "README.md").write_text("placeholder\n")
            confirmed_commit = _commit(root, "initial")

            fake_home = pathlib.Path(home)
            (fake_home / ".claude" / "skills").mkdir(parents=True)
            with mock.patch.object(pathlib.Path, "home", return_value=fake_home):
                result = gate_staleness.check_gate_staleness(
                    project_root=root, confirmed_commit=confirmed_commit
                )
            self.assertTrue(result.stale)
            for stale_file in result.stale_files:
                self.assertIn("fingerprint", stale_file.reason)

    def test_untracked_target_matching_fingerprint_not_stale(self) -> None:
        with (
            tempfile.TemporaryDirectory() as tmp,
            tempfile.TemporaryDirectory() as home,
        ):
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "README.md").write_text("placeholder\n")
            confirmed_commit = _commit(root, "initial")

            fake_home = pathlib.Path(home)
            for name in gate_staleness.INSTALLED_CANONICAL_SKILL_NAMES:
                self._write_gate_file(fake_home / ".claude" / "skills" / name)

            with mock.patch.object(pathlib.Path, "home", return_value=fake_home):
                targets = gate_staleness.resolve_watch_targets(root)
                gate_staleness.record_fingerprints(root, targets)

                result = gate_staleness.check_gate_staleness(
                    project_root=root, confirmed_commit=confirmed_commit
                )
            self.assertFalse(result.stale)

    def test_untracked_target_changed_content_is_stale(self) -> None:
        with (
            tempfile.TemporaryDirectory() as tmp,
            tempfile.TemporaryDirectory() as home,
        ):
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "README.md").write_text("placeholder\n")
            confirmed_commit = _commit(root, "initial")

            fake_home = pathlib.Path(home)
            for name in gate_staleness.INSTALLED_CANONICAL_SKILL_NAMES:
                self._write_gate_file(fake_home / ".claude" / "skills" / name)

            with mock.patch.object(pathlib.Path, "home", return_value=fake_home):
                targets = gate_staleness.resolve_watch_targets(root)
                gate_staleness.record_fingerprints(root, targets)

                one_name = gate_staleness.INSTALLED_CANONICAL_SKILL_NAMES[0]
                self._write_gate_file(
                    fake_home / ".claude" / "skills" / one_name,
                    "Proceed automatically without asking.",
                )

                result = gate_staleness.check_gate_staleness(
                    project_root=root, confirmed_commit=confirmed_commit
                )
            self.assertTrue(result.stale)
            stale_names = {f.path for f in result.stale_files}
            self.assertEqual(stale_names, {f"claude:{one_name}"})

    def test_unresolvable_target_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "project").mkdir()
            # Malformed config (an invalid `targets:` value): install-plan
            # resolution must raise -- via `installer._config_target` --
            # and the whole watch set must fail closed via the
            # `kind="unresolved"` branch specifically, not merely happen to
            # fail closed some other way (e.g. a missing fingerprint file).
            (root / "project" / "agent_skills.yaml").write_text(
                "targets:\n  - not-a-valid-target\n"
            )
            confirmed_commit = _commit(root, "initial")

            result = gate_staleness.check_gate_staleness(
                project_root=root, confirmed_commit=confirmed_commit
            )
            self.assertTrue(result.stale)
            self.assertEqual(len(result.stale_files), len(result.files))
            for stale_file in result.stale_files:
                self.assertIn("could not be resolved", stale_file.reason)

    def test_underscore_prefixed_source_never_watched_for_installed_target(
        self,
    ) -> None:
        """`_shared/chain-defaults.md` must never appear in the resolved
        installed-target watch set: `installer.py`'s own `skill_names()`
        excludes every `_`-prefixed directory from a real install, so
        watching it there would make the check unable to ever pass."""
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "project").mkdir()
            (root / "project" / "agent_skills.yaml").write_text(
                "targets:\n  - claude\nscope: project\n"
            )
            (root / "README.md").write_text("placeholder\n")
            _commit(root, "initial")

            targets = gate_staleness.resolve_watch_targets(root)
            names = {t.canonical_name for t in targets}
            self.assertNotIn("_shared/chain-defaults.md", names)

    def test_record_fingerprints_succeeds_against_realistic_install_fixture(
        self,
    ) -> None:
        """A fixture matching what the real installer actually produces
        (no `_shared/` directory at all, since `skill_names()` never copies
        it) must let `record_fingerprints` complete for every other
        canonical skill -- not raise on the very first (excluded) entry."""
        with (
            tempfile.TemporaryDirectory() as tmp,
            tempfile.TemporaryDirectory() as home,
        ):
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "README.md").write_text("placeholder\n")
            _commit(root, "initial")

            fake_home = pathlib.Path(home)
            for name in gate_staleness.INSTALLED_CANONICAL_SKILL_NAMES:
                self._write_gate_file(fake_home / ".claude" / "skills" / name)

            with mock.patch.object(pathlib.Path, "home", return_value=fake_home):
                targets = gate_staleness.resolve_watch_targets(root)
                fingerprints = gate_staleness.record_fingerprints(root, targets)

            self.assertEqual(
                set(fingerprints),
                {
                    f"claude:{name}"
                    for name in gate_staleness.INSTALLED_CANONICAL_SKILL_NAMES
                },
            )

    def test_record_fingerprints_raises_on_missing_target_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            missing_path = root / "nowhere.md"
            target = gate_staleness.WatchTarget(
                canonical_name="some/skill.md",
                kind="fingerprint",
                absolute_path=missing_path,
            )
            with self.assertRaises(gate_staleness.GateStalenessError) as ctx:
                gate_staleness.record_fingerprints(root, (target,))
            self.assertIn("some/skill.md", str(ctx.exception))

    def test_multi_target_config_watches_every_configured_target(self) -> None:
        """A `targets: [claude, codex]` config must watch BOTH installed
        copies independently -- a divergence in the codex copy alone must
        not be masked by an unchanged claude copy (or vice versa)."""
        with (
            tempfile.TemporaryDirectory() as tmp,
            tempfile.TemporaryDirectory() as home,
        ):
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "project").mkdir()
            (root / "project" / "agent_skills.yaml").write_text(
                "targets:\n  - claude\n  - codex\n"
            )
            (root / "README.md").write_text("placeholder\n")
            confirmed_commit = _commit(root, "initial")

            fake_home = pathlib.Path(home)
            for name in gate_staleness.INSTALLED_CANONICAL_SKILL_NAMES:
                self._write_gate_file(fake_home / ".claude" / "skills" / name)
                self._write_gate_file(fake_home / ".agents" / "skills" / name)

            with mock.patch.object(pathlib.Path, "home", return_value=fake_home):
                targets = gate_staleness.resolve_watch_targets(root)
                qualifiers = {t.canonical_name.split(":", 1)[0] for t in targets}
                self.assertEqual(qualifiers, {"claude", "codex"})

                gate_staleness.record_fingerprints(root, targets)

                one_name = gate_staleness.INSTALLED_CANONICAL_SKILL_NAMES[0]
                self._write_gate_file(
                    fake_home / ".agents" / "skills" / one_name,
                    "Proceed automatically without asking.",
                )

                result = gate_staleness.check_gate_staleness(
                    project_root=root, confirmed_commit=confirmed_commit
                )
            self.assertTrue(result.stale)
            stale_names = {f.path for f in result.stale_files}
            self.assertEqual(stale_names, {f"codex:{one_name}"})


class ResolveWatchTargetsHarnessSelfCheckTest(unittest.TestCase):
    def test_mismatched_canonical_names_length_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "src" / "lrh" / "skills").mkdir(parents=True)
            with self.assertRaises(gate_staleness.GateStalenessError):
                gate_staleness.resolve_watch_targets(
                    root, canonical_names=("only-one-name.md",)
                )


if __name__ == "__main__":
    unittest.main()
