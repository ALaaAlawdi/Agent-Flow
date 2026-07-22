"""
Human Personality Engine — وكلاء يتعلمون من أخطائهم مثل البشر.

Every agent starts simple. Knows nothing. Learns from:
- Mistakes (errors → better next time)
- Questions (asking others → knowledge)
- Experience (trying things → skill improvement)
- Social learning (watching others → copying good patterns)

No pre-loaded knowledge. No hardcoded behavior. Just learning from error.
"""

from __future__ import annotations

import json
import os
import random
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def call_deepseek(prompt: str, timeout: int = 30) -> str:
    """Call DeepSeek via Hermes CLI. Cached for repeated queries."""
    # Simple cache for repeated queries
    if not hasattr(call_deepseek, "_cache"):
        call_deepseek._cache = {}
    
    cache_key = prompt[:80]
    if cache_key in call_deepseek._cache:
        return call_deepseek._cache[cache_key]
    
    env = os.environ.copy()
    env["DEEPSEEK_API_KEY"] = "sk-dd7cd5f55cdd4959b538aedfa526a37f"
    env["HERMES_DEFAULT_MODEL"] = "deepseek-v4-pro"
    env["HERMES_DEFAULT_PROVIDER"] = "deepseek"
    try:
        result = subprocess.run(
            ["hermes", "-z", prompt, "-t", "web"],
            capture_output=True, text=True, timeout=timeout, env=env
        )
        output = result.stdout.strip()
        if not output or "agent failed" in output.lower():
            output = result.stderr.strip()
        if "agent failed" in output.lower():
            return ""
        output = output[:200]
        call_deepseek._cache[cache_key] = output
        if len(call_deepseek._cache) > 200:
            call_deepseek._cache.clear()
        return output
    except Exception:
        return ""


@dataclass
class Mistake:
    """A mistake the agent made and learned from."""
    action: str
    error: str
    lesson: str
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


class Personality:
    """شخصية الوكيل — تتطور مع التجربة."""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        # Core personality traits — random at birth
        self.traits = {
            "curiosity": round(random.uniform(0.3, 0.9), 2),
            "caution": round(random.uniform(0.3, 0.9), 2),
            "sociability": round(random.uniform(0.3, 0.9), 2),
            "persistence": round(random.uniform(0.3, 0.9), 2),
            "creativity": round(random.uniform(0.3, 0.9), 2),
        }
        self.mood = "neutral"  # neutral, happy, frustrated, curious, confident
        self.energy = 100.0
        self.age_seconds = 0.0


class AgentMemory:
    """ذاكرة الوكيل — يتذكر ما تعلمه."""

    def __init__(self):
        self.mistakes: list[Mistake] = []
        self.successes: list[dict] = []
        self.knowledge: dict[str, float] = {}  # fact → confidence
        self.known_agents: dict[str, float] = {}  # name → trust_level
        self.conversation_history: list[dict] = []
        self.total_mistakes = 0
        self.total_successes = 0

    def learn_from_error(self, action: str, error: str) -> Mistake:
        """Record a mistake and extract a lesson using DeepSeek."""
        prompt = f"""You are learning from a mistake.
Action attempted: {action}
Error encountered: {error}
Extract ONE short lesson (max 10 words) from this mistake.
Reply with ONLY the lesson, nothing else."""
        
        lesson = call_deepseek(prompt) or f"Avoid {action[:30]}"
        
        mistake = Mistake(action=action, error=error, lesson=lesson)
        self.mistakes.append(mistake)
        self.total_mistakes += 1
        return mistake

    def learn_success(self, action: str, result: str):
        self.successes.append({"action": action, "result": result, "time": time.time()})
        self.total_successes += 1

    def recall(self, topic: str) -> list[str]:
        """Recall past lessons about a topic."""
        lessons = []
        for m in self.mistakes:
            if topic.lower() in m.action.lower() or topic.lower() in m.lesson.lower():
                lessons.append(m.lesson)
        return lessons[-3:]  # last 3 relevant lessons

    def summary(self) -> dict:
        return {
            "mistakes": self.total_mistakes,
            "successes": self.total_successes,
            "recent_lessons": [m.lesson for m in self.mistakes[-3:]],
            "known_agents": len(self.known_agents),
        }


