"""Regression coverage: /lrh-execute stops with a structured, unambiguous report.

`WI-EXECUTE-OPEN-PREREQ-PR-STOP`. The skill is prose, so these tests pin the
required instructions and the worked-example stop reports. They cannot
exercise runtime agent behavior; they guard against the instructions that
make `/lrh-land <PR>` the immediate next action (and the later
`/lrh-execute <WI-ID>` a non-actionable "after that") from regressing.
"""

from __future__ import annotations

import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILL = "lrh-execute"
SOURCE_ROOT = REPO_ROOT / "src" / "lrh" / "skills"
MIRROR_ROOTS = (
    REPO_ROOT / ".claude" / "skills",
    REPO_ROOT / ".agents" / "skills",
    REPO_ROOT / ".gemini" / "plugins" / "lrh" / "skills",
)
SKILL_FILE = "SKILL.md"
REFERENCE_FILE = "references/creation-pr-check.md"
FENCE = "```"


def _read(root: pathlib.Path, relative: str) -> str:
    return (root / SKILL / relative).read_text()


def _body(text: str) -> str:
    """Return the text after a leading YAML frontmatter block, if any."""
    match = re.match(r"---\n.*?\n---\n", text, re.S)
    return text[match.end() :] if match else text


def _example(reference: str, name: str) -> str:
    start = rf"<!-- worked-example:{name}:start -->\n"
    end = rf"<!-- worked-example:{name}:end -->"
    match = re.search(f"{start}(.*?){end}", reference, re.S)
    assert match, f"worked example {name!r} missing from the reference"
    return match.group(1)


