import json
import re
import unittest

from lrh.pr_brief import render
from tests.pr_brief_tests import sample_data


class InlineMarkupTest(unittest.TestCase):
    def test_escapes_html_and_applies_code_and_bold(self) -> None:
        self.assertEqual(
            render.inline("Use `a<b>` and **bold** <script>"),
            "Use <code>a&lt;b&gt;</code> and <b>bold</b> &lt;script&gt;",
        )

    def test_bold_markers_inside_code_stay_literal(self) -> None:
        self.assertEqual(render.inline("`**x**`"), "<code>**x**</code>")

    def test_unmatched_backtick_stays_literal(self) -> None:
        self.assertEqual(render.inline("a `b"), "a `b")
        self.assertEqual(render.inline("`x` and `y"), "<code>x</code> and `y")

    def test_none_renders_empty(self) -> None:
        self.assertEqual(render.inline(None), "")


class FileSlugTest(unittest.TestCase):
    def test_slugs_are_unique_and_hash_safe(self) -> None:
        used: set[str] = set()
        first = render.file_slug("src/A.py", used)
        second = render.file_slug("src-a.py", used)
        self.assertEqual(first, "f-src-a-py")
        self.assertEqual(second, "f-src-a-py-2")
        self.assertRegex(first, r"^[a-z0-9-]+$")


class ValidateTest(unittest.TestCase):
    def test_sample_is_valid_without_warnings(self) -> None:
        errors, warnings = render.validate(sample_data.sample_data())
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_reports_bad_enums_ids_and_categories(self) -> None:
        data = sample_data.sample_data()
        data["files"][0]["category"] = "mystery"
        data["briefing"]["review_notes"][0]["severity"] = "urgent"
        data["briefing"]["review_notes"][0]["confidence"] = "sure"
        data["briefing"]["tests"]["rows"][0]["tone"] = "loud"
        data["briefing"]["figures"].append(dict(data["briefing"]["figures"][0]))
        data["briefing"]["figures"].append({"id": "files", "html": "<p></p>"})
        data["briefing"]["figures"].append({"id": "f-x", "html": ""})
        errors, _ = render.validate(data)
        joined = "\n".join(errors)
        self.assertIn("unknown category 'mystery'", joined)
        self.assertIn("review_notes[0].severity", joined)
        self.assertIn("review_notes[0].confidence", joined)
        self.assertIn("tests.rows[0].tone", joined)
        self.assertIn("'architecture' is duplicated", joined)
        self.assertIn("figures[2].id 'files'", joined)
        self.assertIn("figures[3].id 'f-x'", joined)
        self.assertIn("figures[3].html is empty", joined)

    def test_warns_about_missing_narrative(self) -> None:
        data = sample_data.sample_data()
        data["briefing"]["headline_summary"] = ""
        data["briefing"]["files"]["src/app/cli.py"]["gist"] = ""
        data["briefing"]["files"]["not/in/pr.py"] = {"gist": "x"}
        _, warnings = render.validate(data)
        self.assertIn("briefing.headline_summary is empty", warnings)
        self.assertIn("no gist for file: src/app/cli.py", warnings)
        self.assertTrue(any("not/in/pr.py" in warning for warning in warnings))

    def test_missing_top_level_keys_are_errors(self) -> None:
        errors, _ = render.validate({"pr": {}})
        self.assertIn("missing top-level key: files", errors)


class StatusChipsTest(unittest.TestCase):
    def test_open_pr_with_conflict_drift_no_ci_no_reviews(self) -> None:
        chips = render.status_chips(sample_data.sample_data())
        self.assertEqual(
            chips,
            [
                ("", "Open"),
                ("crit", "Merge conflict · 1 file"),
                ("warn", "16 commits behind main"),
                ("warn", "No CI checks reported"),
                ("warn", "No reviews yet"),
            ],
        )

    def test_clean_passing_approved_draft(self) -> None:
        data = sample_data.sample_data()
        data["pr"]["is_draft"] = True
        data["status"]["conflicts"] = {"checked": True, "clean": True, "files": []}
        data["status"]["mergeable"] = "MERGEABLE"
        data["status"]["behind_by"] = 0
        data["status"]["checks"] = {
            "total": 3,
            "passing": 3,
            "failing": 0,
            "pending": 0,
        }
        data["status"]["reviews"]["approvals"] = 1
        self.assertEqual(
            render.status_chips(data),
            [
                ("warn", "Draft"),
                ("ok", "Merges cleanly"),
                ("ok", "All 3 checks pass"),
                ("ok", "Approved"),
            ],
        )

    def test_unchecked_conflict_falls_back_to_mergeable_and_failures_win(self) -> None:
        data = sample_data.sample_data()
        data["status"]["conflicts"] = {"checked": False, "clean": None, "files": []}
        data["status"]["checks"] = {
            "total": 4,
            "passing": 2,
            "failing": 1,
            "pending": 1,
        }
        data["status"]["reviews"]["changes_requested"] = 1
        chips = render.status_chips(data)
        self.assertIn(("crit", "Merge conflict"), chips)
        self.assertIn(("crit", "1 of 4 checks failing"), chips)
        self.assertIn(("crit", "Changes requested"), chips)

    def test_merged_pr_shows_only_merged(self) -> None:
        data = sample_data.sample_data()
        data["pr"]["state"] = "MERGED"
        self.assertEqual(render.status_chips(data), [("ok", "Merged")])


