"""Dynamic Agent Registry - Tracks active AIAgent instances."""

from __future__ import annotations

from typing import Any, Optional

# Hermes imports
from run_agent import AIAgent


class DynamicAgentRegistry:
    """Registry storing active AIAgent instances.
    
    Tracks which agents are currently running and their configurations.
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self.agents: dict[str, AIAgent] = {}
        self.configs: dict[str, dict] = {}
        self.status: dict[str, str] = {}  # online, busy, offline
    
    def register(
        self,
        agent_id: str,
        agent: AIAgent,
        config: dict[str, Any],
    ) -> None:
        """Register a running agent.
        
        Args:
            agent_id: Unique agent identifier
            agent: Hermes AIAgent instance
            config: Agent configuration dict
        """
        self.agents[agent_id] = agent
        self.configs[agent_id] = config
        self.status[agent_id] = "online"
    
    def get(self, agent_id: str) -> Optional[AIAgent]:
        """Get running agent by ID.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            AIAgent instance or None if not found
        """
        return self.agents.get(agent_id)
    
    def get_config(self, agent_id: str) -> Optional[dict]:
        """Get agent configuration by ID.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Config dict or None if not found
        """
        return self.configs.get(agent_id)
    
    def unregister(self, agent_id: str) -> None:
        """Remove agent from registry.
        
        Args:
            agent_id: Agent identifier
        """
        self.agents.pop(agent_id, None)
        self.configs.pop(agent_id, None)
        self.status.pop(agent_id, None)
    
    def list_agents(self) -> list[dict[str, Any]]:
        """List all registered agents.
        
        Returns:
            List of agent info dicts
        """
        return [
            {
                "id": agent_id,
                "role": self.configs.get(agent_id, {}).get("role", "unknown"),
                "tools": self.configs.get(agent_id, {}).get("tools", []),
                "status": self.status.get(agent_id, "offline"),
            }
            for agent_id in self.agents.keys()
        ]
    
    def find_by_role(self, role: str) -> list[str]:
        """Find agent IDs by role.
        
        Args:
            role: Role to search for
            
        Returns:
            List of matching agent IDs
        """
        return [
            agent_id
            for agent_id, config in self.configs.items()
            if config.get("role") == role
        ]
    
    def find_by_name(self, name: str) -> list[str]:
        """Find agent IDs by name.
        
        Args:
            name: Name to search for
            
        Returns:
            List of matching agent IDs
        """
        return [
            agent_id
            for agent_id, config in self.configs.items()
            if config.get("name") == name
        ]
    
    def set_status(self, agent_id: str, status: str) -> None:
        """Update agent status.
        
        Args:
            agent_id: Agent identifier
            status: New status (online, busy, offline)
        """
        if agent_id in self.agents:
            self.status[agent_id] = status
    
    def get_status(self, agent_id: str) -> Optional[str]:
        """Get agent status.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Status string or None
        """
        return self.status.get(agent_id)
    
    def get_online_agents(self) -> list[str]:
        """Get IDs of all online agents.
        
        Returns:
            List of online agent IDs
        """
        return [
            agent_id
            for agent_id, status in self.status.items()
            if status == "online"
        ]
    
    def clear(self) -> None:
        """Clear all registered agents."""
        self.agents.clear()
        self.configs.clear()
        self.status.clear()
