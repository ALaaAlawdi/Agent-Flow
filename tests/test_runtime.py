import base64
import hashlib
import hmac
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_flow.runtime import CompanyRuntime


def sign_capability(runtime: CompanyRuntime, secret: bytes, claims: object) -> str:
    payload = json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(secret, payload, hashlib.sha256).digest()
    return f"{runtime._encode_token_part(payload)}.{runtime._encode_token_part(signature)}"


class CompanyRuntimeTests(unittest.TestCase):
    def test_capability_secret_requires_at_least_32_bytes(self):
        with self.assertRaisesRegex(ValueError, "32 bytes"):
            CompanyRuntime("company.db", capability_secret=b"too-short")

    def test_capability_rejects_invalid_ttl_oversized_and_non_object_tokens(self):
        secret = b"test-secret-with-sufficient-entropy"
        with self.assertRaisesRegex(ValueError, "TTL"):
            CompanyRuntime("company.db", capability_secret=secret, capability_ttl_seconds=0)

        runtime = CompanyRuntime("company.db", capability_secret=secret)
        with self.assertRaisesRegex(PermissionError, "invalid"):
            runtime._authenticate_task_capability("a" * 4097, "mission", "task")

        token = sign_capability(runtime, secret, [])
        with self.assertRaisesRegex(PermissionError, "invalid"):
            runtime._authenticate_task_capability(token, "mission", "task")

    def test_capability_requires_canonical_encoding_and_exact_claim_schema(self):
        secret = b"test-secret-with-sufficient-entropy"
        runtime = CompanyRuntime("company.db", capability_secret=secret, clock=lambda: 1_000.0)
        claims = {
            "exp": 1_300,
            "iat": 1_000,
            "mission_id": "mission",
            "nonce": "a" * 32,
            "task_id": "task",
            "worker_id": "founder",
        }
        canonical = sign_capability(runtime, secret, claims)
        payload_part, signature_part = canonical.split(".")
        invalid_encodings = [
            f"{payload_part}=.{signature_part}",
            f"{payload_part}.{signature_part}=",
            f"+{payload_part[1:]}.{signature_part}",
            f"/{payload_part[1:]}.{signature_part}",
            f"{payload_part}.+{signature_part[1:]}",
            f"{payload_part}./{signature_part[1:]}",
        ]
        for invalid_token in invalid_encodings:
            with self.subTest(token=invalid_token):
                with self.assertRaisesRegex(PermissionError, "invalid"):
                    runtime._authenticate_task_capability(invalid_token, "mission", "task")

        invalid_claims = [
            {**claims, "unexpected": "claim"},
            {key: value for key, value in claims.items() if key != "worker_id"},
            {**claims, "iat": True},
            {**claims, "exp": True},
            {**claims, "nonce": "g" * 32},
            {**claims, "nonce": "A" * 32},
        ]
        for malformed in invalid_claims:
            with self.subTest(claims=malformed):
                with self.assertRaisesRegex(PermissionError, "invalid"):
                    runtime._authenticate_task_capability(
                        sign_capability(runtime, secret, malformed), "mission", "task"
                    )

    def test_capability_verifies_hmac_before_parsing_json(self):
        secret = b"test-secret-with-sufficient-entropy"
        runtime = CompanyRuntime("company.db", capability_secret=secret, clock=lambda: 1_000.0)
        claims = {
            "exp": 1_300,
            "iat": 1_000,
            "mission_id": "mission",
            "nonce": "a" * 32,
            "task_id": "task",
            "worker_id": "founder",
        }
        payload_part, signature_part = sign_capability(runtime, secret, claims).split(".")
        replacement = "A" if signature_part[0] != "A" else "B"
        bad_signature_token = f"{payload_part}.{replacement}{signature_part[1:]}"

        with patch("agent_flow.runtime.json.loads") as loads:
            with self.assertRaisesRegex(PermissionError, "invalid"):
                runtime._authenticate_task_capability(bad_signature_token, "mission", "task")
            loads.assert_not_called()

    def test_capability_rejects_invalid_time_invariants(self):
        secret = b"test-secret-with-sufficient-entropy"
        runtime = CompanyRuntime(
            "company.db", capability_secret=secret, capability_ttl_seconds=300, clock=lambda: 1_000.0
        )
        claims = {
            "exp": 1_300,
            "iat": 1_000,
            "mission_id": "mission",
            "nonce": "a" * 32,
            "task_id": "task",
            "worker_id": "founder",
        }
        invalid_times = [
            {**claims, "exp": 1_000},
            {**claims, "exp": 1_301},
            {**claims, "iat": 1_006, "exp": 1_306},
        ]
        for malformed in invalid_times:
            with self.subTest(claims=malformed):
                with self.assertRaisesRegex(PermissionError, "invalid"):
                    runtime._authenticate_task_capability(
                        sign_capability(runtime, secret, malformed), "mission", "task"
                    )

    def test_task_capability_token_authorizes_assigned_worker_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            secret = b"test-secret-with-sufficient-entropy"
            runtime = CompanyRuntime(Path(tmp) / "company.db", capability_secret=secret)
            runtime.bootstrap()
            mission_id = runtime.create_mission("Token Co", "Authenticate external worker submissions.", 120)
            assignments = runtime.form_squad(mission_id)
            packet = next(
                packet for packet in runtime.ready_task_packets(mission_id)
                if packet["task_id"] == "mission_thesis"
            )
            wrong_worker = "redteam"
            self.assertNotEqual(wrong_worker, assignments["mission_thesis"])
            now = int(runtime._clock())
            wrong_worker_token = sign_capability(
                runtime,
                secret,
                {
                    "exp": now + 300,
                    "iat": now,
                    "mission_id": mission_id,
                    "nonce": "a" * 32,
                    "task_id": "mission_thesis",
                    "worker_id": wrong_worker,
                },
            )
            with self.assertRaisesRegex(PermissionError, "assigned"):
                runtime.complete_task_with_capability(
                    mission_id,
                    "mission_thesis",
                    wrong_worker_token,
                    {"artifact": "thesis.md", "verification": "checked", "summary": "bounded thesis"},
                )

            runtime.complete_task_with_capability(
                mission_id,
                "mission_thesis",
                packet["capability_token"],
                {"artifact": "thesis.md", "verification": "checked", "summary": "bounded thesis"},
            )

            task = next(task for task in runtime.mission(mission_id)["tasks"] if task["id"] == "mission_thesis")
            self.assertEqual(task["status"], "done")

    def test_task_capability_token_expires(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = [1_000.0]
            runtime = CompanyRuntime(
                Path(tmp) / "company.db",
                capability_secret=b"test-secret-with-sufficient-entropy",
                capability_ttl_seconds=60,
                clock=lambda: now[0],
            )
            runtime.bootstrap()
            mission_id = runtime.create_mission("Expiry Co", "Reject stale worker authority.", 120)
            runtime.form_squad(mission_id)
            packet = next(
                packet for packet in runtime.ready_task_packets(mission_id)
                if packet["task_id"] == "mission_thesis"
            )
            now[0] = 1_060.0

            with self.assertRaisesRegex(PermissionError, "expired"):
                runtime.complete_task_with_capability(
                    mission_id,
                    "mission_thesis",
                    packet["capability_token"],
                    {"artifact": "thesis.md", "verification": "checked", "summary": "bounded thesis"},
                )

    def test_task_capability_token_rejects_tampered_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = [1_000.0]
            runtime = CompanyRuntime(
                Path(tmp) / "company.db",
                capability_secret=b"test-secret-with-sufficient-entropy",
                capability_ttl_seconds=60,
                clock=lambda: now[0],
            )
            runtime.bootstrap()
            mission_id = runtime.create_mission("Tamper Co", "Reject forged worker authority.", 120)
            runtime.form_squad(mission_id)
            packet = next(
                packet for packet in runtime.ready_task_packets(mission_id)
                if packet["task_id"] == "mission_thesis"
            )
            payload_part, signature_part = packet["capability_token"].split(".")
            payload = json.loads(base64.urlsafe_b64decode(payload_part + "=="))
            payload["exp"] = 2_000
            forged_payload = base64.urlsafe_b64encode(
                json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
            ).rstrip(b"=").decode("ascii")
            forged_token = f"{forged_payload}.{signature_part}"
            now[0] = 1_060.0

            with self.assertRaisesRegex(PermissionError, "invalid"):
                runtime.complete_task_with_capability(
                    mission_id,
                    "mission_thesis",
                    forged_token,
                    {"artifact": "thesis.md", "verification": "checked", "summary": "bounded thesis"},
                )

    def test_task_capability_token_is_scoped_to_one_mission_and_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = CompanyRuntime(
                Path(tmp) / "company.db",
                capability_secret=b"test-secret-with-sufficient-entropy",
            )
            runtime.bootstrap()
            first_mission = runtime.create_mission("First Co", "Issue bounded worker authority.", 120)
            second_mission = runtime.create_mission("Second Co", "Reject cross-mission authority.", 120)
            runtime.form_squad(first_mission)
            runtime.form_squad(second_mission)
            token = next(
                packet["capability_token"] for packet in runtime.ready_task_packets(first_mission)
                if packet["task_id"] == "mission_thesis"
            )

            with self.assertRaisesRegex(PermissionError, "scope"):
                runtime.complete_task_with_capability(
                    second_mission,
                    "mission_thesis",
                    token,
                    {"artifact": "thesis.md", "verification": "checked", "summary": "bounded thesis"},
                )

            with self.assertRaisesRegex(PermissionError, "scope"):
                runtime.complete_task_with_capability(
                    first_mission,
                    "market_intelligence",
                    token,
                    {"artifact": "market.md", "verification": "checked", "summary": "bounded market"},
                )

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
            secret = b"test-secret-with-sufficient-entropy"
            runtime = CompanyRuntime(Path(tmp) / "company.db", capability_secret=secret)
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
            now = int(runtime._clock())
            worker_capability_for_human_gate = sign_capability(
                runtime,
                secret,
                {
                    "exp": now + 300,
                    "iat": now,
                    "mission_id": mission_id,
                    "nonce": "b" * 32,
                    "task_id": "human_launch_approval",
                    "worker_id": "governor",
                },
            )
            with self.assertRaisesRegex(PermissionError, "human"):
                runtime.complete_task_with_capability(
                    mission_id,
                    "human_launch_approval",
                    worker_capability_for_human_gate,
                    evidence,
                )
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
