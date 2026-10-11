import contextlib
import io
import pathlib
import tempfile
import unittest
from unittest import mock

from local_agent import cli, export, recorder, testing_support


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

    def test_evaluate_rejects_malformed_scores_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_json = pathlib.Path(tmp) / "bad.json"
            bad_json.write_text("{not json", encoding="utf-8")
            not_object = pathlib.Path(tmp) / "list.json"
            not_object.write_text("[1, 2]", encoding="utf-8")
            for path in (bad_json, not_object):
                code, err = self._main("evaluate", "run-x", "--scores", str(path))
                with self.subTest(path.name):
                    self.assertEqual(code, 2)
                    self.assertIn("error:", err)

    def test_unknown_task_rejected(self) -> None:
        code, err = self._main("task", "T99", "--lrh-repo", ".")
        self.assertEqual(code, 2)
        self.assertIn("unknown task", err)


class CliAskTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self._tmp.name)
        self.repo = base / "repo"
        self.repo.mkdir()
        testing_support.make_repo(self.repo)
        self.store = base / "store"
        self.answer = base / "answer.md"
        self.answer.write_text("It is a demo (S1:L1).", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _main(self, *argv: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = cli.main(["--store", str(self.store), *argv])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_ask_rate_log_delete_prune(self) -> None:
        code, out, err = self._main(
            "ask",
            "What is the demo?",
            "--repo",
            str(self.repo),
            "--files",
            "project/design/demo.md",
            "--backend",
            "fake",
            "--fake-response",
            str(self.answer),
            "--yes",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("It is a demo (S1:L1).", out)
        self.assertIn("S1 project/design/demo.md", err)
        run_id = recorder.Store(self.store).list_runs()[0]
        self.assertIn(run_id, err)

        self.assertEqual(self._main("rate", run_id, "good")[0], 0)
        code, out, _ = self._main("log")
        self.assertEqual(code, 0)
        self.assertIn("good 1", out)

        code, out, _ = self._main("prune", "--before", "2000-01-01", "--dry-run")
        self.assertIn("would remove 0 run(s)", out)
        self.assertEqual(self._main("delete", run_id)[0], 0)
        self.assertEqual(recorder.Store(self.store).list_runs(), [])
        self.assertEqual(self._main("delete", run_id)[0], 2)

    def test_ask_failures_before_the_call_are_logged(self) -> None:
        cases = (
            (["--wi", "WI-NOPE", "--backend", "fake"], "missing_prerequisite"),
            (
                [
                    "--base-url",
                    "http://10.0.0.5:11434",
                    "--files",
                    "project/design/demo.md",
                ],
                "missing_prerequisite",
            ),
        )
        binary = self.answer.with_name("binary.bin")
        binary.write_bytes(b"\xff\xfe\x00bad")
        cases += (
            (
                ["--backend", "fake", "--fake-response", "/nonexistent/answer.md"],
                "missing_prerequisite",
            ),
            (
                ["--backend", "fake", "--fake-response", str(binary)],
                "missing_prerequisite",
            ),
        )
        seen: set[str] = set()
        for extra, outcome in cases:
            with self.subTest(extra[0]):
                code, _, err = self._main(
                    "ask", "q", "--repo", str(self.repo), *extra, "--yes"
                )
                self.assertEqual(code, 2, err)
                store = recorder.Store(self.store)
                new = set(store.list_runs()) - seen
                self.assertEqual(len(new), 1)
                seen |= new
                self.assertEqual(store.load_run(new.pop())["outcome"], outcome)

    def test_only_enter_or_yes_sends(self) -> None:
        for reply, sent in (("", True), ("yes", True), ("no", False), ("nah", False)):
            with self.subTest(reply=reply):
                before = set(recorder.Store(self.store).list_runs())
                with (
                    mock.patch.object(cli.sys.stdin, "isatty", return_value=True),
                    mock.patch("builtins.input", side_effect=[reply, ""]),
                ):
                    self._main(
                        "ask",
                        "q",
                        "--repo",
                        str(self.repo),
                        "--files",
                        "project/design/demo.md",
                        "--backend",
                        "fake",
                        "--fake-response",
                        str(self.answer),
                    )
                store = recorder.Store(self.store)
                (new,) = set(store.list_runs()) - before
                outcome = store.load_run(new)["outcome"]
                self.assertEqual(outcome == "completed", sent, outcome)

    def test_ask_with_every_file_excluded_is_refused_before_prompting(self) -> None:
        (self.repo / ".env").write_text("X=1\n", encoding="utf-8")
        testing_support.run_git(self.repo, "add", "-A")
        testing_support.run_git(self.repo, "commit", "-q", "-m", "env")
        with (
            mock.patch.object(cli.sys.stdin, "isatty", return_value=True),
            mock.patch("builtins.input", side_effect=AssertionError("must not prompt")),
        ):
            code, out, err = self._main(
                "ask",
                "q",
                "--repo",
                str(self.repo),
                "--files",
                ".env",
                "--backend",
                "fake",
                "--fake-response",
                str(self.answer),
            )
        self.assertEqual(code, 2, err)
        self.assertEqual(out, "")
        self.assertIn("sending 0 of 1", err)
        self.assertIn("NOT SENDING", err)
        store = recorder.Store(self.store)
        (run_id,) = store.list_runs()
        run = store.load_run(run_id)
        self.assertEqual(run["outcome"], "missing_prerequisite")
        self.assertIn(".env (excluded credential-like path", run["outcome_detail"])
        self.assertEqual(run["mode"], "files")
        self.assertEqual(len(run["source_commit"]), 40)
        self.assertEqual([e["path"] for e in run["excluded_sources"]], [".env"])
        self.assertEqual(run["sources"], [])
        summary = export.inspect_run(store, run_id)
        self.assertIn(f"source commit: {run['source_commit']}", summary)

    def _flagged_repo(self) -> str:
        name = "annotated.py"
        (self.repo / name).write_text(
            "token: Callable[[], str] = make_token\n", encoding="utf-8"
        )
        testing_support.run_git(self.repo, "add", "-A")
        testing_support.run_git(self.repo, "commit", "-q", "-m", "flagged")
        return name

    def _ask_flagged(self, name: str, *extra: str) -> tuple[int, str, str]:
        return self._main(
            "ask",
            "q",
            "--repo",
            str(self.repo),
            "--files",
            name,
            "--allow-flagged",
            f"{name}=secret",
            "--backend",
            "fake",
            "--fake-response",
            str(self.answer),
            *extra,
        )

    def _newest_outcome(self, before: set[str]) -> str:
        store = recorder.Store(self.store)
        (new,) = set(store.list_runs()) - before
        return str(store.load_run(new)["outcome"])

    def test_allow_flagged_needs_typed_yes_on_a_terminal(self) -> None:
        name = self._flagged_repo()
        cases = (
            ("--yes", True, [], 2, "missing_prerequisite"),
            ("no terminal", False, [], 2, "missing_prerequisite"),
            ("bare enter", True, [""], 1, "cancelled"),
            ("y is not yes", True, ["y"], 1, "cancelled"),
            ("typed yes", True, ["yes", ""], 0, "completed"),
        )
        for label, tty, replies, code, outcome in cases:
            with self.subTest(label):
                before = set(recorder.Store(self.store).list_runs())
                extra = ("--yes",) if label == "--yes" else ()
                real_adapter = cli._adapter
                adapter_calls: list[object] = []

                def tracking_adapter(args: object) -> object:
                    adapter_calls.append(args)
                    return real_adapter(args)

                with (
                    mock.patch.object(cli, "_confirm_terminal", return_value=tty),
                    mock.patch.object(cli, "_adapter", side_effect=tracking_adapter),
                    mock.patch("builtins.input", side_effect=replies),
                ):
                    got, out, err = self._ask_flagged(name, *extra)
                self.assertEqual(got, code, err)
                self.assertEqual(self._newest_outcome(before), outcome)
                self.assertEqual(bool(out.strip()), outcome == "completed")
                self.assertEqual(bool(adapter_calls), outcome == "completed")
                if replies:
                    listed_at = err.index("ALLOWED DESPITE secret")
                    self.assertLess(listed_at, err.index("type 'yes' to send"))

    def test_allow_flagged_rejects_a_malformed_value(self) -> None:
        code, _, err = self._main(
            "ask",
            "q",
            "--repo",
            str(self.repo),
            "--files",
            "x.py",
            "--allow-flagged",
            "x.py",
        )
        self.assertEqual(code, 2)
        self.assertIn("PATH=CATEGORY", err)

    def test_log_filters_and_rejects_a_bad_date(self) -> None:
        code, out, _ = self._main("log", "--kind", "brief")
        self.assertEqual(code, 0)
        self.assertIn("no runs", out)
        for bad in ("yesterday", "20261009", "2026-W41-1"):
            code, _, err = self._main("log", "--since", bad)
            self.assertEqual(code, 2, bad)
            self.assertIn("YYYY-MM-DD", err)

    def test_log_passes_the_filters_through(self) -> None:
        store = recorder.Store(self.store)
        store.start_run({"kind": "ask", "outcome": "completed"})
        store.start_run({"kind": "brief", "outcome": "completed"})
        store.start_run({"outcome": "completed"})
        code, out, _ = self._main("log", "--kind", "ask", "--kind", "brief")
        self.assertEqual(code, 0)
        self.assertIn("runs: 2", out)
        self.assertNotIn("pilot", out.split("\n")[0])
        code, out, _ = self._main("log", "--since", "2030-01-01")
        self.assertEqual(code, 0)
        self.assertIn("no runs match", out)

    def test_rate_and_prune_report_bad_input(self) -> None:
        self.assertEqual(self._main("rate", "nope", "g")[0], 2)
        code, _, err = self._main("prune", "--before", "yesterday")
        self.assertEqual(code, 2)
        self.assertIn("error:", err)


if __name__ == "__main__":
    unittest.main()
