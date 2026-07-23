"""World WebSocket — real-time agent interactions for the frontend."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any

from agent_flow.agents.world.engine import InteractionDelta, WorldEngine

if TYPE_CHECKING:
    from agent_flow.agents.world.ticker import AutonomousTicker


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


# World manager — يحتفظ بكل العوالم النشطة.
world_manager: dict[str, WorldEngine] = {}
ws_manager = WorldWebSocketManager()
# Autonomous tickers, keyed by world name — one per world.
tickers: dict[str, "AutonomousTicker"] = {}


def get_or_create_world(name: str = "agentverse") -> WorldEngine:
    """الحصول على عالم أو إنشائه إن لم يوجد."""
    if name not in world_manager:
        world_manager[name] = WorldEngine.create_default_world()
    return world_manager[name]


def _pulse_payload(world: WorldEngine, tick: int) -> dict:
    """Build the world_pulse WS frame payload (state + companies)."""
    from agent_flow.agents.world.company_integration import company_store
    state = world.get_state()
    state["companies"] = [c.as_dict() for c in company_store.all()]
    return {"type": "world_pulse", "tick": tick, "state": state}


async def broadcast_delta(world_name: str, world: WorldEngine, delta: InteractionDelta) -> None:
    """Send one WS frame per interaction, plus a rollup world_pulse.

    Order: moves → greetings → asks → answers → learnings → world_pulse.
    """
    for i, m in enumerate(delta.moves):
        await ws_manager.broadcast(world_name, {
            "type": "agent_moved",
            "id": f"mv_{delta.tick:05d}_{i}",
            **m,
            "tick": delta.tick,
        })
    for i, g in enumerate(delta.greetings):
        await ws_manager.broadcast(world_name, {
            "type": "agent_greeted",
            "id": f"grt_{delta.tick:05d}_{i}",
            **g,
            "tick": delta.tick,
        })
    for i, a in enumerate(delta.asks):
        await ws_manager.broadcast(world_name, {
            "type": "agent_asked",
            "id": f"ask_{delta.tick:05d}_{i}",
            **a,
            "tick": delta.tick,
        })
    for i, a in enumerate(delta.answers):
        await ws_manager.broadcast(world_name, {
            "type": "agent_answered",
            "id": f"ans_{delta.tick:05d}_{i}",
            **a,
            "tick": delta.tick,
        })
    for i, L in enumerate(delta.learnings):
        await ws_manager.broadcast(world_name, {
            "type": "agent_learned",
            "id": f"lrn_{delta.tick:05d}_{i}",
            **L,
            "tick": delta.tick,
        })
    await ws_manager.broadcast(world_name, _pulse_payload(world, delta.tick))


async def run_world_ticks(world_name: str, ticks: int = 20, interval: float = 2.0):
    """تشغيل نبضات العالم مع بث التحديثات للواجهة."""
    world = world_manager.get(world_name)
    if not world:
        return

    for _ in range(ticks):
        delta = await world.tick()
        await broadcast_delta(world_name, world, delta)
        await asyncio.sleep(interval)
