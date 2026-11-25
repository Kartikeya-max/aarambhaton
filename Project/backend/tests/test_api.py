"""HTTP-level tests. Skipped automatically when fastapi/httpx are not installed."""
import unittest
from pathlib import Path

try:
    from fastapi.testclient import TestClient
    from app.main import app
    HAVE_API = True
except ImportError:  # pragma: no cover
    HAVE_API = False

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


@unittest.skipUnless(HAVE_API, "fastapi/httpx not installed")
class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_and_plans(self):
        self.assertEqual(self.client.get("/health").json()["status"], "ok")
        self.assertEqual(len(self.client.get("/api/plans").json()), 3)

    def test_review_matches_frontend_contract(self):
        files = {
            "bill": ("planted_cghs_rate.csv", (SAMPLES / "planted_cghs_rate.csv").read_bytes(), "text/csv"),
            "visit_summary": ("visit_summary.txt", (SAMPLES / "visit_summary.txt").read_bytes(), "text/plain"),
        }
        r = self.client.post("/api/review", data={"plan_id": "demo-basic"}, files=files)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(set(body["summary"]), {"totalBilled", "potentialSavings", "issuesFound"})
        self.assertEqual(body["summary"]["issuesFound"], 1)
        self.assertIn("appliedCode", body["items"][0])

    def test_bad_file_is_422(self):
        files = {"bill": ("bill.jpg", b"x", "image/jpeg")}
        r = self.client.post("/api/review", data={"plan_id": "demo-basic"}, files=files)
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main()
