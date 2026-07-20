"""Quantum Superposition - Agents exist in multiple states simultaneously.

Features:
- Quantum-inspired superposition of decisions
- State collapse upon observation
- Entangled agents (shared fate)
- Parallel universes (different strategies)
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class QuantumState:
    """A quantum state representing multiple possibilities."""
    
    def __init__(self, state_id: str, possibilities: dict[str, float]):
        self.state_id = state_id
        # Possibilities with their probability amplitudes
        self.possibilities = possibilities
        self.collapsed = False
        self.collapsed_to: Optional[str] = None
        self.created_at = datetime.now().isoformat()
    
    def observe(self) -> str:
        """Observe the state, causing collapse.
        
        The state collapses to one possibility based on probability.
        Returns the chosen state.
        """
        if self.collapsed:
            return self.collapsed_to
        
        # Weighted random choice based on amplitudes
        outcomes = list(self.possibilities.keys())
        weights = list(self.possibilities.values())
        
        # Normalize
        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]
        
        chosen = random.choices(outcomes, weights=weights, k=1)[0]
        
        self.collapsed = True
        self.collapsed_to = chosen
        return chosen
    
    def interfere_with(self, other: "QuantumState") -> "QuantumState":
        """Two quantum states interfere - constructive or destructive.
        
        Creates a new state combining possibilities.
        """
        combined = {}
        
        for state, amplitude in self.possibilities.items():
            for other_state, other_amplitude in other.possibilities.items():
                key = f"{state}+{other_state}"
                # Interference pattern
                new_amplitude = (amplitude * other_amplitude) ** 0.5
                combined[key] = combined.get(key, 0) + new_amplitude
        
        return QuantumState(
            f"interfered_{self.state_id}_{other.state_id}",
            combined,
        )


class QuantumAgent:
    """An agent that exists in superposition.
    
    Holds multiple possible decisions/actions simultaneously.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.superposition_states: dict[str, QuantumState] = {}
        self.entangled_with: list[str] = []  # Other entangled agents
    
    def enter_superposition(self, decision_id: str, options: dict[str, float]) -> str:
        """Enter superposition with multiple possible decisions."""
        state = QuantumState(decision_id, options)
        self.superposition_states[decision_id] = state
        return state.state_id
    
    def collapse(self, decision_id: str) -> Optional[str]:
        """Collapse the superposition to a single decision."""
        if decision_id not in self.superposition_states:
            return None
        
        state = self.superposition_states[decision_id]
        return state.observe()
    
    def entangle_with(self, other_agent_id: str):
        """Become entangled with another agent.
        
        When one collapses, the other may collapse too.
        """
        if other_agent_id not in self.entangled_with:
            self.entangled_with.append(other_agent_id)


class QuantumEngine:
    """Quantum-inspired decision engine.
    
    Allows agents to:
    - Hold multiple decisions simultaneously (superposition)
    - Collapse to one decision upon observation
    - Interfere states to create new options
    - Entangle with other agents
    """
    
    def __init__(self):
        self.quantum_agents: dict[str, QuantumAgent] = {}
        self.parallel_universes: list[dict] = []  # Different possible realities
        self.entanglement_groups: list[set] = []
    
    def get_or_create_quantum_agent(self, agent_id: str) -> QuantumAgent:
        """Get or create quantum agent."""
        if agent_id not in self.quantum_agents:
            self.quantum_agents[agent_id] = QuantumAgent(agent_id)
        return self.quantum_agents[agent_id]
    
    def superposition_decision(
        self,
        agent_id: str,
        decision_id: str,
        options: dict[str, float],
    ) -> str:
        """Agent holds multiple decisions in superposition."""
        qa = self.get_or_create_quantum_agent(agent_id)
        return qa.enter_superposition(decision_id, options)
    
    def collapse_decision(self, agent_id: str, decision_id: str) -> Optional[str]:
        """Collapse superposition to actual decision."""
        qa = self.quantum_agents.get(agent_id)
        if qa:
            return qa.collapse(decision_id)
        return None
    
    def entangle_agents(self, agent_ids: list[str]):
        """Entangle multiple agents together."""
        entanglement = set(agent_ids)
        self.entanglement_groups.append(entanglement)
        
        # Update each agent
        for aid in agent_ids:
            qa = self.get_or_create_quantum_agent(aid)
            for other in agent_ids:
                if other != aid:
                    qa.entangle_with(other)
    
    def collapse_entangled(self, agent_id: str, decision_id: str) -> dict:
        """Collapse one agent, affecting all entangled.
        
        Returns the state of all entangled agents.
        """
        result = {"primary": None, "entangled": {}}
        
        qa = self.quantum_agents.get(agent_id)
        if not qa:
            return result
        
        # Collapse primary
        primary_result = qa.collapse(decision_id)
        result["primary"] = primary_result
        
        # Collapse all entangled with same logic
        for other_id in qa.entangled_with:
            other_qa = self.quantum_agents.get(other_id)
            if other_qa and decision_id in other_qa.superposition_states:
                # Find entanglement group
                for group in self.entanglement_groups:
                    if agent_id in group and other_id in group:
                        # Same decision for entangled
                        result["entangled"][other_id] = primary_result
                        break
        
        return result
    
    def create_parallel_universe(
        self,
        scenario_name: str,
        agent_assignments: dict[str, str],
    ) -> dict:
        """Create a parallel universe with different agent assignments."""
        universe = {
            "name": scenario_name,
            "assignments": agent_assignments,
            "created_at": datetime.now().isoformat(),
            "outcomes": {},
        }
        self.parallel_universes.append(universe)
        return universe
    
    def simulate_all_universes(
        self,
        task: str,
        max_universes: int = 5,
    ) -> list[dict]:
        """Simulate multiple parallel universes to find best path."""
        results = []
        
        # Generate different strategies
        strategies = [
            "aggressive",
            "conservative",
            "balanced",
            "innovative",
            "collaborative",
        ]
        
        for i, strategy in enumerate(strategies[:max_universes]):
            universe = self.create_parallel_universe(
                f"universe_{strategy}",
                {"strategy": strategy, "task": task},
            )
            
            # Simulate outcome (heuristic)
            outcome_score = self._simulate_universe_outcome(strategy, task)
            universe["outcomes"] = {
                "score": outcome_score,
                "strategy": strategy,
            }
            results.append(universe)
        
        # Sort by score
        results.sort(key=lambda u: -u["outcomes"]["score"])
        return results
    
    def _simulate_universe_outcome(self, strategy: str, task: str) -> float:
        """Simulate outcome of a universe (heuristic scoring)."""
        base_score = 0.5
        
        # Strategy bonuses
        bonuses = {
            "aggressive": 0.7 if "urgent" in task.lower() else 0.4,
            "conservative": 0.6 if "critical" in task.lower() else 0.5,
            "balanced": 0.65,
            "innovative": 0.8 if "new" in task.lower() or "creative" in task.lower() else 0.5,
            "collaborative": 0.75 if "team" in task.lower() else 0.5,
        }
        
        return bonuses.get(strategy, base_score) + random.uniform(-0.1, 0.1)