"""AgentVerse World Integration — ربط العالم بالـ API main."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from agent_flow.agents.world.engine import WorldEngine, WorldAgent, Position, Message
from agent_flow.agents.world.ws import (
    get_or_create_world,
    ws_manager,
    run_world_ticks,
    world_manager,
)

router = APIRouter(prefix="/world", tags=["world"])


@router.get("/{world_name}")
async def get_world_state(world_name: str):
    """حالة العالم الكاملة."""
    world = get_or_create_world(world_name)
    return world.get_state()


@router.post("/{world_name}/agents")
async def add_agent(world_name: str, name: str, skills: str = "general"):
    """إضافة وكيل جديد للعالم."""
    world = get_or_create_world(world_name)
    agent_id = f"agent-{len(world.agents) + 1}"
    agent = WorldAgent(
        agent_id=agent_id,
        name=name,
        position=Position(150, 150),
        skills=skills.split(","),
    )
    world.spawn_agent(agent)
    await ws_manager.broadcast(world_name, {
        "type": "agent_spawned",
        "agent": agent.as_dict(),
    })
    return {"agent_id": agent_id, "name": name, "position": agent.position.as_dict()}


@router.delete("/{world_name}/agents/{agent_id}")
async def remove_agent(world_name: str, agent_id: str):
    """إزالة وكيل من العالم."""
    world = get_or_create_world(world_name)
    world.remove_agent(agent_id)
    await ws_manager.broadcast(world_name, {
        "type": "agent_removed",
        "agent_id": agent_id,
    })
    return {"status": "removed", "agent_id": agent_id}


@router.post("/{world_name}/speak")
async def agent_speak(world_name: str, agent_id: str, content: str, target: str = "nearby"):
    """وكيل يتكلم."""
    world = get_or_create_world(world_name)
    agent = world.agents.get(agent_id)
    if not agent:
        return {"error": "Agent not found"}, 404

    msg = agent.speak(content, target)
    world.send_message(msg)
    await ws_manager.broadcast(world_name, {
        "type": "agent_spoke",
        "message": msg.as_dict(),
    })

    # الوكلاء القريبون يسمعون
    heard_by = []
    for other in world.agents.values():
        if other.agent_id != agent_id:
            heard = other.hear(world)
            if heard:
                heard_by.append(other.agent_id)

    return {
        "message": msg.as_dict(),
        "heard_by": heard_by,
    }


@router.post("/{world_name}/move")
async def agent_move(world_name: str, agent_id: str, x: float, y: float):
    """وكيل يتحرك إلى موقع."""
    world = get_or_create_world(world_name)
    agent = world.agents.get(agent_id)
    if not agent:
        return {"error": "Agent not found"}, 404

    target = Position(x, y)
    agent.move_toward(target)

    await ws_manager.broadcast(world_name, {
        "type": "agent_moved",
        "agent_id": agent_id,
        "position": agent.position.as_dict(),
        "state": agent.state.value,
    })

    return {"position": agent.position.as_dict(), "state": agent.state.value}


@router.post("/{world_name}/tick")
async def world_tick(world_name: str, count: int = 1):
    """نبضة العالم."""
    world = get_or_create_world(world_name)
    for _ in range(count):
        await world.tick()
    await ws_manager.broadcast(world_name, {
        "type": "world_tick",
        "data": world.get_state(),
    })
    return {"tick": world.tick_count, "agent_count": len(world.agents), "message_count": len(world.active_messages)}


@router.post("/{world_name}/run")
async def run_world(world_name: str, ticks: int = 10, interval: float = 1.5):
    """تشغيل العالم تلقائياً لعدد من النبضات."""
    asyncio.create_task(run_world_ticks(world_name, ticks, interval))
    return {"status": "running", "world": world_name, "ticks": ticks}


@router.websocket("/{world_name}/ws")
async def world_websocket(websocket: WebSocket, world_name: str):
    """WebSocket للتحديثات الحية للعالم."""
    await websocket.accept()
    world = get_or_create_world(world_name)
    ws_manager.register(world_name, websocket)

    try:
        # إرسال الحالة الأولية
        await websocket.send_json({
            "type": "world_state",
            "data": world.get_state(),
        })

        # استقبال أوامر من الواجهة
        while True:
            data = await websocket.receive_text()
            try:
                cmd = json.loads(data)
                action = cmd.get("action", "")

                if action == "speak":
                    agent = world.agents.get(cmd.get("agent_id", ""))
                    if agent:
                        msg = agent.speak(cmd.get("content", ""), cmd.get("target", "nearby"))
                        world.send_message(msg)
                        await ws_manager.broadcast(world_name, {
                            "type": "agent_spoke",
                            "message": msg.as_dict(),
                        })

                elif action == "move":
                    agent = world.agents.get(cmd.get("agent_id", ""))
                    if agent:
                        agent.move_toward(Position(cmd["x"], cmd["y"]))
                        await ws_manager.broadcast(world_name, {
                            "type": "agent_moved",
                            "agent_id": agent.agent_id,
                            "position": agent.position.as_dict(),
                        })

                elif action == "tick":
                    for _ in range(cmd.get("count", 1)):
                        await world.tick()
                    await ws_manager.broadcast(world_name, {
                        "type": "world_tick",
                        "data": world.get_state(),
                    })

            except (json.JSONDecodeError, KeyError):
                pass

    except WebSocketDisconnect:
        ws_manager.unregister(world_name, websocket)


# Export for main.py
world_router = router