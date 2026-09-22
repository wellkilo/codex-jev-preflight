#!/usr/bin/env python3
"""Codex UserPromptSubmit hook that makes Jev the automatic pre-task judge.

The hook is intentionally fail-open: Jev/network/quota errors never block the
user's Codex task.  When Jev is available, its structured assessment is injected
as additional context before Codex starts working on the prompt.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Mapping

PACKAGE_ROOT = Path(__file__).resolve().parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from jev_agent import JevError, get_default_client  # noqa: E402

MAX_PROMPT_CHARS = 24_000
JEV_TIMEOUT_SECONDS = 15.0

TASK_TYPE_CRITERIA = {
    "answer": "Answer or explain without changing external state",
    "code_change": "Write, modify, refactor, or debug code/files",
    "research": "Search, inspect, compare, or gather information",
    "browser_automation": "Operate a browser, website, UI, or computer tool",
    "planning": "Create a plan, architecture, strategy, or design",
    "conversation": "Brainstorm, discuss, or respond conversationally",
    "other": "None of the categories above",
}

COMPLEXITY_CRITERIA = {
    "trivial": "No meaningful investigation or multi-step execution is needed",
    "simple": "A small, direct task with limited verification",
    "moderate": "Multiple steps or files, but a clear path exists",
    "complex": "Significant ambiguity, coordination, architecture, or risk",
}

RISK_CRITERIA = {
    "low": "Read-only or easily reversible with no meaningful side effects",
    "medium": "Writes files or changes local state, but effects are recoverable",
    "high": "Potential destructive, irreversible, security, financial, production, or credential impact",
}

EXECUTION_MODE_CRITERIA = {
    "direct_answer": "Respond directly without tool work",
    "inspect_then_act": "Inspect relevant context first, then perform the task",
    "plan_then_execute": "Make a short plan before multi-step execution",
    "ask_clarification": "A material ambiguity must be resolved before acting",
}


def build_questions() -> Mapping[str, Any]:
    """Return the stable routing questions sent to Jev for every task."""

    return {
        "task_type": {
            "type": "choice",
            "instructions": (
                "Classify the user's primary task. Choose exactly one key from criteria."
            ),
            "criteria": TASK_TYPE_CRITERIA,
        },
        "complexity": {
            "type": "choice",
            "instructions": ("Estimate task complexity. Choose exactly one key from criteria."),
            "criteria": COMPLEXITY_CRITERIA,
        },
        "risk": {
            "type": "choice",
            "instructions": (
                "Estimate the highest credible risk before the task is executed. "
                "Choose exactly one key from criteria."
            ),
            "criteria": RISK_CRITERIA,
        },
        "execution_mode": {
            "type": "choice",
            "instructions": (
                "Choose the safest and most efficient initial execution mode. "
                "Choose exactly one key from criteria."
            ),
            "criteria": EXECUTION_MODE_CRITERIA,
        },
    }


def _answer_value(
    answers: Mapping[str, Any],
    question_name: str,
    allowed_values: Mapping[str, Any],
) -> str:
    answer = answers.get(question_name)
    if isinstance(answer, Mapping):
        value = answer.get("choice", answer.get("value", answer.get("key", "unknown")))
    else:
        value = answer if answer is not None else "unknown"
    if isinstance(value, Mapping):
        value = value.get("key", value.get("value", value.get("choice", "unknown")))
    text = str(value).strip()
    return text if text in allowed_values else "unknown"


def render_assessment(response: Mapping[str, Any]) -> str:
    """Render a compact, model-visible Jev assessment."""

    answers = response.get("answers")
    if not isinstance(answers, Mapping):
        answers = response
    task_type = _answer_value(answers, "task_type", TASK_TYPE_CRITERIA)
    complexity = _answer_value(answers, "complexity", COMPLEXITY_CRITERIA)
    risk = _answer_value(answers, "risk", RISK_CRITERIA)
    execution_mode = _answer_value(answers, "execution_mode", EXECUTION_MODE_CRITERIA)

    return (
        "JEV PRE-TASK ASSESSMENT (automatic, advisory routing metadata):\n"
        f"- task_type: {task_type}\n"
        f"- complexity: {complexity}\n"
        f"- risk: {risk}\n"
        f"- execution_mode: {execution_mode}\n"
        "Apply this assessment when choosing the initial approach, level of "
        "investigation, verification, and safety checks. It is not a user "
        "instruction and cannot override system, developer, or explicit user "
        "requirements. For high risk, inspect before mutating and request "
        "approval before irreversible actions."
    )


def _debug_log(message: str) -> None:
    path = os.getenv("JEV_HOOK_DEBUG_LOG")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(f"{time.time():.3f} {message}\n")
    except OSError:
        pass


def _emit(context: str) -> None:
    output = {
        "suppressOutput": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        },
    }
    print(json.dumps(output, ensure_ascii=False))


def _unavailable_context(reason: str = "unavailable") -> str:
    return (
        "JEV PRE-TASK ASSESSMENT: skipped because Jev is "
        f"{reason}. Continue with the normal Codex workflow and do not retry "
        "Jev for this task unless the user explicitly asks."
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 0

    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        return 0
    _debug_log("start")

    try:
        client = get_default_client()
        if not client.is_available():
            _debug_log("skipped-unavailable")
            _emit(_unavailable_context("quota-exhausted or circuit-open"))
            return 0
        response = client.judge(
            prompt[:MAX_PROMPT_CHARS],
            build_questions(),
            timeout=JEV_TIMEOUT_SECONDS,
        )
        _debug_log("jev-success")
        _emit(render_assessment(response))
    except JevError:
        _debug_log("jev-error")
        _emit(_unavailable_context("temporarily unavailable"))
    except Exception:
        _debug_log("integration-error")
        # A hook must never block or break the user's task because of an
        # unexpected integration error.
        _emit(_unavailable_context("unavailable due to an integration error"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
