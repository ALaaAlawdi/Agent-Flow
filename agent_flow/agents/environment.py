"""Shared Environment - Common workspace for all agents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

from hermes_cli.profiles import get_profile_dir


class SharedEnvironment:
    """Shared environment where all agents work together.
    
    Features:
    - Shared knowledge base
    - Common memory
    - Team state
    - Learning/feedback system
    """
    
    def __init__(self, team_name: str):
        """Initialize shared environment for a team.
        
        Args:
            team_name: Name of the team/workspace
        """
        self.team_name = team_name
        # Use Hermes profile directory
        self.profile_dir = get_profile_dir(team_name)
        self.env_dir = self.profile_dir / "environment"
        self.env_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories
        self.knowledge_dir = self.env_dir / "knowledge"
        self.memory_dir = self.env_dir / "memory"
        self.state_dir = self.env_dir / "state"
        self.feedback_dir = self.env_dir / "feedback"
        
        for d in [self.knowledge_dir, self.memory_dir, self.state_dir, self.feedback_dir]:
            d.mkdir(exist_ok=True)
        
        # Initialize team state
        self._init_state()
    
    def _init_state(self):
        """Initialize team state if not exists."""
        state_file = self.state_dir / "team.json"
        if not state_file.exists():
            state = {
                "team_name": self.team_name,
                "created_at": datetime.now().isoformat(),
                "agents": {},
                "goals": [],
                "shared_context": {},
                "task_history": [],
            }
            state_file.write_text(json.dumps(state, indent=2))
    
    # ============== KNOWLEDGE ==============
    
    def add_knowledge(self, key: str, value: Any):
        """Add to shared knowledge base.
        
        Args:
            key: Knowledge key
            value: Knowledge value
        """
        knowledge_file = self.knowledge_dir / f"{key}.json"
        data = {
            "key": key,
            "value": value,
            "updated_at": datetime.now().isoformat(),
            "updated_by": "system",
        }
        knowledge_file.write_text(json.dumps(data, indent=2))
    
    def get_knowledge(self, key: str) -> Optional[Any]:
        """Get from shared knowledge base."""
        knowledge_file = self.knowledge_dir / f"{key}.json"
        if knowledge_file.exists():
            return json.loads(knowledge_file.read_text()).get("value")
        return None
    
    def list_knowledge(self) -> list[str]:
        """List all knowledge keys."""
        return [f.stem for f in self.knowledge_dir.glob("*.json")]
    
    # ============== MEMORY ==============
    
    def add_memory(self, agent_id: str, memory: str):
        """Add memory from an agent.
        
        Args:
            agent_id: Agent who created this memory
            memory: Memory content
        """
        memory_file = self.memory_dir / f"{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        data = {
            "agent_id": agent_id,
            "memory": memory,
            "timestamp": datetime.now().isoformat(),
        }
        memory_file.write_text(json.dumps(data, indent=2))
    
    def get_team_memories(self) -> list[dict]:
        """Get all team memories."""
        memories = []
        for f in self.memory_dir.glob("*.json"):
            memories.append(json.loads(f.read_text()))
        return sorted(memories, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # ============== STATE ==============
    
    def get_state(self) -> dict:
        """Get current team state."""
        state_file = self.state_dir / "team.json"
        if state_file.exists():
            return json.loads(state_file.read_text())
        return {}
    
    def update_state(self, updates: dict):
        """Update team state."""
        state = self.get_state()
        state.update(updates)
        state_file = self.state_dir / "team.json"
        state_file.write_text(json.dumps(state, indent=2))
    
    def register_agent(self, agent_id: str, role: str, capabilities: list):
        """Register an agent in team state."""
        state = self.get_state()
        state["agents"][agent_id] = {
            "role": role,
            "capabilities": capabilities,
            "registered_at": datetime.now().isoformat(),
            "status": "active",
        }
        self.update_state(state)
    
    def update_agent_status(self, agent_id: str, status: str):
        """Update agent status."""
        state = self.get_state()
        if agent_id in state["agents"]:
            state["agents"][agent_id]["status"] = status
            state["agents"][agent_id]["last_updated"] = datetime.now().isoformat()
            self.update_state(state)
    
    def add_goal(self, goal: str):
        """Add a team goal."""
        state = self.get_state()
        state["goals"].append({
            "goal": goal,
            "added_at": datetime.now().isoformat(),
            "status": "active",
        })
        self.update_state(state)
    
    def set_shared_context(self, key: str, value: Any):
        """Set shared context."""
        state = self.get_state()
        state["shared_context"][key] = value
        self.update_state(state)
    
    # ============== FEEDBACK / LEARNING ==============
    
    def add_feedback(self, agent_id: str, task: str, result: str, success: bool, notes: str = ""):
        """Add feedback for an agent's work.
        
        Args:
            agent_id: Agent ID
            task: What they tried to do
            result: What happened
            success: Whether it succeeded
            notes: Additional notes
        """
        feedback_file = self.feedback_dir / f"{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        data = {
            "agent_id": agent_id,
            "task": task,
            "result": result,
            "success": success,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }
        feedback_file.write_text(json.dumps(data, indent=2))
        
        # Update agent's success rate
        self._update_agent_performance(agent_id)
    
    def _update_agent_performance(self, agent_id: str):
        """Calculate agent performance from feedback."""
        feedback_files = list(self.feedback_dir.glob(f"{agent_id}_*.json"))
        
        total = len(feedback_files)
        if total == 0:
            return
        
        successful = 0
        for f in feedback_files:
            data = json.loads(f.read_text())
            if data.get("success"):
                successful += 1
        
        success_rate = successful / total
        
        # Save performance
        perf_file = self.feedback_dir / f"{agent_id}_performance.json"
        perf_file.write_text(json.dumps({
            "agent_id": agent_id,
            "success_rate": success_rate,
            "total_tasks": total,
            "successful_tasks": successful,
            "last_updated": datetime.now().isoformat(),
        }, indent=2))
    
    def get_agent_performance(self, agent_id: str) -> dict:
        """Get agent performance metrics."""
        perf_file = self.feedback_dir / f"{agent_id}_performance.json"
        if perf_file.exists():
            return json.loads(perf_file.read_text())
        return {"agent_id": agent_id, "success_rate": 0.0, "total_tasks": 0}
    
    def get_improvement_suggestions(self, agent_id: str) -> list[str]:
        """Get improvement suggestions based on feedback."""
        feedback_files = list(self.feedback_dir.glob(f"{agent_id}_*.json"))
        
        if len(feedback_files) < 3:
            return ["Need more tasks to generate suggestions"]
        
        suggestions = []
        
        # Analyze failures
        failures = []
        for f in feedback_files[-10:]:  # Last 10
            data = json.loads(f.read_text())
            if not data.get("success"):
                failures.append(data)
        
        if failures:
            suggestions.append(f"Consider improving on {len(failures)} recent failures")
        
        # Get performance
        perf = self.get_agent_performance(agent_id)
        if perf.get("success_rate", 0) < 0.7:
            suggestions.append("Success rate below 70% - consider reviewing approach")
        
        return suggestions if suggestions else ["Good performance - keep it up!"]
    
    def learn_from_team(self) -> dict:
        """Learn from team's collective experience."""
        # Get all agents' performance
        agents = self.get_state().get("agents", {})
        
        learnings = {}
        for agent_id in agents:
            perf = self.get_agent_performance(agent_id)
            suggestions = self.get_improvement_suggestions(agent_id)
            learnings[agent_id] = {
                "performance": perf,
                "suggestions": suggestions,
            }
        
        return learnings
    
    # ============== TASK HISTORY ==============
    
    def add_task_history(self, task: str, agents_used: list, result: str):
        """Add completed task to history."""
        state = self.get_state()
        state["task_history"].append({
            "task": task,
            "agents": agents_used,
            "result_summary": result[:200] if len(result) > 200 else result,
            "completed_at": datetime.now().isoformat(),
        })
        # Keep last 50 tasks
        state["task_history"] = state["task_history"][-50:]
        self.update_state(state)
