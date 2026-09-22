# Contributing

Thanks for helping improve Codex Jev Preflight.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

The test suite is offline and must not call the live Jev API.

## Pull requests

- Keep the hook fail-open. A Jev error must never block a Codex task.
- Never log or commit API keys, prompts, response bodies, or `.env` files.
- Add tests for parsing, quota handling, installer changes, and fallback paths.
- Update `README.md` and `CHANGELOG.md` when behavior changes.

## Security

Do not open a public issue for a vulnerability. Follow `SECURITY.md`.
