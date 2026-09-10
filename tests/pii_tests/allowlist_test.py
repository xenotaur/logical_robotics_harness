import pathlib
import tempfile
import unittest

from lrh.pii import allowlist as pii_allowlist


class ComputeFingerprintTest(unittest.TestCase):
    def test_same_inputs_produce_the_same_fingerprint(self) -> None:
        first = pii_allowlist.compute_fingerprint("a.txt", "email.basic", "deadbeef")
        second = pii_allowlist.compute_fingerprint("a.txt", "email.basic", "deadbeef")

        self.assertEqual(first, second)

    def test_different_content_digest_produces_a_different_fingerprint(self) -> None:
        approved = pii_allowlist.compute_fingerprint("a.txt", "email.basic", "deadbeef")
        different_value = pii_allowlist.compute_fingerprint(
            "a.txt", "email.basic", "cafef00d"
        )

        # This is the whole point of a content-bound fingerprint: approving
        # one value at a path/rule must not silently approve a different,
        # genuinely sensitive value later found at that same path/rule
        # (PR #591 review, chatgpt-codex-connector).
        self.assertNotEqual(approved, different_value)

    def test_different_path_or_rule_produces_a_different_fingerprint(self) -> None:
        base = pii_allowlist.compute_fingerprint("a.txt", "email.basic", "deadbeef")
        different_path = pii_allowlist.compute_fingerprint(
            "b.txt", "email.basic", "deadbeef"
        )
        different_rule = pii_allowlist.compute_fingerprint(
            "a.txt", "ssn.us", "deadbeef"
        )

        self.assertNotEqual(base, different_path)
        self.assertNotEqual(base, different_rule)


class LoadAllowlistTest(unittest.TestCase):
    def test_returns_empty_set_when_no_allowlist_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            allowlist = pii_allowlist.load_allowlist(pathlib.Path(tmp))

            self.assertEqual(allowlist, frozenset())

    def test_parses_fingerprints_ignoring_blank_and_comment_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            (project_root / pii_allowlist.ALLOWLIST_FILENAME).write_text(
                "deadbeef\n"
                "\n"
                "# a full-line comment\n"
                "cafef00d  # reason: known test fixture\n"
            )

            allowlist = pii_allowlist.load_allowlist(project_root)

            self.assertEqual(allowlist, frozenset({"deadbeef", "cafef00d"}))


class IsAllowlistedTest(unittest.TestCase):
    def test_present_fingerprint_is_allowlisted(self) -> None:
        self.assertTrue(
            pii_allowlist.is_allowlisted("deadbeef", frozenset({"deadbeef"}))
        )

    def test_absent_fingerprint_is_not_allowlisted(self) -> None:
        self.assertFalse(
            pii_allowlist.is_allowlisted("cafef00d", frozenset({"deadbeef"}))
        )

    def test_empty_allowlist_suppresses_nothing(self) -> None:
        self.assertFalse(pii_allowlist.is_allowlisted("deadbeef", frozenset()))


if __name__ == "__main__":
    unittest.main()
