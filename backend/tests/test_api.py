import unittest

from fastapi.testclient import TestClient

from app.main import app


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_calculate_returns_graph_and_receipt(self):
        response = self.client.post(
            "/api/v1/calculate",
            json={"query": "EMI for ₹10 lakh at 8.5% for 5 years"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["verification"]["valid"])
        self.assertEqual(payload["calcgraph"]["calculator"], "emi")
        self.assertEqual(len(payload["receipt"]["reproducibility_hash"]), 64)

    def test_incomplete_request_returns_questions(self):
        response = self.client.post("/api/v1/calculate", json={"query": "Calculate my loan EMI"})
        self.assertEqual(response.status_code, 422)
        self.assertGreaterEqual(len(response.json()["detail"]["questions"]), 3)

    def test_compile_verify_execute_lifecycle(self):
        compiled = self.client.post(
            "/api/v1/calcgraph/compile",
            json={"query": "Convert 15 kilometres to miles"},
        )
        graph = compiled.json()["calcgraph"]
        verified = self.client.post("/api/v1/calcgraph/verify", json={"graph": graph})
        executed = self.client.post("/api/v1/calcgraph/execute", json={"graph": graph})
        self.assertEqual(compiled.status_code, 200)
        self.assertTrue(verified.json()["valid"])
        self.assertEqual(executed.json()["calculation"]["answer"], "9.3205678836 miles")

    def test_execute_rejects_unknown_operation(self):
        compiled = self.client.post(
            "/api/v1/calcgraph/compile",
            json={"query": "Calculate 2 + 2"},
        ).json()
        compiled["calcgraph"]["nodes"][-1]["operation"] = "python.exec"
        response = self.client.post("/api/v1/calcgraph/execute", json={"graph": compiled["calcgraph"]})
        self.assertEqual(response.status_code, 422)
        self.assertFalse(response.json()["detail"]["verification"]["valid"])


if __name__ == "__main__":
    unittest.main()
