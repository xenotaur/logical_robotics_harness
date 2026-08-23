"""Initial CLI entrypoint for Logical Robotics Harness."""

# PYTHON_ARGCOMPLETE_OK

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lrh import (
    memory_workflow,
    prompt_workflow,
    prompt_workflow_match,
    prompt_workflow_search,
    serve,
    sessions_workflow,
)
from lrh import version as lrh_version
from lrh.assist import request_cli, snapshot_cli, sourcetree_surveyor
from lrh.cli import argcomplete_adapter
from lrh.cli import github as github_cli
from lrh.control import format_report, validate_project
from lrh.conversations import (
    codex_app_server_export,
    codex_archive,
    codex_file_export,
    codex_session,
    export_inspector,
    pdf_import,
)
from lrh.design import organize as design_organize
from lrh import gate_staleness
from lrh.meta import workspace
from lrh.project import bootstrap, doctor
from lrh.secrets import purge as secrets_purge
from lrh.secrets import review as secrets_review
from lrh.secrets import scan as secrets_scan
from lrh.work_items import audit as work_items_audit
from lrh.work_items import organize as work_items_organize
from lrh.work_items import readiness as work_items_readiness
from lrh.work_items import validate as work_items_validate
from lrh.workstreams import organize as workstreams_organize


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="lrh",
        description=(
            "Logical Robotics Harness command-line interface. "
            "Optional shell completion is available via argcomplete; "
            "Run `scripts/install-completion` for setup guidance."
        ),
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="show LRH package version and exit",
    )
    subparsers = parser.add_subparsers(dest="command")

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate project control files.",
    )
    validate_parser.add_argument(
        "--project-dir",
        default="project",
        help="path to the project control directory (default: project)",
    )
    validate_parser.add_argument(
        "--work-items",
        action="store_true",
        help="validate work-item files and policy rules only",
    )

    request_parser = subparsers.add_parser(
        "request",
        add_help=False,
        help=(
            "Render an assist request from a template "
            "(argcomplete completion optional; run scripts/install-completion)."
        ),
    )
    request_cli.configure_parser(request_parser)

    subparsers.add_parser(
        "snapshot",
        add_help=False,
        help="Generate assist snapshot context packets.",
    )

    subparsers.add_parser(
        "survey",
        add_help=False,
        help="Survey a Python source tree for assist planning workflows.",
    )

    subparsers.add_parser(
        "serve",
        add_help=False,
        help="Start the safe-default local read-only server skeleton.",
    )

    conversation_parser = subparsers.add_parser(
        "conversation",
        help="Conversation import and analysis commands.",
    )
    conversation_subparsers = conversation_parser.add_subparsers(
        dest="conversation_command"
    )
    conversation_subparsers.add_parser(
        "convert-pdf",
        add_help=False,
        help="Convert a local ChatGPT PDF export to Markdown.",
    )
    conversation_subparsers.add_parser(
        "convert-codex-file",
        add_help=False,
        help="Convert an explicit local Codex transcript/source file to Markdown.",
    )
    conversation_subparsers.add_parser(
        "current-codex-thread-id",
        add_help=False,
        help="Report the current Codex thread id and session pointer.",
    )
    conversation_subparsers.add_parser(
        "export-codex-thread",
        add_help=False,
        help="Export a Codex thread through app-server thread/read.",
    )
    conversation_subparsers.add_parser(
        "archive-codex-thread",
        add_help=False,
        help="Export a Codex thread into the durable private archive.",
    )
    conversation_subparsers.add_parser(
        "import-codex-exports",
        add_help=False,
        help="Import existing LRH Codex export directories into the archive.",
    )
    conversation_subparsers.add_parser(
        "inspect-export",
        add_help=False,
        help="Inspect a Codex conversation export Markdown artifact.",
    )

    subparsers.add_parser(
        "version",
        help="Show LRH package version and exit.",
    )

    subparsers.add_parser(
        "github",
        add_help=False,
        help="Query GitHub pull request comments/threads.",
    )

    subparsers.add_parser(
        "prompt",
        add_help=False,
        help="Prompt workflow helper commands.",
    )

    subparsers.add_parser(
        "match",
        add_help=False,
        help="Match prompt files to execution records.",
    )

    subparsers.add_parser(
        "sessions",
        add_help=False,
        help=(
            "Session archive reconciler "
            "(sync/discover/link/report/closeout-sync/schedule)."
        ),
    )

    subparsers.add_parser(
        "search",
        add_help=False,
        help="Search LRH project records.",
    )

    subparsers.add_parser(
        "memory",
        add_help=False,
        help="Memory corpus commands (write/list/validate/repair).",
    )

    skills_parser = subparsers.add_parser(
        "skills",
        help="Manage LRH agent skills.",
    )
    skills_subparsers = skills_parser.add_subparsers(dest="skills_command")

    def add_skills_resolution_args(
        skills_command_parser: argparse.ArgumentParser,
    ) -> None:
        skills_command_parser.add_argument(
            "--local",
            action="store_true",
            help="use project-local skills directory instead of user scope",
        )
        skills_command_parser.add_argument(
            "--scope",
            choices=("user", "project"),
            default=None,
            help="skills scope (default: repo config or user; --local is project)",
        )
        skills_command_parser.add_argument(
            "--target",
            choices=("claude", "codex", "antigravity", "all"),
            default=None,
            help="agent target (default: repo config or claude)",
        )
        skills_command_parser.add_argument(
            "--source",
            default=None,
            help=(
                "canonical skill source: lrh-package, current-repo, or a filesystem"
                " path (default: repo config or lrh-package)"
            ),
        )

    skills_install_parser = skills_subparsers.add_parser(
        "install",
        help=(
            "Install LRH skills to agent skills directories."
            " Use --target and --local to choose exact destinations."
        ),
    )
    skills_install_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="preview what would be installed without writing files",
    )
    skills_install_parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite user-modified skills without warning",
    )
    add_skills_resolution_args(skills_install_parser)
    skills_install_parser.add_argument(
        "--diff",
        action="store_true",
        help="print a unified diff of local modifications for skipped skills",
    )
    skills_status_parser = skills_subparsers.add_parser(
        "status",
        help="Inspect installed LRH skill state without writing files.",
    )
    add_skills_resolution_args(skills_status_parser)
    skills_check_parser = skills_subparsers.add_parser(
        "check",
        help="Check installed LRH skill drift and compatibility without writing files.",
    )
    add_skills_resolution_args(skills_check_parser)

    project_parser = subparsers.add_parser(
        "project",
        help="Project bootstrap and management helpers.",
    )
    project_subparsers = project_parser.add_subparsers(dest="project_command")
    project_init_parser = project_subparsers.add_parser(
        "init",
        help="Initialize LRH project-control scaffolding from package templates.",
    )
    project_init_parser.add_argument(
        "--profile",
        choices=("minimal", "prompt-workflow", "full"),
        default="minimal",
        help="bootstrap profile to apply (default: minimal)",
    )
    project_init_parser.add_argument(
        "--project-root",
        default=".",
        help="target repository root (default: current directory)",
    )
    project_init_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="preview changes without writing files",
    )
    project_init_parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero when changes would be needed",
    )
    project_init_parser.add_argument(
        "--force",
        action="store_true",
        help="allow overwriting existing files",
    )

    project_doctor_parser = project_subparsers.add_parser(
        "doctor",
        help="Diagnose LRH project bootstrap readiness.",
    )
    project_doctor_parser.add_argument(
        "--project-root",
        default=".",
        help="target repository root (default: current directory)",
    )
    project_doctor_parser.add_argument(
        "--json",
        action="store_true",
        help="emit deterministic JSON output",
    )
    project_doctor_parser.add_argument(
        "--strict",
        action="store_true",
        help="return non-zero when warnings are present",
    )

    work_items_parser = subparsers.add_parser(
        "work-items",
        help="Work-item maintenance commands.",
    )
    work_items_subparsers = work_items_parser.add_subparsers(dest="work_items_command")
    work_items_organize_parser = work_items_subparsers.add_parser(
        "organize",
        help=(
            "Conservatively repair work-item frontmatter and status buckets, "
            "including legacy layouts."
        ),
    )
    work_items_organize_parser.add_argument(
        "--project-root",
        default=".",
        help="target repository root (default: current directory)",
    )
    work_items_organize_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="preview planned changes without writing files",
    )
    work_items_organize_parser.add_argument(
        "--check",
        action="store_true",
        help="return non-zero when organization changes would be needed",
    )
    work_items_organize_parser.add_argument(
        "--apply",
        action="store_true",
        help="apply planned file updates and moves",
    )

    work_items_validate_parser = work_items_subparsers.add_parser(
        "validate",
        help="Validate work-item hygiene and status-bucket organization.",
    )
    work_items_validate_parser.add_argument(
        "--project-root",
        default=".",
        help="target repository root (default: current directory)",
    )
    work_items_validate_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )

    work_items_audit_parser = work_items_subparsers.add_parser(
        "audit",
        help="Report deterministic work-item lifecycle and traceability signals.",
    )
    work_items_audit_parser.add_argument(
        "--project-root",
        default=".",
        help="target repository root (default: current directory)",
    )
    work_items_audit_parser.add_argument(
        "--format",
        choices=("md", "json"),
        default="md",
        help="output format (default: md)",
    )

    work_items_readiness_parser = work_items_subparsers.add_parser(
        "readiness",
        help="Report deterministic prompt-readiness diagnostics for work items.",
    )
    work_items_readiness_parser.add_argument(
        "work_item_id", nargs="?", help="work-item ID"
    )
    work_items_readiness_parser.add_argument(
        "--project-root",
        default=".",
        help="target repository root (default: current directory)",
    )
    work_items_readiness_parser.add_argument(
        "--status",
        choices=("proposed", "active", "resolved", "abandoned"),
        help="filter by frontmatter status",
    )
    work_items_readiness_parser.add_argument(
        "--format",
        choices=("md", "json"),
        default="md",
        help="output format (default: md)",
    )

    chain_defaults_parser = subparsers.add_parser(
        "chain-defaults",
        help="Chain-defaults gate-staleness commands.",
    )
    chain_defaults_subparsers = chain_defaults_parser.add_subparsers(
        dest="chain_defaults_command"
    )
    chain_defaults_staleness_parser = chain_defaults_subparsers.add_parser(
        "check-staleness",
        help=(
            "Semantic (marker-scoped) gate-definition staleness check for "
            "stored chain-defaults consent."
        ),
    )
    chain_defaults_staleness_parser.add_argument(
        "--confirmed-commit",
        required=True,
        help="the commit stored consent was last confirmed against",
    )
    chain_defaults_staleness_parser.add_argument(
        "--head",
        default="HEAD",
        help="commit-ish to check against (default: HEAD)",
    )
    chain_defaults_staleness_parser.add_argument(
        "--project-root",
        default=".",
        help="target repository root (default: current directory)",
    )
    chain_defaults_staleness_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )

    secrets_parser = subparsers.add_parser(
        "secrets",
        help="Secrets-hygiene scan/review/purge commands.",
    )
    secrets_subparsers = secrets_parser.add_subparsers(dest="secrets_command")
    secrets_scan_parser = secrets_subparsers.add_parser(
        "scan",
        help="Read-only full-history secrets scan via gitleaks.",
        epilog=(
            "Provider coverage is uneven, not uniform: OpenAI/Anthropic/Gemini\n"
            "keys have structural prefixes gitleaks' default rules catch\n"
            "reliably; Azure-family keys have no distinguishing prefix and are\n"
            "only caught via contextual rules (default or repo-supplied\n"
            ".gitleaks.toml), invisible entirely on a non-suggestive variable\n"
            "name. .ipynb files store source as JSON-escaped strings, which can\n"
            "defeat delimiter-based detection regexes regardless of provider."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    secrets_scan_parser.add_argument(
        "--project-root",
        default=".",
        help="target repository root to scan (default: current directory)",
    )
    secrets_scan_parser.add_argument(
        "--out-dir",
        required=True,
        help=(
            "directory to write findings.json and replacements.txt into. "
            "These files contain real secret values -- choose a gitignored "
            "location, not a directory a later `git add .` would pick up."
        ),
    )
    secrets_scan_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )

    secrets_review_parser = secrets_subparsers.add_parser(
        "review",
        help="Decisions-file-gated triage of a scan's findings.",
        epilog=(
            "Decisions file (YAML), one entry per secret value:\n"
            "  <secret-value>:\n"
            "    decision: keep     # or: ignore\n"
            '    reason: "why"\n'
            "--apply writes out-dir/replacements.reviewed.txt, distinct from\n"
            "scan's draft replacements.txt -- this is the file lrh secrets\n"
            "purge accepts via its --replacements flag, never the draft."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    secrets_review_parser.add_argument(
        "--out-dir",
        required=True,
        help="directory containing scan's findings.json/replacements.txt",
    )
    secrets_review_parser.add_argument(
        "--decisions",
        default=None,
        help="path to the decisions YAML file (see epilog for format)",
    )
    secrets_review_parser.add_argument(
        "--check",
        action="store_true",
        help="exit nonzero if any finding lacks a recorded decision",
    )
    secrets_review_parser.add_argument(
        "--apply",
        action="store_true",
        help="write replacements.reviewed.txt; requires every finding decided",
    )

    secrets_purge_parser = secrets_subparsers.add_parser(
        "purge",
        help="Mirror-clone-scoped git-filter-repo rewrite, verify, never push.",
        epilog=(
            "--replacements must be review --apply's replacements.reviewed.txt\n"
            "output, not scan's draft replacements.txt -- enforced at runtime\n"
            "via a required first-line marker, not just by filename.\n"
            "--refs-file is mandatory; purge refuses to run unscoped.\n"
            "This command never runs `git push` under any flag combination --\n"
            "on success it prints the push command for a human to run manually,\n"
            "together with collaborator-notification and host-support-request\n"
            "reminders."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    secrets_purge_parser.add_argument(
        "--project-root",
        default=".",
        help="target repository root, used to default --source (default: cwd)",
    )
    secrets_purge_parser.add_argument(
        "--source",
        default=None,
        help="URL or path to mirror-clone (default: --project-root's origin)",
    )
    secrets_purge_parser.add_argument(
        "--refs-file",
        required=True,
        help="mandatory: path to a file listing one ref per line to rewrite",
    )
    secrets_purge_parser.add_argument(
        "--replacements",
        required=True,
        help="path to review --apply's replacements.reviewed.txt output",
    )
    secrets_purge_parser.add_argument(
        "--mirror-dir",
        default=None,
        help="directory for the mirror clone (default: a fresh temp dir)",
    )
    secrets_purge_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate inputs without cloning or rewriting anything",
    )
    secrets_purge_parser.add_argument(
        "--apply",
        action="store_true",
        help="mirror-clone, rewrite, and verify (mutually exclusive with --dry-run)",
    )

    workstreams_parser = subparsers.add_parser(
        "workstreams",
        help="Workstream maintenance commands.",
    )
    workstreams_subparsers = workstreams_parser.add_subparsers(
        dest="workstreams_command"
    )
    workstreams_organize_parser = workstreams_subparsers.add_parser(
        "organize",
        help="Organize workstreams into metadata-derived status buckets.",
    )
    workstreams_organize_parser.add_argument(
        "--project-root",
        default=".",
        help="target repository root (default: current directory)",
    )
    workstreams_organize_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="preview planned moves without writing files",
    )
    workstreams_organize_parser.add_argument(
        "--check",
        action="store_true",
        help="return non-zero when organization changes would be needed",
    )
    workstreams_organize_parser.add_argument(
        "--apply",
        action="store_true",
        help="apply planned file moves",
    )

    design_parser = subparsers.add_parser(
        "design",
        help="Design artifact maintenance commands.",
    )
    design_subparsers = design_parser.add_subparsers(dest="design_command")
    design_organize_parser = design_subparsers.add_parser(
        "organize",
        help="Organize design proposals into lifecycle buckets.",
    )
    design_organize_parser.add_argument(
        "--project-root",
        default=".",
        help="target repository root (default: current directory)",
    )
    design_organize_parser.add_argument(
        "--apply",
        action="store_true",
        help="apply planned file moves",
    )

    meta_parser = subparsers.add_parser(
        "meta",
        help="Manage LRH workspace/meta-control state.",
        description=(
            "Manage LRH meta workspaces and project registry records. "
            "Workspace resolution precedence: flags, LRH_CONFIG, LRH_WORKSPACE, "
            "local discovery, then global discovery/defaults."
        ),
        epilog=(
            "Global defaults when XDG variables are unset:\n"
            "  config: ~/.config/lrh/config.toml\n"
            "  state: ~/.local/state/lrh/\n"
            "  cache: ~/.cache/lrh/"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    meta_subparsers = meta_parser.add_subparsers(dest="meta_command")

    def _add_meta_workspace_resolution_args(
        target_parser: argparse.ArgumentParser,
    ) -> None:
        target_parser.add_argument(
            "--workspace",
            "--workspace-root",
            dest="workspace",
            help="explicit workspace/catalog root containing .lrh/config.toml",
        )
        target_parser.add_argument(
            "--config",
            help="explicit workspace config.toml path",
        )
        target_parser.add_argument(
            "--mode",
            choices=("hybrid", "local", "global"),
            help="workspace mode override for resolution",
        )

    meta_init_parser = meta_subparsers.add_parser(
        "init",
        help="Initialize LRH meta workspace paths (defaults to hybrid mode).",
        description=(
            "Initialize LRH meta workspace directories and config. "
            "Default mode is hybrid "
            "(local catalog root + global XDG config/state/cache). "
            "Use --mode local to keep all paths local, or --mode global to keep "
            "workspace and runtime paths in global locations."
        ),
        epilog=(
            "Resolution inputs (high-level): flags, LRH_CONFIG, LRH_WORKSPACE, "
            "local workspace discovery, global workspace discovery.\n\n"
            "Global defaults when XDG variables are unset:\n"
            "  config: ~/.config/lrh/config.toml\n"
            "  state: ~/.local/state/lrh/\n"
            "  cache: ~/.cache/lrh/"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    meta_init_parser.add_argument(
        "--name",
        default="LRH Workspace",
        help="workspace display name for generated README/config",
    )
    meta_init_parser.add_argument(
        "--mode",
        choices=("hybrid", "global", "local"),
        default="hybrid",
        help="initialization mode (default: hybrid)",
    )
    meta_init_parser.add_argument(
        "workspace_root",
        nargs="?",
        help=(
            "workspace/catalog root directory for hybrid mode "
            "(defaults to current directory)"
        ),
    )
    meta_init_parser.add_argument(
        "--workspace-root",
        dest="workspace_root_flag",
        help="explicit workspace/catalog root directory",
    )
    meta_init_parser.add_argument(
        "--force",
        action="store_true",
        help="replace incompatible managed paths/content when safe",
    )

    meta_list_parser = meta_subparsers.add_parser(
        "list",
        help="List registered projects from the workspace registry.",
        description=(
            "List registered projects from the active workspace registry.\n\n"
            "Each record renders:\n"
            "  repo_locator = repository/ref locator\n"
            "  project_dir  = relative path from that locator to project/\n"
            "  setup_state  = truth-first local check result or not_checked "
            "for remote locators"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_meta_workspace_resolution_args(meta_list_parser)

    meta_where_parser = meta_subparsers.add_parser(
        "where",
        help="Show the active workspace and how it was resolved.",
    )
    _add_meta_workspace_resolution_args(meta_where_parser)
    meta_where_parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON for the active workspace",
    )

    meta_config_parser = meta_subparsers.add_parser(
        "config",
        help="Manage workspace meta configuration.",
    )
    _add_meta_workspace_resolution_args(meta_config_parser)
    meta_config_subparsers = meta_config_parser.add_subparsers(
        dest="meta_config_command"
    )
    meta_config_subparsers.add_parser(
        "list", help="List supported config keys and values."
    )
    meta_config_get_parser = meta_config_subparsers.add_parser(
        "get", help="Get one config value."
    )
    meta_config_get_parser.add_argument(
        "key", help="config key (prefer hyphenated names)"
    )
    meta_config_set_parser = meta_config_subparsers.add_parser(
        "set", help="Set one config value."
    )
    meta_config_set_parser.add_argument(
        "key", help="config key (prefer hyphenated names)"
    )
    meta_config_set_parser.add_argument(
        "value", help="boolean value: true/false, yes/no, 1/0"
    )
    meta_config_unset_parser = meta_config_subparsers.add_parser(
        "unset", help="Unset one config value to default."
    )
    meta_config_unset_parser.add_argument(
        "key", help="config key (prefer hyphenated names)"
    )
    meta_register_parser = meta_subparsers.add_parser(
        "register",
        help="Register a project repository in the workspace registry.",
        description=(
            "Register one project-control record in the active workspace registry.\n\n"
            "Locator semantics:\n"
            "  repo_locator = repository/ref locator\n"
            "  project_dir  = relative path from that locator to the LRH "
            "project control directory\n\n"
            "Example:\n"
            "  lrh meta register "
            "https://github.com/xenotaur/taurworks/tree/master/project\n\n"
            "By default, GitHub tree locators are normalized so "
            "repo_locator stores .../tree/<ref> and project_dir stores the tail "
            "path (for example, project)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_meta_workspace_resolution_args(meta_register_parser)
    meta_register_parser.add_argument(
        "repo_locator",
        help="repository locator string (local path, URL, or other stable locator)",
    )
    meta_register_parser.add_argument(
        "--project-dir",
        help=(
            "project control directory relative to repo root "
            "(default: inferred for supported URL patterns, otherwise project)"
        ),
    )
    meta_register_parser.add_argument(
        "--directory-name",
        help="registry directory name under projects/ (default: inferred from locator)",
    )
    meta_register_parser.add_argument(
        "--short-name",
        help="short display label (default: directory name)",
    )
    meta_register_parser.add_argument(
        "--display-name",
        help="human-readable project name (default: inferred from short name)",
    )
    meta_register_parser.add_argument(
        "--force",
        action="store_true",
        help="allow deliberate duplicates and overwrite existing target records",
    )
    meta_refresh_parser = meta_subparsers.add_parser(
        "refresh",
        help="Refresh observation checks for one registered project.",
    )
    _add_meta_workspace_resolution_args(meta_refresh_parser)
    meta_refresh_parser.add_argument("project", help="project selector")

    meta_inspect_parser = meta_subparsers.add_parser(
        "inspect",
        help="Inspect one registered project with workspace context.",
        description=(
            "Inspect one registered project record and resolved workspace context.\n\n"
            "Rendered fields include locator semantics:\n"
            "  repo_locator = repository/ref locator\n"
            "  project_dir  = relative path from that locator to project/."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_meta_workspace_resolution_args(meta_inspect_parser)
    meta_inspect_parser.add_argument(
        "project",
        help="project selector (exact project_id, short_name, or registry_name)",
    )
    meta_set_parser = meta_subparsers.add_parser(
        "set",
        help="Set first-class fields for one registered project.",
    )
    _add_meta_workspace_resolution_args(meta_set_parser)
    meta_set_parser.add_argument("project", help="project selector")
    meta_set_parser.add_argument("--local-repo-path", help="local checkout path")
    meta_set_parser.add_argument("--project-dir", help="project/ path relative to repo")
    meta_set_parser.add_argument("--display-name", help="display name")
    meta_set_parser.add_argument("--short-name", help="short name")

    meta_unset_parser = meta_subparsers.add_parser(
        "unset",
        help="Unset first-class fields for one registered project.",
    )
    _add_meta_workspace_resolution_args(meta_unset_parser)
    meta_unset_parser.add_argument("project", help="project selector")
    meta_unset_parser.add_argument(
        "--local-repo-path", action="store_true", help="unset local checkout path"
    )

    argcomplete_adapter.enable_completion(parser)

    argv = sys.argv[1:]
    if argv and argv[0] == "help":
        if len(argv) == 1:
            parser.print_help()
            raise SystemExit(0)
        argv = [*argv[1:], "--help"]

    first_command_index = 0
    while first_command_index < len(argv) and argv[first_command_index] == "--version":
        first_command_index += 1

    if first_command_index < len(argv) and argv[first_command_index] == "request":
        raise SystemExit(
            request_cli.run_request_cli(
                argv=argv[first_command_index + 1 :],
                prog="lrh request",
            )
        )

    args, passthrough_args = parser.parse_known_args(argv)

    if args.version or args.command == "version":
        if args.command == "request":
            raise SystemExit(
                request_cli.run_request_cli(
                    argv=passthrough_args,
                    prog="lrh request",
                )
            )
        if passthrough_args:
            parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
        print(lrh_version.format_cli_version())
        raise SystemExit(0)

    if args.command == "validate":
        if passthrough_args:
            parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
        report = validate_project(
            Path(args.project_dir),
            work_items_only=args.work_items,
        )
        print(format_report(report))
        raise SystemExit(1 if report.errors else 0)

    if args.command == "snapshot":
        raise SystemExit(
            snapshot_cli.run_snapshot_cli(
                argv=passthrough_args,
                prog="lrh snapshot",
            )
        )

    if args.command == "github":
        raise SystemExit(
            github_cli.run_github_cli(
                argv=passthrough_args,
                prog="lrh github",
            )
        )

    if args.command == "survey":
        raise SystemExit(
            sourcetree_surveyor.main(
                argv=passthrough_args,
                prog="lrh survey",
            )
        )

    if args.command == "serve":
        raise SystemExit(
            serve.run_serve_cli(
                argv=passthrough_args,
                prog="lrh serve",
            )
        )

    if args.command == "conversation":
        if args.conversation_command == "convert-codex-file":
            raise SystemExit(
                codex_file_export.run_convert_codex_file_cli(
                    argv=passthrough_args,
                    prog="lrh conversation convert-codex-file",
                )
            )
        if args.conversation_command == "convert-pdf":
            raise SystemExit(
                pdf_import.run_convert_pdf_cli(
                    argv=passthrough_args,
                    prog="lrh conversation convert-pdf",
                )
            )
        if args.conversation_command == "inspect-export":
            raise SystemExit(
                export_inspector.run_inspect_export_cli(
                    argv=passthrough_args,
                    prog="lrh conversation inspect-export",
                )
            )
        if args.conversation_command == "export-codex-thread":
            raise SystemExit(
                codex_app_server_export.run_export_codex_thread_cli(
                    argv=passthrough_args,
                    prog="lrh conversation export-codex-thread",
                )
            )
        if args.conversation_command == "current-codex-thread-id":
            raise SystemExit(
                codex_session.run_current_codex_thread_id_cli(
                    argv=passthrough_args,
                    prog="lrh conversation current-codex-thread-id",
                )
            )
        if args.conversation_command == "archive-codex-thread":
            raise SystemExit(
                codex_archive.run_archive_codex_thread_cli(
                    argv=passthrough_args,
                    prog="lrh conversation archive-codex-thread",
                )
            )
        if args.conversation_command == "import-codex-exports":
            raise SystemExit(
                codex_archive.run_import_codex_exports_cli(
                    argv=passthrough_args,
                    prog="lrh conversation import-codex-exports",
                )
            )
        parser.error(
            "conversation requires a subcommand "
            "(try: lrh conversation convert-codex-file, "
            "lrh conversation archive-codex-thread, "
            "lrh conversation export-codex-thread, "
            "lrh conversation current-codex-thread-id, "
            "lrh conversation import-codex-exports, "
            "lrh conversation inspect-export, or lrh conversation convert-pdf)"
        )

    if args.command == "prompt":
        raise SystemExit(
            prompt_workflow.run_prompt_cli(
                argv=passthrough_args,
                prog="lrh prompt",
            )
        )

    if args.command == "match":
        raise SystemExit(
            prompt_workflow_match.run_match_cli(
                argv=passthrough_args,
                prog="lrh match",
            )
        )

    if args.command == "search":
        raise SystemExit(
            prompt_workflow_search.run_search_cli(
                argv=passthrough_args,
                prog="lrh search",
            )
        )

    if args.command == "sessions":
        raise SystemExit(
            sessions_workflow.run_sessions_cli(
                argv=passthrough_args,
                prog="lrh sessions",
            )
        )

    if args.command == "memory":
        raise SystemExit(
            memory_workflow.run_memory_cli(
                argv=passthrough_args,
                prog="lrh memory",
            )
        )

    if args.command == "project":
        if args.project_command == "init":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")

            project_root = Path(args.project_root).expanduser().resolve()
            plan = bootstrap.build_plan(
                project_root=project_root,
                profile=args.profile,
                force=args.force,
            )
            formatted_plan = bootstrap.format_plan(plan, project_root)
            if formatted_plan:
                print(formatted_plan)
            print(
                f"summary: create={len(plan.to_create)} "
                f"skip={len(plan.to_skip)} update={len(plan.to_update)} "
                f"overwrite={len(plan.to_overwrite)}"
            )

            if args.dry_run:
                raise SystemExit(0)

            if args.check:
                needs_change = bool(
                    plan.to_create or plan.to_update or plan.to_overwrite
                )
                raise SystemExit(1 if needs_change else 0)

            result = bootstrap.apply_plan(
                project_root=project_root,
                profile=args.profile,
                force=args.force,
            )
            print(
                f"applied: created={len(result.created)} "
                f"skipped={len(result.skipped)} updated={len(result.updated)} "
                f"overwritten={len(result.overwritten)}"
            )
            raise SystemExit(0)

        if args.project_command == "doctor":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")

            project_root = Path(args.project_root).expanduser().resolve()
            diagnosis = doctor.diagnose_project(project_root)
            if args.json:
                print(doctor.format_json_report(diagnosis))
            else:
                print(doctor.format_text_report(diagnosis))

            if diagnosis.has_errors():
                raise SystemExit(1)
            if args.strict and diagnosis.has_warnings():
                raise SystemExit(1)
            raise SystemExit(0)

        parser.error(
            "project requires a subcommand"
            " (try: lrh project init or lrh project doctor)"
        )

    if args.command == "work-items":
        if args.work_items_command == "organize":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            if args.apply and args.dry_run:
                parser.error("--dry-run and --apply are mutually exclusive")
            project_root = Path(args.project_root).expanduser().resolve()
            plan = work_items_organize.plan_organization(project_root=project_root)
            print(work_items_organize.build_text_report(plan))
            if args.check:
                raise SystemExit(1 if plan.planned_changes() else 0)
            if args.apply:
                work_items_organize.apply_plan(plan)
                print(work_items_organize.build_text_report(plan, applied=True))
            raise SystemExit(0)
        if args.work_items_command == "validate":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            project_root = Path(args.project_root).expanduser().resolve()
            try:
                result = work_items_validate.validate_work_items(
                    project_root=project_root
                )
            except (OSError, UnicodeDecodeError):
                print("error: unable to read work-item files")
                raise SystemExit(2)
            if args.format == "json":
                print(work_items_validate.format_json(result))
            else:
                print(work_items_validate.format_text(result))
            raise SystemExit(1 if result.errors else 0)
        if args.work_items_command == "audit":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            project_root = Path(args.project_root).expanduser().resolve()
            try:
                report = work_items_audit.audit_work_items(project_root=project_root)
            except (OSError, UnicodeDecodeError):
                print("error: unable to read work-item files")
                raise SystemExit(2)
            if args.format == "json":
                print(work_items_audit.format_json(report))
            else:
                print(work_items_audit.format_markdown(report))
            raise SystemExit(0)
        if args.work_items_command == "readiness":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            project_root = Path(args.project_root).expanduser().resolve()
            try:
                report = work_items_readiness.evaluate_readiness(
                    project_root=project_root,
                    work_item_id=args.work_item_id,
                    status=args.status,
                )
            except work_items_readiness.WorkItemReadinessError as err:
                print(f"error: {err}")
                raise SystemExit(1) from err
            if args.format == "json":
                print(work_items_readiness.format_json(report))
            else:
                print(work_items_readiness.format_markdown(report))
            raise SystemExit(0)
        parser.error("work-items requires a subcommand (try: lrh work-items organize)")

    if args.command == "chain-defaults":
        if args.chain_defaults_command == "check-staleness":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            project_root = Path(args.project_root).expanduser().resolve()
            try:
                result = gate_staleness.check_gate_staleness(
                    project_root=project_root,
                    confirmed_commit=args.confirmed_commit,
                    head=args.head,
                )
            except gate_staleness.GateStalenessError as err:
                print(f"error: {err}")
                raise SystemExit(2) from err
            if args.format == "json":
                print(gate_staleness.format_json(result))
            else:
                print(gate_staleness.format_text(result))
            raise SystemExit(1 if result.stale else 0)
        parser.error(
            "chain-defaults requires a subcommand "
            "(try: lrh chain-defaults check-staleness)"
        )

    if args.command == "secrets":
        if args.secrets_command == "scan":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            project_root = Path(args.project_root).expanduser().resolve()
            out_dir = Path(args.out_dir).expanduser().resolve()
            result = secrets_scan.run_scan(project_root=project_root, out_dir=out_dir)
            if args.format == "json":
                print(secrets_scan.format_json(result))
            else:
                print(secrets_scan.format_text(result))
            raise SystemExit(0)
        if args.secrets_command == "review":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            if args.check and args.apply:
                parser.error("--check and --apply are mutually exclusive")
            out_dir = Path(args.out_dir).expanduser().resolve()
            decisions_path = (
                Path(args.decisions).expanduser().resolve() if args.decisions else None
            )
            try:
                report = secrets_review.build_report(
                    out_dir=out_dir, decisions_path=decisions_path
                )
            except secrets_review.ReviewInputError as err:
                if args.apply:
                    # A failed --apply must never leave a stale, marker-bearing
                    # replacements.reviewed.txt from an earlier successful
                    # --apply in this same --out-dir -- invalid input is just
                    # as much a failure as undecided findings.
                    secrets_review.invalidate_stale_reviewed(out_dir)
                print(f"error: {err}", file=sys.stderr)
                raise SystemExit(2) from err
            undecided = report.undecided()
            if args.apply:
                print(secrets_review.format_text(report))
                if undecided:
                    secrets_review.invalidate_stale_reviewed(out_dir)
                    print(
                        f"\nFAIL: {len(undecided)} finding(s) undecided; "
                        "cannot --apply until every finding is decided.",
                        file=sys.stderr,
                    )
                    raise SystemExit(1)
                reviewed_path = secrets_review.write_reviewed_replacements(
                    report, out_dir
                )
                print(f"\nWrote {len(report.kept())} secret(s) to {reviewed_path}")
                raise SystemExit(0)
            print(secrets_review.format_text(report))
            if args.check:
                raise SystemExit(1 if undecided else 0)
            raise SystemExit(0)
        if args.secrets_command == "purge":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            if args.dry_run and args.apply:
                parser.error("--dry-run and --apply are mutually exclusive")
            project_root = Path(args.project_root).expanduser().resolve()
            refs_file = Path(args.refs_file).expanduser().resolve()
            replacements_path = Path(args.replacements).expanduser().resolve()
            mirror_dir = (
                Path(args.mirror_dir).expanduser().resolve()
                if args.mirror_dir
                else None
            )
            try:
                output = secrets_purge.run_purge(
                    project_root=project_root,
                    source=args.source,
                    refs_file=refs_file,
                    replacements_path=replacements_path,
                    mirror_dir=mirror_dir,
                    apply=args.apply,
                )
            except secrets_purge.PurgeInputError as err:
                print(f"error: {err}", file=sys.stderr)
                raise SystemExit(2) from err
            print(output)
            raise SystemExit(0)
        parser.error(
            "secrets requires a subcommand "
            "(try: lrh secrets scan, lrh secrets review, or lrh secrets purge)"
        )

    if args.command == "workstreams":
        if args.workstreams_command == "organize":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            if args.apply and args.dry_run:
                parser.error("--dry-run and --apply are mutually exclusive")
            project_root = Path(args.project_root).expanduser().resolve()
            plan = workstreams_organize.plan_organization(project_root=project_root)
            if args.check:
                print(workstreams_organize.build_text_report(plan))
                raise SystemExit(1 if plan.planned_moves() else 0)
            if args.apply:
                try:
                    workstreams_organize.apply_plan(plan)
                except ValueError as err:
                    print(workstreams_organize.build_text_report(plan))
                    print(f"error: {err}")
                    raise SystemExit(1) from err
            print(workstreams_organize.build_text_report(plan, applied=args.apply))
            raise SystemExit(0)
        parser.error(
            "workstreams requires a subcommand (try: lrh workstreams organize)"
        )

    if args.command == "design":
        if args.design_command == "organize":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            project_root = Path(args.project_root).expanduser().resolve()
            plan = design_organize.plan_organization(project_root=project_root)
            if args.apply:
                try:
                    design_organize.apply_plan(plan)
                except ValueError as err:
                    print(design_organize.build_text_report(plan))
                    print(f"error: {err}")
                    raise SystemExit(1) from err
            print(design_organize.build_text_report(plan, applied=args.apply))
            raise SystemExit(0)
        parser.error("design requires a subcommand (try: lrh design organize)")

    if args.command == "meta":
        if args.meta_command == "init":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            spec = workspace.MetaWorkspaceSpec(workspace_name=args.name)
            try:
                if args.mode == "local":
                    result = workspace.init_workspace(
                        Path(
                            args.workspace_root_flag
                            or args.workspace_root
                            or Path.cwd()
                        ),
                        spec=spec,
                        force=args.force,
                    )
                elif args.mode == "hybrid":
                    result = workspace.init_hybrid_workspace(
                        Path(
                            args.workspace_root_flag
                            or args.workspace_root
                            or Path.cwd()
                        ),
                        spec=spec,
                        force=args.force,
                    )
                else:
                    result = workspace.init_global_workspace(
                        spec=spec,
                        force=args.force,
                    )
            except workspace.MetaInitError as err:
                print(f"error: {err}")
                raise SystemExit(1) from err

            if args.mode == "local":
                workspace_root = (
                    Path(args.workspace_root_flag or args.workspace_root or Path.cwd())
                    .expanduser()
                    .resolve()
                )
                print("Initialized LRH local meta workspace at", workspace_root)
            elif args.mode == "hybrid":
                workspace_root = (
                    Path(args.workspace_root_flag or args.workspace_root or Path.cwd())
                    .expanduser()
                    .resolve()
                )
                print("Initialized LRH hybrid meta workspace at", workspace_root)
            else:
                print("Initialized LRH global meta workspace")
            print(
                f"created={len(result.created)} "
                f"updated={len(result.updated)} "
                f"unchanged={len(result.unchanged)}"
            )
            raise SystemExit(0)

        if args.meta_command == "list":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            try:
                active_workspace = workspace.resolve_meta_workspace(
                    cwd=Path.cwd(),
                    options=workspace.MetaWorkspaceResolveOptions(
                        workspace_path=(
                            Path(args.workspace).expanduser()
                            if args.workspace
                            else None
                        ),
                        config_path=(
                            Path(args.config).expanduser() if args.config else None
                        ),
                        mode=args.mode,
                    ),
                )
                records = workspace.list_registered_projects_in_workspace(
                    active_workspace
                )
            except (
                workspace.MetaWorkspaceResolutionError,
                workspace.MetaRegistryError,
            ) as err:
                print(f"error: {err}")
                raise SystemExit(1) from err

            print(workspace.format_project_records(records, workspace=active_workspace))
            raise SystemExit(0)

        if args.meta_command == "where":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            try:
                active_workspace = workspace.resolve_meta_workspace(
                    cwd=Path.cwd(),
                    options=workspace.MetaWorkspaceResolveOptions(
                        workspace_path=(
                            Path(args.workspace).expanduser()
                            if args.workspace
                            else None
                        ),
                        config_path=(
                            Path(args.config).expanduser() if args.config else None
                        ),
                        mode=args.mode,
                    ),
                )
            except (
                workspace.MetaWorkspaceResolutionError,
                workspace.MetaRegistryError,
            ) as err:
                print(f"error: {err}")
                raise SystemExit(1) from err

            try:
                installed_version = lrh_version.get_installed_version()
                workspace_data = workspace.meta_workspace_where_payload(
                    active_workspace,
                    lrh_version=installed_version,
                )
                if args.json:
                    print(json.dumps(workspace_data, indent=2, sort_keys=True))
                else:
                    print(
                        workspace.format_meta_workspace_where(
                            active_workspace,
                            lrh_version=installed_version,
                        )
                    )
                raise SystemExit(0)
            except workspace.MetaRegistryError as err:
                print(f"error: {err}")
                raise SystemExit(1) from err

        if args.meta_command == "config":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            try:
                active_workspace = workspace.resolve_meta_workspace(
                    cwd=Path.cwd(),
                    options=workspace.MetaWorkspaceResolveOptions(
                        workspace_path=(
                            Path(args.workspace).expanduser()
                            if args.workspace
                            else None
                        ),
                        config_path=(
                            Path(args.config).expanduser() if args.config else None
                        ),
                        mode=args.mode,
                    ),
                )
                command = args.meta_config_command
                if command == "list":
                    values = workspace.read_meta_config(active_workspace)
                    for key, value in values.items():
                        print(f"{key}={'true' if value else 'false'}")
                    raise SystemExit(0)
                if command == "get":
                    value = workspace.get_meta_config_value(active_workspace, args.key)
                    print("true" if value else "false")
                    raise SystemExit(0)
                if command == "set":
                    value = workspace.set_meta_config_value(
                        active_workspace, args.key, args.value
                    )
                    print("true" if value else "false")
                    raise SystemExit(0)
                if command == "unset":
                    workspace.unset_meta_config_value(active_workspace, args.key)
                    print("false")
                    raise SystemExit(0)
                parser.error("meta config requires a subcommand (list/get/set/unset)")
            except (
                workspace.MetaWorkspaceResolutionError,
                workspace.MetaRegistryError,
                ValueError,
            ) as err:
                print(f"error: {err}")
                raise SystemExit(1) from err

        if args.meta_command == "register":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            spec = workspace.MetaRegisterSpec(
                repo_locator=args.repo_locator,
                project_dir=args.project_dir,
                directory_name=args.directory_name,
                short_name=args.short_name,
                display_name=args.display_name,
            )
            try:
                active_workspace = workspace.resolve_meta_workspace(
                    cwd=Path.cwd(),
                    options=workspace.MetaWorkspaceResolveOptions(
                        workspace_path=(
                            Path(args.workspace).expanduser()
                            if args.workspace
                            else None
                        ),
                        config_path=(
                            Path(args.config).expanduser() if args.config else None
                        ),
                        mode=args.mode,
                    ),
                )
                result = workspace.register_project_in_workspace(
                    active_workspace,
                    spec=spec,
                    force=args.force,
                )
            except (
                workspace.MetaWorkspaceResolutionError,
                workspace.MetaRegistryError,
            ) as err:
                print(f"error: {err}")
                raise SystemExit(1) from err

            print(f"Registered project in {result.record_path}")
            print(f"project_id={result.project_id}")
            print(f"setup_state={result.setup_state}")
            raise SystemExit(0)

        if args.meta_command == "refresh":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            try:
                active_workspace = workspace.resolve_meta_workspace(
                    cwd=Path.cwd(),
                    options=workspace.MetaWorkspaceResolveOptions(
                        workspace_path=(
                            Path(args.workspace).expanduser()
                            if args.workspace
                            else None
                        ),
                        config_path=(
                            Path(args.config).expanduser() if args.config else None
                        ),
                        mode=args.mode,
                    ),
                )
                result = workspace.refresh_project_observations_in_workspace(
                    active_workspace, selector=args.project
                )
            except (
                workspace.MetaWorkspaceResolutionError,
                workspace.MetaRegistryError,
            ) as err:
                print(f"error: {err}")
                raise SystemExit(1) from err
            print(f"Refreshed project observations in {result.record_path}")
            print(f"setup_state={result.setup_state}")
            raise SystemExit(0)

        if args.meta_command == "inspect":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            try:
                active_workspace = workspace.resolve_meta_workspace(
                    cwd=Path.cwd(),
                    options=workspace.MetaWorkspaceResolveOptions(
                        workspace_path=(
                            Path(args.workspace).expanduser()
                            if args.workspace
                            else None
                        ),
                        config_path=(
                            Path(args.config).expanduser() if args.config else None
                        ),
                        mode=args.mode,
                    ),
                )
                inspect_result = workspace.inspect_registered_project_in_workspace(
                    active_workspace,
                    selector=args.project,
                )
            except (
                workspace.MetaWorkspaceResolutionError,
                workspace.MetaRegistryError,
            ) as err:
                print(f"error: {err}")
                raise SystemExit(1) from err
            print(workspace.format_project_inspect(inspect_result))
            raise SystemExit(0)
        if args.meta_command == "set":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            try:
                active_workspace = workspace.resolve_meta_workspace(
                    cwd=Path.cwd(),
                    options=workspace.MetaWorkspaceResolveOptions(
                        workspace_path=(
                            Path(args.workspace).expanduser()
                            if args.workspace
                            else None
                        ),
                        config_path=(
                            Path(args.config).expanduser() if args.config else None
                        ),
                        mode=args.mode,
                    ),
                )
                result = workspace.set_project_fields_in_workspace(
                    active_workspace,
                    selector=args.project,
                    local_repo_path=args.local_repo_path,
                    project_dir=args.project_dir,
                    short_name=args.short_name,
                    display_name=args.display_name,
                )
            except (
                workspace.MetaWorkspaceResolutionError,
                workspace.MetaRegistryError,
            ) as err:
                print(f"error: {err}")
                raise SystemExit(1) from err
            if result.updated_record:
                print(f"Updated project record in {result.record_path}")
            for binding_path in result.binding_paths:
                print(f"Updated checkout binding in {binding_path}")
            print(f"project_id={result.project_id}")
            raise SystemExit(0)
        if args.meta_command == "unset":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            try:
                active_workspace = workspace.resolve_meta_workspace(
                    cwd=Path.cwd(),
                    options=workspace.MetaWorkspaceResolveOptions(
                        workspace_path=(
                            Path(args.workspace).expanduser()
                            if args.workspace
                            else None
                        ),
                        config_path=(
                            Path(args.config).expanduser() if args.config else None
                        ),
                        mode=args.mode,
                    ),
                )
                result = workspace.unset_project_fields_in_workspace(
                    active_workspace,
                    selector=args.project,
                    local_repo_path=args.local_repo_path,
                )
            except (
                workspace.MetaWorkspaceResolutionError,
                workspace.MetaRegistryError,
            ) as err:
                print(f"error: {err}")
                raise SystemExit(1) from err
            if result.updated_record:
                print(f"Updated project record in {result.record_path}")
            for binding_path in result.binding_paths:
                print(f"Updated checkout binding in {binding_path}")
            if not result.updated_record and not result.binding_paths:
                print("No checkout binding found to unset.")
            print(f"project_id={result.project_id}")
            raise SystemExit(0)

        parser.error("meta requires a subcommand (try: lrh meta init)")

    if args.command == "skills":
        if args.skills_command in {"install", "status", "check"}:
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            from lrh.skills import installer

            local_scope = None
            if args.scope is not None:
                local_scope = args.scope == "project"
            if args.local:
                if local_scope is False:
                    parser.error("--local cannot be combined with --scope user")
                local_scope = True
            try:
                skills_plan = installer.resolve_agent_skills_install_plan(
                    target=args.target,
                    local=local_scope,
                    project_root=Path.cwd(),
                    source=args.source,
                )
                if args.skills_command == "install":
                    reports = installer.install_skills_for_targets(
                        target=skills_plan.target,
                        local=skills_plan.local,
                        project_root=Path.cwd(),
                        dry_run=args.dry_run,
                        force=args.force,
                        source=skills_plan.source,
                    )
                else:
                    reports = installer.inspect_skills_for_targets(
                        target=skills_plan.target,
                        local=skills_plan.local,
                        project_root=Path.cwd(),
                        source=skills_plan.source,
                    )
            except installer.SkillSourceError as err:
                parser.error(str(err))
            for index, report in enumerate(reports):
                if len(reports) > 1:
                    if index:
                        print()
                    print(f"{report.target.value}: {report.skills_dir}")
                if args.skills_command == "install":
                    output = installer.format_report(report, dry_run=args.dry_run)
                elif args.skills_command == "status":
                    output = installer.format_inspection_report(
                        report, issue_label="notice"
                    )
                else:
                    output = installer.format_inspection_report(report)
                if output:
                    print(output)
                if args.skills_command == "install" and args.diff:
                    for result in report.results:
                        if result.status == installer.SkillStatus.USER_MODIFIED:
                            try:
                                diff_text = installer.diff_skill(
                                    result.name,
                                    report.skills_dir,
                                    source=skills_plan.source,
                                    project_root=Path.cwd(),
                                    target=report.target,
                                )
                            except installer.SkillSourceError as err:
                                parser.error(str(err))
                            if diff_text:
                                print(f"\n--- diff: {result.name} ---")
                                print(diff_text, end="")
            if args.skills_command == "check" and any(
                installer.inspection_report_has_failures(report) for report in reports
            ):
                raise SystemExit(1)
            raise SystemExit(0)
        parser.error("skills requires a subcommand (try: lrh skills install)")

    if passthrough_args:
        parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")

    print("Logical Robotics Harness bootstrap CLI")


if __name__ == "__main__":
    main()
