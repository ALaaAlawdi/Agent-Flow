"""Combined FastAPI app for Agent Team System."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from agent_flow.agents import AgentTeam, DemoRunner, SCENARIOS
from hermes_cli.toolset_validation import validate_platform_toolsets


# ---- Authentication Middleware ----
class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Optional API key authentication for production."""

    def __init__(self, app):
        super().__init__(app)
        self.api_key = None
        import os
        self.api_key = os.getenv("API_KEY", "").strip()
        print(f"  🔑 API authentication: {'ENABLED' if self.api_key else 'DISABLED (no API_KEY set)'}")

    async def dispatch(self, request: Request, call_next):
        # Skip auth for health check and docs in all cases
        if request.url.path in ("/health", "/docs", "/openapi.json", "/demo", "/"):
            return await call_next(request)

        if self.api_key:
            req_key = request.headers.get("X-API-Key", "")
            if req_key != self.api_key:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized. Provide X-API-Key header."}
                )

        return await call_next(request)


# ---- Rate Limiting Middleware (simple in-memory) ----
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter."""

    def __init__(self, app):
        super().__init__(app)
        self.requests: dict[str, list[float]] = {}
        from datetime import datetime
        self._datetime = datetime
        import os
        self.rate_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health",):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = self._datetime.now().timestamp()

        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Clean old entries
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if now - t < 60
        ]

        if len(self.requests[client_ip]) >= self.rate_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again in a minute."}
            )

        self.requests[client_ip].append(now)
        return await call_next(request)


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

# Authentication (optional — enabled if API_KEY is set)
app.add_middleware(APIKeyAuthMiddleware)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

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
    model: Optional[str] = None  # e.g., "gpt-4o", "gpt-4o-mini" (defaults to gpt-4o-mini)


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


class AddQueueTaskRequest(BaseModel):
    """Request to add a task to queue."""
    description: str
    priority: int = 5  # 1=low, 5=normal, 10=high, 20=urgent


class CompleteTaskRequest(BaseModel):
    """Request to complete a task."""
    task_id: str
    result: str


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
        model=request.model,
    )

    return {
        "status": "added",
        "team": team_name,
        "agent_id": request.agent_id,
        "role": request.role,
        "model": request.model or "gpt-4o-mini (default)",
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


# ============== TASK QUEUE ROUTES ==============

@app.post("/teams/{team_name}/queue/tasks", response_model=dict)
async def add_queue_task(team_name: str, request: AddQueueTaskRequest):
    """Add a task to the queue."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    from agent_flow.agents import TaskPriority
    priority = TaskPriority(request.priority)
    task = teams[team_name].add_task(request.description, priority)
    
    return {
        "status": "added",
        "task_id": task.id,
        "description": task.description,
        "priority": task.priority.value,
    }


@app.get("/teams/{team_name}/queue/tasks", response_model=dict)
async def list_queue_tasks(team_name: str, status: Optional[str] = None):
    """List tasks in the queue."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams[team_name]
    tasks = team.queue.get_all()
    
    if status:
        from agent_flow.agents import TaskStatus
        tasks = [t for t in tasks if t.status == TaskStatus(status)]
    
    return {
        "tasks": [t.to_dict() for t in tasks],
        "count": len(tasks),
    }


@app.get("/teams/{team_name}/queue/tasks/next", response_model=dict)
async def get_next_task(team_name: str, agent_id: Optional[str] = None):
    """Get next task for an agent."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    task = teams[team_name].get_next_task(agent_id)
    if not task:
        return {"task": None, "message": "No pending tasks"}
    
    return {"task": task.to_dict()}


@app.post("/teams/{team_name}/queue/tasks/{task_id}/complete", response_model=dict)
async def complete_task(team_name: str, task_id: str, request: CompleteTaskRequest):
    """Mark a task as completed."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    teams[team_name].complete_task(task_id, request.result)
    return {"status": "completed", "task_id": task_id}


@app.get("/teams/{team_name}/queue/stats", response_model=dict)
async def get_queue_stats(team_name: str):
    """Get queue statistics."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_queue_stats()


