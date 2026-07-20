# Multi-Agent Collaboration System with Inter-Agent Communication

## Vision
Each agent runs independently with its own task, but knows about other agents. When an agent needs information, it can directly message a colleague - like a real workplace.

## Core Concept: Workplace Simulation

```
┌─────────────────────────────────────────────────────────────────┐
│                     Company Network                                │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │  Researcher │    │    Coder    │    │   Reviewer  │        │
│  │  (Task: A)  │    │  (Task: B) │    │  (Task: C)  │        │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘        │
│         │                   │                   │                 │
│         │   "Hey, what's   │                   │                 │
│         │    the API docs?" │                   │                 │
│         ├───────────────────┼───────────────────┤                 │
│         │                   │                   │                 │
│  ┌──────▼──────────────────────────────────────▼──────┐        │
│  │              Message Broker / Hub                    │        │
│  │   - Agent Registry (who's online)                  │        │
│  │   - Message Queue (pending messages)               │        │
│  │   - Delivery Status (read/delivered)              │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                  │
│  ┌────────────────────────────────────────────────────┐        │
│  │              Agent Manager (Orchestrator)           │        │
│  │   - Start/stop agents                             │        │
│  │   - Monitor health                                │        │
│  │   - Route tasks                                   │        │
│  │   - Handle failures                               │        │
│  └────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Agent Registry
```python
class AgentRegistry:
    """Track all agents in the network"""
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
    
    def register(self, agent_id: str, role: str, capabilities: list):
        """Register new agent"""
        self.agents[agent_id] = AgentInfo(
            id=agent_id,
            role=role,
            capabilities=capabilities,
            status="online",  # online, busy, offline
            current_task=None,
        )
    
    def find_by_role(self, role: str) -> List[AgentInfo]:
        """Find agents by role"""
        return [a for a in self.agents.values() if a.role == role]
    
    def find_by_capability(self, capability: str) -> List[AgentInfo]:
        """Find agents who can help with X"""
        return [a for a in self.agents.values() if capability in a.capabilities]
    
    def get_online_agents(self) -> List[AgentInfo]:
        """Get all available agents"""
        return [a for a in self.agents.values() if a.status == "online"]
```

### 2. Message Broker
```python
class MessageBroker:
    """Route messages between agents"""
    
    def __init__(self):
        self.queue: Dict[str, List[Message]] = {}
        self.registry = AgentRegistry()
    
    def send(self, from_agent: str, to_agent: str, content: str, urgency: str = "normal"):
        """Send message to agent"""
        msg = Message(
            id=uuid4(),
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            urgency=urgency,  # low, normal, high, critical
            timestamp=datetime.now(),
        )
        self.queue.setdefault(to_agent, []).append(msg)
        return msg.id
    
    def broadcast(self, from_agent: str, content: str, to_roles: list = None):
        """Send to all agents or specific roles"""
        targets = self.registry.get_online_agents()
        if to_roles:
            targets = [a for a in targets if a.role in to_roles]
        
        for agent in targets:
            self.send(from_agent, agent.id, content)
    
    def receive(self, agent_id: str) -> List[Message]:
        """Get pending messages for agent"""
        return self.queue.pop(agent_id, [])
    
    def check_messages(self, agent_id: str) -> List[Message]:
        """Peek at messages without removing"""
        return self.queue.get(agent_id, [])
```

### 3. Agent Manager (Orchestrator)
```python
class AgentManager:
    """Manage agent lifecycle"""
    
    def __init__(self):
        self.registry = AgentRegistry()
        self.broker = MessageBroker()
        self.agents: Dict[str, AIAgent] = {}
    
    def spawn_agent(self, agent_id: str, role: str, toolsets: list) -> AIAgent:
        """Create new agent process"""
        agent = AIAgent(
            name=agent_id,
            enabled_toolsets=toolsets,
            tool_progress_callback=self._track_progress,
        )
        
        self.registry.register(agent_id, role, toolsets)
        self.agents[agent_id] = agent
        
        return agent
    
    def assign_task(self, agent_id: str, task: str):
        """Send task to agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Update status
        info = self.registry.agents[agent_id]
        info.status = "busy"
        info.current_task = task
        
        # Inject knowledge of other agents into prompt
        context = self._build_context(agent_id)
        full_task = f"""
Other agents in network:
{self.registry.get_online_agents()}

