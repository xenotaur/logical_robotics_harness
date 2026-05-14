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

    def test_unknown_request_name_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "unknown request name: no-such-request"
        ):
            request_catalog.require("no-such-request")

    def test_representative_legacy_template_name_resolution(self) -> None:
        metadata = request_catalog.require("improve_coverage")

        self.assertEqual(metadata.canonical_name, "improve-coverage")
        self.assertEqual(metadata.template_name, "improve_coverage")


if __name__ == "__main__":
    unittest.main()
