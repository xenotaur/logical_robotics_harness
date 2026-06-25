"""Unit tests for lrh.skills.installer."""

from __future__ import annotations

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


class TestFormatReport(unittest.TestCase):
    def _make_report(
        self,
        statuses: list[installer.SkillStatus],
        newly_created: bool = False,
    ) -> installer.InstallReport:
        results = [
            installer.SkillResult(name=f"skill-{i}", status=s)
            for i, s in enumerate(statuses)
        ]
        return installer.InstallReport(
            results=results, newly_created_skills_dir=newly_created
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
            [installer.SkillStatus.INSTALLED], newly_created=True
        )
        self.assertIn("Restart Claude Code", installer.format_report(report))

    def test_no_restart_note_in_dry_run(self) -> None:
        report = self._make_report(
            [installer.SkillStatus.INSTALLED], newly_created=True
        )
        self.assertNotIn(
            "Restart Claude Code", installer.format_report(report, dry_run=True)
        )


if __name__ == "__main__":
    unittest.main()
