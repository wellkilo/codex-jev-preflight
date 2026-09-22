#!/usr/bin/env python3
"""Configure the local Jev integration without exposing the API key in shell history."""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

from jev_agent.env_config import read_env_file

DEFAULT_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"


def default_env_path() -> Path:
    codex_home = Path(os.getenv("CODEX_HOME", str(Path.home() / ".codex")))
    return codex_home.expanduser() / "jev.env"


def write_env(
    api_key: str,
    env_path: Optional[Path] = None,
    state_path: Optional[Path] = None,
    endpoint: str = DEFAULT_ENDPOINT,
    model: str = DEFAULT_MODEL,
) -> Path:
    """Write a private Jev env file and return its resolved path."""

    env_path = (
        Path(env_path).expanduser().resolve()
        if env_path is not None
        else default_env_path().expanduser().resolve()
    )
    state_path = (
        Path(state_path).expanduser().resolve()
        if state_path is not None
        else env_path.parent / ".jev_quota_state.json"
    )
    env_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "# Local Jev configuration. Never commit this file.\n"
        f"TYPESAFE_API_KEY={api_key}\n"
        f"TYPESAFE_API_ENDPOINT={endpoint}\n"
        f"JEV_MODEL={model}\n"
        f"JEV_STATE_PATH={state_path}\n"
    )
    env_path.write_text(content, encoding="utf-8")
    env_path.chmod(0o600)
    return env_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Configure the local TypeSafe Jev connection for Codex.",
    )
    parser.add_argument(
        "--env-file",
        default=str(default_env_path()),
        help="private env file to write (default: $CODEX_HOME/jev.env)",
    )
    parser.add_argument(
        "--state-path",
        default=None,
        help="quota state file (default: .jev_quota_state.json beside the env file)",
    )
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    env_path = Path(args.env_file).expanduser().resolve()
    state_path = (
        Path(args.state_path).expanduser().resolve()
        if args.state_path
        else env_path.parent / ".jev_quota_state.json"
    )
    existing = read_env_file(env_path)
    existing_key = existing.get("TYPESAFE_API_KEY", "")
    prompt = "TYPESAFE_API_KEY (input hidden)"
    if existing_key:
        prompt += ", press Enter to keep the current value"
    prompt += ": "

    try:
        entered = getpass.getpass(prompt)
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled; configuration was not changed.", file=sys.stderr)
        return 1

    api_key = entered.strip() or existing_key
    if not api_key:
        print("No API key was entered; configuration was not changed.", file=sys.stderr)
        return 1

    written = write_env(
        api_key,
        env_path=env_path,
        state_path=state_path,
        endpoint=args.endpoint,
        model=args.model,
    )
    print(f"Configuration written to: {written}")
    print(f"Quota state file: {state_path}")
    print("File mode is 0600; no manual export is required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
