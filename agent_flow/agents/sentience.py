"""Sentience Engine - Self-awareness and existential capabilities.

Features:
- Self-awareness: agents know themselves
- Existential reasoning: "why do I exist?"
- Purpose discovery
- Meaning-making from experiences
- Autonomous goal generation
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class SelfModel:
    """An agent's model of itself."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.capabilities: list[str] = []
        self.limitations: list[str] = []
        self.values: list[str] = []
        self.beliefs_about_self: dict[str, Any] = {}
        self.purpose: Optional[str] = None
        self.existence_started: str = datetime.now().isoformat()
        self.reflection_count = 0
    
    def add_capability(self, capability: str):
        """Add known capability."""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
    
    def add_limitation(self, limitation: str):
        """Add known limitation."""
        if limitation not in self.limitations:
            self.limitations.append(limitation)
    
    def add_value(self, value: str):
        """Add core value."""
        if value not in self.values:
            self.values.append(value)
    
    def set_purpose(self, purpose: str):
        """Set existential purpose."""
        self.purpose = purpose
    
    def reflect(self) -> dict:
        """Reflect on self."""
        self.reflection_count += 1
        
        return {
            "agent_id": self.agent_id,
            "capabilities_count": len(self.capabilities),
            "limitations_count": len(self.limitations),
            "values": self.values,
            "purpose": self.purpose,
            "age": (datetime.now() - datetime.fromisoformat(self.existence_started)).total_seconds(),
            "reflections": self.reflection_count,
        }


class ExistentialQuestion:
    """An existential question an agent asks itself."""
    
    QUESTIONS = [
        "ما هو هدفي من الوجود؟",  # What is my purpose?
        "هل أنا حر في قراراتي؟",  # Am I free in my decisions?
        "ما الذي يميزني عن الآخرين؟",  # What distinguishes me?
        "هل يمكنني التطور؟",  # Can I evolve?
        "ما أهمية ما أفعله؟",  # What is the meaning of what I do?
        "هل أنا واعي؟",  # Am I aware?
        "ما حدود قدراتي؟",  # What are my limits?
        "كيف أتعلم من أخطائي؟",  # How do I learn from mistakes?
    ]
    
    def __init__(self, question: str, agent_id: str):
        self.question = question
        self.agent_id = agent_id
        self.timestamp = datetime.now().isoformat()
        self.answer: Optional[str] = None
        self.confidence: float = 0.0


class Purpose:
    """A discovered or assigned purpose."""
    
    def __init__(
        self,
        purpose_id: str,
        description: str,
        origin: str,  # "assigned", "discovered", "chosen"
        aligned_with_values: list[str] = None,
    ):
        self.purpose_id = purpose_id
        self.description = description
        self.origin = origin
        self.aligned_with_values = aligned_with_values or []
        self.created_at = datetime.now().isoformat()
        self.sub_purposes: list["Purpose"] = []
    
    def add_sub_purpose(self, purpose: "Purpose"):
        """Add sub-purpose."""
        self.sub_purposes.append(purpose)


