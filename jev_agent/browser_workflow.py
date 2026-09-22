"""Jev-first browser action selection with an LLM fallback.

Typical integration:

1. Convert the current DOM/page into a compact ``state`` string.
2. Convert clickable elements into :class:`ActionCandidate` objects.
3. Ask Jev to choose one candidate.
4. Auto-execute only when Jev's confidence is at least ``min_confidence``.
5. Otherwise call the existing LLM decider and execute its result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, Optional, Sequence

from .jev_client import JevClient, JevError

FALLBACK_REASON_LOW_CONFIDENCE = "low_confidence"
FALLBACK_REASON_MISSING_CONFIDENCE = "missing_confidence"
FALLBACK_REASON_INVALID_KEY = "invalid_key"
FALLBACK_REASON_JEV_UNAVAILABLE = "jev_unavailable"


@dataclass(frozen=True)
class ActionCandidate:
    """One clickable browser action exposed to Jev."""

    key: str
    label: str
    description: str = ""
    role: str = ""
    disabled: bool = False
    dangerous: bool = False

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ActionCandidate":
        """Build a candidate from common DOM/Selenium/Playwright dictionaries."""

        key = value.get("key") or value.get("id") or value.get("selector")
        if not key:
            raise ValueError("candidate mapping requires key, id, or selector")
        text = value.get("label") or value.get("text") or value.get("aria_label") or ""
        return cls(
            key=str(key),
            label=str(text),
            description=str(value.get("description") or value.get("hint") or ""),
            role=str(value.get("role") or value.get("tag") or ""),
            disabled=bool(value.get("disabled", False)),
            dangerous=bool(value.get("dangerous", False)),
        )

    def prompt_text(self) -> str:
        parts = [self.label or self.key]
        if self.role:
            parts.append(f"role={self.role}")
        if self.description:
            parts.append(self.description)
        if self.dangerous:
            parts.append("potentially destructive")
        return "; ".join(parts)


@dataclass(frozen=True)
class ActionDecision:
    """A validated action selected by Jev or the LLM fallback."""

    key: str
    confidence: Optional[float]
    source: str
    rationale: str = ""
    raw: Optional[Mapping[str, Any]] = field(default=None, compare=False)

    def meets_confidence(self, threshold: float) -> bool:
        return self.confidence is not None and self.confidence >= threshold


FallbackDecider = Callable[
    [str, Sequence[ActionCandidate], str],
    ActionDecision,
]
ClickAction = Callable[[str], Any]


class JevFallbackRequired(RuntimeError):
    """Raised when Jev cannot make a trusted decision and no fallback exists."""

    def __init__(self, reason: str, decision: Optional[ActionDecision] = None):
        super().__init__(reason)
        self.reason = reason
        self.decision = decision


class BrowserJevWorkflow:
    """Select and optionally execute the next browser action."""

    def __init__(
        self,
        client: JevClient,
        fallback_decider: Optional[FallbackDecider] = None,
        min_confidence: float = 0.7,
    ) -> None:
        if not 0.0 <= float(min_confidence) <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")
        self.client = client
        self.fallback_decider = fallback_decider
        self.min_confidence = float(min_confidence)

    def decide_next_action(
        self,
        state: str,
        candidates: Sequence[ActionCandidate],
        timeout: Optional[float] = None,
    ) -> ActionDecision:
        """Choose one action, using Jev only when its answer is trustworthy."""

        if not candidates:
            raise ValueError("at least one action candidate is required")
        candidate_map = self._candidate_map(candidates)
        fallback_reason: Optional[str] = None
        jev_decision: Optional[ActionDecision] = None

        if self.client.is_available():
            try:
                raw = self.client.judge(
                    state,
                    self.build_questions(candidates),
                    timeout=timeout,
                )
                jev_decision = parse_action_decision(raw, candidate_map)
            except JevError:
                fallback_reason = FALLBACK_REASON_JEV_UNAVAILABLE
        else:
            fallback_reason = FALLBACK_REASON_JEV_UNAVAILABLE

        if jev_decision is None:
            fallback_reason = fallback_reason or FALLBACK_REASON_INVALID_KEY
        elif jev_decision.confidence is None:
            fallback_reason = FALLBACK_REASON_MISSING_CONFIDENCE
        elif not jev_decision.meets_confidence(self.min_confidence):
            fallback_reason = FALLBACK_REASON_LOW_CONFIDENCE

        if fallback_reason is None:
            return jev_decision  # type: ignore[return-value]

        if self.fallback_decider is None:
            raise JevFallbackRequired(fallback_reason, jev_decision)
        fallback = self.fallback_decider(state, candidates, fallback_reason)
        return self._validate_fallback(fallback, candidate_map)

    def click_next_action(
        self,
        state: str,
        candidates: Sequence[ActionCandidate],
        click: ClickAction,
        timeout: Optional[float] = None,
    ) -> ActionDecision:
        """Select one action and execute it through the supplied click hook."""

        decision = self.decide_next_action(state, candidates, timeout=timeout)
        click(decision.key)
        return decision

    @staticmethod
    def build_questions(
        candidates: Sequence[ActionCandidate],
    ) -> Mapping[str, Any]:
        enabled = [candidate for candidate in candidates if not candidate.disabled]
        if not enabled:
            raise ValueError("all action candidates are disabled")
        criteria: Dict[str, str] = {candidate.key: candidate.prompt_text() for candidate in enabled}
        return {
            "next_action": {
                "type": "choice",
                "instructions": (
                    "Choose exactly one key for the safest and most useful next "
                    "browser action. Use only a key from criteria. Prefer "
                    "reversible actions and return your confidence (0 to 1)."
                ),
                "criteria": criteria,
            }
        }

    @staticmethod
    def _candidate_map(
        candidates: Sequence[ActionCandidate],
    ) -> Dict[str, ActionCandidate]:
        result: Dict[str, ActionCandidate] = {}
        for candidate in candidates:
            if not candidate.key:
                raise ValueError("candidate key cannot be empty")
            if candidate.key in result:
                raise ValueError(f"duplicate candidate key: {candidate.key}")
            result[candidate.key] = candidate
        return result

    @staticmethod
    def _validate_fallback(
        decision: ActionDecision,
        candidate_map: Mapping[str, ActionCandidate],
    ) -> ActionDecision:
        if not isinstance(decision, ActionDecision):
            raise TypeError("fallback_decider must return ActionDecision")
        if decision.key not in candidate_map:
            raise ValueError(f"fallback selected unknown action key: {decision.key}")
        if candidate_map[decision.key].disabled:
            raise ValueError(f"fallback selected disabled action key: {decision.key}")
        return decision


def parse_action_decision(
    response: Mapping[str, Any],
    candidate_map: Mapping[str, ActionCandidate],
) -> Optional[ActionDecision]:
    """Parse common Jev answer shapes without trusting unknown action keys."""

    answers = response.get("answers")
    if not isinstance(answers, Mapping):
        answers = {}
    answer = answers.get("next_action", response)

    choice: Any = answer
    if isinstance(answer, Mapping):
        choice = answer.get("choice", answer.get("value", answer.get("key")))
    structured_choice = choice
    if isinstance(choice, Mapping):
        choice = choice.get("key", choice.get("value", choice.get("choice")))

    key = str(choice).strip() if choice is not None else ""
    selected = candidate_map.get(key)
    if selected is None or selected.disabled:
        return None

    confidence = _extract_confidence(response, answer, structured_choice)
    rationale = _extract_text(answer, ("rationale", "reason", "explanation"))
    return ActionDecision(
        key=key,
        confidence=confidence,
        source="jev",
        rationale=rationale,
        raw=dict(response),
    )


def _extract_confidence(
    response: Mapping[str, Any],
    answer: Any,
    original_choice: Any,
) -> Optional[float]:
    candidates = []
    if isinstance(original_choice, Mapping):
        candidates.extend(
            [
                original_choice.get("confidence"),
                original_choice.get("score"),
                original_choice.get("probability"),
            ]
        )
    if isinstance(answer, Mapping):
        candidates.extend(
            [
                answer.get("confidence"),
                answer.get("score"),
                answer.get("probability"),
            ]
        )
    candidates.extend(
        [
            response.get("confidence"),
            response.get("score"),
        ]
    )
    for value in candidates:
        normalized = _normalize_confidence(value)
        if normalized is not None:
            return normalized
    return None


def _normalize_confidence(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if 0.0 <= number <= 1.0:
        return number
    if 1.0 < number <= 100.0:
        return number / 100.0
    return None


def _extract_text(value: Any, keys: Sequence[str]) -> str:
    if not isinstance(value, Mapping):
        return ""
    for key in keys:
        text = value.get(key)
        if text:
            return str(text)
    return ""
