import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from agent_flow.cli import main as cli_main
from agent_flow.hermes import HermesExecutionError, HermesWorkerAdapter
from agent_flow.runtime import CompanyRuntime


class HermesWorkerAdapterTests(unittest.TestCase):
    def _write_fake_hermes(self, path: Path, script: str) -> Path:
        """Write a cross-platform fake hermes executable. Returns the path to invoke.

        On Windows, returns a .py file; hermes.py detects this and prepends sys.executable
        so CreateProcess handles argument quoting natively (no cmd.exe shell issues).
        On Unix, writes a shebang script and sets the executable bit.
        """
        body = script[script.index("\n") + 1:] if script.startswith("#!/") else script
        if sys.platform == "win32":
            py_path = path.parent / (path.name + ".py")
            py_path.write_text(body, encoding="utf-8")
            return py_path
        path.write_text(script, encoding="utf-8")
        path.chmod(0o700)
        return path

    def test_runs_bounded_packet_through_hermes_without_exposing_capability(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture = root / "argv.json"
            executable = self._write_fake_hermes(
                root / "fake-hermes",
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "capture = {'argv': sys.argv[1:], "
                "'capability_secret': os.environ.get('AGENT_FLOW_CAPABILITY_SECRET')}\n"
                "open(os.environ['FAKE_HERMES_CAPTURE'], 'w').write(json.dumps(capture))\n"
                "print(json.dumps({'artifact': 'thesis.md', 'verification': 'checked', "
                "'summary': 'bounded result'}))\n",
            )
            packet = {
                "mission_id": "mission-1",
                "task_id": "mission_thesis",
                "worker_id": "founder",
                "objective": "Define the company thesis",
                "mission_context": {
                    "title": "Hermes company",
                    "brief": "Create an evidence-backed thesis.",
                    "risk": "medium",
                },
                "budget": {"credits": 8},
                "input_artifacts": [],
                "allowed_tools": [],
                "acceptance_criteria": ["Return a retrievable artifact handle"],
                "evidence_contract": ["artifact", "verification", "summary"],
                "decision_options": [],
                "authority": {
                    "may_mutate_company_state": False,
                    "may_approve_own_work": False,
                    "may_trigger_external_side_effects": False,
                },
                "capability_token": "must-never-reach-hermes",
                "untrusted_extra_secret": "must-also-never-reach-hermes",
            }
            adapter = HermesWorkerAdapter(
                executable=str(executable),
                profile="agent-flow-founder",
                toolsets=("web",),
                workdir=root,
                timeout_seconds=5,
                env={
                    **os.environ,
                    "FAKE_HERMES_CAPTURE": str(capture),
                    "AGENT_FLOW_CAPABILITY_SECRET": "gateway-secret-must-not-be-inherited",
                },
            )

            evidence = adapter.run_task(packet)

            self.assertEqual(
                evidence,
                {
                    "artifact": "thesis.md",
                    "verification": "checked",
                    "summary": "bounded result",
                },
            )
            capture_data = json.loads(capture.read_text(encoding="utf-8"))
            argv = capture_data["argv"]
            self.assertIsNone(capture_data["capability_secret"])
            self.assertEqual(argv[:2], ["-p", "agent-flow-founder"])
            self.assertIn("-z", argv)
            self.assertEqual(argv[argv.index("-t") + 1], "web")
            prompt = argv[argv.index("-z") + 1]
            self.assertNotIn("capability_token", prompt)
            self.assertNotIn("must-never-reach-hermes", prompt)
            self.assertNotIn("must-also-never-reach-hermes", prompt)
            self.assertIn('"task_id":"mission_thesis"', prompt)
            self.assertIn('"objective":"Define the company thesis"', prompt)
            self.assertIn('"may_mutate_company_state":false', prompt)
            self.assertIn('"enabled_toolsets":["web"]', prompt)
            self.assertNotIn('"allowed_tools":[]', prompt)

    def test_rejects_non_json_hermes_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = self._write_fake_hermes(
                root / "fake-hermes",
                "#!/usr/bin/env python3\nprint('```json')\nprint('{}')\nprint('```')\n",
            )
            adapter = HermesWorkerAdapter(
                executable=str(executable),
                profile="agent-flow-founder",
                workdir=root,
                timeout_seconds=5,
            )

            with self.assertRaisesRegex(HermesExecutionError, "valid JSON"):
                adapter.run_task({"mission_id": "mission-1", "task_id": "task-1"})

    def test_bounds_stdout_before_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = self._write_fake_hermes(
                root / "fake-hermes",
                "#!/usr/bin/env python3\nprint('x' * 20000)\n",
            )
            adapter = HermesWorkerAdapter(
                executable=str(executable),
                profile="agent-flow-founder",
                workdir=root,
                timeout_seconds=5,
            )

            with self.assertRaisesRegex(HermesExecutionError, "size limit"):
                adapter.run_task({"mission_id": "mission-1", "task_id": "task-1"})

    def test_rejects_unbounded_toolsets(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "approved read-only toolsets"):
                HermesWorkerAdapter(
                    profile="agent-flow-founder",
                    toolsets=("terminal",),
                    workdir=tmp,
                )

    def test_cli_runs_ready_task_with_hermes_and_submits_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database = root / "company.db"
            executable = self._write_fake_hermes(
                root / "fake-hermes",
                "#!/usr/bin/env python3\n"
                "import json\n"
                "print(json.dumps({'artifact': 'thesis.md', 'verification': 'checked', "
                "'summary': 'completed by Hermes'}))\n",
            )
            runtime = CompanyRuntime(database)
            runtime.bootstrap()
            mission_id = runtime.create_mission("Hermes mission", "Use a Hermes worker", 120, "medium")
            runtime.form_squad(mission_id)
            packet = runtime.ready_task_packets(mission_id, include_capability=False)[0]
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = cli_main(
                    [
                        "--db",
                        str(database),
                        "mission",
                        "run-hermes",
                        mission_id,
                        packet["task_id"],
                        "--profile",
                        "agent-flow-founder",
                        "--toolsets",
                        "web",
                        "--workdir",
                        str(root),
                        "--hermes-bin",
                        str(executable),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(output.getvalue())["status"], "done")
            task = next(
                task for task in runtime.mission(mission_id)["tasks"] if task["id"] == packet["task_id"]
            )
            self.assertEqual(task["status"], "done")
            self.assertEqual(task["evidence"]["summary"], "completed by Hermes")


if __name__ == "__main__":
    unittest.main()
