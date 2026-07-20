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
        
        # Team agents
        self.agents: dict[str, TeamAgent] = {}
        
        # Emit team created event
        self.events.emit(EventType.TEAM_CREATED, {"name": name, "goal": goal})
    
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
    
    def broadcast(self, from_id: str, content: str, to_roles: Optional[list[str]] = None):
        """Broadcast message to team."""
        if to_roles:
            for role in to_roles:
                for agent in self.agents.values():
                    if agent.role == role and agent.id != from_id:
                        self.communication.send_message(from_id, agent.id, content)
        else:
            for agent in self.agents.values():
                if agent.id != from_id:
                    self.communication.send_message(from_id, agent.id, content)
    
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
    
    def add_task(self, description: str, priority: TaskPriority = TaskPriority.NORMAL) -> Task:
        """Add a task to the queue."""
        task = self.queue.add(description, priority)
        self.events.emit(EventType.TASK_STARTED, {
            "task_id": task.id,
            "description": description,
            "priority": priority.value,
        })
        return task
    
    def get_next_task(self, agent_id: Optional[str] = None) -> Optional[Task]:
        """Get next task for an agent."""
        return self.queue.get_next(agent_id)
    
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
        return tasks
    
    def request_help(self, from_agent: str, task: str, description: str) -> list[dict]:
        """Request help from other agents."""
        profiles = self.hub.request_help(from_agent, task, description)
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
