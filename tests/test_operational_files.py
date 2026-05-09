import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class OperationalFileTests(unittest.TestCase):
    def test_makefile_exists(self):
        self.assertTrue((ROOT / "Makefile").exists())

    def test_dev_compose_exists(self):
        self.assertTrue((ROOT / "infra/docker-compose.dev.yml").exists())

    def test_prod_compose_exists(self):
        self.assertTrue((ROOT / "infra/docker-compose.prod.yml").exists())

    def test_dev_compose_does_not_define_caddy(self):
        content = (ROOT / "infra/docker-compose.dev.yml").read_text(encoding="utf-8")
        self.assertNotIn("\n  caddy:\n", content)

    def test_makefile_declares_required_targets(self):
        content = (ROOT / "Makefile").read_text(encoding="utf-8")
        for target in [
            "dev-up:",
            "dev-status:",
            "dev-down:",
            "prod-up:",
            "prod-status:",
            "prod-down:",
            "verify:",
        ]:
            self.assertIn(target, content)

    def test_makefile_uses_helper_scripts(self):
        content = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("python infra/scripts/ensure_env.py", content)
        self.assertIn("python infra/scripts/compose_status.py", content)

    def test_makefile_passes_root_env_file_to_compose(self):
        content = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("docker compose --env-file .env -p my-django-portfolio-dev", content)
        self.assertIn("docker compose --env-file .env -p my-django-portfolio-prod", content)

    def test_dev_compose_uses_root_context_and_infra_dockerfile(self):
        content = (ROOT / "infra/docker-compose.dev.yml").read_text(encoding="utf-8")
        self.assertIn("context: ..", content)
        self.assertIn("dockerfile: infra/Dockerfile", content)

    def test_prod_compose_uses_root_context_and_infra_dockerfile(self):
        content = (ROOT / "infra/docker-compose.prod.yml").read_text(encoding="utf-8")
        self.assertEqual(content.count("context: .."), 3)
        self.assertEqual(content.count("dockerfile: infra/Dockerfile"), 3)

    def test_prod_compose_uses_root_env_file_for_all_app_services(self):
        content = (ROOT / "infra/docker-compose.prod.yml").read_text(encoding="utf-8")
        self.assertEqual(content.count("- ../.env"), 3)


if __name__ == "__main__":
    unittest.main()
