"""CLI-level tests for `lrh skills install`."""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


class SkillsInstallCliTest(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _cli_env(self) -> dict[str, str]:
        env = os.environ.copy()
        src_path = str(self._repo_root() / "src")
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            src_path if not existing else os.pathsep.join([src_path, existing])
        )
        return env

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", *args],
            check=False,
            capture_output=True,
            text=True,
            env=self._cli_env(),
            cwd=self._repo_root(),
        )

    def _run_isolated(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run lrh with a temporary HOME so the skills dir starts empty."""
        with tempfile.TemporaryDirectory() as fake_home:
            env = self._cli_env()
            env["HOME"] = fake_home
            env["USERPROFILE"] = fake_home
            return subprocess.run(
                [sys.executable, "-m", "lrh.cli.main", *args],
                check=False,
                capture_output=True,
                text=True,
                env=env,
                cwd=self._repo_root(),
            )

    def _run_local(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run lrh with a temporary CWD so --local installs to a clean dir."""
        with tempfile.TemporaryDirectory() as fake_cwd:
            return subprocess.run(
                [sys.executable, "-m", "lrh.cli.main", *args],
                check=False,
                capture_output=True,
                text=True,
                env=self._cli_env(),
                cwd=fake_cwd,
            )

    def test_skills_install_help_exits_zero(self) -> None:
        result = self._run("skills", "install", "--help")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--dry-run", result.stdout)
        self.assertIn("--force", result.stdout)
        self.assertIn("--local", result.stdout)
        self.assertIn("--scope", result.stdout)
        self.assertIn("--target", result.stdout)
        self.assertIn("--source", result.stdout)
        self.assertNotIn("Install LRH skills to ~/.claude/skills/", result.stdout)

    def test_skills_status_help_exits_zero(self) -> None:
        result = self._run("skills", "status", "--help")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--local", result.stdout)
        self.assertIn("--target", result.stdout)
        self.assertIn("--source", result.stdout)

    def test_skills_check_help_exits_zero(self) -> None:
        result = self._run("skills", "check", "--help")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--local", result.stdout)
        self.assertIn("--target", result.stdout)
        self.assertIn("--source", result.stdout)

    def test_skills_help_is_target_neutral(self) -> None:
        result = self._run("skills", "--help")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("agent skills directories", result.stdout)
        self.assertNotIn("Claude Code skills", result.stdout)

    def test_skills_install_dry_run_exits_zero(self) -> None:
        result = self._run_isolated("skills", "install", "--dry-run")
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_skills_install_dry_run_reports_would_install(self) -> None:
        result = self._run_isolated("skills", "install", "--dry-run")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("would install", result.stdout)

    def test_skills_install_dry_run_suppresses_restart_note(self) -> None:
        result = self._run_isolated("skills", "install", "--dry-run")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn("Restart Claude Code", result.stdout)

    def test_skills_install_local_dry_run_exits_zero(self) -> None:
        result = self._run_local("skills", "install", "--local", "--dry-run")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("would install", result.stdout)

    def test_skills_install_codex_dry_run_exits_zero(self) -> None:
        result = self._run_isolated(
            "skills", "install", "--target", "codex", "--dry-run"
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("would install", result.stdout)

    def test_skills_install_current_repo_source_dry_run_exits_zero(self) -> None:
        result = self._run_isolated(
            "skills", "install", "--source", "current-repo", "--dry-run"
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("would install", result.stdout)

    def test_skills_install_explicit_path_source_writes_selected_skill(self) -> None:
        with tempfile.TemporaryDirectory() as source_dir:
            source = pathlib.Path(source_dir)
            (source / "sample-skill").mkdir()
            (source / "sample-skill" / "SKILL.md").write_text("sample skill\n")
            with tempfile.TemporaryDirectory() as fake_cwd:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "lrh.cli.main",
                        "skills",
                        "install",
                        "--local",
                        "--source",
                        str(source),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    env=self._cli_env(),
                    cwd=fake_cwd,
                )

                self.assertEqual(result.returncode, 0, msg=result.stderr)
                skill_md = (
                    pathlib.Path(fake_cwd)
                    / ".claude"
                    / "skills"
                    / "sample-skill"
                    / "SKILL.md"
                )
                self.assertEqual(skill_md.read_text(), "sample skill\n")

    def test_skills_status_reports_missing_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as source_dir:
            source = pathlib.Path(source_dir)
            (source / "sample-skill").mkdir()
            (source / "sample-skill" / "SKILL.md").write_text("sample skill\n")
            with tempfile.TemporaryDirectory() as fake_cwd:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "lrh.cli.main",
                        "skills",
                        "status",
                        "--local",
                        "--source",
                        str(source),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    env=self._cli_env(),
                    cwd=fake_cwd,
                )

                self.assertEqual(result.returncode, 0, msg=result.stderr)
                self.assertIn("missing: sample-skill", result.stdout)
                self.assertFalse((pathlib.Path(fake_cwd) / ".claude").exists())

    def test_skills_check_exits_nonzero_for_missing_target(self) -> None:
        with tempfile.TemporaryDirectory() as source_dir:
            source = pathlib.Path(source_dir)
            (source / "sample-skill").mkdir()
            (source / "sample-skill" / "SKILL.md").write_text("sample skill\n")
            with tempfile.TemporaryDirectory() as fake_cwd:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "lrh.cli.main",
                        "skills",
                        "check",
                        "--local",
                        "--source",
                        str(source),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    env=self._cli_env(),
                    cwd=fake_cwd,
                )

                self.assertEqual(result.returncode, 1, msg=result.stderr)
                self.assertIn("missing: sample-skill", result.stdout)

    def test_skills_check_exits_zero_for_up_to_date_target(self) -> None:
        with tempfile.TemporaryDirectory() as source_dir:
            source = pathlib.Path(source_dir)
            (source / "sample-skill").mkdir()
            (source / "sample-skill" / "SKILL.md").write_text("sample skill\n")
            with tempfile.TemporaryDirectory() as fake_cwd:
                env = self._cli_env()
                install_result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "lrh.cli.main",
                        "skills",
                        "install",
                        "--local",
                        "--source",
                        str(source),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    env=env,
                    cwd=fake_cwd,
                )
                self.assertEqual(
                    install_result.returncode, 0, msg=install_result.stderr
                )

                check_result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "lrh.cli.main",
                        "skills",
                        "check",
                        "--local",
                        "--source",
                        str(source),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    env=env,
                    cwd=fake_cwd,
                )

                self.assertEqual(check_result.returncode, 0, msg=check_result.stderr)
                self.assertIn("up to date: sample-skill", check_result.stdout)

    def test_skills_install_invalid_source_rejected(self) -> None:
        result = self._run(
            "skills",
            "install",
            "--source",
            "/not/a/real/skills/source",
            "--dry-run",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("skill source does not exist", result.stderr)

    def test_skills_status_invalid_source_rejected(self) -> None:
        result = self._run(
            "skills",
            "status",
            "--source",
            "/not/a/real/skills/source",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("skill source does not exist", result.stderr)

    def test_skills_install_diff_invalid_source_rejected_without_traceback(
        self,
    ) -> None:
        result = self._run(
            "skills",
            "install",
            "--source",
            "/not/a/real/skills/source",
            "--diff",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("skill source does not exist", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_skills_install_all_local_dry_run_reports_all_targets(self) -> None:
        result = self._run_local(
            "skills", "install", "--local", "--target", "all", "--dry-run"
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("claude:", result.stdout)
        self.assertIn(".claude/skills", result.stdout)
        self.assertIn("codex:", result.stdout)
        self.assertIn(".agents/skills", result.stdout)
        self.assertIn("antigravity:", result.stdout)
        self.assertIn(".gemini/plugins/lrh/skills", result.stdout)

    def test_skills_install_local_codex_writes_agents_skills(self) -> None:
        with tempfile.TemporaryDirectory() as fake_cwd:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "skills",
                    "install",
                    "--local",
                    "--target",
                    "codex",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=self._cli_env(),
                cwd=fake_cwd,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((pathlib.Path(fake_cwd) / ".agents" / "skills").exists())
            self.assertFalse((pathlib.Path(fake_cwd) / ".claude" / "skills").exists())

    def test_skills_install_local_antigravity_writes_plugin_tree(self) -> None:
        with tempfile.TemporaryDirectory() as fake_cwd:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "skills",
                    "install",
                    "--local",
                    "--target",
                    "antigravity",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=self._cli_env(),
                cwd=fake_cwd,
            )
            plugin_root = pathlib.Path(fake_cwd) / ".gemini" / "plugins" / "lrh"

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((plugin_root / "skills").exists())
            self.assertTrue((plugin_root / "plugin.json").exists())
            self.assertFalse((pathlib.Path(fake_cwd) / ".claude").exists())
            self.assertFalse((pathlib.Path(fake_cwd) / ".agents").exists())

    def test_skills_install_uses_repo_config_when_flags_are_absent(self) -> None:
        with tempfile.TemporaryDirectory() as source_dir:
            source = pathlib.Path(source_dir)
            (source / "sample-skill").mkdir()
            (source / "sample-skill" / "SKILL.md").write_text("sample skill\n")
            with tempfile.TemporaryDirectory() as fake_cwd:
                project_dir = pathlib.Path(fake_cwd) / "project"
                project_dir.mkdir()
                (project_dir / "agent_skills.yaml").write_text(
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

                result = subprocess.run(
                    [sys.executable, "-m", "lrh.cli.main", "skills", "install"],
                    check=False,
                    capture_output=True,
                    text=True,
                    env=self._cli_env(),
                    cwd=fake_cwd,
                )

                self.assertEqual(result.returncode, 0, msg=result.stderr)
                skill_md = (
                    pathlib.Path(fake_cwd)
                    / ".agents"
                    / "skills"
                    / "sample-skill"
                    / "SKILL.md"
                )
                self.assertEqual(skill_md.read_text(), "sample skill\n")
                self.assertFalse((pathlib.Path(fake_cwd) / ".claude").exists())

    def test_skills_install_cli_flags_override_repo_config(self) -> None:
        with tempfile.TemporaryDirectory() as source_dir:
            source = pathlib.Path(source_dir)
            (source / "sample-skill").mkdir()
            (source / "sample-skill" / "SKILL.md").write_text("sample skill\n")
            with tempfile.TemporaryDirectory() as fake_cwd:
                project_dir = pathlib.Path(fake_cwd) / "project"
                project_dir.mkdir()
                (project_dir / "agent_skills.yaml").write_text(
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

                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "lrh.cli.main",
                        "skills",
                        "install",
                        "--source",
                        str(source),
                        "--target",
                        "claude",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    env=self._cli_env(),
                    cwd=fake_cwd,
                )

                self.assertEqual(result.returncode, 0, msg=result.stderr)
                skill_md = (
                    pathlib.Path(fake_cwd)
                    / ".claude"
                    / "skills"
                    / "sample-skill"
                    / "SKILL.md"
                )
                self.assertEqual(skill_md.read_text(), "sample skill\n")
                self.assertFalse((pathlib.Path(fake_cwd) / ".agents").exists())

    def test_skills_install_scope_user_overrides_project_repo_config(self) -> None:
        with tempfile.TemporaryDirectory() as source_dir:
            source = pathlib.Path(source_dir)
            (source / "sample-skill").mkdir()
            (source / "sample-skill" / "SKILL.md").write_text("sample skill\n")
            with tempfile.TemporaryDirectory() as fake_cwd:
                with tempfile.TemporaryDirectory() as fake_home:
                    project_dir = pathlib.Path(fake_cwd) / "project"
                    project_dir.mkdir()
                    (project_dir / "agent_skills.yaml").write_text(
                        "\n".join(
                            [
                                "schema_version: 1",
                                "sources:",
                                f"  - {source}",
                                "targets:",
                                "  - claude",
                                "scope: project",
                                "",
                            ]
                        )
                    )
                    env = self._cli_env()
                    env["HOME"] = fake_home
                    env["USERPROFILE"] = fake_home

                    result = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "lrh.cli.main",
                            "skills",
                            "install",
                            "--scope",
                            "user",
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                        env=env,
                        cwd=fake_cwd,
                    )

                    self.assertEqual(result.returncode, 0, msg=result.stderr)
                    skill_md = (
                        pathlib.Path(fake_home)
                        / ".claude"
                        / "skills"
                        / "sample-skill"
                        / "SKILL.md"
                    )
                    self.assertEqual(skill_md.read_text(), "sample skill\n")
                    self.assertFalse((pathlib.Path(fake_cwd) / ".claude").exists())

    def test_skills_install_local_conflicts_with_scope_user(self) -> None:
        result = self._run("skills", "install", "--local", "--scope", "user")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--local cannot be combined with --scope user", result.stderr)

    def test_skills_install_local_codex_diff_reports_local_modification(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as fake_cwd:
            env = self._cli_env()
            install_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "skills",
                    "install",
                    "--local",
                    "--target",
                    "codex",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=env,
                cwd=fake_cwd,
            )
            self.assertEqual(install_result.returncode, 0, msg=install_result.stderr)
            skill_md = next(
                (pathlib.Path(fake_cwd) / ".agents" / "skills").glob("*/SKILL.md")
            )
            skill_md.write_text(skill_md.read_text() + "\n# codex local change\n")

            diff_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "skills",
                    "install",
                    "--local",
                    "--target",
                    "codex",
                    "--diff",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=env,
                cwd=fake_cwd,
            )

            self.assertEqual(diff_result.returncode, 0, msg=diff_result.stderr)
            self.assertIn("warning:", diff_result.stdout)
            self.assertIn("--- diff:", diff_result.stdout)
            self.assertIn("+# codex local change", diff_result.stdout)
            self.assertIn("codex local change", skill_md.read_text())

    def _run_install_in(self, cwd: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", "skills", "install", *args],
            check=False,
            capture_output=True,
            text=True,
            env=self._cli_env(),
            cwd=cwd,
        )

    def _snapshot_tree(self, root: pathlib.Path) -> dict[str, bytes | None]:
        """Map every path under root to its bytes (None for directories)."""
        return {
            str(path.relative_to(root)): (None if path.is_dir() else path.read_bytes())
            for path in sorted(root.rglob("*"))
        }

    def test_skills_install_diff_never_creates_missing_target(self) -> None:
        with tempfile.TemporaryDirectory() as fake_cwd:
            result = self._run_install_in(
                fake_cwd, "--local", "--target", "antigravity", "--diff"
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("would install:", result.stdout)
            self.assertNotIn("  installed:", result.stdout)
            self.assertNotIn("was newly created", result.stdout)
            self.assertEqual(list(pathlib.Path(fake_cwd).iterdir()), [])

    def test_skills_install_diff_leaves_target_missing_a_skill_unchanged(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as fake_cwd:
            root = pathlib.Path(fake_cwd)
            install_result = self._run_install_in(
                fake_cwd, "--local", "--target", "antigravity"
            )
            self.assertEqual(install_result.returncode, 0, msg=install_result.stderr)
            skills_dir = root / ".gemini" / "plugins" / "lrh" / "skills"
            missing_skill = next(
                path for path in sorted(skills_dir.iterdir()) if path.is_dir()
            )
            shutil.rmtree(missing_skill)
            before = self._snapshot_tree(root)

            diff_result = self._run_install_in(
                fake_cwd, "--local", "--target", "antigravity", "--diff"
            )

            self.assertEqual(diff_result.returncode, 0, msg=diff_result.stderr)
            self.assertIn(f"would install: {missing_skill.name}", diff_result.stdout)
            self.assertNotIn("  installed:", diff_result.stdout)
            self.assertFalse(missing_skill.exists())
            self.assertEqual(self._snapshot_tree(root), before)

    def test_skills_install_diff_with_force_previews_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as fake_cwd:
            root = pathlib.Path(fake_cwd)
            install_result = self._run_install_in(
                fake_cwd, "--local", "--target", "codex"
            )
            self.assertEqual(install_result.returncode, 0, msg=install_result.stderr)
            skill_md = next((root / ".agents" / "skills").glob("*/SKILL.md"))
            skill_md.write_text(skill_md.read_text() + "\n# codex local change\n")
            before = self._snapshot_tree(root)

            diff_result = self._run_install_in(
                fake_cwd, "--local", "--target", "codex", "--diff", "--force"
            )

            self.assertEqual(diff_result.returncode, 0, msg=diff_result.stderr)
            self.assertIn(
                f"would overwrite: {skill_md.parent.name}", diff_result.stdout
            )
            self.assertIn("--- diff:", diff_result.stdout)
            self.assertIn("+# codex local change", diff_result.stdout)
            self.assertEqual(self._snapshot_tree(root), before)

    def test_skills_install_invalid_target_rejected(self) -> None:
        result = self._run("skills", "install", "--target", "chatgpt", "--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)

    def test_setup_command_unrecognized(self) -> None:
        result = self._run("setup")
        self.assertNotEqual(result.returncode, 0)


class SkillsExportCliTest(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _run_in(
        self, cwd: pathlib.Path, *args: str
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        src_path = str(self._repo_root() / "src")
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            src_path if not existing else os.pathsep.join([src_path, existing])
        )
        return subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", *args],
            check=False,
            capture_output=True,
            text=True,
            env=env,
            cwd=cwd,
        )

    def _temp_dir(self) -> pathlib.Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return pathlib.Path(directory.name)

    def test_skills_export_help_exits_zero(self) -> None:
        result = self._run_in(self._temp_dir(), "skills", "export", "--help")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--skill", result.stdout)
        self.assertNotIn("--local", result.stdout)
        self.assertNotIn("--scope", result.stdout)

    def test_skills_export_writes_selected_bundles(self) -> None:
        work = self._temp_dir()
        result = self._run_in(
            work,
            "skills",
            "export",
            "--target",
            "chatgpt",
            "--out",
            "bundles",
            "--skill",
            "lrh-design",
            "--skill",
            "lrh-work-item",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("exported: lrh-design", result.stdout)
        self.assertIn("exported: lrh-work-item", result.stdout)
        self.assertEqual(
            sorted(path.name for path in (work / "bundles").iterdir()),
            ["lrh-design.zip", "lrh-work-item.zip"],
        )

    def test_skills_export_default_skips_manual_only_skills(self) -> None:
        work = self._temp_dir()
        result = self._run_in(
            work, "skills", "export", "--target", "chatgpt", "--out", "bundles"
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("skipped (manual-only): lrh-land", result.stdout)
        self.assertFalse((work / "bundles" / "lrh-land.zip").exists())
        self.assertTrue((work / "bundles" / "lrh-design.zip").exists())

    def test_skills_export_explicit_manual_only_reports_notice(self) -> None:
        work = self._temp_dir()
        result = self._run_in(
            work,
            "skills",
            "export",
            "--target",
            "chatgpt",
            "--out",
            "bundles",
            "--skill",
            "lrh-land",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("notice: lrh-land: manual-only skill", result.stdout)
        self.assertTrue((work / "bundles" / "lrh-land.zip").exists())

    def test_skills_export_unknown_skill_rejected(self) -> None:
        work = self._temp_dir()
        result = self._run_in(
            work,
            "skills",
            "export",
            "--target",
            "chatgpt",
            "--out",
            "bundles",
            "--skill",
            "no-such-skill",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown skill(s)", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((work / "bundles").exists())

    def test_skills_export_requires_target_and_out(self) -> None:
        work = self._temp_dir()
        missing_target = self._run_in(work, "skills", "export", "--out", "bundles")
        self.assertEqual(missing_target.returncode, 2)
        self.assertIn("--target", missing_target.stderr)
        missing_out = self._run_in(work, "skills", "export", "--target", "chatgpt")
        self.assertEqual(missing_out.returncode, 2)
        self.assertIn("--out", missing_out.stderr)

    def test_skills_export_rejects_install_only_flags(self) -> None:
        result = self._run_in(
            self._temp_dir(),
            "skills",
            "export",
            "--target",
            "chatgpt",
            "--out",
            "bundles",
            "--local",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_skills_export_rejects_install_targets(self) -> None:
        result = self._run_in(
            self._temp_dir(),
            "skills",
            "export",
            "--target",
            "codex",
            "--out",
            "bundles",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice", result.stderr)

    def test_skills_export_validation_failure_exits_one_without_writing(
        self,
    ) -> None:
        work = self._temp_dir()
        bad_skill = work / "source" / "bad-skill"
        bad_skill.mkdir(parents=True)
        (bad_skill / "SKILL.md").write_text("no frontmatter\n")
        result = self._run_in(
            work,
            "skills",
            "export",
            "--target",
            "chatgpt",
            "--source",
            str(work / "source"),
            "--out",
            "bundles",
        )
        self.assertEqual(result.returncode, 1, msg=result.stderr)
        self.assertIn("error: bad-skill:", result.stdout)
        self.assertIn("no bundles written", result.stdout)
        self.assertFalse((work / "bundles").exists())


if __name__ == "__main__":
    unittest.main()
