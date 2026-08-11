"""Unit tests for lrh.skills.installer."""

from __future__ import annotations

import importlib.resources
import json
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

    def test_codex_target_installs_to_codex_skills_dir(self) -> None:
        skills_dir = self._make_skills_dir()
        report = installer.install_skills(
            skills_dir=skills_dir, target=installer.SkillTarget.CODEX
        )
        self.assertEqual(report.target, installer.SkillTarget.CODEX)
        self.assertTrue((skills_dir / report.results[0].name / "SKILL.md").exists())

    def test_claude_target_preserves_canonical_skill_bytes(self) -> None:
        source_dir = self._make_skills_dir()
        skill_dir = source_dir / "sample-skill"
        skill_dir.mkdir(parents=True)
        source_text = "\n".join(
            [
                "---",
                "name: sample-skill",
                "description: Sample skill.",
                "disable-model-invocation: true",
                'argument-hint: "[thing]"',
                "---",
                "",
                "# Sample Skill",
                "",
            ]
        )
        (skill_dir / "SKILL.md").write_text(source_text)
        skills_dir = self._make_skills_dir()

        installer.install_skills(
            skills_dir=skills_dir,
            source=source_dir,
            target=installer.SkillTarget.CLAUDE,
        )

        installed = skills_dir / "sample-skill"
        self.assertEqual((installed / "SKILL.md").read_text(), source_text)
        self.assertFalse((installed / "agents" / "openai.yaml").exists())

    def test_codex_target_strips_claude_metadata_and_emits_openai_policy(
        self,
    ) -> None:
        source_dir = self._make_skills_dir()
        skill_dir = source_dir / "sample-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    "name: sample-skill",
                    "description: Sample skill.",
                    "disable-model-invocation: true",
                    'argument-hint: "[thing]"',
                    "when_to_use: Invoke when the user asks for sample output.",
                    "---",
                    "",
                    "# Sample Skill",
                    "",
                ]
            )
        )
        skills_dir = self._make_skills_dir()

        installer.install_skills(
            skills_dir=skills_dir,
            source=source_dir,
            target=installer.SkillTarget.CODEX,
        )

        installed = skills_dir / "sample-skill"
        skill_md = (installed / "SKILL.md").read_text()
        self.assertIn("name: sample-skill", skill_md)
        self.assertNotIn("disable-model-invocation", skill_md)
        self.assertNotIn("argument-hint", skill_md)
        self.assertNotIn("when_to_use", skill_md)
        self.assertIn(
            "policy:\n  allow_implicit_invocation: false",
            (installed / "agents" / "openai.yaml").read_text(),
        )

    def test_codex_target_strips_when_to_use_without_disable_model_invocation(
        self,
    ) -> None:
        """A skill with when_to_use but no disable-model-invocation (the
        pattern most LRH skills use, per WI-DELIBERATE-MODEL-INVOCATION)
        must still have when_to_use stripped for Codex, since it is not a
        key Codex's own frontmatter schema recognizes."""
        source_dir = self._make_skills_dir()
        skill_dir = source_dir / "sample-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    "name: sample-skill",
                    "description: Sample skill.",
                    "when_to_use: Invoke when the user asks for sample output.",
                    "---",
                    "",
                    "# Sample Skill",
                    "",
                ]
            )
        )
        skills_dir = self._make_skills_dir()

        installer.install_skills(
            skills_dir=skills_dir,
            source=source_dir,
            target=installer.SkillTarget.CODEX,
        )

        installed = skills_dir / "sample-skill"
        skill_md = (installed / "SKILL.md").read_text()
        self.assertIn("name: sample-skill", skill_md)
        self.assertNotIn("when_to_use", skill_md)
        self.assertFalse((installed / "agents" / "openai.yaml").exists())

    def test_codex_target_strips_multiline_claude_metadata(self) -> None:
        source_dir = self._make_skills_dir()
        skill_dir = source_dir / "sample-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    "name: sample-skill",
                    "argument-hint: >",
                    "  [one]",
                    "  [two]",
                    "---",
                    "",
                    "# Sample Skill",
                    "",
                ]
            )
        )
        skills_dir = self._make_skills_dir()

        installer.install_skills(
            skills_dir=skills_dir,
            source=source_dir,
            target=installer.SkillTarget.CODEX,
        )

        skill_md = (skills_dir / "sample-skill" / "SKILL.md").read_text()
        self.assertNotIn("argument-hint", skill_md)
        self.assertNotIn("[one]", skill_md)
        self.assertNotIn("[two]", skill_md)
        self.assertIn("name: sample-skill", skill_md)

    def test_codex_target_reports_invalid_skill_frontmatter_yaml(self) -> None:
        source_dir = self._make_skills_dir()
        skill_dir = source_dir / "sample-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    "name: [unclosed",
                    "---",
                    "",
                    "# Sample Skill",
                    "",
                ]
            )
        )
        skills_dir = self._make_skills_dir()

        with self.assertRaises(installer.SkillSourceError):
            installer.install_skills(
                skills_dir=skills_dir,
                source=source_dir,
                target=installer.SkillTarget.CODEX,
            )

    def test_codex_target_preserves_authored_openai_policy_value(self) -> None:
        source_dir = self._make_skills_dir()
        skill_dir = source_dir / "sample-skill"
        (skill_dir / "agents").mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    "name: sample-skill",
                    "disable-model-invocation: true",
                    "---",
                    "",
                    "# Sample Skill",
                    "",
                ]
            )
        )
        (skill_dir / "agents" / "openai.yaml").write_text(
            "\n".join(
                [
                    "policy:",
                    "  allow_implicit_invocation: true",
                    "ui:",
                    "  invocation_label: Sample",
                    "",
                ]
            )
        )
        skills_dir = self._make_skills_dir()

        installer.install_skills(
            skills_dir=skills_dir,
            source=source_dir,
            target=installer.SkillTarget.CODEX,
        )

        openai_yaml = (
            skills_dir / "sample-skill" / "agents" / "openai.yaml"
        ).read_text()
        self.assertIn("allow_implicit_invocation: true", openai_yaml)
        self.assertIn("invocation_label: Sample", openai_yaml)

    def test_codex_target_rejects_authored_non_mapping_policy(self) -> None:
        source_dir = self._make_skills_dir()
        skill_dir = source_dir / "sample-skill"
        (skill_dir / "agents").mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    "name: sample-skill",
                    "disable-model-invocation: true",
                    "---",
                    "",
                    "# Sample Skill",
                    "",
                ]
            )
        )
        (skill_dir / "agents" / "openai.yaml").write_text("policy: manual\n")
        skills_dir = self._make_skills_dir()

        with self.assertRaises(installer.SkillSourceError):
            installer.install_skills(
                skills_dir=skills_dir,
                source=source_dir,
                target=installer.SkillTarget.CODEX,
            )

    def test_codex_target_user_modified_skill_skipped(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(
            skills_dir=skills_dir, target=installer.SkillTarget.CODEX
        )
        skill_name = installer._skill_names()[0]
        skill_md = skills_dir / skill_name / "SKILL.md"
        skill_md.write_text(skill_md.read_text() + "\n# codex local change\n")

        report = installer.install_skills(
            skills_dir=skills_dir, target=installer.SkillTarget.CODEX
        )

        modified = next(r for r in report.results if r.name == skill_name)
        self.assertEqual(modified.status, installer.SkillStatus.USER_MODIFIED)
        self.assertIn("codex local change", skill_md.read_text())

    def test_codex_target_force_overwrites_user_modified(self) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(
            skills_dir=skills_dir, target=installer.SkillTarget.CODEX
        )
        skill_name = installer._skill_names()[0]
        skill_md = skills_dir / skill_name / "SKILL.md"
        original = skill_md.read_text()
        skill_md.write_text(original + "\n# codex local change\n")

        report = installer.install_skills(
            skills_dir=skills_dir, force=True, target=installer.SkillTarget.CODEX
        )

        forced = next(r for r in report.results if r.name == skill_name)
        self.assertEqual(forced.status, installer.SkillStatus.FORCED)
        self.assertEqual(skill_md.read_text(), original)

    def test_codex_target_symlinked_skill_root_detected_as_user_modified(
        self,
    ) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(
            skills_dir=skills_dir, target=installer.SkillTarget.CODEX
        )
        skill_name = installer._skill_names()[0]
        skill_dir = skills_dir / skill_name

        secret_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, secret_dir, True)
        (secret_dir / "SKILL.md").write_text("codex-secret-root-contents\n")

        shutil.rmtree(skill_dir)
        skill_dir.symlink_to(secret_dir)

        report = installer.install_skills(
            skills_dir=skills_dir, target=installer.SkillTarget.CODEX
        )
        result = next(r for r in report.results if r.name == skill_name)
        self.assertEqual(result.status, installer.SkillStatus.USER_MODIFIED)

        diff_text = installer.diff_skill(skill_name, skills_dir)
        self.assertIn("installed skill directory is a symlink", diff_text)
        self.assertNotIn("codex-secret-root-contents", diff_text)

    def test_antigravity_target_strips_claude_metadata_and_writes_plugin_manifest(
        self,
    ) -> None:
        source_dir = self._make_skills_dir()
        skill_dir = source_dir / "sample-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    "name: sample-skill",
                    "description: Sample skill.",
                    "disable-model-invocation: true",
                    'argument-hint: "[thing]"',
                    "when_to_use: Invoke when the user asks for sample output.",
                    "---",
                    "",
                    "# Sample Skill",
                    "",
                ]
            )
        )
        plugin_root = Path(tempfile.mkdtemp()) / "lrh"
        self.addCleanup(shutil.rmtree, plugin_root.parent, True)

        report = installer.install_skills(
            skills_dir=plugin_root / "skills",
            source=source_dir,
            target=installer.SkillTarget.ANTIGRAVITY,
        )

        self.assertEqual(report.target, installer.SkillTarget.ANTIGRAVITY)
        installed = plugin_root / "skills" / "sample-skill"
        skill_md = (installed / "SKILL.md").read_text()
        self.assertIn("name: sample-skill", skill_md)
        self.assertIn("when_to_use", skill_md)
        self.assertNotIn("disable-model-invocation", skill_md)
        self.assertNotIn("argument-hint", skill_md)
        manifest = json.loads((plugin_root / "plugin.json").read_text())
        self.assertEqual(manifest["name"], "lrh")
        self.assertEqual(manifest["displayName"], "Logical Robotics Harness")

    def test_antigravity_target_dry_run_writes_nothing(self) -> None:
        source_dir = self._make_skills_dir()
        skill_dir = source_dir / "sample-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("sample skill\n")
        plugin_root = Path(tempfile.mkdtemp()) / "lrh"
        self.addCleanup(shutil.rmtree, plugin_root.parent, True)

        report = installer.install_skills(
            skills_dir=plugin_root / "skills",
            source=source_dir,
            target=installer.SkillTarget.ANTIGRAVITY,
            dry_run=True,
        )

        self.assertEqual(report.results[0].status, installer.SkillStatus.INSTALLED)
        self.assertFalse((plugin_root / "skills" / "sample-skill").exists())
        self.assertFalse((plugin_root / "plugin.json").exists())

    def test_antigravity_target_user_modified_skill_skipped_and_diffed(
        self,
    ) -> None:
        skills_dir = self._make_skills_dir()
        installer.install_skills(
            skills_dir=skills_dir, target=installer.SkillTarget.ANTIGRAVITY
        )
        skill_name = installer._skill_names()[0]
        skill_md = skills_dir / skill_name / "SKILL.md"
        skill_md.write_text(skill_md.read_text() + "\n# antigravity local change\n")

        report = installer.install_skills(
            skills_dir=skills_dir, target=installer.SkillTarget.ANTIGRAVITY
        )
        diff_text = installer.diff_skill(
            skill_name, skills_dir, target=installer.SkillTarget.ANTIGRAVITY
        )

        modified = next(r for r in report.results if r.name == skill_name)
        self.assertEqual(modified.status, installer.SkillStatus.USER_MODIFIED)
        self.assertIn("antigravity local change", skill_md.read_text())
        self.assertIn("+# antigravity local change", diff_text)