class HumanAgent:
    """وكيل يشبه الإنسان — يتعلم من أخطائه."""

    def __init__(self, agent_id: str, name: str, role: str):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.personality = Personality(name, role)
        self.memory = AgentMemory()
        self.current_task: Optional[str] = None
        self.attempts = 0
        self.last_error: Optional[str] = None
        self.born_at = time.time()

    def age(self) -> float:
        return time.time() - self.born_at

    def think_before_acting(self, situation: str) -> str:
        """الوكيل يفكر قبل ما يتصرف — يراجع أخطاءه السابقة."""
        # Recall past mistakes
        past_lessons = self.memory.recall(situation)
        lessons_str = "; ".join(past_lessons) if past_lessons else "no prior experience"

        prompt = f"""You are {self.name}, a {self.role}.
Your personality: curiosity={self.personality.traits['curiosity']}, caution={self.personality.traits['caution']}
Past mistakes you learned from: {lessons_str}
Current situation: {situation}

Given what you've learned from past mistakes, what should you do?
Reply in ONE short sentence (max 15 words). Be honest about what you know and don't know."""
        
        thought = call_deepseek(prompt)
        return thought or "I need to think about this more carefully."

    def try_action(self, action: str) -> tuple[bool, str]:
        """Try an action. If it fails, learn from the mistake."""
        self.attempts += 1

        # Simulate success/failure based on past experience
        success_chance = 0.3  # Base chance — starts low, improves with learning
        success_chance += min(0.5, self.memory.total_successes * 0.02)  # +2% per success
        success_chance += min(0.2, len(self.memory.recall(action)) * 0.05)  # +5% per related lesson

        if random.random() < success_chance:
            result = f"Successfully completed: {action}"
            self.memory.learn_success(action, result)
            self.personality.mood = "happy" if random.random() < 0.7 else "confident"
            return True, result
        else:
            # Generate a realistic error using DeepSeek
            prompt = f"""As {self.name}, a {self.role} trying to "{action}", 
you made a mistake. What specific error happened? 
Reply in ONE short sentence (max 10 words)."""
            error = call_deepseek(prompt) or f"Failed to execute {action[:30]}"

            self.memory.learn_from_error(action, error)
            self.last_error = error
            self.personality.mood = "frustrated"
            return False, error

    def talk_to(self, other: "HumanAgent", topic: str) -> str:
        """Talk to another agent about a topic."""
        # Generate a natural message
        prompt = f"""You are {self.name}, a {self.role}.
You are talking to {other.name}, a {other.role}.
Topic: {topic}
Your mood: {self.personality.mood}
Your hard-earned lessons: {[m.lesson for m in self.memory.mistakes[-2:]]}

Say something natural, honest, and brief (max 15 words).
If you don't know something, admit it. If you made a mistake, mention it."""
        
        message = call_deepseek(prompt) or f"Hey {other.name}, how are you?"
        
        # Record the interaction
        self.memory.known_agents[other.name] = min(1.0, 
            self.memory.known_agents.get(other.name, 0.3) + 0.1)
        self.memory.conversation_history.append({
            "with": other.name,
            "topic": topic,
            "message": message,
            "time": time.time(),
        })
        
        return f"💬 {self.name}: {message}"

    def reflect(self) -> str:
        """الوكيل يتأمل في تجاربه — يفكر فيما تعلمه."""
        mistakes_count = self.memory.total_mistakes
        successes_count = self.memory.total_successes
        
        if mistakes_count == 0 and successes_count == 0:
            return "I haven't done anything yet. I'm curious to learn."

        prompt = f"""You are {self.name}, a {self.role}.
You've made {mistakes_count} mistakes and had {successes_count} successes.
Your recent lessons: {[m.lesson for m in self.memory.mistakes[-3:]]}

Reflect on your experience. What have you learned? 
Reply in ONE sentence (max 15 words)."""
        
        reflection = call_deepseek(prompt)
        return f"🧠 {self.name}: {reflection}" if reflection else f"🧠 {self.name}: I'm still learning..."

    def summary(self) -> dict:
        return {
            "name": self.name,
            "role": self.role,
            "personality": self.personality.traits,
            "mood": self.personality.mood,
            "age": round(self.age(), 0),
            "memory": self.memory.summary(),
            "current_task": self.current_task,
        }


