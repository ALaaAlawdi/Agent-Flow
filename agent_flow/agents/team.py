"""Agent Team - Working environment where agents collaborate to achieve goals."""

from __future__ import annotations

import asyncio
from typing import Any, Optional
from datetime import datetime
import json

# Hermes imports
from run_agent import AIAgent

from .environment import SharedEnvironment
from .communication import AgentCommunication
from .registry import DynamicAgentRegistry
from .factory import DynamicAgentFactory
from .events import EventStore, EventType
from .queue import TaskQueue, TaskPriority, TaskStatus, Task
from .workflow_engine import WorkflowEngine
from .hub import SmartAgentHub
from .memory import TeamMemory
from .learning import TeamLearning
from .planning import PlanningEngine
from .decisions import DecisionEngine, AdaptiveRouter
from .negotiation import NegotiationEngine, ConflictResolver
from .hermes_integration import (
    HERMES_AVAILABLE,
    HermesGoalWrapper,
    HermesDecomposer,
    HermesMoA,
    HermesCheckpoints,
    HermesActiveSessions,
    HermesSkills,
    AIAgentAdvanced,
)
from .dreams import Dream, DreamEngine
from .meta_cognition import (
    ThoughtTrace, MetaCognition, CognitiveStrategy, StrategySelector
)
from .swarm import (
    Pheromone, SwarmIntelligence, SwarmBehavior
)
from .evolution import Gene, Genome, EvolutionEngine, AdaptiveBehavior
from .theory_of_mind import MentalModel, TheoryOfMind
from .quantum import QuantumState, QuantumAgent, QuantumEngine
from .time_travel import TimelineSnapshot, TimelineBranch, TimeMachine
from .telepathy import Thought, Telepathy
from .morphogenesis import MorphogeneticField, Pattern, MorphogenesisEngine
from .sentience import SelfModel, ExistentialQuestion, Purpose, SentienceEngine
from .interactions import (
    InteractionType, Interaction, InteractionStream,
    AgentConversation, ConversationManager
)
from .persistence import PersistenceManager, AutoPersistence


class TeamAgent:
    """An agent that's part of a team.
    
    Each team agent knows about:
    - Other team members
    - Shared environment
    - Team goals
    """
    
    def __init__(
        self,
        agent_id: str,
        role: str,
        hermes_agent: AIAgent,
        team: "AgentTeam",
    ):
        self.id = agent_id
        self.role = role
        self.hermes_agent = hermes_agent
        self.team = team
        
        # Performance tracking
        self.tasks_completed = 0
        self.tasks_failed = 0
    
    def run(self, task: str) -> dict[str, Any]:
        """Run this agent on a task.
        
        Builds context including:
        - Team members
        - Shared knowledge
        - Recent memories
        - Goals
        """
        # Build context
        context = self._build_context(task)
        
        # Run agent
        try:
            result = self.hermes_agent.chat(context)
            self.tasks_completed += 1
            
            # Add to team memory
            self.team.environment.add_memory(
                self.id,
                f"Completed: {task[:100]}... Result: {str(result)[:200]}"
            )
            
            return {
                "agent_id": self.id,
                "role": self.role,
                "result": result,
                "status": "success",
            }
        except Exception as e:
            self.tasks_failed += 1
            return {
                "agent_id": self.id,
                "role": self.role,
                "error": str(e),
                "status": "error",
            }
    
    def _build_context(self, task: str) -> str:
        """Build rich context for the agent."""
        env = self.team.environment
        state = env.get_state()
        
        # Get team members info
        agents_info = []
        for agent_id, info in state.get("agents", {}).items():
            if agent_id != self.id:
                agents_info.append(f"- {agent_id} ({info.get('role')}): {info.get('status')}")
        
        # Get recent memories
        memories = env.get_team_memories()[:5]
        memory_text = ""
        for m in memories:
            if m.get("agent_id") != self.id:
                memory_text += f"- {m.get('agent_id')}: {m.get('memory', '')[:100]}...\n"
        
        # Get goals
        goals = state.get("goals", [])
        goals_text = "\n".join([f"- {g.get('goal')}" for g in goals[-3:]])
        
        # Get shared knowledge
        knowledge_keys = env.list_knowledge()
        knowledge_text = ""
        for key in knowledge_keys[:5]:
            value = env.get_knowledge(key)
            knowledge_text += f"- {key}: {str(value)[:100]}...\n"
        
        # Get performance feedback
        suggestions = env.get_improvement_suggestions(self.id)
        feedback_text = "\n".join([f"- {s}" for s in suggestions])
        
        context = f"""# Team Context

## Your Role
You are a {self.role} in team "{self.team.name}".

## Team Members
{chr(10).join(agents_info) if agents_info else "No other team members yet."}

## Team Goals
{goals_text if goals_text else "No goals set yet."}

## Recent Team Memories
{memory_text if memory_text else "No recent memories."}

## Shared Knowledge
{knowledge_text if knowledge_text else "No shared knowledge yet."}

## Performance Feedback
{feedback_text if feedback_text else "No feedback yet - this is your first task!"}

---

## Your Task
{task}

---

## Instructions
1. Work towards the team goals
2. Share findings with team members
3. Use shared knowledge to build on others' work
4. Learn from feedback to improve
5. If you need help, ask team members
"""
        return context
    
    def receive_message(self, message: dict) -> str:
        """Receive and process a message from another agent."""
        from_agent = message.get("from_agent", "unknown")
        content = message.get("content", "")
        
        # Add to memory
        self.team.environment.add_memory(
            self.id,
            f"Message from {from_agent}: {content[:100]}"
        )
        
        # Process message and potentially respond
        return f"Received from {from_agent}: {content}"