def _flatten(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _split_parts(example: str) -> dict[str, str]:
    parts = re.split(r"(?m)^(Immediate next action|Why|After that): ", example)
    # parts == ['', 'Immediate next action', '...', 'Why', '...', 'After that', '...']
    return {parts[i]: _flatten(parts[i + 1]) for i in range(1, len(parts), 2)}


def _fenced_blocks(text: str) -> list[str]:
    return re.findall(rf"{FENCE}[a-z]*\n(.*?){FENCE}", text, re.S)


def _step1_region(skill: str) -> str:
    start = skill.index("### Step 1 — Resolve the target work item")
    end = skill.index("### Step 1.5")
    return skill[start:end]


class PrereqStopReportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.reference = _read(SOURCE_ROOT, REFERENCE_FILE)
        self.skill = _read(SOURCE_ROOT, SKILL_FILE)

    def test_open_prerequisite_pr_reports_land_as_the_immediate_action(self) -> None:
        """The LCATS case: a reopening PR is open; landing it is the action."""
        parts = _split_parts(_example(self.reference, "named"))
        self.assertEqual(list(parts), ["Immediate next action", "Why", "After that"])
        self.assertEqual(
            parts["Immediate next action"],
            "`/lrh-land https://github.com/xenotaur/LCATS/pull/463`",
        )
        self.assertNotIn("/lrh-execute", parts["Immediate next action"])
        self.assertNotIn("/lrh-execute", parts["Why"])
        self.assertIn("status: proposed", parts["Why"])

    def test_later_execution_command_is_only_a_non_actionable_after_step(self) -> None:
        example = _example(self.reference, "named")
        parts = _split_parts(example)
        self.assertIn("/lrh-execute WI-LINGUISTICS-0014", parts["After that"])
        self.assertIn("not actionable yet", parts["After that"])
        self.assertEqual(example.count("/lrh-execute"), 1)
        self.assertNotIn(FENCE, example)

    def test_zero_or_multiple_matches_use_a_no_pr_form_that_names_no_pr(self) -> None:
        example = _example(self.reference, "no-pr")
        parts = _split_parts(example)
        self.assertEqual(
            parts["Immediate next action"],
            "identify and land the prerequisite PR for WI-LINGUISTICS-0014",
        )
        self.assertNotIn("/lrh-land", example)
        self.assertNotIn("http", example)
        self.assertIn("/lrh-execute WI-LINGUISTICS-0014", parts["After that"])
        self.assertIn("not actionable yet", parts["After that"])
        self.assertNotIn(FENCE, example)

    def test_execution_command_never_sits_in_a_code_block_or_next_step_heading(
        self,
    ) -> None:
        for name, text in (
            ("reference", self.reference),
            ("skill step 1", _step1_region(self.skill)),
        ):
            with self.subTest(section=name):
                for block in _fenced_blocks(text):
                    self.assertNotIn("/lrh-execute <", block)
                    self.assertNotIn("/lrh-execute WI-", block)
                self.assertIsNone(
                    re.search(r"(?mi)^#+.*next step", text),
                    "stop report must not use a 'next step' heading",
                )
        self.assertIn("plain text", self.reference)
        self.assertIn("not inside a fenced code block", self.reference)


class PrereqLookupTest(unittest.TestCase):
    def setUp(self) -> None:
        self.reference = _read(SOURCE_ROOT, REFERENCE_FILE)
        self.skill = _read(SOURCE_ROOT, SKILL_FILE)

    def test_open_pr_enumeration_is_exhaustive_not_the_default_limit(self) -> None:
        commands = [
            command
            for block in _fenced_blocks(self.reference)
            for command in re.findall(r"gh pr list(?:[^\n]*\\\n)*[^\n]*", block)
        ]
        self.assertTrue(commands, "the reference must enumerate open PRs")
        for command in commands:
            with self.subTest(command=command):
                limits = [int(n) for n in re.findall(r"--limit\s+(\d+)", command)]
                self.assertTrue(limits, "gh pr list must pass an explicit --limit")
                self.assertTrue(all(limit > 30 for limit in limits))
                self.assertIn("--base main", command)
                self.assertIn("--state open", command)
        self.assertIn("--paginate", self.reference)
        self.assertIn("Truncation guard", self.reference)
        self.assertIn("default of 30", self.reference)

    def test_a_pr_is_named_only_after_its_head_version_is_proposed(self) -> None:
        self.assertIn("head version of the WI sets `status: proposed`", self.reference)
        self.assertIn("?ref=<headRefOid>", self.reference)
        self.assertIn("is not a prerequisite", self.reference)
        self.assertIn("Exactly one qualifying PR", self.reference)
        self.assertIn("names **no PR**", self.reference)
        self.assertIn("lookup is inconclusive", self.reference)

    def test_availability_requires_present_and_proposed_on_origin_main(self) -> None:
        for name, text in (("reference", self.reference), ("skill", self.skill)):
            with self.subTest(section=name):
                self.assertIn("git show", text)
                self.assertIn("origin/main", text)
                self.assertIn("proposed", text)
        self.assertIn("hard, unconditional gate", self.reference)


class PrereqOrderingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = _read(SOURCE_ROOT, SKILL_FILE)
        self.step1 = _step1_region(self.skill)

    def test_wi_id_check_precedes_readiness_and_mints_no_prompt(self) -> None:
        check = self.step1.index("**Prerequisite lifecycle check**")
        readiness = self.step1.index("lrh work-items readiness <WI-ID>")
        self.assertLess(check, readiness)
        self.assertNotIn("lrh prompt label", self.step1)
        self.assertLess(
            self.skill.index("### Step 1 —"), self.skill.index("### Step 1.5")
        )
        self.assertLess(
            self.skill.index("### Step 1.5"), self.skill.index("### Step 2")
        )

    def test_ws_id_check_precedes_readiness_and_skips_per_candidate(self) -> None:
        check = self.step1.index(
            "**Prerequisite lifecycle check first, before readiness**"
        )
        readiness = self.step1.index("lrh work-items readiness <candidate-WI-ID>")
        self.assertLess(check, readiness)
        self.assertIn("ineligible, not a run-aborting hard stop", self.step1)
        self.assertIn("first such candidate in list order", _flatten(self.step1))
        reference = _read(SOURCE_ROOT, REFERENCE_FILE)
        self.assertIn("**first** such candidate", reference)
        self.assertIn("**every** skipped candidate", reference)
        flat = _flatten(self.step1)
        self.assertIn("do **not** run the open-PR lookup per candidate", flat)
        self.assertIn("runs lazily, once, after the whole list", flat)
        self.assertIn("lookup **once** for all skipped candidates", flat)
        self.assertIn(
            "Do not run the open-PR lookup per candidate", _flatten(reference)
        )

    def test_existing_chain_gates_and_phases_are_unchanged(self) -> None:
        for heading in (
            "### Step 2 — Chain authorization gate",
            "### Step 3 — Implement (inline `/lrh-implement`)",
            "### Step 4 — Land (inline `/lrh-land`)",
            "### Step 5 — Run journal",
            "### Step 6 — Report",
        ):
            self.assertIn(heading, self.skill)
        self.assertIn("`prompt_ready` field specifically", self.skill)


class PrereqJournalTest(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = _read(SOURCE_ROOT, SKILL_FILE)
        start = self.skill.index("### Step 5 — Run journal")
        self.journal = self.skill[start : self.skill.index("### Step 6", start)]

    def test_step1_stop_variant_needs_no_resolved_wi_and_no_prompt(self) -> None:
        self.assertIn("Step 1 stop variant", self.journal)
        self.assertIn(
            "wi: <WI-ID, or null for a WS-ID stop with no resolved WI>", self.journal
        )
        self.assertIn("prompt_id: null", self.journal)
        self.assertIn("result: stopped", self.journal)
        self.assertIn("blocking_prs:", self.journal)
        for reason in (
            "open_prerequisite_pr",
            "prerequisite_pr_not_identified",
            "depends_on_unresolved",
            "no_ready_wi",
        ):
            self.assertIn(reason, self.journal)

    def test_step1_stops_are_journaled_before_reporting(self) -> None:
        step1 = _step1_region(self.skill)
        self.assertGreaterEqual(step1.count("Step 1 stop variant"), 3)
        self.assertIn("`wi: null`", step1)
        self.assertIn(
            "mints **no prompt ID**", _flatten(_read(SOURCE_ROOT, REFERENCE_FILE))
        )


class MirrorConsistencyTest(unittest.TestCase):
    def test_claude_mirror_is_byte_identical_to_source(self) -> None:
        for relative in (SKILL_FILE, REFERENCE_FILE):
            with self.subTest(file=relative):
                self.assertEqual(
                    _read(SOURCE_ROOT, relative),
                    _read(REPO_ROOT / ".claude" / "skills", relative),
                )

    def test_installer_generated_mirrors_match_source_body(self) -> None:
        """`.agents`/`.gemini` carry installer-rendered frontmatter; compare bodies."""
        for root in MIRROR_ROOTS:
            for relative in (SKILL_FILE, REFERENCE_FILE):
                with self.subTest(root=str(root.relative_to(REPO_ROOT)), file=relative):
                    self.assertEqual(
                        _body(_read(SOURCE_ROOT, relative)),
                        _body(_read(root, relative)),
                    )


if __name__ == "__main__":
    unittest.main()