class TestResolveInstallTargets(unittest.TestCase):
    def test_claude_user_target(self) -> None:
        target = installer.resolve_install_targets("claude")[0]
        self.assertEqual(target.target, installer.SkillTarget.CLAUDE)
        self.assertEqual(target.skills_dir, Path.home() / ".claude" / "skills")

    def test_codex_user_target(self) -> None:
        target = installer.resolve_install_targets("codex")[0]
        self.assertEqual(target.target, installer.SkillTarget.CODEX)
        self.assertEqual(target.skills_dir, Path.home() / ".agents" / "skills")

    def test_antigravity_user_target(self) -> None:
        target = installer.resolve_install_targets("antigravity")[0]
        self.assertEqual(target.target, installer.SkillTarget.ANTIGRAVITY)
        self.assertEqual(
            target.skills_dir,
            Path.home() / ".gemini" / "config" / "plugins" / "lrh" / "skills",
        )

    def test_claude_project_target(self) -> None:
        project_root = Path("/tmp/project")
        target = installer.resolve_install_targets(
            "claude", local=True, project_root=project_root
        )[0]
        self.assertEqual(target.skills_dir, project_root / ".claude" / "skills")

    def test_codex_project_target(self) -> None:
        project_root = Path("/tmp/project")
        target = installer.resolve_install_targets(
            "codex", local=True, project_root=project_root
        )[0]
        self.assertEqual(target.skills_dir, project_root / ".agents" / "skills")

    def test_antigravity_project_target(self) -> None:
        project_root = Path("/tmp/project")
        target = installer.resolve_install_targets(
            "antigravity", local=True, project_root=project_root
        )[0]
        self.assertEqual(
            target.skills_dir,
            project_root / ".gemini" / "plugins" / "lrh" / "skills",
        )

    def test_all_target_selects_claude_codex_then_antigravity(self) -> None:
        project_root = Path("/tmp/project")
        targets = installer.resolve_install_targets(
            "all", local=True, project_root=project_root
        )
        self.assertEqual(
            [(target.target, target.skills_dir) for target in targets],
            [
                (installer.SkillTarget.CLAUDE, project_root / ".claude" / "skills"),
                (installer.SkillTarget.CODEX, project_root / ".agents" / "skills"),
                (
                    installer.SkillTarget.ANTIGRAVITY,
                    project_root / ".gemini" / "plugins" / "lrh" / "skills",
                ),
            ],
        )

    def test_install_skills_for_all_targets(self) -> None:
        parent = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, parent, True)

        reports = installer.install_skills_for_targets(
            "all", local=True, project_root=parent
        )

        self.assertEqual(
            [report.target for report in reports], list(installer.SkillTarget)
        )
        self.assertTrue((parent / ".claude" / "skills").exists())
        self.assertTrue((parent / ".agents" / "skills").exists())
        self.assertTrue((parent / ".gemini" / "plugins" / "lrh" / "skills").exists())
        self.assertTrue(
            (parent / ".gemini" / "plugins" / "lrh" / "plugin.json").exists()
        )

    def test_dry_run_all_targets_writes_nothing(self) -> None:
        parent = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, parent, True)

        reports = installer.install_skills_for_targets(
            "all", local=True, project_root=parent, dry_run=True
        )

        self.assertEqual(len(reports), 3)
        self.assertFalse((parent / ".claude").exists())
        self.assertFalse((parent / ".agents").exists())
        self.assertFalse((parent / ".gemini").exists())


