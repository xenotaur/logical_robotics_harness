import tempfile
import unittest
from pathlib import Path

from lrh.control.validator import validate_project


class TestControlValidator(unittest.TestCase):
    def _make_project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "contributors" / "agents").mkdir(parents=True)
        (root / "work_items").mkdir(parents=True)
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
            root / "work_items" / "WI-1.md",
            """---
id: WI-1
title: Task
type: deliverable
status: ready
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
            root / "work_items" / "WI-1.md",
            """---
id: WI-1
title: Task
type: deliverable
status: ready
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
            root / "work_items" / "WI-1.md",
            """---
id: WI-1
title: Task
type: deliverable
status: ready
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
            root / "work_items" / "WI-1.md",
            """---
id: WI-1
title: Task
type: deliverable
status: ready
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
            root / "work_items" / "WI-1.md",
            """---
id: WI-1
title: Task
type: deliverable
status: ready
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
            root / "work_items" / "WI-1.md",
            """---
id: WI-1
title: Task
type: deliverable
status: ready
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


if __name__ == "__main__":
    unittest.main()
