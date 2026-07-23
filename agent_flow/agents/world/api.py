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
from agent_flow.agents.world.company_integration import (
    company_store, create_default_companies, assign_agents_to_companies,
    get_agent_company, get_company_agents, get_nearby_companies,
)

router = APIRouter(prefix="/world", tags=["world"])


@router.get("/{world_name}")
async def get_world_state(world_name: str):
    """حالة العالم الكاملة مع الشركات."""
    world = get_or_create_world(world_name)
    state = world.get_state()
    state["companies"] = [c.as_dict() for c in company_store.all()]
    return state


@router.get("/{world_name}/companies")
async def list_companies(world_name: str):
    """قائمة الشركات في العالم."""
    return {"companies": [c.as_dict() for c in company_store.all()]}


@router.get("/{world_name}/companies/{name}")
async def get_company(world_name: str, name: str):
    """معلومات شركة محددة."""
    company = company_store.get(name)
    if not company:
        return {"error": "Company not found"}, 404
    return company.as_dict()


@router.get("/{world_name}/agents/{agent_id}/company")
async def agent_company(world_name: str, agent_id: str):
    """معرفة شركة وكيل معين."""
    company = get_agent_company(agent_id)
    if not company:
        return {"company": None}
    return {"company": company.as_dict()}


@router.post("/{world_name}/companies/{name}/hire")
async def hire_agent(world_name: str, name: str, agent_id: str):
    """توظيف وكيل في شركة."""
    world = get_or_create_world(world_name)
    company = company_store.get(name)
    if not company:
        return {"error": "Company not found"}, 404
    if agent_id not in world.agents:
        return {"error": "Agent not found"}, 404

    company.add_employee(agent_id)
    world.agents[agent_id].current_location = f"company_{name.lower().replace(' ', '_')}"

    await ws_manager.broadcast(world_name, {
        "type": "agent_hired",
        "agent_id": agent_id,
        "company": name,
    })

    return {"status": "hired", "agent_id": agent_id, "company": name}


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
    state = world.get_state()
    state["companies"] = [c.as_dict() for c in company_store.all()]
    await ws_manager.broadcast(world_name, {
        "type": "world_tick",
        "data": state,
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
        # Initial world state.
        state = world.get_state()
        state["companies"] = [c.as_dict() for c in company_store.all()]
        await websocket.send_json({
            "type": "world_state",
            "data": state,
        })

        # Initial ticker status (idle | running | paused).
        from agent_flow.agents.world.ws import tickers
        existing = tickers.get(world_name)
        if existing and existing.is_running():
            status, pace = "running", existing.pace_seconds
        elif existing:
            status, pace = "paused", existing.pace_seconds
        else:
            status, pace = "idle", 3.0
        await websocket.send_json({
            "type": "world_ticker",
            "status": status,
            "pace_seconds": pace,
        })

        # Command loop.
        from agent_flow.agents.world.ticker import AutonomousTicker

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
                        delta = await world.tick()
                        from agent_flow.agents.world.ws import broadcast_delta
                        await broadcast_delta(world_name, world, delta)

                elif action == "start":
                    pace = float(cmd.get("pace_seconds", 3.0))
                    ticker = tickers.get(world_name)
                    if ticker is None:
                        ticker = AutonomousTicker(world_name, world, ws_manager, pace_seconds=pace)
                        tickers[world_name] = ticker
                    else:
                        ticker.set_pace(pace)
                    await ticker.start()

                elif action == "pause":
                    ticker = tickers.get(world_name)
                    if ticker:
                        await ticker.stop()

                elif action == "set_pace":
                    pace = float(cmd.get("pace_seconds", 3.0))
                    ticker = tickers.get(world_name)
                    if ticker:
                        ticker.set_pace(pace)
                        # Reflect new pace to all subscribers.
                        await ws_manager.broadcast(world_name, {
                            "type": "world_ticker",
                            "status": "running" if ticker.is_running() else "paused",
                            "pace_seconds": ticker.pace_seconds,
                        })

            except (json.JSONDecodeError, KeyError, ValueError):
                pass

    except WebSocketDisconnect:
        ws_manager.unregister(world_name, websocket)


# Export for main.py
world_router = router