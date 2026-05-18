import importlib.resources
import pathlib
import tempfile
import unittest

from lrh.assist import request_templates


class TestTemplateRoot(unittest.TestCase):
    def test_default_template_root_is_package_resource(self) -> None:
        expected_root = importlib.resources.files("lrh.assist").joinpath(
            "templates", "request"
        )
        self.assertEqual(request_templates.get_template_root(), expected_root)
        self.assertTrue(expected_root.joinpath("improve_coverage.md").is_file())


class TestTemplatePathAndLoading(unittest.TestCase):
    def test_existing_template_loads_from_package_resources(self) -> None:
        loaded = request_templates.load_template_text("improve_coverage")
        self.assertIn("{{TARGET_MODULE_GHA}}", loaded)

    def test_ci_assess_status_template_loads_from_package_resources(self) -> None:
        loaded = request_templates.load_template_text("ci_assess_status")
        self.assertIn("CI Feasibility Assessment Request", loaded)

    def test_ci_assess_status_template_includes_portable_ci_playbook(self) -> None:
        loaded = request_templates.load_template_text("ci_assess_status")
        self.assertIn("PACKAGED CI PLAYBOOK SUMMARY", loaded)
        self.assertIn("Do not fail solely because", loaded)
        self.assertIn("docs/how-to/project-setup/ci.md", loaded)

    def test_ci_implement_workflow_template_loads_from_package_resources(self) -> None:
        loaded = request_templates.load_template_text("ci_implement_workflow")
        self.assertIn("CI Migration Implementation Request", loaded)

    def test_ci_implement_workflow_template_includes_portable_ci_playbook(
        self,
    ) -> None:
        loaded = request_templates.load_template_text("ci_implement_workflow")
        self.assertIn("PACKAGED CI PLAYBOOK SUMMARY", loaded)
        self.assertIn("continue with the packaged summary", loaded)
        self.assertIn("docs/how-to/project-setup/ci.md", loaded)

    def test_work_item_semantic_audit_template_loads_from_package_resources(
        self,
    ) -> None:
        loaded = request_templates.load_template_text("work_item_semantic_audit")
        self.assertIn("Semantic Work-Item Lifecycle Audit Request", loaded)
        self.assertIn("Avoid optimistic closure", loaded)

    def test_ready_work_item_template_loads_from_package_resources(self) -> None:
        loaded = request_templates.load_template_text("ready_work_item")

        self.assertIn("Ready Work Item Refinement Request", loaded)
        self.assertIn("{{READINESS_DIAGNOSTICS}}", loaded)
        self.assertIn("Open Questions", loaded)

    def test_missing_template_raises_file_not_found_error(self) -> None:
        with self.assertRaisesRegex(FileNotFoundError, "Template not found"):
            request_templates.load_template_text("does_not_exist")

    def test_load_template_text_reads_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            template_root = pathlib.Path(temp_dir)
            template_path = template_root / "custom.md"
            template_path.write_text("hello café\n", encoding="utf-8")

            loaded = request_templates.load_template_text(
                "custom",
                template_root=template_root,
            )

            self.assertEqual(loaded, "hello café\n")

    def test_codex_prompt_template_uses_portable_repository_guidance(self) -> None:
        loaded = request_templates.load_template_text("codex_prompt_from_work_item")
        self.assertIn("If `AGENTS.md` exists, read and follow it.", loaded)
        self.assertIn("If `PROMPTS.md` exists, follow its prompt-ID", loaded)
        self.assertIn(
            "Prefer `lrh prompt record-execution` if LRH is installed.", loaded
        )

    def test_codex_prompt_template_avoids_repo_local_record_script_assumptions(
        self,
    ) -> None:
        loaded = request_templates.load_template_text("codex_prompt_from_work_item")
        self.assertNotIn("scripts/prompts/record-execution", loaded)
        self.assertIn("if missing, report the gap", loaded)

    def test_review_response_template_includes_task_phase_validation_guidance(
        self,
    ) -> None:
        loaded = request_templates.load_template_text("review_response")
        expected = (
            "Do not routinely run `scripts/develop` during ordinary "
            "agent-task validation."
        )
        self.assertIn(expected, loaded)
        self.assertIn("scripts/version tools", loaded)
        self.assertIn("ModuleNotFoundError: lrh", loaded)
        self.assertIn("setup/bootstrap mismatch", loaded)

    def test_template_root_override_is_used(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            template_root = pathlib.Path(temp_dir)
            template_path = template_root / "override.md"
            template_path.write_text("content\n", encoding="utf-8")

            resolved = request_templates.get_template_path(
                "override",
                template_root=template_root,
            )

            self.assertEqual(resolved, template_path)


if __name__ == "__main__":
    unittest.main()
