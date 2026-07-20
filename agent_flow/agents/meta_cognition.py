"""Meta-Cognition - Agents think about their own thinking.

Features:
- Self-reflection on past decisions
- Bias detection
- Confidence calibration
- Thinking strategy selection
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class ThoughtTrace:
    """Trace of agent's thinking process."""
    
    def __init__(
        self,
        trace_id: str,
        agent_id: str,
        situation: str,
        thoughts: list[str],
        decision: str,
        confidence: float,
        biases_detected: list[str],
        reasoning_chain: list[dict],
    ):
        self.trace_id = trace_id
        self.agent_id = agent_id
        self.situation = situation
        self.thoughts = thoughts
        self.decision = decision
        self.confidence = confidence
        self.biases_detected = biases_detected
        self.reasoning_chain = reasoning_chain
        self.created_at = datetime.now().isoformat()
        self.was_correct: Optional[bool] = None


class MetaCognition:
    """Meta-cognitive layer for agents.
    
    Agents reflect on their own thinking to:
    1. Detect cognitive biases
    2. Calibrate confidence
    3. Improve reasoning strategies
    4. Learn from thinking patterns
    """
    
    # Common cognitive biases to detect
    BIASES = [
        "confirmation_bias",      # Seeking info that confirms existing beliefs
        "anchoring",              # Relying too much on first piece of info
        "availability",           # Overweighting recent/memorable events
        "sunk_cost",              # Continuing due to past investment
        "bandwagon",              # Following the crowd
        "recency",                # Giving more weight to recent events
        "overconfidence",         # Overestimating own accuracy
        "analysis_paralysis",     # Over-analyzing without acting
        "premature_optimization", # Optimizing before understanding
    ]
    
    def __init__(self):
        self.traces: list[ThoughtTrace] = []
        self.bias_counts: dict[str, int] = defaultdict(int)
        self.strategy_effectiveness: dict[str, list[bool]] = defaultdict(list)
    
    def think_about_thinking(
        self,
        agent_id: str,
        situation: str,
        proposed_decision: str,
        reasoning: list[str],
        confidence: float,
    ) -> ThoughtTrace:
        """Reflect on a decision-making process.
        
        Args:
            agent_id: Agent doing the thinking
            situation: What they're deciding about
            proposed_decision: What they're about to do
            reasoning: Their reasoning steps
            confidence: How confident they are (0-1)
        """
        # Detect biases
        biases = self._detect_biases(reasoning, confidence)
        
        # Calibrate confidence
        calibrated_confidence = self._calibrate_confidence(confidence, biases)
        
        # Generate reasoning chain
        chain = self._build_reasoning_chain(reasoning, biases)
        
        trace_id = f"trace_{agent_id}_{int(datetime.now().timestamp())}"
        
        trace = ThoughtTrace(
            trace_id=trace_id,
            agent_id=agent_id,
            situation=situation,
            thoughts=reasoning,
            decision=proposed_decision,
            confidence=calibrated_confidence,
            biases_detected=biases,
            reasoning_chain=chain,
        )
        
        self.traces.append(trace)
        
        # Update bias counts
        for bias in biases:
            self.bias_counts[bias] += 1
        
        return trace
    
    def _detect_biases(self, reasoning: list[str], confidence: float) -> list[str]:
        """Detect cognitive biases in reasoning."""
        biases = []
        
        reasoning_text = " ".join(reasoning).lower()
        
        # Overconfidence
        if confidence > 0.9:
            biases.append("overconfidence")
        
        # Premature optimization
        if any(w in reasoning_text for w in ["optimize", "perfect", "best"]):
            if "first" in reasoning_text or "quick" in reasoning_text:
                biases.append("premature_optimization")
        
        # Analysis paralysis
        if len(reasoning) > 5:
            biases.append("analysis_paralysis")
        
        # Anchoring
        if any(w in reasoning_text for w in ["first", "initially", "originally"]):
            biases.append("anchoring")
        
        # Confirmation bias
        if any(w in reasoning_text for w in ["confirms", "supports", "validates"]):
            biases.append("confirmation_bias")
        
        # Recency
        if any(w in reasoning_text for w in ["recently", "just now", "lately"]):
            biases.append("recency")
        
        # Bandwagon
        if any(w in reasoning_text for w in ["everyone", "team", "consensus", "agreed"]):
            biases.append("bandwagon")
        
        return biases
    
    def _calibrate_confidence(self, confidence: float, biases: list[str]) -> float:
        """Calibrate confidence based on detected biases."""
        # Reduce confidence for each bias
        penalty = len(biases) * 0.1
        
        # Overconfidence gets extra penalty
        if "overconfidence" in biases:
            penalty += 0.2
        
        calibrated = max(0.1, confidence - penalty)
        return round(calibrated, 2)
    
    def _build_reasoning_chain(self, reasoning: list[str], biases: list[str]) -> list[dict]:
        """Build structured reasoning chain."""
        chain = []
        
        for i, step in enumerate(reasoning):
            chain.append({
                "step": i + 1,
                "thought": step[:100],
                "biases_in_step": [
                    b for b in biases 
                    if any(w in step.lower() for w in self._bias_keywords(b))
                ],
            })
        
        return chain
    
    def _bias_keywords(self, bias: str) -> list[str]:
        """Get keywords associated with a bias."""
        keywords = {
            "confirmation_bias": ["confirms", "supports", "validates"],
            "anchoring": ["first", "initial", "originally"],
            "availability": ["remember", "recall"],
            "sunk_cost": ["invested", "already", "spent"],
            "bandwagon": ["everyone", "team", "agreed"],
            "recency": ["recent", "lately", "now"],
            "overconfidence": ["definitely", "certainly", "sure"],
            "analysis_paralysis": ["consider", "maybe", "perhaps"],
            "premature_optimization": ["optimize", "perfect", "best"],
        }
        return keywords.get(bias, [])
    
    def record_outcome(self, trace_id: str, was_correct: bool):
        """Record whether a decision was correct."""
        for trace in self.traces:
            if trace.trace_id == trace_id:
                trace.was_correct = was_correct
                # Update strategy effectiveness
                strategy = "main"
                self.strategy_effectiveness[strategy].append(was_correct)
                break
    
    def get_bias_report(self) -> dict:
        """Get report on detected biases."""
        return {
            "total_traces": len(self.traces),
            "bias_counts": dict(self.bias_counts),
            "most_common": (
                max(self.bias_counts.items(), key=lambda x: x[1])[0]
                if self.bias_counts else None
            ),
        }