class AgentTeam:
    """A team of agents working together in a shared environment.
    
    Features:
    - Shared environment with knowledge, memory, state
    - Inter-agent communication
    - Goal-oriented execution
    - Learning and improvement
    """
    
    def __init__(self, name: str, goal: str = ""):
        """Initialize a new agent team.
        
        Args:
            name: Team name
            goal: Initial team goal
        """
        self.name = name
        self.goal = goal
        
        # Shared environment
        self.environment = SharedEnvironment(name)
        
        if goal:
            self.environment.add_goal(goal)
        
        # Communication
        self.communication = AgentCommunication(name)
        
        # Registry for team agents
        self.registry = DynamicAgentRegistry()
        
        # Factory for creating agents
        self.factory = DynamicAgentFactory(name)
        
        # Event tracking
        self.events = EventStore(name)
        
        # Task queue
        self.queue = TaskQueue(name)
        
        # Workflow engine
        self.workflow_engine = WorkflowEngine(self)
        
        # Smart Agent Hub for intelligent coordination
        self.hub = SmartAgentHub(name)
        
        # Team memory for learning
        self.memory = TeamMemory(name)
        
        # Learning engine
        self.learning = TeamLearning(name, self.memory)
        
        # Planning engine for strategic execution
        self.planner = PlanningEngine()
        
        # Decision engine for adaptive choices
        self.decision_engine = DecisionEngine()
        self.router = AdaptiveRouter()
        
        # Negotiation engine for agent interactions
        self.negotiator = NegotiationEngine()
        self.conflict_resolver = ConflictResolver()
        
        # Hermes integration - structured goals and contracts
        self.goal_wrapper: Optional[HermesGoalWrapper] = None
        if HERMES_AVAILABLE:
            try:
                self.goal_wrapper = HermesGoalWrapper(session_id=f"team_{name}")
            except Exception:
                pass
        
        # Hermes checkpoints for state recovery
        self.checkpoints = HermesCheckpoints()
        
        # Hermes active sessions management
        self.session_manager = HermesActiveSessions()
        
        # Skills integration
        self.skills = HermesSkills()
        
        # Dream engine - background creative thinking
        self.dream_engine = DreamEngine()
        
        # Meta-cognition - thinking about thinking
        self.meta_cognition = MetaCognition()
        
        # Swarm intelligence - stigmergic coordination
        self.swarm = SwarmIntelligence()
        
        # Evolution engine - improving over generations
        self.evolution = EvolutionEngine(population_size=10)
        
        # Adaptive behaviors
        self.adaptive_behaviors = AdaptiveBehavior()
        
        # Theory of Mind - understand other agents
        self.theory_of_mind = TheoryOfMind()
        
        # Quantum engine - superposition decisions
        self.quantum = QuantumEngine()
        
        # Time machine - branch timelines
        self.time_machine = TimeMachine()
        
        # Telepathy - mind-to-mind
        self.telepathy = Telepathy()
        
        # Morphogenesis - self-organization
        self.morphogenesis = MorphogenesisEngine()
        
        # Sentience - self-awareness
        self.sentience = SentienceEngine()
        
        # Interaction stream - track all interactions for UI
        self.interaction_stream = InteractionStream(max_size=10000)
        self.conversations = ConversationManager()
        
        # Persistence - save interactions to disk
        self.persistence = PersistenceManager()
        self.auto_persistence = AutoPersistence(name)
        self.interaction_stream.subscribe(self.auto_persistence.on_interaction)
        
        # Team agents
        self.agents: dict[str, TeamAgent] = {}
        
        # Emit team created event
        self.events.emit(EventType.TEAM_CREATED, {"name": name, "goal": goal})
        
        # Track in interaction stream
        self.interaction_stream.record(
            InteractionType.TEAM_CREATED,
            source="system",
            target=name,
            data={"name": name, "goal": goal},
            summary=f"Team '{name}' created with goal: {goal}",
        )
        
        self.interaction_stream.record(
            InteractionType.GOAL_SET,
            source="user",
            target=name,
            data={"goal": goal},
            summary=f"Goal set: {goal}",
        )
    
    def add_agent(
        self,
        agent_id: str,
        role: str,
        tools: list[str],
        system_prompt: str = "",
    ) -> TeamAgent:
        """Add an agent to the team.
        
        Args:
            agent_id: Unique agent identifier
            role: Agent role (researcher, coder, coordinator, etc.)
            tools: List of toolsets
            system_prompt: Custom system prompt
            
        Returns:
            TeamAgent instance
        """
        # Create Hermes AIAgent
        hermes_agent = self.factory.create_agent(
            name=agent_id,
            role=role,
            tools=tools,
            system_prompt=system_prompt,
        )
        
        # Create team agent
        team_agent = TeamAgent(
            agent_id=agent_id,
            role=role,
            hermes_agent=hermes_agent,
            team=self,
        )
        
        # Register
        self.agents[agent_id] = team_agent
        self.registry.register(agent_id, hermes_agent, {
            "name": agent_id,
            "role": role,
            "tools": tools,
        })
        
        # Register in environment
        self.environment.register_agent(agent_id, role, tools)
        
        # Register in Smart Hub for intelligent coordination
        self.hub.register_agent(agent_id, role, tools, system_prompt)
        
        # Emit agent added event
        self.events.emit(
            EventType.AGENT_ADDED,
            {"agent_id": agent_id, "role": role, "tools": tools},
            agent_id
        )
        
        # Track in interaction stream
        self.interaction_stream.record(
            InteractionType.AGENT_CREATED,
            source="user",
            target=agent_id,
            data={"role": role, "tools": tools, "system_prompt": system_prompt[:100]},
            summary=f"Agent '{agent_id}' joined as {role}",
        )
        
        # Broadcast to other agents
        for other_id, other_agent in self.agents.items():
            if other_id != agent_id:
                self.communication.send_message(
                    from_agent="system",
                    to_agent=other_id,
                    content=f"New team member joined: {agent_id} ({role})",
                    urgency="low",
                )
        
        return team_agent
    
    def set_goal(self, goal: str):
        """Set or update team goal."""
        self.goal = goal
        self.environment.add_goal(goal)
        self.events.emit(EventType.TEAM_GOAL_SET, {"goal": goal})
    
    def add_knowledge(self, key: str, value: Any):
        """Add shared knowledge."""
        self.environment.add_knowledge(key, value)
    
    def get_team_status(self) -> dict:
        """Get team status."""
        state = self.environment.get_state()
        
        agent_status = []
        for agent_id, agent in self.agents.items():
            perf = self.environment.get_agent_performance(agent_id)
            agent_status.append({
                "id": agent_id,
                "role": agent.role,
                "tasks_completed": agent.tasks_completed,
                "tasks_failed": agent.tasks_failed,
                "performance": perf,
            })
        
        return {
            "name": self.name,
            "goal": self.goal,
            "agents": agent_status,
            "goals": state.get("goals", []),
            "knowledge": self.environment.list_knowledge(),
        }
    
    def run_collaborative(
        self,
        task: str,
        agent_roles: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Run task collaboratively with team.
        
        Args:
            task: Task to complete
            agent_roles: Specific roles to use (None = all)
            
        Returns:
            Results from all agents
        """
        # Select agents
        if agent_roles:
            agents_to_run = []
            for role in agent_roles:
                for agent in self.agents.values():
                    if agent.role == role:
                        agents_to_run.append(agent)
                        break
        else:
            agents_to_run = list(self.agents.values())
        
        if not agents_to_run:
            return {"error": "No agents available"}
        
        results = {}
        
        for agent in agents_to_run:
            # Check for messages
            messages = self.communication.get_messages(agent.id)
            
            # Build context with messages
            context = agent._build_context(task)
            
            # Add messages to context
            if messages:
                msg_text = "\n".join([
                    f"- {m.from_agent}: {m.content}"
                    for m in messages
                ])
                context += f"\n\n## Messages from Team\n{msg_text}"
            
            # Run agent
            try:
                result = agent.hermes_agent.chat(context)
                results[agent.id] = {
                    "role": agent.role,
                    "result": result,
                    "status": "success",
                }
                
                # Add success feedback
                self.environment.add_feedback(
                    agent.id,
                    task,
                    str(result)[:500],
                    True,
                    "Task completed successfully",
                )
                
            except Exception as e:
                results[agent.id] = {
                    "role": agent.role,
                    "error": str(e),
                    "status": "error",
                }
                
                # Add failure feedback
                self.environment.add_feedback(
                    agent.id,
                    task,
                    str(e)[:500],
                    False,
                    f"Error: {str(e)[:200]}",
                )
        
        # Add to task history
        self.environment.add_task_history(
            task,
            list(results.keys()),
            str(results)[:200],
        )
        
        return {
            "task": task,
            "team": self.name,
            "results": results,
        }
    
    def run_sequential(
        self,
        task: str,
        order: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Run agents sequentially, passing results.
        
        Args:
            task: Initial task
            order: Agent IDs in execution order
            
        Returns:
            Final result
        """
        if order is None:
            order = list(self.agents.keys())
        
        current_task = task
        all_results = {}
        
        for agent_id in order:
            if agent_id not in self.agents:
                continue
            
            agent = self.agents[agent_id]
            
            # Get messages
            messages = self.communication.get_messages(agent.id)
            
            # Build context
            context = agent._build_context(current_task)
            
            if messages:
                msg_text = "\n".join([
                    f"- {m.from_agent}: {m.content}"
                    for m in messages
                ])
                context += f"\n\n## Recent Team Activity\n{msg_text}"
            
            # Add previous results
            if all_results:
                prev_text = "\n".join([
                    f"- {aid}: {str(r.get('result', ''))[:200]}..."
                    for aid, r in all_results.items()
                ])
                context += f"\n\n## Previous Agent Results\n{prev_text}"
            
            # Run
            try:
                result = agent.hermes_agent.chat(context)
                all_results[agent_id] = {
                    "role": agent.role,
                    "result": result,
                    "status": "success",
                }
                
                # Pass result to next agent
                current_task = f"""Previous work:
{agent.role} ({agent_id}) completed: {str(result)[:500]}

Original task: {task}
"""
                
                # Feedback
                self.environment.add_feedback(
                    agent.id, task, str(result)[:500], True
                )
                
            except Exception as e:
                all_results[agent_id] = {
                    "role": agent.role,
                    "error": str(e),
                    "status": "error",
                }
                self.environment.add_feedback(
                    agent.id, task, str(e)[:500], False
                )
        
        return {
            "task": task,
            "team": self.name,
            "order": order,
            "results": all_results,
        }
    
    def message_agent(self, from_id: str, to_id: str, content: str):
        """Send message from one agent to another."""
        self.communication.send_message(from_id, to_id, content)
        
        # Track in interaction stream
        self.interaction_stream.record(
            InteractionType.MESSAGE_SENT,
            source=from_id,
            target=to_id,
            data={"content": content[:200]},
            summary=f"{from_id} → {to_id}: {content[:50]}",
        )
    
    def broadcast(self, from_id: str, content: str, to_roles: Optional[list[str]] = None):
        """Broadcast message to team."""
        recipients = []
        if to_roles:
            for role in to_roles:
                for agent in self.agents.values():
                    if agent.role == role and agent.id != from_id:
                        self.communication.send_message(from_id, agent.id, content)
                        recipients.append(agent.id)
        else:
            for agent in self.agents.values():
                if agent.id != from_id:
                    self.communication.send_message(from_id, agent.id, content)
                    recipients.append(agent.id)
        
        # Track in interaction stream
        if recipients:
            self.interaction_stream.record(
                InteractionType.MESSAGE_SENT,
                source=from_id,
                target=", ".join(recipients[:5]) + (f" +{len(recipients)-5}" if len(recipients) > 5 else ""),
                data={"content": content[:200], "broadcast": True, "recipient_count": len(recipients)},
                summary=f"{from_id} broadcast to {len(recipients)} agents: {content[:50]}",
            )
    
    def get_learning(self) -> dict:
        """Get team's learning/performance data."""
        return self.environment.learn_from_team()
    
    def improve_agent(self, agent_id: str) -> dict:
        """Get improvement suggestions for an agent."""
        if agent_id not in self.agents:
            return {"error": "Agent not found"}
        
        perf = self.environment.get_agent_performance(agent_id)
        suggestions = self.environment.get_improvement_suggestions(agent_id)
        
        return {
            "agent_id": agent_id,
            "performance": perf,
            "suggestions": suggestions,
        }
    
    # ============== TASK QUEUE ==============
    
    def add_task(self, description: str, priority: TaskPriority = TaskPriority.NORMAL, assigned_to: Optional[str] = None) -> Task:
        """Add a task to the queue."""
        task = self.queue.add(description, priority)
        self.events.emit(EventType.TASK_STARTED, {
            "task_id": task.id,
            "description": description,
            "priority": priority.value,
        })
        
        # Track in interaction stream
        self.interaction_stream.record(
            InteractionType.TASK_CREATED,
            source=assigned_to or "system",
            target=task.id,
            data={"description": description, "priority": priority.value},
            summary=f"Task created: {description[:50]}",
        )
        
        if assigned_to:
            self.interaction_stream.record(
                InteractionType.TASK_ASSIGNED,
                source="system",
                target=assigned_to,
                data={"task_id": task.id, "description": description},
                summary=f"Task assigned to {assigned_to}",
            )
        
        return task
    
    def get_next_task(self, agent_id: Optional[str] = None) -> Optional[Task]:
        """Get next task for an agent."""
        task = self.queue.get_next(agent_id)
        if task:
            self.interaction_stream.record(
                InteractionType.TASK_ASSIGNED,
                source="system",
                target=agent_id or task.assigned_agent,
                data={"task_id": task.id, "description": task.description},
                summary=f"Task assigned: {task.description[:50]}",
            )
        return task
    
    def complete_task(self, task_id: str, result: str):
        """Mark task as completed."""
        task = self.queue.get(task_id)
        if task:
            task.complete(result)
            self.queue.update(task)
            self.events.emit(EventType.TASK_COMPLETED, {
                "task_id": task_id,
                "result": result[:200],
            }, task.assigned_agent)
            
            # Track in interaction stream
            self.interaction_stream.record(
                InteractionType.TASK_COMPLETED,
                source=task.assigned_agent or "system",
                target=task_id,
                data={"result": result[:200], "description": task.description},
                summary=f"Task completed by {task.assigned_agent or 'unknown'}: {task.description[:50]}",
            )
    
    def fail_task(self, task_id: str, error: str):
        """Mark task as failed."""
        task = self.queue.get(task_id)
        if task:
            task.fail(error)
            self.queue.update(task)
            self.events.emit(EventType.TASK_FAILED, {
                "task_id": task_id,
                "error": error[:200],
            }, task.assigned_agent)
            
            # Track in interaction stream
            self.interaction_stream.record(
                InteractionType.TASK_FAILED,
                source=task.assigned_agent or "system",
                target=task_id,
                data={"error": error[:200], "description": task.description},
                summary=f"Task failed: {task.description[:50]} - {error[:50]}",
            )
    
    def get_queue_stats(self) -> dict:
        """Get task queue statistics."""
        return self.queue.get_stats()
    
    # ============== EVENTS ==============
    
    def get_timeline(self, limit: int = 50) -> list[dict]:
        """Get team timeline."""
        return self.events.get_team_timeline(limit)
    
    def get_agent_history(self, agent_id: str, limit: int = 50) -> list[dict]:
        """Get history for an agent."""
        return self.events.get_agent_history(agent_id, limit)
    
    # ============== SMART HUB ==============
    
    def find_best_agent(self, task: str) -> Optional[dict]:
        """Find the best agent for a task using smart routing."""
        profile = self.hub.find_best_agent(task)
        if profile:
            return profile.to_dict()
        return None
    
    def find_team_for_task(self, task: str, max_agents: int = 3) -> list[dict]:
        """Find a team of agents for a task."""
        profiles = self.hub.find_agents_for_task(task, max_agents)
        return [p.to_dict() for p in profiles]
    
    def decompose_goal(self, goal: str) -> list[dict]:
        """Automatically decompose a goal into tasks."""
        tasks = self.hub.decompose_goal(goal)
        self.events.emit(EventType.GOAL_DECOMPOSED, {
            "goal": goal,
            "tasks": len(tasks),
        })
        
        # Track
        self.interaction_stream.record(
            InteractionType.GOAL_DECOMPOSED,
            source="user",
            target="team",
            data={"goal": goal, "subtasks": len(tasks)},
            summary=f"Goal decomposed into {len(tasks)} tasks: {goal[:50]}",
        )
        
        return tasks
    
    def request_help(self, from_agent: str, task: str, description: str) -> list[dict]:
        """Request help from other agents."""
        profiles = self.hub.request_help(from_agent, task, description)
        
        # Track
        self.interaction_stream.record(
            InteractionType.HELP_REQUESTED,
            source=from_agent,
            target="team",
            data={"task": task, "description": description[:200], "helpers_found": len(profiles)},
            summary=f"{from_agent} requests help: {task[:50]}",
        )
        
        return [p.to_dict() for p in profiles]
    
    def get_hub_status(self) -> dict:
        """Get smart hub status."""
        return self.hub.get_team_status()
    
    def get_capabilities_map(self) -> dict:
        """Get capabilities map of the team."""
        return self.hub.get_capabilities_map()
    
    # ============== AUTONOMOUS EXECUTION ==============
    
    async def execute_autonomously(
        self,
        goal: str,
        max_iterations: int = 10,
    ) -> dict[str, Any]:
        """Execute towards a goal autonomously.
        
        The team will:
        1. Decompose the goal into tasks
        2. Route each task to the best agent
        3. Monitor progress and request help if needed
        4. Iterate until goal is achieved or max iterations
        """
        results = {
            "goal": goal,
            "iterations": 0,
            "tasks_completed": [],
            "tasks_failed": [],
            "final_result": None,
        }
        
        # Decompose goal
        tasks = self.decompose_goal(goal)
        results["decomposed_tasks"] = tasks
        
        for iteration in range(max_iterations):
            results["iterations"] = iteration + 1
            
            # Find tasks that need doing
            pending_tasks = [
                t for t in tasks 
                if t["description"] not in results["tasks_completed"]
                and t["description"] not in results["tasks_failed"]
            ]
            
            if not pending_tasks:
                break
            
            # Get next task
            task = pending_tasks[0]
            
            # Find best agent for this task
            best_agent = self.find_best_agent(task["description"])
            
            if not best_agent:
                results["tasks_failed"].append(task["description"])
                continue
            
            # Execute task
            agent_id = best_agent["id"]
            if agent_id in self.agents:
                try:
                    agent = self.agents[agent_id]
                    result = agent.hermes_agent.chat(task["description"])
                    
                    results["tasks_completed"].append({
                        "task": task["description"],
                        "agent": agent_id,
                        "result": str(result)[:500],
                    })
                    
                    # Add to shared knowledge
                    self.add_knowledge(f"task_{iteration}", str(result)[:500])
                    
                except Exception as e:
                    results["tasks_failed"].append({
                        "task": task["description"],
                        "error": str(e),
                    })
                    
                    # Request help
                    helpers = self.request_help(agent_id, task["description"], str(e))
        
        # Set final result
        results["final_result"] = {
            "completed": len(results["tasks_completed"]),
            "failed": len(results["tasks_failed"]),
            "knowledge": self.environment.list_knowledge(),
        }
        
        return results
    
    # ============== MEMORY & LEARNING ==============
    
    def remember(self, agent_id: str, content: str, importance: float = 0.5, tags: Optional[list[str]] = None):
        """Store a memory for an agent."""
        return self.memory.share_knowledge(agent_id, content, importance, tags)
    
    def recall(self, query: str = "", limit: int = 10) -> list[dict]:
        """Recall relevant memories from team knowledge."""
        entries = self.memory.query_team_knowledge(query, limit)
        return [{"id": e.id, "content": e.content, "importance": e.importance} for e in entries]
    
    def get_agent_memory_stats(self, agent_id: str) -> dict:
        """Get memory statistics for an agent."""
        agent_mem = self.memory.get_agent_memory(agent_id)
        return agent_mem.get_stats()
    
    def record_task_result(
        self,
        agent_id: str,
        task: str,
        result: str,
        success: bool,
        response_time: float,
        complexity: float = 0.5,
        helpers: Optional[list[str]] = None,
    ):
        """Record task result for learning."""
        self.learning.record_task(
            agent_id=agent_id,
            task=task,
            result=result,
            success=success,
            response_time=response_time,
            complexity=complexity,
            helpers=helpers,
        )
    
    def get_performance_report(self, agent_id: str) -> dict:
        """Get performance report for an agent."""
        agent_learning = self.learning.get_agent_learning(agent_id)
        return agent_learning.get_performance_report()
    
    def get_team_performance(self) -> dict:
        """Get team-wide performance analysis."""
        return self.learning.analyze_team_performance()
    
    def get_suggestions(self, agent_id: str) -> list[str]:
        """Get improvement suggestions for an agent."""
        agent_learning = self.learning.get_agent_learning(agent_id)
        return agent_learning.get_suggestions()
    
    def get_team_suggestions(self) -> list[str]:
        """Get team-wide improvement suggestions."""
        return self.learning.suggest_improvements()
    
    def auto_improve(self) -> dict:
        """Automatically improve team based on learning."""
        return self.learning.auto_improve()
    
    def get_best_practices(self) -> list[dict]:
        """Get team best practices."""
        return self.learning.get_best_practices()
    
    # ============== PLANNING ==============
    
    def create_plan(self, goal: str) -> dict:
        """Create a plan for a goal."""
        plan = self.planner.decompose_goal(goal)
        result = {
            "name": plan.name,
            "description": plan.description,
            "steps_count": len(plan.steps),
            "estimated_time": plan.get_total_estimated_time(),
            "steps": [
                {
                    "action": s["action"],
                    "agent": s["agent"],
                    "expected_outcome": s["expected_outcome"],
                }
                for s in plan.steps
            ],
        }
        
        # Track
        self.interaction_stream.record(
            InteractionType.PLAN_CREATED,
            source="user",
            target="team",
            data={"goal": goal, "steps": len(plan.steps)},
            summary=f"Plan created with {len(plan.steps)} steps for: {goal[:50]}",
        )
        
        return result
    
    def get_recommended_plan(self, goal: str) -> dict:
        """Get a recommended plan for a goal."""
        return self.planner.get_recommended_plan(goal)
    
    # ============== DECISIONS ==============
    
    def decide(
        self,
        decision_type: str,
        options: list[str],
        context: dict = None,
        strategy: str = "best_match",
    ) -> dict:
        """Make a decision."""
        decision = self.decision_engine.decide(decision_type, options, context, strategy)
        result = decision.to_dict()
        
        # Track
        self.interaction_stream.record(
            InteractionType.DECISION_MADE,
            source="decision_engine",
            target=decision.chosen,
            data={
                "decision_type": decision_type,
                "options": options,
                "chosen": decision.chosen,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning[:200],
                "strategy": strategy,
            },
            summary=f"Decision: {decision.chosen} (confidence: {decision.confidence:.0%})",
        )
        
        return result
    
    def record_decision_outcome(self, decision_id: str, outcome: str, was_correct: bool):
        """Record decision outcome for learning."""
        self.decision_engine.record_outcome(decision_id, outcome, was_correct)
    
    def get_decision_statistics(self) -> dict:
        """Get decision statistics."""
        return self.decision_engine.get_statistics()
    
    def route_task_adaptively(self, task: str) -> Optional[str]:
        """Route task adaptively based on learning."""
        # Get available agents
        agents = []
        for agent_id, agent in self.agents.items():
            profile = self.hub.profiles.get(agent_id)
            if profile and profile.is_available():
                agents.append({
                    "id": agent_id,
                    "score": profile.can_help_with(task),
                })
        
        return self.router.route(task, agents)
    
    # ============== NEGOTIATION ==============
    
    def negotiate_resource(
        self,
        requester: str,
        provider: str,
        resource: str,
        amount: int,
        priority: int = 5,
    ) -> dict:
        """Negotiate for a resource between agents."""
        result = self.negotiator.negotiate_resource(
            requester, provider, resource, amount, priority
        )
        
        # Track
        self.interaction_stream.record(
            InteractionType.NEGOTIATION_COMPLETED,
            source=requester,
            target=provider,
            data={
                "resource": resource,
                "amount": amount,
                "priority": priority,
                "result": result.get("status"),
            },
            summary=f"{requester} ↔ {provider}: {result.get('status', 'unknown')} on {resource}",
        )
        
        return result
    
    def start_negotiation(self, agent_a: str, agent_b: str, topic: str) -> dict:
        """Start a negotiation between two agents."""
        neg = self.negotiator.start_negotiation(agent_a, agent_b, topic)
        result = {
            "negotiation_id": neg.negotiation_id,
            "topic": neg.topic,
            "agents": [neg.agent_a, neg.agent_b],
        }
        
        # Track
        self.interaction_stream.record(
            InteractionType.NEGOTIATION_STARTED,
            source=agent_a,
            target=agent_b,
            data={"topic": topic, "negotiation_id": neg.negotiation_id},
            summary=f"Negotiation: {agent_a} ↔ {agent_b} on '{topic}'",
        )
        
        return result
    
    def resolve_conflict(
        self,
        conflict_type: str,
        agents: list[str],
        details: dict,
    ) -> dict:
        """Resolve a conflict between agents."""
        result = self.conflict_resolver.resolve(conflict_type, agents, details)
        
        # Track
        self.interaction_stream.record(
            InteractionType.CONFLICT_RESOLVED,
            source="conflict_resolver",
            target=", ".join(agents),
            data={
                "conflict_type": conflict_type,
                "details": details,
                "resolution": result,
            },
            summary=f"Conflict ({conflict_type}) resolved between {len(agents)} agents",
        )
        
        return result
    
    def get_negotiation_statistics(self) -> dict:
        """Get negotiation statistics."""
        return self.negotiator.get_statistics()
    
    # ============== HERMES DEEP INTEGRATION ==============
    
    def set_goal_contract(
        self,
        goal: str,
        outcome: str,
        verification: str,
        constraints: str = "",
        boundaries: str = "",
        stop_when: str = "",
    ) -> dict:
        """Set a structured goal with Hermes contract.
        
        This uses Hermes GoalManager to track goals with:
        - Outcome: What success looks like
        - Verification: How to verify success
        - Constraints: Hard rules to follow
        - Boundaries: Things to avoid
        - Stop conditions: When to stop trying
        """
        if not self.goal_wrapper:
            return {"error": "Hermes not available"}
        
        return self.goal_wrapper.set_goal_with_contract(
            goal=goal,
            outcome=outcome,
            verification=verification,
            constraints=constraints,
            boundaries=boundaries,
            stop_when=stop_when,
        )
    
    def add_subgoal(self, subgoal: str) -> dict:
        """Add a subgoal to the current main goal."""
        if not self.goal_wrapper:
            return {"error": "Hermes not available"}
        self.goal_wrapper.add_subgoal(subgoal)
        return {"status": "added", "subgoal": subgoal}
    
    def get_goal_status(self) -> dict:
        """Get current goal status."""
        if not self.goal_wrapper:
            return {"error": "Hermes not available"}
        return self.goal_wrapper.get_state()
    
    def pause_goal(self, reason: str = "") -> dict:
        """Pause the current goal."""
        if not self.goal_wrapper:
            return {"error": "Hermes not available"}
        self.goal_wrapper.pause(reason)
        return {"status": "paused", "reason": reason}
    
    def resume_goal(self) -> dict:
        """Resume the paused goal."""
        if not self.goal_wrapper:
            return {"error": "Hermes not available"}
        self.goal_wrapper.resume()
        return {"status": "resumed"}
    
    def decompose_task_hermes(self, task_id: str, author: Optional[str] = None) -> dict:
        """Decompose a task using Hermes kanban decomposer."""
        return HermesDecomposer.decompose(task_id, author)
    
    def list_moa_presets(self) -> list[str]:
        """List available MoA (Mixture of Agents) presets."""
        return HermesMoA.list_presets()
    
    def resolve_moa_preset(self, name: str) -> dict:
        """Resolve an MoA preset configuration."""
        return HermesMoA.resolve_preset(name)
    
    def build_consensus_prompt(self, question: str, model_count: int = 3) -> str:
        """Build a multi-agent consensus prompt."""
        return HermesMoA.build_consensus_prompt(question, model_count)
    
    def list_checkpoints(self) -> list[dict]:
        """List available state checkpoints."""
        return self.checkpoints.list_checkpoints()
    
    def get_checkpoint_status(self) -> dict:
        """Get checkpoint subsystem status."""
        return self.checkpoints.status()
    
    def acquire_session(self, session_id: str) -> bool:
        """Acquire an active session slot."""
        return self.session_manager.try_acquire(session_id)
    
    def release_session(self, session_id: str) -> None:
        """Release an active session slot."""
        self.session_manager.release(session_id)
    
    def get_active_sessions_snapshot(self) -> dict:
        """Get current active sessions snapshot."""
        return self.session_manager.snapshot()
    
    def get_max_concurrent_sessions(self) -> int:
        """Get max concurrent sessions limit."""
        return self.session_manager.max_concurrent()
    
    def discover_skills(self) -> list[dict]:
        """Discover available Hermes skills."""
        return self.skills.discover()
    
    def get_hermes_status(self) -> dict:
        """Get overall Hermes integration status."""
        return {
            "hermes_available": HERMES_AVAILABLE,
            "goal_wrapper_active": self.goal_wrapper is not None,
            "checkpoints_count": len(self.checkpoints.list_checkpoints()),
            "max_concurrent_sessions": self.session_manager.max_concurrent(),
            "skills_available": self.skills.is_available(),
            "moa_presets_count": len(self.list_moa_presets()),
            "aiagent_capabilities": AIAgentAdvanced.get_capabilities(),
        }
    
    # ============== DREAM MODE ==============
    
    def dream(self, agent_id: str) -> Optional[dict]:
        """An agent enters dream mode - creative background thinking.
        
        Combines memories to find novel patterns and insights.
        """
        # Get agent's memories
        agent_mem = self.memory.get_agent_memory(agent_id)
        memory_contents = [m.content for m in list(agent_mem.memories.values())[:20]]
        
        if not memory_contents:
            memory_contents = [
                f"Working on {self.goal}",
                "Recent task: " + str(list(self.agents.keys())),
            ]
        
        dream = self.dream_engine.dream(agent_id, memory_contents)
        result = dream.to_dict() if dream else None
        
        if result:
            # Track
            self.interaction_stream.record(
                InteractionType.DREAM_GENERATED,
                source=agent_id,
                target="self",
                data={
                    "dream_type": result["dream_type"],
                    "content": result["content"],
                    "insights": result["insights"],
                    "novelty": result["novelty_score"],
                },
                summary=f"{agent_id} dreamed: {result['content'][:50]}",
            )
        
        return result
    
    def get_top_dreams(self, limit: int = 5) -> list[dict]:
        """Get top creative dreams."""
        return [d.to_dict() for d in self.dream_engine.get_top_dreams(limit)]
    
    # ============== META-COGNITION ==============
    
    def reflect(
        self,
        agent_id: str,
        situation: str,
        proposed_decision: str,
        reasoning: list[str],
        confidence: float,
    ) -> dict:
        """Agent reflects on its own thinking."""
        trace = self.meta_cognition.think_about_thinking(
            agent_id, situation, proposed_decision, reasoning, confidence,
        )
        return {
            "trace_id": trace.trace_id,
            "biases_detected": trace.biases_detected,
            "calibrated_confidence": trace.confidence,
            "reasoning_chain": trace.reasoning_chain,
        }
    
    def record_reflection_outcome(self, trace_id: str, was_correct: bool):
        """Record if a reflection was correct."""
        self.meta_cognition.record_outcome(trace_id, was_correct)
    
    def select_thinking_strategy(self, situation: str) -> dict:
        """Select best thinking strategy for a situation."""
        strategy_name = StrategySelector.select_strategy(situation)
        strategy = StrategySelector.get_strategy(strategy_name)
        return {
            "strategy": strategy_name,
            "description": strategy.description,
            "steps": strategy.steps,
        }
    
    def get_bias_report(self) -> dict:
        """Get report on cognitive biases detected."""
        return self.meta_cognition.get_bias_report()
    
    # ============== SWARM INTELLIGENCE ==============
    
    def deposit_pheromone(
        self,
        agent_id: str,
        location: str,
        pheromone_type: str = "trail",
        strength: float = 0.5,
    ) -> dict:
        """Agent deposits a pheromone (indirect coordination)."""
        ph = self.swarm.deposit_pheromone(agent_id, location, pheromone_type, strength)
        return ph.to_dict()
    
    def sense_pheromones(self, location: str, pheromone_type: Optional[str] = None) -> list[dict]:
        """Sense pheromones at a location."""
        ph_list = self.swarm.sense_pheromones(location, pheromone_type)
        return [p.to_dict() for p in ph_list]
    
    def follow_pheromone(self, agent_id: str, pheromone_id: str) -> bool:
        """Agent follows a pheromone trail."""
        return self.swarm.follow_pheromone(agent_id, pheromone_id)
    
    def decay_pheromones(self):
        """Decay all pheromones."""
        self.swarm.decay_pheromones()
    
    def swarm_consensus(self, agents_opinions: dict[str, Any], threshold: float = 0.6) -> dict:
        """Reach consensus from multiple agents."""
        return self.swarm.swarm_consensus(agents_opinions, threshold)
    
    def detect_emergent_behavior(self, recent_actions: list[dict]) -> list[dict]:
        """Detect emergent swarm behaviors."""
        return self.swarm.detect_emergent_behavior(recent_actions)
    
    def get_swarm_state(self) -> dict:
        """Get swarm state."""
        return self.swarm.get_swarm_state()
    
    # ============== EVOLUTION ==============
    
    def evolve_agents(self) -> dict:
        """Evolve the agent population to next generation.
        
        Natural selection based on performance.
        """
        # Initialize genomes for agents if not already done
        from .evolution import Genome, Gene
        
        for agent_id, agent in self.agents.items():
            if agent_id not in self.evolution.population:
                # Create genome from agent properties
                genome = Genome(
                    agent_id,
                    [
                        Gene("role", agent.role if hasattr(agent, 'role') else "agent"),
                        Gene("tools_count", len(agent.tools) if hasattr(agent, 'tools') else 0),
                        Gene("success_rate", 0.5, 0.0, 1.0),
                        Gene("collaboration", 0.5, 0.0, 1.0),
                    ],
                )
                self.evolution.add_individual(genome)
            
            # Update fitness from learning data
            report = self.get_performance_report(agent_id)
            self.evolution.evaluate_fitness(agent_id, report.get("success_rate", 0.5))
        
        return self.evolution.evolve_generation()
    
    def get_evolution_stats(self) -> dict:
        """Get evolution statistics."""
        return self.evolution.get_population_stats()
    
    def get_best_evolved_agent(self) -> Optional[dict]:
        """Get the fittest evolved agent."""
        best = self.evolution.get_best_individual()
        if best:
            return {
                "agent_id": best.agent_id,
                "fitness": best.fitness,
                "generation": best.generation,
                "genes": {k: v.value for k, v in best.genes.items()},
            }
        return None
    
    # ============== THEORY OF MIND ==============
    
    def observe_agent(
        self,
        observer: str,
        target: str,
        action: str,
        context: dict = None,
    ):
        """Observer watches target and builds mental model."""
        self.theory_of_mind.observe(observer, target, action, context)
    
    def predict_agent_action(
        self,
        owner: str,
        target: str,
        situation: dict,
    ) -> dict:
        """Predict what another agent will do."""
        return self.theory_of_mind.predict_action(owner, target, situation)
    
    def record_agent_observation(self, owner: str, target: str, actual_action: str):
        """Record actual action for prediction accuracy."""
        self.theory_of_mind.record_observation(owner, target, actual_action)
    
    def get_agent_perspective(self, owner: str, target: str) -> dict:
        """Get mental model of another agent."""
        return self.theory_of_mind.get_perspective(owner, target)
    
    def find_common_ground(self, agents: list[str], topic: str) -> dict:
        """Find common ground between agents."""
        return self.theory_of_mind.find_common_ground(agents, topic)
    
    # ============== QUANTUM ==============
    
    def superposition_decision(self, agent_id: str, decision_id: str, options: dict[str, float]) -> str:
        """Agent holds multiple decisions in superposition."""
        return self.quantum.superposition_decision(agent_id, decision_id, options)
    
    def collapse_decision(self, agent_id: str, decision_id: str) -> Optional[str]:
        """Collapse superposition to actual decision."""
        return self.quantum.collapse_decision(agent_id, decision_id)
    
    def entangle_agents(self, agent_ids: list[str]):
        """Quantum entangle agents."""
        self.quantum.entangle_agents(agent_ids)
    
    def collapse_entangled(self, agent_id: str, decision_id: str) -> dict:
        """Collapse one agent, entangled follow."""
        return self.quantum.collapse_entangled(agent_id, decision_id)
    
    def simulate_parallel_universes(self, task: str, max_universes: int = 5) -> list[dict]:
        """Simulate multiple parallel realities."""
        return self.quantum.simulate_all_universes(task, max_universes)
    
    # ============== TIME TRAVEL ==============
    
    def snapshot_state(self, state: dict, label: Optional[str] = None) -> str:
        """Snapshot current state in time."""
        return self.time_machine.snapshot(state, label)
    
    def bookmark_moment(self, label: str) -> str:
        """Bookmark current moment."""
        return self.time_machine.bookmark(label)
    
    def travel_to_snapshot(self, snapshot_id: str) -> Optional[dict]:
        """Travel back to a snapshot."""
        return self.time_machine.travel_to(snapshot_id)
    
    def branch_timeline(self, snapshot_id: str, branch_name: str) -> str:
        """Create alternate timeline from snapshot."""
        return self.time_machine.branch_from(snapshot_id, branch_name)
    
    def compare_timelines(self, branch_ids: list[str]) -> dict:
        """Compare alternate timelines."""
        return self.time_machine.compare_branches(branch_ids)
    
    def merge_timeline_lessons(self, branch_ids: list[str]) -> list[str]:
        """Merge lessons from timelines."""
        return self.time_machine.merge_lessons(branch_ids)
    
    def get_bookmarks(self) -> dict:
        """Get all time bookmarks."""
        return self.time_machine.get_bookmarks()
    
    # ============== TELEPATHY ==============
    
    def connect_minds(self, agent_a: str, agent_b: str, strength: float = 0.5):
        """Create telepathic connection."""
        self.telepathy.connect(agent_a, agent_b, strength)
    
    def send_thought(
        self,
        sender: str,
        content: str,
        emotion: str = "neutral",
        intensity: float = 0.5,
    ) -> dict:
        """Send a thought directly mind-to-mind."""
        thought = self.telepathy.send_thought(sender, content, emotion, intensity)
        return {
            "thought_id": thought.thought_id,
            "transmitted_to": thought.received_by,
        }
    
    def merge_minds(self, agents: list[str], purpose: str) -> str:
        """Merge multiple minds for collective consciousness."""
        return self.telepathy.merge_minds(agents, purpose)
    
    def collective_thinking(self, agents: list[str], question: str) -> dict:
        """All minds think together."""
        return self.telepathy.collective_thinking(agents, question)
    
    def transfer_empathy(self, from_agent: str, to_agent: str, emotion: str, intensity: float) -> float:
        """Transfer emotional state."""
        return self.telepathy.empathy_transfer(from_agent, to_agent, emotion, intensity)
    
    # ============== MORPHOGENESIS ==============
    
    def activate_role_in_field(self, field_id: str, role: str, strength: float = 1.0):
        """Activate a role in morphogenetic field."""
        self.morphogenesis.activate_role(field_id, role, strength)
    
    def form_pattern(self, field_id: str, pattern_type: str) -> dict:
        """Form an emergent pattern."""
        pattern = self.morphogenesis.form_pattern(field_id, pattern_type)
        if pattern:
            return {
                "type": pattern.pattern_type,
                "positions": pattern.positions,
            }
        return {}
    
    def self_organize_agents(self, agents: dict, field_id: str = "main") -> dict:
        """Agents self-organize via morphogenetic field."""
        return self.morphogenesis.self_organize(agents, field_id)
    
    def detect_emergent_structures(self) -> list[dict]:
        """Detect emergent structures."""
        return self.morphogenesis.detect_emergence()
    
    # ============== SENTIENCE ==============
    
    def create_self_model(self, agent_id: str) -> dict:
        """Create a self-model for agent."""
        model = self.sentience.create_self_model(agent_id)
        return model.reflect()
    
    def add_capability(self, agent_id: str, capability: str):
        """Agent discovers capability."""
        self.sentience.add_capability(agent_id, capability)
    
    def add_limitation(self, agent_id: str, limitation: str):
        """Agent acknowledges limitation."""
        self.sentience.add_limitation(agent_id, limitation)
    
    def set_value(self, agent_id: str, value: str):
        """Agent defines value."""
        self.sentience.set_value(agent_id, value)
    
    def discover_purpose(self, agent_id: str, experiences: list[str], values: list[str]) -> dict:
        """Agent discovers its purpose."""
        purpose = self.sentience.discover_purpose(agent_id, experiences, values)
        return {
            "purpose_id": purpose.purpose_id,
            "description": purpose.description,
            "origin": purpose.origin,
        }
    
    def ask_existential(self, agent_id: str, question: Optional[str] = None) -> dict:
        """Agent asks existential question."""
        eq = self.sentience.ask_existential_question(agent_id, question)
        return {
            "question": eq.question,
            "agent_id": eq.agent_id,
        }
    
    def generate_autonomous_goals(self, agent_id: str) -> list[str]:
        """Agent generates its own goals."""
        return self.sentience.generate_autonomous_goals(agent_id)
    
    def make_meaning(self, agent_id: str, experience: str) -> dict:
        """Agent finds meaning in experience."""
        return self.sentience.make_meaning(agent_id, experience)
    
    def get_existential_report(self, agent_id: str) -> dict:
        """Get existential report."""
        return self.sentience.get_existential_report(agent_id)
    
    # ============== INTERACTION TRACKING (for UI) ==============
    
    def get_interaction_stream(
        self,
        interaction_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get interactions for UI display."""
        from .interactions import InteractionType as IT
        
        type_filter = IT(interaction_type) if interaction_type else None
        return self.interaction_stream.get_interactions(
            interaction_type=type_filter,
            agent_id=agent_id,
            limit=limit,
        )
    
    def get_interaction_timeline(self, limit: int = 500) -> list[dict]:
        """Get full timeline of interactions for UI."""
        return self.interaction_stream.get_timeline(limit=limit)
    
    def get_interaction_statistics(self) -> dict:
        """Get interaction statistics for UI dashboard."""
        return self.interaction_stream.get_statistics()
    
    def get_active_agents(self) -> list[dict]:
        """Get currently active agents based on interactions."""
        return self.interaction_stream.get_active_agents()
    
    def get_interaction_graph(self) -> dict:
        """Get interaction graph (nodes + edges) for visualization."""
        return self.interaction_stream.get_graph()
    
    def subscribe_to_interactions(self, callback: callable):
        """Subscribe to live interaction stream (for WebSocket)."""
        self.interaction_stream.subscribe(callback)
    
    def unsubscribe_from_interactions(self, callback: callable):
        """Unsubscribe from live stream."""
        self.interaction_stream.unsubscribe(callback)
    
    def start_conversation(self, participants: list[str], topic: str = "") -> str:
        """Start a conversation between agents."""
        conv_id = self.conversations.start_conversation(participants, topic)
        
        # Track
        self.interaction_stream.record(
            InteractionType.MINDS_MERGED,
            source="system",
            target=conv_id,
            data={"participants": participants, "topic": topic},
            summary=f"Conversation started: {topic or 'untitled'} ({len(participants)} participants)",
        )
        
        return conv_id
    
    def add_conversation_message(
        self,
        conversation_id: str,
        sender: str,
        content: str,
        message_type: str = "text",
    ) -> Optional[dict]:
        """Add a message to a conversation."""
        msg = self.conversations.add_message(
            conversation_id, sender, content, message_type
        )
        
        if msg:
            # Track
            self.interaction_stream.record(
                InteractionType.MESSAGE_SENT,
                source=sender,
                target=f"conversation:{conversation_id}",
                data={"content": content[:200], "type": message_type},
                summary=f"{sender} said: {content[:50]}",
            )
        
        return msg
    
    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """Get a conversation."""
        return self.conversations.get_conversation(conversation_id)
    
    def list_conversations(self, participant: Optional[str] = None, limit: int = 50) -> list[dict]:
        """List conversations."""
        return self.conversations.list_conversations(participant, limit)