# ============== EVENT ROUTES ==============

@app.get("/teams/{team_name}/timeline", response_model=dict)
async def get_timeline(team_name: str, limit: int = 50):
    """Get team timeline."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"timeline": teams[team_name].get_timeline(limit)}


@app.get("/teams/{team_name}/agents/{agent_id}/history", response_model=dict)
async def get_agent_history(team_name: str, agent_id: str, limit: int = 50):
    """Get agent history."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"history": teams[team_name].get_agent_history(agent_id, limit)}


# ============== WORKFLOW ROUTES ==============

class CreateWorkflowRequest(BaseModel):
    """Request to create a workflow."""
    name: str
    description: Optional[str] = ""


class AddWorkflowStepRequest(BaseModel):
    """Request to add a workflow step."""
    name: str
    agent_id: str
    task: str
    depends_on: Optional[list[str]] = None


# Workflow storage
workflows: dict[str, Any] = {}


@app.post("/teams/{team_name}/workflows", response_model=dict)
async def create_workflow(team_name: str, request: CreateWorkflowRequest):
    """Create a new workflow."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    from agent_flow.agents import WorkflowEngine
    team = teams[team_name]
    
    if not hasattr(team, 'workflow_engine'):
        team.workflow_engine = WorkflowEngine(team)
    
    workflow = team.workflow_engine.create_workflow(request.name, request.description)
    
    return {
        "status": "created",
        "workflow_id": workflow.id,
        "name": workflow.name,
    }


@app.post("/teams/{team_name}/workflows/{workflow_id}/steps", response_model=dict)
async def add_workflow_step(team_name: str, workflow_id: str, request: AddWorkflowStepRequest):
    """Add a step to a workflow."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams[team_name]
    if not hasattr(team, 'workflow_engine'):
        raise HTTPException(status_code=404, detail="Workflow engine not initialized")
    
    workflow = team.workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    step = workflow.add_step(
        name=request.name,
        agent_id=request.agent_id,
        task=request.task,
        depends_on=request.depends_on,
    )
    
    return {
        "status": "added",
        "step_id": step.id,
        "name": step.name,
    }


@app.get("/teams/{team_name}/workflows", response_model=dict)
async def list_workflows(team_name: str, status: Optional[str] = None):
    """List workflows."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams[team_name]
    if not hasattr(team, 'workflow_engine'):
        return {"workflows": [], "count": 0}
    
    from agent_flow.agents import WorkflowStatus
    status_filter = WorkflowStatus(status) if status else None
    workflow_list = team.workflow_engine.list_workflows(status_filter)
    
    return {
        "workflows": [w.to_dict() for w in workflow_list],
        "count": len(workflow_list),
    }


@app.post("/teams/{team_name}/workflows/{workflow_id}/run", response_model=dict)
async def run_workflow(team_name: str, workflow_id: str, parallel: bool = False):
    """Run a workflow."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams[team_name]
    if not hasattr(team, 'workflow_engine'):
        raise HTTPException(status_code=404, detail="Workflow engine not initialized")
    
    import asyncio
    result = await team.workflow_engine.run_workflow(workflow_id, parallel)
    return result


# ============== TEMPLATE ROUTES ==============

@app.get("/templates", response_model=dict)
async def list_templates():
    """List available agent templates."""
    from agent_flow.agents import list_templates as get_templates
    return {"templates": get_templates(), "count": len(get_templates())}