class TestAgentSkillsConfig(unittest.TestCase):
    def _make_project_root(self) -> Path:
        parent = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, parent, True)
        (parent / "project").mkdir()
        return parent

    def _make_source_dir(self) -> Path:
        parent = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, parent, True)
        source = parent / "skills"
        (source / "sample-skill").mkdir(parents=True)
        (source / "sample-skill" / "SKILL.md").write_text("sample skill\n")
        return source

    def test_absent_repo_config_preserves_existing_defaults(self) -> None:
        project_root = self._make_project_root()

        plan = installer.resolve_agent_skills_install_plan(project_root=project_root)

        self.assertEqual(plan.source, installer.SkillSourceKind.PACKAGE.value)
        self.assertEqual(plan.target, installer.TargetSelection.CLAUDE)
        self.assertFalse(plan.local)

    def test_quoted_list_elements_parse_without_embedded_quotes(self) -> None:
        project_root = self._make_project_root()
        config = project_root / "project" / "agent_skills.yaml"
        config.write_text(
            "\n".join(
                [
                    "schema_version: 1",
                    "sources:",
                    '  - "current-repo"',
                    "targets:",
                    '  - "codex"',
                    "scope: project",
                    "",
                ]
            )
        )

        loaded = installer.load_agent_skills_config(project_root)

        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.source, "current-repo")
        self.assertEqual(loaded.target, installer.TargetSelection.CODEX)
        self.assertTrue(loaded.local)

    def test_configured_source_target_and_scope_influence_install_plan(self) -> None:
        project_root = self._make_project_root()
        source = self._make_source_dir()
        (project_root / "project" / "agent_skills.yaml").write_text(
            "\n".join(
                [
                    "schema_version: 1",
                    "sources:",
                    f"  - {source}",
                    "targets:",
                    "  - codex",
                    "scope: project",
                    "",
                ]
            )
        )

        reports = installer.install_skills_for_targets(project_root=project_root)

        self.assertEqual(
            [report.target for report in reports], [installer.SkillTarget.CODEX]
        )
        skill_md = project_root / ".agents" / "skills" / "sample-skill" / "SKILL.md"
        self.assertEqual(skill_md.read_text(), "sample skill\n")
        self.assertFalse((project_root / ".claude").exists())

    def test_relative_configured_source_resolves_from_project_root(self) -> None:
        project_root = self._make_project_root()
        source = project_root / "skills-source"
        (source / "sample-skill").mkdir(parents=True)
        (source / "sample-skill" / "SKILL.md").write_text("sample skill\n")
        (project_root / "project" / "agent_skills.yaml").write_text(
            "\n".join(
                [
                    "schema_version: 1",
                    "sources:",
                    "  - skills-source",
                    "",
                ]
            )
        )

        plan = installer.resolve_agent_skills_install_plan(project_root=project_root)

        self.assertEqual(plan.source, str(source))

    def test_all_configured_targets_resolve_to_all_targets(self) -> None:
        project_root = self._make_project_root()
        (project_root / "project" / "agent_skills.yaml").write_text(
            "\n".join(
                [
                    "schema_version: 1",
                    "targets:",
                    "  - claude",
                    "  - codex",
                    "  - antigravity",
                    "",
                ]
            )
        )

        plan = installer.resolve_agent_skills_install_plan(project_root=project_root)

        self.assertEqual(plan.target, installer.TargetSelection.ALL)

    def test_claude_codex_configured_targets_remain_two_targets(self) -> None:
        project_root = self._make_project_root()
        (project_root / "project" / "agent_skills.yaml").write_text(
            "\n".join(
                [
                    "schema_version: 1",
                    "targets:",
                    "  - claude",
                    "  - codex",
                    "",
                ]
            )
        )

        plan = installer.resolve_agent_skills_install_plan(project_root=project_root)
        targets = installer.resolve_install_targets(
            plan.target,
            local=True,
            project_root=project_root,
        )

        self.assertEqual(plan.target, installer.TargetSelection.CLAUDE_CODEX)
        self.assertEqual(
            [target.target for target in targets],
            [installer.SkillTarget.CLAUDE, installer.SkillTarget.CODEX],
        )

    def test_configured_antigravity_target_resolves(self) -> None:
        project_root = self._make_project_root()
        (project_root / "project" / "agent_skills.yaml").write_text(
            "\n".join(
                [
                    "schema_version: 1",
                    "targets:",
                    "  - antigravity",
                    "",
                ]
            )
        )

        plan = installer.resolve_agent_skills_install_plan(project_root=project_root)

        self.assertEqual(plan.target, installer.TargetSelection.ANTIGRAVITY)

    def test_cli_values_override_repo_config_values(self) -> None:
        project_root = self._make_project_root()
        (project_root / "project" / "agent_skills.yaml").write_text(
            "\n".join(
                [
                    "schema_version: 1",
                    "sources:",
                    "  - /not/a/real/source",
                    "targets:",
                    "  - codex",
                    "scope: project",
                    "",
                ]
            )
        )

        plan = installer.resolve_agent_skills_install_plan(
            source="lrh-package",
            target="claude",
            local=False,
            project_root=project_root,
        )

        self.assertEqual(plan.source, "lrh-package")
        self.assertEqual(plan.target, installer.TargetSelection.CLAUDE)
        self.assertFalse(plan.local)

    def test_repo_config_cannot_enable_force_overwrite(self) -> None:
        project_root = self._make_project_root()
        (project_root / "project" / "agent_skills.yaml").write_text(
            "\n".join(
                [
                    "schema_version: 1",
                    "install:",
                    "  overwrite: force",
                    "",
                ]
            )
        )

        with self.assertRaises(installer.SkillSourceError):
            installer.resolve_agent_skills_install_plan(project_root=project_root)

    def test_repo_config_rejects_blank_source_values(self) -> None:
        project_root = self._make_project_root()
        (project_root / "project" / "agent_skills.yaml").write_text(
            "\n".join(
                [
                    "schema_version: 1",
                    "sources:",
                    '  - ""',
                    "",
                ]
            )
        )

        with self.assertRaises(installer.SkillSourceError):
            installer.resolve_agent_skills_install_plan(project_root=project_root)

    def test_repo_config_rejects_blank_target_values(self) -> None:
        project_root = self._make_project_root()
        (project_root / "project" / "agent_skills.yaml").write_text(
            "\n".join(
                [
                    "schema_version: 1",
                    "targets:",
                    '  - ""',
                    "",
                ]
            )
        )

        with self.assertRaises(installer.SkillSourceError):
            installer.resolve_agent_skills_install_plan(project_root=project_root)


