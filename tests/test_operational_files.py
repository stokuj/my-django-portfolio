import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPLOY_WORKFLOW = ROOT / ".github/workflows/docker-build-push.yml"


class DeployScriptOrderTests(unittest.TestCase):
    """Ordering of the deploy script steps (#55, #57, F-021, F-001)."""

    def setUp(self):
        self.content = DEPLOY_WORKFLOW.read_text(encoding="utf-8")

    def test_deploy_script_prune_runs_after_up(self):
        up_index = self.content.index("up -d --remove-orphans --wait")
        self.assertGreater(self.content.index("docker builder prune -af"), up_index)
        self.assertGreater(self.content.index("docker image prune -af"), up_index)

    def test_deploy_script_runs_deploy_check_before_up(self):
        check_index = self.content.index("check --deploy --fail-level WARNING")
        self.assertLess(check_index, self.content.index("up -d --remove-orphans --wait"))


if __name__ == "__main__":
    unittest.main()
