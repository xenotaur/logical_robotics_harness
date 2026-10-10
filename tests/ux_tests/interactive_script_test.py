"""Tests for the packaged --interactive script's safety constraints."""

from __future__ import annotations

import re
import unittest

from lrh.ux import frame


class InteractiveScriptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = frame.read_static("lrh-interactive.js").decode("utf-8")
        self.early = frame.read_static("lrh-theme-early.js").decode("utf-8")
        self.both = self.source + self.early

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
                self.assertIsNone(re.search(pattern, self.both))

    def test_storage_is_one_key_and_always_guarded(self) -> None:
        self.assertIn('const THEME_KEY = "lrh-console-theme";', self.source)
        calls = re.findall(r"localStorage\.(\w+)\(([^,)]*)", self.both)
        self.assertTrue(calls)
        self.assertEqual(
            {argument.strip() for _method, argument in calls},
            {"THEME_KEY", '"lrh-console-theme"'},
        )
        for script in (self.source, self.early):
            for match in re.finditer(r"localStorage\.", script):
                preceding = script[max(0, match.start() - 120) : match.start()]
                self.assertIn("try {", preceding)

    def test_a_pinned_theme_hides_the_switch_and_is_never_overridden(self) -> None:
        self.assertIn(
            'root.getAttribute("data-lrh-theme-source") !== "browser"', self.source
        )
        self.assertIn("if (!slot || pinned) return;", self.source)
        self.assertIn('if (root.hasAttribute("data-theme")) return;', self.early)

    def test_filters_keep_unfinished_needs_visible(self) -> None:
        # The list is JSON, never split on spaces: IDs may contain them.
        self.assertIn('JSON.parse(item.dataset.unmet || "[]")', self.source)
        self.assertNotIn("unmet.split(", self.source)

    def test_closing_a_drawer_returns_focus_before_hiding_it(self) -> None:
        body = self.source.split("function showDrawer(id) {", 1)[1].split(
            "\n    }\n", 1
        )[0]
        guard = body.index("drawer.contains(document.activeElement)")
        self.assertLess(guard, body.index("trigger.focus()"))
        fallback = body.index("map.focus({ preventScroll: true })")
        self.assertLess(fallback, body.index("drawer.hidden = hide;"))

    def test_returning_focus_after_a_close_is_not_a_preview(self) -> None:
        self.assertIn(
            "if (!currentSelection() && !restoringFocus) mark(id, true);", self.source
        )
        body = self.source.split("function showDrawer(id) {", 1)[1]
        self.assertLess(
            body.index("restoringFocus = true;"), body.index("trigger.focus()")
        )
        self.assertLess(body.index("map.focus("), body.index("restoringFocus = false;"))

    def test_loading_shows_only_for_real_same_origin_navigations(self) -> None:
        body = self.source.split("function setupLoading() {", 1)[1]
        for guard in (
            "event.defaultPrevented",
            "event.metaKey || event.ctrlKey || event.shiftKey || event.altKey",
            'link.hasAttribute("download")',
            'link.target && link.target !== "_self"',
            "url.origin !== window.location.origin",
            'url.searchParams.has("download")',
        ):
            with self.subTest(guard=guard):
                self.assertIn(guard, body)
        self.assertIn("const LOADING_DELAY_MS = 300;", self.source)
        self.assertIn('window.addEventListener("pageshow", clear);', body)
        self.assertIn('overlay.setAttribute("role", "status");', body)


if __name__ == "__main__":
    unittest.main()
