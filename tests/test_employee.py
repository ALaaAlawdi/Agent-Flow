"""Tests for Named Employee Protocol implementation."""

import unittest
import tempfile
import os
from pathlib import Path

from agent_flow.agents.employee import (
    EmployeeAgent,
    EmployeeTeam,
    EmployeeIdentity,
    Coworker,
    ConsultationRequest,
    ConsultationResponse,
    TaskEvidence,
    LoopState,
    AssessResult,
)


class TestEmployeeIdentity(unittest.TestCase):
    """Test EmployeeIdentity — the four fixed fields."""

    def test_create_identity(self):
        """Identity is created with name, title, goal, coworkers."""
        coworker = Coworker(name="Omar", title="Lead Architect", goal="Design robust systems")
        identity = EmployeeIdentity(
            name="Sara",
            title="Senior Market Analyst",
            goal="Deliver verified market insights for every mission",
            coworkers=[coworker],
        )

        self.assertEqual(identity.name, "Sara")
        self.assertEqual(identity.title, "Senior Market Analyst")
        self.assertEqual(len(identity.coworkers), 1)

    def test_find_coworker(self):
        """Can find a coworker by name (case-insensitive)."""
        cw1 = Coworker(name="Omar", title="Architect", goal="Design systems")
        cw2 = Coworker(name="Lina", title="Skeptic", goal="Challenge claims")
        identity = EmployeeIdentity(
            name="Sara", title="Analyst", goal="Deliver insights",
            coworkers=[cw1, cw2],
        )

        found = identity.find_coworker("omar")
        self.assertIsNotNone(found)
        self.assertEqual(found.title, "Architect")

        found = identity.find_coworker("LINA")
        self.assertIsNotNone(found)
        self.assertEqual(found.title, "Skeptic")

        self.assertIsNone(identity.find_coworker("unknown"))

    def test_identity_to_dict(self):
        """Identity serializes to dict."""
        cw = Coworker(name="Omar", title="Architect", goal="Design")
        identity = EmployeeIdentity(name="Sara", title="Analyst", goal="Insights", coworkers=[cw])

        d = identity.to_dict()
        self.assertEqual(d["name"], "Sara")
        self.assertEqual(d["coworkers"][0]["name"], "Omar")


class TestConsultationProtocol(unittest.TestCase):
    """Test the peer communication protocol."""

    def test_consultation_request_format(self):
        """Consultation request has context, problem, question."""
        req = ConsultationRequest(
            sender_name="Sara",
            receiver_name="Omar",
            context="I am researching market trends",
            problem="I cannot find reliable data on X",
            question="Do you know any reliable data sources for X?",
        )

        msg = req.format_message()
        self.assertIn("Context:", msg)
        self.assertIn("Problem:", msg)
        self.assertIn("Question:", msg)

    def test_consultation_response(self):
        """Response includes confidence."""
        req = ConsultationRequest(
            sender_name="Sara", receiver_name="Omar",
            context="Working on research", problem="Stuck on data",
            question="Help?",
        )

        resp = ConsultationResponse(
            responder_name="Omar",
            request=req,
            answer="Try using public datasets from data.gov",
            confidence=0.8,
        )

        self.assertEqual(resp.confidence, 0.8)
        self.assertIn("Omar", resp.format_message())


class TestTaskEvidence(unittest.TestCase):
    """Test evidence contract."""

    def test_evidence_contract(self):
        """Evidence requires artifact, verification, summary."""
        ev = TaskEvidence(
            artifact="/tmp/report.json",
            verification="File exists and contains valid JSON with 42 records",
            summary="Market analysis shows 15% growth potential",
        )
        self.assertEqual(ev.artifact, "/tmp/report.json")
        d = ev.to_dict()
        self.assertIn("artifact", d)
        self.assertIn("verification", d)
        self.assertIn("summary", d)


