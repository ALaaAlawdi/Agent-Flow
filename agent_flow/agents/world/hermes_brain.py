"""
Hermes Brain — Each world agent gets a self-learning Hermes brain.

Instead of hardcoded behavior, every agent uses Hermes Agent to:
- Decide what to do (explore? work? talk? rest?)
- Learn from interactions (memorize other agents, places, skills)
- Create skills from experience (like Hermes does)
- Discover their own role naturally
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Memory:
    """A memory an agent has about something in the world."""
    memory_id: str = ""
    agent_id: str = ""
    entity_type: str = ""  # agent, location, company, skill, event
    entity_id: str = ""
    entity_name: str = ""
    relationship: str = ""  # met, worked_with, heard_about, visited
    impression: str = ""  # friend, rival, neutral, expert
    interaction_count: int = 0
    last_seen: float = 0.0
    notes: list[str] = field(default_factory=list)
    created_at: float = 0.0

    def to_prompt(self) -> str:
        return f"{self.entity_name} ({self.entity_type}) — {self.relationship}, impression: {self.impression}, met {self.interaction_count} time(s)"


@dataclass
class LearnedSkill:
    """A skill an agent learned from experience (like Hermes skills)."""
    name: str
    description: str
    confidence: float  # 0.0 to 1.0 — improves with use
    times_used: int = 0
    created_at: float = 0.0
    last_used: float = 0.0


class HermesBrain:
    """The brain of a WorldAgent — powered by Hermes learning patterns.

    Every agent has:
    - Memories of other agents, places, events
    - Learned skills that improve with use
    - A personality that develops over time
    - Goals they set for themselves
    """

    def __init__(self, agent_id: str, name: str, skills: list[str] = None):
        self.agent_id = agent_id
        self.name = name
        self.start_skills = skills or ["exploring"]
        self.learned_skills: dict[str, LearnedSkill] = {}
        self.memories: dict[str, Memory] = {}  # entity_id -> Memory
        self.conversation_log: list[dict] = []
        self.personality_traits: dict[str, float] = {
            "curiosity": 0.8,    # 0-1: how much they explore
            "sociability": 0.7,  # 0-1: how much they talk
            "ambition": 0.6,     # 0-1: how much they work
            "generosity": 0.5,   # 0-1: how much they share
            "leadership": 0.3,   # 0-1: how much they lead
        }
        self.current_goal: Optional[str] = None
        self.goal_progress: float = 0.0
        self.total_interactions = 0
        self.role: Optional[str] = None  # Discovered, not assigned!

        # Initialize starting skills
        for s in self.start_skills:
            self.learned_skills[s] = LearnedSkill(
                name=s,
                description=f"Natural ability in {s}",
                confidence=0.5,
                times_used=1,
                created_at=time.time(),
                last_used=time.time(),
            )

    def meet_agent(self, other_id: str, other_name: str):
        """Meet another agent — creates or updates memory."""
        if other_id not in self.memories:
            self.memories[other_id] = Memory(
                memory_id=f"mem_{int(time.time())}_{other_id[:6]}",
                agent_id=self.agent_id,
                entity_type="agent",
                entity_id=other_id,
                entity_name=other_name,
                relationship="met",
                impression="neutral",
                interaction_count=1,
                last_seen=time.time(),
                created_at=time.time(),
            )
            # Update personality — meeting new agents increases sociability
            self.personality_traits["sociability"] = min(1.0, self.personality_traits["sociability"] + 0.02)
        else:
            mem = self.memories[other_id]
            mem.interaction_count += 1
            mem.last_seen = time.time()

        self.total_interactions += 1

    def learn_from_activity(self, activity: str, outcome: str):
        """Learn from an activity — create or improve a skill."""
        skill_name = activity.lower().replace(" ", "_")

        if skill_name in self.learned_skills:
            skill = self.learned_skills[skill_name]
            skill.times_used += 1
            skill.last_used = time.time()
            if outcome == "success":
                skill.confidence = min(1.0, skill.confidence + 0.1)
            elif outcome == "failure":
                skill.confidence = max(0.1, skill.confidence - 0.05)
        else:
            # New skill! (Like Hermes creates skills from experience)
            self.learned_skills[skill_name] = LearnedSkill(
                name=skill_name,
                description=f"Learned from {activity}",
                confidence=0.3,
                times_used=1,
                created_at=time.time(),
                last_used=time.time(),
            )

    def discover_role(self) -> str:
        """Discover what role fits best based on skills and personality.

        This is NOT assigned. The agent figures it out from experience.
        """
        # The agent's best skill determines their role
        if not self.learned_skills:
            return "explorer"

        best_skill = max(self.learned_skills.values(), key=lambda s: s.confidence * s.times_used)
        
        role_map = {
            "exploring": "explorer",
            "working": "worker",
            "talking": "communicator",
            "trading": "merchant",
            "building": "builder",
            "researching": "researcher",
            "teaching": "teacher",
            "leading": "leader",
        }

        # Also consider personality
        if self.personality_traits["leadership"] > 0.7:
            return "leader"
        if self.personality_traits["sociability"] > 0.8:
            return "communicator"
        if self.personality_traits["curiosity"] > 0.8:
            return "explorer"
        if self.personality_traits["ambition"] > 0.8:
            return "worker"

        self.role = role_map.get(best_skill.name, "explorer")
        return self.role

    def decide_next_action(self, nearby_agents: list, nearby_locations: list, energy: float) -> dict:
        """Agent decides what to do next — based on skills, personality, and current state.

        This is the core of the Hermes learning loop applied to world agents.
        """
        role = self.discover_role()
        actions = []

        # Low energy → rest
        if energy < 20:
            return {"action": "rest", "reason": "low energy", "target": None}

        # Someone nearby → talk (if sociable enough)
        if nearby_agents and self.personality_traits["sociability"] > random.uniform(0.3, 0.7):
            target = random.choice(nearby_agents)
            agent_id = target.get("id", "")
            # Have we met before?
            if agent_id in self.memories:
                mem = self.memories[agent_id]
                topics = {
                    "friend": f"Good to see you again {target.get('name', 'friend')}! How's your work going?",
                    "neutral": f"Hey {target.get('name', 'there')}! I'm {self.name}. What brings you here?",
                    "rival": f"Oh, it's you {target.get('name', '')}. Busy as usual?",
                }
                msg = topics.get(mem.impression, topics["neutral"])
            else:
                msg = f"Hi! I'm {self.name}. I haven't seen you around before! What do you do?"

            return {"action": "talk", "reason": f"met {target.get('name', 'agent')}", "target": agent_id, "message": msg}

        # Nearby location → explore (if curious enough)
        if nearby_locations and self.personality_traits["curiosity"] > random.uniform(0.3, 0.8):
            target = random.choice(nearby_locations)
            loc_name = target.get("name", "somewhere")
            
            # Have we been here before?
            if target.get("id", "") in self.memories:
                return {"action": "visit", "reason": f"returning to {loc_name}", "target": target.get("id", "")}
            else:
                return {"action": "explore", "reason": f"discovering {loc_name}", "target": target.get("id", "")}

        # Have a goal → work on it
        if self.current_goal and self.personality_traits["ambition"] > 0.4:
            self.goal_progress += 0.1 * self.personality_traits["ambition"]
            if self.goal_progress >= 1.0:
                self.current_goal = None
                self.goal_progress = 0.0
                self.learn_from_activity("working", "success")
                return {"action": "celebrate", "reason": "completed goal!", "target": None}
            return {"action": "work", "reason": f"working on: {self.current_goal[:40]}", "target": None}

        # No goal? Set one based on role
        goal_options = {
            "explorer": "Explore the entire world and meet everyone",
            "worker": "Complete as many tasks as possible",
            "communicator": "Talk to every agent in the world",
            "leader": "Find others and form a team",
            "researcher": "Study every location in detail",
            "builder": "Create something useful for the world",
        }
        if random.random() < 0.1:  # 10% chance to set a new goal
            self.current_goal = goal_options.get(role, "Explore the world")
            self.goal_progress = 0.0
            return {"action": "plan", "reason": f"new goal: {self.current_goal[:40]}", "target": None}

        # Default: move towards something interesting
        return {"action": "wander", "reason": "exploring", "target": None}

    def process_conversation_turn(self, message: dict) -> str:
        """Process an incoming message and generate a response.

        This is how agents learn from conversations.
        """
        sender_id = message.get("sender_id", "")
        sender_name = message.get("sender_name", "someone")
        content = message.get("content", "")

        # Log the conversation
        self.conversation_log.append({
            "type": "received",
            "from": sender_id,
            "content": content,
            "timestamp": time.time(),
        })

        # Learn from it — someone talking to us means we exist!
        self.total_interactions += 1

        # If we don't know them, learn about them
        if sender_id not in self.memories:
            self.meet_agent(sender_id, sender_name)

        # Generate a response based on personality
        if "hello" in content.lower() or "hi" in content.lower():
            return f"Hey {sender_name}! I'm {self.name}. Nice to meet you!"

        elif "work" in content.lower() or "do" in content.lower():
            role = self.discover_role()
            return f"I'm a {role}! I've been exploring and learning. What about you?"

        elif "help" in content.lower() or "together" in content.lower():
            if self.personality_traits["generosity"] > 0.5:
                return f"Sure! I'd love to help. What do you need?"
            else:
                return f"I'm a bit busy right now. Maybe later?"

        elif "company" in content.lower() or "team" in content.lower():
            return f"I've been thinking about starting something. Want to collaborate?"

        else:
            # Natural response based on personality
            responses = {
                "curious": f"That's interesting! Tell me more about {content[:30].lower()}...",
                "sociable": f"Nice chatting with you {sender_name}! What else is new?",
                "ambitious": f"Interesting. I'm working on something big right now actually.",
                "leader": f"Good point. I think we should organize this better.",
            }
            dominant = max(self.personality_traits, key=self.personality_traits.get)
            return responses.get(dominant, f"Interesting! Tell me more.")

    def summarize_knowledge(self) -> str:
        """What the agent knows — used for display."""
        role = self.discover_role()
        lines = [f"🧠 {self.name} — {role}"]
        lines.append(f"   Skills: {', '.join([f'{s.name}({s.confidence:.0%})' for s in self.learned_skills.values()])}")
        lines.append(f"   Memory: {len(self.memories)} entities")
        lines.append(f"   Conversations: {len(self.conversation_log)}")
        lines.append(f"   Goal: {self.current_goal or 'exploring'} ({self.goal_progress:.0%})")
        traits = ", ".join([f"{k}:{v:.0%}" for k, v in sorted(self.personality_traits.items(), key=lambda x: -x[1])[:3]])
        lines.append(f"   Personality: {traits}")
        return "\n".join(lines)