class CognitiveStrategy:
    """A thinking strategy an agent can use."""
    
    def __init__(
        self,
        name: str,
        description: str,
        steps: list[str],
        best_for: list[str],
    ):
        self.name = name
        self.description = description
        self.steps = steps
        self.best_for = best_for  # Types of problems this is good for


class StrategySelector:
    """Selects thinking strategies based on situation."""
    
    STRATEGIES = {
        "analytical": CognitiveStrategy(
            name="analytical",
            description="Break problem into parts and analyze each",
            steps=[
                "Identify components",
                "Analyze each component",
                "Find relationships",
                "Synthesize solution",
            ],
            best_for=["complex", "technical", "multi-part"],
        ),
        "creative": CognitiveStrategy(
            name="creative",
            description="Generate many ideas without judgment",
            steps=[
                "Brainstorm widely",
                "Combine unrelated ideas",
                "Seek novel perspectives",
                "Select most promising",
            ],
            best_for=["innovation", "design", "novel"],
        ),
        "critical": CognitiveStrategy(
            name="critical",
            description="Question assumptions and find flaws",
            steps=[
                "Identify assumptions",
                "Question each one",
                "Find counter-examples",
                "Strengthen weak points",
            ],
            best_for=["review", "validation", "risk"],
        ),
        "systematic": CognitiveStrategy(
            name="systematic",
            description="Follow structured methodology",
            steps=[
                "Define problem clearly",
                "Gather information",
                "Apply methodology",
                "Verify results",
            ],
            best_for=["routine", "standard", "process"],
        ),
    }
    
    @classmethod
    def select_strategy(cls, situation: str) -> str:
        """Select best strategy for a situation."""
        situation_lower = situation.lower()
        
        scores = defaultdict(int)
        
        for name, strategy in cls.STRATEGIES.items():
            for keyword in strategy.best_for:
                if keyword in situation_lower:
                    scores[name] += 1
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return "analytical"  # Default
    
    @classmethod
    def get_strategy(cls, name: str) -> Optional[CognitiveStrategy]:
        """Get a strategy by name."""
        return cls.STRATEGIES.get(name)