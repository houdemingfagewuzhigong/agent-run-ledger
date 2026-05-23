import json
import unittest

import agent_run_ledger as ledger


class AgentRunLedgerTests(unittest.TestCase):
    def test_risk_flags(self):
        flags = ledger.risk_flags(
            [".github/workflows/deploy.yml", "package-lock.json", ".env"],
            {"files": 22, "insertions": 900, "deletions": 120},
        )

        self.assertIn("workflow changed", flags)
        self.assertIn("dependency lockfile changed", flags)
        self.assertIn("secret-adjacent file changed", flags)
        self.assertIn("large change set", flags)

    def test_sarif_has_warning(self):
        entry = ledger.RunEntry(
            id="run1",
            timestamp="2026-05-23T00:00:00+00:00",
            agent="codex",
            note="test",
            branch="main",
            commit="abc123",
            dirty_files=[".env"],
            diff_stats={"files": 1, "insertions": 1, "deletions": 0},
            risk_flags=["secret-adjacent file changed"],
        )

        data = ledger.sarif([entry])

        self.assertEqual(data["version"], "2.1.0")
        self.assertEqual(data["runs"][0]["results"][0]["level"], "warning")
        json.dumps(data)


if __name__ == "__main__":
    unittest.main()
