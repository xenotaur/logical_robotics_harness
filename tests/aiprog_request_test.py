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
    def test_main_passes_script_relative_template_root_to_service(self) -> None:
        module = _load_request_module()
        expected_root = pathlib.Path("scripts/aiprog/templates/request").resolve()

        with mock.patch.object(
            module.request_cli,
            "run_request_cli",
            return_value=0,
        ) as mock_run_request_cli:
            exit_code = module.main(["improve_coverage", "src/lrh/analysis/foo.py"])

        self.assertEqual(exit_code, 0)
        mock_run_request_cli.assert_called_once()
        self.assertEqual(
            mock_run_request_cli.call_args.kwargs["template_root"],
            expected_root,
        )


if __name__ == "__main__":
    unittest.main()