@app.get("/templates/{template_id}", response_model=dict)
async def get_template(template_id: str):
    """Get a template by ID."""
    from agent_flow.agents import get_template as get_tmpl
    template = get_tmpl(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


# ============== SMART HUB ROUTES ==============

@app.get("/teams/{team_name}/hub/status", response_model=dict)
async def get_hub_status(team_name: str):
    """Get smart hub status."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_hub_status()


@app.get("/teams/{team_name}/hub/capabilities", response_model=dict)
async def get_capabilities_map(team_name: str):
    """Get capabilities map."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"capabilities": teams[team_name].get_capabilities_map()}


@app.get("/teams/{team_name}/hub/best-agent", response_model=dict)
async def find_best_agent(team_name: str, task: str):
    """Find best agent for a task."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"agent": teams[team_name].find_best_agent(task)}


@app.get("/teams/{team_name}/hub/team-for-task", response_model=dict)
async def find_team_for_task(team_name: str, task: str, max_agents: int = 3):
    """Find a team of agents for a task."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"agents": teams[team_name].find_team_for_task(task, max_agents)}


@app.post("/teams/{team_name}/hub/decompose", response_model=dict)
async def decompose_goal(team_name: str, goal: str):
    """Decompose a goal into tasks."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"tasks": teams[team_name].decompose_goal(goal)}


class RequestHelpRequest(BaseModel):
    """Request help."""
    from_agent: str
    task: str
    description: str


@app.post("/teams/{team_name}/hub/help", response_model=dict)
async def request_help(team_name: str, request: RequestHelpRequest):
    """Request help from other agents."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    helpers = teams[team_name].request_help(
        request.from_agent,
        request.task,
        request.description,
    )
    return {"helpers": helpers}


# ============== AUTONOMOUS EXECUTION ROUTES ==============

class ExecuteAutonomousRequest(BaseModel):
    """Execute autonomously."""
    goal: str
    max_iterations: int = 10


@app.post("/teams/{team_name}/autonomous", response_model=dict)
async def execute_autonomous(team_name: str, request: ExecuteAutonomousRequest):
    """Execute goal autonomously."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    import asyncio
    result = await teams[team_name].execute_autonomously(
        request.goal,
        request.max_iterations,
    )
    return result


# ============== MEMORY & LEARNING ROUTES ==============

class RememberRequest(BaseModel):
    """Request to store a memory."""
    agent_id: str
    content: str
    importance: float = 0.5
    tags: Optional[list[str]] = None


@app.post("/teams/{team_name}/memory", response_model=dict)
async def store_memory(team_name: str, request: RememberRequest):
    """Store a memory for an agent."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    memory = teams[team_name].remember(
        request.agent_id,
        request.content,
        request.importance,
        request.tags,
    )
    return {"memory_id": memory.id}


@app.get("/teams/{team_name}/memory", response_model=dict)
async def recall_memories(team_name: str, query: str = "", limit: int = 10):
    """Recall relevant memories."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"memories": teams[team_name].recall(query, limit)}


@app.get("/teams/{team_name}/agents/{agent_id}/memory-stats", response_model=dict)
async def get_memory_stats(team_name: str, agent_id: str):
    """Get memory statistics for an agent."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_agent_memory_stats(agent_id)


class RecordTaskResultRequest(BaseModel):
    """Record task result."""
    agent_id: str
    task: str
    result: str
    success: bool
    response_time: float
    complexity: float = 0.5
    helpers: Optional[list[str]] = None


@app.post("/teams/{team_name}/learning/record", response_model=dict)
async def record_task_result(team_name: str, request: RecordTaskResultRequest):
    """Record task result for learning."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    teams[team_name].record_task_result(
        request.agent_id,
        request.task,
        request.result,
        request.success,
        request.response_time,
        request.complexity,
        request.helpers,
    )
    return {"status": "recorded"}


@app.get("/teams/{team_name}/learning/performance/{agent_id}", response_model=dict)
async def get_agent_performance(team_name: str, agent_id: str):
    """Get performance report for an agent."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_performance_report(agent_id)


@app.get("/teams/{team_name}/learning/performance", response_model=dict)
async def get_team_performance(team_name: str):
    """Get team-wide performance analysis."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_team_performance()


@app.get("/teams/{team_name}/learning/suggestions/{agent_id}", response_model=dict)
async def get_agent_suggestions(team_name: str, agent_id: str):
    """Get improvement suggestions for an agent."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"suggestions": teams[team_name].get_suggestions(agent_id)}


