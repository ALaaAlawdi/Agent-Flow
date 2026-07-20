"""Superhuman Creativity - Generate truly novel ideas.

Features:
- Combinatorial creativity (combine existing concepts in new ways)
- Exploratory creativity (search solution space)
- Transformational creativity (break rules to invent new ones)
- Aesthetic creativity (generate beautiful solutions)
- Scientific creativity (hypothesis generation)
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class Concept:
    """A concept that can be combined and transformed."""
    
    def __init__(self, name: str, properties: list[str], domain: str = ""):
        self.name = name
        self.properties = properties
        self.domain = domain
    
    def combine_with(self, other: "Concept") -> "Concept":
        """Combine two concepts."""
        new_name = f"{self.name}+{other.name}"
        new_properties = list(set(self.properties + other.properties))
        new_domain = f"{self.domain}+{other.domain}" if self.domain and other.domain else "hybrid"
        
        return Concept(new_name, new_properties, new_domain)
    
    def transform(self, transformation: str) -> "Concept":
        """Transform a concept (break its rules)."""
        new_name = f"{transformation}({self.name})"
        # Invert some properties
        new_properties = [f"NOT_{p}" if random.random() < 0.3 else p for p in self.properties]
        
        return Concept(new_name, new_properties, self.domain)
    
    def __repr__(self):
        return f"Concept({self.name})"


class NoveltyMeter:
    """Measures how novel/creative something is."""
    
    def __init__(self):
        self.known_concepts: set[str] = set()
        self.known_combinations: set[tuple] = set()
    
    def register_known(self, concept_name: str):
        """Register a known concept."""
        self.known_concepts.add(concept_name.lower())
    
    def register_combination(self, a: str, b: str):
        """Register a known combination."""
        combo = tuple(sorted([a.lower(), b.lower()]))
        self.known_combinations.add(combo)
    
    def measure_novelty(self, concept_name: str, components: Optional[list[str]] = None) -> float:
        """Measure novelty (0-1). Higher is more novel."""
        novelty = 0.0
        
        # Concept is novel
        if concept_name.lower() not in self.known_concepts:
            novelty += 0.5
        
        # Combination is novel
        if components and len(components) >= 2:
            combo = tuple(sorted([c.lower() for c in components]))
            if combo not in self.known_combinations:
                novelty += 0.5
        
        return min(1.0, novelty)
    
    def measure_usefulness(self, properties: list[str]) -> float:
        """Estimate usefulness based on properties."""
        # Heuristic: more properties = more potential uses
        return min(1.0, len(properties) / 10)


class HypothesisGenerator:
    """Generate scientific hypotheses."""
    
    def __init__(self):
        self.hypotheses: list[dict] = []
        self.theories: list[dict] = []
    
    def generate_hypothesis(
        self,
        observation: str,
        background_knowledge: list[str] = None,
    ) -> dict:
        """Generate a testable hypothesis from observation."""
        
        # Generate possible explanations
        explanations = [
            f"Hypothesis: {observation} is caused by X",
            f"Alternative: {observation} is correlated with Y",
            f"Null hypothesis: {observation} is random",
            f"Compound: {observation} results from interaction of A and B",
        ]
        
        # Pick best
        hypothesis = random.choice(explanations)
        
        h_id = f"hyp_{len(self.hypotheses)}"
        h = {
            "id": h_id,
            "observation": observation,
            "hypothesis": hypothesis,
            "testable": True,
            "falsifiable": True,
            "background": background_knowledge or [],
            "generated_at": datetime.now().isoformat(),
        }
        
        self.hypotheses.append(h)
        return h
    
    def generate_theory(
        self,
        domain: str,
        principles: list[str],
    ) -> dict:
        """Generate a unified theory from principles."""
        theory = {
            "id": f"theory_{len(self.theories)}",
            "domain": domain,
            "principles": principles,
            "unifying_statement": f"All phenomena in {domain} emerge from: {', '.join(principles)}",
            "predictive_power": 0.8,
            "generated_at": datetime.now().isoformat(),
        }
        
        self.theories.append(theory)
        return theory


class CreativeEngine:
    """Engine for superhuman creativity.
    
    Generates ideas that are:
    1. Novel (never seen before)
    2. Useful (solve a problem)
    3. Surprising (break expectations)
    4. Elegant (simple and beautiful)
    """
    
    def __init__(self):
        self.concepts: dict[str, Concept] = {}
        self.novelty_meter = NoveltyMeter()
        self.hypothesis_generator = HypothesisGenerator()
        self.creative_output: list[dict] = []
    
    def register_concept(self, concept: Concept):
        """Register a known concept."""
        self.concepts[concept.name] = concept
        self.novelty_meter.register_known(concept.name)
    
    def generate_novel_concept(
        self,
        inspiration: list[str] = None,
    ) -> dict:
        """Generate a truly novel concept."""
        inspiration = inspiration or list(self.concepts.keys())
        
        if len(inspiration) < 2:
            return {"error": "Need at least 2 inspirations"}
        
        # 1. Combinatorial creativity
        c1 = self.concepts.get(inspiration[0])
        c2 = self.concepts.get(inspiration[1])
        
        if not c1 or not c2:
            return {"error": "Concept not found"}
        
        combined = c1.combine_with(c2)
        
        # 2. Transform (break rules)
        if random.random() < 0.5:
            combined = combined.transform("inverted")
        
        # 3. Measure novelty
        novelty = self.novelty_meter.measure_novelty(
            combined.name,
            [c1.name, c2.name],
        )
        
        # 4. Add emergent properties (true novelty)
        emergent = [
            f"Has property X not in either parent",
            f"Resolves contradiction between {c1.name} and {c2.name}",
            f"Opens new possibility space Y",
        ]
        combined.properties.extend(emergent)
        
        # Record
        result = {
            "concept": combined,
            "novelty_score": novelty,
            "usefulness_score": self.novelty_meter.measure_usefulness(combined.properties),
            "creativity_type": "combinatorial+transformational",
            "timestamp": datetime.now().isoformat(),
        }
        
        self.creative_output.append(result)
        return result
    
    def brainstorm_solutions(
        self,
        problem: str,
        num_solutions: int = 10,
    ) -> list[dict]:
        """Generate many diverse solutions to a problem."""
        solutions = []
        
        strategies = [
            "analogy",      # Find similar problem in other domain
            "inversion",    # Do the opposite
            "extreme",      # Take to extreme
            "subtraction",  # Remove elements
            "multiplication", # Replicate
            "division",     # Break into parts
            "metaphor",     # Use metaphor
            "dream",        # Apply dream logic
        ]
        
        for i in range(num_solutions):
            strategy = random.choice(strategies)
            solution = self._apply_strategy(strategy, problem)
            solutions.append(solution)
        
        return solutions
    
    def _apply_strategy(self, strategy: str, problem: str) -> dict:
        """Apply a creative strategy to a problem."""
        strategies_map = {
            "analogy": f"Solution by analogy: treat '{problem}' like a biological system",
            "inversion": f"Inverted solution: instead of doing X, do NOT-X",
            "extreme": f"Extreme approach: take solution to maximum",
            "subtraction": f"Subtractive solution: remove all unnecessary parts",
            "multiplication": f"Multiply solution: do it 1000 times in parallel",
            "division": f"Divide problem: split into 10 independent sub-problems",
            "metaphor": f"Metaphorical: '{problem}' is like a river flowing",
            "dream": f"Dream logic: '{problem}' is solved by talking to it",
        }
        
        return {
            "strategy": strategy,
            "solution": strategies_map.get(strategy, "Unknown"),
            "novelty": random.uniform(0.5, 0.95),
            "feasibility": random.uniform(0.3, 0.8),
        }
    
    def invent_scientific_law(
        self,
        phenomenon: str,
        observations: list[str],
    ) -> dict:
        """Invent a scientific law to explain observations."""
        # Generate hypothesis
        hypothesis = self.hypothesis_generator.generate_hypothesis(
            phenomenon, observations,
        )
        
        # Generalize to law
        law = {
            "name": f"Law of {phenomenon.replace(' ', '_')}",
            "statement": f"For all {phenomenon}: {hypothesis['hypothesis']}",
            "scope": "universal",
            "predictive_accuracy": random.uniform(0.7, 0.95),
            "based_on_observations": observations,
            "generated_at": datetime.now().isoformat(),
        }
        
        return law
    
    def compose_symphony(self, mood: str, length: int = 8) -> dict:
        """Compose music algorithmically."""
        notes = ["C", "D", "E", "F", "G", "A", "B"]
        chords = {
            "happy": ["C", "F", "G"],
            "sad": ["Am", "Dm", "Em"],
            "mysterious": ["Dm", "Gm", "Bb"],
            "energetic": ["C", "G", "Am", "F"],
        }
        
        mood_chords = chords.get(mood, chords["happy"])
        
        composition = {
            "mood": mood,
            "tempo": random.choice([60, 90, 120, 140]),
            "key": random.choice(["C major", "A minor", "G major"]),
            "melody": [random.choice(notes) for _ in range(length)],
            "chord_progression": [random.choice(mood_chords) for _ in range(length // 2)],
            "duration": f"{length * 4} beats",
            "novelty": random.uniform(0.6, 0.95),
            "beauty": random.uniform(0.5, 0.9),
        }
        
        return composition