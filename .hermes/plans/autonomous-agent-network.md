# Autonomous Agent Network System (Hermes-Powered)

## Vision
Agents that understand each other automatically, share context, and coordinate without human intervention - **powered by Hermes package**.

## Hermes Package Capabilities Used

### 1. `run_agent.AIAgent` - Core Agent Engine
```python
from run_agent import AIAgent

agent = AIAgent(
    model="claude-sonnet-4",
    max_iterations=90,
    enabled_toolsets=["web", "terminal", "file"],
    ephemeral_system_prompt="...",  # Custom prompt
    tool_progress_callback=...,     # Track tools
    step_callback=...,               # Each step
)
result = agent.chat("your task")
```

### 2. `batch_runner.BatchRunner` - Multi-Agent Parallel
```python
from batch_runner import BatchRunner

runner = BatchRunner(
    dataset_file="tasks.jsonl",
    batch_size=10,
    num_workers=4,
    model="claude-sonnet-4",
)
results = runner.run()
```

### 3. `hermes_cli.profiles` - Agent Profiles
```python
from hermes_cli.profiles import list_profiles, get_active_profile_name

profiles = list_profiles()
current = get_active_profile_name()
```

### 4. `hermes_cli.providers` - Model Management
```python
from hermes_cli.providers import ProviderDef, CANONICAL_PROVIDERS

providers = CANONICAL_PROVIDERS  # List of available models
```

### 5. `hermes_cli.toolset_validation` - Tool Permissions
```python
from hermes_cli.toolset_validation import validate_platform_toolsets

validate_platform_toolsets(["web", "terminal"])  # Verify tools
```

All agents share:
- **Common Vocabulary** - Understanding each other's outputs
- **Shared Context** - Real-time state synchronization
- **Protocol** - Standard message format
- **Goals** - Aligned objectives

---

## Hermes-Powered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Network (Hermes)                    │
│                                                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│  │ AIAgent │    │ AIAgent │    │ AIAgent │  ← run_agent   │
│  │   #1    │◄──►│   #2    │◄──►│   #3    │                │
│  └────┬────┘    └────┬────┘    └────┬────┘                │
│       │               │               │                      │
│       └───────────────┼───────────────┘                      │
│                       ▼                                      │
│            ┌─────────────────┐                              │
│            │  Shared Context │◄──► Profile Memory           │
│            │    (Blackboard) │    hermes_cli.profiles       │
│            └─────────────────┘                              │
│                       │                                      │
│                       ▼                                      │
│            ┌─────────────────┐                              │
│            │  BatchRunner    │  ← batch_runner (parallel)   │
│            │  Orchestrator   │                              │
│            └─────────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Components (Hermes-Powered)

### 1. Shared Context (Blackboard) + Hermes Profiles
```python
from hermes_cli.profiles import get_profile_dir, list_profiles
import json
from pathlib import Path

class SharedContext:
    """Central knowledge store - backed by Hermes profile memory"""
    
    def __init__(self, network_name: str):
        self.profile_dir = get_profile_dir()
        self.network_dir = self.profile_dir / "networks" / network_name
        self.network_dir.mkdir(parents=True, exist_ok=True)
    
    def read(self, agent_id: str = None) -> dict:
        """Read from Hermes profile storage"""
        state_file = self.network_dir / "state.json"
        if state_file.exists():
            return json.loads(state_file.read_text())
        return {}
    
    def write(self, agent_id: str, data: dict):
        """Write to Hermes profile storage"""
        state = self.read()
        state[agent_id] = data
        (self.network_dir / "state.json").write_text(json.dumps(state))
```

### 2. Agent Protocol - Using Hermes Callbacks
```python
from run_agent import AIAgent

class HermesAgent:
    """Wrapper around AIAgent with protocol output"""
    
    def __init__(self, name: str, role: str, toolsets: list):
        self.name = name
        self.role = role
        
        # Use Hermes AIAgent
        self.agent = AIAgent(
            enabled_toolsets=toolsets,
            tool_progress_callback=self._on_tool,
            step_callback=self._on_step,
            tool_complete_callback=self._on_complete,
        )
    
    def _on_tool(self, tool_name: str, input_data: dict):
        # Log tool usage to shared context
        context.write(self.name, {"tool": tool_name, "input": input_data})
    
    def run(self, task: str) -> dict:
        """Run with standardized output"""
        response = self.agent.chat(task)
        
        # Convert to protocol format
        return {
            "type": "RESULT",
            "sender": self.name,
            "content": response,
            "confidence": 0.95,  # Could track via Hermes
            "needs": [],
            "knows": [],
        }
```

