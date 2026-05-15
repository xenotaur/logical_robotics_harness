import unittest

from lrh.assist import request_catalog


class TestRequestCatalog(unittest.TestCase):
    def test_canonical_name_resolution(self) -> None:
        metadata = request_catalog.require("prompt-from-work-item")

        self.assertEqual(metadata.canonical_name, "prompt-from-work-item")
        self.assertEqual(metadata.template_name, "codex_prompt_from_work_item")
        self.assertEqual(metadata.category, "work-items")

    def test_legacy_name_resolution(self) -> None:
        metadata = request_catalog.require("codex-prompt-from-work-item")

        self.assertEqual(metadata.canonical_name, "prompt-from-work-item")
        self.assertIn("codex-prompt-from-work-item", metadata.legacy_names)

    def test_run_packet_request_is_structured_work_item_request(self) -> None:
        metadata = request_catalog.require("run-packet-from-work-item")

        self.assertEqual(metadata.canonical_name, "run-packet-from-work-item")
        self.assertEqual(metadata.template_name, "run_packet_from_work_item")
        self.assertEqual(metadata.implementation_target, "structured_run_packet")
        self.assertIn("run_packet_from_work_item", metadata.legacy_names)

    def test_run_report_request_is_structured_work_item_request(self) -> None:
        metadata = request_catalog.require("run-report-from-work-item")

        self.assertEqual(metadata.canonical_name, "run-report-from-work-item")
        self.assertEqual(metadata.template_name, "run_report_from_work_item")
        self.assertEqual(metadata.implementation_target, "structured_run_report")
        self.assertIn("run_report_from_work_item", metadata.legacy_names)

    def test_unknown_request_name_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "unknown request name: no-such-request"
        ):
            request_catalog.require("no-such-request")

    def test_representative_legacy_template_name_resolution(self) -> None:
        metadata = request_catalog.require("improve_coverage")

        self.assertEqual(metadata.canonical_name, "improve-coverage")
        self.assertEqual(metadata.template_name, "improve_coverage")

    def test_canonical_names_follow_design_acronym_guidance(self) -> None:
        canonical_names = request_catalog.canonical_names()

        self.assertIn("review-pull-request-against-work-item", canonical_names)
        self.assertIn("assess-continuous-integration-status", canonical_names)
        self.assertIn("implement-continuous-integration-workflow", canonical_names)
        self.assertNotIn("review-pr-against-work-item", canonical_names)
        self.assertNotIn("assess-ci-status", canonical_names)
        self.assertNotIn("implement-ci-workflow", canonical_names)


if __name__ == "__main__":
    unittest.main()
