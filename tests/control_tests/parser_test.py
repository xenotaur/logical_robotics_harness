import datetime
import tempfile
import unittest
from pathlib import Path

import yaml

from lrh.control import frontmatter_lint, parser
from lrh.control.parser import parse_markdown_file, parse_markdown_text


class TestControlParser(unittest.TestCase):
    def test_parse_markdown_text_frontmatter_and_body(self) -> None:
        parsed = parse_markdown_text("""---
id: SAMPLE
contributors: []
items:
  - one
  - two
status: active
---

# Body

Hello.
""")

        self.assertEqual(parsed.frontmatter["id"], "SAMPLE")
        self.assertEqual(parsed.frontmatter["contributors"], [])
        self.assertEqual(parsed.frontmatter["items"], ["one", "two"])
        self.assertEqual(parsed.body, "\n# Body\n\nHello.\n")

    def test_parse_markdown_text_accepts_closing_delimiter_at_eof(self) -> None:
        parsed = parse_markdown_text("---\nid: EOF\n---")

        self.assertEqual(parsed.frontmatter["id"], "EOF")
        self.assertEqual(parsed.body, "")

    def test_parse_empty_scalar_as_null(self) -> None:
        parsed = parse_markdown_text("---\ngithub:\ndescription:\n---\n")

        self.assertIsNone(parsed.frontmatter["github"])
        self.assertIsNone(parsed.frontmatter["description"])

    def test_parse_markdown_file_reads_from_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.md"
            path.write_text("---\nid: TEST\n---\nbody\n", encoding="utf-8")

            parsed = parse_markdown_file(path)

            self.assertEqual(parsed.frontmatter["id"], "TEST")
            self.assertEqual(parsed.body, "body\n")

    def test_unindented_comment_in_block_list_is_skipped(self) -> None:
        # Bug: unindented comment caused premature list termination (silent data loss).
        parsed = parse_markdown_text("---\nitems:\n  - one\n# comment\n  - two\n---\n")
        self.assertEqual(parsed.frontmatter["items"], ["one", "two"])

    def test_indented_comment_in_block_list_is_skipped(self) -> None:
        # Bug: indented comment raised ValueError("unsupported nested mapping").
        parsed = parse_markdown_text(
            "---\nitems:\n  - one\n  # comment\n  - two\n---\n"
        )
        self.assertEqual(parsed.frontmatter["items"], ["one", "two"])

    def test_multiple_comments_in_block_list_are_all_skipped(self) -> None:
        parsed = parse_markdown_text(
            "---\nitems:\n  - one\n# first\n  # second\n  - two\n  - three\n---\n"
        )
        self.assertEqual(parsed.frontmatter["items"], ["one", "two", "three"])

    def test_comment_only_block_list_yields_null(self) -> None:
        # A block list with only comments and no items parses as null (same as empty).
        parsed = parse_markdown_text("---\nitems:\n# comment only\n---\n")
        self.assertIsNone(parsed.frontmatter["items"])

    def test_created_at_parses_as_datetime(self) -> None:
        # Real YAML resolves an ISO-8601-looking scalar to a datetime, not
        # a str -- consumers must handle this explicitly (Decision 2).
        parsed = parse_markdown_text(
            "---\ncreated_at: 2026-08-02T15:14:34-04:00\n---\n"
        )
        self.assertIsInstance(parsed.frontmatter["created_at"], datetime.datetime)

    def test_colon_collapsed_list_item_parses_as_mapping(self) -> None:
        # An unquoted "key: value"-shaped bullet is valid YAML, but it
        # collapses into a one-entry mapping rather than the plain string
        # the author intended -- this is real YAML behavior, not a parser
        # bug, and callers must detect it (see validator's
        # _check_list_field_items_are_strings).
        parsed = parse_markdown_text(
            "---\nacceptance:\n  - plain bullet\n"
            "  - after sequencing: this collapses\n---\n"
        )
        self.assertEqual(parsed.frontmatter["acceptance"][0], "plain bullet")
        self.assertEqual(
            parsed.frontmatter["acceptance"][1], {"after sequencing": "this collapses"}
        )

    def test_reserved_indicator_scalar_raises_value_error(self) -> None:
        # A plain scalar cannot start with a reserved indicator character
        # (backtick) -- this is a hard YAML syntax error, wrapped as
        # ValueError per PROP-LRH-FRONTMATTER-PARSER Decision 1.
        with self.assertRaises(ValueError):
            parse_markdown_text("---\ntitle: `lrh validate` is broken\n---\n")

    def test_comment_between_multiple_block_lists(self) -> None:
        # Bug: col-0 comment inside foo's list broke the inner loop early,
        # leaving "- b" for the outer loop which raised ValueError.
        parsed = parse_markdown_text(
            "---\nfoo:\n  - a\n# comment\n  - b\nbar:\n  - c\n---\n"
        )
        self.assertEqual(parsed.frontmatter["foo"], ["a", "b"])
        self.assertEqual(parsed.frontmatter["bar"], ["c"])


