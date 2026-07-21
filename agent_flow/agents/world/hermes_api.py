"""AgentVerse API — REPL for the Hermes-powered world."""

from __future__ import annotations

import asyncio
import json
import time
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from agent_flow.agents.world.hermes_world import HermesWorld

router = APIRouter(prefix="/agentverse", tags=["agentverse"])

world = HermesWorld()
world.add_agent("a1", "Zain", "Junior Researcher")
world.add_agent("a2", "Noor", "Code Apprentice")
world.add_agent("a3", "Sara", "Design Explorer")


@router.get("/")
async def get_world():
    """حالة العالم الحالية."""
    return world.get_state()


@router.post("/tick")
async def do_tick(count: int = 3):
    """نبضات — الوكلاء يتكلمون."""
    for _ in range(count):
        world.tick()
    return world.get_state()


@router.get("/conversations")
async def get_conversations():
    """آخر المحادثات."""
    return {"conversations": world.conversations[-40:]}


@router.post("/reset")
async def reset_world():
    """إعادة تعيين العالم."""
    global world
    world = HermesWorld()
    world.add_agent("a1", "Zain", "Junior Researcher")
    world.add_agent("a2", "Noor", "Code Apprentice")
    world.add_agent("a3", "Sara", "Design Explorer")
    return {"status": "reset", "agents": 3}


@router.get("/agents")
async def list_agents():
    """قائمة الوكلاء."""
    return {"agents": {aid: a.summary() for aid, a in world.agents.items()}}