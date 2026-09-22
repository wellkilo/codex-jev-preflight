import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jev_agent.env_config import find_env_file, load_env, read_env_file


class EnvConfigTests(unittest.TestCase):
    def test_reads_quotes_export_and_comments(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(
                "\n".join(
                    [
                        "# comment",
                        "export FIRST=one",
                        'SECOND="two words"',
                        "EMPTY=",
                    ]
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                read_env_file(path),
                {"FIRST": "one", "SECOND": "two words", "EMPTY": ""},
            )

    def test_finds_codex_home_jev_env(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = Path(directory) / ".codex"
            codex_home.mkdir()
            env_path = codex_home / "jev.env"
            env_path.write_text("TYPESAFE_API_KEY=test\n", encoding="utf-8")

            with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}, clear=False):
                self.assertEqual(find_env_file(), env_path)

    def test_existing_environment_wins_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("JEV_TEST_VALUE=from-file\n", encoding="utf-8")
            os.environ["JEV_TEST_VALUE"] = "from-process"
            try:
                load_env(path)
                self.assertEqual(os.environ["JEV_TEST_VALUE"], "from-process")
                load_env(path, override=True)
                self.assertEqual(os.environ["JEV_TEST_VALUE"], "from-file")
            finally:
                os.environ.pop("JEV_TEST_VALUE", None)


if __name__ == "__main__":
    unittest.main()
