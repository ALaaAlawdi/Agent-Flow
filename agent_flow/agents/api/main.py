"""FastAPI endpoints for Dynamic Agent System."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Agent system imports
from agent_flow.agents import (
    DynamicAgentFactory,
    DynamicAgentRegistry,
    AgentCommunication,
    DynamicWorkflow,
)


# Initialize app
app = FastAPI(
    title="Agent-Flow Dynamic Agent API",
    description="Create and manage dynamic AI agents powered by Hermes",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
factory = DynamicAgentFactory("default")
registry = DynamicAgentRegistry()
communication = AgentCommunication("default")
workflow = DynamicWorkflow(registry, communication)


# ============== MODELS ==============

class AgentConfig(BaseModel):
    """Configuration for creating a new agent."""
    name: str
    role: str
    tools: list[str]
    system_prompt: Optional[str] = None
    model: str = "claude-sonnet-4"
    max_iterations: int = 50
    collaborates_with: Optional[list[str]] = None


class AgentUpdate(BaseModel):
    """Configuration for updating an agent."""
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    max_iterations: Optional[int] = None
    collaborates_with: Optional[list[str]] = None


class TaskRequest(BaseModel):
    """Request to run a task."""
    task: str
    agent_ids: Optional[list[str]] = None
    mode: str = "team"  # team, sequential, parallel
    required_roles: Optional[list[str]] = None


class MessageRequest(BaseModel):
    """Request to send a message."""
    to_agent: str
    content: str
    urgency: str = "normal"


# ============== AGENT ROUTES ==============

@app.post("/agents", response_model=dict)
async def create_agent(config: AgentConfig):
    """Create a new dynamic agent.
    
    The agent is created using Hermes AIAgent with the provided configuration.
    """
    try:
        # Validate tools via Hermes
        from hermes_cli.toolset_validation import validate_platform_toolsets
        validate_platform_toolsets(config.tools)
        
        # Create agent via factory
        agent = factory.create_agent(
            name=config.name,
            role=config.role,
            tools=config.tools,
            system_prompt=config.system_prompt,
            model=config.model,
            max_iterations=config.max_iterations,
            collaborates_with=config.collaborates_with,
        )
        
        # Register in registry
        registry.register(
            config.name,
            agent,
            config.dict(),
        )
        
        return {
            "status": "created",
            "agent_id": config.name,
            "role": config.role,
            "tools": config.tools,
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/agents", response_model=dict)
async def list_agents():
    """List all registered agents."""
    agents = registry.list_agents()
    return {
        "agents": agents,
        "count": len(agents),
    }


@app.get("/agents/{agent_id}", response_model=dict)
async def get_agent(agent_id: str):
    """Get agent details."""
    config = registry.get_config(agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    status = registry.get_status(agent_id)
    msg_count = communication.get_message_count(agent_id)
    
    return {
        "id": agent_id,
        "config": config,
        "status": status,
        "pending_messages": msg_count,
    }


@app.delete("/agents/{agent_id}", response_model=dict)
async def delete_agent(agent_id: str):
    """Delete an agent."""
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Unregister
    registry.unregister(agent_id)
    
    # Delete from storage
    factory.delete_agent(agent_id)
    
    # Clear messages
    communication.clear_messages(agent_id)
    
    return {"status": "deleted", "agent_id": agent_id}


@app.put("/agents/{agent_id}", response_model=dict)
async def update_agent(agent_id: str, update: AgentUpdate):
    """Update agent configuration.
    
    Note: Some changes may require restarting the agent.
    """
    config = registry.get_config(agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Apply updates
    if update.system_prompt is not None:
        config["system_prompt"] = update.system_prompt
    if update.model is not None:
        config["model"] = update.model
    if update.max_iterations is not None:
        config["max_iterations"] = update.max_iterations
    if update.collaborates_with is not None:
        config["collaborates_with"] = update.collaborates_with
    
    # Save updated config
    factory._save_config(agent_id, config)
    
    return {
        "status": "updated",
        "agent_id": agent_id,
        "config": config,
    }


# ============== TASK ROUTES ==============

@app.post("/agents/{agent_id}/run", response_model=dict)
async def run_single_agent(agent_id: str, request: TaskRequest):
    """Run a single agent on a task."""
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        result = await workflow.run_single(agent_id, request.task)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run", response_model=dict)
async def run_task(request: TaskRequest):
    """Run task with selected agents or auto-selected agents.
    
    - If agent_ids provided: run those specific agents
    - If required_roles provided: auto-select agents with those roles
    - Otherwise: run all online agents
    """
    # Determine which agents to run
    agent_ids = request.agent_ids
    
    if not agent_ids:
        # Auto-select agents
        agent_ids = workflow.auto_select_agents(
            task=request.task,
            required_roles=request.required_roles,
        )
    
    if not agent_ids:
        raise HTTPException(
            status_code=400,
            detail="No agents available. Create agents first.",
        )
    
    # Run in specified mode
    try:
        if request.mode == "sequential":
            results = await workflow.run_sequential(agent_ids, request.task)
        elif request.mode == "parallel":
            results = await workflow.run_parallel(agent_ids, request.task)
        else:  # team
            results = await workflow.run_team(agent_ids, request.task)
        
        return {
            "task": request.task,
            "mode": request.mode,
            "agents_used": agent_ids,
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== MESSAGE ROUTES ==============

@app.post("/messages", response_model=dict)
async def send_message(message: MessageRequest, from_agent: str = "api"):
    """Send a message from one agent to another."""
    # Validate sender exists (or use "api" as system sender)
    if from_agent != "api":
        if not registry.get(from_agent):
            raise HTTPException(status_code=404, detail="Sender agent not found")
    
    if not registry.get(message.to_agent):
        raise HTTPException(status_code=404, detail="Receiver agent not found")
    
    msg_id = communication.send_message(
        from_agent=from_agent,
        to_agent=message.to_agent,
        content=message.content,
        urgency=message.urgency,
    )
    
    return {
        "status": "sent",
        "message_id": msg_id,
        "from": from_agent,
        "to": message.to_agent,
    }


@app.get("/agents/{agent_id}/messages", response_model=dict)
async def get_messages(agent_id: str, peek: bool = False):
    """Get pending messages for an agent."""
    if not registry.get(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if peek:
        messages = communication.peek_messages(agent_id)
    else:
        messages = communication.get_messages(agent_id)
    
    return {
        "agent_id": agent_id,
        "messages": [m.to_dict() for m in messages],
        "count": len(messages),
    }


# ============== STATUS ROUTES ==============

@app.get("/status", response_model=dict)
async def get_status():
    """Get system status."""
    return {
        "agents": {
            "total": len(registry.agents),
            "online": len(registry.get_online_agents()),
        },
        "storage": {
            "profile_dir": str(factory.profile_dir),
            "saved_agents": factory.list_agents(),
        },
    }


@app.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
