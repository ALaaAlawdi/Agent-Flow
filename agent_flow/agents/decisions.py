"""Adaptive Decision Engine - Agents make decisions based on context."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class Decision:
    """A decision made by an agent."""
    
    def __init__(
        self,
        decision_id: str,
        decision_type: str,
        options: list[str],
        chosen: str,
        reasoning: str,
        confidence: float,
        context: dict = None,
    ):
        self.decision_id = decision_id
        self.decision_type = decision_type
        self.options = options
        self.chosen = chosen
        self.reasoning = reasoning
        self.confidence = confidence
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()
        self.outcome: Optional[str] = None
        self.was_correct: Optional[bool] = None
    
    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type,
            "options": self.options,
            "chosen": self.chosen,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "context": self.context,
            "timestamp": self.timestamp,
            "outcome": self.outcome,
            "was_correct": self.was_correct,
        }


class DecisionEngine:
    """Engine for making adaptive decisions.
    
    Features:
    - Context-aware decision making
    - Confidence scoring
    - Decision history and learning
    - Multiple decision strategies
    """
    
    def __init__(self):
        self.decisions: list[Decision] = []
        self.decision_patterns: dict[str, int] = defaultdict(int)
        self.success_rate_by_type: dict[str, list[bool]] = defaultdict(list)
    
    def decide(
        self,
        decision_type: str,
        options: list[str],
        context: dict = None,
        strategy: str = "best_match",
    ) -> Decision:
        """Make a decision.
        
        Strategies:
        - best_match: Choose option with best match
        - consensus: Choose based on past consensus
        - random: Random choice
        - learned: Choose based on past success
        """
        if strategy == "best_match":
            chosen, confidence, reasoning = self._best_match_strategy(options, context)
        elif strategy == "consensus":
            chosen, confidence, reasoning = self._consensus_strategy(options, decision_type)
        elif strategy == "random":
            chosen, confidence, reasoning = self._random_strategy(options)
        elif strategy == "learned":
            chosen, confidence, reasoning = self._learned_strategy(options, decision_type)
        else:
            chosen = options[0] if options else None
            confidence = 0.5
            reasoning = "Default choice"
        
        decision_id = f"dec_{int(datetime.now().timestamp() * 1000)}"
        
        decision = Decision(
            decision_id=decision_id,
            decision_type=decision_type,
            options=options,
            chosen=chosen,
            reasoning=reasoning,
            confidence=confidence,
            context=context,
        )
        
        self.decisions.append(decision)
        self.decision_patterns[decision_type] += 1
        
        return decision
    
    def _best_match_strategy(self, options: list[str], context: dict) -> tuple[str, float, str]:
        """Choose option with best match to context."""
        if not options:
            return None, 0.0, "No options available"
        
        if not context:
            return options[0], 0.5, "No context provided, chose first option"
        
        # Score each option based on context match
        scored = []
        for option in options:
            score = 0.0
            for key, value in context.items():
                if str(value).lower() in option.lower():
                    score += 1.0
                # Partial match
                for word in str(value).lower().split():
                    if word in option.lower():
                        score += 0.3
            
            scored.append((option, score))
        
        # Sort by score
        scored.sort(key=lambda x: -x[1])
        best_option, best_score = scored[0]
        
        # Calculate confidence (normalize score)
        max_possible = sum(1.0 for _ in context)
        confidence = min(1.0, best_score / max_possible) if max_possible > 0 else 0.5
        
        reasoning = f"Best match for context: {context}"
        
        return best_option, confidence, reasoning
    
    def _consensus_strategy(self, options: list[str], decision_type: str) -> tuple[str, float, str]:
        """Choose based on past consensus for this decision type."""
        if not options:
            return None, 0.0, "No options available"
        
        # Look at past decisions of this type
        past_decisions = [d for d in self.decisions if d.decision_type == decision_type]
        
        if not past_decisions:
            return options[0], 0.5, "No history, chose first option"
        
        # Count frequency of each choice
        choice_count = defaultdict(int)
        for dec in past_decisions:
            choice_count[dec.chosen] += 1
        
        # Choose most frequent
        most_frequent = max(choice_count.items(), key=lambda x: x[1])
        chosen = most_frequent[0]
        
        total = len(past_decisions)
        confidence = most_frequent[1] / total
        
        reasoning = f"Consensus from {total} past decisions"
        
        return chosen, confidence, reasoning
    
    def _random_strategy(self, options: list[str]) -> tuple[str, float, str]:
        """Random choice."""
        import random
        if not options:
            return None, 0.0, "No options available"
        
        chosen = random.choice(options)
        return chosen, 0.5, "Random choice"
    
    def _learned_strategy(self, options: list[str], decision_type: str) -> tuple[str, float, str]:
        """Choose based on past success rates."""
        if not options:
            return None, 0.0, "No options available"
        
        # Get success rates for each option
        option_scores = {}
        for option in options:
            past_outcomes = self.success_rate_by_type.get(decision_type, [])
            # Find past decisions for this option
            option_decisions = [
                d for d in self.decisions 
                if d.decision_type == decision_type and d.chosen == option
            ]
            
            if option_decisions:
                success_count = sum(1 for d in option_decisions if d.was_correct)
                option_scores[option] = success_count / len(option_decisions)
            else:
                option_scores[option] = 0.5  # Default
        
        # Choose best option
        best_option = max(option_scores.items(), key=lambda x: x[1])
        
        return best_option[0], best_option[1], "Learned from past successes"
    
    def record_outcome(self, decision_id: str, outcome: str, was_correct: bool):
        """Record the outcome of a decision for learning."""
        for decision in self.decisions:
            if decision.decision_id == decision_id:
                decision.outcome = outcome
                decision.was_correct = was_correct
                self.success_rate_by_type[decision.decision_type].append(was_correct)
                break
    
    def get_statistics(self) -> dict:
        """Get decision statistics."""
        total = len(self.decisions)
        if total == 0:
            return {"total": 0}
        
        correct = sum(1 for d in self.decisions if d.was_correct is True)
        avg_confidence = sum(d.confidence for d in self.decisions) / total
        
        return {
            "total_decisions": total,
            "correct": correct,
            "incorrect": sum(1 for d in self.decisions if d.was_correct is False),
            "success_rate": correct / total if total > 0 else 0,
            "avg_confidence": avg_confidence,
            "by_type": dict(self.decision_patterns),
        }


class AdaptiveRouter:
    """Adaptive task router that learns optimal routing."""
    
    def __init__(self):
        self.routing_history: list[dict] = []
        self.success_by_route: dict[str, list[bool]] = defaultdict(list)
    
    def route(
        self,
        task: str,
        agents: list[dict],
        context: dict = None,
    ) -> str:
        """Route a task to the best agent based on learning."""
        if not agents:
            return None
        
        # Score each agent
        scored_agents = []
        for agent in agents:
            agent_id = agent.get("id", "")
            
            # Get past performance for this agent
            past_outcomes = self.success_by_route.get(agent_id, [])
            if past_outcomes:
                success_rate = sum(past_outcomes) / len(past_outcomes)
            else:
                success_rate = 0.5  # Default
            
            # Combine with current capability score
            capability_score = agent.get("score", 0.5)
            
            # Final score
            final_score = (success_rate * 0.6) + (capability_score * 0.4)
            
            scored_agents.append((agent_id, final_score))
        
        # Choose best
        scored_agents.sort(key=lambda x: -x[1])
        chosen = scored_agents[0][0]
        
        # Record routing
        self.routing_history.append({
            "task": task,
            "agent": chosen,
            "context": context,
            "timestamp": datetime.now().isoformat(),
        })
        
        return chosen
    
    def record_outcome(self, agent_id: str, success: bool):
        """Record the outcome of a routing decision."""
        self.success_by_route[agent_id].append(success)