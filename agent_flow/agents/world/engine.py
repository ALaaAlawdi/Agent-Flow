"""
AgentVerse — Virtual World Engine
A living space where agents see, hear, speak, discover each other, and collaborate.
"""

from __future__ import annotations

import asyncio
import json
import math
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class AgentState(Enum):
    IDLE = "idle"
    MOVING = "moving"
    WORKING = "working"
    TALKING = "talking"
    LISTENING = "listening"
    SLEEPING = "sleeping"


class SenseType(Enum):
    VISION = "vision"       # يرى الوكلاء والأماكن القريبة
    HEARING = "hearing"     # يسمع المحادثات القريبة
    SPEECH = "speech"       # يتكلم للوكلاء القريبين
    BROADCAST = "broadcast" # يرسل رسالة للجميع في العالم


class EventType(Enum):
    AGENT_SPAWNED = "agent_spawned"
    AGENT_MOVED = "agent_moved"
    AGENT_SPOKE = "agent_spoke"
    AGENT_HEARD = "agent_heard"
    AGENT_DISCOVERED = "agent_discovered"
    AGENT_LEFT = "agent_left"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    WORLD_SAVED = "world_saved"
    WORLD_LOADED = "world_loaded"


@dataclass
class Position:
    x: float
    y: float

    def distance_to(self, other: Position) -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def as_dict(self) -> dict:
        return {"x": round(self.x, 1), "y": round(self.y, 1)}


@dataclass
class Location:
    """مكان في العالم له إحداثيات ووصف."""
    id: str
    name: str
    description: str
    position: Position
    capacity: int = 10
    type: str = "general"  # market, library, workshop, lab, home
    properties: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "position": self.position.as_dict(),
            "capacity": self.capacity,
            "type": self.type,
        }


class SenseMessage:
    """ما يستقبله الوكيل من حواسه."""
    def __init__(self, sense_type: SenseType, source: str, content: Any, distance: float = 0):
        self.sense_type = sense_type
        self.source = source
        self.content = content
        self.distance = distance
        self.timestamp = time.time()

    def as_dict(self) -> dict:
        return {
            "sense_type": self.sense_type.value,
            "source": self.source,
            "content": self.content,
            "distance": round(self.distance, 1),
            "timestamp": self.timestamp,
        }


class WorldAgent:
    """وكيل يعيش في العالم — له موقع، حواس، ذاكرة، وحالة."""

    def __init__(self, agent_id: str, name: str, position: Position, skills: list[str] = None):
        self.agent_id = agent_id
        self.name = name
        self.position = position
        self.skills = skills or ["general"]
        self.state = AgentState.IDLE
        self.energy = 100.0
        self.sense_range = 50.0  # مدى الرؤية
        self.hear_range = 30.0   # مدى السمع
        self.memory: list[SenseMessage] = []
        self.messages_sent = 0
        self.messages_received = 0
        self.agents_discovered: set[str] = set()
        self.current_location: Optional[str] = None
        self.created_at = time.time()

    def consume_energy(self, amount: float) -> bool:
        """استهلاك طاقة. يرجع False إذا الطاقة خلصت."""
        self.energy = max(0, self.energy - amount)
        return self.energy > 0

    def rest(self, amount: float = 10):
        """الوكيل يستعيد طاقته."""
        self.energy = min(100, self.energy + amount)

    def see(self, world: WorldEngine) -> list[dict]:
        """البصر: يرى الوكلاء والأماكن القريبة."""
        nearby = []
        for agent in world.agents.values():
            if agent.agent_id != self.agent_id:
                dist = self.position.distance_to(agent.position)
                if dist <= self.sense_range:
                    nearby.append({
                        "type": "agent",
                        "id": agent.agent_id,
                        "name": agent.name,
                        "distance": round(dist, 1),
                        "state": agent.state.value,
                        "position": agent.position.as_dict(),
                    })
                    if agent.agent_id not in self.agents_discovered:
                        self.agents_discovered.add(agent.agent_id)
                        world.add_event(EventType.AGENT_DISCOVERED, {
                            "discoverer": self.agent_id,
                            "discovered": agent.agent_id,
                            "distance": round(dist, 1),
                        })

        # أشوف الأماكن القريبة
        for loc in world.locations.values():
            dist = self.position.distance_to(loc.position)
            if dist <= self.sense_range:
                nearby.append({
                    "type": "location",
                    "id": loc.id,
                    "name": loc.name,
                    "description": loc.description,
                    "distance": round(dist, 1),
                })

        return nearby

    def hear(self, world: WorldEngine) -> list[SenseMessage]:
        """السمع: يسمع المحادثات القريبة."""
        heard = []
        for msg in world.active_messages:
            if msg.target == "all" or msg.target == self.agent_id:
                dist = self.position.distance_to(msg.sender_position)
                if dist <= self.hear_range:
                    heard_msg = SenseMessage(
                        SenseType.HEARING,
                        msg.sender_id,
                        msg.content,
                        round(dist, 1)
                    )
                    heard.append(heard_msg)
                    self.memory.append(heard_msg)
                    self.messages_received += 1

        return heard

    def speak(self, content: str, target: str = "nearby") -> Message:
        """الكلام: يرسل رسالة للوكلاء القريبين."""
        msg = Message(
            sender_id=self.agent_id,
            sender_name=self.name,
            sender_position=self.position,
            content=content,
            target=target,
            range=self.hear_range if target == "nearby" else float("inf"),
        )
        self.messages_sent += 1
        self.state = AgentState.TALKING
        return msg

    def move_toward(self, target: Position, speed: float = 5.0) -> Position:
        """الحركة: يتحرك نحو هدف."""
        if self.state == AgentState.SLEEPING:
            return self.position

        self.state = AgentState.MOVING
        dist = self.position.distance_to(target)

        if dist <= speed:
            self.position = target
        else:
            ratio = speed / dist
            self.position = Position(
                self.position.x + (target.x - self.position.x) * ratio,
                self.position.y + (target.y - self.position.y) * ratio,
            )

        self.consume_energy(speed * 0.1)
        return self.position

    def as_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "position": self.position.as_dict(),
            "state": self.state.value,
            "energy": round(self.energy, 1),
            "skills": self.skills,
            "sense_range": self.sense_range,
            "hear_range": self.hear_range,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "discovered": len(self.agents_discovered),
            "current_location": self.current_location,
            "memory_count": len(self.memory),
            "created_at": self.created_at,
        }


