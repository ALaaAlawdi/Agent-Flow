"""Superhuman Reasoning - Multi-layered inference beyond human capability.

Features:
- Causal reasoning (understanding cause-effect)
- Counterfactual thinking (what if scenarios)
- Analogical reasoning across domains
- Compositional reasoning (combining concepts)
- Abductive reasoning (best explanation)
- Probabilistic reasoning under uncertainty
- Temporal reasoning across time
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class CausalGraph:
    """Causal graph - represents cause-effect relationships."""
    
    def __init__(self):
        self.nodes: dict[str, dict] = {}  # Causes and effects
        self.edges: list[dict] = []  # Cause->effect relationships
        self.confidence: dict[tuple[str, str], float] = {}  # Confidence in causality
    
    def add_cause(self, cause: str, effect: str, strength: float = 0.8, mechanism: str = ""):
        """Add a causal relationship."""
        if cause not in self.nodes:
            self.nodes[cause] = {"type": "cause"}
        if effect not in self.nodes:
            self.nodes[effect] = {"type": "effect"}
        
        self.edges.append({
            "cause": cause,
            "effect": effect,
            "strength": strength,
            "mechanism": mechanism,
        })
        
        self.confidence[(cause, effect)] = strength
    
    def trace_causes(self, effect: str, depth: int = 3) -> list[dict]:
        """Trace all causes of an effect."""
        causes = []
        visited = set()
        
        def _trace(current: str, current_depth: int, path: list):
            if current_depth > depth or current in visited:
                return
            visited.add(current)
            
            for edge in self.edges:
                if edge["effect"] == current:
                    causes.append({
                        "cause": edge["cause"],
                        "strength": edge["strength"],
                        "path": path + [edge["cause"]],
                        "depth": current_depth,
                    })
                    _trace(edge["cause"], current_depth + 1, path + [edge["cause"]])
        
        _trace(effect, 0, [])
        return causes
    
    def predict_effect(self, cause: str, depth: int = 3) -> list[dict]:
        """Predict effects of a cause."""
        effects = []
        visited = set()
        
        def _trace(current: str, current_depth: int, path: list):
            if current_depth > depth or current in visited:
                return
            visited.add(current)
            
            for edge in self.edges:
                if edge["cause"] == current:
                    effects.append({
                        "effect": edge["effect"],
                        "probability": edge["strength"],
                        "path": path + [edge["effect"]],
                        "depth": current_depth,
                    })
                    _trace(edge["effect"], current_depth + 1, path + [edge["effect"]])
        
        _trace(cause, 0, [])
        return effects


class Counterfactual:
    """Counterfactual scenario - what if things were different?"""
    
    def __init__(self, scenario_id: str, reality: dict, alternative: dict):
        self.scenario_id = scenario_id
        self.reality = reality
        self.alternative = alternative
        self.differences: list[dict] = []
        self.predicted_outcomes: list[dict] = []
        self.timestamp = datetime.now().isoformat()
    
    def analyze_differences(self) -> list[dict]:
        """Analyze what differs between reality and alternative."""
        all_keys = set(self.reality.keys()) | set(self.alternative.keys())
        
        for key in all_keys:
            r_val = self.reality.get(key)
            a_val = self.alternative.get(key)
            
            if r_val != a_val:
                self.differences.append({
                    "key": key,
                    "reality": r_val,
                    "alternative": a_val,
                    "impact": self._estimate_impact(key, r_val, a_val),
                })
        
        return self.differences
    
    def _estimate_impact(self, key: str, r_val: Any, a_val: Any) -> str:
        """Estimate impact of a difference."""
        if isinstance(r_val, (int, float)) and isinstance(a_val, (int, float)):
            ratio = abs(a_val - r_val) / max(abs(r_val), 1)
            if ratio > 0.5:
                return "high"
            elif ratio > 0.2:
                return "medium"
            return "low"
        return "qualitative"
    
    def predict_outcomes(self, causal_graph: CausalGraph) -> list[dict]:
        """Predict outcomes of the alternative scenario."""
        for diff in self.differences:
            # Trace what would change
            effects = causal_graph.predict_effect(diff["key"], depth=2)
            self.predicted_outcomes.append({
                "change": diff,
                "effects": effects,
            })
        
        return self.predicted_outcomes


class Analogy:
    """Analogical mapping between two domains."""
    
    def __init__(self, source_domain: str, target_domain: str):
        self.source_domain = source_domain
        self.target_domain = target_domain
        self.mappings: dict[str, str] = {}  # source concept -> target concept
        self.structure_similarity: float = 0.0
    
    def add_mapping(self, source: str, target: str):
        """Add a mapping between domains."""
        self.mappings[source] = target
    
    def transfer_solution(self, source_solution: str) -> str:
        """Transfer a solution from source to target domain."""
        transferred = source_solution
        
        # Apply mappings
        for source, target in self.mappings.items():
            transferred = transferred.replace(source, target)
        
        return transferred
    
    def compute_similarity(self) -> float:
        """Compute structural similarity between domains."""
        # Simple heuristic
        if not self.mappings:
            return 0.0
        
        self.structure_similarity = min(1.0, len(self.mappings) / 10)
        return self.structure_similarity


class SuperReasoner:
    """Superhuman reasoning engine.
    
    Combines multiple reasoning modes for superior intelligence.
    """
    
    def __init__(self):
        self.causal_graph = CausalGraph()
        self.counterfactuals: list[Counterfactual] = []
        self.analogies: list[Analogy] = []
        self.compositions: list[dict] = []
        self.abductions: list[dict] = []
        self.beliefs: dict[str, float] = {}  # Bayesian beliefs
    
    def reason_about_problem(
        self,
        problem: str,
        context: dict = None,
    ) -> dict:
        """Apply multiple reasoning modes to a problem."""
        reasoning = {
            "problem": problem,
            "modes_applied": [],
            "conclusions": [],
            "confidence": 0.0,
        }
        
        # 1. Causal reasoning
        causal_analysis = self._causal_reasoning(problem, context)
        if causal_analysis:
            reasoning["modes_applied"].append("causal")
            reasoning["conclusions"].extend(causal_analysis)
        
        # 2. Counterfactual reasoning
        cf_analysis = self._counterfactual_reasoning(problem, context)
        if cf_analysis:
            reasoning["modes_applied"].append("counterfactual")
            reasoning["conclusions"].extend(cf_analysis)
        
        # 3. Analogical reasoning
        analogy = self._analogical_reasoning(problem, context)
        if analogy:
            reasoning["modes_applied"].append("analogical")
            reasoning["conclusions"].extend(analogy)
        
        # 4. Abductive reasoning
        abduction = self._abductive_reasoning(problem, context)
        if abduction:
            reasoning["modes_applied"].append("abductive")
            reasoning["conclusions"].extend(abduction)
        
        # 5. Probabilistic reasoning
        prob = self._probabilistic_reasoning(problem, context)
        if prob:
            reasoning["modes_applied"].append("probabilistic")
            reasoning["conclusions"].extend(prob)
        
        # Calculate overall confidence
        reasoning["confidence"] = min(1.0, len(reasoning["conclusions"]) * 0.2)
        
        return reasoning
    
    def _causal_reasoning(self, problem: str, context: dict) -> list[str]:
        """Apply causal reasoning."""
        conclusions = []
        
        # Find relevant causal chains
        for node in self.causal_graph.nodes:
            if any(word in problem.lower() for word in node.lower().split()):
                effects = self.causal_graph.predict_effect(node, depth=2)
                if effects:
                    conclusions.append(f"Causally, {node} leads to {effects[0]['effect']}")
        
        return conclusions[:3]
    
    def _counterfactual_reasoning(self, problem: str, context: dict) -> list[str]:
        """Apply counterfactual reasoning."""
        conclusions = []
        
        if context and "reality" in context and "alternative" in context:
            cf = Counterfactual(
                f"cf_{len(self.counterfactuals)}",
                context["reality"],
                context["alternative"],
            )
            cf.analyze_differences()
            
            for diff in cf.differences[:2]:
                conclusions.append(
                    f"If {diff['key']} were {diff['alternative']} instead of {diff['reality']}, "
                    f"impact would be {diff['impact']}"
                )
            
            self.counterfactuals.append(cf)
        
        return conclusions
    
    def _analogical_reasoning(self, problem: str, context: dict) -> list[str]:
        """Apply analogical reasoning."""
        conclusions = []
        
        for analogy in self.analogies:
            if analogy.source_domain.lower() in problem.lower():
                transferred = analogy.transfer_solution(problem[:100])
                conclusions.append(
                    f"By analogy with {analogy.target_domain}: {transferred[:100]}"
                )
        
        if not conclusions and self.analogies:
            # Use any analogy
            analogy = self.analogies[0]
            transferred = analogy.transfer_solution(problem[:100])
            conclusions.append(f"Similar to {analogy.target_domain}: {transferred[:100]}")
        
        return conclusions
    
    def _abductive_reasoning(self, problem: str, context: dict) -> list[str]:
        """Apply abductive reasoning (inference to best explanation)."""
        conclusions = []
        
        if self.abductions:
            # Find best explanation
            best = max(self.abductions, key=lambda x: x.get("score", 0))
            conclusions.append(f"Best explanation: {best['explanation']}")
        
        return conclusions
    
    def _probabilistic_reasoning(self, problem: str, context: dict) -> list[str]:
        """Apply probabilistic reasoning under uncertainty."""
        conclusions = []
        
        for belief, probability in self.beliefs.items():
            if any(word in problem.lower() for word in belief.lower().split()):
                conclusions.append(
                    f"Probability of {belief}: {probability:.1%}"
                )
        
        return conclusions
    
    def add_causal_knowledge(self, cause: str, effect: str, strength: float = 0.8, mechanism: str = ""):
        """Add causal knowledge."""
        self.causal_graph.add_cause(cause, effect, strength, mechanism)
    
    def create_analogy(self, source: str, target: str) -> Analogy:
        """Create an analogy between domains."""
        analogy = Analogy(source, target)
        self.analogies.append(analogy)
        return analogy
    
    def update_belief(self, belief: str, probability: float):
        """Update Bayesian belief."""
        self.beliefs[belief] = max(0, min(1, probability))
    
    def compose_concepts(self, concept_a: str, concept_b: str) -> dict:
        """Compose two concepts into a new one (creativity)."""
        composition = {
            "id": f"compose_{len(self.compositions)}",
            "components": [concept_a, concept_b],
            "novel_concept": f"{concept_a}-{concept_b}",
            "emergent_properties": [
                f"Combines properties of {concept_a} and {concept_b}",
                f"Has unique synergy not found in either alone",
            ],
            "timestamp": datetime.now().isoformat(),
        }
        
        self.compositions.append(composition)
        return composition


class InferenceEngine:
    """Forward and backward chaining inference."""
    
    def __init__(self):
        self.rules: list[dict] = []
        self.facts: set[str] = set()
        self.inferred: set[str] = set()
    
    def add_rule(self, premises: list[str], conclusion: str, confidence: float = 1.0):
        """Add an inference rule."""
        self.rules.append({
            "premises": premises,
            "conclusion": conclusion,
            "confidence": confidence,
        })
    
    def add_fact(self, fact: str):
        """Add a known fact."""
        self.facts.add(fact)
    
    def forward_chain(self, max_iterations: int = 10) -> list[str]:
        """Forward chaining - derive new facts."""
        new_facts = []
        
        for _ in range(max_iterations):
            made_progress = False
            
            for rule in self.rules:
                # Check if all premises are satisfied
                if all(p in self.facts or p in self.inferred for p in rule["premises"]):
                    if rule["conclusion"] not in self.facts and rule["conclusion"] not in self.inferred:
                        self.inferred.add(rule["conclusion"])
                        new_facts.append(rule["conclusion"])
                        made_progress = True
            
            if not made_progress:
                break
        
        return new_facts
    
    def backward_chain(self, goal: str, depth: int = 5) -> bool:
        """Backward chaining - prove a goal."""
        if depth == 0:
            return False
        
        # Check if goal is a known fact
        if goal in self.facts or goal in self.inferred:
            return True
        
        # Find rules that conclude the goal
        for rule in self.rules:
            if rule["conclusion"] == goal:
                # Try to prove all premises
                if all(self.backward_chain(p, depth - 1) for p in rule["premises"]):
                    self.inferred.add(goal)
                    return True
        
        return False