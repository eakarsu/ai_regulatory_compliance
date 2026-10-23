import pathlib
import unittest
from datetime import datetime, timezone

from ai_fallback import obligation_coverage, risk_summary, deadline_outlook
from list_tools import filter_policies, policies_to_csv

ROOT = pathlib.Path(__file__).resolve().parents[1]

POLICY = {"policy_key": "gdpr-policy", "version": 2, "status": "draft", "legal_hold": False}
EVIDENCE = [
    {"owner_id": "u1", "risk_rating": "high", "deadline": "2020-01-01T00:00:00+00:00"},
    {"owner_id": "u2", "risk_rating": "low", "deadline": "2999-01-01T00:00:00+00:00"},
]


class FallbackTests(unittest.TestCase):
    def test_fallbacks_are_labelled_and_preserve_falsy_values(self):
        for result in (
            obligation_coverage(POLICY, EVIDENCE),
            risk_summary(POLICY, EVIDENCE),
            deadline_outlook(POLICY, EVIDENCE, now=datetime(2026, 1, 1, tzinfo=timezone.utc)),
        ):
            self.assertIs(result["aiGenerated"], False)
            self.assertEqual(result["source"], "deterministic-fallback")
            self.assertTrue(result["sections"])
        coverage = obligation_coverage(POLICY, EVIDENCE)
        self.assertIs(coverage["sections"][2]["detail"], False)
        self.assertEqual(risk_summary(POLICY, [])["sections"][1]["detail"], 0)

    def test_policy_search_filter_and_csv(self):
        rows = [
            {"policy_key": "gdpr-policy", "version": 1, "status": "draft", "reviewer_id": "r1", "legal_hold": False},
            {"policy_key": "sox-policy", "version": 3, "status": "approved", "reviewer_id": "r2", "legal_hold": True},
        ]
        self.assertEqual(len(filter_policies(rows, q="gdpr")), 1)
        self.assertEqual(filter_policies(rows, status="approved")[0]["policy_key"], "sox-policy")
        csv_text = policies_to_csv(rows)
        self.assertIn("gdpr-policy,1,draft,r1,False", csv_text)

    def test_tasks_and_insights_are_wired_behind_auth(self):
        main = (ROOT / "main.py").read_text()
        self.assertIn("tasks_router", main)
        governance = (ROOT / "routers" / "governance.py").read_text()
        self.assertIn("filter_policies", governance)
        self.assertIn("policies_to_csv", governance)
        self.assertIn("/insights", governance)
        tasks = (ROOT / "routers" / "tasks.py").read_text()
        self.assertIn("get_current_user", tasks)


if __name__ == "__main__":
    unittest.main()
