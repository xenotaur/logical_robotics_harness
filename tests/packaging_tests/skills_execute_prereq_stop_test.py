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
import subprocess
import tempfile
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

    def test_multiple_matches_use_a_no_pr_form_that_gives_only_the_count(
        self,
    ) -> None:
        example = _example(self.reference, "no-pr")
        parts = _split_parts(example)
        self.assertEqual(
            parts["Immediate next action"],
            "identify and land the prerequisite PR for WI-LINGUISTICS-0014",
        )
        self.assertNotIn("/lrh-land", example)
        self.assertNotIn("http", example)
        self.assertNotIn("pull/", example)
        self.assertIn("2 open PRs qualify", parts["Why"])
        self.assertIn("/lrh-execute WI-LINGUISTICS-0014", parts["After that"])
        self.assertIn("not actionable yet", parts["After that"])
        self.assertNotIn(FENCE, example)
        # The template must not ask for the qualifying PRs to be listed: a
        # list necessarily names them, contradicting "names no PR".
        flat = _flatten(self.reference)
        self.assertNotIn("(list them)", flat)
        self.assertIn("give only the count", flat)
        self.assertIn("never PR numbers or URLs", flat)

    def test_zero_matches_use_a_distinct_no_pr_example_with_its_own_reason(
        self,
    ) -> None:
        zero = _example(self.reference, "zero-match")
        multi = _example(self.reference, "no-pr")
        self.assertNotEqual(_flatten(zero), _flatten(multi))
        parts = _split_parts(zero)
        self.assertEqual(
            parts["Immediate next action"],
            "identify and land the prerequisite PR for WI-LINGUISTICS-0014",
        )
        self.assertIn("no open PR was found", parts["Why"])
        self.assertIn("unless it is reopened first", parts["Why"])
        self.assertNotIn("qualify", parts["Why"])
        self.assertNotIn("/lrh-land", zero)
        self.assertNotIn("http", zero)
        self.assertIn("/lrh-execute WI-LINGUISTICS-0014", parts["After that"])
        self.assertIn("not actionable yet", parts["After that"])
        self.assertNotIn(FENCE, zero)

    def test_checklist_allows_a_ws_report_to_name_every_verified_blocker(
        self,
    ) -> None:
        checklist = _flatten(self.skill[self.skill.index("## Quality Checklist") :])
        self.assertNotIn("named at most one PR", checklist)
        self.assertIn("exactly one PR in the Immediate next action line", checklist)
        self.assertIn("may additionally name each verified blocker in Why", checklist)
        self.assertIn("never lists PRs, only a count", checklist)

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
        self.assertIn("**every** availability-skipped", reference)
        flat = _flatten(self.step1)
        self.assertIn("do **not** run the open-PR lookup per candidate", flat)
        self.assertIn("runs lazily, once, after the whole list", flat)
        self.assertIn("skipped by the availability check", flat)
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


def _snippet(text: str, marker: str) -> str:
    """Return the first fenced bash block containing `marker`."""
    for block in _fenced_blocks(text):
        if marker in block:
            return block
    raise AssertionError(f"no fenced block containing {marker!r}")


def _git(cwd: pathlib.Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def _run_availability(snippet: str, wi_id: str, cwd: pathlib.Path) -> dict[str, str]:
    script = snippet.replace("<WI-ID>", wi_id).replace("<candidate-WI-ID>", wi_id)
    script += '\nprintf "RESULT path=%s status=%s\\n" "${path:-}" "${status:-}"\n'
    out = subprocess.run(
        ["bash", "-c", script], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout
    line = [ln for ln in out.splitlines() if ln.startswith("RESULT ")][-1]
    path, status = re.match(r"RESULT path=(.*?) status=(.*)$", line).groups()
    return {"path": path, "status": status}


class AvailabilitySnippetBehaviorTest(unittest.TestCase):
    """Run the docs' own bash snippets against real temp repositories."""

    def setUp(self) -> None:
        self.reference = _read(SOURCE_ROOT, REFERENCE_FILE)
        self.skill = _read(SOURCE_ROOT, SKILL_FILE)
        self.snippets = {
            "reference": _snippet(self.reference, "git ls-tree"),
            "skill WI-ID": _snippet(self.skill, "<WI-ID>.md"),
            "skill WS-ID": _snippet(self.skill, "<candidate-WI-ID>.md"),
        }

    def _repo(self, project_dir: str, buckets: dict[str, str]) -> pathlib.Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = pathlib.Path(tmp.name)
        _git(repo, "init", "-q")
        for wi_id, status in buckets.items():
            bucket = repo / project_dir / "project" / "work_items" / status
            bucket.mkdir(parents=True, exist_ok=True)
            (bucket / f"{wi_id}.md").write_text(
                f"---\nid: {wi_id}\nstatus: '{status}'\n---\nbody\n"
            )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "x")
        _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        return repo / project_dir

    def test_status_is_read_at_the_repository_root_and_in_a_nested_project(
        self,
    ) -> None:
        for project_dir in ("", "lcats"):
            cwd = self._repo(
                project_dir, {"WI-AVAIL": "proposed", "WI-DONE": "resolved"}
            )
            for name, snippet in self.snippets.items():
                with self.subTest(project_dir=project_dir or "<root>", snippet=name):
                    proposed = _run_availability(snippet, "WI-AVAIL", cwd)
                    self.assertEqual(proposed["status"], "proposed")
                    self.assertTrue(proposed["path"].endswith("WI-AVAIL.md"))
                    resolved = _run_availability(snippet, "WI-DONE", cwd)
                    self.assertEqual(resolved["status"], "resolved")
                    absent = _run_availability(snippet, "WI-NOPE", cwd)
                    self.assertEqual(absent["path"], "")

    def test_no_snippet_reads_a_cwd_relative_path_from_the_repository_root(
        self,
    ) -> None:
        for name, text in (("reference", self.reference), ("skill", self.skill)):
            with self.subTest(section=name):
                self.assertNotIn('origin/main:$path"', text)
                self.assertIn('origin/main:./$path"', text)


class SnapshotAndScopeWordingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.reference = _flatten(_read(SOURCE_ROOT, REFERENCE_FILE))
        self.skill = _flatten(_read(SOURCE_ROOT, SKILL_FILE))

    def test_fetch_is_a_point_in_time_snapshot_and_failure_is_a_blocker(self) -> None:
        for name, text in (("reference", self.reference), ("skill", self.skill)):
            with self.subTest(section=name):
                self.assertIn("point-in-time snapshot", text)
                self.assertIn("If the fetch fails, stop and report", text)
                self.assertNotIn("never a false positive", text)
                self.assertNotIn("only ever lags behind reality", text)

    def test_open_pr_file_match_accounts_for_a_nested_project_prefix(self) -> None:
        self.assertIn("git rev-parse --show-prefix", self.reference)
        self.assertIn('grep -x "${prefix}project/work_items/', self.reference)

    def test_open_pr_file_match_skips_files_the_pr_removes(self) -> None:
        # A bucket move reported as delete+add must not match the removed path:
        # reading it at the PR's head 404s and a valid blocker goes unnamed.
        self.assertIn('select(.status != "removed")', self.reference)
        self.assertIn("returns 404", self.reference)

    def test_ws_lookup_is_limited_to_availability_skipped_candidates(self) -> None:
        for name, text in (("reference", self.reference), ("skill", self.skill)):
            with self.subTest(section=name):
                self.assertIn("skipped by the availability check", text)
                self.assertIn("cannot make", text)


if __name__ == "__main__":
    unittest.main()
