import json
import pathlib
import tempfile
import unittest

from local_agent import (
    ask,
    context,
    export,
    model,
    recorder,
    runner,
    settings,
    tasks,
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
            testing_support.full_scores(
                usefulness=1, notes="token=ghp_abcdef0123456789abcdef0123"
            ),
        )
        with self.assertRaisesRegex(export.ExportError, "evaluation withheld"):
            self._export(run_id)

    def test_include_output_when_scan_is_clean(self) -> None:
        run_id = self._run(BRIEFING)
        export.record_evaluation(
            self.store, run_id, testing_support.full_scores(usefulness=2)
        )
        exported = self._export(run_id, include_output=True)
        self.assertEqual(exported["briefing"]["summary"], "A small feature.")
        self.assertIn("not project state", exported["briefing_label"])

    def test_include_output_withheld_when_scan_flags_content(self) -> None:
        leaky = dict(BRIEFING, summary="api_key = sk-live-abcdef0123456789abcdef")
        run_id = self._run(leaky)
        export.record_evaluation(
            self.store, run_id, testing_support.full_scores(usefulness=0)
        )
        with self.assertRaisesRegex(export.ExportError, "withheld"):
            self._export(run_id, include_output=True)

    def test_packet_altered_after_run_is_refused(self) -> None:
        run_id = self._run(BRIEFING)
        manifest_file = self.store.packet_dir(self.sha) / "manifest.json"
        altered = json.loads(manifest_file.read_text(encoding="utf-8"))
        altered["source_commit"] = "0" * 40
        manifest_file.write_text(json.dumps(altered), encoding="utf-8")
        with self.assertRaisesRegex(export.ExportError, "no longer matches"):
            self._export(run_id)

    def test_b0_text_follows_scored_and_scanned_rule(self) -> None:
        run_id = runner.record_manual_briefing(
            store=self.store,
            packet_sha256=self.sha,
            briefing_text="Owner wrote this baseline.",
            author_minutes=4,
            task_id="T01",
        )
        default = self._export(run_id)
        self.assertNotIn("Owner wrote this baseline.", json.dumps(default))
        self.assertIn("B0 briefing text", " ".join(default["excluded"]))
        with self.assertRaisesRegex(export.ExportError, "scored runs"):
            self._export(run_id, include_output=True)
        with self.assertRaisesRegex(export.ExportError, "missing evaluation"):
            export.record_evaluation(self.store, run_id, {"total_human_minutes": 4})
        with self.assertRaisesRegex(export.ExportError, "scored runs"):
            self._export(run_id, include_output=True)
        export.record_evaluation(
            self.store,
            run_id,
            testing_support.full_scores(usefulness=2, total_human_minutes=4),
        )
        exported = self._export(run_id, include_output=True)
        self.assertEqual(exported["manual_briefing"], "Owner wrote this baseline.")
        self.assertEqual(exported["run"]["condition"], "B0")

    def test_unfilled_template_is_rejected(self) -> None:
        run_id = self._run(BRIEFING)
        template_path = tasks.DEFAULT_TASKS_FILE.parent / "scores_template.json"
        template = json.loads(template_path.read_text(encoding="utf-8"))
        self.assertEqual(set(template), set(export.EVALUATION_FIELDS))
        with self.assertRaises(export.ExportError):
            export.record_evaluation(self.store, run_id, template)
        filled = dict(template, usefulness=1, diagnostics_surfaced=True)
        with self.assertRaisesRegex(export.ExportError, "non-negative number"):
            export.record_evaluation(self.store, run_id, filled)
        for field in export._COUNT_FIELDS:
            filled[field] = 0
        export.record_evaluation(self.store, run_id, filled)
        with self.assertRaisesRegex(export.ExportError, "non-negative"):
            export.record_evaluation(
                self.store, run_id, dict(filled, review_minutes=-1)
            )

    def test_non_finite_counts_rejected(self) -> None:
        run_id = self._run(BRIEFING)
        for bad in (float("nan"), float("inf")):
            with self.assertRaisesRegex(export.ExportError, "finite"):
                export.record_evaluation(
                    self.store,
                    run_id,
                    testing_support.full_scores(review_minutes=bad),
                )

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
        export.record_evaluation(self.store, run_id, testing_support.full_scores())
        self.assertEqual(self._export(run_id)["evaluation"]["usefulness"], 2)
        with self.assertRaises(export.ExportError):
            export.record_evaluation(
                self.store, run_id, testing_support.full_scores(usefulness=5)
            )
        with self.assertRaises(export.ExportError):
            export.record_evaluation(
                self.store, run_id, testing_support.full_scores(vibes="good")
            )
        with self.assertRaises(export.ExportError):
            export.record_evaluation(
                self.store, run_id, testing_support.full_scores(notes=None)
            )
        for wrong_type in (
            {"usefulness": True},
            {"usefulness": 1.0},
            {"diagnostics_surfaced": 1},
            {"diagnostics_surfaced": 0},
        ):
            with self.subTest(wrong_type):
                with self.assertRaises(export.ExportError):
                    export.record_evaluation(
                        self.store, run_id, testing_support.full_scores(**wrong_type)
                    )
        for field in export.EVALUATION_FIELDS:
            incomplete = testing_support.full_scores()
            del incomplete[field]
            with self.subTest(field):
                with self.assertRaisesRegex(export.ExportError, "missing"):
                    export.record_evaluation(self.store, run_id, incomplete)

    def test_inspect_lists_sources_and_events(self) -> None:
        run_id = self._run(BRIEFING)
        text = export.inspect_run(self.store, run_id)
        self.assertIn("S1 project/work_items/proposed/WI-T-1.md", text)
        self.assertIn("outcome: completed", text)
        self.assertNotIn("SECRET PACKET BODY", text)


class AskExportTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self._tmp.name)
        repo = self.base / "repo"
        repo.mkdir()
        testing_support.make_repo(repo)
        self.store = recorder.Store(
            self.base / "store", clock=testing_support.SteppingClock()
        )
        self.ctx = ask.build_context(repo=repo, files=["project/design/demo.md"])

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _ask(self, answer: str, question: str | None = None) -> str:
        return ask.run_ask(
            store=self.store,
            question=question or "PRIVATE QUESTION?",
            ctx=self.ctx,
            adapter=model.FakeModel([model.ModelResponse(answer, "stop", 1, 1, {})]),
            budgets=settings.Budgets(),
        )

    def _export(self, run_id: str, **kwargs: object) -> dict:
        path = export.export_run(
            self.store, run_id, self.base / "out", home=str(self.base), **kwargs
        )
        return json.loads(path.read_text(encoding="utf-8"))

    def test_default_export_omits_question_answer_and_note(self) -> None:
        run_id = self._ask("PRIVATE ANSWER")
        ask.record_rating(self.store, run_id, "o", "PRIVATE NOTE")
        text = json.dumps(self._export(run_id))
        for secret in ("PRIVATE QUESTION", "PRIVATE ANSWER", "PRIVATE NOTE"):
            self.assertNotIn(secret, text)
        self.assertIn('"value": "ok"', text)

    def test_include_output_requires_rating_and_clean_scan(self) -> None:
        run_id = self._ask("Fine answer (S1:L1).")
        with self.assertRaisesRegex(export.ExportError, "rated runs"):
            self._export(run_id, include_output=True)
        ask.record_rating(self.store, run_id, "g", "nice")
        exported = self._export(run_id, include_output=True)
        self.assertEqual(exported["answer"], "Fine answer (S1:L1).")
        self.assertEqual(exported["run"]["rating"]["note"], "nice")

        leaky = self._ask("api_key = sk-live-abcdef0123456789abcdef")
        ask.record_rating(self.store, leaky, "b")
        with self.assertRaisesRegex(export.ExportError, "withheld"):
            self._export(leaky, include_output=True)

    def test_include_output_withholds_medium_only_findings(self) -> None:
        cases = (
            ("Ask ops@example.org.", "ok", "answer"),
            ("Fine answer.", "ok", "question"),
            ("Fine answer.", "call 555-867-5309 about it", "rating note"),
        )
        for answer, note, label in cases:
            with self.subTest(label):
                question = "Is 10.1.2.3 up?" if label == "question" else None
                run_id = self._ask(answer, question=question)
                ask.record_rating(self.store, run_id, "g", note)
                with self.assertRaisesRegex(export.ExportError, "withheld"):
                    self._export(run_id, include_output=True)

    def test_real_model_runs_export_with_loopback_endpoint(self) -> None:
        class OllamaShaped(model.FakeModel):
            def describe(self) -> dict[str, object]:
                return {
                    "backend": "ollama",
                    "base_url": "http://127.0.0.1:11434",
                    "model": "gemma4:12b",
                    "local_only": True,
                }

        run_id = ask.run_ask(
            store=self.store,
            question="q",
            ctx=self.ctx,
            adapter=OllamaShaped([model.ModelResponse("ok", "stop", 1, 1, {})]),
            budgets=settings.Budgets(),
        )
        exported = self._export(run_id)
        self.assertEqual(exported["run"]["model"]["base_url"], "loopback:11434")
        self.assertNotIn("127.0.0.1", json.dumps(exported))

    def test_hex_digests_do_not_trip_the_final_scan(self) -> None:
        luhn_digest = "5d8f6cce532a7aeb57196be62344095936793400b3aeb3580d248b17d5518a86"
        run_id = self._ask("ok")
        self.store.update_run(run_id, prompt_template_sha256=luhn_digest)
        exported = self._export(run_id)
        self.assertEqual(exported["run"]["prompt_template_sha256"], luhn_digest)

    def test_failure_details_with_findings_are_withheld(self) -> None:
        run_id = ask.record_failure(
            self.store,
            "q",
            "missing_prerequisite",
            "adapter: endpoint must be loopback, got "
            "'http://10.9.8.7:11434/?token=ghp_abcdef0123456789abcdef0123'",
        )
        text = json.dumps(self._export(run_id))
        self.assertNotIn("ghp_", text)
        self.assertNotIn("10.9.8.7", text)
        self.assertIn("[withheld:", text)

    def test_inspect_shows_kind_and_sources(self) -> None:
        run_id = self._ask("x")
        summary = export.inspect_run(self.store, run_id)
        self.assertIn("ask", summary)
        self.assertIn("project/design/demo.md", summary)


if __name__ == "__main__":
    unittest.main()
