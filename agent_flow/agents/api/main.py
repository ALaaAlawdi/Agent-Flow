"""Combined FastAPI app for Agent Team System."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent_flow.agents import AgentTeam
from hermes_cli.toolset_validation import validate_platform_toolsets


# Initialize app
app = FastAPI(
    title="Agent-Flow Team API",
    description="Collaborative multi-agent teams powered by Hermes - كل وكيل يعرف الآخر ويتواصل معه تلقائياً",
    version="0.2.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Teams storage
teams: dict[str, AgentTeam] = {}


# ============== MODELS ==============

class CreateTeamRequest(BaseModel):
    """Request to create a team."""
    name: str
    goal: Optional[str] = ""


class AddAgentRequest(BaseModel):
    """Request to add an agent."""
    agent_id: str
    role: str
    tools: list[str]
    system_prompt: Optional[str] = ""


class SetGoalRequest(BaseModel):
    """Request to set goal."""
    goal: str


class AddKnowledgeRequest(BaseModel):
    """Request to add knowledge."""
    key: str
    value: str


class RunTaskRequest(BaseModel):
    """Request to run a task."""
    task: str
    agent_ids: Optional[list[str]] = None
    mode: str = "collaborative"  # collaborative, sequential


class SendMessageRequest(BaseModel):
    """Request to send message."""
    from_agent: str
    to_agent: str
    content: str


class BroadcastRequest(BaseModel):
    """Request to broadcast."""
    from_agent: str
    content: str
    to_roles: Optional[list[str]] = None


# ============== TEAM ROUTES ==============

@app.post("/teams", response_model=dict)
async def create_team(request: CreateTeamRequest):
    """Create a new agent team.
    
    All agents in the team share:
    - Environment (knowledge, memory, state)
    - Communication channels
    - Goals
    - Learning system
    """
    if request.name in teams:
        raise HTTPException(status_code=400, detail="Team already exists")
    
    team = AgentTeam(request.name, request.goal or "")
    teams[request.name] = team
    
    return {
        "status": "created",
        "team": request.name,
        "goal": request.goal or "",
    }


@app.get("/teams", response_model=dict)
async def list_teams():
    """List all teams."""
    return {
        "teams": [
            {
                "name": name,
                "goal": team.goal,
                "agents_count": len(team.agents),
            }
            for name, team in teams.items()
        ],
        "count": len(teams),
    }


@app.get("/teams/{team_name}", response_model=dict)
async def get_team(team_name: str):
    """Get team details."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_team_status()


@app.delete("/teams/{team_name}", response_model=dict)
async def delete_team(team_name: str):
    """Delete a team."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    del teams[team_name]
    return {"status": "deleted", "team": team_name}


# ============== AGENT ROUTES ==============

@app.post("/teams/{team_name}/agents", response_model=dict)
async def add_agent(team_name: str, request: AddAgentRequest):
    """Add an agent to team.
    
    The agent will:
    - Know about other team members
    - Have access to shared knowledge
    - Be able to communicate with other agents
    - Learn from feedback
    """
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Validate tools via Hermes
    try:
        validate_platform_toolsets(request.tools)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    team = teams[team_name]
    team.add_agent(
        request.agent_id,
        request.role,
        request.tools,
        request.system_prompt or "",
    )
    
    return {
        "status": "added",
        "team": team_name,
        "agent_id": request.agent_id,
        "role": request.role,
    }


@app.get("/teams/{team_name}/agents", response_model=dict)
async def list_agents(team_name: str):
    """List team agents."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams[team_name]
    agents = []
    
    for agent_id, agent in team.agents.items():
        perf = team.environment.get_agent_performance(agent_id)
        agents.append({
            "id": agent_id,
            "role": agent.role,
            "tasks_completed": agent.tasks_completed,
            "tasks_failed": agent.tasks_failed,
            "performance": perf,
        })
    
    return {"agents": agents, "count": len(agents)}


# ============== GOAL ROUTES ==============

@app.post("/teams/{team_name}/goal", response_model=dict)
async def set_goal(team_name: str, request: SetGoalRequest):
    """Set team goal."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    teams[team_name].set_goal(request.goal)
    return {"status": "set", "goal": request.goal}


# ============== KNOWLEDGE ROUTES ==============

@app.post("/teams/{team_name}/knowledge", response_model=dict)
async def add_knowledge(team_name: str, request: AddKnowledgeRequest):
    """Add shared knowledge to team."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    teams[team_name].add_knowledge(request.key, request.value)
    return {"status": "added", "key": request.key}


@app.get("/teams/{team_name}/knowledge", response_model=dict)
async def list_knowledge(team_name: str):
    """List team knowledge."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams[team_name]
    knowledge = []
    
    for key in team.environment.list_knowledge():
        value = team.environment.get_knowledge(key)
        knowledge.append({"key": key, "value": value})
    
    return {"knowledge": knowledge, "count": len(knowledge)}


# ============== TASK ROUTES ==============

@app.post("/teams/{team_name}/run", response_model=dict)
async def run_task(team_name: str, request: RunTaskRequest):
    """Run task with team.
    
    Modes:
    - collaborative: All agents work together
    - sequential: Agents work one after another, passing results
    """
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams[team_name]
    
    if request.mode == "sequential":
        result = team.run_sequential(request.task, request.agent_ids)
    else:
        result = team.run_collaborative(request.task, request.agent_ids)
    
    return result


# ============== MESSAGE ROUTES ==============

@app.post("/teams/{team_name}/messages", response_model=dict)
async def send_message(team_name: str, request: SendMessageRequest):
    """Send message from one agent to another."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams[team_name]
    team.message_agent(request.from_agent, request.to_agent, request.content)
    
    return {
        "status": "sent",
        "from": request.from_agent,
        "to": request.to_agent,
    }


@app.post("/teams/{team_name}/broadcast", response_model=dict)
async def broadcast(team_name: str, request: BroadcastRequest):
    """Broadcast message to team members."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams[team_name]
    team.broadcast(request.from_agent, request.content, request.to_roles)
    
    return {"status": "broadcasted"}


# ============== LEARNING ROUTES ==============

@app.get("/teams/{team_name}/learning", response_model=dict)
async def get_learning(team_name: str):
    """Get team learning data."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_learning()


@app.get("/teams/{team_name}/agents/{agent_id}/improve", response_model=dict)
async def get_improvement(team_name: str, agent_id: str):
    """Get improvement suggestions for agent."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].improve_agent(agent_id)


# ============== STATUS ROUTES ==============

@app.get("/status", response_model=dict)
async def get_status():
    """Get system status."""
    return {
        "teams": len(teams),
        "total_agents": sum(len(t.agents) for t in teams.values()),
    }


@app.get("/health", response_model=dict)
async def health_check():
    """Health check."""
    return {"status": "healthy"}


# ============== DOCUMENTATION ==============

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Agent-Flow Team API",
        "version": "0.2.0",
        "description": "Collaborative multi-agent teams powered by Hermes",
        "docs": "/docs",
        "features": [
            "Dynamic agent creation - no hardcoded agents",
            "Shared environment - agents work in same workspace",
            "Inter-agent communication - agents can message each other",
            "Goal-oriented execution - team works towards common goal",
            "Learning system - agents improve over time",
        ],
    }