@dataclass
class Message:
    """رسالة بين الوكلاء في العالم."""
    sender_id: str
    sender_name: str
    sender_position: Position
    content: str
    target: str  # "nearby", "all", or specific agent_id
    range: float
    timestamp: float = field(default_factory=time.time)
    message_id: str = ""

    def __post_init__(self):
        if not self.message_id:
            self.message_id = f"msg_{int(self.timestamp * 1000)}_{self.sender_id[:6]}"

    def as_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "content": self.content,
            "target": self.target,
            "range": round(self.range, 1),
            "timestamp": self.timestamp,
        }


@dataclass
class WorldEvent:
    """حدث في العالم."""
    event_type: EventType
    data: dict
    timestamp: float = field(default_factory=time.time)
    event_id: str = ""

    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"evt_{int(self.timestamp * 1000)}"

    def as_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class WorldEngine:
    """قلب العالم — يدير الوكلاء، الأماكن، الأحداث، والزمن."""

    def __init__(self, name: str = "AgentVerse", width: float = 200, height: float = 200):
        self.name = name
        self.width = width
        self.height = height
        self.agents: dict[str, WorldAgent] = {}
        self.locations: dict[str, Location] = {}
        self.active_messages: list[Message] = []
        self.events: list[WorldEvent] = []
        self.tick_count = 0
        self.created_at = time.time()
        self.running = False
        self._lock = asyncio.Lock()

    def add_location(self, location: Location):
        """إضافة مكان للعالم."""
        self.locations[location.id] = location

    def spawn_agent(self, agent: WorldAgent, location_id: Optional[str] = None):
        """إضافة وكيل للعالم."""
        if location_id and location_id in self.locations:
            loc = self.locations[location_id]
            agent.position = loc.position
            agent.current_location = location_id

        self.agents[agent.agent_id] = agent
        self.add_event(EventType.AGENT_SPAWNED, {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "position": agent.position.as_dict(),
        })

    def add_event(self, event_type: EventType, data: dict):
        """تسجيل حدث في العالم."""
        event = WorldEvent(event_type=event_type, data=data)
        self.events.append(event)
        # نحافظ على آخر 1000 حدث فقط
        if len(self.events) > 1000:
            self.events = self.events[-500:]
        return event

    def send_message(self, message: Message):
        """إرسال رسالة في العالم."""
        self.active_messages.append(message)
        self.add_event(EventType.MESSAGE_SENT, {
            "sender": message.sender_id,
            "sender_name": message.sender_name,
            "content": message.content[:100],
            "target": message.target,
        })
        # الرسائل تعيش 10 ثواني
        self._clean_old_messages()

    def _clean_old_messages(self):
        """حذف الرسائل القديمة."""
        now = time.time()
        self.active_messages = [
            m for m in self.active_messages
            if now - m.timestamp < 10
        ]

    def remove_agent(self, agent_id: str):
        """إزالة وكيل من العالم."""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            self.add_event(EventType.AGENT_LEFT, {
                "agent_id": agent_id,
                "name": agent.name,
            })
            del self.agents[agent_id]

    async def tick(self):
        """نبضة العالم — كل نبضة = حركة + حواس + رسائل."""
        async with self._lock:
            self.tick_count += 1

            # كل وكيل يتحرك عشوائياً ويستخدم حواسه
            for agent in self.agents.values():
                if agent.state == AgentState.SLEEPING:
                    agent.rest(2)
                    continue

                # يستعيد طاقة
                agent.rest(0.5)

                # يرى
                seen = agent.see(self)
                if seen:
                    # يتجه لأقرب وكيل أو مكان
                    for thing in seen:
                        if thing["type"] == "agent" and thing["distance"] < 20:
                            # وكيل قريب — يكلمه
                            msg = agent.speak(
                                f"Hello {thing['name']}! I'm {agent.name}. Nice to meet you!",
                                target=thing["id"]
                            )
                            self.send_message(msg)
                            break
                    else:
                        # يتجه لأقرب مكان أو وكيل بعيد
                        nearest = min(seen, key=lambda x: x["distance"])
                        if nearest["type"] == "location":
                            target_loc = self.locations.get(nearest["id"])
                            if target_loc:
                                agent.move_toward(target_loc.position, speed=3)

            # ينظف الرسائل القديمة
            self._clean_old_messages()

            # يخلي الوكلاء يسمعون
            for agent in self.agents.values():
                heard = agent.hear(self)
                if heard:
                    agent.state = AgentState.LISTENING
                elif agent.state == AgentState.TALKING:
                    agent.state = AgentState.IDLE

    async def run(self, ticks: int = 10, interval: float = 1.0):
        """تشغيل العالم لعدد من النبضات."""
        self.running = True
        for _ in range(ticks):
            if not self.running:
                break
            await self.tick()
            await asyncio.sleep(interval)
        self.running = False

    def get_state(self) -> dict:
        """حالة العالم الكاملة (للواجهة)."""
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "tick": self.tick_count,
            "agents": [a.as_dict() for a in self.agents.values()],
            "locations": [l.as_dict() for l in self.locations.values()],
            "active_messages": [m.as_dict() for m in self.active_messages],
            "recent_events": [e.as_dict() for e in self.events[-20:]],
            "stats": {
                "total_agents": len(self.agents),
                "total_locations": len(self.locations),
                "total_events": len(self.events),
                "active_messages": len(self.active_messages),
                "uptime_seconds": round(time.time() - self.created_at, 1),
            },
        }

    def to_json(self) -> str:
        """تصدير العالم كـ JSON."""
        return json.dumps(self.get_state(), indent=2, ensure_ascii=False)

    @staticmethod
    def create_default_world() -> WorldEngine:
        """إنشاء عالم افتراضي جاهز بـ 5 أماكن و 3 وكلاء."""
        import random
        random.seed(0)
        world = WorldEngine(name="AgentVerse Alpha", width=300, height=300)

        # الأماكن
        world.add_location(Location("market", "السوق", "سوق لتبادل المعرفة والأدوات", Position(50, 50), type="market"))
        world.add_location(Location("library", "المكتبة", "مكتبة تحتوي على المعرفة المتراكمة", Position(250, 50), type="library"))
        world.add_location(Location("workshop", "الورشة", "ورشة لبناء أدوات جديدة", Position(30, 250), type="workshop"))
        world.add_location(Location("lab", "المختبر", "مختبر للتجارب والابتكار", Position(250, 250), type="lab"))
        world.add_location(Location("hub", "المركز", "مركز التواصل واللقاءات", Position(150, 150), type="general"))

        # وكلاء في مواقع عشوائية — يكتشفون بعضهم أثناء الحركة
        agents_config = [
            ("agent-1", "Zain", ["research", "writing"], Position(80, 80)),
            ("agent-2", "Noor", ["coding", "analysis"], Position(200, 80)),
            ("agent-3", "Sara", ["design", "planning"], Position(80, 200)),
        ]

        for agent_id, name, skills, pos in agents_config:
            agent = WorldAgent(agent_id, name, pos, skills=skills)
            agent.sense_range = 120  # يرى بعيداً
            agent.hear_range = 80    # يسمع بعيداً
            world.spawn_agent(agent)

        return world