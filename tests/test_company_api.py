import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from agent_flow.agents.api.main import app


class CompanyApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "company-api.db"
        self._old_db = os.environ.get("AGENT_FLOW_DB")
        self._old_secret = os.environ.get("AGENT_FLOW_CAPABILITY_SECRET")
        os.environ["AGENT_FLOW_DB"] = str(self.db_path)
        os.environ["AGENT_FLOW_CAPABILITY_SECRET"] = "test-secret-with-sufficient-entropy"
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.tmp.cleanup()
        if self._old_db is None:
            os.environ.pop("AGENT_FLOW_DB", None)
        else:
            os.environ["AGENT_FLOW_DB"] = self._old_db
        if self._old_secret is None:
            os.environ.pop("AGENT_FLOW_CAPABILITY_SECRET", None)
        else:
            os.environ["AGENT_FLOW_CAPABILITY_SECRET"] = self._old_secret

    def test_create_mission_lists_detail_and_events(self):
        create = self.client.post(
            "/missions",
            json={
                "title": "Arabic AI Gate",
                "brief": "Validate an enterprise evaluation wedge.",
                "budget": 120,
                "risk": "high",
            },
        )
        self.assertEqual(create.status_code, 200, create.text)
        created = create.json()
        mission_id = created["mission_id"]

        listing = self.client.get("/missions")
        self.assertEqual(listing.status_code, 200, listing.text)
        missions = listing.json()["missions"]
        self.assertEqual(len(missions), 1)
        self.assertEqual(missions[0]["id"], mission_id)
        self.assertEqual(missions[0]["status"], "active")

        detail = self.client.get(f"/missions/{mission_id}")
        self.assertEqual(detail.status_code, 200, detail.text)
        mission = detail.json()
        self.assertEqual(mission["id"], mission_id)
        self.assertEqual(mission["title"], "Arabic AI Gate")
        self.assertGreater(len(mission["tasks"]), 5)

        events = self.client.get("/company/events")
        self.assertEqual(events.status_code, 200, events.text)
        event_types = [event["type"] for event in events.json()["events"]]
        self.assertIn("company_bootstrapped", event_types)
        self.assertIn("mission_created", event_types)

    def test_form_squad_assigns_agents_and_exposes_ready_packets(self):
        create = self.client.post(
            "/missions",
            json={
                "title": "Control Room",
                "brief": "Route bounded mission work to the right agents.",
                "budget": 90,
                "risk": "medium",
            },
        )
        mission_id = create.json()["mission_id"]

        formed = self.client.post(f"/missions/{mission_id}/form-squad")
        self.assertEqual(formed.status_code, 200, formed.text)
        assignments = formed.json()["assignments"]
        self.assertIn("mission_thesis", assignments)

        detail = self.client.get(f"/missions/{mission_id}")
        tasks = detail.json()["tasks"]
        assigned = {task["id"]: task["assigned_agent"] for task in tasks if task["assigned_agent"]}
        self.assertIn("mission_thesis", assigned)
        self.assertIsNotNone(assigned["mission_thesis"])

        packets = self.client.get(f"/missions/{mission_id}/packets")
        self.assertEqual(packets.status_code, 200, packets.text)
        packet_list = packets.json()["packets"]
        self.assertGreaterEqual(len(packet_list), 1)
        self.assertTrue(all(packet["task_id"] != "human_launch_approval" for packet in packet_list))
        self.assertTrue(all(packet["worker_id"] for packet in packet_list))

    def test_create_mission_rejects_invalid_payload(self):
        response = self.client.post(
            "/missions",
            json={"title": "", "brief": "", "budget": 0, "risk": "impossible"},
        )
        self.assertEqual(response.status_code, 422, response.text)


if __name__ == "__main__":
    unittest.main()
