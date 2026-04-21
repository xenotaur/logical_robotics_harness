import importlib.util
import pathlib
import unittest
from unittest import mock


def _load_request_module():
    script_path = pathlib.Path("scripts/aiprog/request.py").resolve()
    spec = importlib.util.spec_from_file_location("aiprog_request", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestRequestTemplateResolution(unittest.TestCase):
    def test_load_template_uses_script_relative_template_root(self) -> None:
        module = _load_request_module()
        expected_root = pathlib.Path("scripts/aiprog/templates/request").resolve()

        with (
            mock.patch.object(
                module.request_templates,
                "get_template_path",
                return_value=expected_root / "improve_coverage.md",
            ) as mock_get_template_path,
            mock.patch.object(
                module.request_templates,
                "load_template_text",
                return_value="template",
            ) as mock_load_template_text,
        ):
            module._load_template("improve_coverage")

        mock_get_template_path.assert_called_once_with(
            "improve_coverage",
            template_root=expected_root,
        )
        mock_load_template_text.assert_called_once_with(
            "improve_coverage",
            template_root=expected_root,
        )


if __name__ == "__main__":
    unittest.main()