@app.get("/teams/{team_name}/learning/suggestions", response_model=dict)
async def get_team_suggestions(team_name: str):
    """Get team-wide improvement suggestions."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"suggestions": teams[team_name].get_team_suggestions()}


@app.post("/teams/{team_name}/learning/auto-improve", response_model=dict)
async def auto_improve(team_name: str):
    """Automatically improve team based on learning."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].auto_improve()


@app.get("/teams/{team_name}/learning/best-practices", response_model=dict)
async def get_best_practices(team_name: str):
    """Get team best practices."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"best_practices": teams[team_name].get_best_practices()}


# ============== PLANNING ROUTES ==============

@app.get("/teams/{team_name}/plan", response_model=dict)
async def create_plan(team_name: str, goal: str):
    """Create a plan for a goal."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].create_plan(goal)


@app.get("/teams/{team_name}/plan/recommend", response_model=dict)
async def get_recommended_plan(team_name: str, goal: str):
    """Get a recommended plan for a goal."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_recommended_plan(goal)


# ============== DECISION ROUTES ==============

class DecideRequest(BaseModel):
    """Make a decision."""
    decision_type: str
    options: list[str]
    context: Optional[dict] = None
    strategy: str = "best_match"


@app.post("/teams/{team_name}/decide", response_model=dict)
async def make_decision(team_name: str, request: DecideRequest):
    """Make a decision."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].decide(
        request.decision_type,
        request.options,
        request.context,
        request.strategy,
    )


class RecordDecisionRequest(BaseModel):
    """Record decision outcome."""
    decision_id: str
    outcome: str
    was_correct: bool


@app.post("/teams/{team_name}/decide/record", response_model=dict)
async def record_decision(team_name: str, request: RecordDecisionRequest):
    """Record decision outcome."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    teams[team_name].record_decision_outcome(
        request.decision_id,
        request.outcome,
        request.was_correct,
    )
    return {"status": "recorded"}


@app.get("/teams/{team_name}/decide/stats", response_model=dict)
async def get_decision_stats(team_name: str):
    """Get decision statistics."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_decision_statistics()


@app.get("/teams/{team_name}/router/adaptive", response_model=dict)
async def route_adaptively(team_name: str, task: str):
    """Route task adaptively."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"agent": teams[team_name].route_task_adaptively(task)}


# ============== NEGOTIATION ROUTES ==============

class NegotiateRequest(BaseModel):
    """Negotiate for resource."""
    requester: str
    provider: str
    resource: str
    amount: int
    priority: int = 5


@app.post("/teams/{team_name}/negotiate", response_model=dict)
async def negotiate(team_name: str, request: NegotiateRequest):
    """Negotiate for a resource."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].negotiate_resource(
        request.requester,
        request.provider,
        request.resource,
        request.amount,
        request.priority,
    )


class StartNegotiationRequest(BaseModel):
    """Start a negotiation."""
    agent_a: str
    agent_b: str
    topic: str


@app.post("/teams/{team_name}/negotiate/start", response_model=dict)
async def start_negotiation(team_name: str, request: StartNegotiationRequest):
    """Start a negotiation."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].start_negotiation(
        request.agent_a,
        request.agent_b,
        request.topic,
    )


class ResolveConflictRequest(BaseModel):
    """Resolve a conflict."""
    conflict_type: str
    agents: list[str]
    details: dict


@app.post("/teams/{team_name}/conflict/resolve", response_model=dict)
async def resolve_conflict(team_name: str, request: ResolveConflictRequest):
    """Resolve a conflict."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].resolve_conflict(
        request.conflict_type,
        request.agents,
        request.details,
    )


@app.get("/teams/{team_name}/negotiate/stats", response_model=dict)
async def get_negotiation_stats(team_name: str):
    """Get negotiation statistics."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_negotiation_statistics()


# ============== HERMES DEEP INTEGRATION ROUTES ==============

class GoalContractRequest(BaseModel):
    """Goal with Hermes contract."""
    goal: str
    outcome: str
    verification: str
    constraints: str = ""
    boundaries: str = ""
    stop_when: str = ""


@app.post("/teams/{team_name}/hermes/goal", response_model=dict)
async def set_goal_contract(team_name: str, request: GoalContractRequest):
    """Set a structured goal with Hermes contract."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].set_goal_contract(
        request.goal,
        request.outcome,
        request.verification,
        request.constraints,
        request.boundaries,
        request.stop_when,
    )


