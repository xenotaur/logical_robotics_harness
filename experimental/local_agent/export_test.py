import json
import pathlib
import tempfile
import unittest

from local_agent import (
    context,
    export,
    model,
    recorder,
    runner,
    settings,
    testing_support,
)

BRIEFING = {
    "summary": "A small feature.",
    "readiness_statement": "Not execution-ready.",
    "constraints": [],
    "dependencies": [],
    "evidence_gaps": [],
    "relevant_sources": [],
    "open_questions": [],
}


class ExportTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self._tmp.name)
        self.store = recorder.Store(
            self.base / "store", clock=testing_support.SteppingClock()
        )
        manifest = {
            "work_item_id": "WI-T-1",
            "sources": [
                {
                    "source_id": "S1",
                    "path": "project/work_items/proposed/WI-T-1.md",
                    "line_start": 1,
                    "line_end": 3,
                    "total_lines": 3,
                    "truncated": False,
                    "relation": "WorkItem",
                }
            ],
            "omitted_sources": [],
        }
        self.sha = context.packet_sha256(manifest, "SECRET PACKET BODY\n")
        self.store.save_packet(self.sha, manifest, "SECRET PACKET BODY\n")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, briefing: dict) -> str:
        return runner.run_briefing(
            store=self.store,
            packet_sha256=self.sha,
            approved_sha256=self.sha,
            adapter=model.FakeModel(
                [model.ModelResponse(json.dumps(briefing), "stop", 1, 1, {})]
            ),
            budgets=settings.Budgets(),
        )

    def _export(self, run_id: str, **kwargs: object) -> dict:
        path = export.export_run(
            self.store, run_id, self.base / "out", home=str(self.base), **kwargs
        )
        return json.loads(path.read_text(encoding="utf-8"))

    def test_default_export_excludes_raw_content(self) -> None:
        run_id = self._run(BRIEFING)
        exported = self._export(run_id)
        text = json.dumps(exported)
        self.assertNotIn("SECRET PACKET BODY", text)
        self.assertNotIn("A small feature.", text)
        self.assertNotIn("briefing", exported)
        self.assertIn("parsed briefing text", " ".join(exported["excluded"]))
        self.assertEqual(exported["run"]["outcome"], runner.OUTCOME_COMPLETED)

    def test_include_output_requires_scores(self) -> None:
        run_id = self._run(BRIEFING)
        with self.assertRaisesRegex(export.ExportError, "scored runs"):
            self._export(run_id, include_output=True)

    def test_flagged_evaluation_notes_are_withheld(self) -> None:
        run_id = self._run(BRIEFING)
        export.record_evaluation(
            self.store,
            run_id,
            {"usefulness": 1, "notes": "token=ghp_abcdef0123456789abcdef0123"},
        )
        with self.assertRaisesRegex(export.ExportError, "evaluation withheld"):
            self._export(run_id)

    def test_include_output_when_scan_is_clean(self) -> None:
        run_id = self._run(BRIEFING)
        export.record_evaluation(self.store, run_id, {"usefulness": 2})
        exported = self._export(run_id, include_output=True)
        self.assertEqual(exported["briefing"]["summary"], "A small feature.")
        self.assertIn("not project state", exported["briefing_label"])

    def test_include_output_withheld_when_scan_flags_content(self) -> None:
        leaky = dict(BRIEFING, summary="api_key = sk-live-abcdef0123456789abcdef")
        run_id = self._run(leaky)
        export.record_evaluation(self.store, run_id, {"usefulness": 0})
        with self.assertRaisesRegex(export.ExportError, "withheld"):
            self._export(run_id, include_output=True)

    def test_home_paths_rewritten(self) -> None:
        run_id = self._run(BRIEFING)
        exported = self._export(run_id)
        self.assertNotIn(str(self.base), json.dumps(exported))

    def test_failed_attempts_export_too(self) -> None:
        run_id = runner.run_briefing(
            store=self.store,
            packet_sha256=self.sha,
            approved_sha256=self.sha,
            adapter=model.FakeModel(
                [model.BackendError(model.KIND_BACKEND_ERROR, "500")]
            ),
            budgets=settings.Budgets(),
        )
        exported = self._export(run_id)
        self.assertEqual(exported["run"]["outcome"], runner.OUTCOME_BACKEND_ERROR)

    def test_evaluation_validation(self) -> None:
        run_id = self._run(BRIEFING)
        export.record_evaluation(
            self.store, run_id, {"usefulness": 2, "miss_cause": None}
        )
        self.assertEqual(self._export(run_id)["evaluation"]["usefulness"], 2)
        with self.assertRaises(export.ExportError):
            export.record_evaluation(self.store, run_id, {"usefulness": 5})
        with self.assertRaises(export.ExportError):
            export.record_evaluation(self.store, run_id, {"vibes": "good"})

    def test_inspect_lists_sources_and_events(self) -> None:
        run_id = self._run(BRIEFING)
        text = export.inspect_run(self.store, run_id)
        self.assertIn("S1 project/work_items/proposed/WI-T-1.md", text)
        self.assertIn("outcome: completed", text)
        self.assertNotIn("SECRET PACKET BODY", text)


if __name__ == "__main__":
    unittest.main()