_REPO_PROJECT = Path(__file__).resolve().parents[2] / "project"


class TestFastSafeLoad(unittest.TestCase):
    """libyaml parsing is an optimization only: results and errors are unchanged."""

    def test_every_control_file_parses_the_same_as_safe_load(self) -> None:
        files = sorted(_REPO_PROJECT.glob("**/*.md"))
        self.assertGreater(len(files), 100)
        for path in files:
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---\n"):
                continue
            try:
                frontmatter, _body = parser.split_frontmatter_and_body(text)
            except ValueError:
                continue
            with self.subTest(path=str(path.relative_to(_REPO_PROJECT))):
                try:
                    expected = yaml.safe_load(frontmatter)
                except yaml.YAMLError:
                    continue
                self.assertEqual(parser.safe_load_fast(frontmatter), expected)

    def test_syntax_errors_keep_the_pure_python_message(self) -> None:
        for text in ("title: [unclosed\n", "a: 1\n\tb: tab\n", "a: b: c\n"):
            with self.subTest(text=text):
                with self.assertRaises(yaml.YAMLError) as expected:
                    yaml.safe_load(text)
                with self.assertRaises(ValueError) as actual:
                    parser.load_yaml_document(text)
                self.assertEqual(
                    str(actual.exception),
                    f"invalid YAML in frontmatter: {expected.exception}",
                )

    def test_text_the_loaders_disagree_on_matches_safe_load(self) -> None:
        # libyaml accepts or parses each of these differently from the pure
        # loader; found by fuzzing the two against each other.
        for text in (
            "a: b\t\n",
            "status:\tactive\n",
            "a: !\n",
            "a: |#\n  x\n",
            "a: >#\n",
            "\ufeffa: 1\n",
            "a: 1\r\nb: 2\r\n",
            "a: x\x85b: y\n",
            "a: x\u2028y\n",
            "a: \udcff\n",
        ):
            with self.subTest(text=text):
                try:
                    expected = ("ok", yaml.safe_load(text))
                except (yaml.YAMLError, ValueError) as error:
                    expected = ("error", type(error), str(error))
                try:
                    actual = ("ok", parser.safe_load_fast(text))
                except (yaml.YAMLError, ValueError) as error:
                    actual = ("error", type(error), str(error))
                self.assertEqual(actual, expected)

    def test_falls_back_without_libyaml(self) -> None:
        original = parser._FAST_SAFE_LOADER
        parser._FAST_SAFE_LOADER = yaml.SafeLoader
        self.addCleanup(setattr, parser, "_FAST_SAFE_LOADER", original)
        # Lint memoizes scalar kinds; keep this loader's results out of it.
        self.addCleanup(frontmatter_lint._resolved_kind.cache_clear)

        self.assertEqual(parser.safe_load_fast("a: [1, two]\n"), {"a": [1, "two"]})
        with self.assertRaises(yaml.YAMLError):
            parser.safe_load_fast("title: [unclosed\n")


if __name__ == "__main__":
    unittest.main()
