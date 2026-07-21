"""World WebSocket — real-time agent interactions for the frontend."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from agent_flow.agents.world.engine import WorldEngine


class WorldWebSocketManager:
    """يدير اتصالات WebSocket للعالم."""

    def __init__(self):
        self.connections: dict[str, list] = {}  # world_name -> [websocket connections]

    def register(self, world_name: str, websocket: Any):
        if world_name not in self.connections:
            self.connections[world_name] = []
        self.connections[world_name].append(websocket)

    def unregister(self, world_name: str, websocket: Any):
        if world_name in self.connections:
            self.connections[world_name] = [ws for ws in self.connections[world_name] if ws != websocket]
            if not self.connections[world_name]:
                del self.connections[world_name]

    async def broadcast(self, world_name: str, data: dict):
        """إرسال تحديث لجميع المتصلين بالعالم."""
        if world_name not in self.connections:
            return
        dead = []
        for ws in self.connections[world_name]:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.unregister(world_name, ws)


# World manager — يحتفظ بكل العوالم النشطة
world_manager: dict[str, WorldEngine] = {}
ws_manager = WorldWebSocketManager()


def get_or_create_world(name: str = "agentverse") -> WorldEngine:
    """الحصول على عالم أو إنشائه إن لم يوجد."""
    if name not in world_manager:
        world_manager[name] = WorldEngine.create_default_world()
    return world_manager[name]


async def run_world_ticks(world_name: str, ticks: int = 20, interval: float = 2.0):
    """تشغيل نبضات العالم مع بث التحديثات للواجهة."""
    world = world_manager.get(world_name)
    if not world:
        return

    for _ in range(ticks):
        await world.tick()
        state = world.get_state()
        await ws_manager.broadcast(world_name, {
            "type": "world_tick",
            "data": state,
        })
        await asyncio.sleep(interval)