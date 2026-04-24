import os
import pathlib
import tempfile
import unittest

from lrh.assist import request_variables


class TestNormalizeTargetForGha(unittest.TestCase):
    def test_none_input_returns_empty_string(self) -> None:
        self.assertEqual(request_variables.normalize_target_for_gha(None), "")

    def test_empty_input_returns_empty_string(self) -> None:
        self.assertEqual(request_variables.normalize_target_for_gha(""), "")

    def test_already_normalized_target_is_unchanged(self) -> None:
        target = "src/lrh/analysis/foo.py"
        self.assertEqual(request_variables.normalize_target_for_gha(target), target)

    def test_lrh_prefix_is_rewritten_to_src_lrh(self) -> None:
        self.assertEqual(
            request_variables.normalize_target_for_gha("lrh/analysis/foo.py"),
            "src/lrh/analysis/foo.py",
        )

    def test_relative_module_like_path_is_prefixed(self) -> None:
        self.assertEqual(
            request_variables.normalize_target_for_gha("analysis/foo.py"),
            "src/lrh/analysis/foo.py",
        )


class TestComputeSuggestedTestPath(unittest.TestCase):
    def test_src_lrh_path_maps_to_tests_subdir(self) -> None:
        self.assertEqual(
            request_variables.compute_suggested_test_path("src/lrh/analysis/foo.py"),
            "tests/analysis/foo_test.py",
        )

    def test_nested_src_lrh_path_maps_to_nested_tests_path(self) -> None:
        self.assertEqual(
            request_variables.compute_suggested_test_path(
                "src/lrh/analysis/extractors/foo.py"
            ),
            "tests/analysis/extractors/foo_test.py",
        )

    def test_unexpected_structure_uses_fallback(self) -> None:
        self.assertEqual(
            request_variables.compute_suggested_test_path("scripts/tooling.py"),
            "tests/tooling_test.py",
        )

    def test_empty_input_returns_empty_string(self) -> None:
        self.assertEqual(request_variables.compute_suggested_test_path(""), "")


class TestReadOptionalText(unittest.TestCase):
    def test_none_input_returns_empty_string(self) -> None:
        self.assertEqual(request_variables.read_optional_text(None), "")

    def test_reads_valid_utf8_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / "context.md"
            path.write_text("hello utf8\n", encoding="utf-8")

            self.assertEqual(
                request_variables.read_optional_text(str(path)),
                "hello utf8",
            )

    def test_missing_file_raises_file_not_found_error(self) -> None:
        with self.assertRaises(FileNotFoundError):
            request_variables.read_optional_text("does_not_exist.md")


class TestInferRepoName(unittest.TestCase):
    def test_explicit_repo_name_is_preferred(self) -> None:
        self.assertEqual(
            request_variables.infer_repo_name("target-value", "explicit-repo"),
            "explicit-repo",
        )

    def test_infers_repo_name_from_target_input(self) -> None:
        self.assertEqual(
            request_variables.infer_repo_name("src/lrh/analysis/foo.py", None),
            "foo.py",
        )

    def test_falls_back_to_current_working_directory_name(self) -> None:
        original_cwd = pathlib.Path.cwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            try:
                # chdir needed to verify cwd-based fallback behavior.
                os.chdir(temp_path)
                self.assertEqual(
                    request_variables.infer_repo_name(None, None),
                    temp_path.name,
                )
            finally:
                os.chdir(original_cwd)


class TestNormalizeFileReference(unittest.TestCase):
    def test_none_input_returns_empty_string(self) -> None:
        self.assertEqual(request_variables.normalize_file_reference(None), "")

    def test_relative_path_is_normalized(self) -> None:
        self.assertEqual(
            request_variables.normalize_file_reference("./STYLE.md"),
            "STYLE.md",
        )

    def test_path_outside_repo_is_preserved_as_string(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            external_path = pathlib.Path(temp_dir) / "external.md"
            external_path.write_text("outside", encoding="utf-8")
            normalized = request_variables.normalize_file_reference(str(external_path))
            self.assertEqual(normalized, str(external_path).replace("\\", "/"))

    def test_uses_repo_root_not_current_subdirectory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = pathlib.Path(temp_dir) / "repo"
            repo_root.mkdir()
            (repo_root / ".git").mkdir()
            style_path = repo_root / "STYLE.md"
            style_path.write_text("style", encoding="utf-8")
            nested_dir = repo_root / "src" / "lrh"
            nested_dir.mkdir(parents=True)

            original_cwd = pathlib.Path.cwd()
            try:
                os.chdir(nested_dir)
                self.assertEqual(
                    request_variables.normalize_file_reference(str(style_path)),
                    "STYLE.md",
                )
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
