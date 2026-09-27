import contextlib
import io
import pathlib
import tempfile
import unittest

from local_agent import cli


class CliTest(unittest.TestCase):
    def test_unknown_packet_reports_error_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = cli.main(
                    [
                        "--store",
                        str(pathlib.Path(tmp) / "store"),
                        "run",
                        "--packet",
                        "0" * 64,
                        "--approve",
                        "0" * 64,
                        "--backend",
                        "fake",
                    ]
                )
        self.assertEqual(code, 2)
        self.assertIn("no stored packet", stderr.getvalue())

    def test_malformed_packet_id_reports_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = cli.main(
                    ["--store", str(pathlib.Path(tmp) / "s"), "inspect", "../x"]
                )
        self.assertEqual(code, 2)


class CliPilotCommandsTest(unittest.TestCase):
    def _main(self, *argv: str) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = cli.main(["--store", str(pathlib.Path(tmp) / "s"), *argv])
        return code, stderr.getvalue()

    def test_unknown_prompt_version_rejected(self) -> None:
        code, err = self._main(
            "run",
            "--packet",
            "0" * 64,
            "--approve",
            "0" * 64,
            "--backend",
            "fake",
            "--prompt-version",
            "briefing_v9",
        )
        self.assertEqual(code, 2)
        self.assertIn("briefing_v1", err)

    def test_task_requires_matching_repo_flag(self) -> None:
        code, err = self._main("task", "T11", "--lrh-repo", ".")
        self.assertEqual(code, 2)
        self.assertIn("--lcats-repo", err)

    def test_b0_missing_briefing_file_reports_error(self) -> None:
        code, err = self._main(
            "b0",
            "--packet",
            "0" * 64,
            "--briefing-file",
            "/nonexistent/b0.md",
            "--minutes",
            "1",
        )
        self.assertEqual(code, 2)
        self.assertIn("error:", err)

    def test_unknown_task_rejected(self) -> None:
        code, err = self._main("task", "T99", "--lrh-repo", ".")
        self.assertEqual(code, 2)
        self.assertIn("unknown task", err)


if __name__ == "__main__":
    unittest.main()
