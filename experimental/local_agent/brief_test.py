import contextlib
import io
import json
import pathlib
import tempfile
import unittest

from local_agent import ask, brief, cli, model, recorder, settings, testing_support


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _line(prompt_ready: bool, execution_ready: bool) -> str:
    return (
        f"READINESS: prompt_ready={_yes_no(prompt_ready)} "
        f"execution_ready={_yes_no(execution_ready)}"
    )


class BriefTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self._tmp.name)
        self.repo = base / "repo"
        self.repo.mkdir()
        testing_support.make_repo(self.repo)
        self.store_dir = base / "store"
        self.store = recorder.Store(
            self.store_dir, clock=testing_support.SteppingClock()
        )
        self.ctx = brief.build_context(repo=self.repo, work_item="WI-T-1")
        expected = brief.expected_readiness(self.ctx)
        assert expected is not None
        self.expected = expected
        self.agreeing = _line(expected["prompt_ready"], expected["execution_ready"])
        self.contradicting = _line(
            expected["prompt_ready"], not expected["execution_ready"]
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _brief(self, answer: str) -> dict:
        adapter = model.FakeModel(
            [model.ModelResponse(answer, "stop", 10, 5, {"client_elapsed_seconds": 1})]
        )
        run_id = brief.run_brief(
            store=self.store,
            work_item="WI-T-1",
            ctx=self.ctx,
            adapter=adapter,
            budgets=settings.Budgets(),
        )
        self.adapter = adapter
        return self.store.load_run(run_id)


class ReadinessCheckTest(BriefTestBase):
    def test_expected_readiness_comes_from_lrh_diagnostics(self) -> None:
        diagnostics = self.ctx.diagnostics or {}
        self.assertEqual(
            self.expected,
            {
                "prompt_ready": diagnostics["prompt_readiness"]["prompt_ready"],
                "execution_ready": diagnostics["execution_readiness"][
                    "execution_ready"
                ],
            },
        )

    def test_statuses(self) -> None:
        cases = {
            "agrees": f"## Summary\nok\n\n{self.agreeing}\n",
            "contradicts": f"## Summary\nok\n\n{self.contradicting}\n",
            "missing": "## Summary\nno readiness line\n",
        }
        for status, text in cases.items():
            with self.subTest(status):
                check = brief.readiness_check(text, self.ctx)["readiness_check"]
                self.assertEqual(check["status"], status)

    def test_any_disagreeing_line_contradicts(self) -> None:
        text = f"{self.agreeing}\n{self.contradicting}\n"
        check = brief.readiness_check(text, self.ctx)["readiness_check"]
        self.assertEqual(check["status"], "contradicts")
        self.assertEqual(check["mismatches"], ["execution_ready"])

    def test_line_is_matched_case_insensitively_but_strictly(self) -> None:
        loose = self.agreeing.lower().replace("readiness:", "Readiness:")
        check = brief.readiness_check(loose, self.ctx)["readiness_check"]
        self.assertEqual(check["status"], "agrees")
        garbled = self.agreeing.replace("yes", "maybe").replace("no", "maybe")
        check = brief.readiness_check(garbled, self.ctx)["readiness_check"]
        self.assertEqual(check["status"], "missing")

    def test_light_markdown_around_the_line_is_accepted(self) -> None:
        wrappers = (
            "**{}**",
            "`{}`",
            "- {}",
            "> {}",
            "{}.",
            "### {}",
        )
        for wrapper in wrappers:
            with self.subTest(wrapper):
                text = "## Summary\nok\n\n" + wrapper.format(self.agreeing)
                check = brief.readiness_check(text, self.ctx)["readiness_check"]
                self.assertEqual(check["status"], "agrees")

    def test_repeated_agreeing_lines_are_duplicated(self) -> None:
        text = f"## Summary\n{self.agreeing}\n\n{self.agreeing}\n"
        check = brief.readiness_check(text, self.ctx)["readiness_check"]
        self.assertEqual(check["status"], "duplicated")

    def test_agreeing_line_not_at_the_end_is_misplaced(self) -> None:
        text = f"{self.agreeing}\n\n## Summary\nmore text after it\n"
        check = brief.readiness_check(text, self.ctx)["readiness_check"]
        self.assertEqual(check["status"], "misplaced")

    def test_without_diagnostics_the_check_is_unavailable(self) -> None:
        bare = ask.AskContext(
            mode=ask.MODE_WORK_ITEM,
            repo="r",
            source_commit="0" * 40,
            text="",
            source_refs=[],
            excluded=[],
        )
        check = brief.readiness_check(self.agreeing, bare)["readiness_check"]
        self.assertEqual(check["status"], "unavailable")


class RunBriefTest(BriefTestBase):
    def test_agreeing_brief_is_recorded_and_not_flagged(self) -> None:
        run = self._brief(f"## Summary\nok (S1:L1)\n\n{self.agreeing}\n")
        self.assertEqual(run["kind"], "brief")
        self.assertEqual(run["work_item_id"], "WI-T-1")
        self.assertEqual(run["prompt_version"], "brief_v2")
        self.assertEqual(run["readiness_check"]["status"], "agrees")
        prompt = self.adapter.requests[0].prompt
        self.assertIn("Do not write a readiness section", prompt)
        self.assertIn("[diagnostics]", prompt)
        self.assertIn("readiness agrees", ask.footer(self.store, run["run_id"]))
        self.assertIn("flagged runs: 0", ask.summarize(self.store))

    def test_contradicting_or_missing_brief_is_flagged(self) -> None:
        self._brief(f"## Summary\nok\n\n{self.contradicting}\n")
        self._brief("## Summary\nno readiness line\n")
        summary = ask.summarize(self.store)
        self.assertIn("runs: 2 (brief 2)", summary)
        self.assertIn("flagged runs: 2", summary)

    def test_readiness_block_is_written_by_the_tool(self) -> None:
        block = brief.readiness_block(self.ctx)
        self.assertTrue(block.startswith("## Readiness (from LRH diagnostics)"))
        self.assertIn(
            f"- prompt_ready: {_yes_no(self.expected['prompt_ready'])}", block
        )
        self.assertIn(
            f"- execution_ready: {_yes_no(self.expected['execution_ready'])}", block
        )
        self.assertIn("EXECUTION_READINESS_NOT_READY", block)
        # The block never looks like the model's checked line.
        check = brief.readiness_check(block, self.ctx)["readiness_check"]
        self.assertEqual(check["status"], "missing")

    def test_block_is_streamed_first_and_stored_before_the_answer(self) -> None:
        streamed: list[str] = []
        adapter = model.FakeModel(
            [
                model.ModelResponse(
                    f"## Summary\nok\n\n{self.agreeing}\n", "stop", 1, 1, {}
                )
            ]
        )
        run_id = brief.run_brief(
            store=self.store,
            work_item="WI-T-1",
            ctx=self.ctx,
            adapter=adapter,
            budgets=settings.Budgets(),
            on_text=streamed.append,
        )
        block = brief.readiness_block(self.ctx)
        self.assertEqual(streamed[0], block)
        answer = self.store.read_json(run_id, "output.json")["answer"]
        self.assertTrue(answer.startswith("## Summary"))
        output = self.store.read_json(run_id, "output.json")
        self.assertEqual(output["preamble"], block)
        self.assertNotIn("Readiness (from LRH", answer)
        self.assertTrue(answer.endswith(self.agreeing + "\n"))
        run = self.store.load_run(run_id)
        self.assertEqual(run["readiness_check"]["status"], "agrees")

    def test_misplaced_brief_is_flagged(self) -> None:
        self._brief(f"{self.agreeing}\n## Summary\nafter\n")
        self.assertIn("flagged runs: 1", ask.summarize(self.store))

    def test_inspect_shows_the_readiness_check(self) -> None:
        from local_agent import export

        run = self._brief(f"## Summary\nok\n\n{self.agreeing}\n")
        summary = export.inspect_run(self.store, run["run_id"])
        self.assertIn("run " + run["run_id"] + " (brief)", summary)
        self.assertIn('"status": "agrees"', summary)

    def test_block_values_cannot_add_lines(self) -> None:
        tricky = ask.AskContext(
            mode=ask.MODE_WORK_ITEM,
            repo="r",
            source_commit="0" * 40,
            text="",
            source_refs=[],
            excluded=[],
            diagnostics={
                "prompt_readiness": {
                    "prompt_ready": False,
                    "blocking_reasons": ["missing\n- prompt_ready: yes"],
                },
                "execution_readiness": {"execution_ready": False, "issues": []},
            },
        )
        block = brief.readiness_block(tricky)
        self.assertNotIn("\n- prompt_ready: yes", block)
        self.assertIn("- blocking: missing - prompt_ready: yes", block)

    def test_empty_answer_keeps_preamble_apart(self) -> None:
        run = self._brief("")
        output = self.store.read_json(run["run_id"], "output.json")
        self.assertEqual(output["answer"], "")
        self.assertTrue(output["preamble"].startswith("## Readiness"))

    def test_brief_prompt_puts_the_request_after_the_sources(self) -> None:
        self._brief(f"## Summary\nok\n\n{self.agreeing}\n")
        prompt = self.adapter.requests[0].prompt
        self.assertLess(prompt.index("Sources:"), prompt.index("Brief the owner"))

    def test_empty_answer_has_no_readiness_check(self) -> None:
        run = self._brief("")
        self.assertEqual(run["outcome"], "invalid_model_output")
        self.assertNotIn("readiness_check", run)


class BriefCliTest(BriefTestBase):
    def _main(self, *argv: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = cli.main(["--store", str(self.store_dir), *argv])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_brief_command_runs_and_logs_as_brief(self) -> None:
        answer = pathlib.Path(self._tmp.name) / "answer.md"
        answer.write_text(f"## Summary\nok\n\n{self.agreeing}\n", encoding="utf-8")
        code, out, err = self._main(
            "brief",
            "WI-T-1",
            "--repo",
            str(self.repo),
            "--backend",
            "fake",
            "--fake-response",
            str(answer),
            "--yes",
        )
        self.assertEqual(code, 0, err)
        self.assertIn(self.agreeing, out)
        self.assertTrue(out.startswith("## Readiness (from LRH diagnostics)"))
        self.assertIn("readiness agrees", err)
        store = recorder.Store(self.store_dir)
        (run_id,) = store.list_runs()
        self.assertEqual(store.load_run(run_id)["kind"], "brief")

    def test_unknown_work_item_is_logged_as_a_brief_failure(self) -> None:
        code, _, _ = self._main(
            "brief", "WI-NOPE", "--repo", str(self.repo), "--backend", "fake", "--yes"
        )
        self.assertEqual(code, 2)
        store = recorder.Store(self.store_dir)
        (run_id,) = store.list_runs()
        run = store.load_run(run_id)
        self.assertEqual((run["kind"], run["work_item_id"]), ("brief", "WI-NOPE"))
        self.assertEqual(run["prompt_version"], "brief_v2")
        self.assertEqual(run["outcome"], "missing_prerequisite")

    def test_brief_has_no_allow_flagged_option(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                cli.main(
                    [
                        "--store",
                        str(self.store_dir),
                        "brief",
                        "WI-T-1",
                        "--allow-flagged",
                        "x.py=secret",
                    ]
                )

    def _export(self, run_id: str, **kwargs: object) -> dict:
        from local_agent import export

        path = export.export_run(
            self.store,
            run_id,
            pathlib.Path(self._tmp.name) / "out",
            home=self._tmp.name,
            **kwargs,
        )
        return json.loads(path.read_text(encoding="utf-8"))

    def test_brief_exports_like_an_ask_run(self) -> None:
        from local_agent import export

        run = self._brief(f"## Summary\nBRIEF BODY\n\n{self.agreeing}\n")
        ask.record_rating(self.store, run["run_id"], "g", "PRIVATE NOTE")
        default = json.dumps(self._export(run["run_id"]))
        for private in ("PRIVATE NOTE", "BRIEF BODY", "Brief the owner"):
            self.assertNotIn(private, default)
        self.assertIn('"status": "agrees"', default)
        full = self._export(run["run_id"], include_output=True)
        self.assertIn("BRIEF BODY", full["answer"])
        self.assertEqual(full["run"]["rating"]["note"], "PRIVATE NOTE")
        with self.assertRaisesRegex(export.ExportError, "rated runs"):
            unrated = self._brief(f"## Summary\nok\n\n{self.agreeing}\n")
            self._export(unrated["run_id"], include_output=True)


if __name__ == "__main__":
    unittest.main()
