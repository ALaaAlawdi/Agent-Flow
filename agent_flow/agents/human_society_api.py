"""Human Society API — وكلاء يتعلمون من أخطائهم."""

from fastapi import APIRouter

from agent_flow.agents.human_personality import AgentSociety

router = APIRouter(prefix="/society", tags=["society"])

society = AgentSociety()
society.add_agent("a1", "Zain", "Junior Researcher")
society.add_agent("a2", "Noor", "Code Apprentice")
society.add_agent("a3", "Sara", "Design Explorer")


@router.get("/")
async def get_society():
    return society.state()


@router.post("/step")
async def do_step(count: int = 1):
    for _ in range(count):
        society.step()
    return society.state()


@router.post("/reset")
async def reset():
    global society
    society = AgentSociety()
    society.add_agent("a1", "Zain", "Junior Researcher")
    society.add_agent("a2", "Noor", "Code Apprentice")
    society.add_agent("a3", "Sara", "Design Explorer")
    return {"status": "reset"}


@router.get("/conversations")
async def get_conversations():
    return {"conversations": society.conversations}