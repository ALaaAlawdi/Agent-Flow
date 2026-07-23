"""
Named Employee Agent — implements the Employee Protocol.

Each agent has identity (name, title, goal, coworkers), runs an autonomous
decision loop (orient → act → assess → consult/submit/reflect), communicates
with peers, and learns from experience.

See: docs/EMPLOYEE_PROTOCOL.md
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from .events import EventStore, EventType
from .hermes_learning_loop import AgentLearningLoop, MemoryStore, SkillSystem


# ──────────────────────────────────────────────
# Identity
# ──────────────────────────────────────────────


@dataclass
class Coworker:
    """A peer the agent knows and can consult."""

    name: str
    title: str
    goal: str


@dataclass
class EmployeeIdentity:
    """The four fixed fields that define an employee agent."""

    name: str
    title: str
    goal: str
    coworkers: list[Coworker] = field(default_factory=list)

    def find_coworker(self, name: str) -> Optional[Coworker]:
        for cw in self.coworkers:
            if cw.name.lower() == name.lower():
                return cw
        return None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "title": self.title,
            "goal": self.goal,
            "coworkers": [{"name": cw.name, "title": cw.title, "goal": cw.goal} for cw in self.coworkers],
        }


# ──────────────────────────────────────────────
# Decision Loop State
# ──────────────────────────────────────────────

from enum import Enum, auto


class LoopState(Enum):
    ORIENT = auto()
    ACT = auto()
    ASSESS = auto()
    CONSULT = auto()
    INTEGRATE = auto()
    SUBMIT = auto()
    REFLECT = auto()


class AssessResult(Enum):
    DONE = "done"
    STUCK = "stuck"
    UNCERTAIN = "uncertain"
    PROGRESS = "progress"


# ──────────────────────────────────────────────
# Peer Messages
# ──────────────────────────────────────────────


@dataclass
class ConsultationRequest:
    """A structured request to a coworker."""

    sender_name: str
    receiver_name: str
    context: str  # What I am working on, what I have done
    problem: str  # The specific thing I am uncertain about
    question: str  # The one thing I need
    sent_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def format_message(self) -> str:
        return f"""Context: {self.context}
Problem: {self.problem}
Question: {self.question}"""


@dataclass
class ConsultationResponse:
    """A coworker's response to a consultation."""

    responder_name: str
    request: ConsultationRequest
    answer: str
    confidence: float = 0.5
    responded_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def format_message(self) -> str:
        return f"Response from {self.responder_name} (confidence: {self.confidence:.0%}):\n{self.answer}"


# ──────────────────────────────────────────────
# Evidence Contract
# ──────────────────────────────────────────────


@dataclass
class TaskEvidence:
    """Evidence contract — artifact, verification, summary."""

    artifact: str  # path, URL, object ID
    verification: str  # how the artifact was actually checked
    summary: str  # bounded conclusion supported by evidence

    def to_dict(self) -> dict:
        return {
            "artifact": self.artifact,
            "verification": self.verification,
            "summary": self.summary,
        }


# ──────────────────────────────────────────────
# Employee Agent
# ──────────────────────────────────────────────


