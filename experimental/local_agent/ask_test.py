import json
import pathlib
import subprocess
import tempfile
import unittest

from local_agent import ask, model, recorder, settings, sources, testing_support

ANSWER = "The demo design is described in S1:L1-L3. See also S9."


def _response(text: str, **kwargs: object) -> model.ModelResponse:
    fields = {"done_reason": "stop", "prompt_tokens": 50, "output_tokens": 20}
    fields.update(kwargs)
    return model.ModelResponse(
        text,
        fields["done_reason"],
        fields["prompt_tokens"],
        fields["output_tokens"],
        {"client_elapsed_seconds": 1.5},
        thinking_chars=int(fields.get("thinking_chars", 0)),
    )


class AskTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self._tmp.name)
        self.repo = base / "repo"
        self.repo.mkdir()
        (self.repo / "README.md").write_text("# Fixture\n\nHello.\n", encoding="utf-8")
        (self.repo / ".env").write_text("TOKEN=abc\n", encoding="utf-8")
        (self.repo / "leaky.md").write_text(
            "config: api_key = sk-live-abcdef0123456789abcdef\n", encoding="utf-8"
        )
        (self.repo / "contact.md").write_text(
            "Ask ops@example.org; the server listens on 127.0.0.1.\n",
            encoding="utf-8",
        )
        leaky_item = testing_support.READY_ITEM.replace("WI-T-1", "WI-T-9").replace(
            "  - project/design/demo.md",
            "  - https://admin:hunter2secret@example.com/design.md",
        )
        item_path = self.repo / "project/work_items/proposed/WI-T-9.md"
        item_path.parent.mkdir(parents=True)
        item_path.write_text(leaky_item, encoding="utf-8")
        testing_support.make_repo(self.repo)
        self.store = recorder.Store(
            base / "store", clock=testing_support.SteppingClock()
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()


class BuildContextTest(AskTestBase):
    def test_files_mode_sends_tracked_files_with_line_numbers(self) -> None:
        ctx = ask.build_context(repo=self.repo, files=["project/design/demo.md"])
        self.assertEqual(ctx.mode, ask.MODE_FILES)
        self.assertEqual(
            [r["path"] for r in ctx.source_refs], ["project/design/demo.md"]
        )
        self.assertIn("[S1] project/design/demo.md", ctx.text)
        self.assertIn("L1: # Demo design", ctx.text)

    def test_credential_paths_and_flagged_text_are_excluded(self) -> None:
        ctx = ask.build_context(
            repo=self.repo, files=[".env", "leaky.md", "project/design/demo.md"]
        )
        excluded = {entry["path"]: entry["reason"] for entry in ctx.excluded}
        self.assertIn("credential-like", excluded[".env"])
        self.assertIn("sensitivity scan", excluded["leaky.md"])
        self.assertNotIn("TOKEN=abc", ctx.text)
        self.assertNotIn("sk-live", ctx.text)
        self.assertNotIn("sk-live", json.dumps(ctx.excluded))

    def test_medium_only_source_is_sent_with_category_warnings(self) -> None:
        ctx = ask.build_context(repo=self.repo, files=["contact.md"])
        self.assertEqual(ctx.excluded, [])
        self.assertIn("ops@example.org", ctx.text)
        ref = ctx.source_refs[0]
        self.assertEqual(list(ref["sensitivity_warnings"]), ["email", "ip_address"])
        summary = ask.source_summary(ctx)
        self.assertIn("WARN: email, ip_address", summary)
        self.assertNotIn("ops@example.org", summary)
        self.assertNotIn("127.0.0.1", summary)

    def test_run_record_names_categories_not_values(self) -> None:
        ctx = ask.build_context(repo=self.repo, files=["contact.md"])
        run_id = ask.run_ask(
            store=self.store,
            question="Who runs ops?",
            ctx=ctx,
            adapter=model.FakeModel([_response("See S1:L1.")]),
            budgets=settings.Budgets(),
        )
        run_json = json.dumps(self.store.load_run(run_id))
        self.assertIn("ip_address", run_json)
        self.assertNotIn("ops@example.org", run_json)
        self.assertNotIn("127.0.0.1", run_json)

    def test_private_and_untracked_paths_are_excluded(self) -> None:
        (self.repo / "untracked.md").write_text("new\n", encoding="utf-8")
        ctx = ask.build_context(
            repo=self.repo,
            files=["project/executions/AD_HOC/private.md", "untracked.md"],
        )
        self.assertEqual(ctx.source_refs, [])
        self.assertEqual(len(ctx.excluded), 2)

    def test_overview_mode_sends_readme_and_filtered_listing(self) -> None:
        ctx = ask.build_context(repo=self.repo)
        self.assertEqual(ctx.mode, ask.MODE_OVERVIEW)
        self.assertEqual(ctx.source_refs[0]["path"], "README.md")
        self.assertIn("project/design/demo.md", ctx.text)
        self.assertNotIn(".env\n", ctx.text)
        self.assertNotIn("project/executions/", ctx.text)

    def test_work_item_mode_carries_diagnostics(self) -> None:
        ctx = ask.build_context(repo=self.repo, work_item="WI-T-1")
        self.assertEqual(ctx.mode, ask.MODE_WORK_ITEM)
        self.assertIsNotNone(ctx.diagnostics)
        self.assertIn("EXECUTION_READINESS_NOT_READY", ctx.text)

    def test_high_severity_diagnostics_refuse_the_request(self) -> None:
        with self.assertRaises(sources.SourceError) as caught:
            ask.build_context(repo=self.repo, work_item="WI-T-9")
        message = str(caught.exception)
        self.assertIn("url_credentials", message)
        self.assertNotIn("hunter2secret", message)

    def test_nested_private_paths_are_excluded_and_unlisted(self) -> None:
        nested = self.repo / "sub/project/executions/AD_HOC/private.md"
        nested.parent.mkdir(parents=True)
        nested.write_text("nested private notes\n", encoding="utf-8")
        testing_support.run_git(self.repo, "add", "-A")
        testing_support.run_git(self.repo, "commit", "-q", "-m", "nested")
        ctx = ask.build_context(
            repo=self.repo, files=["sub/project/executions/AD_HOC/private.md"]
        )
        self.assertEqual(ctx.source_refs, [])
        self.assertIn("private path", ctx.excluded[0]["reason"])
        overview = ask.build_context(repo=self.repo)
        self.assertNotIn("sub/project/executions", overview.text)

    def test_medium_findings_in_the_listing_are_warned(self) -> None:
        named = self.repo / "notes/ops@example.org.md"
        named.parent.mkdir(parents=True)
        named.write_text("plain\n", encoding="utf-8")
        testing_support.run_git(self.repo, "add", "-A")
        testing_support.run_git(self.repo, "commit", "-q", "-m", "named")
        ctx = ask.build_context(repo=self.repo)
        self.assertIn("email", ctx.context_warnings)
        summary = ask.source_summary(ctx)
        self.assertIn("context WARN: email", summary)
        self.assertNotIn("ops@example.org", summary)

    def test_uncommitted_edits_are_not_sent(self) -> None:
        (self.repo / "project/design/demo.md").write_text("DIRTY\n", encoding="utf-8")
        ctx = ask.build_context(repo=self.repo, files=["project/design/demo.md"])
        self.assertNotIn("DIRTY", ctx.text)

    def test_all_excluded_files_are_not_sendable(self) -> None:
        ctx = ask.build_context(repo=self.repo, files=[".env", "leaky.md"])
        self.assertEqual(ctx.source_refs, [])
        self.assertIn("all requested sources were excluded", ask.unsendable_reason(ctx))
        summary = ask.source_summary(ctx)
        self.assertIn("sending 0 of 2", summary)
        self.assertIn("NOT SENDING", summary)

    def test_run_ask_refuses_without_sources_and_makes_no_call(self) -> None:
        ctx = ask.build_context(repo=self.repo, files=[".env"])
        adapter = model.FakeModel([_response(ANSWER)])
        run_id = ask.run_ask(
            store=self.store,
            question="q",
            ctx=ctx,
            adapter=adapter,
            budgets=settings.Budgets(),
        )
        run = self.store.load_run(run_id)
        self.assertEqual(run["outcome"], "missing_prerequisite")
        self.assertEqual(adapter.requests, [])

    def test_file_with_nothing_within_budget_is_excluded(self) -> None:
        (self.repo / "big.txt").write_text("x" * 200 + "\n", encoding="utf-8")
        testing_support.run_git(self.repo, "add", "-A")
        testing_support.run_git(self.repo, "commit", "-q", "-m", "big")
        ctx = ask.build_context(
            repo=self.repo,
            files=["big.txt"],
            budgets=settings.Budgets(max_packet_bytes=50),
        )
        self.assertEqual(ctx.source_refs, [])
        self.assertEqual(ctx.excluded, [{"path": "big.txt", "reason": "budget"}])
        self.assertIsNotNone(ask.unsendable_reason(ctx))

    def test_duplicate_files_are_sent_once(self) -> None:
        ctx = ask.build_context(
            repo=self.repo,
            files=["project/design/demo.md", "project/design/demo.md"],
        )
        self.assertEqual(len(ctx.source_refs), 1)
        self.assertIn("sending 1 of 1", ask.source_summary(ctx))

    def test_work_item_mode_needs_the_work_item_itself(self) -> None:
        ctx = ask.AskContext(
            mode=ask.MODE_WORK_ITEM,
            repo=str(self.repo),
            source_commit="0" * 40,
            text="",
            source_refs=[{"source_id": "S1", "relation": "Design"}],
            excluded=[{"path": "project/work_items/x.md", "reason": "secret"}],
        )
        self.assertIn("work item itself", ask.unsendable_reason(ctx))
        ok = ask.build_context(repo=self.repo, work_item="WI-T-1")
        self.assertIsNone(ask.unsendable_reason(ok))

    def test_overview_is_sendable_and_counts_sources(self) -> None:
        ctx = ask.build_context(repo=self.repo)
        self.assertIsNone(ask.unsendable_reason(ctx))
        self.assertIn("sending 1 of 1 + tracked-file listing", ask.source_summary(ctx))

    def test_source_summary_lists_sources_and_exclusions(self) -> None:
        ctx = ask.build_context(
            repo=self.repo, files=["project/design/demo.md", ".env"]
        )
        summary = ask.source_summary(ctx)
        self.assertIn("S1 project/design/demo.md", summary)
        self.assertIn("excluded .env", summary)


class _StreamThenFail:
    """Streams one chunk, then fails like a mid-answer timeout."""

    def __init__(self, error: BaseException) -> None:
        self.error = error

    def describe(self) -> dict[str, object]:
        return {"backend": "fake"}

    def preflight(self) -> dict[str, object]:
        return {}

    def generate(self, request: model.ModelRequest) -> model.ModelResponse:
        assert request.on_text is not None
        request.on_text("half an ans")
        raise self.error


class AllowFlaggedTest(AskTestBase):
    """The owner's --allow-flagged override (proposal Decision 3)."""

    ANNOTATED = "annotated.py"

    def setUp(self) -> None:
        super().setUp()
        files = {
            self.ANNOTATED: "def f(\n    token: Callable[[], str] = make_token,\n):\n"
            "    if secret:\n        keep(secret)\n",
            "mixed.py": 'api_key = "sk-live-abcdef0123456789abcdef"\n',
            "notes/token=abcd1234efgh.py": "token: Callable[[], str] = x\n",
            "plain.py": "print('hello')\n",
        }
        for name, text in files.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        testing_support.run_git(self.repo, "add", "-A")
        testing_support.run_git(self.repo, "commit", "-q", "-m", "flagged")

    def _build(self, files: list[str], allow: dict[str, set[str]]) -> ask.AskContext:
        return ask.build_context(
            repo=self.repo,
            files=files,
            allow_flagged={path: frozenset(cats) for path, cats in allow.items()},
        )

    def test_without_override_the_file_is_excluded(self) -> None:
        ctx = ask.build_context(repo=self.repo, files=[self.ANNOTATED])
        self.assertEqual(ctx.source_refs, [])
        self.assertIn("sensitivity scan (secret)", ctx.excluded[0]["reason"])

    def test_allowed_file_is_sent_with_each_finding_listed(self) -> None:
        ctx = self._build([self.ANNOTATED], {self.ANNOTATED: {"secret"}})
        self.assertIn("token: Callable", ctx.text)
        self.assertEqual(
            [(f["start_line"], f["end_line"]) for f in ctx.allowed_flagged],
            [(2, 2), (4, 5)],
        )
        summary = ask.source_summary(ctx)
        self.assertIn(
            "ALLOWED DESPITE secret: secret.keyword_assignment at L2", summary
        )
        self.assertIn("at L4-L5", summary)
        self.assertNotIn("make_token", summary)
        # The final scan skips the body but keeps the header.
        self.assertNotIn("token: Callable", ctx.scan_text)
        self.assertIn(f"### [S1] {self.ANNOTATED}", ctx.scan_text)

    def test_other_files_are_still_fully_scanned(self) -> None:
        ctx = self._build([self.ANNOTATED, "plain.py"], {self.ANNOTATED: {"secret"}})
        self.assertIn("print('hello')", ctx.scan_text)
        self.assertIn("secret", ctx.context_warnings)

    def test_findings_beyond_the_budget_are_not_listed(self) -> None:
        ctx = ask.build_context(
            repo=self.repo,
            files=[self.ANNOTATED],
            allow_flagged={self.ANNOTATED: frozenset({"secret"})},
            budgets=settings.Budgets(max_packet_bytes=60),
        )
        self.assertEqual([f["start_line"] for f in ctx.allowed_flagged], [2])

    def test_override_never_degrades_into_an_exclusion(self) -> None:
        private = "project/executions/AD_HOC/private.md"
        (self.repo / "untracked.py").write_text("token: Callable[[], str] = x\n")
        cases = {
            "extra category": (
                [self.ANNOTATED],
                {self.ANNOTATED: {"secret", "token"}},
            ),
            "untracked": (["untracked.py"], {"untracked.py": {"secret"}}),
            "private path": ([private], {private: {"secret"}}),
        }
        for label, (files, allow) in cases.items():
            with self.subTest(label):
                with self.assertRaisesRegex(sources.SourceError, "--allow-flagged"):
                    self._build(files, allow)
        with self.assertRaisesRegex(sources.SourceError, "budget"):
            ask.build_context(
                repo=self.repo,
                files=["plain.py", self.ANNOTATED],
                allow_flagged={self.ANNOTATED: frozenset({"secret"})},
                budgets=settings.Budgets(max_packet_bytes=16),
            )

    def test_duplicate_override_entries_merge(self) -> None:
        ctx = ask.build_context(
            repo=self.repo,
            files=["mixed.py"],
            allow_flagged={
                "mixed.py": frozenset({"secret"}),
                "./mixed.py": frozenset({"token"}),
            },
        )
        self.assertEqual(
            {f["category"] for f in ctx.allowed_flagged}, {"secret", "token"}
        )

    def test_override_refused_when_budget_cuts_every_flagged_line(self) -> None:
        late = "late.py"
        (self.repo / late).write_text(
            "x = 1\n" * 20 + "token: Callable[[], str] = make_token\n",
            encoding="utf-8",
        )
        testing_support.run_git(self.repo, "add", "-A")
        testing_support.run_git(self.repo, "commit", "-q", "-m", "late")
        with self.assertRaisesRegex(sources.SourceError, "nothing to confirm"):
            ask.build_context(
                repo=self.repo,
                files=[late],
                allow_flagged={late: frozenset({"secret"})},
                budgets=settings.Budgets(max_packet_bytes=30),
            )

    def test_newline_in_a_requested_path_is_refused(self) -> None:
        odd = "safe\ntoken: abcdef123.py"
        try:
            (self.repo / odd).write_text("token: Callable[[], str] = x\n")
        except OSError:
            self.skipTest("filesystem rejects newlines in names")
        testing_support.run_git(self.repo, "add", "-A")
        testing_support.run_git(self.repo, "commit", "-q", "-m", "odd")
        with self.assertRaisesRegex(
            sources.SourceError, "control or invisible"
        ) as caught:
            self._build([odd], {odd: {"secret"}})
        # The refusal quotes the path rather than printing a raw newline.
        self.assertNotIn("\n", str(caught.exception))
        self.assertIn("\\n", str(caught.exception))
        # Without the override, the excluded path is quoted in the prompt and
        # summary too, so it cannot forge a line in either.
        plain = ask.build_context(repo=self.repo, files=[odd, "plain.py"])
        for shown in (plain.text, ask.source_summary(plain)):
            self.assertNotIn("\ntoken: abcdef123", shown)
            self.assertIn("safe\\ntoken", shown)
        # The listing returns the real, unquoted name, which path checks reject.
        commit = sources.resolve_commit(self.repo, "HEAD")
        self.assertIn(odd, sources.list_tracked_files(self.repo, commit))

    def test_context_warning_label_covers_any_severity(self) -> None:
        ctx = self._build([self.ANNOTATED], {self.ANNOTATED: {"secret"}})
        self.assertIn(
            "context WARN: secret (sensitivity categories anywhere",
            ask.source_summary(ctx),
        )

    def test_another_high_category_is_refused(self) -> None:
        with self.assertRaisesRegex(
            sources.SourceError, r"cannot send mixed.py.*token"
        ):
            self._build(["mixed.py"], {"mixed.py": {"secret"}})

    def test_override_refusals(self) -> None:
        cases = {
            "not requested": ([self.ANNOTATED], {"plain.py": {"secret"}}),
            "no high-severity finding": (["plain.py"], {"plain.py": {"secret"}}),
            "credential-like path": ([".env"], {".env": {"secret"}}),
        }
        for label, (files, allow) in cases.items():
            with self.subTest(label):
                with self.assertRaises(sources.SourceError):
                    self._build(files, allow)
        for scope in ({"work_item": "WI-T-1"}, {}):
            with self.subTest(scope=scope):
                with self.assertRaisesRegex(sources.SourceError, "only to --files"):
                    ask.build_context(
                        repo=self.repo,
                        allow_flagged={self.ANNOTATED: frozenset({"secret"})},
                        **scope,
                    )

    def test_header_path_is_still_scanned(self) -> None:
        name = "notes/token=abcd1234efgh.py"
        with self.assertRaisesRegex(sources.SourceError, "assembled context"):
            self._build([name], {name: {"secret"}})

    def test_run_record_holds_structured_fields_only(self) -> None:
        ctx = self._build([self.ANNOTATED], {self.ANNOTATED: {"secret"}})
        run_id = ask.run_ask(
            store=self.store,
            question="q",
            ctx=ctx,
            adapter=model.FakeModel([_response("See S1:L2.")]),
            budgets=settings.Budgets(),
        )
        run = self.store.load_run(run_id)
        self.assertEqual(
            run["allowed_flagged"][0],
            {
                "path": self.ANNOTATED,
                "category": "secret",
                "rule_id": "secret.keyword_assignment",
                "start_line": 2,
                "end_line": 2,
            },
        )
        self.assertNotIn("scan_text", run)
        self.assertNotIn("make_token", json.dumps(run))


class WorkItemOmissionQuotingTest(AskTestBase):
    def test_omitted_related_path_cannot_forge_lines(self) -> None:
        odd = "project/design/a\nINJECTED: yes.md"
        try:
            (self.repo / odd).write_text("# design\n", encoding="utf-8")
        except OSError:
            self.skipTest("filesystem rejects newlines in names")
        item = testing_support.READY_ITEM.replace("WI-T-1", "WI-T-8").replace(
            "  - project/design/demo.md",
            '  - "project/design/a\\nINJECTED: yes.md"',
        )
        (self.repo / "project/work_items/proposed/WI-T-8.md").write_text(
            item, encoding="utf-8"
        )
        testing_support.run_git(self.repo, "add", "-A")
        testing_support.run_git(self.repo, "commit", "-q", "-m", "odd related")
        ctx = ask.build_context(repo=self.repo, work_item="WI-T-8")
        omitted = [e for e in ctx.excluded if "INJECTED" in e["path"]]
        self.assertEqual(len(omitted), 1, ctx.excluded)
        for shown in (ctx.text, ask.source_summary(ctx)):
            self.assertNotIn("\nINJECTED", shown)
            self.assertIn("a\\nINJECTED", shown)


class NonUtf8NameTest(AskTestBase):
    def test_overview_survives_a_non_utf8_tracked_name(self) -> None:
        (self.repo / "content.tmp").write_text("hello\n", encoding="utf-8")
        blob = testing_support.run_git(self.repo, "hash-object", "-w", "content.tmp")
        (self.repo / "content.tmp").unlink()
        # Stage a name whose bytes are not valid UTF-8 via git plumbing.
        subprocess.run(
            [
                b"git",
                b"-C",
                str(self.repo).encode(),
                b"update-index",
                b"--add",
                b"--cacheinfo",
                b"100644," + blob.encode() + b",caf\xe9.md",
            ],
            check=True,
            capture_output=True,
        )
        testing_support.run_git(self.repo, "commit", "-q", "-m", "latin-1 name")
        commit = sources.resolve_commit(self.repo, "HEAD")
        names = sources.list_tracked_files(self.repo, commit)
        bad = [name for name in names if name.startswith("caf")]
        self.assertEqual(len(bad), 1)
        with self.assertRaisesRegex(sources.SourceError, "not valid UTF-8"):
            sources.check_path_allowed(bad[0])
        ctx = ask.build_context(repo=self.repo)
        self.assertNotIn("caf", ctx.text)


class RunAskTest(AskTestBase):
    def _ask(self, adapter: model.ModelAdapter, **kwargs: object) -> dict:
        ctx = ask.build_context(repo=self.repo, files=["project/design/demo.md"])
        chunks: list[str] = []
        run_id = ask.run_ask(
            store=self.store,
            question="What does the demo design say?",
            ctx=ctx,
            adapter=adapter,
            budgets=kwargs.pop("budgets", settings.Budgets()),
            on_text=chunks.append,
        )
        self.chunks = chunks
        return self.store.load_run(run_id)

    def test_completed_run_streams_and_is_logged(self) -> None:
        adapter = model.FakeModel([_response(ANSWER)])
        run = self._ask(adapter)
        self.assertEqual(run["outcome"], "completed")
        self.assertEqual("".join(self.chunks), ANSWER)
        self.assertEqual(run["kind"], "ask")
        self.assertEqual(run["citations"]["citations_total"], 2)
        self.assertEqual(run["citations"]["unresolved_citations"], ["S9"])
        output = self.store.read_json(run["run_id"], "output.json")
        self.assertEqual(output["answer"], ANSWER)
        request = adapter.requests[0]
        self.assertIsNone(request.output_schema)
        self.assertIn("What does the demo design say?", request.prompt)

    def test_empty_answer_reports_hidden_reasoning(self) -> None:
        run = self._ask(model.FakeModel([_response("", thinking_chars=5000)]))
        self.assertEqual(run["outcome"], "invalid_model_output")
        self.assertIn("hidden reasoning", run["outcome_detail"])

    def test_output_limit_keeps_partial_answer(self) -> None:
        run = self._ask(model.FakeModel([_response("partial", done_reason="length")]))
        self.assertEqual(run["outcome"], "budget_exhausted")
        output = self.store.read_json(run["run_id"], "output.json")
        self.assertEqual(output["answer"], "partial")

    def test_backend_failures_are_recorded(self) -> None:
        cases = (
            (model.KIND_TIMEOUT, "timeout"),
            (model.KIND_MISSING_PREREQUISITE, "missing_prerequisite"),
            (model.KIND_BACKEND_ERROR, "backend_error"),
        )
        for kind, outcome in cases:
            with self.subTest(kind):
                run = self._ask(model.FakeModel([model.BackendError(kind, "x")]))
                self.assertEqual(run["outcome"], outcome)

    def test_input_budget_blocks_the_call(self) -> None:
        adapter = model.FakeModel([_response(ANSWER)])
        run = self._ask(
            adapter, budgets=settings.Budgets(max_estimated_input_tokens=10)
        )
        self.assertEqual(run["outcome"], "budget_exhausted")
        self.assertEqual(adapter.requests, [])

    def test_excluded_content_is_never_sent_or_logged(self) -> None:
        adapter = model.FakeModel([_response(ANSWER)])
        ctx = ask.build_context(
            repo=self.repo, files=[".env", "leaky.md", "project/design/demo.md"]
        )
        run_id = ask.run_ask(
            store=self.store,
            question="q",
            ctx=ctx,
            adapter=adapter,
            budgets=settings.Budgets(),
        )
        run_dir = self.store.run_dir(run_id)
        logged = "".join(path.read_text("utf-8") for path in run_dir.iterdir())
        for secret in ("TOKEN=abc", "sk-live"):
            self.assertNotIn(secret, adapter.requests[0].prompt)
            self.assertNotIn(secret, logged)

    def test_preflight_failure_makes_no_call(self) -> None:
        adapter = model.FakeModel(
            [_response(ANSWER)],
            preflight_error=model.BackendError(
                model.KIND_MISSING_PREREQUISITE, "model not pulled"
            ),
        )
        run = self._ask(adapter)
        self.assertEqual(run["outcome"], "missing_prerequisite")
        self.assertEqual(adapter.requests, [])

    def test_partial_streamed_answer_is_kept_on_failure(self) -> None:
        timeout = model.BackendError(model.KIND_TIMEOUT, "slow")
        run = self._ask(_StreamThenFail(timeout))
        self.assertEqual(run["outcome"], "timeout")
        output = self.store.read_json(run["run_id"], "output.json")
        self.assertEqual(output, {"answer": "half an ans", "partial": True})

    def test_placeholders_in_the_question_are_not_expanded(self) -> None:
        ctx = ask.build_context(repo=self.repo, files=["project/design/demo.md"])
        prompt = ask.render_prompt("What is {{CONTEXT}}?", ctx)
        self.assertIn("What is {{CONTEXT}}?", prompt)
        self.assertEqual(prompt.count("L1: # Demo design"), 1)

    def test_record_failure_logs_a_run_without_a_call(self) -> None:
        run_id = ask.record_failure(self.store, "q", "cancelled", "declined")
        run = self.store.load_run(run_id)
        self.assertEqual(run["outcome"], "cancelled")
        self.assertIn("cancelled 1", ask.summarize(self.store))

    def test_cancellation_is_recorded_then_reraised(self) -> None:
        with self.assertRaises(KeyboardInterrupt):
            self._ask(model.FakeModel([KeyboardInterrupt()]))
        run = self.store.load_run(self.store.list_runs()[0])
        self.assertEqual(run["outcome"], "cancelled")


class RatingAndLogTest(AskTestBase):
    def _completed(self, answer: str = ANSWER) -> str:
        ctx = ask.build_context(repo=self.repo, files=["project/design/demo.md"])
        return ask.run_ask(
            store=self.store,
            question="q",
            ctx=ctx,
            adapter=model.FakeModel([_response(answer)]),
            budgets=settings.Budgets(),
        )

    def test_rating_is_stored(self) -> None:
        run_id = self._completed()
        ask.record_rating(self.store, run_id, "g", "useful ")
        run = self.store.load_run(run_id)
        self.assertEqual(run["rating"], {"value": "good", "note": "useful"})
        with self.assertRaises(ValueError):
            ask.record_rating(self.store, run_id, "x")

    def test_summary_counts_outcomes_ratings_and_flags(self) -> None:
        good = self._completed("Clean answer citing S1:L1-L2.")
        self._completed()
        ask.record_rating(self.store, good, "g")
        summary = ask.summarize(self.store)
        self.assertIn("runs: 2", summary)
        self.assertIn("completed 2", summary)
        self.assertIn("good 1", summary)
        self.assertIn("unrated 1", summary)
        self.assertIn("flagged runs: 1", summary)
        self.assertIn("latency: median 1.5s", summary)

    def test_p90_uses_nearest_rank(self) -> None:
        for seconds in range(1, 11):
            run_id = self._completed()
            usage = self.store.load_run(run_id)["usage"]
            usage["backend_timings"] = {"client_elapsed_seconds": float(seconds)}
            self.store.update_run(run_id, usage=usage)
        self.assertIn("p90 9.0s", ask.summarize(self.store))

    def test_summary_without_runs(self) -> None:
        self.assertIn("no runs", ask.summarize(self.store))


if __name__ == "__main__":
    unittest.main()
