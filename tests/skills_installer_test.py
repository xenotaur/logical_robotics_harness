"""Unit tests for lrh.skills.installer."""

from __future__ import annotations

import importlib.resources
import shutil
import tempfile
import unittest
from pathlib import Path

from lrh.skills import installer


class TestInstallSkills(unittest.TestCase):
    def _make_skills_dir(self) -> Path:
        """Return a not-yet-existing path for use as a skills directory."""
        parent = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, parent, True)
        return parent / "skills"

    def test_install_new_skills(self) -> None:
        skills_dir = self._make_skills_dir()
        report = installer.install_skills(skills_dir=skills_dir)
        self.assertTrue(report.newly_created_skills_dir)
        self.assertTrue(len(report.results) > 0)
        for result in report.results:
            self.assertEqual(result.status, installer.SkillStatus.INSTALLED)
            self.assertTrue((skills_dir / result.name / "SKILL.md").exists())

    def test_install_idempotent(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir)
        report2 = installer.install_skills(skills_dir=skills_dir)
        self.assertFalse(report2.newly_created_skills_dir)
        for result in report2.results:
            self.assertEqual(result.status, installer.SkillStatus.UP_TO_DATE)

    def test_dry_run_writes_nothing(self) -> None:
        skills_dir = self._make_skills_dir()
        report = installer.install_skills(skills_dir=skills_dir, dry_run=True)
        self.assertTrue(report.newly_created_skills_dir)
        for result in report.results:
            self.assertEqual(result.status, installer.SkillStatus.INSTALLED)
            self.assertFalse((skills_dir / result.name).exists())

    def test_user_modified_skill_skipped(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir)
        skill_name = installer._skill_names()[0]
        skill_md = skills_dir / skill_name / "SKILL.md"
        skill_md.write_text(skill_md.read_text() + "\n# local modification\n")
        report = installer.install_skills(skills_dir=skills_dir)
        modified = next(r for r in report.results if r.name == skill_name)
        self.assertEqual(modified.status, installer.SkillStatus.USER_MODIFIED)
        self.assertIn("local modification", skill_md.read_text())

    def test_force_overwrites_user_modified(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir)
        skill_name = installer._skill_names()[0]
        skill_md = skills_dir / skill_name / "SKILL.md"
        original = skill_md.read_text()
        skill_md.write_text(original + "\n# local modification\n")
        report = installer.install_skills(skills_dir=skills_dir, force=True)
        forced = next(r for r in report.results if r.name == skill_name)
        self.assertEqual(forced.status, installer.SkillStatus.FORCED)
        self.assertEqual(skill_md.read_text(), original)


class TestInstallNamedSkills(unittest.TestCase):
    def _make_skills_dir(self) -> Path:
        """Return a not-yet-existing path for use as a skills directory."""
        parent = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, parent, True)
        return parent / "skills"

    def test_refreshes_named_skill_with_differing_bytes(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir)
        skill_name = installer._skill_names()[0]
        skill_md = skills_dir / skill_name / "SKILL.md"
        original = skill_md.read_text()
        skill_md.write_text(original + "\n# local modification\n")

        results = installer.install_named_skills([skill_name], skills_dir=skills_dir)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, skill_name)
        self.assertEqual(results[0].status, installer.RefreshStatus.REFRESHED)
        self.assertEqual(skill_md.read_text(), original)

    def test_unnamed_skill_with_differing_bytes_is_left_alone(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir)
        names = installer._skill_names()
        self.assertGreaterEqual(
            len(names), 2, "test requires at least 2 packaged skills"
        )
        target_name, other_name = names[0], names[1]
        other_md = skills_dir / other_name / "SKILL.md"
        other_md.write_text(other_md.read_text() + "\n# local modification\n")

        installer.install_named_skills([target_name], skills_dir=skills_dir)

        self.assertIn("local modification", other_md.read_text())
        report = installer.install_skills(skills_dir=skills_dir)
        other_result = next(r for r in report.results if r.name == other_name)
        self.assertEqual(other_result.status, installer.SkillStatus.USER_MODIFIED)

    def test_absent_name_returns_absent_and_leaves_existing_dir_untouched(
        self,
    ) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir)
        absent_name = "not-a-real-skill"
        stale_dir = skills_dir / absent_name
        stale_dir.mkdir(parents=True)
        (stale_dir / "SKILL.md").write_text("stale content that must survive\n")

        results = installer.install_named_skills([absent_name], skills_dir=skills_dir)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, absent_name)
        self.assertEqual(results[0].status, installer.RefreshStatus.ABSENT)
        self.assertTrue(stale_dir.exists())
        self.assertEqual(
            (stale_dir / "SKILL.md").read_text(), "stale content that must survive\n"
        )

    def test_absent_name_with_no_existing_dir_creates_nothing(self) -> None:
        # Deliberately does not call install_skills() first, unlike the other
        # tests in this class — skills_dir itself must not exist yet, so this
        # actually exercises the mkdir-skip behavior for an all-absent call,
        # not just the absent name's own subdirectory.
        skills_dir = self._make_skills_dir()
        self.assertFalse(skills_dir.exists())
        absent_name = "not-a-real-skill"

        results = installer.install_named_skills([absent_name], skills_dir=skills_dir)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, installer.RefreshStatus.ABSENT)
        self.assertFalse(skills_dir.exists())
        self.assertFalse((skills_dir / absent_name).exists())

    def test_bare_string_raises_instead_of_iterating_characters(self) -> None:
        skills_dir = self._make_skills_dir()
        with self.assertRaises(TypeError):
            installer.install_named_skills("lrh-closeout", skills_dir=skills_dir)

    def test_non_string_element_raises_type_error(self) -> None:
        skills_dir = self._make_skills_dir()
        with self.assertRaises(TypeError):
            installer.install_named_skills([123], skills_dir=skills_dir)

    def test_one_shot_iterable_is_not_silently_consumed(self) -> None:
        skills_dir = self._make_skills_dir()
        skill_name = installer._skill_names()[0]

        results = installer.install_named_skills(
            (name for name in [skill_name]), skills_dir=skills_dir
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, installer.RefreshStatus.REFRESHED)
        self.assertTrue((skills_dir / skill_name / "SKILL.md").exists())


