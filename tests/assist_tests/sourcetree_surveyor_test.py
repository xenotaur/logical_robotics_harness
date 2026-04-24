import json
import pathlib
import tempfile
import unittest

from lrh.assist import sourcetree_surveyor


class TestSourcetreeSurveyorImport(unittest.TestCase):
    def test_module_imports_from_assist_package(self) -> None:
        self.assertTrue(hasattr(sourcetree_surveyor, "survey_python_tree"))
        self.assertTrue(callable(sourcetree_surveyor.survey_python_tree))


class TestSourcetreeSurveyorAnalysis(unittest.TestCase):
    def test_scan_tree_collects_public_and_private_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir) / "src"
            tests_root = pathlib.Path(temp_dir) / "tests"
            root.mkdir(parents=True)
            tests_root.mkdir(parents=True)

            source_path = root / "sample.py"
            source_path.write_text(
                "\n".join(
                    [
                        "import os",
                        "from pathlib import Path",
                        "",
                        "def public_func():",
                        '    """Public doc."""',
                        "    return 1",
                        "",
                        "async def _private_async():",
                        "    return 2",
                        "",
                        "class PublicClass:",
                        '    """Class doc."""',
                        "    pass",
                        "",
                        "class _PrivateClass:",
                        "    pass",
                        "",
                        'if __name__ == "__main__":',
                        "    pass",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (tests_root / "sample_test.py").write_text("", encoding="utf-8")

            survey = sourcetree_surveyor.survey_python_tree(root, tests_root)
            self.assertEqual(survey.schema_version, "1.0")
            self.assertEqual(survey.tests_root, str(tests_root))
            self.assertFalse(survey.tests_root_inferred)
            self.assertEqual(survey.discovered_test_files, ["sample_test.py"])
            self.assertEqual(len(survey.files), 1)

            report = survey.files[0]
            self.assertEqual(report.relpath, "sample.py")
            self.assertEqual(report.module, "sample")
            self.assertEqual(report.syntax_error, None)
            self.assertEqual(report.top_level_imports, 2)
            self.assertTrue(report.has_main_guard)
            self.assertEqual(report.test_file_guess, "sample_test.py")
            self.assertTrue(report.test_file_exists)

            self.assertEqual(
                [s.name for s in report.functions], ["public_func", "_private_async"]
            )
            self.assertEqual(
                [s.kind for s in report.functions], ["function", "async_function"]
            )
            self.assertEqual(
                [s.name for s in report.classes], ["PublicClass", "_PrivateClass"]
            )

    def test_json_and_markdown_render_expected_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir) / "src"
            root.mkdir(parents=True)
            source_path = root / "simple.py"
            source_path.write_text("def visible():\n    return 1\n", encoding="utf-8")

            survey = sourcetree_surveyor.survey_python_tree(root, tests_root=None)

            markdown = sourcetree_surveyor.to_markdown(survey)
            self.assertIn("# Surface inventory:", markdown)
            self.assertIn("### Public functions", markdown)
            self.assertIn("`visible`", markdown)

            json_text = sourcetree_surveyor.to_json(survey)
            payload = json.loads(json_text)
            self.assertEqual(payload["schema_version"], "1.0")
            self.assertEqual(payload["files"][0]["module"], "simple")
            self.assertEqual(payload["files"][0]["functions"][0]["name"], "visible")
            self.assertIn("pyproject_toml_present", payload)

    def test_infers_tests_root_when_local_tests_directory_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir) / "workspace"
            source_root = root / "src"
            source_root.mkdir(parents=True)
            (source_root / "module.py").write_text(
                "def demo():\n    return 1\n",
                encoding="utf-8",
            )
            tests_root = source_root / "tests"
            tests_root.mkdir()
            (tests_root / "test_module.py").write_text("", encoding="utf-8")

            survey = sourcetree_surveyor.survey_python_tree(
                source_root,
                tests_root=None,
            )

            self.assertTrue(survey.tests_root_inferred)
            self.assertEqual(survey.tests_root, str(tests_root))
            self.assertEqual(survey.discovered_test_files, ["test_module.py"])

    def test_cli_candidate_match_handles_windows_relpath_separator(self) -> None:
        self.assertTrue(
            sourcetree_surveyor._is_cli_candidate_relpath("pkg\\tools\\cli.py")
        )


if __name__ == "__main__":
    unittest.main()
