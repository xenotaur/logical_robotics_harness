"""Synthetic briefing data shared by the pr_brief tests."""

from __future__ import annotations

import copy
from typing import Any

from lrh.pr_brief import gather

_FILES = [
    {
        "path": "src/app/providers.py",
        "status": "added",
        "additions": 120,
        "deletions": 0,
        "previous_path": "",
        "category": "code",
    },
    {
        "path": "src/app/cli.py",
        "status": "modified",
        "additions": 30,
        "deletions": 4,
        "previous_path": "",
        "category": "code",
    },
    {
        "path": "tests/providers_test.py",
        "status": "added",
        "additions": 90,
        "deletions": 0,
        "previous_path": "",
        "category": "tests",
    },
    {
        "path": "docs/guide.md",
        "status": "renamed",
        "additions": 5,
        "deletions": 2,
        "previous_path": "docs/old-guide.md",
        "category": "docs",
    },
]


def sample_data() -> dict[str, Any]:
    """Return a fully populated, valid briefing document."""
    files = copy.deepcopy(_FILES)
    briefing = gather.empty_briefing(files)
    briefing.update(
        {
            "title": "Provider support for Example",
            "headline_summary": "Adds a `providers` module. **Needs a rebase.**",
            "summary": ["First paragraph.", "Second paragraph."],
            "at_a_glance": [{"label": "Kind", "value": "Feature"}],
            "figures": [
                {
                    "id": "architecture",
                    "nav": "How it fits",
                    "eyebrow": "Architecture",
                    "title": "How the pieces fit",
                    "intro": "Boxes and arrows.",
                    "html": '<svg viewBox="0 0 10 10"><rect class="svg-box"/></svg>',
                    "caption": "Teal is new.",
                }
            ],
            "behavior_changes": [
                {"what": "Listing", "before": "Old output.", "after": "New output."}
            ],
            "tests": {
                "note": "Tests were not run.",
                "rows": [
                    {
                        "behavior": "Config validation",
                        "where": "tests/providers_test.py",
                        "how": "unit",
                        "tone": "accent",
                    }
                ],
                "gaps": ["The CLI handler."],
            },
            "review_notes": [
                {
                    "severity": "blocker",
                    "title": "One merge conflict",
                    "body": ["Keep both sides."],
                    "where": "src/app/cli.py",
                    "confidence": "confirmed",
                },
                {
                    "severity": "info",
                    "label": "Naming",
                    "title": "A shadowed built-in",
                    "body": "Rename it.",
                },
            ],
            "footer_note": "Based on the full diff.",
        }
    )
    briefing["files"]["src/app/providers.py"] = {
        "gist": "The new module.",
        "points": ["Defines `Provider`."],
        "snippet": "class Provider:\n    pass",
    }
    for path in ("src/app/cli.py", "tests/providers_test.py", "docs/guide.md"):
        briefing["files"][path]["gist"] = f"Changes to {path}."
    return {
        "schema_version": gather.SCHEMA_VERSION,
        "generated_at": "2026-11-23T12:00:00+00:00",
        "pr": {
            "repo": "example/widgets",
            "number": 7,
            "url": "https://github.com/example/widgets/pull/7",
            "title": "Add providers",
            "author_login": "octo",
            "author_name": "Octo Cat",
            "state": "OPEN",
            "is_draft": False,
            "base": "main",
            "head": "add-providers",
            "base_sha": "a" * 40,
            "base_sha_is_tip": True,
            "head_sha": "b" * 40,
            "created_at": "2026-11-01T10:00:00Z",
            "updated_at": "2026-11-02T10:00:00Z",
            "additions": 245,
            "deletions": 6,
            "changed_files": 4,
            "commits": [{"sha": "b" * 12, "headline": "Add providers"}],
            "labels": [],
            "body": "",
        },
        "status": {
            "mergeable": "CONFLICTING",
            "merge_state": "DIRTY",
            "checks": {"total": 0, "passing": 0, "failing": 0, "pending": 0},
            "reviews": {
                "decision": "",
                "count": 0,
                "approvals": 0,
                "changes_requested": 0,
                "comments": 0,
            },
            "ahead_by": 1,
            "behind_by": 16,
            "merge_base_sha": "c" * 40,
            "merge_base_date": "2026-08-01T00:00:00Z",
            "conflicts": {"checked": True, "clean": False, "files": ["src/app/cli.py"]},
        },
        "categories": [dict(category) for category in gather.CATEGORIES],
        "files": files,
        "briefing": briefing,
    }
