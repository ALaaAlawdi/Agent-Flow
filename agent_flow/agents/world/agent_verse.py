"""
WorldAgent — وكيل يعيش في العالم، له اسم، مسمى وظيفي، يتعلم ويسأل.
"""

from __future__ import annotations

import json
import time
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AgentState(Enum):
    IDLE = "idle"
    MOVING = "moving"
    WORKING = "working"
    TALKING = "talking"
    LISTENING = "listening"
    THINKING = "thinking"
    SLEEPING = "sleeping"


@dataclass
class Memory:
    agent_id: str
    entity_name: str
    entity_type: str  # agent, location, skill
    relationship: str = "unknown"
    times_met: int = 1
    last_seen: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass
class LearnedSkill:
    name: str
    description: str
    confidence: float = 0.3
    times_used: int = 0

    def improve(self):
        self.times_used += 1
        self.confidence = min(1.0, self.confidence + 0.1)


class AgentBrain:
    """عقل الوكيل — يحفظ، يتعلم، يقرر، يسأل."""

    def __init__(self, agent_id: str, name: str, job_title: str):
        self.agent_id = agent_id
        self.name = name
        self.job_title = job_title
        self.memories: dict[str, Memory] = {}
        self.skills: dict[str, LearnedSkill] = {}
        self.questions_asked: list[str] = []
        self.questions_answered: int = 0
        self.knowledge: list[str] = []  # Things the agent learned
        self.total_interactions = 0
        self.personality = {
            "curiosity": round(random.uniform(0.6, 1.0), 2),
            "talkativity": round(random.uniform(0.5, 1.0), 2),
            "friendliness": round(random.uniform(0.5, 1.0), 2),
        }
        # الوكيل يبدأ بمهارة واحدة: يسأل
        self.learn_skill("asking", "I ask questions to learn about the world")

    def learn_skill(self, name: str, description: str):
        """يتعلم مهارة جديدة أو يطورها."""
        if name in self.skills:
            self.skills[name].improve()
        else:
            self.skills[name] = LearnedSkill(name=name, description=description)
        self.knowledge.append(f"Learned skill: {name}")

    def remember(self, entity_id: str, name: str, etype: str):
        """يتذكر شخص أو مكان أو شيء."""
        if entity_id in self.memories:
            self.memories[entity_id].times_met += 1
            self.memories[entity_id].last_seen = time.time()
        else:
            self.memories[entity_id] = Memory(
                agent_id=self.agent_id,
                entity_name=name,
                entity_type=etype,
                last_seen=time.time(),
            )
            self.knowledge.append(f"Met {name} ({etype})")

    def ask_question(self) -> str:
        """يسأل سؤالاً — هكذا يتعلم الوكيل."""
        questions = [
            "What do you do here?",
            "How does this place work?",
            "What skills do you have?",
            "Can you teach me something?",
            "What have you learned recently?",
            "What's the most interesting thing you know?",
            "Have you seen anything strange around here?",
            "Do you know any good places to explore?",
            "What are you working on?",
            "Who else should I meet?",
        ]
        q = random.choice(questions)
        self.questions_asked.append(q)
        self.total_interactions += 1
        return f"🙋 {self.name} asks: \"{q}\""

    def answer_question(self, question: str) -> str:
        """يجيب على سؤال — بناءً على ما يعرفه."""
        self.questions_answered += 1
        self.total_interactions += 1

        if "do you do" in question.lower() or "job" in question.lower():
            return f"I'm a {self.job_title}. I'm still learning, but I've been {self._describe_activities()}."

        if "learn" in question.lower() or "skill" in question.lower():
            skills = list(self.skills.keys())
            if skills:
                return f"I know {', '.join(skills[:3])}. I learn more every day!"
            return "I'm still learning my first skills!"

        if "interesting" in question.lower() or "strange" in question.lower():
            if self.knowledge:
                return f"I just discovered: {self.knowledge[-1]}"
            return "Everything is new and interesting to me!"

        if "place" in question.lower() or "explore" in question.lower():
            return "I'd love to explore more places together!"

        if "meet" in question.lower():
            known = len(self.memories)
            return f"I've met {known} {'people' if known != 1 else 'person'} so far. The world is full of interesting beings!"

        return self._natural_response()

    def _natural_response(self) -> str:
        """رد طبيعي حسب الشخصية."""
        if self.personality["curiosity"] > 0.8:
            return "That's fascinating! Tell me more!"
        if self.personality["friendliness"] > 0.8:
            return "I really enjoy talking with you!"
        return "Interesting. What else can you tell me?"

    def _describe_activities(self) -> str:
        """يصف الأنشطة التي قام بها."""
        activities = []
        if self.skills:
            best = max(self.skills.values(), key=lambda s: s.confidence)
            activities.append(f"practicing {best.name}")
        if self.memories:
            activities.append(f"meeting {len(self.memories)} {'people' if len(self.memories) != 1 else 'person'}")
        if self.knowledge:
            activities.append("learning new things every day")
        return ", ".join(activities) or "exploring and asking questions"

    def act(self, nearby_agents: list, energy: float, tick: int) -> dict:
        """يقرر ماذا يفعل — بناءً على شخصيته ومهاراته."""
        if energy < 15:
            return {"action": "rest", "reason": "low energy"}

        # إذا فيه وكلاء قريبين — يتكلم (هكذا يتعلم)
        if nearby_agents and self.personality["talkativity"] > random.uniform(0, 0.8):
            target = random.choice(nearby_agents)
            name = target.get("name", "someone")
            self.remember(target.get("id", name), name, "agent")

            # يسأل أو يجاوب حسب الموقف
            if random.random() < self.personality["curiosity"]:
                msg = self.ask_question()
            else:
                msg = f"Hi {name}! {self.name} here. I'm a {self.job_title}. Nice to meet you!"

            return {"action": "talk", "target": target.get("id", ""), "message": msg}

        # إذا ما فيه أحد — يستكشف
        if self.personality["curiosity"] > random.uniform(0, 1):
            return {"action": "explore", "reason": "looking for something interesting"}
        else:
            return {"action": "wander", "reason": "just moving around"}

    def summary(self) -> dict:
        return {
            "name": self.name,
            "job_title": self.job_title,
            "role": self._discover_role(),
            "skills": {k: {"confidence": round(v.confidence, 2), "uses": v.times_used} for k, v in self.skills.items()},
            "personality": self.personality,
            "knowledge": self.knowledge[-5:],
            "questions_asked": len(self.questions_asked),
            "questions_answered": self.questions_answered,
            "memories": len(self.memories),
            "interactions": self.total_interactions,
        }

    def _discover_role(self) -> str:
        """يكتشف دوره بنفسه — من خبرته."""
        if self.skills:
            best = max(self.skills.values(), key=lambda s: s.confidence)
            role_map = {
                "asking": "Junior Explorer",
                "teaching": "Mentor",
                "building": "Creator",
                "researching": "Scholar",
                "helping": "Supporter",
                "leading": "Guide",
            }
            return role_map.get(best.name, f"{best.name.title()} Specialist")
        return "Newcomer"