class SubgoalRequest(BaseModel):
    """Subgoal."""
    subgoal: str


@app.post("/teams/{team_name}/hermes/subgoal", response_model=dict)
async def add_subgoal(team_name: str, request: SubgoalRequest):
    """Add a subgoal."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].add_subgoal(request.subgoal)


@app.get("/teams/{team_name}/hermes/goal/status", response_model=dict)
async def get_goal_status(team_name: str):
    """Get goal status."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_goal_status()


class PauseGoalRequest(BaseModel):
    """Pause goal."""
    reason: str = ""


@app.post("/teams/{team_name}/hermes/goal/pause", response_model=dict)
async def pause_goal(team_name: str, request: PauseGoalRequest):
    """Pause the current goal."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].pause_goal(request.reason)


@app.post("/teams/{team_name}/hermes/goal/resume", response_model=dict)
async def resume_goal(team_name: str):
    """Resume paused goal."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].resume_goal()


class DecomposeRequest(BaseModel):
    """Decompose task."""
    task_id: str
    author: Optional[str] = None


@app.post("/teams/{team_name}/hermes/decompose", response_model=dict)
async def decompose_task(team_name: str, request: DecomposeRequest):
    """Decompose a task using Hermes."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].decompose_task_hermes(request.task_id, request.author)


@app.get("/teams/{team_name}/hermes/moa/presets", response_model=dict)
async def list_moa_presets(team_name: str):
    """List MoA presets."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"presets": teams[team_name].list_moa_presets()}


@app.get("/teams/{team_name}/hermes/moa/preset/{name}", response_model=dict)
async def resolve_moa_preset(team_name: str, name: str):
    """Resolve MoA preset."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].resolve_moa_preset(name)


@app.get("/teams/{team_name}/hermes/moa/consensus", response_model=dict)
async def build_consensus_prompt(team_name: str, question: str, model_count: int = 3):
    """Build consensus prompt."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    prompt = teams[team_name].build_consensus_prompt(question, model_count)
    return {"prompt": prompt}


@app.get("/teams/{team_name}/hermes/checkpoints", response_model=dict)
async def list_checkpoints(team_name: str):
    """List checkpoints."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"checkpoints": teams[team_name].list_checkpoints()}


@app.get("/teams/{team_name}/hermes/checkpoints/status", response_model=dict)
async def get_checkpoint_status(team_name: str):
    """Get checkpoint status."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_checkpoint_status()


class SessionAcquireRequest(BaseModel):
    """Session acquire."""
    session_id: str


@app.post("/teams/{team_name}/hermes/sessions/acquire", response_model=dict)
async def acquire_session(team_name: str, request: SessionAcquireRequest):
    """Acquire session slot."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    acquired = teams[team_name].acquire_session(request.session_id)
    return {"acquired": acquired}


@app.post("/teams/{team_name}/hermes/sessions/release", response_model=dict)
async def release_session(team_name: str, request: SessionAcquireRequest):
    """Release session slot."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    teams[team_name].release_session(request.session_id)
    return {"released": True}


@app.get("/teams/{team_name}/hermes/sessions/snapshot", response_model=dict)
async def get_sessions_snapshot(team_name: str):
    """Get active sessions snapshot."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_active_sessions_snapshot()


@app.get("/teams/{team_name}/hermes/skills", response_model=dict)
async def discover_skills(team_name: str):
    """Discover Hermes skills."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"skills": teams[team_name].discover_skills()}


