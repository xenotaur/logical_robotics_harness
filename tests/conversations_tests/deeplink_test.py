import json
import re
import unittest
from importlib import resources
from unittest import mock

from lrh.conversations import claude_session, codex_session, deeplink

CLAUDE_UUID = "a6e3e7d1-6dca-4a75-999f-73b646ceb1fa"
CODEX_UUID = "01a032cd-cef2-73c0-9714-b61b36ae4513"


def _vectors() -> dict:
    return deeplink.load_definition()["vectors"]


class TestSharedVectors(unittest.TestCase):
    """The accept and reject vectors are shared with the Console allowlist."""

    def test_accept_vectors_build_the_expected_link(self) -> None:
        for vector in _vectors()["accept"]:
            with self.subTest(pointer=vector["pointer"]):
                self.assertEqual(
                    deeplink.link_for(vector["pointer"]),
                    vector["link"],
                )

    def test_accept_links_are_session_links(self) -> None:
        for vector in _vectors()["accept"]:
            with self.subTest(link=vector["link"]):
                self.assertTrue(deeplink.is_session_link(vector["link"]))

    def test_reject_pointers_have_no_link(self) -> None:
        for pointer in _vectors()["reject_pointers"]:
            with self.subTest(pointer=pointer):
                self.assertIsNone(deeplink.link_for(pointer))

    def test_reject_links_are_not_session_links(self) -> None:
        for link in _vectors()["reject_links"]:
            with self.subTest(link=link):
                self.assertFalse(deeplink.is_session_link(link))

    def test_every_built_link_passes_the_link_check(self) -> None:
        for vector in _vectors()["accept"]:
            link = deeplink.link_for(vector["pointer"])
            self.assertIsNotNone(link)
            self.assertTrue(deeplink.is_session_link(link))


class TestLinkFor(unittest.TestCase):
    def test_claude_pointer_gets_the_local_prefix(self) -> None:
        self.assertEqual(
            deeplink.link_for(f"claude-app:{CLAUDE_UUID}"),
            f"claude://claude.ai/epitaxy/local_{CLAUDE_UUID}",
        )

    def test_local_prefix_is_added_exactly_once(self) -> None:
        link = deeplink.link_for(f"claude-app:local_{CLAUDE_UUID}")
        self.assertEqual(link, f"claude://claude.ai/epitaxy/local_{CLAUDE_UUID}")
        self.assertEqual(link.count("local_"), 1)
        self.assertIsNone(deeplink.link_for(f"claude-app:local_local_{CLAUDE_UUID}"))

    def test_codex_pointer_builds_a_thread_link(self) -> None:
        self.assertEqual(
            deeplink.link_for(f"codex-app:{CODEX_UUID}"),
            f"codex://threads/{CODEX_UUID}",
        )

    def test_codex_pointer_does_not_take_a_claude_prefix(self) -> None:
        self.assertIsNone(deeplink.link_for(f"codex-app:local_{CODEX_UUID}"))

    def test_id_case_is_preserved_not_normalized(self) -> None:
        upper = CLAUDE_UUID.upper()
        self.assertEqual(
            deeplink.link_for(f"claude-app:{upper}"),
            f"claude://claude.ai/epitaxy/local_{upper}",
        )

    def test_antigravity_has_no_link(self) -> None:
        self.assertIsNone(deeplink.link_for(f"antigravity-app:{CLAUDE_UUID}"))

    def test_sentinels_and_junk_have_no_link(self) -> None:
        for pointer in ("", "pending", "none", "claude-app", ":", "x:y"):
            with self.subTest(pointer=pointer):
                self.assertIsNone(deeplink.link_for(pointer))

    def test_non_string_input_has_no_link(self) -> None:
        for value in (None, 7, b"claude-app:x", ["claude-app:x"]):
            with self.subTest(value=value):
                self.assertIsNone(deeplink.link_for(value))  # type: ignore[arg-type]

    def test_the_helper_cannot_tell_host_ids_from_child_ids(self) -> None:
        # Both are bare UUIDs; only the session index distinguishes them, so
        # the invariant lives on the producer side (see the module docstring).
        child_id = "ca300163-96b7-4242-8194-63f72bba4697"
        self.assertIsNotNone(deeplink.link_for(f"claude-app:{child_id}"))


