# Dynamic Multi-Agent System (Hermes-Powered)

## Vision
A system where users create dynamic agents that run independently and communicate automatically - **built entirely on Hermes package**.

---

## Hermes Package as Foundation

```python
# All agent functionality comes from Hermes
from run_agent import AIAgent           # Core agent engine
from batch_runner import BatchRunner    # Parallel execution
from hermes_cli.profiles import get_profile_dir  # Storage
from hermes_cli.toolset_validation import validate_platform_toolsets
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Dynamic Agent System                             │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │                      API Layer                               │      │
│  │   POST /agents → DynamicAgentFactory                        │      │
│  │   POST /run    → DynamicWorkflow                           │      │
│  └─────────────────────────────────────────────────────────────┘      │
│                                  │                                    │
│                                  ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │                  Factory Layer                               │      │
│  │   DynamicAgentFactory:                                      │      │
│  │   - create_agent(config) → AIAgent                         │      │
│  │   - validate_tools(config.tools) → hermes_cli             │      │
│  │   - register(agent) → Hermes profiles                      │      │
│  └─────────────────────────────────────────────────────────────┘      │
│                                  │                                    │
│                                  ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │                  Hermes Layer (THE ENGINE)                  │      │
│  │                                                               │      │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │      │
│  │   │  AIAgent    │    │  AIAgent    │    │  AIAgent    │   │      │
│  │   │ (dynamic)   │    │ (dynamic)   │    │ (dynamic)   │   │      │
│  │   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘   │      │
│  │          │                   │                   │            │      │
│  │          └───────────────────┼───────────────────┘            │      │
│  │                              ▼                                │      │
│  │                    ┌─────────────┐                           │      │
│  │                    │BatchRunner  │◄── parallel execution    │      │
│  │                    └─────────────┘                           │      │
│  │                                                               │      │
│  └─────────────────────────────────────────────────────────────┘      │
│                                  │                                    │
│                                  ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │                  Storage Layer (Hermes Profiles)             │      │
│  │   get_profile_dir() / "networks" / {agent_id}              │      │
│  └─────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Components (All Hermes-Powered)

### 1. DynamicAgentFactory - Creates agents from config

```python
from run_agent import AIAgent
from hermes_cli.toolset_validation import validate_platform_toolsets
from hermes_cli.profiles import get_profile_dir
import json
from pathlib import Path

class DynamicAgentFactory:
    """Factory that creates AIAgent instances from user config"""
    
    def __init__(self, network_name: str = "default"):
        self.network_name = network_name
        self.profile_dir = get_profile_dir() / "networks" / network_name
        self.profile_dir.mkdir(parents=True, exist_ok=True)
    
    def create_agent(self, config: dict) -> AIAgent:
        """
        Create Hermes AIAgent from user configuration.
        
        POST /agents with:
        {
            "name": "my-researcher",
            "role": "researcher",
            "tools": ["web"],
            "system_prompt": "You are a researcher...",
            "model": "claude-sonnet-4",
            "max_iterations": 50
        }
        """
        
        # 1. Validate tools using Hermes
        validate_platform_toolsets(config.get("tools", []))
        
        # 2. Build system prompt
        system_prompt = self._build_prompt(config)
        
        # 3. Create Hermes AIAgent (THE CORE)
        agent = AIAgent(
            name=config["name"],
            enabled_toolsets=config.get("tools", ["web"]),
            ephemeral_system_prompt=system_prompt,
            max_iterations=config.get("max_iterations", 50),
            model=config.get("model", "claude-sonnet-4"),
            
            # Callbacks for tracking
            tool_progress_callback=self._on_tool,
            step_callback=self._on_step,
        )
        
        # 4. Save config to Hermes profile storage
        self._save_config(config)
        
        return agent
    
    def _build_prompt(self, config: dict) -> str:
        """Build system prompt from config"""
        role = config.get("role", "assistant")
        custom = config.get("system_prompt", "")
        
        return f"""
# Agent: {config['name']}
Role: {role}

{custom}

# Communication
You can message other agents using: @agent-name: message
Share findings with your team.
"""
    
    def _save_config(self, config: dict):
        """Save to Hermes profile directory"""
        agent_dir = self.profile_dir / config["name"]
        agent_dir.mkdir(exist_ok=True)
        (agent_dir / "config.json").write_text(json.dumps(config, indent=2))
