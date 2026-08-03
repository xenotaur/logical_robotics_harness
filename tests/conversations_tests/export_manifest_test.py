import unittest
from datetime import datetime, timezone

from lrh.conversations import (
    ConversationExportManifest,
    ConversationExportManifestError,
    TranscriptStatistics,
    build_codex_manifest,
    statistics_for_text,
)

SOURCE_SHA256 = "a" * 64
EXPORTED_AT = "2026-08-03T16:45:59+00:00"


class TestTranscriptStatistics(unittest.TestCase):
    def test_statistics_for_text_counts_bytes_characters_and_lines(self) -> None:
        statistics = statistics_for_text(
            "hello\nsnowman: \u2603", turn_count=2, message_count=3
        )

        self.assertEqual(statistics.byte_count, 18)
        self.assertEqual(statistics.character_count, 16)
        self.assertEqual(statistics.line_count, 2)
        self.assertEqual(statistics.turn_count, 2)
        self.assertEqual(statistics.message_count, 3)

    def test_rejects_negative_statistics(self) -> None:
        with self.assertRaisesRegex(ConversationExportManifestError, "byte_count"):
            TranscriptStatistics(byte_count=-1, character_count=1, line_count=1)


class TestConversationExportManifest(unittest.TestCase):
    def test_build_codex_manifest_uses_private_non_authoritative_defaults(self) -> None:
        manifest = build_codex_manifest(
            transcript_text="hello",
            source_sha256=SOURCE_SHA256,
            exported_at=EXPORTED_AT,
        )

        mapping = manifest.to_mapping()

        self.assertEqual(mapping["kind"], "lrh_codex_conversation_export")
        self.assertEqual(mapping["schema_version"], 1)
        self.assertEqual(mapping["source_tool"], "codex")
        self.assertEqual(mapping["source_adapter"], "codex_manual_export")
        self.assertEqual(mapping["privacy"], "private")
        self.assertEqual(mapping["authority"], "non_authoritative_context")
        self.assertEqual(mapping["sensitivity"], "unscanned")
        self.assertEqual(mapping["sensitivity_scan"], {"status": "not_scanned"})
        self.assertEqual(mapping["source_sha256"], SOURCE_SHA256)
        self.assertEqual(mapping["exported_at"], EXPORTED_AT)
        self.assertEqual(mapping["adapter_version"], 1)
        self.assertEqual(mapping["warnings"], [])
        self.assertEqual(
            mapping["transcript_statistics"],
            {"byte_count": 5, "character_count": 5, "line_count": 1},
        )

    def test_accepts_timezone_aware_datetime_export_timestamp(self) -> None:
        manifest = build_codex_manifest(
            transcript_text="hello",
            source_sha256=SOURCE_SHA256,
            exported_at=datetime(2026, 8, 3, 16, 45, 59, tzinfo=timezone.utc),
        )

        self.assertEqual(manifest.exported_at, EXPORTED_AT)

    def test_rejects_naive_datetime_export_timestamp(self) -> None:
        with self.assertRaisesRegex(ConversationExportManifestError, "timezone-aware"):
            build_codex_manifest(
                transcript_text="hello",
                source_sha256=SOURCE_SHA256,
                exported_at=datetime(2026, 8, 3, 16, 45, 59),
            )

    def test_round_trips_from_mapping_with_sensitivity_and_warnings(self) -> None:
        manifest = ConversationExportManifest.from_mapping(
            {
                "kind": "lrh_codex_conversation_export",
                "schema_version": 1,
                "source_tool": "codex",
                "source_adapter": "codex_file_import",
                "privacy": "private",
                "authority": "non_authoritative_context",
                "sensitivity": "potential",
                "sensitivity_scan": {
                    "status": "scanned",
                    "scanner": "lrh_builtin_sensitive_scan",
                    "scanner_version": 1,
                    "finding_count": 1,
                    "categories": ["email"],
                },
                "source_id": "codex-thread-123",
                "source_sha256": SOURCE_SHA256,
                "exported_at": EXPORTED_AT,
                "adapter_version": 2,
                "warnings": ["turn_boundaries_not_inferred"],
                "transcript_statistics": {
                    "byte_count": 20,
                    "character_count": 20,
                    "line_count": 3,
                    "turn_count": 2,
                    "message_count": 4,
                },
            }
        )

        self.assertEqual(manifest.source_adapter, "codex_file_import")
        self.assertEqual(manifest.sensitivity, "potential")
        self.assertEqual(manifest.source_id, "codex-thread-123")
        self.assertEqual(manifest.adapter_version, 2)
        self.assertEqual(manifest.warnings, ("turn_boundaries_not_inferred",))
        self.assertEqual(manifest.transcript_statistics.turn_count, 2)
        self.assertEqual(manifest.transcript_statistics.message_count, 4)

    def test_rejects_missing_required_field(self) -> None:
        mapping = _valid_mapping()
        del mapping["source_sha256"]

        with self.assertRaisesRegex(
            ConversationExportManifestError, "missing required field: source_sha256"
        ):
            ConversationExportManifest.from_mapping(mapping)

    def test_rejects_invalid_source_hash(self) -> None:
        with self.assertRaisesRegex(ConversationExportManifestError, "source_sha256"):
            build_codex_manifest(
                transcript_text="hello",
                source_sha256="not-a-sha",
                exported_at=EXPORTED_AT,
            )

    def test_rejects_public_privacy(self) -> None:
        mapping = _valid_mapping()
        mapping["privacy"] = "public"

        with self.assertRaisesRegex(ConversationExportManifestError, "privacy"):
            ConversationExportManifest.from_mapping(mapping)

    def test_rejects_non_codex_source_tool(self) -> None:
        mapping = _valid_mapping()
        mapping["source_tool"] = "chatgpt"

        with self.assertRaisesRegex(ConversationExportManifestError, "source_tool"):
            ConversationExportManifest.from_mapping(mapping)

    def test_serialized_frontmatter_is_stable(self) -> None:
        manifest = build_codex_manifest(
            transcript_text="hello\nworld",
            source_sha256=SOURCE_SHA256,
            exported_at=EXPORTED_AT,
            source_id="codex-thread-123",
            sensitivity="none_detected",
            sensitivity_scan={
                "categories": [],
                "finding_count": 0,
                "scanner_version": 1,
                "status": "scanned",
                "scanner": "lrh_builtin_sensitive_scan",
            },
            warnings=("turn_boundaries_not_inferred",),
            turn_count=2,
            message_count=2,
        )

        self.assertEqual(
            manifest.to_frontmatter(),
            """---
kind: "lrh_codex_conversation_export"
schema_version: 1
source_tool: "codex"
source_adapter: "codex_manual_export"
privacy: "private"
authority: "non_authoritative_context"
sensitivity: "none_detected"
sensitivity_scan:
  status: "scanned"
  scanner: "lrh_builtin_sensitive_scan"
  scanner_version: 1
  finding_count: 0
  categories: []
source_id: "codex-thread-123"
source_sha256: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
exported_at: "2026-08-03T16:45:59+00:00"
adapter_version: 1
warnings:
  - "turn_boundaries_not_inferred"
transcript_statistics:
  byte_count: 11
  character_count: 11
  line_count: 2
  turn_count: 2
  message_count: 2
---
""",
        )


def _valid_mapping() -> dict[str, object]:
    return {
        "kind": "lrh_codex_conversation_export",
        "schema_version": 1,
        "source_tool": "codex",
        "source_adapter": "codex_manual_export",
        "privacy": "private",
        "authority": "non_authoritative_context",
        "sensitivity": "unscanned",
        "sensitivity_scan": {"status": "not_scanned"},
        "source_sha256": SOURCE_SHA256,
        "exported_at": EXPORTED_AT,
        "adapter_version": 1,
        "warnings": [],
        "transcript_statistics": {
            "byte_count": 5,
            "character_count": 5,
            "line_count": 1,
        },
    }


if __name__ == "__main__":
    unittest.main()
