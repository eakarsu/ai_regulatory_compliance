import hashlib
import os
import time
import unittest

os.environ.setdefault("JWT_SECRET", "integration-test-secret-that-is-at-least-32-characters")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("AUTH_MODE", "local")
os.environ.setdefault("ENABLE_LEGACY_ROUTES", "false")


@unittest.skipUnless(os.getenv("RUN_DB_TESTS") == "true", "set RUN_DB_TESTS=true for PostgreSQL API tests")
class GovernanceApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from main import app
        cls.client = TestClient(app)

    def api(self, method, path, token=None, **kwargs):
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return self.client.request(method, path, headers=headers, **kwargs)

    def test_complete_governed_release_and_tenant_isolation(self):
        suffix = str(time.time_ns())
        password = "ValidPassphrase!123"
        owner_response = self.api("POST", "/api/auth/register", json={"email": f"owner-{suffix}@example.com", "password": password, "name": "Policy Owner", "organization": "Alpha Compliance"})
        self.assertEqual(owner_response.status_code, 201, owner_response.text)
        owner_token, owner = owner_response.json()["access_token"], owner_response.json()["user"]
        self.assertEqual(owner["role"], "admin")

        reviewer_email, approver_email = f"reviewer-{suffix}@example.com", f"approver-{suffix}@example.com"
        reviewer = self.api("POST", "/api/auth/users", owner_token, json={"email": reviewer_email, "password": password, "name": "Reviewer", "role": "admin"})
        approver = self.api("POST", "/api/auth/users", owner_token, json={"email": approver_email, "password": password, "name": "Approver", "role": "admin"})
        self.assertEqual(reviewer.status_code, 201, reviewer.text); self.assertEqual(approver.status_code, 201, approver.text)
        reviewer_user, approver_user = reviewer.json(), approver.json()
        reviewer_token = self.api("POST", "/api/auth/login", json={"email": reviewer_email, "password": password}).json()["access_token"]
        approver_token = self.api("POST", "/api/auth/login", json={"email": approver_email, "password": password}).json()["access_token"]

        source = self.api("POST", "/api/governance/sources", owner_token, json={
            "source_uri": "https://regulator.example/rules/42", "publisher": "Example Regulator", "jurisdiction": "US",
            "effective_at": "2027-01-01T00:00:00Z", "source_version": "2027.1", "content_digest": hashlib.sha256(b"rule-v1").hexdigest(),
            "provenance": {"retrieval": "signed-feed", "license": "test"},
        })
        self.assertEqual(source.status_code, 201, source.text)
        changed_source = self.api("POST", "/api/governance/sources", owner_token, json={
            "source_uri": "https://regulator.example/rules/42", "publisher": "Example Regulator", "jurisdiction": "US",
            "effective_at": "2027-06-01T00:00:00Z", "source_version": "2027.2", "content_digest": hashlib.sha256(b"rule-v2").hexdigest(),
            "provenance": {"retrieval": "signed-feed", "license": "test"},
        })
        self.assertEqual(changed_source.status_code, 201, changed_source.text); self.assertTrue(changed_source.json()["changed"]); self.assertEqual(changed_source.json()["previous_version"], "2027.1")
        from database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        with self.assertRaises(Exception):
            db.execute(text("UPDATE regulatory_source_versions SET publisher='tampered' WHERE id=CAST(:id AS UUID)"), {"id": source.json()["id"]}); db.commit()
        db.rollback(); db.close()
        policy = self.api("POST", "/api/governance/policies", owner_token, json={"policy_key": "access-control", "body_digest": hashlib.sha256(b"policy-v1").hexdigest(), "reviewer_id": reviewer_user["id"], "retain_until": "2035-01-01T00:00:00Z"})
        self.assertEqual(policy.status_code, 201, policy.text); policy_id = policy.json()["id"]
        evidence = self.api("POST", f"/api/governance/policies/{policy_id}/evidence", owner_token, json={"source_version_id": source.json()["id"], "locator": "§42(a)", "obligation": "Review privileged access quarterly", "owner_id": reviewer_user["id"], "deadline": "2030-01-01T00:00:00Z", "risk_rating": "high"})
        self.assertEqual(evidence.status_code, 201, evidence.text)
        evaluation = self.api("POST", f"/api/governance/policies/{policy_id}/evaluations", reviewer_token, json={"scenario": "Privileged access evidence is current and every obligation has an accountable owner."})
        self.assertEqual(evaluation.status_code, 201, evaluation.text); self.assertTrue(evaluation.json()["passed"])
        transitions = [(owner_token, "review"), (reviewer_token, "approval_pending")]
        for token, target in transitions:
            response = self.api("POST", f"/api/governance/policies/{policy_id}/transitions", token, json={"target": target, "rationale": f"Validated transition to {target}"})
            self.assertEqual(response.status_code, 200, response.text)
        sod_failure = self.api("POST", f"/api/governance/policies/{policy_id}/transitions", owner_token, json={"target": "approved", "rationale": "Owner must not self approve"})
        self.assertEqual(sod_failure.status_code, 409, sod_failure.text)
        for target in ["approved", "released"]:
            response = self.api("POST", f"/api/governance/policies/{policy_id}/transitions", approver_token, json={"target": target, "rationale": f"Independent decision to {target}"})
            self.assertEqual(response.status_code, 200, response.text)
        hold = self.api("PATCH", f"/api/governance/policies/{policy_id}/retention", approver_token, json={"legal_hold": True, "retain_until": "2036-01-01T00:00:00Z"})
        self.assertEqual(hold.status_code, 200, hold.text); self.assertTrue(hold.json()["legal_hold"])
        shortened = self.api("PATCH", f"/api/governance/policies/{policy_id}/retention", approver_token, json={"retain_until": "2030-01-01T00:00:00Z"})
        self.assertEqual(shortened.status_code, 409, shortened.text)
        export = self.api("GET", "/api/governance/audit-export", approver_token)
        self.assertEqual(export.status_code, 200, export.text); self.assertEqual(len(export.json()["records"]), 4); self.assertEqual(len(export.json()["sha256"]), 64)

        outsider = self.api("POST", "/api/auth/register", json={"email": f"other-{suffix}@example.com", "password": password, "name": "Other Owner", "organization": "Beta Compliance"})
        outsider_token = outsider.json()["access_token"]
        self.assertEqual(self.api("GET", f"/api/governance/policies/{policy_id}", outsider_token).status_code, 404)
        self.assertEqual(self.api("GET", "/api/governance/sources", outsider_token).json(), [])
        self.assertEqual(self.api("GET", "/api/ai/logs", owner_token).status_code, 404)


if __name__ == "__main__":
    unittest.main()
