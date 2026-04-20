import pathlib
import tempfile
import unittest

from lrh.assist import request_templates


class TestTemplateRoot(unittest.TestCase):
    def test_default_template_root_matches_repo_layout(self) -> None:
        expected_root = pathlib.Path("scripts/aiprog/templates/request").resolve()
        self.assertEqual(request_templates.get_template_root(), expected_root)
        self.assertTrue(expected_root.is_dir())

    def test_template_root_from_script_path_matches_script_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = pathlib.Path(temp_dir) / "scripts" / "aiprog" / "request.py"
            script_path.parent.mkdir(parents=True)
            script_path.write_text("#!/usr/bin/env python\n", encoding="utf-8")

            expected_root = script_path.parent / "templates" / "request"
            self.assertEqual(
                request_templates.get_template_root_from_script_path(script_path),
                expected_root,
            )


class TestTemplatePathAndLoading(unittest.TestCase):
    def test_existing_template_resolves_successfully(self) -> None:
        template_path = request_templates.get_template_path("improve_coverage")
        self.assertTrue(template_path.exists())
        self.assertEqual(template_path.name, "improve_coverage.md")

    def test_missing_template_raises_file_not_found_error(self) -> None:
        with self.assertRaisesRegex(FileNotFoundError, "Template not found"):
            request_templates.get_template_path("does_not_exist")

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
