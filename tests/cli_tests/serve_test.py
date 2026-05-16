import contextlib
import io
import json
import pathlib
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
        self.assertIn("safe-default LRH local server skeleton", output)
        self.assertIn("--host", output)
        self.assertIn("--port", output)
        self.assertIn("--allow-nonlocal-host", output)
        self.assertIn("not an autonomous runner", output)

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

    def test_project_root_status_uses_name_not_file_contents(self) -> None:
        config = serve.ServeConfig(project_root=pathlib.Path("/tmp/example-project"))
        payload = serve.status_payload(config)

        self.assertEqual(payload["project_root_name"], "example-project")
        self.assertNotIn("project_root", payload)


class TestLrhServeRoutes(unittest.TestCase):
    def _start_server(self) -> tuple[serve.ThreadingHTTPServer, str]:
        config = serve.ServeConfig(port=0)
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

    def test_index_health_and_status_routes_are_read_only_skeleton(self) -> None:
        _httpd, base_url = self._start_server()

        index_status, index_type, index_body = self._read(base_url + "/")
        health_status, health_type, health_body = self._read(base_url + "/health")
        api_status, api_type, api_body = self._read(base_url + "/api/status")

        self.assertEqual(index_status, 200)
        self.assertIn("text/html", index_type)
        self.assertIn("Safe-default local server skeleton", index_body)
        self.assertIn("does not", index_body)
        self.assertEqual(health_status, 200)
        self.assertIn("application/json", health_type)
        self.assertEqual(json.loads(health_body), {"status": "ok"})
        self.assertEqual(api_status, 200)
        self.assertIn("application/json", api_type)
        payload = json.loads(api_body)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["routes"], ["/", "/health", "/api/status"])
        self.assertFalse(payload["capabilities"]["write_routes"])

    def test_arbitrary_file_paths_are_not_served(self) -> None:
        _httpd, base_url = self._start_server()

        with self.assertRaises(urllib.error.HTTPError) as err_ctx:
            urllib.request.urlopen(base_url + "/pyproject.toml", timeout=5)

        self.assertEqual(err_ctx.exception.code, 404)
        body = err_ctx.exception.read().decode("utf-8")
        self.assertEqual(json.loads(body), {"error": "not_found"})

    def test_write_methods_are_rejected(self) -> None:
        _httpd, base_url = self._start_server()
        request = urllib.request.Request(base_url + "/api/status", method="POST")

        with self.assertRaises(urllib.error.HTTPError) as err_ctx:
            urllib.request.urlopen(request, timeout=5)

        self.assertEqual(err_ctx.exception.code, 405)
        body = err_ctx.exception.read().decode("utf-8")
        self.assertEqual(json.loads(body), {"error": "method_not_allowed"})


if __name__ == "__main__":
    unittest.main()
