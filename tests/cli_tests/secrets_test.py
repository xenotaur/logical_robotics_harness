import json
import pathlib
import subprocess
import tempfile
import unittest
import unittest.mock

from lrh.cli import main as cli_main
from lrh.secrets import review as secrets_review
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


class TestLrhSecretsReviewCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = pathlib.Path(__file__).resolve().parents[2]

    def _run_lrh(
        self, args: list[str], cwd: pathlib.Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["lrh", *args],
            check=False,
            capture_output=True,
            text=True,
            cwd=cwd or self.repo_root,
        )

    def test_lrh_secrets_review_help(self) -> None:
        result = self._run_lrh(["secrets", "review", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("--out-dir", result.stdout)
        self.assertIn("--decisions", result.stdout)
        self.assertIn("--check", result.stdout)
        self.assertIn("--apply", result.stdout)

    def test_lrh_secrets_requires_subcommand_names_scan(self) -> None:
        result = self._run_lrh(["secrets"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("secrets requires a subcommand", result.stderr)

    def test_lrh_secrets_review_missing_findings_report_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)  # no findings.json written
            result = self._run_lrh(
                ["secrets", "review", "--out-dir", str(out_dir), "--check"]
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("not found", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_lrh_secrets_review_out_dir_not_a_directory_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            not_a_dir = pathlib.Path(tmp) / "does-not-exist"
            result = self._run_lrh(
                ["secrets", "review", "--out-dir", str(not_a_dir), "--check"]
            )
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)

    def test_lrh_secrets_review_malformed_decisions_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            with (out_dir / "findings.json").open("w") as f:
                json.dump([{"Secret": "sk-aaa", "RuleID": "openai-api-key"}], f)
            decisions_path = out_dir / "decisions.yaml"
            decisions_path.write_text("sk-aaa: keep\n")  # not a mapping
            result = self._run_lrh(
                [
                    "secrets",
                    "review",
                    "--out-dir",
                    str(out_dir),
                    "--decisions",
                    str(decisions_path),
                    "--check",
                ]
            )
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)

    def test_lrh_secrets_review_apply_invalidates_stale_reviewed_on_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            stale = out_dir / "replacements.reviewed.txt"
            out_dir.mkdir(parents=True, exist_ok=True)
            stale.write_text("# lrh-secrets-reviewed v1\nold-secret==>x\n")
            with (out_dir / "findings.json").open("w") as f:
                json.dump([{"Secret": "sk-new", "RuleID": "generic-api-key"}], f)
            result = self._run_lrh(
                ["secrets", "review", "--out-dir", str(out_dir), "--apply"]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(
                stale.exists(), "a failed --apply must not leave a stale reviewed file"
            )

    def test_lrh_secrets_review_apply_invalidates_stale_reviewed_on_input_error(
        self,
    ) -> None:
        """A --apply that fails via ReviewInputError (not just undecided
        findings) must also invalidate a stale reviewed file -- regression
        test for a gap a substitute self-review caught: the invalidation
        call originally lived only inside the undecided-findings branch,
        never reached when build_report() itself raised first."""
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            stale = out_dir / "replacements.reviewed.txt"
            stale.write_text("# lrh-secrets-reviewed v1\nold-secret==>x\n")
            # Malformed decisions file triggers ReviewInputError before
            # undecided() is ever computed.
            decisions_path = out_dir / "decisions.yaml"
            decisions_path.write_text("sk-aaa: keep\n")  # not a mapping
            with (out_dir / "findings.json").open("w") as f:
                json.dump([{"Secret": "sk-aaa", "RuleID": "openai-api-key"}], f)
            result = self._run_lrh(
                [
                    "secrets",
                    "review",
                    "--out-dir",
                    str(out_dir),
                    "--decisions",
                    str(decisions_path),
                    "--apply",
                ]
            )
            self.assertEqual(result.returncode, 2)
            self.assertFalse(
                stale.exists(),
                "a --apply failing via ReviewInputError must also invalidate "
                "a stale reviewed file",
            )

    def test_lrh_secrets_review_check_fails_on_undecided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            with (out_dir / "findings.json").open("w") as f:
                json.dump([{"Secret": "sk-aaa", "RuleID": "openai-api-key"}], f)
            result = self._run_lrh(
                ["secrets", "review", "--out-dir", str(out_dir), "--check"]
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("UNDECIDED", result.stdout)

    def test_lrh_secrets_review_check_passes_when_decided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            with (out_dir / "findings.json").open("w") as f:
                json.dump([{"Secret": "sk-aaa", "RuleID": "openai-api-key"}], f)
            decisions_path = out_dir / "decisions.yaml"
            decisions_path.write_text("sk-aaa:\n  decision: keep\n  reason: real\n")
            result = self._run_lrh(
                [
                    "secrets",
                    "review",
                    "--out-dir",
                    str(out_dir),
                    "--decisions",
                    str(decisions_path),
                    "--check",
                ]
            )
            self.assertEqual(result.returncode, 0)

    def test_lrh_secrets_review_apply_writes_reviewed_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            with (out_dir / "findings.json").open("w") as f:
                json.dump([{"Secret": "sk-aaa", "RuleID": "openai-api-key"}], f)
            decisions_path = out_dir / "decisions.yaml"
            decisions_path.write_text("sk-aaa:\n  decision: keep\n  reason: real\n")
            result = self._run_lrh(
                [
                    "secrets",
                    "review",
                    "--out-dir",
                    str(out_dir),
                    "--decisions",
                    str(decisions_path),
                    "--apply",
                ]
            )
            self.assertEqual(result.returncode, 0)
            reviewed = out_dir / "replacements.reviewed.txt"
            self.assertTrue(reviewed.exists())
            self.assertEqual(
                reviewed.read_text().splitlines()[0], "# lrh-secrets-reviewed v1"
            )

    def test_lrh_secrets_review_apply_refuses_when_undecided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            with (out_dir / "findings.json").open("w") as f:
                json.dump([{"Secret": "sk-aaa", "RuleID": "openai-api-key"}], f)
            result = self._run_lrh(
                ["secrets", "review", "--out-dir", str(out_dir), "--apply"]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((out_dir / "replacements.reviewed.txt").exists())

    def test_lrh_secrets_review_check_and_apply_mutually_exclusive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            result = self._run_lrh(
                [
                    "secrets",
                    "review",
                    "--out-dir",
                    str(out_dir),
                    "--check",
                    "--apply",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("mutually exclusive", result.stderr)

    def test_lrh_secrets_review_delegates_to_secrets_review_module(self) -> None:
        fake_report = secrets_review.ReviewReport(secrets=[], decisions={})
        with unittest.mock.patch(
            "lrh.cli.main.secrets_review.build_report",
            return_value=fake_report,
        ) as mock_build_report:
            with unittest.mock.patch(
                "sys.argv",
                ["lrh", "secrets", "review", "--out-dir", "/tmp/out"],
            ):
                with self.assertRaises(SystemExit) as exc:
                    cli_main.main()
        self.assertEqual(exc.exception.code, 0)
        mock_build_report.assert_called_once()
        _, kwargs = mock_build_report.call_args
        self.assertEqual(kwargs["out_dir"], pathlib.Path("/tmp/out").resolve())
        self.assertIsNone(kwargs["decisions_path"])


class TestLrhSecretsPurgeCli(unittest.TestCase):
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

    def test_lrh_secrets_purge_help(self) -> None:
        result = self._run_lrh(["secrets", "purge", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("--project-root", result.stdout)
        self.assertIn("--source", result.stdout)
        self.assertIn("--refs-file", result.stdout)
        self.assertIn("--replacements", result.stdout)
        self.assertIn("--mirror-dir", result.stdout)
        self.assertIn("--dry-run", result.stdout)
        self.assertIn("--apply", result.stdout)

    def test_lrh_secrets_purge_help_documents_reviewed_replacements_expectation(
        self,
    ) -> None:
        result = self._run_lrh(["secrets", "purge", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("replacements.reviewed.txt", result.stdout)

    def test_lrh_secrets_requires_subcommand_mentions_purge(self) -> None:
        result = self._run_lrh(["secrets"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lrh secrets purge", result.stderr)

    def test_lrh_secrets_purge_missing_refs_file_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            replacements_path = out_dir / "replacements.reviewed.txt"
            replacements_path.write_text(
                "# lrh-secrets-reviewed v1\nsk-aaa==>***REMOVED-x***\n"
            )
            result = self._run_lrh(
                [
                    "secrets",
                    "purge",
                    "--refs-file",
                    str(out_dir / "missing-refs.txt"),
                    "--replacements",
                    str(replacements_path),
                    "--dry-run",
                ]
            )
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)

    def test_lrh_secrets_purge_missing_marker_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            refs_file = out_dir / "refs.txt"
            refs_file.write_text("refs/heads/main\n")
            replacements_path = out_dir / "replacements.txt"
            replacements_path.write_text("sk-aaa==>***REMOVED-x***\n")
            result = self._run_lrh(
                [
                    "secrets",
                    "purge",
                    "--refs-file",
                    str(refs_file),
                    "--replacements",
                    str(replacements_path),
                    "--dry-run",
                ]
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("review --apply", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_lrh_secrets_purge_dry_run_and_apply_mutually_exclusive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            refs_file = out_dir / "refs.txt"
            refs_file.write_text("refs/heads/main\n")
            replacements_path = out_dir / "replacements.reviewed.txt"
            replacements_path.write_text(
                "# lrh-secrets-reviewed v1\nsk-aaa==>***REMOVED-x***\n"
            )
            result = self._run_lrh(
                [
                    "secrets",
                    "purge",
                    "--refs-file",
                    str(refs_file),
                    "--replacements",
                    str(replacements_path),
                    "--dry-run",
                    "--apply",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("mutually exclusive", result.stderr)

    def test_lrh_secrets_purge_dry_run_reports_no_rewrite(self) -> None:
        # Mocks the git-filter-repo availability boundary rather than
        # requiring the real binary, so this unit test stays hermetic --
        # the real-binary path is covered separately by the skip-gated
        # smoke test.
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            refs_file = out_dir / "refs.txt"
            refs_file.write_text("refs/heads/main\n")
            replacements_path = out_dir / "replacements.reviewed.txt"
            replacements_path.write_text(
                "# lrh-secrets-reviewed v1\nsk-aaa==>***REMOVED-x***\n"
            )
            with unittest.mock.patch(
                "lrh.cli.main.secrets_purge.check_filter_repo_available",
                return_value=None,
            ):
                with unittest.mock.patch(
                    "sys.argv",
                    [
                        "lrh",
                        "secrets",
                        "purge",
                        "--source",
                        "git@example.com:x",
                        "--refs-file",
                        str(refs_file),
                        "--replacements",
                        str(replacements_path),
                        "--dry-run",
                    ],
                ):
                    with self.assertRaises(SystemExit) as exc:
                        cli_main.main()
            self.assertEqual(exc.exception.code, 0)

    def test_lrh_secrets_purge_delegates_to_secrets_purge_module(self) -> None:
        with unittest.mock.patch(
            "lrh.cli.main.secrets_purge.run_purge",
            return_value="DRY RUN: ...",
        ) as mock_run_purge:
            with unittest.mock.patch(
                "sys.argv",
                [
                    "lrh",
                    "secrets",
                    "purge",
                    "--refs-file",
                    "/tmp/refs.txt",
                    "--replacements",
                    "/tmp/replacements.reviewed.txt",
                    "--dry-run",
                ],
            ):
                with self.assertRaises(SystemExit) as exc:
                    cli_main.main()
        self.assertEqual(exc.exception.code, 0)
        mock_run_purge.assert_called_once()
        _, kwargs = mock_run_purge.call_args
        self.assertEqual(kwargs["refs_file"], pathlib.Path("/tmp/refs.txt").resolve())
        self.assertEqual(
            kwargs["replacements_path"],
            pathlib.Path("/tmp/replacements.reviewed.txt").resolve(),
        )
        self.assertFalse(kwargs["apply"])
        self.assertIsNone(kwargs["mirror_dir"])


if __name__ == "__main__":
    unittest.main()