class TestDiffSkill(unittest.TestCase):
    def _make_skills_dir(self) -> Path:
        """Return a not-yet-existing path for use as a skills directory."""
        parent = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, parent, True)
        return parent / "skills"

    def test_diff_no_changes(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir)
        skill_name = installer._skill_names()[0]
        self.assertEqual(installer.diff_skill(skill_name, skills_dir), "")

    def test_diff_modified_text_file(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir)
        skill_name = installer._skill_names()[0]
        skill_md = skills_dir / skill_name / "SKILL.md"
        skill_md.write_text(skill_md.read_text() + "\n# local modification\n")
        diff_text = installer.diff_skill(skill_name, skills_dir)
        self.assertIn("SKILL.md", diff_text)
        self.assertIn("+# local modification", diff_text)

    def test_diff_added_file(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir)
        skill_name = installer._skill_names()[0]
        (skills_dir / skill_name / "extra.md").write_text("not in the package\n")
        diff_text = installer.diff_skill(skill_name, skills_dir)
        self.assertIn("extra.md: added", diff_text)

    def test_diff_removed_file(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir)
        skill_name = installer._skill_names()[0]
        skill_dir = skills_dir / skill_name
        pkg_root = importlib.resources.files(installer._SKILLS_PACKAGE).joinpath(
            skill_name
        )
        pkg_files = installer._collect_pkg_files(pkg_root)
        other_file = next(rel for rel in pkg_files if rel != "SKILL.md")
        (skill_dir / other_file).unlink()
        diff_text = installer.diff_skill(skill_name, skills_dir)
        self.assertIn(f"{other_file}: removed", diff_text)

    def test_diff_binary_file(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir)
        skill_name = installer._skill_names()[0]
        skill_md = skills_dir / skill_name / "SKILL.md"
        skill_md.write_bytes(b"\xff\xfe\x00\x01not valid utf-8")
        diff_text = installer.diff_skill(skill_name, skills_dir)
        self.assertIn("SKILL.md: binary files differ", diff_text)

    def test_diff_symlink_not_dereferenced(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir)
        skill_name = installer._skill_names()[0]
        skill_dir = skills_dir / skill_name

        secret_target = Path(tempfile.mkdtemp()) / "secret.txt"
        self.addCleanup(shutil.rmtree, secret_target.parent, True)
        secret_target.write_text("super-secret-target-contents\n")

        skill_md = skill_dir / "SKILL.md"
        skill_md.unlink()
        skill_md.symlink_to(secret_target)

        diff_text = installer.diff_skill(skill_name, skills_dir)
        self.assertIn("SKILL.md: symlink — skipped", diff_text)
        self.assertNotIn("super-secret-target-contents", diff_text)

    def test_diff_nested_added_symlink_counts_as_modified(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir)
        skill_name = installer._skill_names()[0]
        skill_dir = skills_dir / skill_name

        secret_target = Path(tempfile.mkdtemp()) / "secret.txt"
        self.addCleanup(shutil.rmtree, secret_target.parent, True)
        secret_target.write_text("nested-secret-contents\n")
        (skill_dir / "sneaky.md").symlink_to(secret_target)

        # No other file changed, so pkg_files == fs_files once symlinks are
        # excluded from both sides — the symlink's mere presence must still
        # be detected as a local modification, not silently ignored.
        report = installer.install_skills(skills_dir=skills_dir)
        result = next(r for r in report.results if r.name == skill_name)
        self.assertEqual(result.status, installer.SkillStatus.USER_MODIFIED)

        diff_text = installer.diff_skill(skill_name, skills_dir)
        self.assertIn("sneaky.md: symlink — skipped", diff_text)
        self.assertNotIn("nested-secret-contents", diff_text)

    def test_symlinked_skill_root_detected_as_user_modified(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir)
        skill_name = installer._skill_names()[0]
        skill_dir = skills_dir / skill_name

        secret_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, secret_dir, True)
        (secret_dir / "SKILL.md").write_text("secret-root-contents\n")

        shutil.rmtree(skill_dir)
        skill_dir.symlink_to(secret_dir)

        report = installer.install_skills(skills_dir=skills_dir)
        result = next(r for r in report.results if r.name == skill_name)
        self.assertEqual(result.status, installer.SkillStatus.USER_MODIFIED)

    def test_diff_symlinked_skill_root_not_dereferenced(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir)
        skill_name = installer._skill_names()[0]
        skill_dir = skills_dir / skill_name

        secret_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, secret_dir, True)
        (secret_dir / "SKILL.md").write_text("secret-root-contents\n")

        shutil.rmtree(skill_dir)
        skill_dir.symlink_to(secret_dir)

        diff_text = installer.diff_skill(skill_name, skills_dir)
        self.assertIn("installed skill directory is a symlink", diff_text)
        self.assertNotIn("secret-root-contents", diff_text)


