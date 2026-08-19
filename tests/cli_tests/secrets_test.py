import pathlib
import subprocess
import unittest
import unittest.mock

from lrh.cli import main as cli_main
from lrh.secrets import scan as secrets_scan


class TestLrhSecretsScanCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = pathlib.Path(__file__).resolve().parents[2]

    def _run_lrh(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["lrh", *args],
            check=False,
            capture_output=True,
            text=True,
            cwd=self.repo_root,
        )

    def test_lrh_secrets_scan_help(self) -> None:
        result = self._run_lrh(["secrets", "scan", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("--project-root", result.stdout)
        self.assertIn("--out-dir", result.stdout)
        self.assertIn("--format", result.stdout)

    def test_lrh_secrets_scan_help_documents_provider_coverage_limits(self) -> None:
        result = self._run_lrh(["secrets", "scan", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Azure", result.stdout)
        self.assertIn(".ipynb", result.stdout)

    def test_lrh_secrets_requires_subcommand(self) -> None:
        result = self._run_lrh(["secrets"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("secrets requires a subcommand", result.stderr)
        self.assertIn("lrh secrets scan", result.stderr)

    def test_lrh_secrets_scan_delegates_to_secrets_scan_module(self) -> None:
        fake_result = secrets_scan.ScanResult(
            findings_count=0,
            replacements_count=0,
            findings_path=pathlib.Path("/tmp/out/findings.json"),
            replacements_path=None,
        )
        with unittest.mock.patch(
            "lrh.cli.main.secrets_scan.run_scan",
            return_value=fake_result,
        ) as mock_run_scan:
            with unittest.mock.patch(
                "sys.argv",
                [
                    "lrh",
                    "secrets",
                    "scan",
                    "--project-root",
                    ".",
                    "--out-dir",
                    "/tmp/out",
                    "--format",
                    "json",
                ],
            ):
                with self.assertRaises(SystemExit) as exc:
                    cli_main.main()
        self.assertEqual(exc.exception.code, 0)
        mock_run_scan.assert_called_once()
        _, kwargs = mock_run_scan.call_args
        self.assertEqual(kwargs["out_dir"], pathlib.Path("/tmp/out").resolve())
        self.assertEqual(kwargs["project_root"], pathlib.Path(".").resolve())


if __name__ == "__main__":
    unittest.main()
