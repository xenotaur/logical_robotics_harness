import os
import socket
import unittest
import urllib.error
import urllib.request
from unittest import mock

from local_agent import model, settings

DIGEST = "a" * 64


class FakeTransport:
    """Records calls and serves canned Ollama API responses."""

    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, object, float]] = []

    def __call__(self, method, url, body, timeout):
        self.calls.append((method, url, body, timeout))
        path = url.split("11434", 1)[1]
        response = self.responses[path]
        if isinstance(response, BaseException):
            raise response
        return response


def _healthy(**overrides: object) -> dict[str, object]:
    responses: dict[str, object] = {
        "/api/version": {"version": "0.32.5"},
        "/api/tags": {"models": [{"name": "gemma4:12b", "digest": DIGEST}]},
        "/api/show": {"details": {"quantization_level": "Q4_K_M"}},
        "/api/chat": {
            "message": {"content": "{}"},
            "done_reason": "stop",
            "prompt_eval_count": 10,
            "eval_count": 5,
        },
    }
    responses.update(overrides)
    return responses


def _adapter(transport: FakeTransport, **kwargs: object) -> model.OllamaModel:
    return model.OllamaModel(
        base_url="http://127.0.0.1:11434",
        model="gemma4:12b",
        manifest_digest=DIGEST,
        transport=transport,
        **kwargs,
    )


class OpenerTest(unittest.TestCase):
    def test_opener_ignores_proxy_environment(self) -> None:
        proxy_env = {"http_proxy": "http://proxy.invalid:3128"}
        with mock.patch.dict(os.environ, proxy_env):
            default = urllib.request.build_opener()
            opener = model.build_opener()

        def proxies(director: urllib.request.OpenerDirector) -> list[dict]:
            return [
                handler.proxies
                for handler in director.handlers
                if isinstance(handler, urllib.request.ProxyHandler)
            ]

        # Control: a default opener would route through the env proxy.
        self.assertIn({"http": "http://proxy.invalid:3128"}, proxies(default))
        self.assertFalse(any(proxies(opener)))

    def test_opener_refuses_redirects(self) -> None:
        opener = model.build_opener()
        redirect_handlers = [
            handler
            for handler in opener.handlers
            if isinstance(handler, urllib.request.HTTPRedirectHandler)
        ]
        self.assertEqual(len(redirect_handlers), 1)
        self.assertIsNone(
            redirect_handlers[0].redirect_request(
                None, None, 302, "Found", {}, "http://example.com/"
            )
        )


class OllamaLocalOnlyTest(unittest.TestCase):
    def test_non_loopback_endpoint_refused(self) -> None:
        for url in (
            "http://10.0.0.5:11434",
            "https://127.0.0.1:11434",
            "http://ollama.com",
        ):
            with self.assertRaises(model.BackendError) as caught:
                model.OllamaModel(base_url=url, transport=FakeTransport({}))
            self.assertEqual(caught.exception.kind, model.KIND_MISSING_PREREQUISITE)

    def test_cloud_tagged_model_refused(self) -> None:
        with self.assertRaisesRegex(model.BackendError, "cloud"):
            model.OllamaModel(model="gemma4:31b-cloud", transport=FakeTransport({}))

    def test_preflight_passes_for_pinned_local_model(self) -> None:
        transport = FakeTransport(_healthy())
        result = _adapter(transport).preflight()
        self.assertEqual(result["manifest_digest"], DIGEST)
        self.assertIn("pinned_manifest_digest", result["checks"])

    def test_digest_mismatch_refused(self) -> None:
        tags = {"models": [{"name": "gemma4:12b", "digest": "b" * 64}]}
        with self.assertRaisesRegex(model.BackendError, "digest mismatch"):
            _adapter(FakeTransport(_healthy(**{"/api/tags": tags}))).preflight()

    def test_remote_fields_refused_before_prompting(self) -> None:
        tags = {
            "models": [
                {"name": "gemma4:12b", "digest": DIGEST, "remote_host": "ollama.com"}
            ]
        }
        transport = FakeTransport(_healthy(**{"/api/tags": tags}))
        with self.assertRaisesRegex(model.BackendError, "remote"):
            _adapter(transport).preflight()
        self.assertFalse(any(call[1].endswith("/api/chat") for call in transport.calls))

        show = {"remote_model": "gemma4:31b"}
        with self.assertRaisesRegex(model.BackendError, "remote"):
            _adapter(FakeTransport(_healthy(**{"/api/show": show}))).preflight()

    def test_missing_model_is_missing_prerequisite(self) -> None:
        tags = {"models": [{"name": "qwen3:8b", "digest": DIGEST}]}
        with self.assertRaises(model.BackendError) as caught:
            _adapter(FakeTransport(_healthy(**{"/api/tags": tags}))).preflight()
        self.assertEqual(caught.exception.kind, model.KIND_MISSING_PREREQUISITE)

    def test_unreachable_service_is_missing_prerequisite(self) -> None:
        error = urllib.error.URLError(ConnectionRefusedError("refused"))
        with self.assertRaises(model.BackendError) as caught:
            _adapter(FakeTransport(_healthy(**{"/api/version": error}))).preflight()
        self.assertEqual(caught.exception.kind, model.KIND_MISSING_PREREQUISITE)

    def test_timeout_is_classified(self) -> None:
        transport = FakeTransport(_healthy(**{"/api/chat": socket.timeout("slow")}))
        request = model.ModelRequest("p", {"type": "object"}, settings.Budgets())
        with self.assertRaises(model.BackendError) as caught:
            _adapter(transport).generate(request)
        self.assertEqual(caught.exception.kind, model.KIND_TIMEOUT)

    def test_generate_sends_budgets_schema_and_no_tools(self) -> None:
        transport = FakeTransport(_healthy())
        budgets = settings.Budgets(num_ctx=1024, max_output_tokens=64)
        request = model.ModelRequest("hello", {"type": "object"}, budgets)
        response = _adapter(transport).generate(request)
        method, url, body, timeout = transport.calls[-1]
        self.assertEqual((method, url.rsplit("/", 2)[-2:]), ("POST", ["api", "chat"]))
        self.assertNotIn("tools", body)
        self.assertEqual(body["format"], {"type": "object"})
        self.assertEqual(body["options"]["num_ctx"], 1024)
        self.assertEqual(body["options"]["num_predict"], 64)
        self.assertEqual(timeout, budgets.wall_time_seconds)
        self.assertEqual(response.prompt_tokens, 10)


if __name__ == "__main__":
    unittest.main()
