"""Smart Agent Hub - Intelligent agent coordination and self-organization."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Optional
from collections import defaultdict

from .events import EventStore, EventType


class Capability:
    """Agent capability."""
    
    def __init__(self, name: str, description: str = "", keywords: list[str] = None):
        self.name = name
        self.description = description
        self.keywords = keywords or []
    
    def matches(self, query: str) -> float:
        """Check if this capability matches a query."""
        query_lower = query.lower()
        score = 0.0
        
        # Exact name match
        if self.name.lower() in query_lower:
            score += 1.0
        
        # Description match
        if self.description:
            for word in self.description.lower().split():
                if word in query_lower:
                    score += 0.3
        
        # Keyword match
        for kw in self.keywords:
            if kw.lower() in query_lower:
                score += 0.5
        
        return score


class AgentProfile:
    """Profile of an agent with capabilities and preferences."""
    
    # Predefined capabilities registry
    CAPABILITIES = {
        "web": Capability("web", "Web browsing and search", ["search", "browse", "fetch", "http"]),
        "terminal": Capability("terminal", "Command line and shell", ["bash", "shell", "cmd", "exec"]),
        "file": Capability("file", "File operations", ["read", "write", "edit", "file"]),
        "code": Capability("code", "Programming and coding", ["code", "program", "develop", "debug"]),
        "research": Capability("research", "Research and analysis", ["research", "analyze", "study", "investigate"]),
        "write": Capability("write", "Writing and documentation", ["write", "document", "draft", "edit"]),
        "review": Capability("review", "Code and document review", ["review", "check", "audit", "inspect"]),
        "test": Capability("test", "Testing and QA", ["test", "qa", "validate", "verify"]),
        "deploy": Capability("deploy", "Deployment and DevOps", ["deploy", "release", "infrastructure", "ci/cd"]),
        "coordinate": Capability("coordinate", "Coordination and planning", ["plan", "organize", "coordinate", "manage"]),
    }
    
    def __init__(
        self,
        agent_id: str,
        role: str,
        tools: list[str],
        system_prompt: str = "",
    ):
        self.id = agent_id
        self.role = role
        self.tools = tools
        self.system_prompt = system_prompt
        
        # Capabilities derived from tools and role
        self.capabilities: list[Capability] = []
        self._derive_capabilities()
        
        # Performance history
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.avg_response_time = 0.0
        self.success_rate = 0.0
        
        # Workload
        self.current_task: Optional[str] = None
        self.busy_until: Optional[str] = None
        
        # Preferences
        self.prefers_tasks = []  # Task types they prefer
        self.avoids_tasks = []   # Task types they avoid
    
    def _derive_capabilities(self):
        """Derive capabilities from tools and role."""
        # Map tools to capabilities
        tool_to_cap = {
            "web": "web",
            "terminal": "terminal", 
            "file": "file",
        }
        
        for tool in self.tools:
            cap_name = tool_to_cap.get(tool, tool)
            if cap_name in self.CAPABILITIES:
                self.capabilities.append(self.CAPABILITIES[cap_name])
        
        # Add role-based capability
        if self.role in self.CAPABILITIES:
            self.capabilities.append(self.CAPABILITIES[self.role])
        
        # Add role as capability
        self.capabilities.append(Capability(
            self.role, 
            f"Specializes in {self.role}",
            [self.role]
        ))
    
    def can_help_with(self, query: str) -> float:
        """Check if this agent can help with a query."""
        if not self.capabilities:
            return 0.0
        
        max_score = 0.0
        for cap in self.capabilities:
            score = cap.matches(query)
            max_score = max(max_score, score)
        
        return max_score
    
    def is_available(self) -> bool:
        """Check if agent is available."""
        if self.current_task:
            # Check if still busy
            if self.busy_until:
                try:
                    busy_time = datetime.fromisoformat(self.busy_until)
                    if datetime.now() < busy_time:
                        return False
                except:
                    pass
        return True
    
    def mark_busy(self, task: str, duration_minutes: int = 30):
        """Mark agent as busy."""
        from datetime import timedelta
        self.current_task = task
        self.busy_until = (datetime.now() + timedelta(minutes=duration_minutes)).isoformat()
    
    def mark_free(self):
        """Mark agent as free."""
        self.current_task = None
        self.busy_until = None
    
    def update_performance(self, success: bool, response_time: float):
        """Update performance metrics."""
        # Update counts
        if success:
            self.tasks_completed += 1
        else:
            self.tasks_failed += 1
        
        # Update success rate
        total = self.tasks_completed + self.tasks_failed
        if total > 0:
            self.success_rate = self.tasks_completed / total
        
        # Update avg response time (exponential moving average)
        if self.avg_response_time == 0:
            self.avg_response_time = response_time
        else:
            self.avg_response_time = 0.7 * self.avg_response_time + 0.3 * response_time
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "tools": self.tools,
            "capabilities": [c.name for c in self.capabilities],
            "is_available": self.is_available(),
            "current_task": self.current_task,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "success_rate": round(self.success_rate, 2),
            "avg_response_time": round(self.avg_response_time, 2),
        }


class SmartAgentHub:
    """Intelligent hub for agent coordination and self-organization.
    
    Features:
    - Auto-discovery of agent capabilities
    - Smart task routing based on capabilities and availability
    - Proactive help when agents struggle
    - Goal decomposition into tasks
    - Agent-to-agent negotiation
    """
    
    def __init__(self, team_name: str):
        self.team_name = team_name
        self.profiles: dict[str, AgentProfile] = {}
        self.events = EventStore(team_name)
        
        # Task routing history
        self.task_history: list[dict] = []
        
        # Pending requests for help
        self.help_requests: dict[str, dict] = {}
    
    def register_agent(
        self,
        agent_id: str,
        role: str,
        tools: list[str],
        system_prompt: str = "",
    ) -> AgentProfile:
        """Register an agent in the hub."""
        profile = AgentProfile(agent_id, role, tools, system_prompt)
        self.profiles[agent_id] = profile
        
        # Emit event
        self.events.emit(
            EventType.AGENT_REGISTERED,
            {"agent_id": agent_id, "role": role, "capabilities": [c.name for c in profile.capabilities]}
        )
        
        return profile
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent."""
        if agent_id in self.profiles:
            del self.profiles[agent_id]
            self.events.emit(
                EventType.AGENT_UNREGISTERED,
                {"agent_id": agent_id}
            )
    
    def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        """Get agent profile."""
        return self.profiles.get(agent_id)
    
    def find_best_agent(
        self,
        task_query: str,
        exclude_busy: bool = True,
    ) -> Optional[AgentProfile]:
        """Find the best agent for a task based on capabilities."""
        candidates = []
        
        for agent_id, profile in self.profiles.items():
            # Skip busy agents if requested
            if exclude_busy and not profile.is_available():
                continue
            
            # Calculate match score
            score = profile.can_help_with(task_query)
            
            # Boost score for availability
            if profile.is_available():
                score *= 1.5
            
            # Boost score for success rate
            score *= (0.5 + profile.success_rate * 0.5)
            
            if score > 0:
                candidates.append((score, profile))
        
        if not candidates:
            return None
        
        # Return highest scoring agent
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    
    def find_agents_for_task(
        self,
        task_query: str,
        max_agents: int = 3,
    ) -> list[AgentProfile]:
        """Find multiple agents that can work on a task."""
        agents = []
        
        for agent_id, profile in self.profiles.items():
            score = profile.can_help_with(task_query)
            if score > 0:
                agents.append((score, profile))
        
        # Sort by score
        agents.sort(key=lambda x: x[0], reverse=True)
        
        return [a for _, a in agents[:max_agents]]
    
    def route_task(
        self,
        task: str,
        preferred_roles: Optional[list[str]] = None,
    ) -> Optional[AgentProfile]:
        """Intelligently route a task to the best agent."""
        # First try to find by preferred roles
        if preferred_roles:
            for role in preferred_roles:
                for profile in self.profiles.values():
                    if profile.role == role and profile.is_available():
                        # Emit routing event
                        self.events.emit(
                            EventType.TASK_ROUTED,
                            {
                                "task": task[:100],
                                "agent_id": profile.id,
                                "role": profile.role,
                            }
                        )
                        return profile
        
        # Otherwise use smart routing
        best = self.find_best_agent(task)
        
        if best:
            self.events.emit(
                EventType.TASK_ROUTED,
                {
                    "task": task[:100],
                    "agent_id": best.id,
                    "role": best.role,
                }
            )
        
        return best
    
    def request_help(
        self,
        from_agent: str,
        task: str,
        description: str,
    ) -> list[AgentProfile]:
        """Request help from other agents."""
        request_id = f"help_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.help_requests[request_id] = {
            "id": request_id,
            "from_agent": from_agent,
            "task": task,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }
        
        # Find agents that can help
        helpers = self.find_agents_for_task(description)
        
        # Emit help request event
        self.events.emit(
            EventType.HELP_REQUESTED,
            {
                "request_id": request_id,
                "from_agent": from_agent,
                "helpers_found": len(helpers),
            }
        )
        
        return [h for h in helpers if h.id != from_agent]
    
    def offer_help(
        self,
        from_agent: str,
        to_agent: str,
        task: str,
    ) -> bool:
        """Proactively offer help to another agent."""
        # Check if help is needed
        target = self.profiles.get(to_agent)
        if not target:
            return False
        
        # Emit help offer event
        self.events.emit(
            EventType.HELP_OFFERED,
            {
                "from_agent": from_agent,
                "to_agent": to_agent,
                "task": task,
            }
        )
        
        return True
    
    def decompose_goal(self, goal: str) -> list[dict]:
        """Automatically decompose a goal into tasks.
        
        This is a simple heuristic-based decomposition.
        For production, this could use an LLM.
        """
        tasks = []
        
        # Simple keyword-based decomposition
        goal_lower = goal.lower()
        
        # Research task
        if any(w in goal_lower for w in ["بحث", "research", "find", "discover", "learn"]):
            tasks.append({
                "type": "research",
                "description": f"Research: {goal}",
                "required_capabilities": ["research", "web"],
            })
        
        # Code task
        if any(w in goal_lower for w in ["build", "code", "implement", "create", "write", "برمج", "ابنِ"]):
            tasks.append({
                "type": "code",
                "description": f"Implement: {goal}",
                "required_capabilities": ["code", "terminal"],
            })
        
        # Review task
        if any(w in goal_lower for w in ["review", "check", "validate", "مراجعة"]):
            tasks.append({
                "type": "review",
                "description": f"Review: {goal}",
                "required_capabilities": ["review", "code"],
            })
        
        # Test task
        if any(w in goal_lower for w in ["test", "testify", "اختبر"]):
            tasks.append({
                "type": "test",
                "description": f"Test: {goal}",
                "required_capabilities": ["test", "code"],
            })
        
        # Document task
        if any(w in goal_lower for w in ["document", "write", "docs", "توثيق"]):
            tasks.append({
                "type": "document",
                "description": f"Document: {goal}",
                "required_capabilities": ["write"],
            })
        
        # Deploy task
        if any(w in goal_lower for w in ["deploy", "release", "نشر"]):
            tasks.append({
                "type": "deploy",
                "description": f"Deploy: {goal}",
                "required_capabilities": ["deploy", "terminal"],
            })
        
        # If no specific tasks identified, create a general task
        if not tasks:
            tasks.append({
                "type": "general",
                "description": goal,
                "required_capabilities": [],
            })
        
        return tasks
    
    def get_team_status(self) -> dict:
        """Get team status including all agents."""
        agents = []
        
        for agent_id, profile in self.profiles.items():
            agents.append(profile.to_dict())
        
        return {
            "team_name": self.team_name,
            "total_agents": len(agents),
            "available_agents": len([a for a in agents if a["is_available"]]),
            "agents": agents,
        }
    
    def get_capabilities_map(self) -> dict:
        """Get map of all capabilities in the team."""
        cap_map = defaultdict(list)
        
        for agent_id, profile in self.profiles.items():
            for cap in profile.capabilities:
                cap_map[cap.name].append(agent_id)
        
        return dict(cap_map)
