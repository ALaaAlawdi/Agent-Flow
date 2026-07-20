"""Agent Memory - Long-term memory for agents to learn and improve."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str
    content: str
    memory_type: str  # "task", "insight", "pattern", "skill", "preference"
    importance: float  # 0-1
    created_at: str
    accessed_at: str
    access_count: int = 0
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)


class AgentMemory:
    """Long-term memory for agents to learn from experiences.
    
    Features:
    - Persistent storage of experiences
    - Importance-based retention
    - Tag-based retrieval
    - Pattern recognition
    - Skill accumulation
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.memories: dict[str, MemoryEntry] = {}
        self._id_counter = 0
        
        # Statistics
        self.stats = {
            "total_memories": 0,
            "by_type": defaultdict(int),
            "avg_importance": 0.0,
        }
    
    def _generate_id(self) -> str:
        """Generate unique memory ID."""
        self._id_counter += 1
        return f"mem_{self.agent_id}_{self._id_counter}_{int(datetime.now().timestamp())}"
    
    def remember(
        self,
        content: str,
        memory_type: str = "task",
        importance: float = 0.5,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
    ) -> MemoryEntry:
        """Store a memory."""
        now = datetime.now().isoformat()
        
        entry = MemoryEntry(
            id=self._generate_id(),
            content=content,
            memory_type=memory_type,
            importance=importance,
            created_at=now,
            accessed_at=now,
            access_count=0,
            tags=tags or [],
            metadata=metadata or {},
        )
        
        self.memories[entry.id] = entry
        self._update_stats()
        
        return entry
    
    def recall(self, query: str = "", memory_type: Optional[str] = None, limit: int = 10) -> list[MemoryEntry]:
        """Recall relevant memories."""
        results = []
        
        for entry in self.memories.values():
            # Filter by type
            if memory_type and entry.memory_type != memory_type:
                continue
            
            # Score by relevance
            score = 0.0
            if query:
                query_lower = query.lower()
                # Content match
                if query_lower in entry.content.lower():
                    score += 1.0
                # Tag match
                for tag in entry.tags:
                    if query_lower in tag.lower():
                        score += 0.5
                # Importance boost
                score *= (0.5 + entry.importance * 0.5)
            else:
                score = entry.importance * (1.0 + 0.1 * entry.access_count)
            
            if score > 0:
                results.append((score, entry))
        
        # Sort by score
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Update access counts
        for _, entry in results[:limit]:
            entry.access_count += 1
            entry.accessed_at = datetime.now().isoformat()
        
        return [e for _, e in results[:limit]]
    
    def learn_from_task(
        self,
        task: str,
        result: str,
        success: bool,
        insights: Optional[list[str]] = None,
    ):
        """Learn from a task execution."""
        # Remember the task
        self.remember(
            content=f"Task: {task}\nResult: {result[:500]}",
            memory_type="task",
            importance=0.8 if success else 0.9,
            tags=["task", "success" if success else "failure"],
            metadata={"success": success},
        )
        
        # Remember insights
        if insights:
            for insight in insights:
                self.remember(
                    content=insight,
                    memory_type="insight",
                    importance=0.7,
                    tags=["insight"],
                )
        
        # If failed, remember the failure more strongly
        if not success:
            self.remember(
                content=f"Failed task: {task}\nError: {result[:300]}",
                memory_type="pattern",
                importance=0.95,
                tags=["failure", "lesson"],
                metadata={"task": task, "learned": True},
            )
    
    def extract_skills(self) -> list[dict]:
        """Extract learned skills from memory."""
        skills = []
        
        for entry in self.memories.values():
            if entry.memory_type in ("skill", "insight"):
                skills.append({
                    "content": entry.content,
                    "importance": entry.importance,
                    "tags": entry.tags,
                })
        
        return skills
    
    def get_patterns(self) -> list[dict]:
        """Get recurring patterns from memory."""
        patterns = []
        
        # Group by tags
        tag_groups = defaultdict(list)
        for entry in self.memories.values():
            for tag in entry.tags:
                tag_groups[tag].append(entry)
        
        # Find frequent patterns
        for tag, entries in tag_groups.items():
            if len(entries) >= 2:
                patterns.append({
                    "pattern": tag,
                    "occurrences": len(entries),
                    "avg_importance": sum(e.importance for e in entries) / len(entries),
                })
        
        return patterns
    
    def _update_stats(self):
        """Update memory statistics."""
        self.stats["total_memories"] = len(self.memories)
        
        # Count by type
        type_counts = defaultdict(int)
        total_importance = 0.0
        
        for entry in self.memories.values():
            type_counts[entry.memory_type] += 1
            total_importance += entry.importance
        
        self.stats["by_type"] = dict(type_counts)
        
        if self.memories:
            self.stats["avg_importance"] = total_importance / len(self.memories)
    
    def get_stats(self) -> dict:
        """Get memory statistics."""
        self._update_stats()
        return dict(self.stats)
    
    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "agent_id": self.agent_id,
            "memories": [e.to_dict() for e in self.memories.values()],
            "stats": self.get_stats(),
        }


class TeamMemory:
    """Shared memory for the entire team.
    
    Allows agents to share knowledge and learn collectively.
    """
    
    def __init__(self, team_name: str):
        self.team_name = team_name
        self.agent_memories: dict[str, AgentMemory] = {}
        self.shared_knowledge: dict[str, MemoryEntry] = {}
        
        # Team-level patterns
        self.team_patterns: list[dict] = []
    
    def get_agent_memory(self, agent_id: str) -> AgentMemory:
        """Get or create memory for an agent."""
        if agent_id not in self.agent_memories:
            self.agent_memories[agent_id] = AgentMemory(agent_id)
        return self.agent_memories[agent_id]
    
    def share_knowledge(
        self,
        agent_id: str,
        content: str,
        importance: float = 0.6,
        tags: Optional[list[str]] = None,
    ):
        """Share knowledge with the team."""
        entry = self.get_agent_memory(agent_id).remember(
            content=content,
            memory_type="skill",
            importance=importance,
            tags=tags or ["shared"],
        )
        
        # Also add to shared knowledge
        self.shared_knowledge[entry.id] = entry
        
        return entry
    
    def query_team_knowledge(
        self,
        query: str,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """Query team-wide knowledge."""
        results = []
        
        for entry in self.shared_knowledge.values():
            if query.lower() in entry.content.lower():
                results.append(entry)
        
        results.sort(key=lambda e: e.importance, reverse=True)
        return results[:limit]
    
    def get_team_insights(self) -> dict:
        """Get aggregated team insights."""
        all_patterns = []
        
        for agent_memory in self.agent_memories.values():
            all_patterns.extend(agent_memory.get_patterns())
        
        return {
            "total_shared_knowledge": len(self.shared_knowledge),
            "agent_count": len(self.agent_memories),
            "patterns": all_patterns,
        }
