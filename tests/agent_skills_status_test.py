import json
import pathlib
import tempfile
import unittest

from lrh import agent_skills_status
from lrh.skills import installer


def _write_config(root: pathlib.Path, text: str) -> None:
    path = root / "project" / "agent_skills.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


class ComputeStatusTest(unittest.TestCase):
    def test_missing_config_reports_conventional_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            status = agent_skills_status.compute_status(project_root=root)
            self.assertFalse(status.profile_exists)
            self.assertEqual(status.sources.value, "lrh-package")
            self.assertFalse(status.sources.from_config)
            self.assertEqual(status.targets.value, "claude")
            self.assertFalse(status.targets.from_config)
            self.assertEqual(status.scope.value, "user")
            self.assertFalse(status.scope.from_config)
            self.assertIsNone(status.install_overwrite)

    def test_full_config_reports_from_config_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_config(
                root,
                "schema_version: 1\n"
                "sources:\n  - current-repo\n"
                "targets:\n  - codex\n"
                "scope: project\n"
                "install:\n  overwrite: skip\n",
            )
            status = agent_skills_status.compute_status(project_root=root)
            self.assertTrue(status.profile_exists)
            self.assertEqual(status.sources.value, "current-repo")
            self.assertTrue(status.sources.from_config)
            self.assertEqual(status.targets.value, "codex")
            self.assertTrue(status.targets.from_config)
            self.assertEqual(status.scope.value, "project")
            self.assertTrue(status.scope.from_config)
            self.assertEqual(status.install_overwrite, "skip")

    def test_partial_config_mixes_from_config_and_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_config(root, "schema_version: 1\ntargets:\n  - codex\n")
            status = agent_skills_status.compute_status(project_root=root)
            self.assertTrue(status.profile_exists)
            self.assertEqual(status.sources.value, "lrh-package")
            self.assertFalse(status.sources.from_config)
            self.assertEqual(status.targets.value, "codex")
            self.assertTrue(status.targets.from_config)
            self.assertEqual(status.scope.value, "user")
            self.assertFalse(status.scope.from_config)
            self.assertIsNone(status.install_overwrite)

    def test_empty_config_file_reports_exists_with_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_config(root, "")
            status = agent_skills_status.compute_status(project_root=root)
            self.assertTrue(status.profile_exists)
            self.assertFalse(status.sources.from_config)
            self.assertIsNone(status.install_overwrite)

    def test_overwrite_false_is_distinct_from_not_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_config(root, "install:\n  overwrite: false\n")
            status = agent_skills_status.compute_status(project_root=root)
            self.assertFalse(status.install_overwrite)
            self.assertIsNotNone(status.install_overwrite)

    def test_malformed_config_raises_agent_skills_status_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_config(root, "sources: not-a-list\n")
            with self.assertRaises(agent_skills_status.AgentSkillsStatusError):
                agent_skills_status.compute_status(project_root=root)

    def test_agent_skills_status_error_is_installer_skill_source_error(self) -> None:
        self.assertIs(
            agent_skills_status.AgentSkillsStatusError, installer.SkillSourceError
        )


class FormatTest(unittest.TestCase):
    def test_format_text_missing_config(self) -> None:
        status = agent_skills_status.AgentSkillsStatus(
            profile_exists=False,
            sources=agent_skills_status.FieldStatus("lrh-package", False),
            targets=agent_skills_status.FieldStatus("claude", False),
            scope=agent_skills_status.FieldStatus("user", False),
            install_overwrite=None,
        )
        text = agent_skills_status.format_text(status)
        self.assertIn("exists: False", text)
        self.assertIn("conventional-default", text)
        self.assertIn("None", text)

    def test_format_json_round_trips(self) -> None:
        status = agent_skills_status.AgentSkillsStatus(
            profile_exists=True,
            sources=agent_skills_status.FieldStatus("current-repo", True),
            targets=agent_skills_status.FieldStatus("codex", True),
            scope=agent_skills_status.FieldStatus("project", True),
            install_overwrite="skip",
        )
        parsed = json.loads(agent_skills_status.format_json(status))
        self.assertTrue(parsed["profile_exists"])
        self.assertEqual(parsed["sources"], {"value": "current-repo", "from_config": True})
        self.assertEqual(parsed["install_overwrite"], "skip")


if __name__ == "__main__":
    unittest.main()
