import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def test_demo_runs_company_to_human_gate_without_self_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "demo.db"
            result = subprocess.run(
                [sys.executable, "-m", "agent_flow.cli", "--db", str(db), "demo"],
                cwd=Path(__file__).resolve().parents[1],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(output["mission_status"], "active")
            self.assertEqual(output["next_gate"], "human_launch_approval")
            self.assertEqual(output["next_gate_status"], "ready")
            self.assertGreater(output["budget_spent"], 0)
            self.assertTrue(db.exists())
            artifact_dir = Path(output["artifact_directory"])
            self.assertTrue(artifact_dir.is_dir())
            self.assertEqual(len(list(artifact_dir.glob("*.json"))), 12)

    def test_cli_exposes_packets_and_accepts_evidence_proposals(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "workers.db"
            root = Path(__file__).resolve().parents[1]
            create = subprocess.run(
                [
                    sys.executable, "-m", "agent_flow.cli", "--db", str(db),
                    "mission", "create", "--title", "Worker Co", "--brief", "External workers", "--budget", "120",
                ],
                cwd=root, check=False, capture_output=True, text=True,
            )
            self.assertEqual(create.returncode, 0, create.stderr)
            created = json.loads(create.stdout)
            mission_id = created["mission_id"]

            packets = subprocess.run(
                [sys.executable, "-m", "agent_flow.cli", "--db", str(db), "mission", "packets", mission_id],
                cwd=root, check=False, capture_output=True, text=True,
            )
            self.assertEqual(packets.returncode, 0, packets.stderr)
            self.assertEqual(len(json.loads(packets.stdout)), 4)

            completed = subprocess.run(
                [
                    sys.executable, "-m", "agent_flow.cli", "--db", str(db), "mission", "complete",
                    mission_id, "mission_thesis", "--actor", created["assignments"]["mission_thesis"],
                    "--artifact", "artifacts/thesis.md", "--verification", "checked", "--summary", "bounded thesis",
                ],
                cwd=root, check=False, capture_output=True, text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["status"], "done")


if __name__ == "__main__":
    unittest.main()