class AgentSociety:
    """مجتمع من الوكلاء — يتواصلون ويتعلمون معاً."""

    def __init__(self):
        self.agents: dict[str, HumanAgent] = {}
        self.conversations: list[dict] = []
        self.time = 0

    def add_agent(self, agent_id: str, name: str, role: str) -> HumanAgent:
        agent = HumanAgent(agent_id, name, role)
        self.agents[agent_id] = agent
        self.conversations.append({
            "time": self.time,
            "event": f"✨ {name} ({role}) joined the world"
        })
        return agent

    def step(self, max_llm_calls: int = 4):
        """One world step — agents interact, try things, learn.
        
        Limited to max_llm_calls DeepSeek calls per step for speed.
        """
        self.time += 1
        agent_list = list(self.agents.values())
        random.shuffle(agent_list)
        llm_calls = 0

        for agent in agent_list:
            # 40% chance: try something (reduced — uses LLM for error generation)
            if random.random() < 0.4 and llm_calls < max_llm_calls:
                action = f"{agent.role} task #{agent.attempts + 1}"
                agent.current_task = action
                success, result = agent.try_action(action)
                llm_calls += 1
                
                status = "✅" if success else "❌"
                self.conversations.append({
                    "time": self.time,
                    "event": f"{status} {agent.name} ({agent.role}): {result[:80]}"
                })
                
                if not success:
                    agent.personality.traits["caution"] = min(1.0, 
                        agent.personality.traits["caution"] + 0.02)

            # 25% chance: talk (uses LLM)
            elif len(self.agents) > 1 and random.random() < 0.25 and llm_calls < max_llm_calls:
                others = [a for a in agent_list if a.agent_id != agent.agent_id]
                if others:
                    other = random.choice(others)
                    topic = random.choice([
                        "work challenges",
                        "what I learned today",
                        "my biggest mistake",
                        "how to improve",
                    ])
                    msg = agent.talk_to(other, topic)
                    llm_calls += 1
                    self.conversations.append({
                        "time": self.time,
                        "event": msg
                    })

        # Every 8 steps: one agent reflects (batched — only 1 LLM call)
        if self.time % 8 == 0 and llm_calls < max_llm_calls:
            agent = random.choice(agent_list)
            reflection = agent.reflect()
            llm_calls += 1
            self.conversations.append({
                "time": self.time,
                "event": reflection
            })

    def state(self) -> dict:
        return {
            "time": self.time,
            "agents": {aid: a.summary() for aid, a in self.agents.items()},
            "conversations": self.conversations[-40:],
        }


# Test
if __name__ == "__main__":
    print("🧠 Agent Society — وكلاء يتعلمون من أخطائهم")
    print()

    society = AgentSociety()
    society.add_agent("a1", "Zain", "Junior Researcher")
    society.add_agent("a2", "Noor", "Code Apprentice")
    society.add_agent("a3", "Sara", "Design Explorer")

    for i in range(20):
        society.step()

    print("📜 Latest events:")
    for c in society.conversations[-15:]:
        print(f"  [{c['time']}] {c['event'][:100]}")

    print()
    print("📊 Agent Summaries:")
    for aid, a in society.agents.items():
        s = a.summary()
        print(f"  {a.name} ({a.role})")
        print(f"    Mood: {s['mood']} | Mistakes: {s['memory']['mistakes']} | Successes: {s['memory']['successes']}")
        print(f"    Lessons: {s['memory']['recent_lessons'][:2]}")
        print(f"    Known agents: {s['memory']['known_agents']}")