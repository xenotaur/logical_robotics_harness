import pathlib
import tempfile
import unittest

from local_agent import context, settings, testing_support


class ContextPacketTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        self.commit = testing_support.make_repo(self.repo)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _build(
        self, work_item_id: str, budgets: settings.Budgets | None = None
    ) -> context.ContextPacket:
        return context.build_packet(
            repo=self.repo,
            repo_label="TEST",
            revision="HEAD",
            project_dir=".",
            work_item_id=work_item_id,
            budgets=budgets or settings.Budgets(),
        )

    def test_ready_item_keeps_execution_readiness_error(self) -> None:
        packet = self._build("WI-T-1")
        diagnostics = packet.manifest["diagnostics"]
        self.assertTrue(diagnostics["prompt_readiness"]["prompt_ready"])
        self.assertFalse(diagnostics["execution_readiness"]["execution_ready"])
        codes = [i["code"] for i in diagnostics["execution_readiness"]["issues"]]
        self.assertIn("EXECUTION_READINESS_NOT_READY", codes)
        self.assertIn("EXECUTION_READINESS_NOT_READY", packet.text)
        self.assertEqual(packet.manifest["source_commit"], self.commit)

    def test_thin_item_blocking_reasons_are_visible(self) -> None:
        packet = self._build("WI-T-2")
        readiness = packet.manifest["diagnostics"]["prompt_readiness"]
        self.assertFalse(readiness["prompt_ready"])
        self.assertIn("missing Required Changes section", readiness["blocking_reasons"])
        self.assertIn("missing Required Changes section", packet.text)

    def test_related_sources_included_with_dependency_first(self) -> None:
        packet = self._build("WI-T-1")
        relations = [s["relation"] for s in packet.manifest["sources"]]
        self.assertEqual(relations[0], "WorkItem")
        self.assertIn("Dependency", relations)
        self.assertIn("Design", relations)
        self.assertLess(relations.index("Dependency"), relations.index("Design"))
        self.assertIn("[S1]", packet.text)

    def test_budget_truncation_and_omission_are_recorded(self) -> None:
        packet = self._build(
            "WI-T-1",
            settings.Budgets(max_packet_bytes=700, max_source_bytes=200),
        )
        manifest = packet.manifest
        self.assertLessEqual(manifest["source_bytes"], 700)
        self.assertEqual(manifest["rendered_bytes"], len(packet.text.encode("utf-8")))
        truncated = [s for s in manifest["sources"] if s["truncated"]]
        self.assertTrue(truncated or manifest["omitted_sources"])

    def test_packet_hash_is_stable_for_same_inputs(self) -> None:
        self.assertEqual(self._build("WI-T-1").sha256, self._build("WI-T-1").sha256)

    def test_private_paths_never_selected(self) -> None:
        packet = self._build("WI-T-1")
        paths = [s["path"] for s in packet.manifest["sources"]]
        self.assertFalse(any("executions" in path for path in paths))


class SubdirectoryProjectTest(unittest.TestCase):
    def test_prefixed_reference_resolves_by_labelled_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            repo.mkdir()
            item = repo / "sub/project/work_items/proposed/WI-T-1.md"
            testing_support.make_repo(repo, project_dir="sub")
            text = item.read_text(encoding="utf-8").replace(
                "  - project/design/demo.md",
                "  - sub/project/design/proposals/a/00_proposal.md",
            )
            item.write_text(text, encoding="utf-8")
            testing_support.run_git(repo, "commit", "-qam", "prefix")
            packet = context.build_packet(
                repo=repo,
                repo_label="TEST",
                revision="HEAD",
                project_dir="sub",
                work_item_id="WI-T-1",
                budgets=settings.Budgets(),
            )
        unresolved = packet.manifest["diagnostics"]["unresolved_references"]
        self.assertEqual(
            unresolved[0]["reference"], "sub/project/design/proposals/a/00_proposal.md"
        )
        fallback = [
            s
            for s in packet.manifest["sources"]
            if s["resolved_by"] == "prefix_fallback"
        ]
        self.assertEqual(
            fallback[0]["path"], "sub/project/design/proposals/a/00_proposal.md"
        )


if __name__ == "__main__":
    unittest.main()
