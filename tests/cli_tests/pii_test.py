import pathlib
import subprocess
import tempfile
import unittest
import unittest.mock

from lrh.cli import main as cli_main
from lrh.pii import config as pii_config
from lrh.pii import layer2 as pii_layer2
from lrh.pii import output as pii_output
from lrh.pii import scan as pii_scan


class TestLrhPiiScanCli(unittest.TestCase):
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

    def test_lrh_pii_scan_help(self) -> None:
        result = self._run_lrh(["pii", "scan", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("--project-root", result.stdout)
        self.assertIn("--out-dir", result.stdout)
        self.assertIn("--config", result.stdout)
        self.assertIn("--format", result.stdout)

    def test_lrh_pii_scan_help_documents_disclosed_gaps(self) -> None:
        result = self._run_lrh(["pii", "scan", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("no OCR", result.stdout)
        self.assertIn("ML/NLP", result.stdout)

    def test_lrh_pii_requires_subcommand(self) -> None:
        result = self._run_lrh(["pii"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pii requires a subcommand", result.stderr)
        self.assertIn("lrh pii scan", result.stderr)

    def test_lrh_pii_scan_delegates_to_pii_scan_module(self) -> None:
        fake_result = pii_scan.ScanResult(
            findings_count=0,
            allowlisted_count=0,
            findings_path=pathlib.Path("/tmp/out/pii_findings.json"),
            findings=(),
        )
        with unittest.mock.patch(
            "lrh.cli.main.pii_scan.run_scan", return_value=fake_result
        ) as mock_run_scan:
            with unittest.mock.patch(
                "sys.argv",
                [
                    "lrh",
                    "pii",
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
        self.assertIsNone(kwargs["config_path"])

    def test_lrh_pii_scan_resolves_config_flag(self) -> None:
        fake_result = pii_scan.ScanResult(
            findings_count=0,
            allowlisted_count=0,
            findings_path=pathlib.Path("/tmp/out/pii_findings.json"),
            findings=(),
        )
        with unittest.mock.patch(
            "lrh.cli.main.pii_scan.run_scan", return_value=fake_result
        ) as mock_run_scan:
            with unittest.mock.patch(
                "sys.argv",
                [
                    "lrh",
                    "pii",
                    "scan",
                    "--out-dir",
                    "/tmp/out",
                    "--config",
                    "/tmp/custom.toml",
                ],
            ):
                with self.assertRaises(SystemExit):
                    cli_main.main()
        _, kwargs = mock_run_scan.call_args
        self.assertEqual(
            kwargs["config_path"], pathlib.Path("/tmp/custom.toml").resolve()
        )

    def test_lrh_pii_scan_reports_config_error(self) -> None:
        with unittest.mock.patch(
            "lrh.cli.main.pii_scan.run_scan",
            side_effect=pii_config.PiiConfigError("bad config"),
        ):
            with unittest.mock.patch(
                "sys.argv",
                ["lrh", "pii", "scan", "--out-dir", "/tmp/out"],
            ):
                with self.assertRaises(SystemExit) as exc:
                    cli_main.main()
        self.assertEqual(exc.exception.code, 2)

    def test_lrh_pii_scan_reports_non_git_project_root_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with unittest.mock.patch(
                "sys.argv",
                ["lrh", "pii", "scan", "--project-root", tmp, "--out-dir", "/tmp/out"],
            ):
                with self.assertRaises(SystemExit) as exc:
                    cli_main.main()
        self.assertEqual(exc.exception.code, 2)

    def test_lrh_pii_scan_reports_layer2_content_read_error_cleanly(self) -> None:
        with unittest.mock.patch(
            "lrh.cli.main.pii_scan.run_scan",
            side_effect=pii_layer2.Layer2ContentReadError("git show failed"),
        ):
            with unittest.mock.patch(
                "sys.argv",
                ["lrh", "pii", "scan", "--out-dir", "/tmp/out"],
            ):
                with self.assertRaises(SystemExit) as exc:
                    cli_main.main()
        self.assertEqual(exc.exception.code, 2)

    def test_lrh_pii_scan_reports_layer1_blob_read_error_cleanly(self) -> None:
        with unittest.mock.patch(
            "lrh.cli.main.pii_scan.run_scan",
            side_effect=pii_output.Layer1BlobReadError("git rev-parse failed"),
        ):
            with unittest.mock.patch(
                "sys.argv",
                ["lrh", "pii", "scan", "--out-dir", "/tmp/out"],
            ):
                with self.assertRaises(SystemExit) as exc:
                    cli_main.main()
        self.assertEqual(exc.exception.code, 2)

    def test_lrh_pii_scan_reports_os_error_cleanly(self) -> None:
        with unittest.mock.patch(
            "lrh.cli.main.pii_scan.run_scan",
            side_effect=OSError("Permission denied: /tmp/out"),
        ):
            with unittest.mock.patch(
                "sys.argv",
                ["lrh", "pii", "scan", "--out-dir", "/tmp/out"],
            ):
                with self.assertRaises(SystemExit) as exc:
                    cli_main.main()
        self.assertEqual(exc.exception.code, 2)

    def test_lrh_pii_scan_reports_missing_explicit_config_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with unittest.mock.patch(
                "sys.argv",
                [
                    "lrh",
                    "pii",
                    "scan",
                    "--project-root",
                    tmp,
                    "--out-dir",
                    "/tmp/out",
                    "--config",
                    str(pathlib.Path(tmp) / "does-not-exist.toml"),
                ],
            ):
                with self.assertRaises(SystemExit) as exc:
                    cli_main.main()
        self.assertEqual(exc.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
