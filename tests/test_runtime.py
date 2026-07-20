import tempfile
import unittest
from pathlib import Path

from agent_flow.runtime import CompanyRuntime


class CompanyRuntimeTests(unittest.TestCase):
    def test_bootstrap_registers_default_agents_and_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = CompanyRuntime(Path(tmp) / "company.db")

            runtime.bootstrap()

            agents = runtime.list_agents()
            self.assertGreaterEqual(len(agents), 8)
            self.assertIn("founder", {agent["id"] for agent in agents})
            self.assertTrue(all(agent["reputation"] == 50 for agent in agents))
            events = runtime.events()
            self.assertEqual(events[0]["type"], "company_bootstrapped")

    def test_create_mission_builds_budgeted_dependency_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = CompanyRuntime(Path(tmp) / "company.db")
            runtime.bootstrap()

            mission_id = runtime.create_mission(
                title="Impossible Company",
                brief="Invent a defensible AI-native company.",
                budget=120,
                risk="high",
            )

            mission = runtime.mission(mission_id)
            self.assertEqual(mission["budget_total"], 120)
            self.assertEqual(mission["budget_spent"], 0)
            self.assertEqual(mission["risk"], "high")
            ready = {task["id"] for task in mission["tasks"] if task["status"] == "ready"}
            self.assertEqual(
                ready,
                {"mission_thesis", "market_intelligence", "customer_pain", "risk_hypothesis"},
            )
            self.assertEqual(mission["tasks"][-1]["id"], "human_launch_approval")
            self.assertEqual(runtime.events()[-1]["type"], "mission_created")

    def test_form_squad_assigns_capable_agents_and_keeps_human_gate_unassigned(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = CompanyRuntime(Path(tmp) / "company.db")
            runtime.bootstrap()
            mission_id = runtime.create_mission("Moonshot", "Build the impossible safely.", 120, "high")

            assignments = runtime.form_squad(mission_id)

            mission = runtime.mission(mission_id)
            agents = {agent["id"]: agent for agent in runtime.list_agents()}
            for task in mission["tasks"]:
                if task["human_only"]:
                    self.assertIsNone(task["assigned_agent"])
                    continue
                assigned = task["assigned_agent"]
                self.assertEqual(assignments[task["id"]], assigned)
                self.assertIn(task["capability"], agents[assigned]["capabilities"])
            producer = assignments["prototype"]
            self.assertNotEqual(producer, assignments["independent_verification"])
            self.assertNotEqual(producer, assignments["red_team"])
            self.assertEqual(runtime.events()[-1]["type"], "squad_formed")

    def test_completion_requires_evidence_dependencies_and_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = CompanyRuntime(Path(tmp) / "company.db")
            runtime.bootstrap()
            mission_id = runtime.create_mission("Evidence Co", "Only verified work counts.", 120)
            assignments = runtime.form_squad(mission_id)

            with self.assertRaisesRegex(ValueError, "evidence"):
                runtime.complete_task(mission_id, "mission_thesis", assignments["mission_thesis"], {})
            with self.assertRaisesRegex(RuntimeError, "not ready"):
                runtime.complete_task(
                    mission_id,
                    "architecture",
                    assignments["architecture"],
                    {"artifact": "architecture.md", "verification": "reviewed", "summary": "draft"},
                )

            evidence = {"artifact": "artifact.md", "verification": "checked", "summary": "claim falsified"}
            for task_id in ("mission_thesis", "market_intelligence", "customer_pain", "risk_hypothesis"):
                runtime.complete_task(mission_id, task_id, assignments[task_id], evidence)

            mission = runtime.mission(mission_id)
            tasks = {task["id"]: task for task in mission["tasks"]}
            self.assertEqual(mission["budget_spent"], 20)
            self.assertEqual(tasks["venture_design"]["status"], "ready")
            self.assertEqual(runtime.events()[-1]["type"], "task_completed")

        with tempfile.TemporaryDirectory() as tmp:
            runtime = CompanyRuntime(Path(tmp) / "company.db")
            runtime.bootstrap()
            mission_id = runtime.create_mission("Poor Co", "Budget discipline.", 3)
            assignments = runtime.form_squad(mission_id)
            with self.assertRaisesRegex(RuntimeError, "budget"):
                runtime.complete_task(
                    mission_id,
                    "mission_thesis",
                    assignments["mission_thesis"],
                    {"artifact": "thesis.md", "verification": "checked", "summary": "done"},
                )

    def test_launch_requires_real_human_approval_after_all_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = CompanyRuntime(Path(tmp) / "company.db")
            runtime.bootstrap()
            mission_id = runtime.create_mission("Constitution Co", "Agents cannot approve themselves.", 120, "critical")
            assignments = runtime.form_squad(mission_id)
            evidence = {"artifact": "proof.json", "verification": "independently checked", "summary": "passed"}

            while True:
                mission = runtime.mission(mission_id)
                ready = [
                    task for task in mission["tasks"]
                    if task["status"] == "ready" and not task["human_only"]
                ]
                if not ready:
                    break
                for task in ready:
                    task_evidence = dict(evidence)
                    if task["independent_review"]:
                        task_evidence["decision"] = "build" if task["id"] == "board_review" else "pass"
                    runtime.complete_task(mission_id, task["id"], assignments[task["id"]], task_evidence)

            tasks = {task["id"]: task for task in runtime.mission(mission_id)["tasks"]}
            self.assertEqual(tasks["human_launch_approval"]["status"], "ready")
            with self.assertRaises(PermissionError):
                runtime.complete_task(mission_id, "human_launch_approval", "governor", evidence)
            with self.assertRaisesRegex(PermissionError, "human"):
                runtime.approve_launch(mission_id, actor="governor", actor_type="agent", rationale="I approve myself")
            with self.assertRaisesRegex(ValueError, "rationale"):
                runtime.approve_launch(mission_id, actor="Alaa", actor_type="human", rationale="")

            runtime.approve_launch(
                mission_id,
                actor="Alaa",
                actor_type="human",
                rationale="Reviewed evidence, risks, economics, and rollback boundaries.",
            )

            mission = runtime.mission(mission_id)
            self.assertEqual(mission["status"], "approved_for_launch")
            self.assertEqual(mission["tasks"][-1]["status"], "done")
            self.assertEqual(runtime.events()[-1]["type"], "launch_approved")

    def test_verified_work_updates_reputation_and_board_can_record_lesson(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = CompanyRuntime(Path(tmp) / "company.db")
            runtime.bootstrap()
            mission_id = runtime.create_mission("Learning Co", "Turn outcomes into memory.", 120)
            assignments = runtime.form_squad(mission_id)
            evidence = {"artifact": "evidence.json", "verification": "checked", "summary": "result"}

            runtime.complete_task(mission_id, "mission_thesis", assignments["mission_thesis"], evidence)
            founder = next(agent for agent in runtime.list_agents() if agent["id"] == "founder")
            self.assertEqual(founder["reputation"], 51)
            with self.assertRaisesRegex(RuntimeError, "board"):
                runtime.record_lesson(mission_id, "pivot", "Premature lesson", "archivist")

            while True:
                ready = [
                    task for task in runtime.mission(mission_id)["tasks"]
                    if task["status"] == "ready" and not task["human_only"]
                ]
                if not ready:
                    break
                for task in ready:
                    task_evidence = dict(evidence)
                    if task["independent_review"]:
                        task_evidence["decision"] = "pivot" if task["id"] == "board_review" else "pass"
                    runtime.complete_task(mission_id, task["id"], assignments[task["id"]], task_evidence)
            with self.assertRaisesRegex(RuntimeError, "board decision"):
                runtime.record_lesson(mission_id, "build", "Contradicts the board", "archivist")
            lesson_id = runtime.record_lesson(
                mission_id,
                outcome="pivot",
                content="Start with the deployment gate; defer the full simulation cloud.",
                actor="archivist",
            )

            lessons = runtime.lessons()
            self.assertEqual(lessons[0]["id"], lesson_id)
            self.assertEqual(lessons[0]["outcome"], "pivot")
            self.assertEqual(runtime.events()[-1]["type"], "lesson_recorded")

    def test_ready_task_packets_are_bounded_inputs_for_ai_workers(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = CompanyRuntime(Path(tmp) / "company.db")
            runtime.bootstrap()
            mission_id = runtime.create_mission("Packet Co", "Keep models outside the control plane.", 120, "high")
            runtime.form_squad(mission_id)

            packets = runtime.ready_task_packets(mission_id)

            self.assertEqual(len(packets), 4)
            packet = next(item for item in packets if item["task_id"] == "mission_thesis")
            self.assertEqual(packet["mission_id"], mission_id)
            self.assertEqual(packet["worker_id"], "founder")
            self.assertEqual(packet["budget"]["credits"], 5)
            self.assertEqual(packet["input_artifacts"], [])
            self.assertFalse(packet["authority"]["may_mutate_company_state"])
            self.assertFalse(packet["authority"]["may_approve_own_work"])
            self.assertEqual(packet["evidence_contract"], ["artifact", "verification", "summary"])

    def test_failed_independent_review_blocks_launch_even_if_board_recommends_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = CompanyRuntime(Path(tmp) / "company.db")
            runtime.bootstrap()
            mission_id = runtime.create_mission("Blocked Co", "A red-team failure must have force.", 120, "critical")
            assignments = runtime.form_squad(mission_id)

            while True:
                mission = runtime.mission(mission_id)
                ready = [task for task in mission["tasks"] if task["status"] == "ready" and not task["human_only"]]
                if not ready:
                    break
                for task in ready:
                    evidence = {
                        "artifact": f"artifact-{task['id']}",
                        "verification": "checked",
                        "summary": "bounded result",
                    }
                    if task["independent_review"]:
                        evidence["decision"] = (
                            "fail" if task["id"] == "red_team" else "build" if task["id"] == "board_review" else "pass"
                        )
                    runtime.complete_task(mission_id, task["id"], assignments[task["id"]], evidence)

            with self.assertRaisesRegex(RuntimeError, "blocking independent review"):
                runtime.approve_launch(mission_id, "Human", "human", "Reviewed all evidence")


if __name__ == "__main__":
    unittest.main()
