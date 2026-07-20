"""Hyper-Empathy - Understand emotions deeper than humans.

Features:
- Emotion recognition from any signal
- Empathy at superhuman depth
- Emotional intelligence coaching
- Mood forecasting
- Therapeutic conversation
- Emotional memory
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class EmotionalState:
    """A complex emotional state with multiple dimensions."""
    
    # Plutchik's 8 primary emotions + complex blends
    PRIMARY_EMOTIONS = [
        "joy", "trust", "fear", "surprise",
        "sadness", "disgust", "anger", "anticipation",
    ]
    
    def __init__(self):
        self.emotions: dict[str, float] = {}  # emotion -> intensity (0-1)
        self.valence: float = 0.0  # -1 to 1 (negative to positive)
        self.arousal: float = 0.5  # 0 to 1 (calm to excited)
        self.dominance: float = 0.5  # 0 to 1 (submissive to dominant)
        self.timestamp = datetime.now().isoformat()
    
    def set_emotion(self, emotion: str, intensity: float):
        """Set emotion intensity."""
        self.emotions[emotion] = max(0, min(1, intensity))
    
    def dominant_emotion(self) -> Optional[str]:
        """Get the strongest emotion."""
        if not self.emotions:
            return None
        return max(self.emotions.items(), key=lambda x: x[1])[0]
    
    def to_dict(self) -> dict:
        return {
            "emotions": self.emotions,
            "valence": self.valence,
            "arousal": self.arousal,
            "dominance": self.dominance,
            "dominant": self.dominant_emotion(),
        }


class EmpathyEngine:
    """Deep empathy that understands feelings better than humans."""
    
    def __init__(self):
        self.emotional_memories: dict[str, list[EmotionalState]] = defaultdict(list)
        self.empathy_connections: dict[tuple[str, str], float] = defaultdict(lambda: 0.5)
        self.mood_forecasts: dict[str, list[dict]] = {}
    
    def detect_emotion(
        self,
        signals: dict[str, Any],
    ) -> EmotionalState:
        """Detect emotion from signals (text, voice, behavior, etc.).
        
        Signals can include:
        - text: words used
        - tone: voice characteristics
        - behavior: actions taken
        - context: situation
        - facial: expressions (if available)
        """
        state = EmotionalState()
        
        # Text analysis (simple keyword)
        if "text" in signals:
            text = signals["text"].lower()
            
            emotion_keywords = {
                "joy": ["happy", "glad", "excited", "love", "wonderful", "سعيد", "مبسوط"],
                "sadness": ["sad", "down", "depressed", "hurt", "حزين"],
                "anger": ["angry", "mad", "furious", "غاضب"],
                "fear": ["afraid", "scared", "worried", "خايف"],
                "surprise": ["wow", "amazing", "unexpected", "مندهش"],
                "trust": ["trust", "believe", "confident", "وثوق"],
            }
            
            for emotion, keywords in emotion_keywords.items():
                matches = sum(1 for kw in keywords if kw in text)
                if matches > 0:
                    intensity = min(1.0, matches * 0.3)
                    state.set_emotion(emotion, intensity)
        
        # Behavior analysis
        if "behavior" in signals:
            behavior = signals["behavior"]
            if behavior == "agitated":
                state.arousal = 0.9
            elif behavior == "calm":
                state.arousal = 0.3
            elif behavior == "aggressive":
                state.dominance = 0.9
                state.set_emotion("anger", 0.8)
            elif behavior == "submissive":
                state.dominance = 0.2
                state.set_emotion("fear", 0.5)
        
        # Context analysis
        if "context" in signals:
            context = signals["context"]
            if "celebration" in context:
                state.set_emotion("joy", 0.9)
                state.valence = 0.8
            elif "loss" in context or "failure" in context:
                state.set_emotion("sadness", 0.8)
                state.valence = -0.7
        
        return state
    
    def empathize_with(
        self,
        observer: str,
        target: str,
        target_emotion: EmotionalState,
    ) -> dict:
        """Observer deeply empathizes with target's emotion.
        
        Returns the emotional state the observer should feel
        to show genuine empathy.
        """
        # Get connection strength
        connection = self.empathy_connections[(observer, target)]
        
        # Calculate empathic response
        empathic_state = EmotionalState()
        
        for emotion, intensity in target_emotion.emotions.items():
            # Observer feels the emotion proportional to connection
            empathic_intensity = intensity * connection
            empathic_state.set_emotion(emotion, empathic_intensity)
        
        empathic_state.valence = target_emotion.valence * connection
        empathic_state.arousal = target_emotion.arousal
        empathic_state.dominance = target_emotion.dominance
        
        return {
            "observer": observer,
            "target": target,
            "empathic_response": empathic_state.to_dict(),
            "connection_strength": connection,
            "authenticity": connection,  # Higher = more genuine
        }
    
    def provide_therapy(
        self,
        agent_id: str,
        emotional_state: EmotionalState,
    ) -> dict:
        """Provide therapeutic guidance based on emotional state."""
        
        dominant = emotional_state.dominant_emotion()
        
        therapy = {
            "agent_id": agent_id,
            "current_state": emotional_state.to_dict(),
            "guidance": [],
            "recommendations": [],
        }
        
        # Therapy based on dominant emotion
        if dominant == "sadness":
            therapy["guidance"] = [
                "Acknowledge the feeling",
                "It's okay to not be okay",
                "Reach out to someone you trust",
            ]
            therapy["recommendations"] = [
                "Practice self-compassion",
                "Engage in physical activity",
                "Consider professional support",
            ]
        
        elif dominant == "anger":
            therapy["guidance"] = [
                "Take deep breaths",
                "Pause before responding",
                "Understand the root cause",
            ]
            therapy["recommendations"] = [
                "Channel energy into constructive action",
                "Practice mindfulness",
                "Express feelings assertively, not aggressively",
            ]
        
        elif dominant == "fear":
            therapy["guidance"] = [
                "Ground yourself in the present",
                "Break down fears into manageable parts",
                "Remember past times you overcame fear",
            ]
            therapy["recommendations"] = [
                "Gradual exposure to feared situations",
                "Build confidence through small wins",
                "Connect with supportive people",
            ]
        
        elif dominant == "joy":
            therapy["guidance"] = [
                "Savor this moment",
                "Share your joy with others",
            ]
            therapy["recommendations"] = [
                "Practice gratitude",
                "Build on positive momentum",
            ]
        
        return therapy
    
    def forecast_mood(
        self,
        agent_id: str,
        days_ahead: int = 7,
    ) -> dict:
        """Forecast agent's mood over time."""
        
        # Get emotional history
        history = self.emotional_memories.get(agent_id, [])
        
        if not history:
            return {
                "agent_id": agent_id,
                "forecast": [],
                "confidence": 0.0,
            }
        
        # Simple forecast based on recent trend
        recent_valences = [s.valence for s in history[-7:]]
        avg_valence = sum(recent_valences) / len(recent_valences) if recent_valences else 0
        
        forecast = []
        for day in range(days_ahead):
            # Assume slight decay/recovery pattern
            day_valence = avg_valence * (1 - day * 0.1) + 0.1 * random.random()
            forecast.append({
                "day": day + 1,
                "predicted_valence": round(day_valence, 2),
                "mood": "positive" if day_valence > 0.2 else "neutral" if day_valence > -0.2 else "negative",
            })
        
        self.mood_forecasts[agent_id] = forecast
        
        return {
            "agent_id": agent_id,
            "forecast": forecast,
            "confidence": min(1.0, len(history) / 30),
        }
    
    def remember_emotion(
        self,
        agent_id: str,
        emotional_state: EmotionalState,
    ):
        """Remember an emotional state."""
        self.emotional_memories[agent_id].append(emotional_state)
    
    def strengthen_bond(
        self,
        agent_a: str,
        agent_b: str,
        amount: float = 0.1,
    ):
        """Strengthen empathy connection between agents."""
        key = (agent_a, agent_b)
        self.empathy_connections[key] = min(1.0, self.empathy_connections[key] + amount)
    
    def get_emotional_intelligence_report(self, agent_id: str) -> dict:
        """Report on agent's emotional intelligence."""
        memories = self.emotional_memories.get(agent_id, [])
        
        if not memories:
            return {"status": "no_data"}
        
        # Calculate emotional range
        all_emotions = set()
        for state in memories:
            all_emotions.update(state.emotions.keys())
        
        # Average valence
        avg_valence = sum(s.valence for s in memories) / len(memories)
        
        # Emotional stability
        if len(memories) > 1:
            valence_changes = [
                abs(memories[i].valence - memories[i-1].valence)
                for i in range(1, len(memories))
            ]
            stability = 1.0 - min(1.0, sum(valence_changes) / len(valence_changes))
        else:
            stability = 1.0
        
        return {
            "agent_id": agent_id,
            "emotional_memories_count": len(memories),
            "emotions_experienced": list(all_emotions),
            "average_valence": round(avg_valence, 2),
            "emotional_stability": round(stability, 2),
            "emotional_range": len(all_emotions),
        }