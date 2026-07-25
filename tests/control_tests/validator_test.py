import tempfile
import unittest
from pathlib import Path

from lrh.control.validator import validate_project


class TestControlValidator(unittest.TestCase):
    def _make_project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "contributors" / "agents").mkdir(parents=True)
        (root / "work_items" / "active").mkdir(parents=True)
        (root / "work_items" / "proposed").mkdir(parents=True)
        (root / "work_items" / "resolved").mkdir(parents=True)
        (root / "work_items" / "abandoned").mkdir(parents=True)
        (root / "focus").mkdir(parents=True)
        return root

    def _write(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _seed_valid_focus(self, root: Path) -> None:
        self._write(
            root / "focus" / "current_focus.md",
            """---
id: FOCUS-1
title: Focus
status: active
---

# Focus
""",
        )

    def test_valid_contributor_parsing(self) -> None:
        root = self._make_project()
        self._write(
            root / "contributors" / "human.md",
            """---
id: person-1
type: human
roles: [admin]
display_name: Person
status: active
---
""",
        )
        self._seed_valid_focus(root)

        report = validate_project(root)

        self.assertFalse(
            any(issue.code == "MISSING_REQUIRED_FIELD" for issue in report.issues)
        )

    def test_invalid_contributor_enum(self) -> None:
        root = self._make_project()
        self._write(
            root / "contributors" / "human.md",
            """---
id: person-1
type: cyborg
roles: [admin]
display_name: Person
status: active
---
""",
        )
        self._seed_valid_focus(root)

        report = validate_project(root)

        self.assertTrue(
            any(issue.code == "CONTRIBUTOR_TYPE_INVALID" for issue in report.issues)
        )

    def test_null_required_enum_is_invalid(self) -> None:
        root = self._make_project()
        self._write(
            root / "contributors" / "human.md",
            """---
id: person-1
type: human
roles: [admin]
display_name: Person
status: null
---
""",
        )
        self._seed_valid_focus(root)

        report = validate_project(root)

        self.assertTrue(
            any(issue.code == "CONTRIBUTOR_STATUS_INVALID" for issue in report.issues)
        )

    def test_duplicate_contributor_ids(self) -> None:
        root = self._make_project()
        contributor = """---
id: duplicate-id
type: human
roles: [admin]
display_name: Person
status: active
---
"""
        self._write(root / "contributors" / "a.md", contributor)
        self._write(root / "contributors" / "agents" / "b.md", contributor)
        self._seed_valid_focus(root)

        report = validate_project(root)

        self.assertTrue(
            any(issue.code == "DUPLICATE_CONTRIBUTOR_ID" for issue in report.issues)
        )

    def test_owner_unknown_contributor(self) -> None:
        root = self._make_project()
        self._write(
            root / "contributors" / "human.md",
            """---
id: person-1
type: human
roles: [admin]
display_name: Person
status: active
---
""",
        )
        self._seed_valid_focus(root)
        self._write(
            root / "work_items" / "active" / "WI-1.md",
            """---
id: WI-1
title: Task
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
owner: missing
---
""",
        )

        report = validate_project(root)

        self.assertTrue(any(issue.code == "UNKNOWN_OWNER" for issue in report.issues))

    def test_owner_referencing_agent_is_error(self) -> None:
        root = self._make_project()
        self._write(
            root / "contributors" / "agents" / "agent.md",
            """---
id: agent-1
type: agent
roles: [editor]
display_name: Agent
status: active
execution_mode: autonomous
---
""",
        )
        self._seed_valid_focus(root)
        self._write(
            root / "work_items" / "active" / "WI-1.md",
            """---
id: WI-1
title: Task
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
owner: agent-1
---
""",
        )

        report = validate_project(root)

        self.assertTrue(any(issue.code == "OWNER_NOT_HUMAN" for issue in report.issues))

    def test_assigned_agents_referencing_human_is_error(self) -> None:
        root = self._make_project()
        self._write(
            root / "contributors" / "human.md",
            """---
id: person-1
type: human
roles: [editor]
display_name: Person
status: active
---
""",
        )
        self._seed_valid_focus(root)
        self._write(
            root / "work_items" / "active" / "WI-1.md",
            """---
id: WI-1
title: Task
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
owner: person-1
assigned_agents:
  - person-1
---
""",
        )

        report = validate_project(root)

        self.assertTrue(
            any(issue.code == "ASSIGNED_AGENT_NOT_AGENT" for issue in report.issues)
        )

    def test_owner_missing_from_contributors_warns(self) -> None:
        root = self._make_project()
        self._write(
            root / "contributors" / "human.md",
            """---
id: person-1
type: human
roles: [editor]
display_name: Person
status: active
---
""",
        )
        self._seed_valid_focus(root)
        self._write(
            root / "work_items" / "active" / "WI-1.md",
            """---
id: WI-1
title: Task
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
owner: person-1
contributors: []
---
""",
        )

        report = validate_project(root)

        self.assertTrue(
            any(issue.code == "OWNER_NOT_IN_CONTRIBUTORS" for issue in report.warnings)
        )

    def test_assigned_human_orchestrated_agent_warns(self) -> None:
        root = self._make_project()
        self._write(
            root / "contributors" / "human.md",
            """---
id: owner-1
type: human
roles: [admin]
display_name: Owner
status: active
---
""",
        )
        self._write(
            root / "contributors" / "agents" / "agent.md",
            """---
id: agent-1
type: agent
roles: [editor]
display_name: Agent
status: inactive
execution_mode: human_orchestrated
---
""",
        )
        self._seed_valid_focus(root)
        self._write(
            root / "work_items" / "active" / "WI-1.md",
            """---
id: WI-1
title: Task
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
blocked: false
blocked_reason: null
resolution: null
owner: owner-1
contributors:
  - owner-1
assigned_agents:
  - agent-1
---
""",
        )

        report = validate_project(root)

        codes = {issue.code for issue in report.warnings}
        self.assertIn("ASSIGNED_AGENT_HUMAN_ORCHESTRATED", codes)
        self.assertIn("ASSIGNED_AGENT_INACTIVE", codes)

    def test_archived_focus_ids_can_be_referenced_by_work_items(self) -> None:
        root = self._make_project()
        self._seed_valid_focus(root)
        self._write(
            root / "focus" / "archive" / "2026" / "completed_focus.md",
            """---
id: FOCUS-ARCHIVED
title: Archived focus
status: completed
---

# Archived focus
""",
        )
        self._write(
            root / "work_items" / "resolved" / "WI-1.md",
            """---
id: WI-1
title: Historical task
type: deliverable
status: resolved
blocked: false
blocked_reason: null
resolution: Completed
related_focus:
  - FOCUS-ARCHIVED
---
""",
        )

        report = validate_project(root)

        self.assertFalse(
            any(issue.code == "UNKNOWN_RELATED_FOCUS" for issue in report.errors)
        )

    def test_valid_bootstrap_style_configuration(self) -> None:
        root = self._make_project()
        self._write(
            root / "contributors" / "human.md",
            """---
id: owner-1
type: human
roles: [admin, editor]
display_name: Owner
status: active
---
""",
        )
        self._write(
            root / "contributors" / "agents" / "agent.md",
            """---
id: agent-1
type: agent
roles: [editor]
display_name: Agent
status: active
execution_mode: human_orchestrated
---
""",
        )
        self._write(
            root / "focus" / "current_focus.md",
            """---
id: FOCUS-1
title: Focus
status: active
active_contributors:
  - owner-1
  - agent-1
---
""",
        )
        self._write(
            root / "work_items" / "active" / "WI-1.md",
            """---
id: WI-1
title: Task
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
owner: owner-1
contributors:
  - owner-1
  - agent-1
assigned_agents: []
related_focus:
  - FOCUS-1
depends_on: []
blocked_by: []
---
""",
        )

        report = validate_project(root)

        self.assertEqual(report.errors, [])


class TestExecutionRecordValidation(unittest.TestCase):
    """Stage 2 of PROP-LRH-EXECUTION-SESSIONS: advisory warnings for the
    optional session fields on execution records."""

    _INSTRUCTION_CODE = "EXECUTION_INSTRUCTION_SOURCE_ABSOLUTE_PATH"

    def _make_project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "focus").mkdir(parents=True)
        (root / "focus" / "current_focus.md").write_text(
            "---\nid: FOCUS-1\ntitle: Focus\nstatus: active\n---\n",
            encoding="utf-8",
        )
        return root

    def _write_record(self, root: Path, name: str, extra: str) -> None:
        path = root / "executions" / "AD_HOC" / f"{name}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n"
            f"execution_id: {name}\n"
            f"prompt_id: PROMPT(AD_HOC:{name.upper()})[2026-07-25T00:00:00-04:00]\n"
            "work_item: AD_HOC\n"
            "status: landed\n"
            f"{extra}"
            "created_at: 2026-07-25T00:00:00-04:00\n"
            "---\n\n# Summary\n\nTest record.\n",
            encoding="utf-8",
        )

    def _issues_for(self, root: Path, code_prefix: str) -> list:
        report = validate_project(root)
        return [issue for issue in report.issues if issue.code.startswith(code_prefix)]

    def test_valid_schemes_and_sentinels_do_not_warn(self) -> None:
        root = self._make_project()
        for name, value in [
            ("rec_claude", "claude-app:4c3d03d6-abc"),
            ("rec_codex", "codex-cloud:task-123"),
            ("rec_chatgpt", "chatgpt:conv-456"),
            ("rec_pending", "pending"),
            ("rec_none", "none"),
        ]:
            self._write_record(root, name, f"session_transcript: {value}\n")

        issues = self._issues_for(root, "EXECUTION_SESSION_TRANSCRIPT")

        self.assertEqual(issues, [])

    def test_absolute_path_transcript_warns(self) -> None:
        root = self._make_project()
        self._write_record(
            root, "rec_home", "session_transcript: ~/.claude/projects/x/a.jsonl\n"
        )
        self._write_record(root, "rec_abs", "session_transcript: /var/tmp/a.jsonl\n")
        self._write_record(
            root, "rec_win", "session_transcript: C:\\Users\\x\\a.jsonl\n"
        )

        issues = self._issues_for(root, "EXECUTION_SESSION_TRANSCRIPT")

        self.assertEqual(len(issues), 3)
        self.assertEqual(
            {issue.code for issue in issues},
            {"EXECUTION_SESSION_TRANSCRIPT_ABSOLUTE_PATH"},
        )
        self.assertEqual({issue.severity for issue in issues}, {"warning"})

    def test_bare_id_transcript_warns_malformed(self) -> None:
        root = self._make_project()
        self._write_record(root, "rec_bare", "session_transcript: bareid\n")

        issues = self._issues_for(root, "EXECUTION_SESSION_TRANSCRIPT")

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "EXECUTION_SESSION_TRANSCRIPT_MALFORMED")

    def test_sequence_all_valid_does_not_warn(self) -> None:
        root = self._make_project()
        self._write_record(
            root,
            "rec_seq_ok",
            "session_transcript: [claude-app:aaa, codex-cloud:bbb]\n",
        )

        issues = self._issues_for(root, "EXECUTION_SESSION_TRANSCRIPT")

        self.assertEqual(issues, [])

    def test_sequence_with_bad_element_warns(self) -> None:
        root = self._make_project()
        self._write_record(
            root,
            "rec_seq_bad",
            "session_transcript: [claude-app:aaa, bareid]\n",
        )

        issues = self._issues_for(root, "EXECUTION_SESSION_TRANSCRIPT")

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "EXECUTION_SESSION_TRANSCRIPT_MALFORMED")

    def test_absolute_instruction_source_warns(self) -> None:
        root = self._make_project()
        self._write_record(root, "rec_isrc_abs", "instruction_source: ~/prompts/a.md\n")

        issues = self._issues_for(root, self._INSTRUCTION_CODE)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, self._INSTRUCTION_CODE)
        self.assertEqual(issues[0].severity, "warning")

    def test_scheme_and_relative_instruction_source_do_not_warn(self) -> None:
        root = self._make_project()
        self._write_record(
            root,
            "rec_isrc_promptspace",
            "instruction_source: promptspace:Z. Completed Prompts/a.md\n",
        )
        self._write_record(
            root,
            "rec_isrc_relative",
            "instruction_source: project/work_items/proposed/WI-X.md\n",
        )

        issues = self._issues_for(root, self._INSTRUCTION_CODE)

        self.assertEqual(issues, [])

    def test_agent_is_open_ended_no_warning(self) -> None:
        root = self._make_project()
        for name, agent in [
            ("rec_agent_claude", "claude_app"),
            ("rec_agent_codex", "codex_cloud"),
            ("rec_agent_manual", "manual"),
            ("rec_agent_other", "some_future_backend"),
        ]:
            self._write_record(root, name, f"agent: {agent}\n")

        issues = self._issues_for(root, "EXECUTION_")

        self.assertEqual(issues, [])

    def test_readme_is_not_parsed_as_a_record(self) -> None:
        root = self._make_project()
        (root / "executions").mkdir(parents=True, exist_ok=True)
        (root / "executions" / "README.md").write_text(
            "# Execution Records\n\nNo frontmatter here.\n", encoding="utf-8"
        )

        report = validate_project(root)

        self.assertEqual([i for i in report.issues if i.code == "YAML_PARSE_ERROR"], [])


if __name__ == "__main__":
    unittest.main()