@app.get("/teams/{team_name}/hermes/status", response_model=dict)
async def get_hermes_status(team_name: str):
    """Get Hermes integration status."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_hermes_status()


# ============== INTERACTION TRACKING ROUTES (for UI) ==============

@app.get("/teams/{team_name}/interactions", response_model=dict)
async def get_interactions(
    team_name: str,
    type: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 100,
):
    """Get interaction stream for UI display.
    
    Query params:
    - type: Filter by interaction type (e.g., 'message_sent', 'task_completed')
    - agent_id: Filter by agent
    - limit: Max number of interactions
    """
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    interactions = teams[team_name].get_interaction_stream(
        interaction_type=type,
        agent_id=agent_id,
        limit=limit,
    )
    
    return {
        "interactions": interactions,
        "count": len(interactions),
    }


@app.get("/teams/{team_name}/interactions/timeline", response_model=dict)
async def get_interaction_timeline(team_name: str, limit: int = 500):
    """Get full timeline of interactions (chronological)."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {
        "timeline": teams[team_name].get_interaction_timeline(limit=limit),
    }


@app.get("/teams/{team_name}/interactions/stats", response_model=dict)
async def get_interaction_stats(team_name: str):
    """Get interaction statistics for dashboard."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_interaction_statistics()


@app.get("/teams/{team_name}/interactions/active-agents", response_model=dict)
async def get_active_agents(team_name: str):
    """Get currently active agents based on recent interactions."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {
        "active_agents": teams[team_name].get_active_agents(),
    }


@app.get("/teams/{team_name}/interactions/graph", response_model=dict)
async def get_interaction_graph(team_name: str):
    """Get interaction graph for visualization (nodes + edges)."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].get_interaction_graph()


# ============== CONVERSATION ROUTES ==============

class StartConversationRequest(BaseModel):
    """Start conversation."""
    participants: list[str]
    topic: str = ""


@app.post("/teams/{team_name}/conversations", response_model=dict)
async def start_conversation(team_name: str, request: StartConversationRequest):
    """Start a conversation between agents."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    conv_id = teams[team_name].start_conversation(
        request.participants,
        request.topic,
    )
    
    return {"conversation_id": conv_id}


class ConversationMessageRequest(BaseModel):
    """Message in conversation."""
    sender: str
    content: str
    type: str = "text"


@app.post("/teams/{team_name}/conversations/{conv_id}/messages", response_model=dict)
async def add_conversation_message(
    team_name: str,
    conv_id: str,
    request: ConversationMessageRequest,
):
    """Add a message to conversation."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    msg = teams[team_name].add_conversation_message(
        conv_id,
        request.sender,
        request.content,
        request.type,
    )
    
    if not msg:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return msg


@app.get("/teams/{team_name}/conversations/{conv_id}", response_model=dict)
async def get_conversation(team_name: str, conv_id: str):
    """Get a conversation by ID."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    conv = teams[team_name].get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conv


@app.get("/teams/{team_name}/conversations", response_model=dict)
async def list_conversations(
    team_name: str,
    participant: Optional[str] = None,
    limit: int = 50,
):
    """List conversations."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {
        "conversations": teams[team_name].list_conversations(participant, limit),
    }


# ============== WEBSOCKET FOR LIVE INTERACTIONS ==============

try:
    from fastapi import WebSocket, WebSocketDisconnect
    
    @app.websocket("/teams/{team_name}/ws/interactions")
    async def websocket_interactions(websocket: WebSocket, team_name: str):
        """WebSocket endpoint for live interaction stream."""
        await websocket.accept()
        
        if team_name not in teams:
            await websocket.send_json({"error": "Team not found"})
            await websocket.close()
            return
        
        # Subscribe to interaction stream
        async def send_interaction(interaction_dict):
            try:
                await websocket.send_json(interaction_dict)
            except Exception:
                pass
        
        # Sync callback for the stream
        def sync_callback(interaction_dict):
            # Schedule async send
            import asyncio
            asyncio.create_task(send_interaction(interaction_dict))
        
        teams[team_name].subscribe_to_interactions(sync_callback)
        
        try:
            # Send initial state
            await websocket.send_json({
                "type": "connected",
                "team": team_name,
                "message": "Subscribed to interaction stream",
            })
            
            # Keep connection alive
            while True:
                data = await websocket.receive_text()
                # Echo back or handle client messages
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            teams[team_name].unsubscribe_from_interactions(sync_callback)
        except Exception:
            teams[team_name].unsubscribe_from_interactions(sync_callback)
            try:
                await websocket.close()
            except Exception:
                pass

except ImportError:
    # WebSocket not available
    pass


# ============== PERSISTENCE ROUTES ==============

@app.post("/teams/{team_name}/persist", response_model=dict)
async def persist_team(team_name: str):
    """Manually trigger persistence save."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    teams[team_name].auto_persistence.flush()
    return {"status": "saved"}


