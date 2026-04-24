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
