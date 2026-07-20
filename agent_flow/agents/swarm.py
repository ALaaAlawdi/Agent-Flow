"""Swarm Intelligence - Collective intelligence from agent interactions.

Features:
- Stigmergy (indirect coordination through environment)
- Swarm consensus without central control
- Emergent behavior detection
- Collective problem solving
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class Pheromone:
    """Digital pheromone for stigmergic coordination.
    
    Like ants leaving pheromones, agents leave traces that
    influence other agents' behavior.
    """
    
    def __init__(
        self,
        pheromone_id: str,
        location: str,  # Where in the environment
        type: str,  # "trail", "warning", "opportunity", "danger"
        strength: float,  # 0-1
        deposited_by: str,
        ttl: int = 100,  # Time to live in ticks
    ):
        self.pheromone_id = pheromone_id
        self.location = location
        self.type = type
        self.strength = strength
        self.deposited_by = deposited_by
        self.created_at = datetime.now().isoformat()
        self.ttl = ttl
        self.age = 0
        self.followers: list[str] = []  # Agents who followed this pheromone
    
    def decay(self, amount: float = 0.05) -> bool:
        """Decay pheromone. Returns False if expired."""
        self.age += 1
        self.strength = max(0, self.strength - amount)
        return self.strength > 0 and self.age < self.ttl
    
    def reinforce(self, amount: float = 0.1):
        """Reinforce pheromone (when others follow it)."""
        self.strength = min(1.0, self.strength + amount)
        self.age = 0  # Reset age
    
    def to_dict(self) -> dict:
        return {
            "pheromone_id": self.pheromone_id,
            "location": self.location,
            "type": self.type,
            "strength": self.strength,
            "deposited_by": self.deposited_by,
            "followers_count": len(self.followers),
            "age": self.age,
        }


class SwarmBehavior:
    """A swarm behavior pattern."""
    
    FLOCKING = "flocking"      # Move together
    FORAGING = "foraging"      # Search for resources
    DEFENDING = "defending"    # Protect territory
    BUILDING = "building"      # Collective construction
    EXPLORING = "exploring"    # Scout new areas
    CONSENSUS = "consensus"    # Collective decision


class SwarmIntelligence:
    """Swarm intelligence system.
    
    Features:
    - Stigmergic coordination via digital pheromones
    - Emergent behavior detection
    - Collective decision-making
    - Swarm consensus
    """
    
    def __init__(self):
        self.pheromones: dict[str, Pheromone] = {}
        self.swarm_state: dict[str, Any] = {}
        self.behavior_log: list[dict] = []
        self.consensus_history: list[dict] = []
    
    def deposit_pheromone(
        self,
        agent_id: str,
        location: str,
        pheromone_type: str = "trail",
        strength: float = 0.5,
    ) -> Pheromone:
        """Agent deposits a pheromone at a location."""
        p_id = f"pher_{len(self.pheromones)}_{int(datetime.now().timestamp())}"
        
        pheromone = Pheromone(
            pheromone_id=p_id,
            location=location,
            type=pheromone_type,
            strength=strength,
            deposited_by=agent_id,
        )
        
        self.pheromones[p_id] = pheromone
        return pheromone
    
    def sense_pheromones(
        self,
        location: str,
        pheromone_type: Optional[str] = None,
    ) -> list[Pheromone]:
        """Agent senses pheromones at a location."""
        sensed = []
        
        for ph in self.pheromones.values():
            if ph.location == location:
                if pheromone_type is None or ph.type == pheromone_type:
                    sensed.append(ph)
        
        # Sort by strength
        sensed.sort(key=lambda p: -p.strength)
        return sensed
    
    def follow_pheromone(self, agent_id: str, pheromone_id: str) -> bool:
        """Agent follows a pheromone."""
        if pheromone_id not in self.pheromones:
            return False
        
        ph = self.pheromones[pheromone_id]
        if agent_id not in ph.followers:
            ph.followers.append(agent_id)
            ph.reinforce(0.1)
            return True
        return False
    
    def decay_pheromones(self):
        """Decay all pheromones (called periodically)."""
        expired = []
        
        for p_id, ph in self.pheromones.items():
            if not ph.decay():
                expired.append(p_id)
        
        for p_id in expired:
            del self.pheromones[p_id]
    
    def detect_emergent_behavior(self, recent_actions: list[dict]) -> list[dict]:
        """Detect emergent behavior patterns."""
        behaviors = []
        
        if len(recent_actions) < 3:
            return behaviors
        
        # Pattern: Many agents at same location
        location_count = defaultdict(int)
        for action in recent_actions:
            loc = action.get("location")
            if loc:
                location_count[loc] += 1
        
        for loc, count in location_count.items():
            if count >= 3:
                behaviors.append({
                    "type": "convergence",
                    "location": loc,
                    "agent_count": count,
                    "description": f"{count} agents converging on {loc}",
                })
        
        # Pattern: Coordinated timing
        timestamps = [a.get("timestamp") for a in recent_actions if a.get("timestamp")]
        if len(timestamps) >= 3:
            behaviors.append({
                "type": "synchronization",
                "description": "Agents acting in coordinated timing",
            })
        
        return behaviors
    
    def swarm_consensus(
        self,
        agents_opinions: dict[str, Any],
        threshold: float = 0.6,
    ) -> dict:
        """Reach consensus from multiple agents' opinions.
        
        Args:
            agents_opinions: {agent_id: opinion}
            threshold: Agreement threshold (0-1)
        
        Returns:
            Consensus result
        """
        if not agents_opinions:
            return {"consensus": None, "agreement": 0}
        
        # Count opinions
        opinion_count = defaultdict(int)
        for opinion in agents_opinions.values():
            opinion_count[str(opinion)] += 1
        
        total = len(agents_opinions)
        top_opinion, top_count = max(opinion_count.items(), key=lambda x: x[1])
        agreement = top_count / total
        
        consensus_id = f"consensus_{int(datetime.now().timestamp())}"
        
        result = {
            "consensus_id": consensus_id,
            "consensus": top_opinion if agreement >= threshold else None,
            "agreement": agreement,
            "total_agents": total,
            "agreeing": top_count,
            "disagreeing": total - top_count,
            "threshold_met": agreement >= threshold,
            "all_opinions": dict(opinion_count),
        }
        
        self.consensus_history.append(result)
        return result
    
    def flocking_step(
        self,
        agents: dict[str, dict],
    ) -> dict[str, dict]:
        """Apply flocking rules (separation, alignment, cohesion).
        
        Each agent adjusts based on neighbors.
        """
        new_positions = {}
        
        for agent_id, agent in agents.items():
            neighbors = [
                a for aid, a in agents.items()
                if aid != agent_id
            ]
            
            if not neighbors:
                new_positions[agent_id] = agent
                continue
            
            # Cohesion: move toward center of neighbors
            center_x = sum(a.get("x", 0) for a in neighbors) / len(neighbors)
            center_y = sum(a.get("y", 0) for a in neighbors) / len(neighbors)
            
            # Alignment: match average velocity
            avg_vx = sum(a.get("vx", 0) for a in neighbors) / len(neighbors)
            avg_vy = sum(a.get("vy", 0) for a in neighbors) / len(neighbors)
            
            # Separation: avoid being too close
            separation_x = 0
            separation_y = 0
            for n in neighbors:
                dx = agent.get("x", 0) - n.get("x", 0)
                dy = agent.get("y", 0) - n.get("y", 0)
                dist = max(0.1, (dx**2 + dy**2) ** 0.5)
                if dist < 2:  # Too close
                    separation_x += dx / dist
                    separation_y += dy / dist
            
            new_pos = {
                **agent,
                "x": agent.get("x", 0) + (center_x - agent.get("x", 0)) * 0.1,
                "y": agent.get("y", 0) + (center_y - agent.get("y", 0)) * 0.1,
                "vx": avg_vx * 0.8,
                "vy": avg_vy * 0.8,
            }
            
            new_positions[agent_id] = new_pos
        
        return new_positions
    
    def log_behavior(self, behavior: str, details: dict):
        """Log swarm behavior."""
        self.behavior_log.append({
            "behavior": behavior,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        })
    
    def get_swarm_state(self) -> dict:
        """Get current swarm state."""
        return {
            "pheromones_count": len(self.pheromones),
            "pheromones_by_type": {
                t: len([p for p in self.pheromones.values() if p.type == t])
                for t in ["trail", "warning", "opportunity", "danger"]
            },
            "consensus_count": len(self.consensus_history),
            "behaviors_observed": len(self.behavior_log),
        }