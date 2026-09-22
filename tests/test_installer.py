import json
import tempfile
import unittest
from pathlib import Path

from install_jev_global_hook import HOOK_SCRIPT_NAME, START_MARKER, install


class InstallerTests(unittest.TestCase):
    def test_installer_merges_hook_and_instructions_without_duplicates(self):
        project_root = Path(__file__).resolve().parents[1]
        hook_script = project_root / HOOK_SCRIPT_NAME

        with tempfile.TemporaryDirectory() as directory:
            codex_home = Path(directory) / ".codex"
            codex_home.mkdir()
            (codex_home / "hooks.json").write_text(
                json.dumps(
                    {
                        "hooks": {
                            "UserPromptSubmit": [
                                {
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": "echo existing",
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            (codex_home / "AGENTS.md").write_text(
                "# Existing instructions\n",
                encoding="utf-8",
            )

            install(
                codex_home=codex_home,
                hook_script=hook_script,
                python_executable="python3",
                trust_hook=False,
            )
            install(
                codex_home=codex_home,
                hook_script=hook_script,
                python_executable="python3",
                trust_hook=False,
            )

            hooks = json.loads((codex_home / "hooks.json").read_text(encoding="utf-8"))
            groups = hooks["hooks"]["UserPromptSubmit"]
            commands = [handler["command"] for group in groups for handler in group["hooks"]]
            self.assertIn("echo existing", commands)
            self.assertEqual(
                sum(HOOK_SCRIPT_NAME in command for command in commands),
                1,
            )

            instructions = (codex_home / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("# Existing instructions", instructions)
            self.assertEqual(instructions.count(START_MARKER), 1)


if __name__ == "__main__":
    unittest.main()
