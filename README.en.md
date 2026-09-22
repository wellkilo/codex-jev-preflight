<div align="center">

# Codex Jev Preflight

**Ask TypeSafe Jev for an advisory pre-task assessment before Codex starts working.**

[![CI](https://github.com/wellkilo/codex-jev-preflight/actions/workflows/ci.yml/badge.svg)](https://github.com/wellkilo/codex-jev-preflight/actions/workflows/ci.yml)
[![Docs](https://github.com/wellkilo/codex-jev-preflight/actions/workflows/pages.yml/badge.svg)](https://wellkilo.github.io/codex-jev-preflight/)
[![Release](https://img.shields.io/github/v/release/wellkilo/codex-jev-preflight?display_name=tag)](https://github.com/wellkilo/codex-jev-preflight/releases)
[![License](https://img.shields.io/github/license/wellkilo/codex-jev-preflight)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)

[Live demo](https://wellkilo.github.io/codex-jev-preflight/) ·
[Quick start](#quick-start) ·
[Architecture](docs/architecture.md) ·
[Security](SECURITY.md) ·
[中文](README.md)

</div>

## What it does

A fail-open Codex `UserPromptSubmit` hook that injects four advisory routing fields:

```text
task_type · complexity · risk · execution_mode
```

The assessment never overrides system, developer, or explicit user instructions.

## Quick start

Paste this prompt into Codex:

```text
Install and configure Codex Jev Preflight from https://github.com/wellkilo/codex-jev-preflight.

Requirements:
1. Read the repository README first.
2. Install the project from source.
3. Run codex-jev-configure and ask me to enter the TypeSafe Jev API key with hidden input. Never ask me to paste the key into chat.
4. Run codex-jev-install and verify the hook output.
5. Preserve existing hooks.json and AGENTS.md configuration.
6. Tell me whether Codex must be restarted or a new task must be opened.
```

Manual install:

```bash
git clone https://github.com/wellkilo/codex-jev-preflight.git
cd codex-jev-preflight

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .

codex-jev-configure
codex-jev-install
```

The installer does not trust the hook automatically. Approve it in Codex, or use `codex-jev-install --trust` if you accept automatic trust.

## Routing fields

| Field | Values |
| --- | --- |
| `task_type` | `answer`, `code_change`, `research`, `browser_automation`, `planning`, `conversation`, `other` |
| `complexity` | `trivial`, `simple`, `moderate`, `complex` |
| `risk` | `low`, `medium`, `high` |
| `execution_mode` | `direct_answer`, `inspect_then_act`, `plan_then_execute`, `ask_clarification` |

## Configuration

The default private config file is `$CODEX_HOME/jev.env`.

```dotenv
TYPESAFE_API_KEY=your-key
TYPESAFE_API_ENDPOINT=https://api.typesafe.ai/v1/systemone
JEV_MODEL=jev-latest
JEV_STATE_PATH=/absolute/path/to/.jev_quota_state.json
```

The hook sends the first 24,000 characters of the current user prompt to the configured TypeSafe endpoint. See [SECURITY.md](SECURITY.md) for the data boundary.

## Verify

```bash
python -m unittest discover -s tests -v

HOOK=$(python -c 'import jev_user_prompt_hook; print(jev_user_prompt_hook.__file__)')
printf '%s' '{"prompt":"Review the project and propose a fix","hook_event_name":"UserPromptSubmit"}' |
  python "$HOOK"
```

## License

MIT. This project is not affiliated with OpenAI, Codex, TypeSafe, or Jev.
