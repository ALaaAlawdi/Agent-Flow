"""Dream Mode - Background processing and creative thinking.

While agents are idle, they 'dream' - they:
- Reorganize memories and find hidden patterns
- Generate creative ideas from random combinations
- Predict future issues
- Discover novel solutions
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class Dream:
    """A dream produced during idle processing."""
    
    def __init__(
        self,
        dream_id: str,
        agent_id: str,
        dream_type: str,
        content: str,
        insights: list[str],
        novelty_score: float,
    ):
        self.dream_id = dream_id
        self.agent_id = agent_id
        self.dream_type = dream_type  # "pattern", "innovation", "warning", "connection"
        self.content = content
        self.insights = insights
        self.novelty_score = novelty_score  # 0-1
        self.created_at = datetime.now().isoformat()
        self.validated = False
        self.used = False
    
    def to_dict(self) -> dict:
        return {
            "dream_id": self.dream_id,
            "agent_id": self.agent_id,
            "dream_type": self.dream_type,
            "content": self.content,
            "insights": self.insights,
            "novelty_score": self.novelty_score,
            "created_at": self.created_at,
        }


class DreamEngine:
    """Engine for creative background thinking.
    
    When agents are idle, they enter 'dream mode' where they:
    1. Combine unrelated memories to find patterns
    2. Generate novel solutions
    3. Predict potential problems
    4. Discover unexpected connections
    """
    
    def __init__(self):
        self.dreams: list[Dream] = []
        self.patterns_discovered: list[dict] = []
    
    def dream(
        self,
        agent_id: str,
        memories: list[str],
        current_context: dict = None,
    ) -> Dream:
        """Generate a dream from memories.
        
        Combines random memories to find patterns and insights.
        """
        if len(memories) < 2:
            return None
        
        # Random combination of memories
        sample = random.sample(memories, min(3, len(memories)))
        
        # Generate dream type
        dream_type = random.choice([
            "pattern", "innovation", "warning", "connection"
        ])
        
        # Generate insights based on type
        if dream_type == "pattern":
            insights = self._find_patterns(sample)
            content = f"Pattern detected across {len(sample)} experiences"
        elif dream_type == "innovation":
            insights = self._generate_innovations(sample)
            content = f"Novel idea combining {len(sample)} concepts"
        elif dream_type == "warning":
            insights = self._predict_warnings(sample, current_context)
            content = f"Potential issue predicted"
        else:  # connection
            insights = self._find_connections(sample)
            content = f"Unexpected connection found"
        
        # Calculate novelty
        novelty = random.uniform(0.6, 0.95)
        
        dream_id = f"dream_{agent_id}_{int(datetime.now().timestamp())}"
        
        dream = Dream(
            dream_id=dream_id,
            agent_id=agent_id,
            dream_type=dream_type,
            content=content,
            insights=insights,
            novelty_score=novelty,
        )
        
        self.dreams.append(dream)
        return dream
    
    def _find_patterns(self, memories: list[str]) -> list[str]:
        """Find patterns across memories."""
        patterns = []
        
        # Common words as patterns
        word_count = defaultdict(int)
        for mem in memories:
            for word in mem.lower().split():
                if len(word) > 4:
                    word_count[word] += 1
        
        # Top patterns
        for word, count in sorted(word_count.items(), key=lambda x: -x[1])[:3]:
            if count > 1:
                patterns.append(f"Repeated concept: '{word}'")
        
        if not patterns:
            patterns.append("Emergent behavior detected in recent activities")
        
        return patterns
    
    def _generate_innovations(self, memories: list[str]) -> list[str]:
        """Generate innovative ideas."""
        return [
            f"Combine concepts from: {random.choice(memories)[:50]}",
            "Try parallel execution instead of sequential",
            "Use caching for repeated operations",
            "Automate the manual steps",
        ]
    
    def _predict_warnings(self, memories: list[str], context: dict = None) -> list[str]:
        """Predict potential issues."""
        warnings = [
            "Similar past situation led to failure - be careful",
            "Resource exhaustion possible if current trend continues",
            "Consider edge cases that weren't covered",
        ]
        return warnings[:2]
    
    def _find_connections(self, memories: list[str]) -> list[str]:
        """Find unexpected connections."""
        return [
            f"Memory A relates to Memory B through concept X",
            "Cross-domain insight: similar pattern in different context",
            "Unexpected synergy between previously unrelated areas",
        ]
    
    def get_top_dreams(self, limit: int = 5) -> list[Dream]:
        """Get top dreams by novelty."""
        sorted_dreams = sorted(self.dreams, key=lambda d: -d.novelty_score)
        return sorted_dreams[:limit]
    
    def validate_dream(self, dream_id: str) -> bool:
        """Mark a dream as validated."""
        for dream in self.dreams:
            if dream.dream_id == dream_id:
                dream.validated = True
                return True
        return False