class TestResolveSkillSource(unittest.TestCase):
    def _make_source_dir(self) -> Path:
        parent = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, parent, True)
        source = parent / "skills"
        (source / "sample-skill").mkdir(parents=True)
        (source / "sample-skill" / "SKILL.md").write_text("sample skill\n")
        (source / "_shared").mkdir()
        (source / "_shared" / "ignored.md").write_text("ignored\n")
        return source

    def test_package_source_lists_packaged_skills(self) -> None:
        source = installer.resolve_skill_source("lrh-package")

        self.assertEqual(source.kind, installer.SkillSourceKind.PACKAGE)
        self.assertIn("lrh-implement", source.skill_names())

    def test_current_repo_source_uses_project_root(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        source = installer.resolve_skill_source("current-repo", project_root=repo_root)

        self.assertEqual(source.kind, installer.SkillSourceKind.CURRENT_REPO)
        self.assertIn("lrh-implement", source.skill_names())

    def test_explicit_path_source_lists_non_private_skill_dirs(self) -> None:
        source_dir = self._make_source_dir()
        source = installer.resolve_skill_source(source_dir)

        self.assertEqual(source.kind, installer.SkillSourceKind.PATH)
        self.assertEqual(source.skill_names(), ["sample-skill"])

    def test_explicit_path_source_rejects_top_level_symlink(self) -> None:
        source_dir = self._make_source_dir()
        real_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, real_dir, True)
        (real_dir / "SKILL.md").write_text("linked skill\n")
        link_path = source_dir / "linked-skill"
        try:
            link_path.symlink_to(real_dir, target_is_directory=True)
        except OSError as err:
            self.skipTest(f"symlink creation unsupported: {err}")
        source = installer.resolve_skill_source(source_dir)

        with self.assertRaises(installer.SkillSourceError):
            source.skill_names()

    def test_missing_source_raises_source_error(self) -> None:
        with self.assertRaises(installer.SkillSourceError):
            installer.resolve_skill_source(Path("/not/a/real/skills/source"))

    def test_install_skills_from_explicit_path_source(self) -> None:
        source_dir = self._make_source_dir()
        skills_dir = Path(tempfile.mkdtemp()) / "target"
        self.addCleanup(shutil.rmtree, skills_dir.parent, True)

        report = installer.install_skills(skills_dir=skills_dir, source=source_dir)

        self.assertEqual([result.name for result in report.results], ["sample-skill"])
        self.assertEqual(report.results[0].status, installer.SkillStatus.INSTALLED)
        self.assertEqual(
            (skills_dir / "sample-skill" / "SKILL.md").read_text(), "sample skill\n"
        )
        self.assertFalse((skills_dir / "_shared").exists())

    def test_explicit_path_source_preserves_user_modified_safety(self) -> None:
        source_dir = self._make_source_dir()
        skills_dir = Path(tempfile.mkdtemp()) / "target"
        self.addCleanup(shutil.rmtree, skills_dir.parent, True)
        installer.install_skills(skills_dir=skills_dir, source=source_dir)
        skill_md = skills_dir / "sample-skill" / "SKILL.md"
        skill_md.write_text("locally changed\n")

        report = installer.install_skills(skills_dir=skills_dir, source=source_dir)

        self.assertEqual(report.results[0].status, installer.SkillStatus.USER_MODIFIED)
        self.assertEqual(skill_md.read_text(), "locally changed\n")

    def test_explicit_path_source_rejects_nested_symlink_when_comparing_existing_skill(
        self,
    ) -> None:
        source_dir = self._make_source_dir()
        skills_dir = Path(tempfile.mkdtemp()) / "target"
        self.addCleanup(shutil.rmtree, skills_dir.parent, True)
        installer.install_skills(skills_dir=skills_dir, source=source_dir)
        secret_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, secret_dir, True)
        secret_file = secret_dir / "secret.txt"
        secret_file.write_text("do not compare me\n")
        link_path = source_dir / "sample-skill" / "secret-link.md"
        try:
            link_path.symlink_to(secret_file)
        except OSError as err:
            self.skipTest(f"symlink creation unsupported: {err}")

        with self.assertRaises(installer.SkillSourceError):
            installer.install_skills(skills_dir=skills_dir, source=source_dir)

    def test_explicit_path_source_rejects_nested_symlink(self) -> None:
        source_dir = self._make_source_dir()
        secret_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, secret_dir, True)
        secret_file = secret_dir / "secret.txt"
        secret_file.write_text("do not copy me\n")
        link_path = source_dir / "sample-skill" / "secret-link.md"
        try:
            link_path.symlink_to(secret_file)
        except OSError as err:
            self.skipTest(f"symlink creation unsupported: {err}")
        skills_dir = Path(tempfile.mkdtemp()) / "target"
        self.addCleanup(shutil.rmtree, skills_dir.parent, True)

        with self.assertRaises(installer.SkillSourceError):
            installer.install_skills(skills_dir=skills_dir, source=source_dir)

        self.assertFalse((skills_dir / "sample-skill" / "secret-link.md").exists())
        self.assertFalse((skills_dir / "sample-skill").exists())

    def test_diff_skill_uses_explicit_path_source(self) -> None:
        source_dir = self._make_source_dir()
        skills_dir = Path(tempfile.mkdtemp()) / "target"
        self.addCleanup(shutil.rmtree, skills_dir.parent, True)
        installer.install_skills(skills_dir=skills_dir, source=source_dir)
        skill_md = skills_dir / "sample-skill" / "SKILL.md"
        skill_md.write_text("locally changed\n")

        diff_text = installer.diff_skill("sample-skill", skills_dir, source=source_dir)

        self.assertIn("--- source/SKILL.md", diff_text)
        self.assertIn("+++ installed/SKILL.md", diff_text)
        self.assertIn("+locally changed", diff_text)

    def test_diff_skill_rejects_nested_source_symlink(self) -> None:
        source_dir = self._make_source_dir()
        skills_dir = Path(tempfile.mkdtemp()) / "target"
        self.addCleanup(shutil.rmtree, skills_dir.parent, True)
        installer.install_skills(skills_dir=skills_dir, source=source_dir)
        secret_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, secret_dir, True)
        secret_file = secret_dir / "secret.txt"
        secret_file.write_text("do not diff me\n")
        link_path = source_dir / "sample-skill" / "secret-link.md"
        try:
            link_path.symlink_to(secret_file)
        except OSError as err:
            self.skipTest(f"symlink creation unsupported: {err}")

        with self.assertRaises(installer.SkillSourceError):
            installer.diff_skill("sample-skill", skills_dir, source=source_dir)


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


