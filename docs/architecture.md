# Architecture

```text
User prompt
    |
    v
Codex UserPromptSubmit hook
    |
    +-- load local Jev configuration
    +-- call TypeSafe Jev when quota is available
    +-- validate four routing choices
    +-- inject advisory assessment into Codex context
    |
    v
Codex continues with normal system and developer instructions
```

## Routing contract

Jev receives four independent choice questions:

| Field | Values |
| --- | --- |
| `task_type` | `answer`, `code_change`, `research`, `browser_automation`, `planning`, `conversation`, `other` |
| `complexity` | `trivial`, `simple`, `moderate`, `complex` |
| `risk` | `low`, `medium`, `high` |
| `execution_mode` | `direct_answer`, `inspect_then_act`, `plan_then_execute`, `ask_clarification` |

The result is advisory. It cannot override system instructions, developer
instructions, or explicit user requirements.

## Failure behavior

The hook is fail-open:

1. If the persistent quota breaker is open, it emits a skipped assessment and
   returns success.
2. If Jev times out or returns a transport/API error, it emits a skipped
   assessment and returns success.
3. If the response cannot be parsed, unknown values become `unknown`.
4. Codex always continues with the original prompt.

The quota circuit breaker is persisted so separate Codex tasks do not repeatedly
consume a known-exhausted account. Temporary rate limits use a bounded cooldown.