class TestEmployeeAgent(unittest.TestCase):
    """Test the autonomous decision loop."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.coworker = Coworker(name="Omar", title="Lead Architect", goal="Design robust systems")
        self.identity = EmployeeIdentity(
            name="Sara",
            title="Senior Market Analyst",
            goal="Deliver verified market insights for every mission",
            coworkers=[self.coworker],
        )

    def _make_agent(self):
        return EmployeeAgent(
            identity=self.identity,
            storage_dir=self.tmpdir,
            act_handler=lambda task: f"[Sara] Research complete: market size is $10B. Done.",
        )

    def test_create_agent(self):
        """Agent is created with identity and initial state."""
        agent = self._make_agent()
        self.assertEqual(agent.identity.name, "Sara")
        self.assertEqual(agent.state, LoopState.ORIENT)

    def test_orient(self):
        """Orient reads goal, task, messages, memory."""
        agent = self._make_agent()
        ctx = agent.orient("Research the AI market")
        self.assertIn("ai market", ctx["task"].lower())
        self.assertTrue(ctx["in_scope"])

    def test_orient_out_of_scope(self):
        """Task outside goal scope is flagged."""
        agent = self._make_agent()
        # Goal is about "market insights", this is about "HR policies" — no overlap
        ctx = agent.orient("Design HR policies for remote work")
        self.assertFalse(ctx["in_scope"])

    def test_run_task_completes(self):
        """Run full loop: orient → act → assess → submit → reflect."""
        agent = self._make_agent()
        result = agent.run_task("Research AI market trends")

        self.assertEqual(result["status"], "completed")
        self.assertIn("submission", result)
        self.assertIn("reflection", result)
        self.assertGreater(result["iterations"], 0)

    def test_run_task_out_of_scope(self):
        """Task outside scope returns out_of_scope status."""
        agent = self._make_agent()
        result = agent.run_task("Design HR policies for the company")
        self.assertEqual(result["status"], "out_of_scope")

    def test_assess_done(self):
        """Assess recognizes completion."""
        agent = self._make_agent()
        agent.current_task = "test"
        state = agent.assess("Task is complete and done. Final report submitted.")
        self.assertEqual(state, AssessResult.DONE)

    def test_assess_stuck(self):
        """Assess recognizes stuck state."""
        agent = self._make_agent()
        agent.current_task = "test"
        state = agent.assess("Error: cannot proceed. I am stuck.")
        self.assertEqual(state, AssessResult.STUCK)

    def test_assess_uncertain(self):
        """Assess recognizes uncertainty."""
        agent = self._make_agent()
        agent.current_task = "test"
        state = agent.assess("Maybe this approach could work, but I am not sure.")
        self.assertEqual(state, AssessResult.UNCERTAIN)

    def test_assess_progress(self):
        """Assess recognizes progress."""
        agent = self._make_agent()
        agent.current_task = "test"
        state = agent.assess("Still working on it, making good progress.")
        self.assertEqual(state, AssessResult.PROGRESS)

    def test_consult(self):
        """Consult picks a coworkers and creates a request."""
        agent = self._make_agent()
        agent.current_task = "Research market"

        req = agent.consult("Data is missing", "Where can I find this data?")
        self.assertIsNotNone(req)
        self.assertEqual(req.receiver_name, "Omar")
        self.assertEqual(req.sender_name, "Sara")

    def test_consult_no_coworkers(self):
        """Consult returns None when no coworkers available."""
        identity = EmployeeIdentity(name="Solo", title="Worker", goal="Get things done", coworkers=[])
        agent = EmployeeAgent(identity=identity, storage_dir=self.tmpdir)
        agent.current_task = "test"

        req = agent.consult("Stuck", "Help?")
        self.assertIsNone(req)

    def test_handle_consultation(self):
        """Agent handles incoming consultation as a coworker."""
        agent = self._make_agent()

        req = ConsultationRequest(
            sender_name="Omar",
            receiver_name="Sara",
            context="Designing system",
            problem="Need market data for sizing",
            question="What is the market size for this?",
        )

        resp = agent.handle_consultation(req)
        self.assertEqual(resp.responder_name, "Sara")
        self.assertGreater(resp.confidence, 0.5)  # Relevant to market analyst

    def test_handle_consultation_irrelevant(self):
        """Irrelevant consultation gets low confidence."""
        agent = self._make_agent()

        req = ConsultationRequest(
            sender_name="Omar",
            receiver_name="Sara",
            context="Building a bridge",
            problem="Need structural engineering help",
            question="How much concrete do I need?",
        )

        resp = agent.handle_consultation(req)
        self.assertLess(resp.confidence, 0.5)  # Not relevant to market analyst

    def test_submit_with_evidence(self):
        """Submit requires evidence contract."""
        agent = self._make_agent()
        agent.current_task = "Research market"

        ev = TaskEvidence(
            artifact="/tmp/report.json",
            verification="Checked with real data",
            summary="Market is growing",
        )

        submission = agent.submit(ev)
        self.assertEqual(submission["evidence"]["artifact"], "/tmp/report.json")

    def test_reflect(self):
        """Reflect saves memories and proposes skills."""
        agent = self._make_agent()
        agent.current_task = "Complex market analysis with multiple data sources"
        agent.iterations_in_current_task = 8

        reflection = agent.reflect()
        self.assertIn("memories_stored", reflection)
        self.assertIn("skills", reflection)

    def test_coworker_observations(self):
        """Agent builds knowledge about coworkers over time."""
        agent = self._make_agent()

        agent._observe_coworker("Omar", "Good at architecture decisions")
        agent._observe_coworker("Omar", "Helpful for system design questions")

        self.assertEqual(len(agent.coworker_observations["Omar"]), 2)


class TestEmployeeTeam(unittest.TestCase):
    """Test team of employee agents."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_team_creation(self):
        """Team holds multiple agents."""
        team = EmployeeTeam("Venture Team")
        self.assertEqual(team.name, "Venture Team")
        self.assertEqual(len(team.agents), 0)

    def test_add_agent(self):
        """Agents can be added to team."""
        team = EmployeeTeam("Venture Team")

        sara = EmployeeAgent(
            identity=EmployeeIdentity(
                name="Sara", title="Analyst", goal="Market insights",
                coworkers=[Coworker(name="Omar", title="Architect", goal="Design")],
            ),
            storage_dir=os.path.join(self.tmpdir, "sara"),
        )

        omar = EmployeeAgent(
            identity=EmployeeIdentity(
                name="Omar", title="Architect", goal="Design",
                coworkers=[Coworker(name="Sara", title="Analyst", goal="Market insights")],
            ),
            storage_dir=os.path.join(self.tmpdir, "omar"),
        )

        team.add_agent(sara)
        team.add_agent(omar)

        self.assertEqual(len(team.agents), 2)

    def test_run_task_on_agent(self):
        """Task runs on specific agent."""
        team = EmployeeTeam("Test Team")

        agent = EmployeeAgent(
            identity=EmployeeIdentity(name="Test", title="Tester", goal="Test things", coworkers=[]),
            storage_dir=os.path.join(self.tmpdir, "test"),
            act_handler=lambda t: "All tests pass. Done.",
        )
        team.add_agent(agent)

        result = team.run_task_on_agent("Test", "Run the test suite")
        self.assertEqual(result["status"], "completed")

    def test_run_task_nonexistent_agent(self):
        """Error when agent not found."""
        team = EmployeeTeam("Empty Team")
        result = team.run_task_on_agent("Ghost", "Do something")
        self.assertIn("error", result)

    def test_message_delivery(self):
        """Messages are delivered between agents."""
        team = EmployeeTeam("Collab Team")

        sara = EmployeeAgent(
            identity=EmployeeIdentity(
                name="Sara", title="Analyst", goal="Market insights",
                coworkers=[Coworker(name="Omar", title="Architect", goal="Design")],
            ),
            storage_dir=os.path.join(self.tmpdir, "sara"),
        )

        omar = EmployeeAgent(
            identity=EmployeeIdentity(
                name="Omar", title="Architect", goal="Design",
                coworkers=[Coworker(name="Sara", title="Analyst", goal="Market insights")],
            ),
            storage_dir=os.path.join(self.tmpdir, "omar"),
        )

        team.add_agent(sara)
        team.add_agent(omar)

        # Sara consults Omar
        sara.current_task = "Research"
        req = sara.consult("Need help", "How to structure this?")
        self.assertIsNotNone(req)

        # Deliver messages
        team.deliver_messages()

        # Omar should have received the consultation
        self.assertGreater(len(omar.inbox), 0)
        # Sara should have received a response
        self.assertGreater(len(sara.inbox), 0)


if __name__ == "__main__":
    unittest.main()
