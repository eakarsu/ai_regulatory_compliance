import unittest
from governance import validate_source, evaluate_release, transition

class GovernanceTests(unittest.TestCase):
    def test_source_provenance(self):
        source={"source_uri":"https://regulator.example/rule","publisher":"Regulator","jurisdiction":"US","effective_at":"2026-01-01T00:00:00Z","source_version":"v1","content_digest":"abc"}
        self.assertEqual(validate_source(source), source)
        with self.assertRaises(ValueError): validate_source({**source,"source_uri":"http://insecure.test"})
    def test_release_evaluation(self):
        self.assertTrue(evaluate_release([{"source_uri":"https://x","locator":"§1"}],[{"owner_id":"o","deadline":"2026-12-01","risk_rating":"high"}])["passed"])
        self.assertFalse(evaluate_release([],[])["passed"])
    def test_lifecycle_and_segregation(self):
        self.assertEqual(transition("draft","review","analyst","owner","owner"),"review")
        with self.assertRaises(PermissionError): transition("review","approval_pending","admin","owner","wrong",reviewer_id="reviewer")
        self.assertEqual(transition("review","approval_pending","admin","owner","reviewer",reviewer_id="reviewer"),"approval_pending")
        with self.assertRaises(PermissionError): transition("draft","released","admin","o","a")
        with self.assertRaises(ValueError): transition("approval_pending","approved","admin","owner","owner",evaluation_passed=True)
        self.assertEqual(transition("approval_pending","approved","admin","owner","approver",reviewer_id="reviewer",evaluation_passed=True),"approved")
        self.assertEqual(transition("approved","released","admin","owner","approver",reviewer_id="reviewer",approver_id="approver",evaluation_passed=True),"released")

if __name__ == '__main__': unittest.main()
