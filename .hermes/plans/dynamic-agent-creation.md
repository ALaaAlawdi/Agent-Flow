# Dynamic Agent Creation System (No Hardcoded Agents)

## Vision
Users define their own agents with custom names, roles, tools, and behaviors. Agents are created dynamically at runtime - nothing is hardcoded.

## Core Concept: Agent Factory

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User's Request                                 │
│                                                                       │
│  POST /agents                                                         │
│  {                                                                    │
│    "name": "my-researcher",        # User chooses name             │
│    "role": "researcher",           # Or custom: "data-finder"      │
│    "description": "Finds info",    # What this agent does          │
│    "tools": ["web", "memory"],    # User selects tools             │
│    "system_prompt": "You are...", # Custom instructions            │
│    "collaborates_with": ["coder"]  # Auto-connects to these roles  │
│  }                                                                    │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Dynamic Agent Factory                            │
│                                                                       │
│  1. Validate tools (hermes_cli.toolset_validation)                  │
│  2. Generate unique agent_id                                        │
│  3. Create Hermes AIAgent instance                                  │
│  4. Register in network                                            │
│  5. Auto-link with collaborators                                    │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Running Agent (Dynamic)                            │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │  AIAgent (from run_agent)                                   │      │
│  │  - name: "my-researcher"                                    │      │
│  │  - role: "researcher"                                       │      │
│  │  - tools: ["web", "memory"]                                │      │
│  │  - prompt: "You are a researcher who..."                   │      │
│  └─────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## API: Create Agent (Dynamic)

```python
# POST /agents - Create custom agent
{
    "name": "my-researcher",           # Required: unique name
    "role": "researcher",              # Required: role identifier
    "description": "Finds research",   # Optional: for humans
    "tools": ["web", "memory"],       # Required: from allowed list
    "system_prompt": """              # Optional: custom instructions
        You are a research specialist.
        Focus on finding accurate information.
        Cite your sources.
        Share findings with teammates.
    """,
    "model": "claude-sonnet-4",       # Optional: override default
    "max_iterations": 50,             # Optional: override default
    "collaborates_with": [            # Optional: auto-link agents
        "coder",
        "analyst"
    ],
    "triggers": [                      # Optional: auto-start conditions
        {"on": "task_type", "value": "research"},
        {"on": "message", "contains": "find"}
    ]
}
```

---

## Dynamic Agent Registry

```python
class DynamicAgentRegistry:
    """Registry that stores user-created agents"""
    
    def __init__(self, storage_path: Path):
        self.agents_file = storage_path / "agents.json"
        self.agents: Dict[str, DynamicAgent] = {}
        self._load()
    
    def create(self, config: AgentConfig) -> DynamicAgent:
        """Create agent from user config"""
        
        # Validate tools
        validate_platform_toolsets(config.tools)
        
        # Generate ID if not provided
        agent_id = config.name.lower().replace(" ", "-")
        
        # Build system prompt
        system_prompt = self._build_prompt(config)
        
        # Create Hermes AIAgent
        hermes_agent = AIAgent(
            name=agent_id,
            enabled_toolsets=config.tools,
            ephemeral_system_prompt=system_prompt,
            max_iterations=config.max_iterations or 50,
            model=config.model or "claude-sonnet-4",
        )
        
        # Create dynamic agent
        agent = DynamicAgent(
            id=agent_id,
            name=config.name,
            role=config.role,
            description=config.description,
            tools=config.tools,
            hermes_agent=hermes_agent,
            collaborators=config.collaborates_with or [],
            config=config,
        )
        
        # Store
        self.agents[agent_id] = agent
        self._save()
        
        return agent
    
    def _build_prompt(self, config: AgentConfig) -> str:
        """Build system prompt from user config"""
        return f"""
# Agent: {config.name}

## Role
{config.role}

## Description
{config.description or 'No description provided'}

## Your Capabilities
You have access to: {', '.join(config.tools)}

## Instructions
{custom_system_prompt or 'Complete the given task to the best of your ability.'}

## Collaboration
You work with: {', '.join(config.collaborates_with or ['other agents'])}
When you need help, you can message them.

## Communication Protocol
- To message another agent: @agent-name: your message
- Always share relevant findings with your team
- Ask for help when stuck
"""
```

---

## Automatic Collaboration Setup

```python
class AutoLinker:
    """Automatically connect agents based on config"""
    
    def link_agents(self, agent: DynamicAgent, registry: DynamicAgentRegistry):
        """Link agent to collaborators"""
        
        for collaborator_role in agent.collaborators:
            # Find agents with matching role
            matches = registry.find_by_role(collaborator_role)
            
            for match in matches:
                # Create bidirectional link
                agent.connected_agents.append(match.id)
                match.connected_agents.append(agent.id)
                
                # Tell each about the other
                agent.hermes_agent.add_context(
                    f"Team member: {match.name} ({match.role})"
                )
                match.hermes_agent.add_context(
                    f"Team member: {agent.name} ({agent.role})"
                )
```

---

## Dynamic Workflow Execution

