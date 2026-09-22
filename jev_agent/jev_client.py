"""Quota-aware client for the Typesafe / SystemOne Jev API.

The client is intentionally dependency-free.  It uses ``urllib`` by default,
but accepts an injected transport so it can also be used with ``requests`` or
an existing agent HTTP abstraction.

Important behaviour:
* a confirmed exhausted quota opens a persistent circuit breaker;
* temporary rate limits and transport failures use a short cooldown;
* no request is sent while the circuit breaker is open;
* the state is written atomically so separate agent processes see it.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

LOGGER = logging.getLogger(__name__)

DEFAULT_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
DEFAULT_STATE_PATH = ".jev_quota_state.json"


class JevError(RuntimeError):
    """Base class for Jev integration errors."""


class JevConfigurationError(JevError):
    """The client is not configured well enough to make a request."""


class JevUnavailable(JevError):
    """Jev is temporarily or permanently disabled by the circuit breaker."""

    def __init__(self, reason: str, status: Optional[Mapping[str, Any]] = None):
        super().__init__(reason)
        self.reason = reason
        self.status = dict(status or {})


class JevQuotaExhausted(JevUnavailable):
    """The account/API allowance is exhausted."""


class JevTransportError(JevError):
    """The HTTP transport failed before receiving an API response."""


class JevApiError(JevError):
    """The API returned an unsuccessful response."""

    def __init__(self, message: str, status_code: int, body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


@dataclass(frozen=True)
class HttpResponse:
    """Small transport-neutral response object."""

    status_code: int
    headers: Mapping[str, str]
    body: bytes


class UrllibTransport:
    """Default zero-dependency JSON POST transport."""

    def post(
        self,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout: float,
    ) -> HttpResponse:
        request = urllib_request.Request(
            url,
            data=body,
            headers=dict(headers),
            method="POST",
        )
        try:
            with urllib_request.urlopen(request, timeout=timeout) as response:
                return HttpResponse(
                    status_code=int(response.status),
                    headers={k.lower(): v for k, v in response.headers.items()},
                    body=response.read(),
                )
        except HTTPError as exc:
            return HttpResponse(
                status_code=int(exc.code),
                headers={k.lower(): v for k, v in exc.headers.items()},
                body=exc.read(),
            )
        except (URLError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            raise JevTransportError(f"Jev transport error: {reason}") from exc


def _header(headers: Mapping[str, str], name: str) -> Optional[str]:
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return str(value)
    return None


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _parse_duration(value: Optional[str]) -> Optional[float]:
    """Parse values such as ``30``, ``1.5s``, ``2m`` and ``1h``."""

    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    multiplier = 1.0
    if text.endswith("ms"):
        multiplier = 0.001
        text = text[:-2]
    elif text.endswith("s"):
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 60.0
        text = text[:-1]
    elif text.endswith("h"):
        multiplier = 3600.0
        text = text[:-1]
    try:
        return max(0.0, float(text) * multiplier)
    except ValueError:
        return None


def _parse_reset_at(
    headers: Mapping[str, str], now: float, default_delay: float
) -> Optional[float]:
    retry_after = _header(headers, "retry-after")
    delay = _parse_duration(retry_after)
    if delay is not None:
        return now + delay
    if retry_after:
        try:
            parsed = parsedate_to_datetime(retry_after)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return max(now, parsed.timestamp())
        except (TypeError, ValueError, OverflowError):
            pass

    for name in ("x-ratelimit-reset-after", "x-rate-limit-reset-after"):
        delay = _parse_duration(_header(headers, name))
        if delay is not None:
            return now + delay

    for name in ("x-ratelimit-reset", "x-rate-limit-reset"):
        raw = _parse_int(_header(headers, name))
        if raw is None:
            continue
        if raw > 10_000_000_000:
            # Unix timestamp in milliseconds.
            return max(now, raw / 1000.0)
        if raw >= 1_000_000_000:
            # Unix timestamp in seconds.
            return max(now, float(raw))
        # Small values are commonly seconds remaining until reset.
        return now + max(0, raw)

    return now + default_delay


def _is_quota_body(body: str) -> bool:
    text = body.lower()
    markers = (
        "insufficient_quota",
        "quota_exceeded",
        "quota exceeded",
        "quota exhausted",
        "out of credits",
        "no credits",
        "credit balance",
        "billing hard limit",
        "usage limit reached",
        "额度不足",
        "额度耗尽",
        "余额不足",
    )
    return any(marker in text for marker in markers)


def _json_or_text(body: bytes) -> Any:
    if not body:
        return {}
    text = body.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


class JevStateStore:
    """Thread-safe, optionally persistent circuit-breaker state."""

    def __init__(
        self,
        path: Optional[Path] = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.path = Path(path).expanduser() if path is not None else None
        self._clock = clock
        self._lock = threading.RLock()
        self._state: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.path is None or not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
        except (OSError, ValueError):
            LOGGER.warning("Could not read Jev quota state from %s", self.path)
            return {}

    def _save_locked(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._state, ensure_ascii=False, indent=2)
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            dir=str(self.path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(temp_name, self.path)
        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass

    def _clear_locked(self) -> None:
        if self._state:
            self._state = {}
            self._save_locked()

    def status(self) -> Dict[str, Any]:
        with self._lock:
            if not self._state.get("disabled"):
                result = dict(self._state)
                result["available"] = True
                return result
            disabled_until = self._state.get("disabled_until")
            if disabled_until is not None and self._clock() >= float(disabled_until):
                self._clear_locked()
                return {"available": True}
            result = dict(self._state)
            result["available"] = False
            return result

    def block(
        self,
        kind: str,
        reason: str,
        disabled_until: Optional[float] = None,
    ) -> None:
        with self._lock:
            previous_state = dict(self._state)
            current_until = self._state.get("disabled_until")
            if self._state.get("disabled") and current_until is None:
                return
            if current_until is not None and disabled_until is not None:
                disabled_until = max(float(current_until), float(disabled_until))
            self._state = {
                "disabled": True,
                "kind": kind,
                "reason": reason,
                "disabled_until": disabled_until,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            for key in ("remaining", "limit"):
                if key in previous_state:
                    self._state[key] = previous_state[key]
            self._save_locked()

    def update_quota_headers(self, headers: Mapping[str, str]) -> None:
        remaining = _parse_int(_header(headers, "x-ratelimit-remaining"))
        limit = _parse_int(_header(headers, "x-ratelimit-limit"))
        with self._lock:
            if remaining is not None:
                self._state["remaining"] = remaining
            if limit is not None:
                self._state["limit"] = limit
            self._save_locked()
        if remaining == 0:
            reset_at = _parse_reset_at(
                headers,
                now=self._clock(),
                default_delay=60.0,
            )
            self.block(
                "quota",
                "Jev quota exhausted (X-RateLimit-Remaining is 0)",
                reset_at,
            )

    def clear(self) -> None:
        with self._lock:
            self._clear_locked()


class JevClient:
    """Call Jev with a persistent quota circuit breaker.

    ``transport`` only needs a ``post(url, headers, body, timeout)`` method
    returning :class:`HttpResponse`.  This makes the client straightforward to
    test and easy to adapt to an existing ``requests.Session`` wrapper.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 10.0,
        state_path: Optional[str] = None,
        persist_state: bool = True,
        transport: Optional[Any] = None,
        temporary_cooldown: float = 15.0,
        rate_limit_cooldown: float = 30.0,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("TYPESAFE_API_KEY")
        self.endpoint = endpoint or os.getenv("TYPESAFE_API_ENDPOINT", DEFAULT_ENDPOINT)
        self.model = model or os.getenv("JEV_MODEL", DEFAULT_MODEL)
        self.timeout = float(timeout)
        self.temporary_cooldown = float(temporary_cooldown)
        self.rate_limit_cooldown = float(rate_limit_cooldown)
        self.transport = transport or UrllibTransport()
        self._clock = clock
        self._request_lock = threading.RLock()

        if persist_state:
            configured_path = state_path or os.getenv("JEV_STATE_PATH", DEFAULT_STATE_PATH)
            resolved_path: Optional[Path] = Path(configured_path)
        else:
            resolved_path = None
        self._store = JevStateStore(resolved_path, clock=clock)

    @property
    def state_path(self) -> Optional[Path]:
        return self._store.path

    def status(self) -> Dict[str, Any]:
        return self._store.status()

    def is_available(self) -> bool:
        return bool(self._store.status().get("available"))

    def reset(self) -> None:
        """Manually close the breaker, for example after adding credits."""

        self._store.clear()

    def judge(
        self,
        state: str,
        questions: Mapping[str, Any],
        timeout: Optional[float] = None,
    ) -> Mapping[str, Any]:
        """Run one Jev judgement or raise a Jev-specific exception."""

        if not isinstance(state, str) or not state.strip():
            raise ValueError("state must be a non-empty string")
        if not isinstance(questions, Mapping) or not questions:
            raise ValueError("questions must be a non-empty mapping")
        if not self.api_key:
            raise JevConfigurationError("TYPESAFE_API_KEY is not configured")

        with self._request_lock:
            current = self._store.status()
            if not current.get("available"):
                kind = current.get("kind")
                message = current.get("reason") or "Jev is unavailable"
                if kind == "quota":
                    raise JevQuotaExhausted(message, current)
                raise JevUnavailable(message, current)

            payload = {
                "model": self.model,
                "state": state,
                "questions": dict(questions),
            }
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            request_timeout = self.timeout if timeout is None else float(timeout)
            try:
                response = self.transport.post(
                    self.endpoint,
                    headers,
                    body,
                    request_timeout,
                )
            except JevError:
                raise
            except Exception as exc:
                raise JevTransportError(f"Jev transport error: {exc}") from exc

            parsed = _json_or_text(response.body)

            if not 200 <= response.status_code < 300:
                self._handle_error(response, parsed)
                raise AssertionError("unreachable")

            if isinstance(parsed, Mapping) and parsed.get("error"):
                error_text = json.dumps(parsed, ensure_ascii=False)
                if _is_quota_body(error_text):
                    self._block_quota(error_text, response.headers)
                    raise JevQuotaExhausted(error_text, self._store.status())
                raise JevApiError(
                    f"Jev returned an error body: {error_text}",
                    response.status_code,
                    error_text,
                )

            self._store.update_quota_headers(response.headers)
            if not isinstance(parsed, Mapping):
                raise JevApiError(
                    "Jev returned a non-object JSON response",
                    response.status_code,
                    str(parsed),
                )
            return parsed

    def judge_or_none(
        self,
        state: str,
        questions: Mapping[str, Any],
        timeout: Optional[float] = None,
    ) -> Optional[Mapping[str, Any]]:
        """Convenience wrapper for agents that always have an LLM fallback."""

        try:
            return self.judge(state, questions, timeout=timeout)
        except JevError as exc:
            LOGGER.warning("Skipping Jev: %s", exc)
            return None

    def _block_quota(
        self,
        reason: str,
        headers: Mapping[str, str],
    ) -> None:
        now = self._clock()
        reset_at = _parse_reset_at(
            headers,
            now=now,
            default_delay=0.0,
        )
        # A zero default means no reset header: keep it disabled indefinitely.
        if reset_at is not None and reset_at <= now + 0.001:
            reset_at = None
        self._store.block("quota", reason, reset_at)

    def _handle_error(self, response: HttpResponse, parsed: Any) -> None:
        body_text = (
            json.dumps(parsed, ensure_ascii=False) if not isinstance(parsed, str) else parsed
        )
        status = response.status_code

        if status == 402 or (status in (403, 429) and _is_quota_body(body_text)):
            self._block_quota(body_text or "Jev quota exhausted", response.headers)
            raise JevQuotaExhausted(
                f"Jev quota exhausted (HTTP {status})",
                self._store.status(),
            )

        if status in (401, 403):
            reason = f"Jev authentication/authorization failed (HTTP {status})"
            self._store.block("auth", reason, None)
            raise JevUnavailable(reason, self._store.status())

        if status == 429:
            until = _parse_reset_at(
                response.headers,
                now=self._clock(),
                default_delay=self.rate_limit_cooldown,
            )
            reason = "Jev rate limit reached"
            self._store.block("temporary", reason, until)
            raise JevUnavailable(reason, self._store.status())

        if status >= 500:
            until = self._clock() + self.temporary_cooldown
            reason = f"Jev server error (HTTP {status})"
            self._store.block("temporary", reason, until)
            raise JevApiError(f"{reason}: {body_text}", status, body_text)

        raise JevApiError(
            f"Jev request failed (HTTP {status}): {body_text}",
            status,
            body_text,
        )