class EmployeeAgent:
    """An agent that follows the Named Employee Protocol.

    Identity is fixed at creation. Every task flows through the autonomous
    decision loop: orient → act → assess → (consult → integrate) → submit → reflect.
    """

    def __init__(
        self,
        identity: EmployeeIdentity,
        *,
        storage_dir: str = "/opt/data/Agent-Flow/agent_memories",
        act_handler: Optional[Callable[[str], str]] = None,
    ):
        self.identity = identity
        self.state = LoopState.ORIENT
        self.learning_loop = AgentLearningLoop(identity.name, identity.name)

        # Inbox/outbox for peer communication
        self.inbox: list[ConsultationRequest | ConsultationResponse] = []
        self.outbox: list[ConsultationRequest | ConsultationResponse] = []
        self.sent_requests: dict[str, ConsultationRequest] = {}

        # Task tracking
        self.current_task: Optional[str] = None
        self.current_evidence: Optional[TaskEvidence] = None
        self.iterations_in_current_task = 0
        self.max_iterations = 50
        self.consultation_count = 0
        self.max_consultations_per_task = 5

        # Coworker knowledge (built over time through interaction)
        self.coworker_observations: dict[str, list[str]] = {}

        # Events
        self.events = EventStore(f"employee_{identity.name}")

        # Storage
        self.storage_dir = Path(storage_dir) / identity.name
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # External action handler (actual work, can be LLM call)
        self._act_handler = act_handler or self._default_act_handler

        self._load_state()

    # ── ORIENT ──────────────────────────────

    def orient(self, task: str) -> dict:
        """Read goal, task, messages, and memory before acting.

        Returns orientation context dict.
        """
        self.state = LoopState.ORIENT
        self.current_task = task
        self.iterations_in_current_task = 0

        # Read messages from coworkers
        messages = self._read_inbox()

        # Recall relevant memories
        relevant_memories = self.learning_loop.memory.recall(query=task, limit=5)

        # Check if task is within goal scope
        in_scope = self._is_in_scope(task)

        orientation = {
            "agent": self.identity.name,
            "title": self.identity.title,
            "goal": self.identity.goal,
            "task": task,
            "in_scope": in_scope,
            "messages_waiting": len(messages),
            "relevant_memories": len(relevant_memories),
            "coworkers_known": [cw.name for cw in self.identity.coworkers],
        }

        self._emit("oriented", orientation)
        return orientation

    # ── ACT ─────────────────────────────────

    def act(self) -> str:
        """Work on the task using available tools.

        Continues until reaching an assess state.
        """
        self.state = LoopState.ACT
        self.iterations_in_current_task += 1

        if not self.current_task:
            raise RuntimeError("Cannot act without a task. Call orient() first.")

        # Perform the actual work
        result = self._act_handler(self.current_task)

        # Record in learning loop
        nudge = self.learning_loop.after_action(self.current_task[:50], result)

        self._emit("acted", {"iteration": self.iterations_in_current_task, "nudge": nudge})
        return result

    # ── ASSESS ──────────────────────────────

    def assess(self, last_result: str) -> AssessResult:
        """Evaluate whether task is done, stuck, uncertain, or progressing.

        The agent makes this judgment autonomously.
        """
        self.state = LoopState.ASSESS

        # Heuristic assessment (can be enhanced with LLM)
        if self.iterations_in_current_task >= self.max_iterations:
            state = AssessResult.STUCK
        elif self._is_complete(last_result):
            state = AssessResult.DONE
        elif self._is_stuck(last_result):
            state = AssessResult.STUCK
        elif self._is_uncertain(last_result):
            state = AssessResult.UNCERTAIN
        else:
            state = AssessResult.PROGRESS

        self._emit("assessed", {"result": state.value, "iteration": self.iterations_in_current_task})
        return state

    # ── CONSULT ─────────────────────────────

    def consult(self, problem: str, question: str) -> Optional[ConsultationRequest]:
        """Consult a coworker with a specific question.

        Picks the best coworker for the problem type, sends a structured
        consultation request.
        """
        self.state = LoopState.CONSULT

        if self.consultation_count >= self.max_consultations_per_task:
            return None

        coworker = self._pick_coworker_for_problem(problem)
        if not coworker:
            return None

        request = ConsultationRequest(
            sender_name=self.identity.name,
            receiver_name=coworker.name,
            context=f"Working on: {self.current_task}\nIterations: {self.iterations_in_current_task}",
            problem=problem,
            question=question,
        )

        self.outbox.append(request)
        self.sent_requests[coworker.name] = request
        self.consultation_count += 1

        self._emit("consulted", {"coworker": coworker.name, "question": question})
        return request

    # ── INTEGRATE ───────────────────────────

    def integrate(self, response: ConsultationResponse) -> bool:
        """Integrate a coworker's response.

        Returns True if response resolves the uncertainty.
        """
        self.state = LoopState.INTEGRATE

        # Assess the response — never blindly follow
        resolved = response.confidence >= 0.3 and len(response.answer) > 10

        # Record what we learned about this coworker
        self._observe_coworker(
            response.responder_name,
            f"Helpful for: {response.request.problem[:100]} — confidence: {response.confidence:.0%}",
        )

        # Learn from the consultation
        self.learning_loop.after_action(
            f"consulted_{response.responder_name}",
            f"Integrated response: {response.answer[:100]} (resolved={resolved})",
        )

        self._emit("integrated", {"coworker": response.responder_name, "resolved": resolved})
        return resolved

    # ── SUBMIT ──────────────────────────────

    def submit(self, evidence: TaskEvidence) -> dict:
        """Submit task with evidence contract.

        Requires all three: artifact, verification, summary.
        """
        self.state = LoopState.SUBMIT
        self.current_evidence = evidence

        submission = {
            "agent": self.identity.name,
            "task": self.current_task[:200] if self.current_task else "",
            "evidence": evidence.to_dict(),
            "submitted_at": datetime.now().isoformat(),
        }

        self._emit("submitted", evidence.to_dict())
        self._save_state()

        return submission

    # ── REFLECT ─────────────────────────────

    def reflect(self) -> dict:
        """Save what was learned. Propose long-term skills if generalizable.

        Returns reflection summary.
        """
        self.state = LoopState.REFLECT

        # Save key facts to short-term memory
        if self.current_task:
            self.learning_loop.memory.add(
                event_type="task_complete",
                data={"task": self.current_task[:100], "iterations": self.iterations_in_current_task},
                importance=0.6,
            )

        # Check if anything generalizable
        generalizable = self._find_generalizable_skills()
        if generalizable:
            for skill_name in generalizable:
                self.learning_loop.skills.get_or_create(
                    name=skill_name,
                    description=f"Generalized from task: {self.current_task[:60] if self.current_task else 'unknown'}",
                    tags=["generalized", "from-reflection"],
                )

        # Reset task state but keep learning
        self.consultation_count = 0

        reflection = {
            "agent": self.identity.name,
            "memories_stored": len(self.learning_loop.memory.memories),
            "skills": len(self.learning_loop.skills.skills),
            "generalized_skills": generalizable,
            "reflected_at": datetime.now().isoformat(),
        }

        self._emit("reflected", reflection)
        self._save_state()

        return reflection

    # ── FULL LOOP ───────────────────────────

    def run_task(self, task: str) -> dict:
        """Run the complete autonomous decision loop for a task.

        orient → act → assess → (consult → integrate → act) ... → submit → reflect
        """
        # Orient
        ctx = self.orient(task)

        if not ctx["in_scope"]:
            return {"status": "out_of_scope", "orientation": ctx, "suggestion": self._route_to_coworker(task)}

        last_result = ""

        while True:
            # Act
            last_result = self.act()

            # Assess
            state = self.assess(last_result)

            if state == AssessResult.DONE:
                break

            elif state in (AssessResult.STUCK, AssessResult.UNCERTAIN):
                # Consult
                problem = f"Task: {task[:80]}... Result so far: {last_result[:100]}"
                question = "How should I proceed?" if state == AssessResult.STUCK else "Can you verify this approach?"

                request = self.consult(problem, question)
                if request is None:
                    break  # Can't consult more, submit what we have

                # In a real system, this would go through message passing.
                # For now, simulate integration with no response.
                # The caller can inject responses via receive_message().
                if not self.inbox:
                    break  # No response yet, break to avoid infinite loop

                # Integrate available responses
                for msg in self.inbox:
                    if isinstance(msg, ConsultationResponse) and msg.request == request:
                        self.inbox.remove(msg)
                        self.integrate(msg)
                        break
                else:
                    break  # No matching response, break

            elif state == AssessResult.PROGRESS:
                continue  # Keep acting

            else:
                break

        # Build evidence
        artifact_path = str(self.storage_dir / f"task_{int(time.time())}.json")
        verification = f"Task '{task[:50]}' completed in {self.iterations_in_current_task} iterations by {self.identity.name}"

        evidence = TaskEvidence(
            artifact=artifact_path,
            verification=verification,
            summary=last_result[:500],
        )

        # Save evidence
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        Path(artifact_path).write_text(json.dumps(evidence.to_dict(), indent=2))

        # Submit
        submission = self.submit(evidence)

        # Reflect
        reflection = self.reflect()

        return {
            "status": "completed",
            "submission": submission,
            "reflection": reflection,
            "iterations": self.iterations_in_current_task,
            "consultations": self.consultation_count,
        }

    # ── PEER COMMUNICATION ──────────────────

    def receive_message(self, message: ConsultationRequest | ConsultationResponse):
        """Receive a message from a coworker — placed in inbox."""
        self.inbox.append(message)

    def send_message(self, message: ConsultationRequest | ConsultationResponse):
        """Place a message in outbox for delivery."""
        self.outbox.append(message)

    def poll_outbox(self) -> list[ConsultationRequest | ConsultationResponse]:
        """Get and clear outbox for message delivery."""
        messages = list(self.outbox)
        self.outbox.clear()
        return messages

    def handle_consultation(self, request: ConsultationRequest) -> ConsultationResponse:
        """Handle an incoming consultation request as a coworker.

        Answers based on own title and goal, not by taking over the task.
        """
        # Determine if this falls within our expertise
        relevant = self._is_in_scope(request.question)

        if relevant:
            answer = f"As {self.identity.title}, I can help with this.\n"
            answer += f"My goal '{self.identity.goal}' is relevant to your question.\n"
            answer += f"Based on my expertise, I recommend proceeding with: {self._generate_advice(request)}"
            confidence = 0.7
        else:
            answer = f"As {self.identity.title}, this falls outside my core expertise (goal: {self.identity.goal}).\n"
            answer += f"I suggest consulting a coworker with more relevant expertise."
            confidence = 0.2

        return ConsultationResponse(
            responder_name=self.identity.name,
            request=request,
            answer=answer,
            confidence=confidence,
        )

    # ── HELPERS ─────────────────────────────

    STOP_WORDS = {
        "for", "the", "a", "an", "is", "are", "of", "in", "to", "and", "or", "on", "at",
        "be", "it", "this", "that", "with", "from", "by", "as", "not", "no", "all",
        "every", "each", "some", "any", "can", "will", "would", "could", "should",
        "have", "has", "had", "do", "does", "did", "was", "were", "been", "being",
    }

    def _is_in_scope(self, task: str) -> bool:
        """Check if a task falls within the agent's goal scope."""
        goal_keywords = set(self.identity.goal.lower().split()) - self.STOP_WORDS
        task_keywords = set(task.lower().split()) - self.STOP_WORDS
        overlap = goal_keywords & task_keywords
        return len(overlap) > 0

    def _is_complete(self, result: str) -> bool:
        """Heuristic: does result indicate completion?"""
        indicators = ["done", "complete", "finished", "completed", "final", "submitted"]
        result_lower = result.lower()
        return any(ind in result_lower for ind in indicators) and len(result) >= 30

    def _is_stuck(self, result: str) -> bool:
        """Heuristic: does result indicate being stuck?"""
        indicators = ["error", "failed", "stuck", "cannot", "unable", "don't know", "unsure"]
        result_lower = result.lower()
        return any(ind in result_lower for ind in indicators)

    def _is_uncertain(self, result: str) -> bool:
        """Heuristic: does result indicate uncertainty?"""
        indicators = ["maybe", "perhaps", "possibly", "might", "could be", "not sure", "uncertain"]
        result_lower = result.lower()
        return any(ind in result_lower for ind in indicators)

    def _pick_coworker_for_problem(self, problem: str) -> Optional[Coworker]:
        """Pick the best coworker for a problem type."""
        if not self.identity.coworkers:
            return None

        problem_lower = problem.lower()

        # Problem → title mapping
        title_map = {
            "research": ["oracle", "researcher"],
            "market": ["oracle", "analyst"],
            "data": ["oracle", "researcher"],
            "design": ["architect"],
            "architecture": ["architect"],
            "system": ["architect"],
            "security": ["architect", "redteam"],
            "code": ["inventor", "developer"],
            "build": ["inventor", "developer"],
            "prototype": ["inventor"],
            "verify": ["skeptic", "reviewer"],
            "review": ["skeptic", "reviewer"],
            "risk": ["governor", "skeptic"],
            "policy": ["governor"],
            "price": ["economist"],
            "cost": ["economist"],
            "economic": ["economist"],
        }

        for keyword, preferred_titles in title_map.items():
            if keyword in problem_lower:
                for title in preferred_titles:
                    for cw in self.identity.coworkers:
                        if title.lower() in cw.title.lower():
                            return cw

        # Fallback: first coworker
        return self.identity.coworkers[0]

    def _route_to_coworker(self, task: str) -> Optional[str]:
        """Suggest a coworker to route to when task is out of scope."""
        cw = self._pick_coworker_for_problem(task)
        return cw.name if cw else None

    def _observe_coworker(self, name: str, observation: str):
        """Record what we learn about a coworker through interaction."""
        if name not in self.coworker_observations:
            self.coworker_observations[name] = []
        self.coworker_observations[name].append(observation)

    def _find_generalizable_skills(self) -> list[str]:
        """Would this help in a completely different mission?"""
        skills = []
        if self.iterations_in_current_task > 5 and self.consultation_count == 0:
            skills.append("independent_execution")
        if self.consultation_count > 0:
            skills.append("collaborative_problem_solving")
        if self.iterations_in_current_task > 10:
            skills.append("complex_task_persistence")
        return skills

    def _read_inbox(self) -> list:
        """Read and return current inbox messages."""
        msgs = list(self.inbox)
        return msgs

    def _default_act_handler(self, task: str) -> str:
        """Default action handler — simulates work output."""
        return f"[{self.identity.name}] Working on task: {task[:80]}... (iteration {self.iterations_in_current_task})"

    def _generate_advice(self, request: ConsultationRequest) -> str:
        """Generate advice based on our identity and expertise."""
        return (
            f"Based on my experience as {self.identity.title}, "
            f"I suggest analyzing the problem from the perspective of '{self.identity.goal}'."
        )

    def _emit(self, phase: str, data: dict):
        """Emit an event to the event store."""
        try:
            self.events.emit(
                EventType(f"employee_{phase}"),
                {"agent": self.identity.name, "phase": phase, **data},
            )
        except Exception:
            pass

    def _save_state(self):
        """Save agent state to disk."""
        try:
            state = {
                "identity": self.identity.to_dict(),
                "learning_summary": self.learning_loop.summary(),
                "coworker_observations": self.coworker_observations,
            }
            (self.storage_dir / "state.json").write_text(json.dumps(state, indent=2, default=str))
        except Exception:
            pass

    def _load_state(self):
        """Load agent state from disk."""
        state_file = self.storage_dir / "state.json"
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text())
                self.coworker_observations = data.get("coworker_observations", {})
            except Exception:
                pass

    def summary(self) -> dict:
        """Return agent summary."""
        return {
            "identity": self.identity.to_dict(),
            "learning": self.learning_loop.summary(),
            "inbox_count": len(self.inbox),
            "outbox_count": len(self.outbox),
            "coworker_observations": {k: len(v) for k, v in self.coworker_observations.items()},
        }


