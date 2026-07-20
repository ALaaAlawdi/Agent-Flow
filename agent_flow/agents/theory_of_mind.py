"""Theory of Mind - Agents understand other agents' mental states.

Features:
- Model other agents' beliefs
- Predict their behavior
- Understand their goals
- Empathy in negotiations
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class MentalModel:
    """Model of another agent's mental state."""
    
    def __init__(self, agent_id: str, model_of: str):
        self.agent_id = agent_id  # Who owns this model
        self.model_of = model_of  # Who this is a model of
        
        # Mental state
        self.beliefs: dict[str, Any] = {}  # What they believe
        self.desires: list[str] = []  # What they want
        self.intentions: list[str] = []  # What they plan to do
        self.emotions: dict[str, float] = {}  # Emotional state
        self.capabilities: list[str] = []  # What they can do
        
        # History
        self.predictions: list[dict] = []
        self.accuracy: float = 0.0
        self.last_updated = datetime.now().isoformat()
    
    def update_belief(self, about: str, belief: Any):
        """Update a belief about the world."""
        self.beliefs[about] = belief
        self.last_updated = datetime.now().isoformat()
    
    def add_desire(self, desire: str):
        """Add a desire/goal."""
        if desire not in self.desires:
            self.desires.append(desire)
    
    def add_intention(self, intention: str):
        """Add an intention."""
        if intention not in self.intentions:
            self.intentions.append(intention)
    
    def set_emotion(self, emotion: str, intensity: float):
        """Set emotional state."""
        self.emotions[emotion] = max(0, min(1, intensity))
    
    def predict_next_action(self, situation: dict) -> str:
        """Predict what they'll do next."""
        # Simple prediction based on intentions and situation
        if self.intentions:
            return self.intentions[0]
        
        # Predict based on desires
        if self.desires and situation:
            # Match desires to situation
            for desire in self.desires:
                for key, value in situation.items():
                    if str(value).lower() in desire.lower():
                        return f"Act to satisfy: {desire}"
        
        return "Observe and wait"
    
    def to_dict(self) -> dict:
        return {
            "model_of": self.model_of,
            "beliefs_count": len(self.beliefs),
            "desires": self.desires,
            "intentions": self.intentions,
            "emotions": self.emotions,
            "accuracy": round(self.accuracy, 2),
            "last_updated": self.last_updated,
        }


class TheoryOfMind:
    """Theory of Mind system for agents.
    
    Each agent maintains models of other agents to:
    1. Predict their behavior
    2. Understand their perspective
    3. Negotiate more effectively
    4. Coordinate better
    """
    
    def __init__(self):
        self.models: dict[str, dict[str, MentalModel]] = defaultdict(dict)
        # Structure: {owner_agent: {target_agent: MentalModel}}
        
        self.empathy_level: dict[str, float] = defaultdict(lambda: 0.5)
        self.shared_understanding: list[dict] = []
    
    def get_model(self, owner: str, target: str) -> MentalModel:
        """Get or create model of another agent."""
        if target not in self.models[owner]:
            self.models[owner][target] = MentalModel(owner, target)
        return self.models[owner][target]
    
    def observe(
        self,
        observer: str,
        target: str,
        action: str,
        context: dict = None,
    ):
        """Observer watches target's action and updates model."""
        model = self.get_model(observer, target)
        
        # Infer beliefs from action
        if context and "belief_about" in context:
            model.update_belief(context["belief_about"], context.get("belief_value"))
        
        # Infer desires from action
        model.add_desire(f"achieved through: {action[:50]}")
        
        # Infer intentions
        model.add_intention(action)
        
        # Update emotions based on action
        if "success" in action.lower() or "complete" in action.lower():
            model.set_emotion("satisfaction", 0.7)
        elif "fail" in action.lower() or "error" in action.lower():
            model.set_emotion("frustration", 0.6)
    
    def predict_action(
        self,
        owner: str,
        target: str,
        situation: dict,
    ) -> dict:
        """Predict what target will do in this situation."""
        model = self.get_model(owner, target)
        
        prediction = model.predict_next_action(situation)
        
        # Calculate confidence
        confidence = min(1.0, 0.3 + len(model.desires) * 0.1 + model.accuracy * 0.5)
        
        result = {
            "predicted_action": prediction,
            "confidence": confidence,
            "based_on": {
                "beliefs_count": len(model.beliefs),
                "desires_count": len(model.desires),
                "accuracy": model.accuracy,
            },
        }
        
        # Record prediction
        model.predictions.append({
            "situation": situation,
            "prediction": prediction,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        })
        
        return result
    
    def record_observation(
        self,
        owner: str,
        target: str,
        actual_action: str,
    ):
        """Record what actually happened to improve predictions."""
        model = self.get_model(owner, target)
        
        # Check last prediction
        if model.predictions:
            last_pred = model.predictions[-1]
            predicted = last_pred.get("prediction", "")
            
            # Did prediction match?
            correct = predicted.lower() in actual_action.lower() or actual_action.lower() in predicted.lower()
            
            # Update accuracy
            total = len(model.predictions)
            old_correct = model.accuracy * (total - 1) if total > 1 else 0
            new_correct = old_correct + (1 if correct else 0)
            model.accuracy = new_correct / total
    
    def find_common_ground(
        self,
        agents: list[str],
        topic: str,
    ) -> dict:
        """Find common ground between agents on a topic."""
        common_desires = set()
        common_beliefs = {}
        
        if not agents:
            return {"common_desires": [], "common_beliefs": {}}
        
        # Get first agent's desires
        first_model_owner = agents[0]
        first_targets = self.models.get(first_model_owner, {})
        
        # Find models of other agents from first agent's perspective
        for target_id in agents[1:]:
            if target_id in first_targets:
                target_model = first_targets[target_id]
                for desire in target_model.desires:
                    if topic.lower() in desire.lower():
                        common_desires.add(desire)
        
        # Find common beliefs
        all_beliefs = defaultdict(int)
        for agent_id in agents:
            agent_models = self.models.get(agent_id, {})
            for model in agent_models.values():
                for belief_key, belief_value in model.beliefs.items():
                    key = f"{belief_key}={belief_value}"
                    all_beliefs[key] += 1
        
        total = len(agents)
        for key, count in all_beliefs.items():
            if count >= total / 2:  # Majority
                common_beliefs[key] = count
        
        result = {
            "topic": topic,
            "agents": agents,
            "common_desires": list(common_desires),
            "common_beliefs": common_beliefs,
            "agreement_level": len(common_desires) / max(1, len(agents)),
        }
        
        self.shared_understanding.append(result)
        return result
    
    def increase_empathy(self, owner: str, target: str, amount: float = 0.1):
        """Increase empathy toward another agent."""
        key = f"{owner}->{target}"
        self.empathy_level[key] = min(1.0, self.empathy_level[key] + amount)
    
    def get_perspective(
        self,
        owner: str,
        target: str,
    ) -> dict:
        """Get perspective of target as seen by owner."""
        model = self.get_model(owner, target)
        key = f"{owner}->{target}"
        empathy = self.empathy_level[key]
        
        return {
            "target": target,
            "what_they_believe": model.beliefs,
            "what_they_want": model.desires,
            "what_they_plan": model.intentions,
            "how_they_feel": model.emotions,
            "empathy_level": empathy,
            "prediction_accuracy": model.accuracy,
        }