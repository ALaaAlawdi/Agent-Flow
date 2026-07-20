import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from agent_flow import cli


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
            env = {**os.environ, "AGENT_FLOW_CAPABILITY_SECRET": "test-secret-with-sufficient-entropy"}
            create = subprocess.run(
                [
                    sys.executable, "-m", "agent_flow.cli", "--db", str(db),
                    "mission", "create", "--title", "Worker Co", "--brief", "External workers", "--budget", "120",
                ],
                cwd=root, check=False, capture_output=True, text=True, env=env,
            )
            self.assertEqual(create.returncode, 0, create.stderr)
            created = json.loads(create.stdout)
            mission_id = created["mission_id"]

            packets = subprocess.run(
                [sys.executable, "-m", "agent_flow.cli", "--db", str(db), "mission", "packets", mission_id],
                cwd=root, check=False, capture_output=True, text=True, env=env,
            )
            self.assertEqual(packets.returncode, 0, packets.stderr)
            packet_list = json.loads(packets.stdout)
            self.assertEqual(len(packet_list), 4)
            token = next(
                packet["capability_token"] for packet in packet_list
                if packet["task_id"] == "mission_thesis"
            )

            completed = subprocess.run(
                [
                    sys.executable, "-m", "agent_flow.cli", "--db", str(db), "mission", "complete",
                    mission_id, "mission_thesis",
                    "--artifact", "artifacts/thesis.md", "--verification", "checked", "--summary", "bounded thesis",
                ],
                cwd=root, check=False, capture_output=True, text=True, env=env, input=token,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["status"], "done")

    def test_cli_worker_commands_require_capability_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ)
            env.pop("AGENT_FLOW_CAPABILITY_SECRET", None)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_flow.cli",
                    "--db",
                    str(Path(tmp) / "workers.db"),
                    "mission",
                    "packets",
                    "mission-id",
                ],
                cwd=Path(__file__).resolve().parents[1],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("AGENT_FLOW_CAPABILITY_SECRET", result.stderr)

    def test_cli_bounds_capability_stdin_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            bounded_stdin = Mock()
            bounded_stdin.read.return_value = "a" * 4097
            argv = [
                "--db", str(Path(tmp) / "workers.db"), "mission", "complete", "mission", "task",
                "--artifact", "artifact", "--verification", "checked", "--summary", "bounded",
            ]
            with (
                patch.object(cli.sys, "stdin", bounded_stdin),
                patch.dict(os.environ, {"AGENT_FLOW_CAPABILITY_SECRET": "test-secret-with-sufficient-entropy"}),
                self.assertRaises(SystemExit),
            ):
                cli.main(argv)

            bounded_stdin.read.assert_called_once_with(4097)


if __name__ == "__main__":
    unittest.main()