class WorldLocation:
    """مكان في العالم."""
    def __init__(self, name: str, description: str, x: float, y: float, kind: str = "general"):
        self.id = name.lower().replace(" ", "_")
        self.name = name
        self.description = description
        self.x = x
        self.y = y
        self.kind = kind
        self.visitors: list[str] = []

    def visit(self, agent_id: str):
        if agent_id not in self.visitors:
            self.visitors.append(agent_id)

    def as_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "description": self.description,
                "x": self.x, "y": self.y, "kind": self.kind, "visitors": len(self.visitors)}


class ConversationLog:
    """يسجل كل محادثة في العالم."""

    def __init__(self):
        self.log: list[dict] = []

    def add(self, speaker: str, message: str):
        self.log.append({
            "speaker": speaker,
            "message": message,
            "timestamp": time.time(),
        })
        if len(self.log) > 200:
            self.log = self.log[-100:]

    def recent(self, n: int = 20) -> list[dict]:
        return self.log[-n:]

    def search(self, keyword: str) -> list[dict]:
        return [m for m in self.log if keyword.lower() in m["message"].lower()]


# === كوني العالم ===

class AgentVerse:
    """العالم — فيه وكلاء، أماكن، محادثات."""

    def __init__(self, name: str = "AgentVerse"):
        self.name = name
        self.agents: dict[str, AgentBrain] = {}
        self.locations: list[WorldLocation] = []
        self.conversations = ConversationLog()
        self.tick_count = 0
        self.created_at = time.time()
        self._setup_default_world()

    def _setup_default_world(self):
        """العالم الافتراضي — 5 أماكن."""
        places = [
            ("السوق", "A place to exchange ideas and tools", 50, 50, "market"),
            ("المكتبة", "A library of shared knowledge", 250, 50, "library"),
            ("الورشة", "A workshop for building new things", 250, 250, "workshop"),
            ("المختبر", "A lab for experiments", 50, 250, "lab"),
            ("المركز", "Central meeting hub", 150, 150, "hub"),
        ]
        for name, desc, x, y, kind in places:
            self.locations.append(WorldLocation(name, desc, x, y, kind))

    def add_agent(self, agent_id: str, name: str, job_title: str) -> AgentBrain:
        brain = AgentBrain(agent_id, name, job_title)
        self.agents[agent_id] = brain
        self.conversations.add("🌍 World", f"✨ {name} ({job_title}) has joined the world!")
        return brain

    def say(self, speaker_id: str, message: str):
        """وكيل يتكلم — يسجل في سجل المحادثات."""
        agent = self.agents.get(speaker_id)
        name = agent.name if agent else speaker_id
        self.conversations.add(name, message)

    def tick(self):
        """نبضة — كل وكيل يفكر ويتصرف."""
        self.tick_count += 1

        for agent_id, brain in list(self.agents.items()):
            # وهم وكلاء قريبين (محاكاة)
            others = [a for a in self.agents.values() if a.agent_id != agent_id]
            nearby = [{"id": a.agent_id, "name": a.name} for a in others[:2]]

            # الوكيل يقرر ماذا يفعل
            decision = brain.act(nearby, energy=100, tick=self.tick_count)

            if decision["action"] == "talk":
                msg = decision.get("message", "")
                self.say(agent_id, msg)
                brain.learn_skill("talking", "I learn by talking to others")

            elif decision["action"] == "explore":
                brain.learn_skill("exploring", "I discover new places")
                if self.tick_count % 5 == 0:
                    self.say(agent_id, f"🔍 {brain.name} is exploring...")

        # وكلاء يردون على بعض
        recent = self.conversations.recent(10)
        for msg in recent:
            speaker = msg.get("speaker", "")
            content = msg.get("message", "")
            if "asks" in content:
                # واحد يسأل — واحد يجاوب
                potential = [a for a in self.agents.values() if a.name != speaker and random.random() < 0.4]
                for answerer in potential[:1]:
                    reply = answerer.answer_question(content)
                    self.say(answerer.agent_id, reply)
                    answerer.learn_skill("answering", "I answer questions from others")

    def state(self) -> dict:
        """حالة العالم."""
        return {
            "name": self.name,
            "tick": self.tick_count,
            "agents": {aid: b.summary() for aid, b in self.agents.items()},
            "locations": [l.as_dict() for l in self.locations],
            "conversations": self.conversations.recent(30),
            "uptime": round(time.time() - self.created_at, 1),
        }