Your ID: {agent_id}
Your Role: {info.role}

Task:
{task}

You can message other agents using: @agent_id: message
"""
        return agent.chat(full_task)
    
    def message_other_agent(self, from_id: str, to_id: str, message: str):
        """Agent communicates with colleague"""
        self.broker.send(from_id, to_id, message)
        
        # Notify receiving agent
        if to_id in self.agents:
            pending = self.broker.check_messages(to_id)
            # Next time agent runs, it will see the message
```

### 4. Agent Communication Protocol
```python
# Every agent's prompt includes this:
COMMUNICATION_PROTOCOL = """
# Inter-Agent Communication

You can communicate with other agents in the network:
- To ask a question: @agent_id: your question here
- To share info: @agent_id: here's what I found

Available agents:
{agent_list}

When you need help:
1. Identify which agent can help
2. Send them a message with @
3. Wait for their response (if urgent, mark as critical)

Examples:
@researcher-001: What's the latest API documentation?
@coder-001: Can you help me debug this error?
"""
```

---

## Agent Types with Communication

| Agent | Role | Knows About | Can Message |
|-------|------|-------------|-------------|
| **Coordinator** | Manage | All | All |
| **Researcher** | Search | Coordinator, Analyst | Coordinator |
| **Coder** | Build | Coordinator, Reviewer | Coordinator, Reviewer |
| **Reviewer** | Verify | Coordinator, Coder | Coordinator, Coder |
| **Analyst** | Data | Coordinator, Researcher | Coordinator, Researcher |

---

## Workflow Example

```python
from agent_flow.agents import AgentManager, AgentRegistry, MessageBroker

# Setup
manager = AgentManager()

# Create team
coordinator = manager.spawn_agent("coord-001", "coordinator", ["web", "memory"])
researcher = manager.spawn_agent("research-001", "researcher", ["web"])
coder = manager.spawn_agent("coder-001", "coder", ["terminal", "file"])
reviewer = manager.spawn_agent("review-001", "reviewer", ["terminal", "file"])

# Assign tasks
manager.assign_task("coord-001", "Build a user authentication API")

# Agent can communicate during work
# researcher-001 messages coder-001:
manager.message_other_agent(
    "research-001", 
    "coder-001", 
    "I found the requirements. Here's what you need..."
)

# Get results
results = {
    "coordinator": coordinator.get_result(),
    "researcher": researcher.get_result(),
    "coder": coder.get_result(),
    "reviewer": reviewer.get_result(),
}
```

---

## API Endpoints

```python
# Agent Management
POST   /agents              # Create agent
GET    /agents              # List agents
GET    /agents/{id}         # Agent status
DELETE /agents/{id}         # Stop agent
POST   /agents/{id}/task   # Assign task

# Messaging
POST   /messages                    # Send message
GET    /agents/{id}/messages        # Get messages
POST   /agents/{id}/broadcast      # Broadcast to role

# Team
POST   /teams              # Create team
GET    /teams/{id}/status  # Team status
POST   /teams/{id}/run     # Run team workflow
```

---

## Implementation Structure

```
agent_flow/agents/
├── __init__.py
├── manager.py           # AgentManager - orchestrator
├── registry.py          # AgentRegistry - track agents
├── broker.py            # MessageBroker - routing
├── protocol.py          # Communication format
├── types/
│   ├── __init__.py
│   ├── base.py        # BaseAgent with messaging
│   ├── coordinator.py
│   ├── researcher.py
│   ├── coder.py
│   └── reviewer.py
└── api/
    ├── __init__.py
    ├── main.py        # FastAPI
    └── routes.py     # Endpoints
```

---

## Communication Flow

```
Agent A needs info from Agent B:

1. Agent A identifies need
   → "I should ask the researcher"

2. Agent A sends message via broker
   → broker.send("agent-a", "researcher-001", "What's the API?")

3. Agent B receives notification
   → Message queued for researcher-001

4. Agent B processes request
   → researcher-001 responds with info

5. Agent A receives response
   → Can continue with the information
```

---

## Next Steps
1. Create `manager.py` - AgentManager class
2. Create `registry.py` - AgentRegistry class
3. Create `broker.py` - MessageBroker class
4. Add communication protocol to prompts
5. Build REST API
6. Add real-time (WebSocket) support
7. Test inter-agent messaging
