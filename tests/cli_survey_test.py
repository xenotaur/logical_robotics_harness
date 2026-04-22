import pathlib
import subprocess
import unittest
import unittest.mock

from lrh.cli import main as cli_main


class TestLrhSurveyCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = pathlib.Path(__file__).resolve().parents[1]

    def _run_lrh(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["lrh", *args],
            check=False,
            capture_output=True,
            text=True,
            cwd=self.repo_root,
        )

    def test_lrh_survey_help(self) -> None:
        result = self._run_lrh(["survey", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("lrh survey", result.stdout)
        self.assertIn("--tests-root", result.stdout)
        self.assertIn("--format", result.stdout)

    def test_lrh_survey_json_output(self) -> None:
        result = self._run_lrh(
            [
                "survey",
                str(self.repo_root / "src/lrh/assist"),
                "--tests-root",
                str(self.repo_root / "tests/assist"),
                "--format",
                "json",
            ]
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('"module": "sourcetree_surveyor"', result.stdout)
        self.assertIn('"test_file_guess": "sourcetree_surveyor_test.py"', result.stdout)

    def test_lrh_survey_invalid_root(self) -> None:
        result = self._run_lrh(["survey", "does/not/exist"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("ERROR: root not found or not a directory", result.stderr)

    def test_lrh_survey_invalid_tests_root(self) -> None:
        result = self._run_lrh(
            [
                "survey",
                str(self.repo_root / "src/lrh/assist"),
                "--tests-root",
                "does/not/exist",
            ]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn(
            "ERROR: tests-root not found or not a directory",
            result.stderr,
        )

    def test_lrh_survey_delegates_to_assist_module(self) -> None:
        with unittest.mock.patch(
            "lrh.cli.main.sourcetree_surveyor.main",
            return_value=7,
        ) as mock_survey_main:
            with unittest.mock.patch(
                "sys.argv",
                ["lrh", "survey", "src/lrh/assist", "--format", "json"],
            ):
                with self.assertRaises(SystemExit) as exc:
                    cli_main.main()
        self.assertEqual(exc.exception.code, 7)
        mock_survey_main.assert_called_once_with(
            argv=["src/lrh/assist", "--format", "json"],
            prog="lrh survey",
        )


if __name__ == "__main__":
    unittest.main()
