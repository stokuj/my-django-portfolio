from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.compose_status import build_status_table
from scripts.ensure_env import ensure_env


class EnsureEnvTests(unittest.TestCase):
    def test_dev_mode_copies_example_when_env_missing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / ".env.example"
            env = root / ".env"
            example.write_text("SECRET_KEY=test\n", encoding="utf-8")

            created = ensure_env(
                env_path=env, example_path=example, create_if_missing=True
            )

            self.assertTrue(created)
            self.assertEqual(env.read_text(encoding="utf-8"), "SECRET_KEY=test\n")

    def test_prod_mode_fails_when_env_missing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / ".env.example"
            env = root / ".env"
            example.write_text("SECRET_KEY=test\n", encoding="utf-8")

            with self.assertRaises(FileNotFoundError):
                ensure_env(env_path=env, example_path=example, create_if_missing=False)

    def test_dev_mode_fails_when_example_missing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / ".env.example"
            env = root / ".env"

            with self.assertRaises(FileNotFoundError):
                ensure_env(env_path=env, example_path=example, create_if_missing=True)


class ComposeStatusTests(unittest.TestCase):
    def test_build_status_table_renders_header_and_rows(self):
        rows = [
            {
                "name": "portfolio-web-1",
                "status": "Up 10 seconds",
                "image": "my-django-portfolio:dev",
                "ports": "127.0.0.1:8000->8000/tcp",
            }
        ]

        table = build_status_table(rows)

        self.assertIn("NAME", table)
        self.assertIn("STATUS", table)
        self.assertIn("IMAGE", table)
        self.assertIn("PORTS", table)
        self.assertIn("portfolio-web-1", table)

    def test_build_status_table_handles_empty_rows(self):
        table = build_status_table([])
        self.assertIn("No matching containers found.", table)


if __name__ == "__main__":
    unittest.main()