```

### 2. DynamicAgentRegistry - Stores running agents

```python
class DynamicAgentRegistry:
    """Registry storing active AIAgent instances"""
    
    def __init__(self):
        self.agents: Dict[str, AIAgent] = {}
        self.configs: Dict[str, dict] = {}
    
    def register(self, agent_id: str, agent: AIAgent, config: dict):
        """Register running agent"""
        self.agents[agent_id] = agent
        self.configs[agent_id] = config
    
    def get(self, agent_id: str) -> AIAgent:
        """Get running agent"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> list[dict]:
        """List all registered agents"""
        return [
            {"id": id, "config": self.configs[id]}
            for id in self.agents.keys()
        ]
    
    def find_by_role(self, role: str) -> list[str]:
        """Find agents by role"""
        return [
            id for id, cfg in self.configs.items()
            if cfg.get("role") == role
        ]
```

### 3. AgentCommunication - Inter-agent messaging

```python
import uuid
from datetime import datetime

class AgentCommunication:
    """Message broker using Hermes profile storage"""
    
    def __init__(self, profile_dir: Path):
        self.profile_dir = profile_dir
        self.profile_dir.mkdir(parents=True, exist_ok=True)
    
    def send_message(self, from_agent: str, to_agent: str, content: str):
        """Send message between agents"""
        msg = {
            "id": str(uuid.uuid4()),
            "from": from_agent,
            "to": to_agent,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Store in Hermes profile
        msg_file = self.profile_dir / "messages" / f"{to_agent}.jsonl"
        msg_file.parent.mkdir(exist_ok=True)
        with open(msg_file, "a") as f:
            f.write(json.dumps(msg) + "\n")
    
    def get_messages(self, agent_id: str) -> list[dict]:
        """Get pending messages for agent"""
        msg_file = self.profile_dir / "messages" / f"{agent_id}.jsonl"
        if not msg_file.exists():
            return []
        
        messages = []
        with open(msg_file) as f:
            for line in f:
                messages.append(json.loads(line))
        
        # Clear after reading
        msg_file.unlink()
        return messages
```

### 4. DynamicWorkflow - Execute with Hermes

```python
from run_agent import AIAgent

class DynamicWorkflow:
    """Execute tasks using Hermes AIAgent"""
    
    def __init__(self, registry: DynamicAgentRegistry, comm: AgentCommunication):
        self.registry = registry
        self.comm = comm
    
    async def run_single(self, agent_id: str, task: str) -> dict:
        """Run single agent"""
        agent = self.registry.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Check for messages first
        messages = self.comm.get_messages(agent_id)
        context = self._build_context(task, messages)
        
        # Run via Hermes
        result = agent.chat(context)
        
        return {
            "agent_id": agent_id,
            "result": result,
            "messages_received": len(messages),
        }
    
    async def run_team(self, agent_ids: list[str], task: str) -> dict:
        """Run multiple agents with communication"""
        results = {}
        
        for agent_id in agent_ids:
            # Get messages from teammates
            messages = self.comm.get_messages(agent_id)
            
            # Build context with team context
            context = self._build_context(task, messages, results)
            
            # Run agent
            agent = self.registry.get(agent_id)
            result = agent.chat(context)
            
            results[agent_id] = result
            
            # Broadcast to collaborators
            config = self.registry.configs[agent_id]
            for collaborator in config.get("collaborates_with", []):
                collab_ids = self.registry.find_by_role(collaborator)
                for collab_id in collab_ids:
                    self.comm.send_message(
                        agent_id, collab_id,
                        f"Completed: {result[:200]}..."
                    )
        
        return results
    
    def _build_context(self, task: str, messages: list, previous_results: dict = None) -> str:
        """Build context prompt"""
        context = f"Task: {task}\n"
        
        if messages:
            context += "\nMessages from team:\n"
            for msg in messages:
                context += f"- {msg['from']}: {msg['content']}\n"
        
        if previous_results:
            context += "\nPrevious agent results:\n"
            for agent_id, result in previous_results.items():
                context += f"- {agent_id}: {result[:300]}...\n"
        
        return context
```

---

## API Layer (FastAPI + Hermes)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

# Storage
factory = DynamicAgentFactory("my-network")
registry = DynamicAgentRegistry()
comm = AgentCommunication(factory.profile_dir)
workflow = DynamicWorkflow(registry, comm)

# Models
class AgentConfig(BaseModel):
    name: str
    role: str
    tools: List[str]
    system_prompt: Optional[str] = None
    model: Optional[str] = "claude-sonnet-4"
    max_iterations: Optional[int] = 50
    collaborates_with: Optional[List[str]] = None

class TaskRequest(BaseModel):
    task: str
    agent_ids: Optional[List[str]] = None  # If None, auto-select

# Routes
@app.post("/agents")
def create_agent(config: AgentConfig):
    """Create dynamic agent from config"""
    try:
        # Validate tools via Hermes
        validate_platform_toolsets(config.tools)
        
        # Create AIAgent
        agent = factory.create_agent(config.dict())
        
        # Register
        registry.register(config.name, agent, config.dict())
        
        return {"status": "created", "agent_id": config.name}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/agents")
def list_agents():
    """List all agents"""
    return {"agents": registry.list_agents()}

@app.post("/agents/{agent_id}/run")
def run_agent(agent_id: str, request: TaskRequest):
    """Run single agent"""
    import asyncio
    result = asyncio.run(workflow.run_single(agent_id, request.task))
    return result

@app.post("/run")
def run_team(request: TaskRequest):
    """Run team workflow"""
    import asyncio
    
    agent_ids = request.agent_ids
    if not agent_ids:
        # Auto-select based on task
        # Simple: find all available
        agent_ids = list(registry.agents.keys())
    
    result = asyncio.run(workflow.run_team(agent_ids, request.task))
    return {"results": result}

@app.get("/agents/{agent_id}/messages")
def get_messages(agent_id: str):
    """Get pending messages"""
    return {"messages": comm.get_messages(agent_id)}
```

---

## Usage Example

```bash
# 1. Create researcher agent
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "market-researcher",
    "role": "researcher",
    "tools": ["web"],
    "system_prompt": "You find market data and trends.",
    "collaborates_with": ["coder"]
  }'

# 2. Create coder agent
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "backend-coder",
    "role": "coder", 
    "tools": ["terminal", "file"],
    "collaborates_with": ["researcher"]
  }'

# 3. Run task - they communicate automatically
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Build a market analysis API for Saudi Arabia"
  }'

# Response:
{
  "results": {
    "market-researcher": "Found: Saudi market growth 5.2%...",
    "backend-coder": "Created: /api/market/analysis endpoint..."
  }
}
```

---

## File Structure

```
agent_flow/agents/
├── __init__.py
├── factory.py           # DynamicAgentFactory (AIAgent creation)
├── registry.py         # DynamicAgentRegistry (active agents)
├── communication.py   # AgentCommunication (messages)
├── workflow.py        # DynamicWorkflow (execution)
└── api/
    ├── __init__.py
    └── main.py        # FastAPI endpoints
```

---

## What Comes From Hermes

| Component | Hermes Source |
|-----------|---------------|
| Agent Engine | `run_agent.AIAgent` |
| Parallel Execution | `batch_runner.BatchRunner` |
| Storage | `hermes_cli.profiles.get_profile_dir()` |
| Tool Validation | `hermes_cli.toolset_validation` |
| Profiles | `hermes_cli.profiles` |

---

## Implementation Priority

1. **factory.py** - Create AIAgent from config (uses Hermes)
2. **registry.py** - Track running agents
3. **communication.py** - Message passing via profile storage
4. **workflow.py** - Task execution
5. **api/main.py** - FastAPI endpoints
6. **Tests** - Verify Hermes integration

---

Ready to implement? The entire system is built on Hermes package - no custom agent logic needed.
