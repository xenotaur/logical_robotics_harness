import json
import pathlib
import tempfile
import unittest

from local_agent import context, model, recorder, runner, settings, testing_support

VALID_BRIEFING = {
    "summary": "Adds a small feature.",
    "readiness_statement": "Prompt-ready; not execution-ready; WI-T-0 is proposed.",
    "constraints": [{"text": "One module", "kind": "fact", "refs": ["S1:L22-L24"]}],
    "dependencies": [{"text": "WI-T-0 first", "kind": "fact", "refs": ["S2"]}],
    "evidence_gaps": [{"text": "No design detail", "kind": "suggestion", "refs": []}],
    "relevant_sources": [
        {"text": "Design", "kind": "fact", "refs": ["S9", "api_key=sk-secret"]}
    ],
    "open_questions": [{"text": "Which module?", "kind": "question", "refs": []}],
}


def _response(text: str, done_reason: str = "stop") -> model.ModelResponse:
    return model.ModelResponse(text, done_reason, 100, 20, {})


class RunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self._tmp.name)
        self.store = recorder.Store(
            base / "store", clock=testing_support.SteppingClock()
        )
        manifest = {
            "work_item_id": "WI-T-1",
            "source_commit": "c" * 40,
            "sources": [
                {"source_id": "S1", "line_start": 1, "line_end": 40},
                {"source_id": "S2", "line_start": 1, "line_end": 10},
            ],
        }
        self.sha = context.packet_sha256(manifest, "packet text\n")
        self.store.save_packet(self.sha, manifest, "packet text\n")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, adapter: model.ModelAdapter, **kwargs: object) -> dict:
        run_id = runner.run_briefing(
            store=self.store,
            packet_sha256=self.sha,
            approved_sha256=self.sha,
            adapter=adapter,
            budgets=kwargs.pop("budgets", settings.Budgets()),
            **kwargs,
        )
        return self.store.load_run(run_id)

    def test_completed_records_citations_and_output(self) -> None:
        run = self._run(model.FakeModel([_response(json.dumps(VALID_BRIEFING))]))
        self.assertEqual(run["outcome"], runner.OUTCOME_COMPLETED)
        self.assertIn("not human-accepted", run["outcome_detail"])
        self.assertEqual(run["citations"]["citations_total"], 4)
        self.assertEqual(run["citations"]["unresolved_citations"], ["S9"])
        self.assertEqual(run["citations"]["malformed_citations"], 1)
        self.assertNotIn("sk-secret", json.dumps(run))
        output = self.store.read_json(run["run_id"], "output.json")
        self.assertEqual(output["briefing"]["summary"], "Adds a small feature.")
        events, truncated = self.store.events(run["run_id"])
        self.assertFalse(truncated)
        self.assertEqual(events[-1]["type"], "outcome")
        self.assertEqual([e["seq"] for e in events], list(range(1, len(events) + 1)))

    def test_unapproved_packet_creates_no_run(self) -> None:
        with self.assertRaises(runner.ApprovalError):
            runner.run_briefing(
                store=self.store,
                packet_sha256=self.sha,
                approved_sha256="0" * 64,
                adapter=model.FakeModel([]),
                budgets=settings.Budgets(),
            )
        self.assertEqual(self.store.list_runs(), [])

    def test_tampered_stored_packet_is_refused(self) -> None:
        packet_file = self.store.packet_dir(self.sha) / "packet.md"
        packet_file.write_text("packet text\nINJECTED\n", encoding="utf-8")
        adapter = model.FakeModel([_response(json.dumps(VALID_BRIEFING))])
        with self.assertRaisesRegex(runner.ApprovalError, "no longer matches"):
            self._run(adapter)
        self.assertEqual(self.store.list_runs(), [])
        self.assertEqual(adapter.requests, [])

    def test_missing_prerequisite(self) -> None:
        adapter = model.FakeModel(
            [],
            preflight_error=model.BackendError(
                model.KIND_MISSING_PREREQUISITE, "service not running"
            ),
        )
        run = self._run(adapter)
        self.assertEqual(run["outcome"], runner.OUTCOME_MISSING_PREREQUISITE)

    def test_timeout(self) -> None:
        adapter = model.FakeModel([model.BackendError(model.KIND_TIMEOUT, "slow")])
        self.assertEqual(self._run(adapter)["outcome"], runner.OUTCOME_TIMEOUT)

    def test_malformed_json(self) -> None:
        run = self._run(model.FakeModel([_response("not json")]))
        self.assertEqual(run["outcome"], runner.OUTCOME_INVALID_OUTPUT)
        raw = self.store.read_json(run["run_id"], "output.json")
        self.assertEqual(raw["raw_text"], "not json")

    def test_schema_violation(self) -> None:
        broken = dict(VALID_BRIEFING, constraints=[{"text": "x", "kind": "rumor"}])
        run = self._run(model.FakeModel([_response(json.dumps(broken))]))
        self.assertEqual(run["outcome"], runner.OUTCOME_INVALID_OUTPUT)

    def test_output_token_limit_is_budget_exhausted(self) -> None:
        run = self._run(model.FakeModel([_response('{"summary": "cut', "length")]))
        self.assertEqual(run["outcome"], runner.OUTCOME_BUDGET_EXHAUSTED)

    def test_returned_output_tokens_over_budget(self) -> None:
        response = model.ModelResponse(
            json.dumps(VALID_BRIEFING), "stop", 100, 5000, {}
        )
        run = self._run(model.FakeModel([response]))
        self.assertEqual(run["outcome"], runner.OUTCOME_BUDGET_EXHAUSTED)
        self.assertIn("5000", run["outcome_detail"])

    def test_input_over_budget_never_calls_model(self) -> None:
        adapter = model.FakeModel([_response(json.dumps(VALID_BRIEFING))])
        run = self._run(adapter, budgets=settings.Budgets(max_estimated_input_tokens=5))
        self.assertEqual(run["outcome"], runner.OUTCOME_BUDGET_EXHAUSTED)
        self.assertEqual(adapter.requests, [])

    def test_cancellation_is_recorded_then_reraised(self) -> None:
        adapter = model.FakeModel([KeyboardInterrupt()])
        with self.assertRaises(KeyboardInterrupt):
            self._run(adapter)
        run = self.store.load_run(self.store.list_runs()[0])
        self.assertEqual(run["outcome"], runner.OUTCOME_CANCELLED)

    def test_unexpected_error_is_recorded_then_reraised(self) -> None:
        adapter = model.FakeModel([RuntimeError("boom")])
        with self.assertRaises(RuntimeError):
            self._run(adapter)
        run = self.store.load_run(self.store.list_runs()[0])
        self.assertEqual(run["outcome"], runner.OUTCOME_BACKEND_ERROR)

    def test_prompt_contains_packet_and_no_tool_surface(self) -> None:
        adapter = model.FakeModel([_response(json.dumps(VALID_BRIEFING))])
        self._run(adapter)
        request = adapter.requests[0]
        self.assertIn("packet text", request.prompt)
        self.assertNotIn("tools", request.output_schema)


if __name__ == "__main__":
    unittest.main()
