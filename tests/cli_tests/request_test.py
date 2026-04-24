import subprocess
import tempfile
import unittest


class TestLrhRequestCli(unittest.TestCase):
    def _run_lrh(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            return subprocess.run(
                ["lrh", *args],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

    def test_lrh_request_help(self) -> None:
        result = self._run_lrh(["request", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("lrh request", result.stdout)

    def test_lrh_request_improve_coverage(self) -> None:
        result = self._run_lrh(
            ["request", "improve_coverage", "src/lrh/analysis/llm_extractor.py"]
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("TARGET MODULE:", result.stdout)
        self.assertIn("src/lrh/analysis/llm_extractor.py", result.stdout)

    def test_lrh_request_invalid_arguments(self) -> None:
        result = self._run_lrh(["request", "assessment", "--scope", "work_item"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("requires --target", result.stderr)


if __name__ == "__main__":
    unittest.main()
