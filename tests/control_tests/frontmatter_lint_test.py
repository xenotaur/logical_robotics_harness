import unittest

from lrh.control import frontmatter_lint


class TestUnescapedColon(unittest.TestCase):
    def test_list_item_colon_collapse(self) -> None:
        text = "acceptance:\n  - a bullet: with an unquoted colon\n"
        findings = frontmatter_lint.iter_unsafe_scalars(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category, frontmatter_lint.CATEGORY_UNESCAPED_COLON
        )
        self.assertEqual(findings[0].field, "acceptance")
        self.assertEqual(findings[0].line, 2)

    def test_list_item_in_unknown_field_not_flagged(self) -> None:
        # "- key: value" under a field this module doesn't know is meant
        # to hold plain strings is just as likely to be a genuine YAML
        # mapping entry (e.g. someone else's "steps:" list) as it is
        # colon-collapsed prose -- never rewrite a shape that could be
        # real structure.
        text = "steps:\n  - name: test\n"
        self.assertEqual(frontmatter_lint.iter_unsafe_scalars(text), [])

    def test_scalar_field_mid_value_colon(self) -> None:
        text = "title: Some Title: With Colon\n"
        findings = frontmatter_lint.iter_unsafe_scalars(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category, frontmatter_lint.CATEGORY_UNESCAPED_COLON
        )

    def test_quoted_colon_is_safe(self) -> None:
        text = 'title: "Some Title: With Colon"\n'
        self.assertEqual(frontmatter_lint.iter_unsafe_scalars(text), [])


class TestUnescapedHash(unittest.TestCase):
    def test_mid_scalar_hash(self) -> None:
        text = "instruction_source: discovered verifying PR #531\n"
        findings = frontmatter_lint.iter_unsafe_scalars(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, frontmatter_lint.CATEGORY_UNESCAPED_HASH)

    def test_leading_hash_is_reserved_indicator_not_hash(self) -> None:
        text = "title: #starts with hash\n"
        findings = frontmatter_lint.iter_unsafe_scalars(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category, frontmatter_lint.CATEGORY_RESERVED_INDICATOR
        )

    def test_quoted_hash_is_safe(self) -> None:
        text = "instruction_source: 'discovered verifying PR #531'\n"
        self.assertEqual(frontmatter_lint.iter_unsafe_scalars(text), [])


class TestReservedIndicator(unittest.TestCase):
    def test_backtick_leading_scalar(self) -> None:
        text = "title: `lrh validate` is broken\n"
        findings = frontmatter_lint.iter_unsafe_scalars(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].category, frontmatter_lint.CATEGORY_RESERVED_INDICATOR
        )

    def test_flow_sequence_is_not_flagged(self) -> None:
        text = "evidence: []\nimplemented_by: [WI-A, WI-B]\n"
        self.assertEqual(frontmatter_lint.iter_unsafe_scalars(text), [])

    def test_flow_mapping_is_not_flagged(self) -> None:
        text = "meta: {}\n"
        self.assertEqual(frontmatter_lint.iter_unsafe_scalars(text), [])


class TestImplicitNonStringType(unittest.TestCase):
    def test_numeric_commit_hash_flagged(self) -> None:
        text = "commit: 7926567\n"
        findings = frontmatter_lint.iter_unsafe_scalars(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, frontmatter_lint.CATEGORY_IMPLICIT_TYPE)

    def test_unknown_field_not_flagged(self) -> None:
        # A numeric-looking value in a field not in KNOWN_STRING_FIELDS is
        # not this check's business -- conservative by design.
        text = "some_unlisted_field: 7926567\n"
        self.assertEqual(frontmatter_lint.iter_unsafe_scalars(text), [])

    def test_created_at_datetime_not_flagged(self) -> None:
        # Accepted divergence per PROP-LRH-FRONTMATTER-PARSER Decision 2 --
        # created_at is deliberately excluded from KNOWN_STRING_FIELDS.
        text = "created_at: 2026-07-18T03:15:20-04:00\n"
        self.assertEqual(frontmatter_lint.iter_unsafe_scalars(text), [])

    def test_null_value_not_flagged_by_default(self) -> None:
        # Most KNOWN_STRING_FIELDS members legitimately use null (owner,
        # commit, pr, rerun_of, blocked_reason, resolution, ...).
        for field in ("resolution", "blocked_reason", "rerun_of", "owner", "commit"):
            with self.subTest(field=field):
                text = f"{field}: null\n"
                self.assertEqual(frontmatter_lint.iter_unsafe_scalars(text), [])

    def test_null_value_flagged_for_non_nullable_string_fields(self) -> None:
        # A literal "null" in a field that should never actually be null
        # (e.g. title) almost certainly means the author typed literal
        # text, not an intentional absence.
        text = "title: null\n"
        findings = frontmatter_lint.iter_unsafe_scalars(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, frontmatter_lint.CATEGORY_IMPLICIT_TYPE)

    def test_bool_value_flagged(self) -> None:
        text = "resolution: true\n"
        findings = frontmatter_lint.iter_unsafe_scalars(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, frontmatter_lint.CATEGORY_IMPLICIT_TYPE)


class TestBlockScalarsAreOutOfScope(unittest.TestCase):
    def test_folded_scalar_body_not_scanned(self) -> None:
        text = (
            "summary: >\n"
            "  This line has an unquoted colon: right here\n"
            "  and a hash # too\n"
        )
        self.assertEqual(frontmatter_lint.iter_unsafe_scalars(text), [])

    def test_comment_lines_skipped(self) -> None:
        text = "# a top-level comment with `backtick` and #hash\ntitle: fine\n"
        self.assertEqual(frontmatter_lint.iter_unsafe_scalars(text), [])


if __name__ == "__main__":
    unittest.main()