class TestInspectSkills(unittest.TestCase):
    def _make_skills_dir(self) -> Path:
        parent = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, parent, True)
        return parent / "skills"

    def _make_source(self, skill_md: str = "sample skill\n") -> Path:
        source_dir = self._make_skills_dir()
        skill_dir = source_dir / "sample-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(skill_md)
        return source_dir

    def test_inspect_reports_missing_without_writing(self) -> None:
        source_dir = self._make_source()
        skills_dir = self._make_skills_dir()

        report = installer.inspect_skills(skills_dir=skills_dir, source=source_dir)

        self.assertFalse(skills_dir.exists())
        self.assertEqual(
            report.results[0].status, installer.SkillInspectionStatus.MISSING
        )
        self.assertTrue(installer.inspection_report_has_failures(report))

    def test_inspect_reports_up_to_date_after_install(self) -> None:
        source_dir = self._make_source()
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir, source=source_dir)

        report = installer.inspect_skills(skills_dir=skills_dir, source=source_dir)

        self.assertEqual(
            report.results[0].status, installer.SkillInspectionStatus.UP_TO_DATE
        )
        self.assertFalse(installer.inspection_report_has_failures(report))

    def test_inspect_reports_modified_target_copy(self) -> None:
        source_dir = self._make_source()
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir, source=source_dir)
        (skills_dir / "sample-skill" / "SKILL.md").write_text("changed\n")

        report = installer.inspect_skills(skills_dir=skills_dir, source=source_dir)

        self.assertEqual(
            report.results[0].status, installer.SkillInspectionStatus.MODIFIED
        )
        self.assertTrue(installer.inspection_report_has_failures(report))

    def test_inspect_reports_symlinked_target_copy_modified(self) -> None:
        source_dir = self._make_source()
        skills_dir = self._make_skills_dir()
        installer.install_skills(skills_dir=skills_dir, source=source_dir)
        shutil.rmtree(skills_dir / "sample-skill")
        outside_dir = self._make_skills_dir()
        outside_dir.mkdir(parents=True)
        (outside_dir / "SKILL.md").write_text("sample skill\n")
        (skills_dir / "sample-skill").symlink_to(outside_dir, target_is_directory=True)

        report = installer.inspect_skills(skills_dir=skills_dir, source=source_dir)

        self.assertEqual(
            report.results[0].status, installer.SkillInspectionStatus.MODIFIED
        )
        self.assertTrue(installer.inspection_report_has_failures(report))

    def test_inspect_reports_symlinked_source_entry_error(self) -> None:
        source_dir = self._make_skills_dir()
        source_dir.mkdir(parents=True)
        real_skill = source_dir / "real-skill"
        real_skill.mkdir()
        (real_skill / "SKILL.md").write_text("sample skill\n")
        (source_dir / "sample-skill").symlink_to(real_skill, target_is_directory=True)
        skills_dir = self._make_skills_dir()

        with self.assertRaisesRegex(
            installer.SkillSourceError, "skill source contains symlinked entry"
        ):
            installer.inspect_skills(skills_dir=skills_dir, source=source_dir)

    def test_inspect_reports_codex_unsupported_metadata(self) -> None:
        source_dir = self._make_source(
            "\n".join(
                [
                    "---",
                    "name: sample-skill",
                    'argument-hint: "[thing]"',
                    "---",
                    "",
                    "# Sample",
                    "",
                ]
            )
        )
        skills_dir = self._make_skills_dir()
        installer.install_skills(
            skills_dir=skills_dir, source=source_dir, target=installer.SkillTarget.CODEX
        )

        report = installer.inspect_skills(
            skills_dir=skills_dir, source=source_dir, target=installer.SkillTarget.CODEX
        )

        self.assertEqual(
            report.results[0].status, installer.SkillInspectionStatus.UP_TO_DATE
        )
        self.assertEqual(report.results[0].issues[0].code, "unsupported_metadata")
        self.assertTrue(installer.inspection_report_has_failures(report))

    def test_inspect_reports_invalid_codex_metadata(self) -> None:
        source_dir = self._make_source()
        skill_dir = source_dir / "sample-skill"
        (skill_dir / "agents").mkdir()
        (skill_dir / "agents" / "openai.yaml").write_text("- not-a-mapping\n")
        skills_dir = self._make_skills_dir()

        report = installer.inspect_skills(
            skills_dir=skills_dir, source=source_dir, target=installer.SkillTarget.CODEX
        )

        self.assertEqual(report.results[0].issues[0].code, "invalid_codex_metadata")
        self.assertTrue(installer.inspection_report_has_failures(report))

    def test_inspect_reports_non_mapping_skill_frontmatter_source_error(self) -> None:
        source_dir = self._make_source(
            "\n".join(
                [
                    "---",
                    "- not-a-mapping",
                    "---",
                    "",
                    "# Sample",
                    "",
                ]
            )
        )
        skills_dir = self._make_skills_dir()

        report = installer.inspect_skills(
            skills_dir=skills_dir, source=source_dir, target=installer.SkillTarget.CODEX
        )

        self.assertEqual(
            report.results[0].status, installer.SkillInspectionStatus.SOURCE_ERROR
        )
        self.assertEqual(report.results[0].issues[0].code, "source_error")
        self.assertIn(
            "frontmatter must be a mapping", report.results[0].issues[0].message
        )
        self.assertTrue(installer.inspection_report_has_failures(report))

    def test_inspect_skills_for_targets_honors_all_selection(self) -> None:
        source_dir = self._make_source()
        project_root = self._make_skills_dir()

        reports = installer.inspect_skills_for_targets(
            target=installer.TargetSelection.ALL,
            local=True,
            project_root=project_root,
            source=source_dir,
        )

        self.assertEqual(
            [report.target for report in reports],
            [
                installer.SkillTarget.CLAUDE,
                installer.SkillTarget.CODEX,
                installer.SkillTarget.ANTIGRAVITY,
            ],
        )
        self.assertEqual(
            [report.skills_dir for report in reports],
            [
                project_root / ".claude" / "skills",
                project_root / ".agents" / "skills",
                project_root / ".gemini" / "plugins" / "lrh" / "skills",
            ],
        )

    def test_format_inspection_report(self) -> None:
        source_dir = self._make_source()
        skills_dir = self._make_skills_dir()
        report = installer.inspect_skills(skills_dir=skills_dir, source=source_dir)

        output = installer.format_inspection_report(report)

        self.assertIn("missing: sample-skill", output)

    def test_format_inspection_report_deduplicates_source_error(self) -> None:
        source_dir = self._make_source(
            "\n".join(
                [
                    "---",
                    "- not-a-mapping",
                    "---",
                    "",
                    "# Sample",
                    "",
                ]
            )
        )
        skills_dir = self._make_skills_dir()
        report = installer.inspect_skills(
            skills_dir=skills_dir, source=source_dir, target=installer.SkillTarget.CODEX
        )

        output = installer.format_inspection_report(report)

        self.assertIn("source error: sample-skill: SKILL.md frontmatter", output)
        self.assertNotIn("\n  error: sample-skill:", f"\n{output}")

    def test_format_inspection_report_accepts_custom_issue_label(self) -> None:
        source_dir = self._make_source(
            "\n".join(
                [
                    "---",
                    "name: sample-skill",
                    'argument-hint: "[thing]"',
                    "---",
                    "",
                    "# Sample",
                    "",
                ]
            )
        )
        skills_dir = self._make_skills_dir()
        installer.install_skills(
            skills_dir=skills_dir, source=source_dir, target=installer.SkillTarget.CODEX
        )
        report = installer.inspect_skills(
            skills_dir=skills_dir, source=source_dir, target=installer.SkillTarget.CODEX
        )

        output = installer.format_inspection_report(report, issue_label="notice")

        self.assertIn("notice: sample-skill:", output)
        self.assertNotIn("error: sample-skill:", output)


if __name__ == "__main__":
    unittest.main()
