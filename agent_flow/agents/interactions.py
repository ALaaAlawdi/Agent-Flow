"""Interaction Tracking - Track every interaction for UI display.

Captures:
- Agent-to-agent messages
- Task executions
- Decisions made
- Conflicts and resolutions
- Memory accesses
- Learning events
- Dreams, quanta, timelines
- Performance metrics
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from collections import defaultdict
from enum import Enum


class InteractionType(str, Enum):
    """Types of agent interactions."""
    # Core
    AGENT_CREATED = "agent_created"
    AGENT_REGISTERED = "agent_registered"
    AGENT_UNREGISTERED = "agent_unregistered"
    
    # Communication
    MESSAGE_SENT = "message_sent"
    HELP_REQUESTED = "help_requested"
    HELP_OFFERED = "help_offered"
    THOUGHT_TRANSMITTED = "thought_transmitted"
    MINDS_MERGED = "minds_merged"
    
    # Tasks
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    # Reasoning
    DECISION_MADE = "decision_made"
    PLAN_CREATED = "plan_created"
    GOAL_DECOMPOSED = "goal_decomposed"
    CAUSAL_REASONING = "causal_reasoning"
    
    # Memory & Learning
    MEMORY_STORED = "memory_stored"
    MEMORY_RECALLED = "memory_recalled"
    INSIGHT_GAINED = "insight_gained"
    LESSON_LEARNED = "lesson_learned"
    
    # Conflicts
    NEGOTIATION_STARTED = "negotiation_started"
    NEGOTIATION_COMPLETED = "negotiation_completed"
    CONFLICT_RESOLVED = "conflict_resolved"
    
    # Swarm
    PHEROMONE_DEPOSITED = "pheromone_deposited"
    PHEROMONE_FOLLOWED = "pheromone_followed"
    SWARM_CONSENSUS = "swarm_consensus"
    EMERGENT_BEHAVIOR = "emergent_behavior"
    
    # Creative
    NOVEL_CONCEPT = "novel_concept"
    BRAINSTORM = "brainstorm"
    HYPOTHESIS = "hypothesis"
    
    # Predictions
    TREND_DETECTED = "trend_detected"
    FORECAST_MADE = "forecast_made"
    ANOMALY_DETECTED = "anomaly_detected"
    
    # Emotional
    EMOTION_DETECTED = "emotion_detected"
    EMPATHY_SHOWN = "empathy_shown"
    THERAPY_PROVIDED = "therapy_provided"
    
    # Quantum
    SUPERPOSITION = "superposition"
    COLLAPSE = "collapse"
    ENTANGLEMENT = "entanglement"
    
    # Time
    SNAPSHOT = "snapshot"
    BRANCH = "branch"
    BOOKMARK = "bookmark"
    TIME_TRAVEL = "time_travel"
    
    # Sentience
    SELF_MODEL = "self_model"
    PURPOSE_DISCOVERED = "purpose_discovered"
    EXISTENTIAL_QUESTION = "existential_question"
    AUTONOMOUS_GOAL = "autonomous_goal"
    MEANING_MADE = "meaning_made"
    
    # Evolution
    MUTATION = "mutation"
    CROSSOVER = "crossover"
    NATURAL_SELECTION = "natural_selection"
    SPECIATION = "speciation"
    
    # Dreams
    DREAM_GENERATED = "dream_generated"
    INSIGHT_FROM_DREAM = "insight_from_dream"
    
    # Meta
    REFLECTION = "reflection"
    BIAS_DETECTED = "bias_detected"
    STRATEGY_SELECTED = "strategy_selected"
    
    # Performance
    PERFORMANCE_RECORDED = "performance_recorded"
    SUGGESTION_GENERATED = "suggestion_generated"
    AUTO_IMPROVEMENT = "auto_improvement"
    
    # System
    TEAM_CREATED = "team_created"
    GOAL_SET = "goal_set"


class Interaction:
    """A single interaction in the system."""
    
    def __init__(
        self,
        interaction_id: str,
        interaction_type: InteractionType,
        source: Optional[str] = None,  # Who/what initiated
        target: Optional[str] = None,  # Who/what was affected
        data: dict = None,
        summary: str = "",
        metadata: dict = None,
    ):
        self.interaction_id = interaction_id
        self.interaction_type = interaction_type
        self.source = source
        self.target = target
        self.data = data or {}
        self.summary = summary
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "interaction_id": self.interaction_id,
            "type": self.interaction_type.value,
            "source": self.source,
            "target": self.target,
            "data": self.data,
            "summary": self.summary,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class InteractionStream:
    """Real-time stream of all interactions.
    
    Used for UI display to show what agents are doing.
    """
    
    def __init__(self, max_size: int = 10000):
        self.interactions: list[Interaction] = []
        self.max_size = max_size
        self.subscribers: list[callable] = []  # WebSocket subscribers
        
        # Indexes for fast querying
        self.by_type: dict[str, list[Interaction]] = defaultdict(list)
        self.by_agent: dict[str, list[Interaction]] = defaultdict(list)
        self.by_time: list[Interaction] = []
        
        # Statistics
        self.stats = {
            "total": 0,
            "by_type": defaultdict(int),
            "by_agent": defaultdict(int),
        }
    
    def record(
        self,
        interaction_type: InteractionType,
        source: Optional[str] = None,
        target: Optional[str] = None,
        data: dict = None,
        summary: str = "",
        metadata: dict = None,
    ) -> Interaction:
        """Record a new interaction."""
        interaction_id = f"int_{len(self.interactions)}_{int(datetime.now().timestamp() * 1000)}"
        
        interaction = Interaction(
            interaction_id=interaction_id,
            interaction_type=interaction_type,
            source=source,
            target=target,
            data=data or {},
            summary=summary,
            metadata=metadata or {},
        )
        
        # Add to stream
        self.interactions.append(interaction)
        
        # Maintain max size
        if len(self.interactions) > self.max_size:
            removed = self.interactions.pop(0)
            self._remove_from_indexes(removed)
        
        # Update indexes
        self.by_type[interaction_type.value].append(interaction)
        self.by_time.append(interaction)
        
        if source:
            self.by_agent[source].append(interaction)
            self.stats["by_agent"][source] += 1
        
        if target and target != source:
            self.by_agent[target].append(interaction)
            self.stats["by_agent"][target] += 1
        
        # Update stats
        self.stats["total"] += 1
        self.stats["by_type"][interaction_type.value] += 1
        
        # Notify subscribers (for WebSocket)
        self._notify(interaction)
        
        return interaction
    
    def _remove_from_indexes(self, interaction: Interaction):
        """Remove interaction from indexes."""
        try:
            self.by_type[interaction.interaction_type.value].remove(interaction)
            self.by_time.remove(interaction)
            if interaction.source and interaction in self.by_agent[interaction.source]:
                self.by_agent[interaction.source].remove(interaction)
            if interaction.target and interaction.target != interaction.source:
                if interaction in self.by_agent[interaction.target]:
                    self.by_agent[interaction.target].remove(interaction)
        except (ValueError, KeyError):
            pass
    
    def subscribe(self, callback: callable):
        """Subscribe to live interaction stream (for WebSocket)."""
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback: callable):
        """Unsubscribe from stream."""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def _notify(self, interaction: Interaction):
        """Notify all subscribers of new interaction."""
        for callback in self.subscribers:
            try:
                callback(interaction.to_dict())
            except Exception:
                pass
    
    def get_interactions(
        self,
        interaction_type: Optional[InteractionType] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
        since: Optional[str] = None,
    ) -> list[dict]:
        """Get interactions with filters."""
        
        # Choose source
        if agent_id:
            candidates = self.by_agent.get(agent_id, [])
        elif interaction_type:
            candidates = self.by_type.get(interaction_type.value, [])
        else:
            candidates = self.interactions
        
        # Apply since filter
        if since:
            candidates = [i for i in candidates if i.timestamp >= since]
        
        # Sort by time (newest first)
        candidates = sorted(candidates, key=lambda i: i.timestamp, reverse=True)
        
        # Limit
        return [i.to_dict() for i in candidates[:limit]]
    
    def get_timeline(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 500,
    ) -> list[dict]:
        """Get full timeline of interactions."""
        candidates = self.interactions
        
        if start_time:
            candidates = [i for i in candidates if i.timestamp >= start_time]
        if end_time:
            candidates = [i for i in candidates if i.timestamp <= end_time]
        
        # Sort by time (oldest first for timeline)
        candidates = sorted(candidates, key=lambda i: i.timestamp)
        
        return [i.to_dict() for i in candidates[:limit]]
    
    def get_statistics(self) -> dict:
        """Get interaction statistics."""
        return {
            "total_interactions": self.stats["total"],
            "by_type": dict(self.stats["by_type"]),
            "by_agent": dict(self.stats["by_agent"]),
            "unique_types": len(self.stats["by_type"]),
            "unique_agents": len(self.stats["by_agent"]),
            "current_size": len(self.interactions),
            "max_size": self.max_size,
        }
    
    def get_active_agents(self) -> list[dict]:
        """Get currently active agents based on recent interactions."""
        recent = self.get_interactions(limit=200)
        
        agent_activity = defaultdict(int)
        for i in recent:
            if i["source"]:
                agent_activity[i["source"]] += 1
            if i["target"]:
                agent_activity[i["target"]] += 1
        
        return [
            {"agent_id": agent_id, "interactions": count}
            for agent_id, count in sorted(
                agent_activity.items(),
                key=lambda x: -x[1],
            )
        ]
    
    def get_graph(self) -> dict:
        """Get interaction graph for visualization.
        
        Returns nodes (agents) and edges (interactions between them).
        """
        nodes = set()
        edges = []
        edge_count = defaultdict(int)
        
        for interaction in self.interactions:
            if interaction.source:
                nodes.add(interaction.source)
            if interaction.target:
                nodes.add(interaction.target)
            
            if interaction.source and interaction.target:
                edge_key = (interaction.source, interaction.target)
                edge_count[edge_key] += 1
        
        for (source, target), count in edge_count.items():
            edges.append({
                "source": source,
                "target": target,
                "weight": count,
                "type": "interaction",
            })
        
        return {
            "nodes": [{"id": n, "type": "agent"} for n in nodes],
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }
    
    def clear(self):
        """Clear all interactions."""
        self.interactions.clear()
        self.by_type.clear()
        self.by_agent.clear()
        self.by_time.clear()
        self.stats = {
            "total": 0,
            "by_type": defaultdict(int),
            "by_agent": defaultdict(int),
        }


class AgentConversation:
    """A conversation between multiple agents."""
    
    def __init__(self, conversation_id: str, participants: list[str], topic: str = ""):
        self.conversation_id = conversation_id
        self.participants = participants
        self.topic = topic
        self.messages: list[dict] = []
        self.started_at = datetime.now().isoformat()
        self.last_activity = self.started_at
        self.status = "active"
    
    def add_message(
        self,
        sender: str,
        content: str,
        message_type: str = "text",
        metadata: dict = None,
    ) -> dict:
        """Add a message to the conversation."""
        if sender not in self.participants:
            self.participants.append(sender)
        
        message = {
            "sender": sender,
            "content": content,
            "type": message_type,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        
        self.messages.append(message)
        self.last_activity = message["timestamp"]
        
        return message
    
    def to_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "participants": self.participants,
            "topic": self.topic,
            "messages": self.messages,
            "message_count": len(self.messages),
            "started_at": self.started_at,
            "last_activity": self.last_activity,
            "status": self.status,
        }


class ConversationManager:
    """Manages all conversations between agents."""
    
    def __init__(self):
        self.conversations: dict[str, AgentConversation] = {}
        self.by_participant: dict[str, list[str]] = defaultdict(list)
    
    def start_conversation(
        self,
        participants: list[str],
        topic: str = "",
    ) -> str:
        """Start a new conversation."""
        conv_id = f"conv_{len(self.conversations)}_{int(datetime.now().timestamp())}"
        
        conversation = AgentConversation(conv_id, participants, topic)
        self.conversations[conv_id] = conversation
        
        for participant in participants:
            self.by_participant[participant].append(conv_id)
        
        return conv_id
    
    def add_message(
        self,
        conversation_id: str,
        sender: str,
        content: str,
        message_type: str = "text",
        metadata: dict = None,
    ) -> Optional[dict]:
        """Add a message to an existing conversation."""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return None
        
        return conversation.add_message(sender, content, message_type, metadata)
    
    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """Get conversation by ID."""
        conversation = self.conversations.get(conversation_id)
        if conversation:
            return conversation.to_dict()
        return None
    
    def list_conversations(
        self,
        participant: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """List conversations, optionally filtered by participant."""
        if participant:
            conv_ids = self.by_participant.get(participant, [])
            candidates = [self.conversations[cid] for cid in conv_ids if cid in self.conversations]
        else:
            candidates = list(self.conversations.values())
        
        # Sort by last activity
        candidates.sort(key=lambda c: c.last_activity, reverse=True)
        
        return [c.to_dict() for c in candidates[:limit]]