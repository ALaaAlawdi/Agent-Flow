"""Telepathy - Direct mind-to-mind communication between agents.

Features:
- Share mental models instantly
- Empathy transfer
- Collective consciousness moments
- Mind merging for complex problems
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class Thought:
    """A single thought that can be transmitted."""
    
    def __init__(
        self,
        thought_id: str,
        sender: str,
        content: str,
        emotion: str = "neutral",
        intensity: float = 0.5,
        context: dict = None,
    ):
        self.thought_id = thought_id
        self.sender = sender
        self.content = content
        self.emotion = emotion
        self.intensity = intensity
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()
        self.received_by: list[str] = []
        self.understood_by: dict[str, float] = {}  # recipient -> understanding level
    
    def transmit_to(self, recipient: str):
        """Mark thought as transmitted."""
        if recipient not in self.received_by:
            self.received_by.append(recipient)
    
    def understand(self, recipient: str, level: float):
        """Record how well recipient understood."""
        self.understood_by[recipient] = max(0, min(1, level))


class Telepathy:
    """Direct mind-to-mind communication.
    
    Features:
    - Instant thought transmission
    - Empathy transfer
    - Mind merging
    - Collective consciousness
    """
    
    def __init__(self):
        self.thoughts: list[Thought] = []
        self.connections: dict[str, list[str]] = defaultdict(list)  # Network
        self.collective_minds: dict[str, set] = {}  # Merged minds
        self.empathy_strength: dict[tuple, float] = defaultdict(lambda: 0.5)
    
    def connect(self, agent_a: str, agent_b: str, strength: float = 0.5):
        """Create telepathic connection between agents."""
        if agent_b not in self.connections[agent_a]:
            self.connections[agent_a].append(agent_b)
            self.connections[agent_b].append(agent_a)
        self.empathy_strength[(agent_a, agent_b)] = strength
    
    def send_thought(
        self,
        sender: str,
        content: str,
        emotion: str = "neutral",
        intensity: float = 0.5,
        recipients: Optional[list[str]] = None,
    ) -> Thought:
        """Send a thought to connected agents."""
        thought_id = f"thought_{len(self.thoughts)}_{int(datetime.now().timestamp())}"
        
        thought = Thought(
            thought_id=thought_id,
            sender=sender,
            content=content,
            emotion=emotion,
            intensity=intensity,
        )
        
        # Send to connected or specified recipients
        targets = recipients or self.connections.get(sender, [])
        for target in targets:
            thought.transmit_to(target)
        
        self.thoughts.append(thought)
        return thought
    
    def merge_minds(self, agents: list[str], purpose: str) -> str:
        """Merge multiple minds for collective consciousness.
        
        All merged minds share knowledge and work as one.
        """
        merge_id = f"merge_{len(self.collective_minds)}_{int(datetime.now().timestamp())}"
        self.collective_minds[merge_id] = set(agents)
        
        return merge_id
    
    def share_mental_model(
        self,
        owner: str,
        target: str,
        model: dict,
    ) -> float:
        """Share mental model with another agent.
        
        Returns understanding level achieved.
        """
        # Calculate understanding based on empathy
        empathy = self.empathy_strength.get((owner, target), 0.5)
        
        # Number of shared concepts
        owner_keys = set(model.keys())
        understanding = empathy  # Base on empathy
        
        # Boost for complex models
        if len(owner_keys) > 3:
            understanding += 0.1
        
        understanding = min(1.0, understanding)
        
        return understanding
    
    def collective_thinking(
        self,
        agents: list[str],
        question: str,
    ) -> dict:
        """All minds think together on a question.
        
        Each mind contributes its perspective.
        """
        contributions = {}
        
        for agent_id in agents:
            # Each agent contributes based on its specialty
            contribution = {
                "agent": agent_id,
                "perspective": f"From {agent_id}'s view: consider {question}",
                "timestamp": datetime.now().isoformat(),
            }
            contributions[agent_id] = contribution
        
        # Synthesize
        synthesis = {
            "question": question,
            "contributors": list(agents),
            "individual_thoughts": contributions,
            "collective_insight": f"Combined wisdom from {len(agents)} minds",
        }
        
        return synthesis
    
    def empathy_transfer(
        self,
        from_agent: str,
        to_agent: str,
        emotion: str,
        intensity: float,
    ) -> float:
        """Transfer emotional state from one agent to another.
        
        Returns actual intensity transferred (affected by empathy).
        """
        empathy = self.empathy_strength.get((from_agent, to_agent), 0.5)
        transferred = intensity * empathy
        
        return transferred
    
    def get_network(self) -> dict:
        """Get the telepathy network."""
        return {
            "connections": {k: list(v) for k, v in self.connections.items()},
            "collective_minds": len(self.collective_minds),
            "total_thoughts": len(self.thoughts),
        }