import tempfile
import unittest
from pathlib import Path

from configure_jev import write_env
from jev_agent.env_config import read_env_file


class ConfigureTests(unittest.TestCase):
    def test_write_env_uses_private_permissions_and_absolute_state_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env_path = root / "config" / "jev.env"
            state_path = root / "state" / "quota.json"

            written = write_env(
                "test-secret",
                env_path=env_path,
                state_path=state_path,
                endpoint="https://example.test/jev",
                model="test-model",
            )

            self.assertEqual(written, env_path.resolve())
            self.assertEqual(env_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(
                read_env_file(env_path),
                {
                    "TYPESAFE_API_KEY": "test-secret",
                    "TYPESAFE_API_ENDPOINT": "https://example.test/jev",
                    "JEV_MODEL": "test-model",
                    "JEV_STATE_PATH": str(state_path.resolve()),
                },
            )


if __name__ == "__main__":
    unittest.main()
