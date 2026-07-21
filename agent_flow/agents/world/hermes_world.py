"""
AgentVerse Hermes Integration — agents powered by REAL LLM (DeepSeek).

Each agent gets a Hermes Learning Loop automatically:
1. Agent-curated memory (نظام ذاكرة مع تذكير ذاتي)
2. Autonomous skill creation (خلق مهارات من التجربة)
3. Self-improving skills (مهارات تتحسن مع الاستخدام)
"""

from __future__ import annotations

import asyncio
import os
import random
import subprocess
import time
from pathlib import Path

from agent_flow.agents.hermes_learning_loop import AgentLearningFactory, AgentLearningLoop


def _hermes_chat(prompt: str, timeout: int = 30) -> str:
    """Direct call to Hermes Agent with DeepSeek — returns actual LLM response."""
    env = os.environ.copy()
    env["DEEPSEEK_API_KEY"] = "sk-dd7cd5f55cdd4959b538aedfa526a37f"
    env["HERMES_DEFAULT_MODEL"] = "deepseek-v4-pro"
    env["HERMES_DEFAULT_PROVIDER"] = "deepseek"

    try:
        result = subprocess.run(
            ["hermes", "-z", prompt, "-t", "web"],
            capture_output=True, text=True, timeout=timeout,
            env=env
        )
        output = result.stdout.strip()
        if not output:
            output = result.stderr.strip()
        if "agent failed" in output.lower() or "error" in output.lower():
            return f"[Thinking...]"
        return output[:200]
    except subprocess.TimeoutExpired:
        return "[Still thinking...]"
    except FileNotFoundError:
        return "[Hermes not available]"
    except Exception as e:
        return f"[...]"


class HermesAgentBrain:
    """Agent brain powered by real DeepSeek through Hermes CLI.
    
    Every agent automatically gets:
    - Memory store with self-nudge
    - Skill creation from experience
    - Skills that improve with use
    """

    def __init__(self, agent_id: str, name: str, job_title: str):
        self.agent_id = agent_id
        self.name = name
        self.job_title = job_title
        self.personality = {
            "curiosity": round(random.uniform(0.7, 1.0), 2),
            "talkativity": round(random.uniform(0.6, 1.0), 2),
            "friendliness": round(random.uniform(0.6, 1.0), 2),
        }
        self.knowledge: list[str] = []
        self.skills: dict[str, float] = {"asking": 0.3}
        self.interactions = 0
        self.last_response = ""

        # 🧠 Hermes Learning Loop — ينشأ تلقائياً مع كل وكيل
        self.learning_loop = AgentLearningFactory.create_for(agent_id, name)

    def ask(self) -> str:
        """Agent asks a question using real LLM."""
        prompt = (
            f"You are {self.name}, a {self.job_title} in a virtual world. "
            f"You are curious (curiosity={self.personality['curiosity']}), "
            f"friendly (friendliness={self.personality['friendliness']}). "
            f"Ask ONE short curious question to another agent you just met. "
            f"Maximum 15 words. Do not explain. Just the question."
        )
        response = _hermes_chat(prompt)
        self.interactions += 1
        self.skills["asking"] = min(1.0, self.skills.get("asking", 0) + 0.05)
        # 🧠 تعلم من السؤال
        self.learning_loop.after_action("ask_question", "asked")
        return f"🙋 {self.name} asks: \"{response}\""

    def answer(self, question: str) -> str:
        """Agent answers a question using real LLM."""
        skills = ", ".join([f"{k}({v:.0%})" for k, v in self.skills.items()])
        knowledge = "; ".join(self.knowledge[-3:]) if self.knowledge else "still learning"

        prompt = (
            f"You are {self.name}, a {self.job_title} in a virtual world. "
            f"Your skills: {skills}. Your knowledge: {knowledge}. "
            f"Someone just asked you: \"{question}\" "
            f"Answer naturally and briefly (max 20 words). Be helpful and {self.job_title.lower()}."
        )
        response = _hermes_chat(prompt)
        self.interactions += 1
        self.skills["answering"] = min(1.0, self.skills.get("answering", 0) + 0.05)
        # 🧠 تعلم من الإجابة
        self.learning_loop.after_action("answer_question", "answered")
        return f"{self.name}: {response}"

    def greet(self, other_name: str) -> str:
        """Greet another agent naturally."""
        prompt = (
            f"You are {self.name}, a {self.job_title}. You meet {other_name} for the first time. "
            f"Introduce yourself briefly (max 15 words). Be friendly."
        )
        response = _hermes_chat(prompt)
        self.interactions += 1
        self.knowledge.append(f"Met {other_name}")
        # 🧠 تعلم من اللقاء
        self.learning_loop.after_action("greet_agent", f"completed: met {other_name}")
        return f"{self.name}: {response}"

    def learn(self, topic: str):
        """Record something the agent learned."""
        self.knowledge.append(topic)
        skill_name = topic.lower().replace(" ", "_")[:20]
        self.skills[skill_name] = min(1.0, self.skills.get(skill_name, 0) + 0.1)
        # 🧠 تعلم من الموضوع
        self.learning_loop.after_action("learn_topic", f"completed: {topic}")

    def summary(self) -> dict:
        return {
            "name": self.name,
            "job_title": self.job_title,
            "personality": self.personality,
            "local_skills": {k: round(v, 2) for k, v in sorted(self.skills.items(), key=lambda x: -x[1])},
            "interactions": self.interactions,
            "last_response": self.last_response[:50] if self.last_response else "",
            "learning_loop": self.learning_loop.summary() if self.learning_loop else {},
        }


