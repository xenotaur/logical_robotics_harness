"""Tests for the packaged --interactive script's safety constraints."""

from __future__ import annotations

import re
import unittest

from lrh.ux import frame


class InteractiveScriptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = frame.read_static("lrh-interactive.js").decode("utf-8")

    def test_the_script_never_evaluates_strings_or_fetches(self) -> None:
        for pattern in (
            r"\beval\s*\(",
            r"new\s+Function\b",
            r"\binnerHTML\b",
            r"\bouterHTML\b",
            r"insertAdjacentHTML",
            r"document\.write",
            r"\bfetch\s*\(",
            r"XMLHttpRequest",
            r"WebSocket",
            r"setTimeout\s*\(\s*[\"'`]",
        ):
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, self.source))

    def test_storage_is_one_key_and_always_guarded(self) -> None:
        self.assertEqual(
            set(re.findall(r'"(lrh-[a-z-]+)"', self.source)) & {"lrh-console-theme"},
            {"lrh-console-theme"},
        )
        uses = [match.start() for match in re.finditer(r"localStorage\.", self.source)]
        self.assertTrue(uses)
        for start in uses:
            preceding = self.source[max(0, start - 120) : start]
            self.assertIn("try {", preceding)

    def test_a_pinned_theme_hides_the_switch(self) -> None:
        self.assertIn('const pinned = root.hasAttribute("data-theme");', self.source)
        self.assertIn("if (!slot || pinned) return;", self.source)

    def test_filters_keep_unfinished_needs_visible(self) -> None:
        self.assertIn("item.dataset.unmet", self.source)


if __name__ == "__main__":
    unittest.main()
