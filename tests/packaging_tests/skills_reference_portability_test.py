"""Regression coverage for LRH skills used outside the LRH repository."""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

from lrh.skills import installer

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "skills" / "third_party_no_docs"
SOURCE_ROOT = REPO_ROOT / "src" / "lrh" / "skills"
TARGET_ROOTS = (
    REPO_ROOT / ".claude" / "skills",
    REPO_ROOT / ".agents" / "skills",
    REPO_ROOT / ".gemini" / "plugins" / "lrh" / "skills",
)
AFFECTED_SKILLS = (
    "lrh-codex-export",
    "lrh-codex-session",
    "lrh-config-skills",
    "lrh-doc-audit",
)


class SkillsReferencePortabilityTest(unittest.TestCase):
    def test_third_party_fixture_has_project_control_without_docs_tree(self) -> None:
        self.assertTrue((FIXTURE_ROOT / "project").is_dir())
        self.assertFalse((FIXTURE_ROOT / "docs").exists())

    def test_affected_source_skills_define_portable_reference_behavior(self) -> None:
        for skill_name in AFFECTED_SKILLS:
            with self.subTest(skill=skill_name):
                content = (SOURCE_ROOT / skill_name / "SKILL.md").read_text()
                self.assertIn("optional", content.lower())
                self.assertIn("client", content.lower())
                self.assertIn("installed", content.lower())

    def test_rendered_targets_preserve_portability_guidance(self) -> None:
        for target_root in TARGET_ROOTS:
            for skill_name in AFFECTED_SKILLS:
                with self.subTest(target=target_root, skill=skill_name):
                    content = (target_root / skill_name / "SKILL.md").read_text()
                    self.assertIn("client", content.lower())
                    self.assertIn("optional", content.lower())

    def test_codex_export_missing_reference_is_not_runtime_failure(self) -> None:
        content = (SOURCE_ROOT / "lrh-codex-export" / "SKILL.md").read_text()
        self.assertIn("lrh conversation --help", content)
        self.assertIn(
            "missing LRH-owned documentation file as an export failure", content
        )

    def test_bundled_audit_reference_is_authoritative_without_docs_tree(self) -> None:
        content = (
            SOURCE_ROOT / "lrh-doc-audit" / "references" / "audit-requirements.md"
        ).read_text()
        self.assertIn("bundled reference", content)
        self.assertIn("not required in an independent", content)

    def test_installed_skill_and_cli_help_work_without_client_docs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            client_root = pathlib.Path(temporary_directory) / "client"
            shutil.copytree(FIXTURE_ROOT, client_root)
            installed_root = client_root / ".agents" / "skills"

            installer.install_skills(
                skills_dir=installed_root,
                target=installer.SkillTarget.CODEX,
                source=SOURCE_ROOT,
                force=True,
            )

            self.assertTrue(
                (installed_root / "lrh-codex-export" / "SKILL.md").is_file()
            )
            self.assertFalse(
                (
                    client_root / "docs" / "reference" / "cli" / "conversation.md"
                ).exists()
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "conversation",
                    "current-codex-thread-id",
                    "--help",
                ],
                cwd=client_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("current-codex-thread-id", result.stdout)


if __name__ == "__main__":
    unittest.main()