```python
class DynamicWorkflow:
    """Execute workflow with dynamic agents"""
    
    async def run_task(self, task: str, agent_ids: list[str]):
        """Run task with selected agents"""
        
        # 1. Analyze task to determine needed roles
        needed_roles = self._analyze_task(task)
        
        # 2. Find available agents
        available = []
        for role in needed_roles:
            agents = registry.find_by_role(role)
            available.extend(agents)
        
        # 3. If no agent exists for role, create one dynamically
        for role in needed_roles:
            if not registry.find_by_role(role):
                # Auto-create missing agent
                agent = registry.create(AgentConfig(
                    name=f"auto-{role}-001",
                    role=role,
                    tools=self._default_tools_for_role(role),
                ))
                available.append(agent)
        
        # 4. Run agents - they communicate automatically
        results = await self._run_with_communication(task, available)
        
        return results
    
    async def _run_with_communication(self, task: str, agents: list[DynamicAgent]):
        """Run agents with auto-communication"""
        
        # Each agent knows about others via system prompt
        for agent in agents:
            # Inject team info
            team_info = "\n".join([
                f"- {a.name}: {a.role}" 
                for a in agents if a.id != agent.id
            ])
            agent.hermes_agent.add_context(f"Your team:\n{team_info}")
        
        # Run first agent
        current_result = agents[0].run(task)
        
        # Pass results to next agent
        for agent in agents[1:]:
            # Agent automatically sees previous work
            context = f"Previous work:\n{current_result}\n\nTask: {task}"
            current_result = agent.run(context)
        
        return current_result
```

---

## Full API Endpoints

```python
# Agent CRUD
POST   /agents                    # Create dynamic agent
GET    /agents                    # List all agents
GET    /agents/{id}              # Get agent details
PUT    /agents/{id}              # Update agent config
DELETE /agents/{id}              # Delete agent

# Dynamic Execution
POST   /agents/{id}/run           # Run single agent
POST   /run                       # Run task with auto-selected agents

# Team Management
POST   /teams                     # Create team from agents
GET    /teams/{id}               # Get team status
POST   /teams/{id}/run           # Run team workflow

# Communication
GET    /agents/{id}/messages     # Get pending messages
POST   /agents/{id}/message      # Send message to agent

# Templates
GET    /templates                 # List agent templates
POST   /agents/from-template      # Create from template
```

---

## Agent Templates (Not Hardcoded - User Editable)

```python
# Stored in database, user can modify
AGENT_TEMPLATES = [
    {
        "id": "researcher",
        "name": "Researcher",
        "description": "Finds and analyzes information",
        "default_tools": ["web"],
        "default_prompt": "You are a research specialist...",
    },
    {
        "id": "coder", 
        "name": "Coder",
        "description": "Writes and debugs code",
        "default_tools": ["terminal", "file"],
        "default_prompt": "You are a software developer...",
    },
    # Users can add their own templates
]
```

---

## Complete Flow

```
1. User sends POST /agents with custom config
           │
           ▼
2. Factory validates, creates Hermes AIAgent
           │
           ▼
3. Agent registered, linked to collaborators
           │
           ▼
4. User runs task: POST /run with "Build API"
           │
           ▼
5. System finds/creates needed agents
           │
           ▼
6. Agents run with auto-communication
   - Researcher finds requirements
   - Coder writes code (messages researcher if needed)
   - Reviewer checks (messages coder if issues)
           │
           ▼
7. Results returned to user
```

---

## Implementation Structure

```
agent_flow/agents/
├── __init__.py
├── factory.py           # DynamicAgentFactory - creates agents
├── registry.py          # DynamicAgentRegistry - stores user agents
├── templates.py         # Agent templates (user-editable)
├── workflow.py         # DynamicWorkflow - auto-execution
├── types/
│   ├── __init__.py
│   └── dynamic.py     # DynamicAgent class
└── api/
    ├── __init__.py
    ├── main.py
    └── routes.py      # All endpoints
```

---

## Example: User Creates Custom Agent

```bash
# 1. Create custom researcher
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "market-researcher",
    "role": "researcher", 
    "description": "Researches market trends",
    "tools": ["web"],
    "system_prompt": "You specialize in market analysis...",
    "collaborates_with": ["analyst"]
  }'

# 2. Create custom coder  
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "backend-coder",
    "role": "coder",
    "tools": ["terminal", "file"],
    "collaborates_with": ["reviewer"]
  }'

# 3. Run task - system auto-selects agents
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Build a market analysis API"
  }'

# Response:
{
  "task": "Build a market analysis API",
  "agents_used": ["market-researcher", "backend-coder"],
  "results": {
    "market-researcher": {...},
    "backend-coder": {...}
  }
}
```

---

## Key Points

1. **No Hardcoded Agents** - Every agent created from user config
2. **Dynamic Tools** - Users pick from allowed toolsets
3. **Auto-Discovery** - Agents find each other automatically
4. **Templates** - Users can create reusable templates
5. **Auto-Scaling** - System creates agents as needed
6. **Communication** - Agents message each other without hardcoding
