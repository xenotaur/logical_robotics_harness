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
        # clear=True so other *_proxy variables on the host cannot merge in.
        with mock.patch.dict(os.environ, proxy_env, clear=True):
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


class FakeStream:
    def __init__(self, chunks: list[dict]) -> None:
        self.chunks = chunks
        self.calls: list[tuple] = []

    def __call__(self, url, body, timeout):
        self.calls.append((url, body, timeout))
        for chunk in self.chunks:
            if isinstance(chunk, BaseException):
                raise chunk
            yield chunk


class OllamaStreamingTest(unittest.TestCase):
    def _adapter(self, stream: FakeStream, clock=None) -> model.OllamaModel:
        kwargs = {"clock": clock} if clock else {}
        return model.OllamaModel(
            base_url="http://127.0.0.1:11434",
            model="gemma4:12b",
            manifest_digest=DIGEST,
            transport=FakeTransport(_healthy()),
            stream_transport=stream,
            **kwargs,
        )

    def test_streams_text_with_thinking_off_and_no_format(self) -> None:
        stream = FakeStream(
            [
                {"message": {"content": "Hel", "thinking": "hmm"}},
                {"message": {"content": "lo"}},
                {
                    "message": {"content": ""},
                    "done": True,
                    "done_reason": "stop",
                    "eval_count": 2,
                    "prompt_eval_count": 9,
                },
            ]
        )
        seen: list[str] = []
        request = model.ModelRequest("p", None, settings.Budgets(), on_text=seen.append)
        response = self._adapter(stream).generate(request)
        url, body, _ = stream.calls[0]
        self.assertTrue(url.endswith("/api/chat"))
        self.assertIs(body["think"], False)
        self.assertTrue(body["stream"])
        self.assertNotIn("format", body)
        self.assertNotIn("tools", body)
        self.assertEqual(seen, ["Hel", "lo"])
        self.assertEqual(response.text, "Hello")
        self.assertEqual(response.thinking_chars, 3)
        self.assertEqual(response.output_tokens, 2)

    def test_stream_without_done_is_backend_error(self) -> None:
        stream = FakeStream([{"message": {"content": "cut"}}])
        request = model.ModelRequest(
            "p", None, settings.Budgets(), on_text=lambda _: None
        )
        with self.assertRaises(model.BackendError) as caught:
            self._adapter(stream).generate(request)
        self.assertEqual(caught.exception.kind, model.KIND_BACKEND_ERROR)

    def test_stream_stops_when_wall_time_runs_out(self) -> None:
        ticks = iter([0.0, 400.0, 400.0])
        stream = FakeStream(
            [{"message": {"content": "a"}}, {"message": {"content": "b"}}]
        )
        request = model.ModelRequest(
            "p", None, settings.Budgets(), on_text=lambda _: None
        )
        with self.assertRaises(model.BackendError) as caught:
            self._adapter(stream, clock=lambda: next(ticks)).generate(request)
        self.assertEqual(caught.exception.kind, model.KIND_TIMEOUT)

    def test_stream_error_chunk_keeps_its_message(self) -> None:
        stream = FakeStream([{"error": "model ran out of memory"}])
        request = model.ModelRequest(
            "p", None, settings.Budgets(), on_text=lambda _: None
        )
        with self.assertRaisesRegex(model.BackendError, "out of memory"):
            self._adapter(stream).generate(request)

    def test_output_failure_is_not_reported_as_backend_failure(self) -> None:
        stream = FakeStream([{"message": {"content": "a"}}])

        def broken(_: str) -> None:
            raise BrokenPipeError("stdout closed")

        request = model.ModelRequest("p", None, settings.Budgets(), on_text=broken)
        with self.assertRaises(BrokenPipeError):
            self._adapter(stream).generate(request)

    def test_stream_socket_timeout_is_classified(self) -> None:
        stream = FakeStream([socket.timeout("slow")])
        request = model.ModelRequest(
            "p", None, settings.Budgets(), on_text=lambda _: None
        )
        with self.assertRaises(model.BackendError) as caught:
            self._adapter(stream).generate(request)
        self.assertEqual(caught.exception.kind, model.KIND_TIMEOUT)


