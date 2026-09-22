# Codex Jev Preflight

A fail-open Codex `UserPromptSubmit` hook that asks TypeSafe Jev for advisory
task routing metadata before Codex starts working:

- `task_type`
- `complexity`
- `risk`
- `execution_mode`

The assessment is advisory only. It never overrides system instructions,
developer instructions, or explicit user requirements.

Documentation site: <https://wellkilo.github.io/codex-jev-preflight/>

## Quick start prompt for Codex

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

## Install

```bash
git clone https://github.com/wellkilo/codex-jev-preflight.git
cd codex-jev-preflight

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Configure the API key without exposing it in shell history:

```bash
codex-jev-configure
```

Install the global Codex hook:

```bash
codex-jev-install
```

The installer does not trust the hook automatically. Approve it in Codex when
prompted, or explicitly run `codex-jev-install --trust` if you accept automatic
trust.

## Verify

```bash
python -m unittest discover -s tests -v

HOOK=$(python -c 'import jev_user_prompt_hook; print(jev_user_prompt_hook.__file__)')
printf '%s' '{"prompt":"Review the project and propose a fix","hook_event_name":"UserPromptSubmit"}' |
  python "$HOOK"
```

## Configuration

The default private config file is `$CODEX_HOME/jev.env`, normally
`~/.codex/jev.env`.

```dotenv
TYPESAFE_API_KEY=your-key
TYPESAFE_API_ENDPOINT=https://api.typesafe.ai/v1/systemone
JEV_MODEL=jev-latest
JEV_STATE_PATH=/absolute/path/to/.jev_quota_state.json
```

The hook sends the first 24,000 characters of the current user prompt to the
configured TypeSafe endpoint. See `README.md` and `SECURITY.md` for the full
configuration, privacy, quota, troubleshooting, and uninstall instructions.

## License

MIT. This project is not affiliated with OpenAI, Codex, TypeSafe, or Jev.
