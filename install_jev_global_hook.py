#!/usr/bin/env python3
"""Install the Jev-first UserPromptSubmit hook globally for Codex."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

START_MARKER = "<!-- JEV-FIRST-START -->"
END_MARKER = "<!-- JEV-FIRST-END -->"
HOOK_SCRIPT_NAME = "jev_user_prompt_hook.py"

GLOBAL_INSTRUCTIONS = """\
<!-- JEV-FIRST-START -->
## Jev-first automatic preflight

- A global `UserPromptSubmit` hook automatically asks Jev to assess each user task before work begins when Jev quota is available.
- When `JEV PRE-TASK ASSESSMENT` is present, treat it as advisory routing, complexity, risk, and execution-mode metadata. Use it to choose the initial approach and safety controls.
- Do not let a Jev assessment override system, developer, or explicit user instructions.
- Do not call Jev again for the same prompt unless a new structured decision is genuinely required.
- If the assessment says Jev was skipped because quota is exhausted or the service is unavailable, continue with the normal Codex workflow and do not retry Jev during that task.
<!-- JEV-FIRST-END -->
"""


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def atomic_write(path: Path, content: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.chmod(temp_name, mode)
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def merge_global_instructions(existing: str) -> str:
    start = existing.find(START_MARKER)
    end = existing.find(END_MARKER)
    if start != -1 and end != -1 and end > start:
        end += len(END_MARKER)
        return existing[:start].rstrip() + "\n\n" + GLOBAL_INSTRUCTIONS + existing[end:].lstrip()
    if existing.strip():
        return existing.rstrip() + "\n\n" + GLOBAL_INSTRUCTIONS
    return GLOBAL_INSTRUCTIONS


def _read_app_server_response(process: subprocess.Popen, request_id: int) -> Dict[str, Any]:
    while True:
        line = process.stdout.readline()
        if not line:
            stderr = process.stderr.read() if process.stderr else ""
            raise RuntimeError(f"Codex app-server closed: {stderr}")
        message = json.loads(line)
        if message.get("id") == request_id and ("result" in message or "error" in message):
            if "error" in message:
                raise RuntimeError(f"Codex app-server error: {message['error']}")
            return message["result"]


def trust_hook_via_app_server(
    codex_command: str,
    hooks_path: Path,
    hook_script: Path,
) -> bool:
    """Use Codex's own app-server API to mark the installed hook trusted."""

    process = subprocess.Popen(
        [codex_command, "app-server", "--stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:

        def send(payload: Dict[str, Any]) -> None:
            if process.stdin is None:
                raise RuntimeError("Codex app-server stdin is unavailable")
            process.stdin.write(json.dumps(payload) + "\n")
            process.stdin.flush()

        send(
            {
                "id": 1,
                "method": "initialize",
                "params": {
                    "clientInfo": {
                        "name": "jev-hook-installer",
                        "version": "1.0",
                    }
                },
            }
        )
        _read_app_server_response(process, 1)

        send(
            {
                "id": 2,
                "method": "hooks/list",
                "params": {"cwds": [str(hook_script.parent)]},
            }
        )
        result = _read_app_server_response(process, 2)
        entries = result.get("data", [])
        target = None
        for entry in entries:
            for hook in entry.get("hooks", []):
                if hook.get("sourcePath") == str(hooks_path) and HOOK_SCRIPT_NAME in str(
                    hook.get("command", "")
                ):
                    target = hook
                    break
            if target is not None:
                break
        if target is None:
            raise RuntimeError("installed Jev hook was not found by app-server")

        key_path = f"hooks.state.{json.dumps(target['key'])}"
        writes = (
            ("trusted_hash", target["currentHash"]),
            ("enabled", True),
        )
        for request_id, (suffix, value) in enumerate(writes, start=10):
            send(
                {
                    "id": request_id,
                    "method": "config/value/write",
                    "params": {
                        "keyPath": f"{key_path}.{suffix}",
                        "value": value,
                        "mergeStrategy": "upsert",
                        "reloadUserConfig": True,
                    },
                }
            )
            _read_app_server_response(process, request_id)
        return True
    finally:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()


def install(
    codex_home: Path,
    hook_script: Path,
    python_executable: str,
    codex_command: str = "codex",
    trust_hook: bool = False,
) -> None:
    codex_home = codex_home.expanduser().resolve()
    hook_script = hook_script.expanduser().resolve()
    if not hook_script.is_file():
        raise FileNotFoundError(f"hook script not found: {hook_script}")

    hooks_path = codex_home / "hooks.json"
    instructions_path = codex_home / "AGENTS.md"
    config = read_json(hooks_path)
    hooks = config.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"{hooks_path}: hooks must be an object")
    groups = hooks.setdefault("UserPromptSubmit", [])
    if not isinstance(groups, list):
        raise ValueError(f"{hooks_path}: hooks.UserPromptSubmit must be an array")

    cleaned_groups: List[Any] = []
    for group in groups:
        if not isinstance(group, dict):
            cleaned_groups.append(group)
            continue
        handlers = group.get("hooks")
        if not isinstance(handlers, list):
            cleaned_groups.append(group)
            continue
        kept = [
            handler
            for handler in handlers
            if not (
                isinstance(handler, dict) and HOOK_SCRIPT_NAME in str(handler.get("command", ""))
            )
        ]
        if kept:
            updated_group = dict(group)
            updated_group["hooks"] = kept
            cleaned_groups.append(updated_group)

    if os.name == "nt":
        command = subprocess.list2cmdline([python_executable, str(hook_script)])
    else:
        command = f"{shlex.quote(python_executable)} {shlex.quote(str(hook_script))}"
    cleaned_groups.append(
        {
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                    "timeout": 25,
                    "statusMessage": "Jev is assessing the task",
                    "additionalContextLimit": 0,
                }
            ]
        }
    )
    hooks["UserPromptSubmit"] = cleaned_groups
    config.setdefault(
        "description",
        "Global Codex hooks configured by the Jev integration.",
    )

    if hooks_path.exists():
        shutil.copy2(hooks_path, hooks_path.with_suffix(hooks_path.suffix + ".bak"))
    atomic_write(
        hooks_path,
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
    )

    existing_instructions = (
        instructions_path.read_text(encoding="utf-8") if instructions_path.exists() else ""
    )
    if instructions_path.exists():
        shutil.copy2(
            instructions_path,
            instructions_path.with_suffix(instructions_path.suffix + ".bak"),
        )
    atomic_write(
        instructions_path,
        merge_global_instructions(existing_instructions).rstrip() + "\n",
    )

    print(f"Installed Jev UserPromptSubmit hook: {hooks_path}")
    print(f"Updated global instructions: {instructions_path}")
    print(f"Hook script: {hook_script}")

    trusted = False
    if trust_hook:
        try:
            trusted = trust_hook_via_app_server(
                codex_command,
                hooks_path,
                hook_script,
            )
        except Exception as exc:
            print(f"Automatic hook trust failed: {exc}")
    if trusted:
        print("Hook trust: trusted (no manual approval needed)")
    else:
        print("Hook trust: not confirmed; approve the hook once in Codex if asked.")
    print("Restart Codex or open a new task so the global hook is loaded.")


def main() -> int:
    default_script = Path(__file__).resolve().parent / HOOK_SCRIPT_NAME
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--codex-home",
        default=os.getenv("CODEX_HOME", str(Path.home() / ".codex")),
    )
    parser.add_argument("--hook-script", default=str(default_script))
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--codex", default="codex")
    parser.add_argument(
        "--trust",
        action="store_true",
        help="explicitly mark the installed hook trusted through Codex app-server",
    )
    args = parser.parse_args()
    install(
        codex_home=Path(args.codex_home),
        hook_script=Path(args.hook_script),
        python_executable=args.python,
        codex_command=args.codex,
        trust_hook=args.trust,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
