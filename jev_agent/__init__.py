"""Drop-in Jev integration for Codex-driven agent workflows."""

from __future__ import annotations

import threading
from typing import Any, Mapping, Optional

from .browser_workflow import (
    ActionCandidate,
    ActionDecision,
    BrowserJevWorkflow,
    JevFallbackRequired,
    parse_action_decision,
)
from .env_config import load_env
from .jev_client import (
    DEFAULT_ENDPOINT,
    DEFAULT_MODEL,
    JevApiError,
    JevClient,
    JevConfigurationError,
    JevError,
    JevQuotaExhausted,
    JevTransportError,
    JevUnavailable,
)

# Importing jev_agent is enough to pick up a local env file. Existing environment
# variables still win, which keeps deployment/CI configuration authoritative.
load_env()

_default_client: Optional[JevClient] = None
_default_client_lock = threading.Lock()


def get_default_client() -> JevClient:
    global _default_client
    with _default_client_lock:
        if _default_client is None:
            _default_client = JevClient()
        return _default_client


def jev_judge(
    state: str,
    questions: Mapping[str, Any],
    timeout: float = 10,
) -> Mapping[str, Any]:
    """Convenience function matching the simple integration example."""

    return get_default_client().judge(state, questions, timeout=timeout)


def is_jev_available() -> bool:
    """Cheap check before doing expensive DOM/candidate preparation."""

    return get_default_client().is_available()


__all__ = [
    "ActionCandidate",
    "ActionDecision",
    "BrowserJevWorkflow",
    "DEFAULT_ENDPOINT",
    "DEFAULT_MODEL",
    "JevApiError",
    "JevClient",
    "JevConfigurationError",
    "JevError",
    "JevFallbackRequired",
    "JevQuotaExhausted",
    "JevTransportError",
    "JevUnavailable",
    "get_default_client",
    "is_jev_available",
    "jev_judge",
    "load_env",
    "parse_action_decision",
]
