"""Morphogenetic Field - Emergent structure formation.

Like biological morphogenesis, agents can:
- Self-organize into structures
- Form emergent hierarchies
- Create patterns without central control
- Develop specialized roles naturally
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class MorphogeneticField:
    """A field that influences agent behavior and structure.
    
    Like morphogens in biology that create patterns,
    this field shapes how agents organize themselves.
    """
    
    def __init__(self, field_id: str):
        self.field_id = field_id
        self.concentration: dict[str, float] = {}  # Position -> concentration
        self.activation_threshold = 0.5
        self.inhibition_strength = 0.3
        self.sources: list[str] = []  # Active sources
    
    def set_source(self, position: str, strength: float = 1.0):
        """Set a morphogen source at a position."""
        self.concentration[position] = strength
        if position not in self.sources:
            self.sources.append(position)
    
    def diffuse(self, rate: float = 0.1):
        """Diffuse morphogens through the field."""
        new_concentration = dict(self.concentration)
        
        positions = list(self.concentration.keys())
        for pos in positions:
            # Diffuse to neighbors
            for neighbor_pos in positions:
                if neighbor_pos != pos:
                    diff = self.concentration[pos] - self.concentration[neighbor_pos]
                    transfer = diff * rate
                    new_concentration[neighbor_pos] = new_concentration.get(neighbor_pos, 0) + transfer
        
        self.concentration = new_concentration
    
    def is_activated(self, position: str) -> bool:
        """Check if position has activating concentration."""
        return self.concentration.get(position, 0) >= self.activation_threshold


class Pattern:
    """An emergent pattern in the morphogenetic field."""
    
    PATTERN_TYPES = [
        "stripe",      # Zabra-like
        "spot",        # Polka-dot
        "gradient",    # Linear gradient
        "wave",        # Wave-like
        "cluster",     # Clusters
        "tree",        # Branching
        "spiral",      # Spiral
    ]
    
    def __init__(self, pattern_type: str, positions: list[str]):
        self.pattern_type = pattern_type
        self.positions = positions
        self.created_at = datetime.now().isoformat()
        self.stability = 0.5  # How stable the pattern is


class MorphogenesisEngine:
    """Engine for emergent structure formation.
    
    Agents self-organize based on:
    - Local morphogen concentrations
    - Neighbor interactions
    - Activation/inhibition rules
    """
    
    def __init__(self):
        self.fields: dict[str, MorphogeneticField] = {}
        self.patterns: list[Pattern] = []
        self.organization_history: list[dict] = []
    
    def create_field(self, field_id: str) -> MorphogeneticField:
        """Create a new morphogenetic field."""
        field = MorphogeneticField(field_id)
        self.fields[field_id] = field
        return field
    
    def activate_role(
        self,
        field_id: str,
        role_position: str,
        strength: float = 1.0,
    ):
        """Activate a role in the morphogenetic field."""
        if field_id not in self.fields:
            self.create_field(field_id)
        
        self.fields[field_id].set_source(role_position, strength)
    
    def form_pattern(
        self,
        field_id: str,
        pattern_type: str,
    ) -> Optional[Pattern]:
        """Form an emergent pattern in the field."""
        if field_id not in self.fields:
            return None
        
        field = self.fields[field_id]
        
        # Identify positions based on pattern type
        if pattern_type == "cluster":
            # Find high-concentration areas
            positions = [
                pos for pos, conc in field.concentration.items()
                if conc >= field.activation_threshold
            ]
        elif pattern_type == "gradient":
            # All positions in concentration order
            positions = sorted(
                field.concentration.keys(),
                key=lambda p: -field.concentration[p],
            )
        else:
            # Random positions
            positions = random.sample(
                list(field.concentration.keys()),
                min(3, len(field.concentration)),
            )
        
        pattern = Pattern(pattern_type, positions)
        self.patterns.append(pattern)
        return pattern
    
    def self_organize(
        self,
        agents: dict[str, dict],
        field_id: str = "main",
    ) -> dict:
        """Agents self-organize based on morphogenetic field.
    
        Each agent:
        1. Senses local concentration
        2. Moves toward activation
        3. Inhibits neighbors if too dense
        """
        if field_id not in self.fields:
            return {"status": "no_field"}
        
        field = self.fields[field_id]
        movements = {}
        
        for agent_id, agent_state in agents.items():
            current_pos = agent_state.get("role", "default")
            
            # Sense concentrations
            local_conc = field.concentration.get(current_pos, 0)
            
            # Decide movement
            if local_conc >= field.activation_threshold:
                # Stay - activated
                movements[agent_id] = {"action": "stay", "position": current_pos}
            else:
                # Move toward higher concentration
                better_pos = max(
                    field.concentration.items(),
                    key=lambda x: x[1],
                    default=(current_pos, 0),
                )[0]
                movements[agent_id] = {"action": "move", "position": better_pos}
        
        # Record
        self.organization_history.append({
            "field": field_id,
            "movements": movements,
            "timestamp": datetime.now().isoformat(),
        })
        
        return movements
    
    def detect_emergence(self) -> list[dict]:
        """Detect emergent patterns and structures."""
        emergent = []
        
        for pattern in self.patterns[-5:]:  # Recent patterns
            emergent.append({
                "type": pattern.pattern_type,
                "stability": pattern.stability,
                "positions": pattern.positions,
            })
        
        return emergent
    
    def get_field_state(self, field_id: str) -> dict:
        """Get state of a morphogenetic field."""
        if field_id not in self.fields:
            return {}
        
        field = self.fields[field_id]
        return {
            "sources": field.sources,
            "concentrations": field.concentration,
            "activated": sum(1 for c in field.concentration.values() if c >= field.activation_threshold),
        }