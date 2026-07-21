"""
Conversation Tracker — Records every agent interaction in the world.

Tracks:
- Who talked to whom
- What they said
- Relationships that form
- Topics discussed
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Conversation:
    """A recorded conversation between two or more agents."""
    conversation_id: str
    participants: list[str]
    participant_names: dict[str, str]
    messages: list[dict] = field(default_factory=list)
    started_at: float = 0.0
    ended_at: Optional[float] = None
    topics: list[str] = field(default_factory=list)
    outcome: Optional[str] = None  # became_friends, formed_company, shared_info, etc.

    def duration(self) -> float:
        end = self.ended_at or time.time()
        return round(end - self.started_at, 1)


@dataclass
class Relationship:
    """Relationship between two agents — evolves over time."""
    agent_a: str
    agent_b: str
    type: str = "acquaintance"  # acquaintance, friend, rival, collaborator, leader_follower
    strength: float = 0.1  # 0-1, grows with positive interactions
    interactions: int = 0
    conversations: int = 0
    last_talk: float = 0.0
    topics_discussed: list[str] = field(default_factory=list)


class ConversationTracker:
    """Tracks every conversation between agents in the world."""

    def __init__(self):
        self.conversations: list[Conversation] = []
        self.relationships: dict[tuple[str, str], Relationship] = {}
        self.active_conversations: dict[str, Conversation] = {}  # agent_pair -> conversation

    def start_conversation(self, speaker: str, listener: str, names: dict[str, str], first_message: str) -> Conversation:
        """Start tracking a new conversation."""
        pair = tuple(sorted([speaker, listener]))
        conv_id = f"conv_{int(time.time() * 1000)}_{speaker[:4]}_{listener[:4]}"

        conv = Conversation(
            conversation_id=conv_id,
            participants=[speaker, listener],
            participant_names=names,
            started_at=time.time(),
            topics=self._extract_topics(first_message),
        )

        conv.messages.append({
            "from": speaker,
            "content": first_message,
            "timestamp": time.time(),
        })

        self.conversations.append(conv)
        self.active_conversations[pair] = conv

        # Update or create relationship
        self._update_relationship(speaker, listener, first_message)

        return conv

    def add_message(self, speaker: str, listener: str, content: str):
        """Add a message to an ongoing conversation."""
        pair = tuple(sorted([speaker, listener]))
        conv = self.active_conversations.get(pair)

        if conv:
            conv.messages.append({
                "from": speaker,
                "content": content,
                "timestamp": time.time(),
            })
            topics = self._extract_topics(content)
            for t in topics:
                if t not in conv.topics:
                    conv.topics.append(t)

        # Update relationship
        self._update_relationship(speaker, listener, content)

    def end_conversation(self, speaker: str, listener: str, outcome: Optional[str] = None):
        """End a tracked conversation."""
        pair = tuple(sorted([speaker, listener]))
        conv = self.active_conversations.pop(pair, None)
        if conv:
            conv.ended_at = time.time()
            if outcome:
                conv.outcome = outcome

    def _update_relationship(self, agent_a: str, agent_b: str, message: str):
        """Update relationship between two agents based on interaction."""
        if agent_a == agent_b:
            return

        pair = tuple(sorted([agent_a, agent_b]))

        if pair not in self.relationships:
            self.relationships[pair] = Relationship(
                agent_a=pair[0],
                agent_b=pair[1],
            )

        rel = self.relationships[pair]
        rel.interactions += 1
        rel.last_talk = time.time()

        # Determine relationship type based on interaction patterns
        positive_words = ["thanks", "help", "great", "nice", "together", "friend", "good", "love"]
        negative_words = ["no", "stop", "bad", "wrong", "never", "hate"]

        if any(w in message.lower() for w in positive_words):
            rel.strength = min(1.0, rel.strength + 0.05)
        elif any(w in message.lower() for w in negative_words):
            rel.strength = max(0, rel.strength - 0.05)

        # Evolve relationship type
        if rel.strength > 0.7 and rel.interactions > 10:
            rel.type = "friend"
        elif rel.strength > 0.5 and rel.interactions > 5:
            rel.type = "collaborator"
        elif rel.strength < 0.2 and rel.interactions > 3:
            rel.type = "rival"
        elif rel.interactions > 3:
            rel.type = "acquaintance"

        # Extract topics
        topics = self._extract_topics(message)
        for t in topics:
            if t not in rel.topics_discussed:
                rel.topics_discussed.append(t)

    def _extract_topics(self, text: str) -> list[str]:
        """Extract topics from text."""
        topic_keywords = {
            "work": "work",
            "build": "building",
            "code": "coding",
            "research": "research",
            "help": "collaboration",
            "team": "teamwork",
            "company": "company",
            "explore": "exploration",
            "learn": "learning",
            "skill": "skills",
            "idea": "ideas",
            "project": "projects",
        }
        return [v for k, v in topic_keywords.items() if k in text.lower()]

    def get_network_stats(self) -> dict:
        """Get stats about the conversation network."""
        if not self.relationships:
            return {"total_conversations": 0, "total_relationships": 0, "avg_strength": 0}

        return {
            "total_conversations": len(self.conversations),
            "total_relationships": len(self.relationships),
            "avg_strength": round(sum(r.strength for r in self.relationships.values()) / len(self.relationships), 2),
            "friends": sum(1 for r in self.relationships.values() if r.type == "friend"),
            "collaborators": sum(1 for r in self.relationships.values() if r.type == "collaborator"),
            "rivals": sum(1 for r in self.relationships.values() if r.type == "rival"),
        }

    def get_agent_network(self, agent_id: str) -> list[dict]:
        """Get all relationships for a specific agent."""
        return [
            {
                "with": r.agent_b if r.agent_a == agent_id else r.agent_a,
                "type": r.type,
                "strength": round(r.strength, 2),
                "interactions": r.interactions,
                "topics": r.topics_discussed,
            }
            for r in self.relationships.values()
            if r.agent_a == agent_id or r.agent_b == agent_id
        ]


# Global conversation tracker
conversation_tracker = ConversationTracker()