class TestFormatReport(unittest.TestCase):
    def _make_report(
        self,
        statuses: list[installer.SkillStatus],
        newly_created: bool = False,
        skills_dir: Path | None = None,
    ) -> installer.InstallReport:
        results = [
            installer.SkillResult(name=f"skill-{i}", status=s)
            for i, s in enumerate(statuses)
        ]
        return installer.InstallReport(
            results=results,
            newly_created_skills_dir=newly_created,
            skills_dir=skills_dir or Path("/fake/skills"),
        )

    def test_format_installed(self) -> None:
        report = self._make_report([installer.SkillStatus.INSTALLED])
        self.assertIn("installed: skill-0", installer.format_report(report))

    def test_format_up_to_date(self) -> None:
        report = self._make_report([installer.SkillStatus.UP_TO_DATE])
        self.assertIn("up to date: skill-0", installer.format_report(report))

    def test_format_user_modified(self) -> None:
        report = self._make_report([installer.SkillStatus.USER_MODIFIED])
        output = installer.format_report(report)
        self.assertIn("warning:", output)
        self.assertIn("local modifications", output)

    def test_format_forced(self) -> None:
        report = self._make_report([installer.SkillStatus.FORCED])
        self.assertIn("overwritten: skill-0", installer.format_report(report))

    def test_format_dry_run_installed(self) -> None:
        report = self._make_report([installer.SkillStatus.INSTALLED])
        self.assertIn(
            "would install: skill-0", installer.format_report(report, dry_run=True)
        )

    def test_format_dry_run_forced(self) -> None:
        report = self._make_report([installer.SkillStatus.FORCED])
        self.assertIn(
            "would overwrite: skill-0", installer.format_report(report, dry_run=True)
        )

    def test_restart_note_when_newly_created(self) -> None:
        report = self._make_report(
            [installer.SkillStatus.INSTALLED],
            newly_created=True,
            skills_dir=Path("/custom/skills"),
        )
        output = installer.format_report(report)
        self.assertIn("Restart Claude Code", output)
        self.assertIn("/custom/skills", output)

    def test_no_restart_note_in_dry_run(self) -> None:
        report = self._make_report(
            [installer.SkillStatus.INSTALLED], newly_created=True
        )
        self.assertNotIn(
            "Restart Claude Code", installer.format_report(report, dry_run=True)
        )


if __name__ == "__main__":
    unittest.main()