class RenderTest(unittest.TestCase):
    def test_renders_every_section_in_order(self) -> None:
        page = render.render(sample_data.sample_data())
        self.assertTrue(page.startswith("<title>Widgets PR 7 Briefing</title>"))
        self.assertNotIn("{{", page)
        positions = [
            page.index(f'<section id="{section}">')
            for section in (
                "summary",
                "map",
                "architecture",
                "changes",
                "files",
                "tests",
                "review",
            )
        ]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('<a href="#architecture">How it fits</a>', page)
        self.assertIn(
            '<p class="lede">Adds a <code>providers</code> module. '
            "<b>Needs a rebase.</b></p>",
            page,
        )
        self.assertIn('<article class="file" id="f-src-app-providers-py"', page)
        self.assertIn('<span class="badge new">new</span>', page)
        self.assertIn('<span class="fprev">from docs/old-guide.md</span>', page)
        self.assertIn('<pre class="snip">class Provider:\n    pass</pre>', page)
        self.assertIn('<span class="sev blocker">Blocks merge</span>', page)
        self.assertIn('<span class="sev info">Naming</span>', page)
        self.assertIn('<span class="conf">Confirmed</span>', page)
        self.assertIn('<rect class="svg-box"/>', page)

    def test_files_json_is_parseable_and_cannot_close_its_script(self) -> None:
        data = sample_data.sample_data()
        data["files"][1]["path"] = "src/</script><b>.py"
        data["briefing"]["files"]["src/</script><b>.py"] = {"gist": "x"}
        del data["briefing"]["files"]["src/app/cli.py"]
        page = render.render(data)
        match = re.search(
            r'<script type="application/json" id="pr-brief-files">(.*?)</script>',
            page,
            re.S,
        )
        self.assertIsNotNone(match)
        payload = json.loads(match.group(1))
        self.assertEqual(payload["files"][1]["p"], "src/</script><b>.py")
        self.assertEqual(payload["colors"]["code"], "var(--cat-1)")
        self.assertIn("src/&lt;/script&gt;&lt;b&gt;.py", page)

    def test_empty_optional_sections_are_omitted(self) -> None:
        data = sample_data.sample_data()
        for key in ("summary", "at_a_glance", "figures", "behavior_changes"):
            data["briefing"][key] = []
        data["briefing"]["tests"] = {"note": "", "rows": [], "gaps": []}
        data["briefing"]["review_notes"] = []
        page = render.render(data)
        for section in ("summary", "changes", "tests", "review"):
            self.assertNotIn(f'<section id="{section}">', page)
        self.assertIn('<section id="map">', page)
        self.assertIn('<section id="files">', page)

    def test_missing_gist_renders_placeholder(self) -> None:
        data = sample_data.sample_data()
        data["briefing"]["files"]["src/app/cli.py"]["gist"] = ""
        page = render.render(data)
        self.assertIn("No summary written for this file.", page)

    def test_standalone_format_wraps_document(self) -> None:
        page = render.render(sample_data.sample_data(), output_format="standalone")
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertTrue(page.rstrip().endswith("</html>"))

    def test_invalid_data_raises(self) -> None:
        data = sample_data.sample_data()
        data["briefing"]["review_notes"][0]["severity"] = "urgent"
        with self.assertRaises(render.BriefingError):
            render.render(data)
        with self.assertRaises(render.BriefingError):
            render.render(sample_data.sample_data(), output_format="pdf")


if __name__ == "__main__":
    unittest.main()