@app.get("/teams/{team_name}/history", response_model=dict)
async def get_team_history(
    team_name: str,
    type: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 100,
):
    """Get team history from disk (persisted)."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    history = teams[team_name].persistence.load_interactions(
        team_name=team_name,
        limit=limit,
        interaction_type=type,
        agent_id=agent_id,
    )
    
    return {
        "history": history,
        "count": len(history),
        "persisted": True,
    }


@app.get("/teams/{team_name}/stats", response_model=dict)
async def get_team_db_stats(team_name: str):
    """Get team statistics from database."""
    if team_name not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return teams[team_name].persistence.get_team_stats(team_name)


@app.get("/teams", response_model=dict)
async def list_all_teams():
    """List all teams in the database."""
    # Use the first team's persistence manager to access all teams
    if not teams:
        return {"teams": []}
    
    first_team = next(iter(teams.values()))
    return {"teams": first_team.persistence.list_teams()}


# ============== DEMO SCENARIOS ROUTES ==============

@app.get("/scenarios", response_model=dict)
async def list_scenarios():
    """List all available demo scenarios.
    
    Each scenario pre-fills a team with agents and runs them
    through a realistic workflow. Perfect for UI demos.
    """
    return {
        "scenarios": DemoRunner.list_scenarios(),
    }


@app.get("/scenarios/{scenario_id}", response_model=dict)
async def get_scenario(scenario_id: str):
    """Get details of a specific scenario."""
    scenario = DemoRunner.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    return {
        **scenario.to_dict(),
        "team_config": scenario.team_config,
        "steps": scenario.run_steps,
    }


@app.post("/scenarios/{scenario_id}/run", response_model=dict)
async def run_scenario(scenario_id: str):
    """Run a demo scenario - pre-fills team, agents, and executes steps.
    
    Returns a summary with:
    - Number of agents added
    - Steps executed
    - Final stats
    """
    result = await DemoRunner.run_scenario(scenario_id, teams)
    return result


# ============== MODELS ROUTES ==============

@app.get("/models", response_model=dict)
async def list_models():
    """List all available AI models (OpenAI is default)."""
    from agent_flow.agents.factory import DynamicAgentFactory
    
    return {
        "models": DynamicAgentFactory.list_available_models(),
        "default": DynamicAgentFactory.DEFAULT_MODEL,
        "providers": ["openai", "anthropic", "google", "meta"],
    }


@app.get("/models/default", response_model=dict)
async def get_default_model():
    """Get the default model."""
    from agent_flow.agents.factory import DynamicAgentFactory
    
    return {
        "default_model": DynamicAgentFactory.DEFAULT_MODEL,
        "note": "All agents use OpenAI models by default",
    }


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
        "version": "0.3.0",
        "description": "Collaborative multi-agent teams powered by Hermes + OpenAI",
        "docs": "/docs",
        "demo_ui": "/demo",
        "scenarios": "/scenarios",
        "models": "/models",
        "features": [
            "Dynamic agent creation - no hardcoded agents",
            "21 cognitive capabilities (superhuman AI)",
            "OpenAI models by default (gpt-4o-mini)",
            "Real-time interaction tracking",
            "Pre-built demo scenarios (one-click)",
            "Persistent history (survives restart)",
            "WebSocket live updates",
        ],
    }


@app.get("/demo")
async def demo_ui():
    """Serve the demo HTML page."""
    from fastapi.responses import HTMLResponse
    from pathlib import Path
    
    demo_path = Path(__file__).parent.parent.parent.parent / "demo.html"
    if demo_path.exists():
        return HTMLResponse(content=demo_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Demo file not found</h1>", status_code=404)
