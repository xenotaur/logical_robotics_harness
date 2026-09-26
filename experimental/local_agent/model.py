"""Model adapters: a deterministic fake and a local-only Ollama client.

The model never receives tools. Adapters expose only a preflight check and a
single ``generate`` call. The Ollama adapter refuses non-loopback endpoints,
disables HTTP proxies and redirects, requires the pinned local manifest digest,
and rejects models the service reports as remote or cloud-hosted before any
prompt is sent.
"""

from __future__ import annotations

import dataclasses
import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any, Protocol

from local_agent import settings

KIND_MISSING_PREREQUISITE = "missing_prerequisite"
KIND_BACKEND_ERROR = "backend_error"
KIND_TIMEOUT = "timeout"

_LOOPBACK_HOSTS = ("127.0.0.1", "::1", "localhost")
_REMOTE_FIELDS = ("remote_host", "remote_model")


class BackendError(Exception):
    """A classified failure from a model backend."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


@dataclasses.dataclass(frozen=True)
class ModelRequest:
    prompt: str
    output_schema: dict[str, object]
    budgets: settings.Budgets


@dataclasses.dataclass(frozen=True)
class ModelResponse:
    text: str
    done_reason: str | None
    prompt_tokens: int | None
    output_tokens: int | None
    backend_timings: dict[str, object]


class ModelAdapter(Protocol):
    def describe(self) -> dict[str, object]: ...

    def preflight(self) -> dict[str, object]: ...

    def generate(self, request: ModelRequest) -> ModelResponse: ...


class FakeModel:
    """Scripted backend for deterministic tests and dry runs.

    Each script entry is either a ``ModelResponse`` to return or an exception
    to raise. ``preflight_error`` simulates a failing preflight.
    """

    def __init__(
        self,
        script: list[ModelResponse | BaseException],
        *,
        preflight_error: BackendError | None = None,
    ) -> None:
        self._script = list(script)
        self._preflight_error = preflight_error
        self.requests: list[ModelRequest] = []

    def describe(self) -> dict[str, object]:
        return {"backend": "fake", "model": "fake", "local_only": True}

    def preflight(self) -> dict[str, object]:
        if self._preflight_error is not None:
            raise self._preflight_error
        return {"backend": "fake", "checks": ["scripted"]}

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        if not self._script:
            raise BackendError(KIND_BACKEND_ERROR, "fake script exhausted")
        step = self._script.pop(0)
        if isinstance(step, BaseException):
            raise step
        return step


Transport = Callable[[str, str, dict[str, object] | None, float], dict[str, Any]]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: object, **kwargs: object) -> None:
        return None


def build_opener() -> urllib.request.OpenerDirector:
    """An opener with no proxies (ignores *_proxy env vars) and no redirects."""
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())


def urllib_transport(
    method: str, url: str, body: dict[str, object] | None, timeout: float
) -> dict[str, Any]:
    """JSON-over-HTTP with proxies and redirects disabled."""
    opener = build_opener()
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    with opener.open(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def check_loopback_url(base_url: str) -> None:
    parsed = urllib.parse.urlparse(base_url)
    if parsed.username is not None or parsed.password is not None:
        raise BackendError(
            KIND_MISSING_PREREQUISITE,
            "endpoint must not embed credentials (user info) in the URL",
        )
    if parsed.scheme != "http" or parsed.hostname not in _LOOPBACK_HOSTS:
        raise BackendError(
            KIND_MISSING_PREREQUISITE,
            f"endpoint must be plain http on a loopback host, got {base_url!r}",
        )


class OllamaModel:
    """Local-only Ollama chat client pinned to one installed model."""

    def __init__(
        self,
        *,
        base_url: str = settings.DEFAULT_OLLAMA_BASE_URL,
        model: str = settings.DEFAULT_MODEL,
        manifest_digest: str = settings.DEFAULT_MODEL_MANIFEST_DIGEST,
        transport: Transport = urllib_transport,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        check_loopback_url(base_url)
        if "cloud" in model.lower():
            raise BackendError(
                KIND_MISSING_PREREQUISITE, f"cloud-tagged model refused: {model}"
            )
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._digest = manifest_digest.removeprefix("sha256:")
        # The weight-layer pin is only known for the pre-registered model; a
        # fallback or custom model records none rather than a false value.
        self._layer_digest: str | None = None
        if model == settings.DEFAULT_MODEL and self._digest == (
            settings.DEFAULT_MODEL_MANIFEST_DIGEST
        ):
            self._layer_digest = settings.DEFAULT_MODEL_LAYER_DIGEST
        self._transport = transport
        self._clock = clock
        self._server_version: str | None = None

    def describe(self) -> dict[str, object]:
        return {
            "backend": "ollama",
            "base_url": self._base_url,
            "model": self._model,
            "manifest_digest": self._digest,
            "model_layer_digest": self._layer_digest,
            "server_version": self._server_version,
            "local_only": True,
        }

    def _call(
        self, method: str, path: str, body: dict[str, object] | None, timeout: float
    ) -> dict[str, Any]:
        try:
            return self._transport(method, f"{self._base_url}{path}", body, timeout)
        except (TimeoutError, socket.timeout) as error:
            raise BackendError(KIND_TIMEOUT, f"{path} timed out") from error
        except urllib.error.HTTPError as error:
            raise BackendError(
                KIND_BACKEND_ERROR, f"{path} returned HTTP {error.code}"
            ) from error
        except urllib.error.URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                raise BackendError(KIND_TIMEOUT, f"{path} timed out") from error
            raise BackendError(
                KIND_MISSING_PREREQUISITE,
                f"inference service unreachable at {self._base_url}: {error.reason}",
            ) from error
        except (ConnectionError, OSError) as error:
            raise BackendError(
                KIND_MISSING_PREREQUISITE,
                f"inference service unreachable at {self._base_url}: {error}",
            ) from error
        except ValueError as error:
            raise BackendError(
                KIND_BACKEND_ERROR, f"{path} returned invalid JSON"
            ) from error

    def preflight(self) -> dict[str, object]:
        """Verify local-only serving of the pinned model before any prompt."""
        version = self._call("GET", "/api/version", None, 10.0)
        self._server_version = str(version.get("version"))

        tags = self._call("GET", "/api/tags", None, 10.0)
        entries = [
            entry
            for entry in tags.get("models", [])
            if entry.get("name") == self._model or entry.get("model") == self._model
        ]
        if not entries:
            raise BackendError(
                KIND_MISSING_PREREQUISITE, f"model not installed locally: {self._model}"
            )
        entry = entries[0]
        if any(field in entry for field in _REMOTE_FIELDS):
            raise BackendError(
                KIND_MISSING_PREREQUISITE, f"model is served remotely: {self._model}"
            )
        observed = str(entry.get("digest", "")).removeprefix("sha256:")
        if observed != self._digest:
            raise BackendError(
                KIND_MISSING_PREREQUISITE,
                f"model digest mismatch: expected {self._digest}, got {observed}",
            )

        show = self._call("POST", "/api/show", {"model": self._model}, 10.0)
        if any(field in show for field in _REMOTE_FIELDS):
            raise BackendError(
                KIND_MISSING_PREREQUISITE,
                f"service reports remote serving for {self._model}",
            )
        details = show.get("details", {}) if isinstance(show, dict) else {}
        return {
            "backend": "ollama",
            "server_version": self._server_version,
            "manifest_digest": observed,
            "quantization": details.get("quantization_level"),
            "parameter_size": details.get("parameter_size"),
            "checks": [
                "loopback_endpoint",
                "proxies_and_redirects_disabled",
                "pinned_manifest_digest",
                "no_remote_fields_in_tags",
                "no_remote_fields_in_show",
            ],
        }

    def generate(self, request: ModelRequest) -> ModelResponse:
        budgets = request.budgets
        body: dict[str, object] = {
            "model": self._model,
            "messages": [{"role": "user", "content": request.prompt}],
            "stream": False,
            "format": request.output_schema,
            "options": {
                "num_ctx": budgets.num_ctx,
                "num_predict": budgets.max_output_tokens,
                "temperature": budgets.temperature,
                "seed": budgets.seed,
            },
        }
        started = self._clock()
        result = self._call("POST", "/api/chat", body, budgets.wall_time_seconds)
        elapsed = self._clock() - started
        # The socket timeout is not a total wall-clock bound; enforce it here.
        if elapsed > budgets.wall_time_seconds:
            raise BackendError(
                KIND_TIMEOUT,
                f"/api/chat took {elapsed:.1f}s, over the "
                f"{budgets.wall_time_seconds:.0f}s wall-time budget",
            )
        message = result.get("message") or {}
        return ModelResponse(
            text=str(message.get("content", "")),
            done_reason=result.get("done_reason"),
            prompt_tokens=result.get("prompt_eval_count"),
            output_tokens=result.get("eval_count"),
            backend_timings={
                "client_elapsed_seconds": round(elapsed, 3),
                "total_duration_ns": result.get("total_duration"),
                "load_duration_ns": result.get("load_duration"),
                "prompt_eval_duration_ns": result.get("prompt_eval_duration"),
                "eval_duration_ns": result.get("eval_duration"),
            },
        )
