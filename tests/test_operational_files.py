import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPLOY_WORKFLOW = ROOT / ".github/workflows/docker-build-push.yml"


class DeployScriptOrderTests(unittest.TestCase):
    """Ordering of the deploy script steps (#55, #57, F-021, F-001, F-010, F-056)."""

    def setUp(self):
        self.content = DEPLOY_WORKFLOW.read_text(encoding="utf-8")

    def test_deploy_script_prune_runs_after_up(self):
        up_index = self.content.index("up -d --remove-orphans --wait")
        self.assertGreater(self.content.index("docker builder prune -af"), up_index)
        self.assertGreater(self.content.index("docker image prune -af"), up_index)

    def test_deploy_script_runs_deploy_check_before_up(self):
        check_index = self.content.index("check --deploy --fail-level WARNING")
        self.assertLess(check_index, self.content.index("up -d --remove-orphans --wait"))

    def test_deploy_script_logs_out_of_ghcr_after_pull_before_up(self):
        pull_index = self.content.index("infra/docker-compose.prod.yml pull")
        logout_index = self.content.index("docker logout ghcr.io")
        self.assertLess(pull_index, logout_index)
        self.assertLess(logout_index, self.content.index("up -d --remove-orphans --wait"))

    def test_deploy_script_dumps_db_before_up(self):
        dump_index = self.content.index("pg_dump -Fc")
        self.assertLess(dump_index, self.content.index("up -d --remove-orphans --wait"))


if __name__ == "__main__":
    unittest.main()