# ──────────────────────────────────────────────
# Team of Employees
# ──────────────────────────────────────────────


class EmployeeTeam:
    """A group of employee agents that can communicate with each other."""

    def __init__(self, name: str):
        self.name = name
        self.agents: dict[str, EmployeeAgent] = {}
        self.message_queue: list[ConsultationRequest | ConsultationResponse] = []

    def add_agent(self, agent: EmployeeAgent):
        self.agents[agent.identity.name] = agent

    def deliver_messages(self):
        """Deliver all pending messages between agents."""
        for agent in self.agents.values():
            for msg in agent.poll_outbox():
                if isinstance(msg, ConsultationRequest):
                    receiver = self.agents.get(msg.receiver_name)
                    if receiver:
                        # Coworker handles the consultation
                        response = receiver.handle_consultation(msg)
                        receiver.inbox.append(msg)
                        agent.inbox.append(response)
                elif isinstance(msg, ConsultationResponse):
                    receiver = self.agents.get(msg.responder_name)
                    if receiver:
                        receiver.inbox.append(msg)

    def run_task_on_agent(self, agent_name: str, task: str) -> dict:
        """Run a task on a specific agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent '{agent_name}' not found"}

        result = agent.run_task(task)

        # Deliver any messages generated during the task
        self.deliver_messages()

        return result

    def summary(self) -> dict:
        return {
            "team": self.name,
            "agents": {name: agent.summary() for name, agent in self.agents.items()},
        }
