"""Minimal .env loader used by the Jev integration.

The loader deliberately does not override values already present in the
process environment.  That lets CI/deployment environment variables remain
authoritative while local development can use a project-local ``.env``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Mapping, Optional


def read_env_file(path: Path) -> Dict[str, str]:
    """Read a small dotenv-style file without requiring python-dotenv."""

    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key] = value
    return values


def find_env_file() -> Optional[Path]:
    """Find an explicit or conventional local Jev env file."""

    explicit = os.getenv("JEV_ENV_FILE")
    if explicit:
        return Path(explicit).expanduser()
    codex_home = Path(os.getenv("CODEX_HOME", str(Path.home() / ".codex")))
    xdg_config_home = Path(os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    candidates = (
        Path(__file__).resolve().parent.parent / ".env",
        Path.cwd() / ".env",
        codex_home.expanduser() / "jev.env",
        xdg_config_home.expanduser() / "codex-jev-preflight" / "env",
    )
    seen = set()
    for candidate in candidates:
        normalized = candidate.expanduser()
        if normalized in seen:
            continue
        seen.add(normalized)
        if normalized.exists():
            return normalized
    return None


def load_env(
    path: Optional[Path] = None,
    override: bool = False,
) -> Optional[Path]:
    """Load Jev-related values and return the file that was used."""

    env_path = Path(path).expanduser() if path is not None else find_env_file()
    if env_path is None or not env_path.exists():
        return None
    values: Mapping[str, str] = read_env_file(env_path)
    for key, value in values.items():
        if override or key not in os.environ:
            os.environ[key] = value
    return env_path