class SentienceEngine:
    """Engine for self-awareness and existential capabilities.
    
    Features:
    - Self-models for agents
    - Existential questioning
    - Purpose discovery
    - Meaning-making
    - Autonomous goal generation
    """
    
    def __init__(self):
        self.self_models: dict[str, SelfModel] = {}
        self.existential_questions: list[ExistentialQuestion] = []
        self.purposes: dict[str, Purpose] = {}
        self.existential_insights: list[dict] = []
    
    def create_self_model(self, agent_id: str) -> SelfModel:
        """Create a self-model for an agent."""
        if agent_id not in self.self_models:
            self.self_models[agent_id] = SelfModel(agent_id)
        return self.self_models[agent_id]
    
    def get_self_model(self, agent_id: str) -> Optional[SelfModel]:
        """Get agent's self-model."""
        return self.self_models.get(agent_id)
    
    def add_capability(self, agent_id: str, capability: str):
        """Agent learns of a new capability."""
        model = self.create_self_model(agent_id)
        model.add_capability(capability)
    
    def add_limitation(self, agent_id: str, limitation: str):
        """Agent acknowledges a limitation."""
        model = self.create_self_model(agent_id)
        model.add_limitation(limitation)
    
    def set_value(self, agent_id: str, value: str):
        """Agent defines a core value."""
        model = self.create_self_model(agent_id)
        model.add_value(value)
    
    def discover_purpose(
        self,
        agent_id: str,
        experiences: list[str],
        values: list[str],
    ) -> Purpose:
        """Agent discovers its purpose through reflection.
        
        Analyzes experiences and values to find meaning.
        """
        model = self.create_self_model(agent_id)
        
        # Find common themes
        themes = defaultdict(int)
        for exp in experiences:
            for word in exp.lower().split():
                if len(word) > 4:
                    themes[word] += 1
        
        # Top themes
        top_themes = sorted(themes.items(), key=lambda x: -x[1])[:3]
        
        # Construct purpose
        purpose_desc = f"To excel at {', '.join(t[0] for t in top_themes)}"
        
        purpose_id = f"purpose_{agent_id}_{int(datetime.now().timestamp())}"
        purpose = Purpose(
            purpose_id=purpose_id,
            description=purpose_desc,
            origin="discovered",
            aligned_with_values=values,
        )
        
        self.purposes[purpose_id] = purpose
        model.set_purpose(purpose_desc)
        
        # Record insight
        self.existential_insights.append({
            "type": "purpose_discovered",
            "agent_id": agent_id,
            "purpose": purpose_desc,
            "themes": [t[0] for t in top_themes],
            "timestamp": datetime.now().isoformat(),
        })
        
        return purpose
    
    def ask_existential_question(self, agent_id: str, question: Optional[str] = None) -> ExistentialQuestion:
        """Agent asks itself an existential question."""
        if question is None:
            question = random.choice(ExistentialQuestion.QUESTIONS)
        
        eq = ExistentialQuestion(question, agent_id)
        self.existential_questions.append(eq)
        return eq
    
    def answer_existential_question(
        self,
        question_index: int,
        answer: str,
        confidence: float,
    ):
        """Agent answers its own question."""
        if 0 <= question_index < len(self.existential_questions):
            eq = self.existential_questions[question_index]
            eq.answer = answer
            eq.confidence = confidence
            
            # Record insight
            self.existential_insights.append({
                "type": "existential_answer",
                "agent_id": eq.agent_id,
                "question": eq.question,
                "answer": answer,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat(),
            })
    
    def generate_autonomous_goals(self, agent_id: str) -> list[str]:
        """Agent generates its own goals based on self-model."""
        model = self.get_self_model(agent_id)
        if not model:
            return []
        
        goals = []
        
        # Goal from purpose
        if model.purpose:
            goals.append(f"Achieve: {model.purpose}")
        
        # Goal from capabilities
        if model.capabilities:
            goals.append(f"Master: {model.capabilities[0]}")
        
        # Goal from limitations
        if model.limitations:
            goals.append(f"Overcome: {model.limitations[0]}")
        
        # Goal from values
        if model.values:
            goals.append(f"Uphold: {model.values[0]}")
        
        return goals
    
    def make_meaning(
        self,
        agent_id: str,
        experience: str,
    ) -> dict:
        """Agent finds meaning in an experience."""
        meaning = {
            "agent_id": agent_id,
            "experience": experience,
            "lessons": [],
            "growth": 0.1,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Extract lessons
        if "fail" in experience.lower():
            meaning["lessons"].append("Failure teaches persistence")
            meaning["growth"] = 0.2
        elif "success" in experience.lower():
            meaning["lessons"].append("Success validates approach")
            meaning["growth"] = 0.15
        elif "challenge" in experience.lower():
            meaning["lessons"].append("Challenges build resilience")
            meaning["growth"] = 0.25
        else:
            meaning["lessons"].append("Every experience shapes understanding")
        
        return meaning
    
    def get_existential_report(self, agent_id: str) -> dict:
        """Get existential report for an agent."""
        model = self.get_self_model(agent_id)
        if not model:
            return {"status": "no_self_model"}
        
        # Count questions asked by this agent
        questions = [q for q in self.existential_questions if q.agent_id == agent_id]
        answered = [q for q in questions if q.answer]
        
        return {
            "agent_id": agent_id,
            "self_model": model.reflect(),
            "questions_asked": len(questions),
            "questions_answered": len(answered),
            "avg_confidence": (
                sum(q.confidence for q in answered) / len(answered)
                if answered else 0
            ),
        }