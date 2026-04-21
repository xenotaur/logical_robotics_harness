import os
import pathlib
import subprocess
import sys
import unittest


class TestLrhRequestCli(unittest.TestCase):
    def _run_lrh(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        src_path = pathlib.Path("src").resolve()
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            str(src_path) if not existing else f"{src_path}{os.pathsep}{existing}"
        )
        return subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", *args],
            check=False,
            capture_output=True,
            text=True,
            env=env,
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