class TestDefinition(unittest.TestCase):
    def test_pointer_prefixes_match_the_session_modules(self) -> None:
        prefixes = {
            route.name: route.pointer_prefix for route in deeplink.load_routes()
        }
        self.assertEqual(
            prefixes["claude-app"], claude_session.CLAUDE_SESSION_TRANSCRIPT_PREFIX
        )
        self.assertEqual(
            prefixes["codex-app"], codex_session.CODEX_SESSION_TRANSCRIPT_PREFIX
        )

    def test_unsupported_vendors_are_not_routes(self) -> None:
        routed = {route.pointer_prefix for route in deeplink.load_routes()}
        for entry in deeplink.load_definition()["unsupported"]:
            self.assertNotIn(entry["pointer_prefix"], routed)

    def test_route_statuses_are_recorded(self) -> None:
        statuses = {route.name: route.status for route in deeplink.load_routes()}
        self.assertEqual(statuses, {"claude-app": "verified", "codex-app": "verified"})

    def test_definition_is_flat_json_the_rust_side_can_parse(self) -> None:
        text = (
            resources.files("lrh.conversations")
            .joinpath(deeplink.DEFINITION_RESOURCE)
            .read_text(encoding="utf-8")
        )
        definition = json.loads(text)
        self.assertEqual(definition["schema_version"], 1)

        def only_plain_json(value: object) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    self.assertIsInstance(key, str)
                    only_plain_json(item)
            elif isinstance(value, list):
                for item in value:
                    only_plain_json(item)
            else:
                self.assertIsInstance(value, (str, int))

        only_plain_json(definition)

    def test_link_patterns_are_anchored_to_their_own_vendor(self) -> None:
        patterns = {
            route.name: route.link_pattern() for route in deeplink.load_routes()
        }
        claude_link = f"claude://claude.ai/epitaxy/local_{CLAUDE_UUID}"
        codex_link = f"codex://threads/{CODEX_UUID}"
        self.assertIsNotNone(patterns["claude-app"].fullmatch(claude_link))
        self.assertIsNone(patterns["claude-app"].fullmatch(codex_link))
        self.assertIsNotNone(patterns["codex-app"].fullmatch(codex_link))
        self.assertIsNone(patterns["codex-app"].fullmatch(claude_link))
        self.assertIsInstance(patterns["codex-app"], re.Pattern)


class TestDefinitionErrors(unittest.TestCase):
    def setUp(self) -> None:
        deeplink.load_definition.cache_clear()
        deeplink.load_routes.cache_clear()
        self.addCleanup(deeplink.load_definition.cache_clear)
        self.addCleanup(deeplink.load_routes.cache_clear)

    def _with_definition(self, definition: object) -> mock._patch:
        return mock.patch.object(
            deeplink.resources,
            "files",
            return_value=_FakeResource(json.dumps(definition)),
        )

    def test_malformed_json_is_a_definition_error(self) -> None:
        with mock.patch.object(
            deeplink.resources, "files", return_value=_FakeResource("{not json")
        ):
            with self.assertRaises(deeplink.SessionLinkDefinitionError):
                deeplink.load_definition()

    def test_missing_vendors_list_is_a_definition_error(self) -> None:
        with self._with_definition({"schema_version": 1}):
            with self.assertRaises(deeplink.SessionLinkDefinitionError):
                deeplink.load_definition()

    def test_vendor_entry_missing_a_field_is_a_definition_error(self) -> None:
        with self._with_definition({"vendors": [{"name": "x"}]}):
            with self.assertRaises(deeplink.SessionLinkDefinitionError):
                deeplink.load_routes()

    def test_route_without_an_id_placeholder_is_a_definition_error(self) -> None:
        entry = {
            "name": "x",
            "pointer_prefix": "x-app:",
            "scheme": "x",
            "host": "h",
            "path_template": "/fixed",
            "id_prefix": "",
            "id_shape": "uuid",
            "status": "verified",
        }
        with self._with_definition({"vendors": [entry]}):
            with self.assertRaises(deeplink.SessionLinkDefinitionError):
                deeplink.load_routes()


class _FakeResource:
    def __init__(self, text: str) -> None:
        self._text = text

    def joinpath(self, _name: str) -> "_FakeResource":
        return self

    def read_text(self, encoding: str = "utf-8") -> str:
        return self._text


if __name__ == "__main__":
    unittest.main()