class OllamaLocalOnlyTest(unittest.TestCase):
    def test_credentials_are_reported_first_and_never_echoed(self) -> None:
        for url in (
            "http://bob:hunter2@127.0.0.1:99999",
            "http://bob:hunter2@127.0.0.1:11434",
        ):
            with self.subTest(url):
                with self.assertRaises(model.BackendError) as caught:
                    model.check_loopback_url(url)
                self.assertIn("credentials", str(caught.exception))
                self.assertNotIn("hunter2", str(caught.exception))

    def test_non_loopback_error_does_not_echo_the_url(self) -> None:
        with self.assertRaises(model.BackendError) as caught:
            model.check_loopback_url("http://gpu-box.corp.internal:11434/?t=abc123")
        message = str(caught.exception)
        self.assertNotIn("abc123", message)
        self.assertNotIn("gpu-box", message)

    def test_extra_url_parts_are_rejected_without_echo(self) -> None:
        for url in (
            "http://127.0.0.1:11434/x",
            "http://127.0.0.1:11434/?session=opaque123",
            "http://127.0.0.1:11434/;p=opaque123",
            "http://localhost:11434#opaque123",
        ):
            with self.subTest(url):
                with self.assertRaises(model.BackendError) as caught:
                    model.check_loopback_url(url)
                self.assertEqual(caught.exception.kind, model.KIND_MISSING_PREREQUISITE)
                self.assertNotIn("opaque123", str(caught.exception))
        for url in (
            "http://127.0.0.1:11434",
            "http://127.0.0.1:11434/",
            "http://[::1]",
        ):
            with self.subTest(url):
                model.check_loopback_url(url)

    def test_unparsable_url_is_refused_without_echo(self) -> None:
        for url in (
            "http://[SECRETTOKEN]:11434",
            "http://[::1]SECRETTOKEN:11434",
            "http://SECRETTOKEN@[::1",
        ):
            with self.subTest(url):
                with self.assertRaises(model.BackendError) as caught:
                    model.check_loopback_url(url)
                self.assertEqual(caught.exception.kind, model.KIND_MISSING_PREREQUISITE)
                self.assertNotIn("SECRETTOKEN", str(caught.exception))

    def test_whitespace_and_control_characters_are_refused(self) -> None:
        for url in (
            " http://127.0.0.1:11434",
            "http://127.0.0.1:11434 ",
            "http://loc\nalhost:11434",
            "http://127.0.0.1:11434\t",
        ):
            with self.subTest(repr(url)):
                with self.assertRaisesRegex(model.BackendError, "whitespace"):
                    model.check_loopback_url(url)

    def test_accepted_url_is_rebuilt_from_host_and_port(self) -> None:
        cases = {
            "http://127.0.0.1:11434": "http://127.0.0.1:11434",
            "http://127.0.0.1:11434/": "http://127.0.0.1:11434",
            "http://127.0.0.1:11434?": "http://127.0.0.1:11434",
            "http://localhost:11434#": "http://localhost:11434",
            "HTTP://LOCALHOST:11434/;": "http://localhost:11434",
            "http://[::1]": "http://[::1]",
            "http://[::1]:11434/": "http://[::1]:11434",
        }
        for url, expected in cases.items():
            with self.subTest(url):
                self.assertEqual(model.check_loopback_url(url), expected)

    def test_invalid_port_rejected(self) -> None:
        for url in ("http://127.0.0.1:99999", "http://localhost:abc"):
            with self.subTest(url):
                with self.assertRaises(model.BackendError) as caught:
                    model.check_loopback_url(url)
                self.assertEqual(caught.exception.kind, model.KIND_MISSING_PREREQUISITE)

    def test_non_loopback_endpoint_refused(self) -> None:
        for url in (
            "http://10.0.0.5:11434",
            "https://127.0.0.1:11434",
            "http://ollama.com",
        ):
            with self.assertRaises(model.BackendError) as caught:
                model.OllamaModel(base_url=url, transport=FakeTransport({}))
            self.assertEqual(caught.exception.kind, model.KIND_MISSING_PREREQUISITE)

    def test_userinfo_in_endpoint_refused(self) -> None:
        with self.assertRaisesRegex(model.BackendError, "credentials"):
            model.OllamaModel(
                base_url="http://user:secret@127.0.0.1:11434",
                transport=FakeTransport({}),
            )

    def test_layer_digest_only_for_preregistered_model(self) -> None:
        pinned = model.OllamaModel(transport=FakeTransport({}))
        self.assertEqual(
            pinned.describe()["model_layer_digest"],
            settings.DEFAULT_MODEL_LAYER_DIGEST,
        )
        fallback = model.OllamaModel(
            model="qwen3:8b", manifest_digest=DIGEST, transport=FakeTransport({})
        )
        self.assertIsNone(fallback.describe()["model_layer_digest"])

    def test_total_wall_time_overrun_is_timeout(self) -> None:
        ticks = iter([0.0, 301.0])
        adapter = _adapter(FakeTransport(_healthy()), clock=lambda: next(ticks))
        request = model.ModelRequest("p", {"type": "object"}, settings.Budgets())
        with self.assertRaises(model.BackendError) as caught:
            adapter.generate(request)
        self.assertEqual(caught.exception.kind, model.KIND_TIMEOUT)

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
