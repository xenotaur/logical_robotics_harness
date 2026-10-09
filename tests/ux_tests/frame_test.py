"""Tests for the LRH Console app frame."""

from __future__ import annotations

import datetime
import re
import unittest

from lrh.ux import frame

_PAGE = (
    '<!doctype html>\n<html lang="en">\n<head><title>LRH Example</title></head>\n'
    '<body>\n<div class="lrh-app-shell">content</div>\n</body>\n</html>\n'
)
_PROJECTS = (
    frame.Project(selector="lcats", label="Lcats"),
    frame.Project(
        selector="logical_robotics_harness", label="Logical Robotics Harness"
    ),
)
_AT = datetime.datetime(2026, 10, 8, 12, 30, 5, tzinfo=datetime.UTC)


def _framed(path: str, query: dict[str, str] | None = None) -> str:
    return frame.apply_frame(
        _PAGE,
        frame.FrameContext(
            path=path, query=query or {}, projects=_PROJECTS, rendered_at=_AT
        ),
    )


class FrameTest(unittest.TestCase):
    def test_frame_wraps_the_body_without_changing_it(self) -> None:
        page = _framed("/meta")

        main = page.split('<main class="lrh-main" id="lrh-content">', 1)[1]
        main = main.split("</main>", 1)[0]
        self.assertIn('<div class="lrh-app-shell">content</div>', main)
        self.assertTrue(page.endswith("</body>\n</html>\n"))
        self.assertEqual(page.count("<body>"), 1)

    def test_top_bar_links_home_and_to_settings(self) -> None:
        page = _framed("/workbench")

        self.assertIn('<a class="lrh-home" href="/meta">', page)
        self.assertIn('href="/settings"', page)
        self.assertIn('<span class="lrh-pagetitle">LRH Example</span>', page)
        self.assertIn("Rendered 12:30:05 UTC", page)
        self.assertIn('src="/static/lrh-icon-64.png"', page)

    def test_all_projects_scope_lists_views_and_every_project(self) -> None:
        page = _framed("/meta")

        self.assertIn('<span class="lrh-scopename">All projects</span>', page)
        self.assertIn('<a href="/meta" aria-current="true">All projects</a>', page)
        self.assertIn('<a href="/project/lcats">Lcats</a>', page)
        for label in ("Statusboard", "Workspace", "Workbench", "Conversations"):
            self.assertIn(f'<span class="lrh-label">{label}</span>', page)
        self.assertIn('href="/meta" aria-current="page"', page)

    def test_project_scope_comes_from_the_path(self) -> None:
        page = _framed("/project/lcats/workstreams/WS-ONE")

        self.assertIn('<span class="lrh-scopename">Lcats</span>', page)
        self.assertIn('<a href="/project/lcats" aria-current="true">Lcats</a>', page)
        self.assertIn('<span class="lrh-label">Overview</span>', page)
        self.assertEqual(
            frame.scope_selector("/meta/project", {"project": "lcats"}), "lcats"
        )
        self.assertIsNone(frame.scope_selector("/style", {}))

    def test_drawer_opens_only_with_an_item(self) -> None:
        self.assertNotIn("lrh-drawer", _framed("/meta").split("</style>")[-1])

        page = _framed("/project/lcats", {"item": "WI-ONE", "view": "map"})
        self.assertIn('<h2 id="lrh-drawer-title" class="lrh-mono">WI-ONE</h2>', page)
        self.assertIn('href="/project/lcats/work-items/WI-ONE"', page)
        self.assertIn('href="/project/lcats?view=map"', page)

    def test_drawer_without_a_project_explains_the_full_page(self) -> None:
        page = _framed("/meta", {"item": "WI-ONE"})

        self.assertIn("Choose a project scope", page)
        self.assertNotIn("/work-items/", page)

    def test_untrusted_values_are_escaped(self) -> None:
        page = _framed("/project/<b>x", {"item": '<script>alert("x")</script>'})

        self.assertNotIn("<script>", page)
        self.assertNotIn("<b>x", page)
        self.assertIn("&lt;script&gt;", page)

    def test_a_page_with_its_own_main_keeps_one_main_landmark(self) -> None:
        page = frame.apply_frame(
            _PAGE.replace("content", "<main>content</main>"),
            frame.FrameContext(path="/", query={}, rendered_at=_AT),
        )

        self.assertEqual(page.count("<main"), 1)
        self.assertIn('<div class="lrh-main" id="lrh-content">', page)

    def test_drawer_comes_before_the_page_in_reading_order(self) -> None:
        page = _framed("/project/lcats", {"item": "WI-ONE"})

        self.assertLess(page.index("lrh-drawer"), page.index('id="lrh-content"'))
        self.assertLess(page.index('class="lrh-skip"'), page.index("lrh-topbar"))

    def test_page_title_is_escaped_in_the_top_bar(self) -> None:
        page = frame.apply_frame(
            _PAGE.replace("LRH Example", "A &amp; <b>B</b>"),
            frame.FrameContext(path="/", query={}, rendered_at=_AT),
        )

        self.assertIn('<span class="lrh-pagetitle">A &amp; &lt;b&gt;B&lt;/b&gt;', page)

    def test_a_page_without_a_body_is_left_alone(self) -> None:
        context = frame.FrameContext(path="/", query={})
        self.assertEqual(frame.apply_frame("plain text", context), "plain text")

    def test_icons_are_inline_hidden_and_use_the_text_color(self) -> None:
        for name in frame.ICON_NAMES:
            with self.subTest(icon=name):
                svg = frame.icon(name)
                self.assertTrue(svg.startswith("<svg "))
                self.assertIn('aria-hidden="true"', svg)
                self.assertIn('stroke="currentColor"', svg)
        with self.assertRaises(ValueError):
            frame.icon("missing")

    def test_every_served_static_file_is_packaged(self) -> None:
        for name in frame.STATIC_FILES:
            with self.subTest(name=name):
                self.assertTrue(frame.read_static(name))
        self.assertIsNone(frame.read_static("icons/settings.svg"))
        self.assertIsNone(frame.read_static("../frame.py"))

    def test_licenses_ship_with_the_font_and_icons(self) -> None:
        font = frame.read_static("fonts/OFL-montserrat.txt").decode("utf-8")
        icons = frame.read_static("icons/LICENSE-lucide.txt").decode("utf-8")
        self.assertIn("The Montserrat Project Authors", font)
        self.assertIn("SIL OPEN FONT LICENSE Version 1.1", font)
        self.assertIn("ISC License", icons)

    def test_the_frame_uses_no_scripts(self) -> None:
        page = _framed("/project/lcats", {"item": "WI-ONE"})
        self.assertNotIn("<script", page.lower())
        self.assertIsNone(re.search(r"\son[a-z]+\s*=", page, flags=re.I))
        self.assertIn('<input type="checkbox" id="lrh-rail"', page)


if __name__ == "__main__":
    unittest.main()
