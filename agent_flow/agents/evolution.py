"""Evolution - Agents evolve and improve over generations.

Features:
- Genetic algorithm for agent strategies
- Mutation and crossover of successful behaviors
- Natural selection based on performance
- Speciation (specialization)
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class Gene:
    """A single trait that can evolve."""
    
    def __init__(self, name: str, value: Any, min_val: Any = None, max_val: Any = None):
        self.name = name
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
    
    def mutate(self, rate: float = 0.1) -> "Gene":
        """Mutate this gene."""
        new_value = self.value
        
        if isinstance(self.value, (int, float)) and random.random() < rate:
            if isinstance(self.value, int):
                delta = random.randint(-2, 2)
                new_value = self.value + delta
                if self.min_val is not None:
                    new_value = max(self.min_val, new_value)
                if self.max_val is not None:
                    new_value = min(self.max_val, new_value)
            else:
                delta = random.uniform(-0.5, 0.5)
                new_value = self.value + delta
        
        elif isinstance(self.value, str) and random.random() < rate:
            # String mutation - character change
            if self.value:
                pos = random.randint(0, len(self.value) - 1)
                chars = "abcdefghijklmnopqrstuvwxyz_-"
                new_value = (
                    self.value[:pos] + 
                    random.choice(chars) + 
                    self.value[pos+1:]
                )
        
        elif isinstance(self.value, list) and random.random() < rate:
            # List mutation - add or remove
            if random.random() < 0.5 and self.value:
                new_value = self.value[:-1]
            else:
                new_value = self.value + [f"new_{random.randint(1, 100)}"]
        
        return Gene(self.name, new_value, self.min_val, self.max_val)


class Genome:
    """A complete set of genes for an agent."""
    
    def __init__(self, agent_id: str, genes: list[Gene]):
        self.agent_id = agent_id
        self.genes = {g.name: g for g in genes}
        self.fitness = 0.0
        self.generation = 0
        self.age = 0
    
    def get(self, gene_name: str, default: Any = None) -> Any:
        """Get gene value."""
        if gene_name in self.genes:
            return self.genes[gene_name].value
        return default
    
    def set(self, gene_name: str, value: Any):
        """Set gene value."""
        if gene_name in self.genes:
            self.genes[gene_name].value = value
        else:
            self.genes[gene_name] = Gene(gene_name, value)
    
    def mutate(self, rate: float = 0.1) -> "Genome":
        """Create mutated copy."""
        new_genes = [g.mutate(rate) for g in self.genes.values()]
        new_genome = Genome(f"{self.agent_id}_mut", new_genes)
        new_genome.generation = self.generation + 1
        return new_genome
    
    def crossover(self, other: "Genome") -> "Genome":
        """Combine with another genome."""
        new_genes = []
        
        for gene_name in set(self.genes.keys()) | set(other.genes.keys()):
            # Random choice from each parent
            if gene_name in self.genes and gene_name in other.genes:
                if random.random() < 0.5:
                    new_genes.append(self.genes[gene_name])
                else:
                    new_genes.append(other.genes[gene_name])
            elif gene_name in self.genes:
                new_genes.append(self.genes[gene_name])
            else:
                new_genes.append(other.genes[gene_name])
        
        new_genome = Genome(
            f"cross_{self.agent_id}_{other.agent_id}",
            new_genes,
        )
        new_genome.generation = max(self.generation, other.generation) + 1
        return new_genome


class EvolutionEngine:
    """Engine for evolving agent populations.
    
    Features:
    - Fitness evaluation
    - Natural selection
    - Mutation
    - Crossover (recombination)
    - Speciation
    """
    
    def __init__(self, population_size: int = 10):
        self.population: dict[str, Genome] = {}
        self.population_size = population_size
        self.generation = 0
        self.evolution_history: list[dict] = []
        
        # Species tracking
        self.species: dict[str, list[str]] = defaultdict(list)
    
    def add_individual(self, genome: Genome):
        """Add an individual to the population."""
        self.population[genome.agent_id] = genome
    
    def evaluate_fitness(
        self,
        agent_id: str,
        fitness: float,
    ):
        """Set fitness for an individual."""
        if agent_id in self.population:
            self.population[agent_id].fitness = fitness
    
    def natural_selection(self) -> list[str]:
        """Select the fittest individuals."""
        # Sort by fitness
        sorted_pop = sorted(
            self.population.values(),
            key=lambda g: -g.fitness,
        )
        
        # Keep top half
        survivors = sorted_pop[:max(2, len(sorted_pop) // 2)]
        
        # Survivors' IDs
        survivor_ids = [g.agent_id for g in survivors]
        
        # Remove others
        for agent_id in list(self.population.keys()):
            if agent_id not in survivor_ids:
                del self.population[agent_id]
        
        return survivor_ids
    
    def evolve_generation(self) -> dict:
        """Evolve one generation.
        
        1. Selection: keep fittest
        2. Crossover: combine survivors
        3. Mutation: add variation
        4. Fill population
        """
        if len(self.population) < 2:
            return {"status": "insufficient_population"}
        
        # Select survivors
        survivors = self.natural_selection()
        
        if not survivors:
            return {"status": "no_survivors"}
        
        # Generate offspring
        offspring = []
        survivor_genomes = [self.population[sid] for sid in survivors]
        
        while len(self.population) + len(offspring) < self.population_size:
            # Select two parents
            parent_a = random.choice(survivor_genomes)
            parent_b = random.choice(survivor_genomes)
            
            if parent_a.agent_id == parent_b.agent_id:
                continue
            
            # Crossover
            child = parent_a.crossover(parent_b)
            
            # Mutate
            if random.random() < 0.3:
                child = child.mutate(0.15)
            
            offspring.append(child)
        
        # Add offspring to population
        for child in offspring:
            self.population[child.agent_id] = child
        
        self.generation += 1
        
        # Update species
        self._update_species()
        
        # Log
        result = {
            "generation": self.generation,
            "survivors": len(survivor_genomes),
            "offspring": len(offspring),
            "population_size": len(self.population),
            "avg_fitness": sum(g.fitness for g in self.population.values()) / len(self.population),
            "max_fitness": max(g.fitness for g in self.population.values()),
        }
        
        self.evolution_history.append(result)
        return result
    
    def _update_species(self):
        """Group individuals into species based on similarity."""
        self.species.clear()
        
        # Simple speciation: group by a gene value
        for genome in self.population.values():
            # Use a specific gene to determine species
            species_key = str(genome.get("role", "default"))
            self.species[species_key].append(genome.agent_id)
    
    def get_best_individual(self) -> Optional[Genome]:
        """Get the fittest individual."""
        if not self.population:
            return None
        
        return max(self.population.values(), key=lambda g: g.fitness)
    
    def get_population_stats(self) -> dict:
        """Get population statistics."""
        if not self.population:
            return {"size": 0}
        
        fitnesses = [g.fitness for g in self.population.values()]
        
        return {
            "size": len(self.population),
            "generation": self.generation,
            "avg_fitness": sum(fitnesses) / len(fitnesses),
            "max_fitness": max(fitnesses),
            "min_fitness": min(fitnesses),
            "species_count": len(self.species),
            "species": {k: len(v) for k, v in self.species.items()},
        }


class AdaptiveBehavior:
    """Behaviors that adapt and evolve."""
    
    def __init__(self):
        self.behaviors: dict[str, dict] = {}
    
    def register_behavior(self, name: str, params: dict):
        """Register an adaptive behavior."""
        self.behaviors[name] = {
            "params": params,
            "success_count": 0,
            "failure_count": 0,
            "effectiveness": 0.5,
        }
    
    def record_result(self, behavior_name: str, success: bool):
        """Record behavior outcome."""
        if behavior_name not in self.behaviors:
            return
        
        b = self.behaviors[behavior_name]
        if success:
            b["success_count"] += 1
        else:
            b["failure_count"] += 1
        
        # Update effectiveness
        total = b["success_count"] + b["failure_count"]
        b["effectiveness"] = b["success_count"] / total if total > 0 else 0.5
    
    def get_best_behavior(self, context: str = None) -> Optional[str]:
        """Get the most effective behavior."""
        if not self.behaviors:
            return None
        
        sorted_behaviors = sorted(
            self.behaviors.items(),
            key=lambda x: -x[1]["effectiveness"],
        )
        
        return sorted_behaviors[0][0]
    
    def adapt(self, behavior_name: str, adjustments: dict):
        """Adapt a behavior's parameters."""
        if behavior_name in self.behaviors:
            self.behaviors[behavior_name]["params"].update(adjustments)