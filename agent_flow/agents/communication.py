"""Agent Communication - Message broker for inter-agent messaging."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Hermes imports
from hermes_cli.profiles import get_profile_dir


class AgentMessage:
    """Represents a message between agents."""
    
    def __init__(
        self,
        msg_id: str,
        from_agent: str,
        to_agent: str,
        content: str,
        timestamp: str,
        urgency: str = "normal",
    ):
        self.id = msg_id
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.content = content
        self.timestamp = timestamp
        self.urgency = urgency
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "from": self.from_agent,
            "to": self.to_agent,
            "content": self.content,
            "timestamp": self.timestamp,
            "urgency": self.urgency,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentMessage:
        return cls(
            msg_id=data.get("id", str(uuid.uuid4())),
            from_agent=data["from"],
            to_agent=data["to"],
            content=data["content"],
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            urgency=data.get("urgency", "normal"),
        )


class AgentCommunication:
    """Message broker using Hermes profile storage.
    
    Allows agents to send messages to each other using
    Hermes profile directory as storage backend.
    """
    
    def __init__(self, network_name: str = "default"):
        """Initialize communication broker.
        
        Args:
            network_name: Name of the network (for storage isolation)
        """
        self.network_name = network_name
        # get_profile_dir requires 'name' argument
        self.profile_dir = get_profile_dir(network_name) / "networks" / network_name
        self.messages_dir = self.profile_dir / "messages"
        self.messages_dir.mkdir(parents=True, exist_ok=True)
    
    def send_message(
        self,
        from_agent: str,
        to_agent: str,
        content: str,
        urgency: str = "normal",
    ) -> str:
        """Send message from one agent to another.
        
        Args:
            from_agent: Sender agent ID
            to_agent: Receiver agent ID
            content: Message content
            urgency: Message urgency (low, normal, high, critical)
            
        Returns:
            Message ID
        """
        msg = AgentMessage(
            msg_id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            timestamp=datetime.now().isoformat(),
            urgency=urgency,
        )
        
        # Append to receiver's message file
        msg_file = self.messages_dir / f"{to_agent}.jsonl"
        with open(msg_file, "a") as f:
            f.write(json.dumps(msg.to_dict()) + "\n")
        
        return msg.id
    
    def get_messages(self, agent_id: str, clear: bool = True) -> list[AgentMessage]:
        """Get pending messages for an agent.
        
        Args:
            agent_id: Agent to get messages for
            clear: Whether to clear messages after reading
            
        Returns:
            List of messages
        """
        msg_file = self.messages_dir / f"{agent_id}.jsonl"
        if not msg_file.exists():
            return []
        
        messages = []
        with open(msg_file) as f:
            for line in f:
                if line.strip():
                    messages.append(AgentMessage.from_dict(json.loads(line)))
        
        # Clear messages after reading (by default)
        if clear:
            msg_file.unlink()
        
        return messages
    
    def peek_messages(self, agent_id: str) -> list[AgentMessage]:
        """Peek at messages without clearing.
        
        Args:
            agent_id: Agent to peek messages for
            
        Returns:
            List of messages
        """
        msg_file = self.messages_dir / f"{agent_id}.jsonl"
        if not msg_file.exists():
            return []
        
        messages = []
        with open(msg_file) as f:
            for line in f:
                if line.strip():
                    messages.append(AgentMessage.from_dict(json.loads(line)))
        
        return messages
    
    def broadcast(
        self,
        from_agent: str,
        content: str,
        to_agents: list[str],
        urgency: str = "normal",
    ) -> list[str]:
        """Broadcast message to multiple agents.
        
        Args:
            from_agent: Sender agent ID
            content: Message content
            to_agents: List of receiver agent IDs
            urgency: Message urgency
            
        Returns:
            List of message IDs
        """
        msg_ids = []
        for to_agent in to_agents:
            msg_id = self.send_message(from_agent, to_agent, content, urgency)
            msg_ids.append(msg_id)
        return msg_ids
    
    def broadcast_to_role(
        self,
        from_agent: str,
        content: str,
        to_roles: list[str],
        registry: "DynamicAgentRegistry",
        urgency: str = "normal",
    ) -> list[str]:
        """Broadcast message to all agents with given roles.
        
        Args:
            from_agent: Sender agent ID
            content: Message content
            to_roles: List of role names
            registry: Registry to look up agents by role
            urgency: Message urgency
            
        Returns:
            List of message IDs
        """
        to_agents = []
        for role in to_roles:
            agents = registry.find_by_role(role)
            to_agents.extend(agents)
        
        return self.broadcast(from_agent, content, to_agents, urgency)
    
    def clear_messages(self, agent_id: str) -> None:
        """Clear all messages for an agent.
        
        Args:
            agent_id: Agent ID
        """
        msg_file = self.messages_dir / f"{agent_id}.jsonl"
        if msg_file.exists():
            msg_file.unlink()
    
    def get_message_count(self, agent_id: str) -> int:
        """Get count of pending messages.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Number of pending messages
        """
        messages = self.peek_messages(agent_id)
        return len(messages)
