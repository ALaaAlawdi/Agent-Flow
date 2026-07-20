# Multi-Agent API System Plan

## Goal
Allow app users to build custom AI agents and make them communicate/collaborate.

## Core Features

### 1. Agent Builder API
- Create agents with custom specs (name, role, toolsets, instructions)
- Agent templates (Researcher, Coder, Reviewer, Analyst)
- Custom system prompts
- Tool permissions per agent

### 2. Agent Communication Hub
- Inter-agent messaging
- Shared context/memory between agents
- Conversation threads
- Real-time collaboration

### 3. Team/Squad Management
- Group agents into teams
- Define roles within teams
- Set collaboration rules

### 4. Execution API
- Run single agent on task
- Run multi-agent workflows
- Sequential & parallel execution
- Result aggregation

---

## API Endpoints Design

### Agents
```
POST   /api/agents              - Create agent
GET    /api/agents             - List user's agents
GET    /api/agents/{id}        - Get agent details
PUT    /api/agents/{id}        - Update agent
DELETE /api/agents/{id}        - Delete agent
POST   /api/agents/{id}/run    - Run agent on task
```

### Teams
```
POST   /api/teams              - Create team
GET    /api/teams              - List teams
GET    /api/teams/{id}         - Get team details
PUT    /api/teams/{id}         - Update team
DELETE /api/teams/{id}         - Delete team
POST   /api/teams/{id}/run     - Run team workflow
POST   /api/teams/{id}/chat    - Agent-to-agent chat
```

### Conversations
```
GET    /api/conversations              - List conversations
GET    /api/conversations/{id}         - Get conversation messages
POST   /api/conversations/{id}/message  - Send message
```

---

## Data Models

### Agent
```python
{
    "id": "uuid",
    "user_id": "uuid",
    "name": "researcher-001",
    "role": "Researcher",  # or custom
    "system_prompt": "You are a research assistant...",
    "toolsets": ["web"],
    "tools": ["search", "scrape", "summarize"],
    "budget": {
        "max_iterations": 50,
        "max_tokens": 100000
    },
    "created_at": "timestamp",
    "updated_at": "timestamp"
}
```

### Team
```python
{
    "id": "uuid",
    "user_id": "uuid",
    "name": "Product Team",
    "description": "Team for product research",
    "agents": [
        {"agent_id": "uuid", "role": "researcher"},
        {"agent_id": "uuid", "role": "coder"},
        {"agent_id": "uuid", "role": "reviewer"}
    ],
    "workflow": "sequential",  # or "parallel", "debate"
    "created_at": "timestamp"
}
```

### Conversation
```python
{
    "id": "uuid",
    "team_id": "uuid",
    "messages": [
        {
            "agent_id": "uuid",
            "role": "sender|receiver",
            "content": "message text",
            "timestamp": "timestamp"
        }
    ]
}
```

---

## Implementation Modules

```
agent_flow/api/
├── __init__.py
├── main.py              # FastAPI app
├── models.py            # Pydantic models
├── routes/
│   ├── __init__.py
│   ├── agents.py        # Agent CRUD + run
│   ├── teams.py         # Team CRUD + run
│   └── conversations.py # Messaging
├── services/
│   ├── __init__.py
│   ├── agent_builder.py # Build agents from specs
│   ├── executor.py       # Run agents (Hermes)
│   ├── orchestrator.py  # Multi-agent coordination
│   └── storage.py       # SQLite persistence
└── dependencies.py       # Auth, validation
```

---

## Execution Flow

### Single Agent Run
```
User Request → API → AgentBuilder → HermesWorkerAdapter → 
Hermes CLI → Result → Store Evidence → Return to User
```

### Multi-Agent Run
```
User Request → API → Orchestrator →
  For each agent:
    → HermesWorkerAdapter → Hermes CLI
  Aggregate Results → Store → Return
```

### Agent Chat
```
Agent A → API → Store Message → 
Notify Agent B → Agent B processes → 
Response → Store → Return
```

---

## Hermes Integration

Use existing `HermesWorkerAdapter`:
```python
from agent_flow.hermes import HermesWorkerAdapter

adapter = HermesWorkerAdapter(
    profile="default",
    toolsets=agent.toolsets,
    workdir="/tmp/agent-workspace"
)
result = adapter.run_task(packet)
```

---

## Next Steps
1. Create FastAPI project structure
2. Implement Agent CRUD
3. Implement Team management
4. Build Hermes executor integration
5. Add conversation/messaging system
6. Add authentication
7. Deploy & test
