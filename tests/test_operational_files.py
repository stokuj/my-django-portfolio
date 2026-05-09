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
        self.assertIn("docker compose --env-file .env -p my_django_portfolio", content)

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

    def test_prod_up_uses_shell_env_guard(self):
        content = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("test -f .env", content)

    def test_prod_status_uses_docker_ps_not_python(self):
        content = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("docker ps", content)

    def test_makefile_uses_original_prod_project_name(self):
        content = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("-p my_django_portfolio", content)

    def test_prod_compose_all_services_have_logging(self):
        content = (ROOT / "infra/docker-compose.prod.yml").read_text(encoding="utf-8")
        self.assertEqual(content.count("    logging:"), 6)

    def test_prod_compose_logging_has_rotation(self):
        content = (ROOT / "infra/docker-compose.prod.yml").read_text(encoding="utf-8")
        self.assertIn('max-size: "10m"', content)
        self.assertIn('max-file: "3"', content)

    def test_deploy_script_has_down_before_up(self):
        content = (ROOT / ".github/workflows/docker-build-push.yml").read_text(encoding="utf-8")
        self.assertIn("down --remove-orphans", content)

    def test_deploy_script_has_builder_prune(self):
        content = (ROOT / ".github/workflows/docker-build-push.yml").read_text(encoding="utf-8")
        self.assertIn("docker builder prune -af", content)

    def test_deploy_script_has_image_prune_all(self):
        content = (ROOT / ".github/workflows/docker-build-push.yml").read_text(encoding="utf-8")
        self.assertIn("docker image prune -af", content)

    def test_deploy_script_prune_runs_after_up(self):
        content = (ROOT / ".github/workflows/docker-build-push.yml").read_text(encoding="utf-8")
        up_index = content.index("up -d --force-recreate")
        prune_index = content.index("docker image prune -af")
        self.assertGreater(prune_index, up_index)


if __name__ == "__main__":
    unittest.main()
