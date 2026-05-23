import contextlib
import io
import json
import pathlib
import socket
import tempfile
import threading
import unittest
import unittest.mock
import urllib.error
import urllib.request

from lrh import serve
from lrh.cli import main as cli_main


class TestLrhServeCli(unittest.TestCase):
    def test_lrh_serve_help_documents_safe_defaults(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with unittest.mock.patch("sys.argv", ["lrh", "serve", "--help"]):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as err_ctx:
                    cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(stderr.getvalue(), "")
        output = stdout.getvalue()
        self.assertIn("safe-default LRH local read-only viewer", output)
        self.assertIn("--host", output)
        self.assertIn("--port", output)
        self.assertIn("--allow-nonlocal-host", output)
        self.assertIn("not an autonomous runner", " ".join(output.split()))

    def test_default_config_binds_to_localhost(self) -> None:
        parser = serve.build_parser("lrh serve")
        args = parser.parse_args([])
        config = serve.config_from_args(args)

        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 8765)
        self.assertFalse(config.allow_nonlocal_host)

    def test_show_config_reports_no_write_or_agent_capabilities(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = serve.run_serve_cli(["--show-config"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["host"], "127.0.0.1")
        self.assertFalse(payload["capabilities"]["write_routes"])
        self.assertFalse(payload["capabilities"]["agent_dispatch"])
        self.assertFalse(payload["capabilities"]["branch_mutation"])
        self.assertFalse(payload["capabilities"]["pull_request_mutation"])
        self.assertFalse(payload["capabilities"]["arbitrary_file_serving"])

    def test_unsafe_host_requires_explicit_opt_in(self) -> None:
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as err_ctx:
                serve.run_serve_cli(["--host", "0.0.0.0", "--show-config"])

        self.assertEqual(err_ctx.exception.code, 2)
        self.assertIn("refusing to bind to '0.0.0.0'", stderr.getvalue())
        self.assertIn("--allow-nonlocal-host", stderr.getvalue())

    def test_unsafe_host_can_be_explicitly_opted_in_for_configuration(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = serve.run_serve_cli(
                [
                    "--host",
                    "0.0.0.0",
                    "--allow-nonlocal-host",
                    "--show-config",
                ]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["host"], "0.0.0.0")

    def test_ipv6_loopback_uses_ipv6_server_class(self) -> None:
        self.assertEqual(serve._address_family_for_host("::1"), socket.AF_INET6)

    @unittest.skipUnless(socket.has_ipv6, "IPv6 is unavailable")
    def test_ipv6_loopback_server_can_be_created(self) -> None:
        httpd = serve.create_http_server(serve.ServeConfig(host="::1", port=0))
        self.addCleanup(httpd.server_close)

        self.assertEqual(httpd.address_family, socket.AF_INET6)

    def test_project_root_status_uses_name_not_file_contents(self) -> None:
        config = serve.ServeConfig(project_root=pathlib.Path("/tmp/example-project"))
        payload = serve.status_payload(config)

        self.assertEqual(payload["project_root_name"], "example-project")
        self.assertNotIn("project_root", payload)


class TestLrhServeRoutes(unittest.TestCase):
    def _start_server(
        self, project_root: pathlib.Path | None = None
    ) -> tuple[serve.ThreadingHTTPServer, str]:
        config = serve.ServeConfig(
            port=0, project_root=project_root or pathlib.Path(".")
        )
        httpd = serve.create_http_server(config)
        host, port = httpd.server_address[:2]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(httpd.shutdown)
        self.addCleanup(httpd.server_close)
        return httpd, f"http://{host}:{port}"

    def _read(self, url: str) -> tuple[int, str, str]:
        with urllib.request.urlopen(url, timeout=5) as response:
            body = response.read().decode("utf-8")
            content_type = response.headers.get("Content-Type", "")
            return response.status, content_type, body

    def _head(self, url: str) -> tuple[int, str]:
        request = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(request, timeout=5) as response:
            content_type = response.headers.get("Content-Type", "")
            return response.status, content_type

    def test_index_health_and_status_routes_are_read_only_viewer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root)
            _httpd, base_url = self._start_server(root)

            index_status, index_type, index_body = self._read(base_url + "/")
            health_status, health_type, health_body = self._read(base_url + "/health")
            api_status, api_type, api_body = self._read(base_url + "/api/status")

        self.assertEqual(index_status, 200)
        self.assertIn("text/html", index_type)
        self.assertIn("Safe-default read-only project viewer", index_body)
        self.assertIn('class="lrh-app-shell"', index_body)
        self.assertIn('id="system-overview"', index_body)
        self.assertIn('class="lrh-status-badge lrh-status-badge--stable"', index_body)
        self.assertIn("Evidence summary", index_body)
        self.assertIn("Observed run/test evidence is not yet available", index_body)
        self.assertIn("Execution-ready leaves", index_body)
        self.assertIn("does not", index_body)
        self.assertEqual(health_status, 200)
        self.assertIn("application/json", health_type)
        self.assertEqual(json.loads(health_body), {"status": "ok"})
        self.assertEqual(api_status, 200)
        self.assertIn("application/json", api_type)
        payload = json.loads(api_body)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(
            payload["routes"],
            [
                "/",
                "/workbench",
                "/workbench/prompt",
                "/workbench/run-packet",
                "/workbench/run-report",
                "/meta",
                "/meta/project",
                "/project/<project_id>",
                "/project/<project_id>/designs/<design_id>",
                "/project/<project_id>/workstreams/<workstream_id>",
                "/project/<project_id>/work-items/<work_item_id>",
                "/project/<project_id>/work-items/<work_item_id>/prompt",
                "/health",
                "/api/status",
                "/api/project",
                "/api/workbench",
                "/api/meta",
                "/api/workbench/prompt",
                "/api/workbench/run-packet",
                "/api/workbench/run-report",
            ],
        )
        self.assertFalse(payload["capabilities"]["write_routes"])
        self.assertFalse(payload["capabilities"]["packet_generation"])
        self.assertEqual(payload["port"], _httpd.server_address[1])
        self.assertNotEqual(payload["port"], 0)

    def test_project_api_returns_read_only_project_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root)
            _httpd, base_url = self._start_server(root)

            status, content_type, body = self._read(base_url + "/api/project")

        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        payload = json.loads(body)
        self.assertEqual(payload["mode"], "safe-default-read-only-viewer")
        self.assertEqual(payload["project"]["name"], root.name)
        self.assertEqual(payload["validation"]["status"], "valid")
        self.assertEqual(payload["current_focus"]["id"], "FOCUS-1")
        self.assertEqual(payload["workstreams"]["by_status"], {"active": 1})
        self.assertEqual(
            [item["id"] for item in payload["active_workstreams"]], ["WS-A"]
        )
        self.assertEqual(payload["work_items"]["by_status"], {"active": 2})
        self.assertEqual(payload["work_items"]["by_type"], {"deliverable": 2})
        self.assertEqual(
            [item["id"] for item in payload["work_items"]["items"]], ["WI-A", "WI-B"]
        )
        self.assertEqual(payload["planning"]["active_leaf_ids"], ["WI-A", "WI-B"])
        self.assertEqual(payload["execution"]["ready_count"], 1)
        self.assertEqual(payload["execution"]["ready_work_items"][0]["id"], "WI-A")
        self.assertEqual(
            payload["execution"]["ready_work_items"][0]["run_packet"]["surface"],
            "lrh request run-packet-from-work-item",
        )
        self.assertFalse(payload["capabilities"]["agent_dispatch"])
        self.assertFalse(payload["capabilities"]["external_network_calls"])

    def test_project_api_reports_validation_warnings_and_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root, unknown_contributor=True)

            warning_payload = serve.project_viewer_payload(
                serve.ServeConfig(project_root=root)
            )

            _write_viewer_project(root, duplicate_work_item=True)
            error_payload = serve.project_viewer_payload(
                serve.ServeConfig(project_root=root)
            )

        self.assertEqual(warning_payload["validation"]["status"], "valid")
        self.assertEqual(warning_payload["validation"]["warning_count"], 1)
        self.assertIn(
            "FOCUS_UNKNOWN_ACTIVE_CONTRIBUTOR",
            [diagnostic["code"] for diagnostic in warning_payload["diagnostics"]],
        )
        self.assertEqual(error_payload["validation"]["status"], "error")
        self.assertGreaterEqual(error_payload["validation"]["error_count"], 1)
        self.assertEqual(error_payload["work_items"]["total"], 0)

    def test_project_api_handles_no_workstreams_or_ready_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_minimal_project(root)

            payload = serve.project_viewer_payload(serve.ServeConfig(project_root=root))

        self.assertEqual(payload["validation"]["status"], "valid")
        self.assertEqual(
            payload["workstreams"], {"total": 0, "by_status": {}, "items": []}
        )
        self.assertEqual(payload["active_workstreams"], [])
        self.assertEqual(payload["planning"]["active_leaf_ids"], [])
        self.assertEqual(payload["execution"]["ready_work_items"], [])
        self.assertEqual(payload["execution"]["ready_count"], 0)

    def test_workbench_html_uses_semantic_read_only_regions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root)
            _httpd, base_url = self._start_server(root)

            status, content_type, body = self._read(base_url + "/workbench")

        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn('class="lrh-page-header"', body)
        self.assertIn('class="lrh-guardrail-callout"', body)
        self.assertIn("Renderable work items", body)
        self.assertIn("Preview run packet", body)
        self.assertIn("does not execute prompts", body)

    def test_workbench_api_lists_deterministic_preview_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root)
            _httpd, base_url = self._start_server(root)

            status, content_type, body = self._read(base_url + "/api/workbench")

        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        payload = json.loads(body)
        self.assertEqual(payload["mode"], "safe-default-prompt-packet-report-workbench")
        self.assertEqual(
            [item["id"] for item in payload["work_items"]], ["WI-A", "WI-B"]
        )
        first = payload["work_items"][0]
        self.assertEqual(
            first["prompt_preview_url"], "/workbench/prompt?work_item=WI-A"
        )
        self.assertEqual(
            first["packet_preview_url"], "/workbench/run-packet?work_item=WI-A"
        )
        self.assertEqual(
            first["report_preview_url"], "/workbench/run-report?work_item=WI-A"
        )
        self.assertTrue(first["execution_ready"])
        self.assertIn("no agent dispatch or backend execution", payload["safety"])
        self.assertFalse(payload["capabilities"]["write_routes"])
        self.assertFalse(payload["capabilities"]["branch_mutation"])

    def test_workbench_prompt_preview_route_uses_prompt_renderer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root)
            _httpd, base_url = self._start_server(root)

            status, content_type, body = self._read(
                base_url + "/api/workbench/prompt?work_item=WI-A"
            )

        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        payload = json.loads(body)
        self.assertEqual(payload["kind"], "prompt")
        self.assertEqual(payload["work_item_id"], "WI-A")
        self.assertIn(
            "PROMPT(WI-A:LRH_SERVE_WORKBENCH_PREVIEW)[UNEXECUTED]", payload["markdown"]
        )
        self.assertIn("# ROLE", payload["markdown"])
        self.assertEqual(payload["diagnostics"], [])

    def test_project_work_item_route_shows_readiness_and_prompt_affordances(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root)
            _httpd, base_url = self._start_server(root)

            status, content_type, body = self._read(
                base_url + "/project/main/work-items/WI-A"
            )

        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn("Readiness state: <strong>ready</strong>", body)
        self.assertIn("Preview generated prompt", body)
        self.assertIn("Equivalent CLI:", body)

    def test_project_work_item_prompt_route_renders_escaped_prompt_preview(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root)
            _httpd, base_url = self._start_server(root)

            status, content_type, body = self._read(
                base_url + "/project/main/work-items/WI-A/prompt"
            )

        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn("Copy-friendly Markdown", body)
        self.assertIn("<textarea", body)

    def test_project_work_item_route_uses_selected_registered_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            alpha = root / "repos" / "alpha"
            _write_viewer_project(alpha)
            _write_local_meta_workspace(root)
            _write_project_record(root, "alpha", "repos/alpha", display_name="Alpha")
            _httpd, base_url = self._start_server(root)

            status, content_type, body = self._read(
                base_url + "/project/alpha/work-items/WI-A"
            )

        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn("Project: alpha", body)
        self.assertIn("Readiness state: <strong>ready</strong>", body)

    def test_project_work_item_prompt_route_uses_selected_registered_project(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            alpha = root / "repos" / "alpha"
            _write_viewer_project(alpha)
            _write_local_meta_workspace(root)
            _write_project_record(root, "alpha", "repos/alpha", display_name="Alpha")
            _httpd, base_url = self._start_server(root)

            status, content_type, body = self._read(
                base_url + "/project/alpha/work-items/WI-A/prompt"
            )

        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn("prompt: WI-A", body)
        self.assertIn("Copy-friendly Markdown", body)

    def test_workbench_run_packet_preview_reports_missing_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root)
            _httpd, base_url = self._start_server(root)

            status, _content_type, body = self._read(
                base_url + "/api/workbench/run-packet?work_item=WI-B"
            )

        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["kind"], "run-packet")
        self.assertIn("# Dry-Run Run Packet Review Required", payload["markdown"])
        self.assertIn("execution_ready must be true", payload["markdown"])
        self.assertTrue(payload["diagnostics"])

    def test_workbench_run_report_preview_route_uses_report_renderer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root)
            _httpd, base_url = self._start_server(root)

            status, _content_type, body = self._read(
                base_url + "/api/workbench/run-report?work_item=WI-A"
            )

        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["kind"], "run-report")
        self.assertIn("# Run Report: WI-A", payload["markdown"])
        self.assertIn("requires-human-review", payload["markdown"])
        self.assertIn("does not execute work", payload["markdown"])

    def test_workbench_artifact_html_labels_preview_as_not_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root)
            _httpd, base_url = self._start_server(root)

            status, content_type, body = self._read(
                base_url + "/workbench/run-packet?work_item=WI-A"
            )

        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn('class="lrh-workbench-artifact"', body)
        self.assertIn("Copy-friendly Markdown", body)
        self.assertIn("unavailable as execution", body)

    def test_workbench_download_is_in_memory_markdown_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root)
            _httpd, base_url = self._start_server(root)

            status, content_type, body = self._read(
                base_url + "/workbench/run-packet?work_item=WI-A&download=1"
            )

        self.assertEqual(status, 200)
        self.assertIn("text/markdown", content_type)
        self.assertIn("# Dry-Run Run Packet: WI-A", body)

    def test_project_and_workbench_routes_do_not_mutate_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root)
            tracked_file = root / "project" / "work_items" / "active" / "WI-A.md"
            before = tracked_file.stat().st_mtime_ns
            before_files = sorted(path.relative_to(root) for path in root.rglob("*"))
            _httpd, base_url = self._start_server(root)

            project_status, _content_type, _body = self._read(base_url + "/api/project")
            packet_status, _packet_type, _packet_body = self._read(
                base_url + "/api/workbench/run-packet?work_item=WI-A"
            )
            after = tracked_file.stat().st_mtime_ns
            after_files = sorted(path.relative_to(root) for path in root.rglob("*"))

        self.assertEqual(project_status, 200)
        self.assertEqual(packet_status, 200)
        self.assertEqual(after, before)
        self.assertEqual(after_files, before_files)

    def test_workbench_head_validates_artifact_work_item_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root)
            _httpd, base_url = self._start_server(root)

            html_status, html_type = self._head(
                base_url + "/workbench/run-packet?work_item=WI-A"
            )
            api_status, api_type = self._head(
                base_url + "/api/workbench/prompt?work_item=WI-A"
            )

            with self.assertRaises(urllib.error.HTTPError) as missing_query_ctx:
                self._head(base_url + "/workbench/run-packet")
            with self.assertRaises(urllib.error.HTTPError) as missing_item_ctx:
                self._head(base_url + "/api/workbench/prompt?work_item=missing")

        self.assertEqual(html_status, 200)
        self.assertIn("text/html", html_type)
        self.assertEqual(api_status, 200)
        self.assertIn("application/json", api_type)
        self.assertEqual(missing_query_ctx.exception.code, 404)
        self.assertEqual(missing_item_ctx.exception.code, 404)

    def test_meta_route_renders_empty_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_local_meta_workspace(root)
            _httpd, base_url = self._start_server(root)

            status, content_type, body = self._read(base_url + "/meta")

        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn("Meta Operational Triage", body)
        self.assertIn("Total registered projects shown: 0", body)
        self.assertIn("No registered projects", body)
        self.assertIn("Needs Attention (0)", body)
        self.assertIn("Unknown (0)", body)

    def test_meta_route_renders_multiple_projects_in_lane_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            alpha = root / "repos" / "alpha"
            beta = root / "repos" / "beta"
            _write_viewer_project(alpha)
            _write_viewer_project(beta)
            _write_local_meta_workspace(root)
            _write_project_record(root, "beta", "repos/beta", display_name="Beta")
            _write_project_record(root, "alpha", "repos/alpha", display_name="Alpha")
            _httpd, base_url = self._start_server(root)

            status, content_type, body = self._read(base_url + "/api/meta")

        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        payload = json.loads(body)
        self.assertEqual(
            [lane["label"] for lane in payload["lanes"]],
            [
                "Needs Attention",
                "Active Work",
                "Awaiting Review",
                "Stable",
                "Blocked",
                "Unknown",
            ],
        )
        active_lane = payload["lanes"][1]
        self.assertEqual(active_lane["count"], 2)
        self.assertEqual(
            [card["display_name"] for card in active_lane["projects"]],
            ["Alpha", "Beta"],
        )
        first_card = active_lane["projects"][0]
        self.assertEqual(first_card["source_state"], "live")
        self.assertEqual(first_card["validation_status"], "valid")
        self.assertEqual(first_card["active_work_item_count"], 2)
        self.assertEqual(first_card["ready_leaf_count"], 1)
        self.assertEqual(first_card["readiness_deficient_leaf_count"], 1)
        self.assertEqual(first_card["detail_url"], "/project/alpha")
        self.assertTrue(first_card["capability_gaps"])
        self.assertFalse(
            any(
                gap.get("field") == "source_state"
                and gap.get("state") == "not_implemented"
                for gap in first_card["capability_gaps"]
            )
        )

    def test_meta_route_isolates_unavailable_project_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_local_meta_workspace(root)
            (root / "projects" / "broken").mkdir(parents=True)
            _httpd, base_url = self._start_server(root)

            status, _content_type, body = self._read(base_url + "/api/meta")

        self.assertEqual(status, 200)
        payload = json.loads(body)
        needs_attention = payload["lanes"][0]
        self.assertEqual(needs_attention["count"], 1)
        broken = needs_attention["projects"][0]
        self.assertEqual(broken["display_name"], "broken")
        self.assertEqual(broken["source_state"], "unavailable")
        self.assertEqual(broken["validation_status"], "unavailable")
        self.assertIn("missing project record file", broken["diagnostics"][0])

    def test_meta_route_escapes_dynamic_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_local_meta_workspace(root)
            _write_project_record(
                root,
                "escape",
                "https://example.test/repo?<script>",
                display_name='<script>alert("x")</script>',
            )
            _httpd, base_url = self._start_server(root)

            status, _content_type, body = self._read(base_url + "/meta")

        self.assertEqual(status, 200)
        self.assertIn("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;", body)
        self.assertNotIn('<script>alert("x")</script>', body)
        self.assertIn("https://example.test/repo?&lt;script&gt;", body)

    def test_meta_route_honors_registered_project_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "repos" / "custom"
            _write_minimal_project(repo / "docs")
            _write_local_meta_workspace(root)
            _write_project_record(
                root,
                "custom",
                "repos/custom",
                display_name="Custom Dir",
                project_dir="docs/project",
            )
            _httpd, base_url = self._start_server(root)

            status, _content_type, body = self._read(base_url + "/api/meta")

        self.assertEqual(status, 200)
        payload = json.loads(body)
        stable_lane = payload["lanes"][3]
        self.assertEqual(stable_lane["count"], 1)
        custom = stable_lane["projects"][0]
        self.assertEqual(custom["display_name"], "Custom Dir")
        self.assertEqual(custom["source_state"], "live")
        self.assertEqual(custom["validation_status"], "valid")

    def test_meta_route_propagates_warning_counts_to_needs_attention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            warned = root / "repos" / "warned"
            _write_viewer_project(warned, unknown_contributor=True)
            _write_local_meta_workspace(root)
            _write_project_record(root, "warned", "repos/warned", display_name="Warned")
            _httpd, base_url = self._start_server(root)

            status, _content_type, body = self._read(base_url + "/api/meta")

        self.assertEqual(status, 200)
        payload = json.loads(body)
        needs_attention = payload["lanes"][0]
        self.assertEqual(needs_attention["count"], 1)
        warned_card = needs_attention["projects"][0]
        self.assertEqual(warned_card["display_name"], "Warned")
        self.assertEqual(warned_card["validation_status"], "valid")
        self.assertEqual(warned_card["validation_warning_count"], 1)
        self.assertEqual(warned_card["validation_diagnostics"], [])
        self.assertIsNone(warned_card["validation_next_action"])

    def test_meta_route_error_cards_include_actionable_validation_diagnostics(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            broken = root / "repos" / "broken"
            _write_viewer_project(broken, duplicate_work_item=True)
            _write_local_meta_workspace(root)
            _write_project_record(root, "broken", "repos/broken", display_name="Broken")
            _httpd, base_url = self._start_server(root)

            status, _content_type, body = self._read(base_url + "/api/meta")

        self.assertEqual(status, 200)
        payload = json.loads(body)
        broken_card = _find_meta_project(payload, "Broken")
        self.assertEqual(broken_card["validation_status"], "error")
        self.assertTrue(broken_card["validation_diagnostics"])
        self.assertTrue(
            any(
                "Validation errors:" in item
                for item in broken_card["validation_diagnostics"]
            )
        )
        self.assertIn("lrh validate", broken_card["validation_next_action"])

    def test_meta_route_error_cards_with_project_dir_dot_use_repo_root_command(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "repos" / "dot-root"
            _write_viewer_project(repo, duplicate_work_item=True)
            _write_local_meta_workspace(root)
            _write_project_record(
                root,
                "dot-root",
                "repos/dot-root",
                display_name="Dot Root",
                project_dir=".",
            )
            _httpd, base_url = self._start_server(root)

            status, _content_type, body = self._read(base_url + "/api/meta")

        self.assertEqual(status, 200)
        payload = json.loads(body)
        card = _find_meta_project(payload, "Dot Root")
        self.assertIn(
            f"cd {repo} && lrh validate",
            card["validation_next_action"],
        )

    def test_meta_route_error_card_validation_diagnostics_are_html_escaped(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            escaped = root / "repos" / "escaped"
            _write_viewer_project(escaped, duplicate_work_item=True)
            _write(
                escaped / "project" / "focus" / "current.md",
                """---
id: FOCUS-1
title: Focus
status: active
active_workstream_ids:
  - WS-A
active_contributor_ids:
  - contributor<script>
---
Body.
""",
            )
            _write_local_meta_workspace(root)
            _write_project_record(
                root, "escaped", "repos/escaped", display_name="Escaped"
            )
            _httpd, base_url = self._start_server(root)
            _status, _content_type, body = self._read(base_url + "/meta")

        self.assertIn("Validation diagnostics", body)
        self.assertIn("&amp;&amp; lrh validate", body)
        self.assertNotIn("<h4>Validation diagnostics</h4><p>None.</p>", body)

    def test_meta_route_valid_cards_do_not_render_validation_diagnostics_section(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root / "repos" / "alpha")
            _write_local_meta_workspace(root)
            _write_project_record(root, "alpha", "repos/alpha", display_name="Alpha")
            _httpd, base_url = self._start_server(root)
            _status, _content_type, body = self._read(base_url + "/meta")

        self.assertNotIn("<h4>Validation diagnostics</h4>", body)

    def test_meta_route_derives_review_blocked_stable_and_workstream_lanes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            active_stream = root / "repos" / "active-stream"
            review_stream = root / "repos" / "review-stream"
            blocked_repo = root / "repos" / "blocked"
            stable_repo = root / "repos" / "stable"
            _write_viewer_project(active_stream)
            _write_reviewing_workstream_project(review_stream)
            _write_blocked_project(blocked_repo)
            _write_minimal_project(stable_repo)
            _write_local_meta_workspace(root)
            _write_project_record(
                root, "active-stream", "repos/active-stream", display_name="Active"
            )
            _write_project_record(
                root, "review-stream", "repos/review-stream", display_name="Review"
            )
            _write_project_record(
                root, "blocked", "repos/blocked", display_name="Blocked"
            )
            _write_project_record(root, "stable", "repos/stable", display_name="Stable")
            _httpd, base_url = self._start_server(root)

            status, _content_type, body = self._read(base_url + "/api/meta")

        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["lanes"][1]["projects"][0]["display_name"], "Active")
        self.assertEqual(payload["lanes"][2]["projects"][0]["display_name"], "Review")
        self.assertEqual(payload["lanes"][3]["projects"][0]["display_name"], "Stable")
        self.assertEqual(payload["lanes"][4]["projects"][0]["display_name"], "Blocked")

    def test_meta_route_marks_local_path_without_project_missing_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            (root / "repos" / "empty").mkdir(parents=True)
            _write_local_meta_workspace(root)
            _write_project_record(root, "empty", "repos/empty", display_name="Empty")
            _httpd, base_url = self._start_server(root)

            status, _content_type, body = self._read(base_url + "/api/meta")

        self.assertEqual(status, 200)
        payload = json.loads(body)
        empty = payload["lanes"][0]["projects"][0]
        self.assertEqual(empty["display_name"], "Empty")
        self.assertEqual(empty["source_state"], "missing_project")
        self.assertIn("PROJECT_CONTROL_DIR_NOT_FOUND", empty["diagnostics"][0])

    def test_meta_route_marks_missing_local_checkout_as_missing_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_local_meta_workspace(root)
            _write_project_record(
                root,
                "missing-repo",
                "repos/missing-repo",
                display_name="Missing Repo",
            )
            _httpd, base_url = self._start_server(root)

            status, _content_type, body = self._read(base_url + "/api/meta")

        self.assertEqual(status, 200)
        payload = json.loads(body)
        project = _find_meta_project(payload, "Missing Repo")
        self.assertEqual(project["display_name"], "Missing Repo")
        self.assertEqual(project["source_state"], "missing_repo")
        self.assertIn("LOCAL_REPO_PATH_MISSING", project["diagnostics"][0])

    def test_meta_route_remote_only_includes_local_checkout_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_local_meta_workspace(root)
            _write_project_record(
                root,
                "remote-only",
                "https://example.test/team/remote-only",
                display_name="Remote Only",
            )
            _httpd, base_url = self._start_server(root)

            status, _content_type, body = self._read(base_url + "/api/meta")

        self.assertEqual(status, 200)
        payload = json.loads(body)
        project = _find_meta_project(payload, "Remote Only")
        self.assertEqual(project["display_name"], "Remote Only")
        self.assertEqual(project["source_state"], "needs_local_checkout")
        self.assertFalse(
            any(
                gap.get("field") == "source_state"
                and gap.get("state") == "not_implemented"
                for gap in project.get("capability_gaps", [])
            )
        )
        self.assertIn(
            "Run: lrh meta set remote-only --local-repo-path PATH",
            project["diagnostics"][0],
        )

    def test_meta_route_remote_only_card_orders_setup_guidance_before_diagnostics(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_local_meta_workspace(root)
            _write_project_record(
                root,
                "remote-only",
                "https://example.test/team/remote-only",
                display_name="Remote Only",
            )
            _httpd, base_url = self._start_server(root)
            status, _content_type, body = self._read(base_url + "/meta")

        self.assertEqual(status, 200)
        self.assertIn("Next useful action", body)
        self.assertIn("Diagnostics", body)
        self.assertLess(body.index("Next useful action"), body.index("Diagnostics"))

    def test_meta_route_remote_only_setup_guidance_shell_quotes_registry_name(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_local_meta_workspace(root)
            _write_project_record(
                root,
                "name with & hash#",
                "https://example.test/repo",
                display_name="Remote",
            )
            _httpd, base_url = self._start_server(root)
            _status, _content_type, body = self._read(base_url + "/meta")

        self.assertIn(
            (
                "Run: lrh meta set &#x27;name with &amp; hash#&#x27; "
                "--local-repo-path PATH"
            ),
            body,
        )

    def test_meta_route_falls_back_to_default_project_dir_when_record_omits_it(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "repos" / "legacy"
            _write_minimal_project(repo)
            _write_local_meta_workspace(root)
            _write_project_record(
                root,
                "legacy",
                "repos/legacy",
                display_name="Legacy",
                project_dir=None,
            )
            _httpd, base_url = self._start_server(root)

            status, _content_type, body = self._read(base_url + "/api/meta")

        self.assertEqual(status, 200)
        payload = json.loads(body)
        project = _find_meta_project(payload, "Legacy")
        self.assertEqual(project["source_state"], "live")
        self.assertEqual(project["validation_status"], "valid")

    def test_meta_detail_links_url_encode_registry_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_local_meta_workspace(root)
            _write_project_record(
                root,
                "name with & hash#",
                "https://example.test/repo",
                display_name="Remote",
            )
            _httpd, base_url = self._start_server(root)

            status, _content_type, body = self._read(base_url + "/api/meta")

        self.assertEqual(status, 200)
        payload = json.loads(body)
        card = payload["lanes"][5]["projects"][0]
        self.assertEqual(
            card["detail_url"],
            "/project/name%20with%20%26%20hash%23",
        )

    def test_project_dashboard_route_renders_registered_project_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            alpha = root / "repos" / "alpha"
            _write_viewer_project(alpha)
            _write_local_meta_workspace(root)
            _write_project_record(root, "alpha", "repos/alpha", display_name="Alpha")
            _httpd, base_url = self._start_server(root)

            status, content_type, body = self._read(base_url + "/project/alpha")

        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn("Project Operational Dashboard: Alpha", body)
        self.assertIn("Primary operational summary", body)
        self.assertIn("Validation summary", body)
        self.assertIn("Capability gaps", body)
        self.assertIn("Diagnostics and details", body)
        self.assertIn("Back to meta triage dashboard", body)
        self.assertIn('<a href="/project/alpha/designs/DP-1">', body)
        self.assertIn('<a href="/project/alpha/workstreams/WS-A">', body)
        self.assertLess(
            body.index("Primary operational summary"),
            body.index("Diagnostics and details"),
        )

    def test_design_detail_route_renders_lifecycle_and_traceability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            alpha = root / "repos" / "alpha"
            _write_viewer_project(alpha)
            _write_local_meta_workspace(root)
            _write_project_record(root, "alpha", "repos/alpha", display_name="Alpha")
            _httpd, base_url = self._start_server(root)

            status, content_type, body = self._read(
                base_url + "/project/alpha/designs/DP-1"
            )

        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn("Design: DP-1", body)
        self.assertIn("Status: adopted", body)
        self.assertIn("Implementation status: not_started", body)
        self.assertIn("Prompt actions are not implemented", body)

    def test_workstream_detail_route_renders_relationships_and_escaping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            alpha = root / "repos" / "alpha"
            _write_viewer_project(alpha)
            _write(
                alpha / "project" / "workstreams" / "active" / "WS-B.md",
                """---
id: WS-B
kind: planning_node
title: Child <stream>
status: active
stage: planning
parent_id: WS-A
---
Body.
""",
            )
            _write_local_meta_workspace(root)
            _write_project_record(root, "alpha", "repos/alpha", display_name="Alpha")
            _httpd, base_url = self._start_server(root)
            status, content_type, body = self._read(
                base_url + "/project/alpha/workstreams/WS-B"
            )
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn("Workstream: WS-B", body)
        self.assertIn("Parent: WS-A", body)
        self.assertIn("Child &lt;stream&gt;", body)

    def test_project_dashboard_route_escapes_dynamic_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_local_meta_workspace(root)
            _write_project_record(
                root,
                "escape",
                "https://example.test/repo?<script>",
                display_name='<script>alert("x")</script>',
            )
            _httpd, base_url = self._start_server(root)

            status, _content_type, body = self._read(base_url + "/project/escape")

        self.assertEqual(status, 200)
        self.assertIn("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;", body)
        self.assertNotIn('<script>alert("x")</script>', body)

    def test_project_dashboard_remote_only_shows_setup_guidance_before_facts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_local_meta_workspace(root)
            _write_project_record(
                root,
                "remote-only",
                "https://example.test/team/remote-only",
                display_name="Remote Only",
            )
            _httpd, base_url = self._start_server(root)
            status, _content_type, body = self._read(base_url + "/project/remote-only")

        self.assertEqual(status, 200)
        self.assertIn("Next useful action", body)
        self.assertIn("Validation summary", body)
        self.assertIn("lrh meta set remote-only --local-repo-path PATH", body)
        self.assertIn("errors: <span>Unknown / not implemented</span>", body)
        self.assertIn("warnings: <span>Unknown / not implemented</span>", body)
        self.assertLess(
            body.index("Next useful action"), body.index("Validation summary")
        )

    def test_project_dashboard_route_unknown_project_returns_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_local_meta_workspace(root)
            _httpd, base_url = self._start_server(root)

            with self.assertRaises(urllib.error.HTTPError) as err_ctx:
                urllib.request.urlopen(base_url + "/project/missing", timeout=5)

        self.assertEqual(err_ctx.exception.code, 404)

    def test_project_dashboard_head_supports_existing_and_missing_projects(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            alpha = root / "repos" / "alpha"
            _write_viewer_project(alpha)
            _write_local_meta_workspace(root)
            _write_project_record(root, "alpha", "repos/alpha", display_name="Alpha")
            _httpd, base_url = self._start_server(root)

            status, content_type = self._head(base_url + "/project/alpha")
            self.assertEqual(status, 200)
            self.assertIn("text/html", content_type)

            with self.assertRaises(urllib.error.HTTPError) as err_ctx:
                self._head(base_url + "/project/missing")

        self.assertEqual(err_ctx.exception.code, 404)

    def test_detail_routes_support_custom_project_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            alpha = root / "repos" / "alpha"
            _write_viewer_project(alpha / "control")
            _write_local_meta_workspace(root)
            _write_project_record(
                root,
                "alpha",
                "repos/alpha",
                display_name="Alpha",
                project_dir="control",
            )
            _httpd, base_url = self._start_server(root)
            design_status, _, _ = self._read(base_url + "/project/alpha/designs/DP-1")
            workstream_status, _, _ = self._read(
                base_url + "/project/alpha/workstreams/WS-A"
            )
        self.assertEqual(design_status, 200)
        self.assertEqual(workstream_status, 200)

    def test_detail_head_matches_get_not_found_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            alpha = root / "repos" / "alpha"
            _write_viewer_project(alpha)
            _write_local_meta_workspace(root)
            _write_project_record(root, "alpha", "repos/alpha", display_name="Alpha")
            _httpd, base_url = self._start_server(root)

            with self.assertRaises(urllib.error.HTTPError) as get_err:
                urllib.request.urlopen(
                    base_url + "/project/alpha/designs/DOES-NOT-EXIST", timeout=5
                )
            with self.assertRaises(urllib.error.HTTPError) as head_err:
                self._head(base_url + "/project/alpha/designs/DOES-NOT-EXIST")

        self.assertEqual(get_err.exception.code, 404)
        self.assertEqual(head_err.exception.code, 404)

    def test_meta_feature_introduces_no_write_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_local_meta_workspace(root)
            _httpd, base_url = self._start_server(root)

            request = urllib.request.Request(base_url + "/meta", method="POST")
            with self.assertRaises(urllib.error.HTTPError) as err_ctx:
                urllib.request.urlopen(request, timeout=5)

            status, content_type = self._head(base_url + "/meta")

        self.assertEqual(err_ctx.exception.code, 405)
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)

    def test_arbitrary_file_paths_are_not_served(self) -> None:
        _httpd, base_url = self._start_server()

        with self.assertRaises(urllib.error.HTTPError) as err_ctx:
            urllib.request.urlopen(base_url + "/pyproject.toml", timeout=5)

        self.assertEqual(err_ctx.exception.code, 404)
        body = err_ctx.exception.read().decode("utf-8")
        self.assertEqual(json.loads(body), {"error": "not_found"})

    def test_workbench_rejects_arbitrary_work_item_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            _write_viewer_project(root)
            _httpd, base_url = self._start_server(root)

            with self.assertRaises(urllib.error.HTTPError) as err_ctx:
                urllib.request.urlopen(
                    base_url + "/api/workbench/prompt?work_item=../../STYLE.md",
                    timeout=5,
                )

        self.assertEqual(err_ctx.exception.code, 404)
        body = err_ctx.exception.read().decode("utf-8")
        payload = json.loads(body)
        self.assertEqual(payload["error"], "not_found")

    def test_write_methods_are_rejected(self) -> None:
        _httpd, base_url = self._start_server()

        for method in ("POST", "PUT", "DELETE", "PATCH", "OPTIONS"):
            with self.subTest(method=method):
                request = urllib.request.Request(
                    base_url + "/api/project", method=method
                )

                with self.assertRaises(urllib.error.HTTPError) as err_ctx:
                    urllib.request.urlopen(request, timeout=5)

                self.assertEqual(err_ctx.exception.code, 405)
                body = err_ctx.exception.read().decode("utf-8")
                self.assertEqual(json.loads(body), {"error": "method_not_allowed"})


def _write_local_meta_workspace(root: pathlib.Path) -> None:
    _write(
        root / ".lrh" / "config.toml",
        "\n".join(
            [
                'schema_version = "0.1"',
                "",
                "[workspace]",
                'name = "test workspace"',
                'mode = "local"',
                "",
                "[paths]",
                f"catalog_root = {json.dumps(str(root))}",
                f"projects_dir = {json.dumps(str(root / 'projects'))}",
                f"config_dir = {json.dumps(str(root / '.lrh'))}",
                f"state_dir = {json.dumps(str(root / 'private' / 'state'))}",
                f"cache_dir = {json.dumps(str(root / 'private' / 'cache'))}",
                "",
            ]
        ),
    )
    (root / "projects").mkdir(parents=True, exist_ok=True)


def _find_meta_project(
    payload: dict[str, object], display_name: str
) -> dict[str, object]:
    for lane in payload["lanes"]:
        for project in lane["projects"]:
            if project["display_name"] == display_name:
                return project
    raise AssertionError(f"project {display_name!r} not found in meta payload")


def _write_project_record(
    root: pathlib.Path,
    registry_name: str,
    repo_locator: str,
    *,
    display_name: str,
    project_dir: str | None = "project",
) -> None:
    locator_lines = [f"repo_locator = {json.dumps(repo_locator)}"]
    if project_dir is not None:
        locator_lines.append(f"project_dir = {json.dumps(project_dir)}")
    _write(
        root / "projects" / registry_name / "project.toml",
        "\n".join(
            [
                'schema_version = "0.1"',
                "",
                "[project]",
                f"short_name = {json.dumps(registry_name)}",
                f"display_name = {json.dumps(display_name)}",
                'status = "active"',
                'setup_state = "unknown"',
                "",
                "[identity]",
                f"project_id = {json.dumps(f'proj-{registry_name}')}",
                "",
                "[locators]",
                *locator_lines,
                "",
                "[registry]",
                f"directory_name = {json.dumps(registry_name)}",
                "",
            ]
        ),
    )


def _write_minimal_project(root: pathlib.Path) -> None:
    project_dir = root / "project"
    (project_dir / "focus").mkdir(parents=True, exist_ok=True)
    (project_dir / "work_items").mkdir(parents=True, exist_ok=True)
    _write(
        project_dir / "focus" / "current_focus.md",
        """---
id: FOCUS-1
title: Current Focus
status: active
---
Focus body.
""",
    )


def _write_reviewing_workstream_project(root: pathlib.Path) -> None:
    _write_viewer_project(root)
    _write(
        root / "project" / "workstreams" / "active" / "WS-A.md",
        """---
id: WS-A
kind: planning_node
title: Active Stream
status: active
stage: reviewing
work_items:
  - WI-A
  - WI-B
---
Body.
""",
    )


def _write_blocked_project(root: pathlib.Path) -> None:
    _write_minimal_project(root)
    _write(
        root / "project" / "work_items" / "active" / "WI-DEP.md",
        """---
id: WI-DEP
title: Dependency
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
related_focus:
  - FOCUS-1
---
Body.
""",
    )
    _write(
        root / "project" / "work_items" / "active" / "WI-BLOCKED.md",
        """---
id: WI-BLOCKED
title: Blocked Work
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
blocked_by:
  - WI-DEP
related_focus:
  - FOCUS-1
---
Body.
""",
    )


def _write_viewer_project(
    root: pathlib.Path,
    *,
    unknown_contributor: bool = False,
    duplicate_work_item: bool = False,
) -> None:
    _write_minimal_project(root)
    project_dir = root / "project"
    focus_file = project_dir / "focus" / "current_focus.md"
    if unknown_contributor:
        focus_file.write_text(
            """---
id: FOCUS-1
title: Current Focus
status: active
active_contributors:
  - missing-contributor
---
Focus body.
""",
            encoding="utf-8",
        )
    (project_dir / "work_items" / "active").mkdir(parents=True, exist_ok=True)
    (project_dir / "workstreams" / "active").mkdir(parents=True, exist_ok=True)
    _write(
        project_dir / "work_items" / "active" / "WI-B.md",
        """---
id: WI-B
title: Beta
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
related_focus:
  - FOCUS-1
---
Body.
""",
    )
    _write(
        project_dir / "work_items" / "active" / "WI-A.md",
        """---
id: WI-A
title: Alpha
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
related_focus:
  - FOCUS-1
execution_ready: true
autonomy_level: human_gated
operation_risk: read_only
allowed_paths:
  - src/lrh/serve.py
forbidden_paths:
  - .env
validation_commands:
  - scripts/test
required_evidence:
  - tests
expected_artifacts:
  - viewer-summary
requires_human_approval: true
requires_human_merge: true
requires_human_closeout: true
policy_gates:
  - review
agent_constraints:
  - read-only serve route
---
## Summary
Build the safe-default workbench.

## Problem
Local users need previewable prompt, packet, and report artifacts.

## Scope
- Add workbench preview routes.
- Keep all actions read-only.

## Out of Scope
- Agent dispatch.
- Branch mutation.

## Required Changes
- Render prompt previews.
- Render packet previews.
- Render report previews.

## Validation
- scripts/test

## Acceptance Criteria
- Prompt preview is available.
- Packet preview is available.
- Report preview is available.
""",
    )
    if duplicate_work_item:
        _write(
            project_dir / "work_items" / "active" / "WI-DUP.md",
            """---
id: WI-A
title: Duplicate Alpha
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
---
Body.
""",
        )
    _write(
        project_dir / "workstreams" / "active" / "WS-A.md",
        """---
id: WS-A
kind: planning_node
title: Active Stream
status: active
stage: executing
work_items:
  - WI-A
  - WI-B
---
Body.
""",
    )
    _write(
        project_dir / "design" / "proposals" / "adopted" / "DP-1.md",
        """---
id: DP-1
type: design_proposal
title: Design One
status: adopted
implementation_status: not_started
implemented_by:
  - WI-A
related_workstreams:
  - WS-A
---
Body.
""",
    )


def _write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