### 3. Coordinator - Using Hermes BatchRunner
```python
from batch_runner import BatchRunner
from run_agent import AIAgent

class HermesCoordinator:
    """Orchestrate multiple agents using Hermes"""
    
    def run_parallel(self, agents: list, task: str) -> list:
        """Run agents in parallel using BatchRunner"""
        # Create task file
        tasks = [{"agent": a.name, "task": task} for a in agents]
        
        runner = BatchRunner(
            dataset_file=self._write_tasks(tasks),
            num_workers=len(agents),
            model="claude-sonnet-4",
        )
        return runner.run()
    
    def run_sequential(self, agents: list, task: str) -> list:
        """Run agents one by one, passing results"""
        results = []
        current_task = task
        
        for agent in agents:
            result = agent.run(current_task)
            results.append(result)
            
            # Pass context to next agent
            current_task = f"Previous result: {result['content']}\n\nOriginal task: {task}"
        
        return results
```

### 4. Tool Validation - Using Hermes
```python
from hermes_cli.toolset_validation import validate_platform_toolsets

def validate_agent_tools(toolsets: list) -> bool:
    """Validate tools using Hermes built-in validation"""
    try:
        validate_platform_toolsets(toolsets)
        return True
    except ValueError:
        return False
```

---

## Agent Types (Hermes-Powered)

| Agent | Role | Hermes AIAgent toolsets | Purpose |
|-------|------|------------------------|---------|
| **Coordinator** | Orchestrate | `["web", "memory"]` | Manage workflow, delegate |
| **Researcher** | Gather info | `["web"]` | Search, analyze |
| **Coder** | Generate code | `["terminal", "file"]` | Build, fix |
| **Reviewer** | Quality check | `["terminal", "file"]` | Verify, critique |
| **Analyst** | Data processing | `["web", "file"]` | Extract, compute |
| **Reporter** | Summarize | `["file"]` | Compile, present |

---

## Workflow Modes (Hermes-Powered)

### 1. Sequential (AIAgent.chain)
```
A → B → C  (each passes to next)
```
```python
for agent in agents:
    result = agent.run(task)
    task = f"Context: {result}\n{task}"
```

### 2. Parallel (BatchRunner)
```
A ─┬─→ B  (all work on same task via BatchRunner)
   ├─→ C
   └─→ D
```
```python
runner = BatchRunner(tasks, num_workers=len(agents))
results = runner.run()
```

### 3. Debate (Multi-AIAgent)
```
A ──►│       (proposal)
     ├──► Consensus ──► Decision
B ──►│       (objection)
```
```python
proposals = [a.run(task) for a in agents]
consensus = coordinator.synthesize(proposals)
```

### 4. Pipeline (AIAgent + callbacks)
```
[Input] → A → B → C → [Output]
              ↑
              └──── D ─┘ (feedback loop)
```
```python
class Pipeline:
    def __init__(self, agents):
        self.agents = agents
    
    def run(self, input_data):
        result = input_data
        for agent in self.agents:
            result = agent.run(result)
        return result
```

---

## Implementation Structure

```
agent_flow/agents/
├── __init__.py
├── network.py          # AgentNetwork (Hermes-powered)
├── protocol.py         # Message format + vocabulary
├── coordinator.py      # HermesCoordinator (BatchRunner)
├── types/
│   ├── __init__.py
│   ├── base.py        # HermesAgent (wrapper around AIAgent)
│   ├── coordinator.py # Coordinator role
│   ├── researcher.py  # Researcher role
│   ├── coder.py       # Coder role
│   ├── reviewer.py    # Reviewer role
│   └── analyst.py     # Analyst role
└── examples/
    └── demo_network.py
```

---

## Usage Example (Hermes-Powered)

```python
from agent_flow.agents import AgentNetwork
from agent_flow.agents.types import Coordinator, Researcher, Coder

# Create network with Hermes-powered agents
network = AgentNetwork(name="dev-team")

# Add Hermes AIAgent wrappers
coordinator = network.add(Coordinator("manager", toolsets=["web", "memory"]))
researcher = network.add(Researcher("searcher", toolsets=["web"]))
coder = network.add(Coder("builder", toolsets=["terminal", "file"]))

# Run (Hermes handles execution)
result = await network.run(
    task="Build a web API with registration",
    mode="sequential"  # or "parallel", "debate", "pipeline"
)

# Result includes evidence from each Hermes agent
print(result)
```

---

## Auto-Understanding Features (Hermes-Powered)

1. **Hermes Callbacks** - Track what each agent does in real-time
2. **Shared Profile Memory** - All agents use same Hermes profile storage
3. **Tool Validation** - Uses Hermes built-in `validate_platform_toolsets`
4. **Standard Output** - All AIAgent outputs parsed uniformly
5. **Iteration Budget** - Track confidence per agent
6. **Provider Management** - Use Hermes `CANONICAL_PROVIDERS` for models

---

## Next Steps
1. Create `agent_flow/agents/` module
2. Implement `HermesAgent` wrapper around `run_agent.AIAgent`
3. Build `SharedContext` using Hermes profile storage
4. Create `HermesCoordinator` using `BatchRunner`
5. Add pre-built agent types (Coordinator, Researcher, Coder...)
6. Add orchestration modes (sequential, parallel, debate, pipeline)
7. Build demo API

7. Build demo API
