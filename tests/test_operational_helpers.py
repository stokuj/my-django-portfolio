import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

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

    def test_dev_mode_noop_when_env_exists(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / ".env.example"
            env = root / ".env"
            example.write_text("SECRET_KEY=dummy\n", encoding="utf-8")
            env.write_text("SECRET_KEY=existing\n", encoding="utf-8")

            created = ensure_env(
                env_path=env, example_path=example, create_if_missing=True
            )

            self.assertFalse(created)
            self.assertEqual(env.read_text(encoding="utf-8"), "SECRET_KEY=existing\n")

    def test_prod_mode_fails_when_env_missing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / ".env.example"
            env = root / ".env"
            example.write_text("SECRET_KEY=test\n", encoding="utf-8")

            with self.assertRaisesRegex(FileNotFoundError, "Missing env file"):
                ensure_env(env_path=env, example_path=example, create_if_missing=False)

    def test_dev_mode_fails_when_example_missing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / ".env.example"
            env = root / ".env"

            with self.assertRaisesRegex(FileNotFoundError, "Missing example env file"):
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

        expected = (
            "NAME             STATUS         IMAGE                    PORTS                   \n"
            "portfolio-web-1  Up 10 seconds  my-django-portfolio:dev  127.0.0.1:8000->8000/tcp"
        )
        self.assertEqual(table, expected)

    def test_build_status_table_multiple_rows(self):
        rows = [
            {
                "name": "web",
                "status": "Up",
                "image": "img:dev",
                "ports": "8000/tcp",
            },
            {
                "name": "db-server",
                "status": "Up 2 hours",
                "image": "postgres:15",
                "ports": "5432/tcp",
            },
        ]

        table = build_status_table(rows)

        expected = (
            "NAME       STATUS      IMAGE        PORTS   \n"
            "web        Up          img:dev      8000/tcp\n"
            "db-server  Up 2 hours  postgres:15  5432/tcp"
        )
        self.assertEqual(table, expected)

    def test_build_status_table_handles_empty_rows(self):
        table = build_status_table([])
        self.assertIn("No matching containers found.", table)


if __name__ == "__main__":
    unittest.main()