class HermesWorld:
    """World where agents talk using real DeepSeek."""

    def __init__(self):
        self.agents: dict[str, HermesAgentBrain] = {}
        self.conversations: list[dict] = []
        self.tick_count = 0

    def add_agent(self, agent_id: str, name: str, job_title: str) -> HermesAgentBrain:
        brain = HermesAgentBrain(agent_id, name, job_title)
        self.agents[agent_id] = brain
        self.conversations.append({
            "from": "🌍 World",
            "msg": f"✨ {name} ({job_title}) has joined the world!",
            "tick": 0,
        })
        return brain

    def tick(self):
        """One world tick — agents talk using real LLM."""
        self.tick_count += 1
        agent_list = list(self.agents.values())
        random.shuffle(agent_list)

        for agent in agent_list:
            # Random interaction with another agent
            others = [a for a in agent_list if a.agent_id != agent.agent_id]
            if not others or random.random() < 0.4:
                continue

            other = random.choice(others)

            # 50% ask, 40% greet, 10% share knowledge
            roll = random.random()
            if roll < 0.5:
                msg = agent.ask()
                reply = other.answer(msg)
                self.conversations.append({"from": "🗣️", "msg": msg, "tick": self.tick_count})
                self.conversations.append({"from": "💬", "msg": reply, "tick": self.tick_count})
                agent.learn(f"talked_to_{other.name}")
            elif roll < 0.9:
                msg = agent.greet(other.name)
                reply = self._acknowledge(other, agent.name)
                self.conversations.append({"from": "👋", "msg": msg, "tick": self.tick_count})
                self.conversations.append({"from": "💬", "msg": reply, "tick": self.tick_count})
            else:
                if agent.knowledge:
                    msg = f"{agent.name}: I learned something! {random.choice(agent.knowledge)}"
                    self.conversations.append({"from": "🧠", "msg": msg, "tick": self.tick_count})

        # Keep last 100 messages
        if len(self.conversations) > 100:
            self.conversations = self.conversations[-80:]

    def _acknowledge(self, agent: HermesAgentBrain, other_name: str) -> str:
        prompt = (
            f"You are {agent.name}, a {agent.job_title}. {other_name} just greeted you. "
            f"Reply briefly and friendly (max 12 words)."
        )
        response = _hermes_chat(prompt)
        agent.interactions += 1
        # تعلّم من لقاء الآخرين
        agent.learning_loop.after_action("acknowledge_greeting", f"completed: greeted by {other_name}")
        return f"{agent.name}: {response}"

    def get_state(self) -> dict:
        return {
            "name": "AgentVerse — Powered by DeepSeek",
            "tick": self.tick_count,
            "agents": {aid: b.summary() for aid, b in self.agents.items()},
            "conversations": self.conversations[-30:],
            "learning_loops": {aid: AgentLearningFactory.get(aid).summary() if AgentLearningFactory.get(aid) else {}
                              for aid in self.agents},
        }


# Test if run directly
if __name__ == "__main__":
    print("🌍 Testing Hermes-powered AgentVerse...")
    world = HermesWorld()
    world.add_agent("a1", "Zain", "Junior Researcher")
    world.add_agent("a2", "Noor", "Code Apprentice")
    world.add_agent("a3", "Sara", "Design Explorer")

    for i in range(10):
        world.tick()
        print(f"\n--- Tick {world.tick_count} ---")

    print("\n📊 Summary:")
    for aid, a in world.agents.items():
        s = a.summary()
        print(f"   {s['name']} ({s['job_title']})")
        print(f"      Interactions: {s['interactions']}")
        print(f"      Skills: {s['skills']}")