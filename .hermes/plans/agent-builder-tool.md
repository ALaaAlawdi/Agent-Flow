# Agent Builder Tool Plan

## Goal
Build specialized AI agents (workers) for Agent-Flow company using Hermes `batch_runner` and `run_agent` modules.

## Available Tools from Hermes Package

### 1. `batch_runner.BatchRunner`
- Run multiple agent tasks in parallel
- `Pool` size control
- Progress tracking
- Tool stats

### 2. `run_agent.AIAgent`
- Single agent execution
- `IterationBudget` control
- Context compression
- Tool guardrails

### 3. Hermes Tool Sets
- `web` - Read-only web browsing
- `terminal` - Command execution (restricted)
- `file` - File operations
- `computer-use` - Desktop automation

## Implementation Phases

### Phase 1: Basic Worker Factory
```
agent_flow/workers/
├── __init__.py
├── factory.py       # Create workers from spec
├── specs.py         # Worker definitions
└── base.py         # Base worker class
```

### Phase 2: Worker Types
- `Researcher` - Web search & synthesis
- `Coder` - Code generation & review
- `Reviewer` - Quality assurance
- `Analyst` - Data analysis

### Phase 3: Team Composition
- `Squad` - Group of workers
- `Manager` - Worker coordination
- `Pipeline` - Sequential workflow

## Example Worker Spec

```python
worker_spec = {
    "name": "researcher-001",
    "role": "Researcher",
    "toolsets": ["web"],
    "budget": {
        "max_iterations": 50,
        "max_tokens": 100000,
    },
    "instructions": "Search, analyze, and summarize..."
}
```

## Next Steps
1. Create `agent_flow/workers/` directory
2. Implement `WorkerFactory` class
3. Add worker types (Researcher, Coder, etc.)
4. Add team/squad management
5. Integrate with existing `HermesWorkerAdapter`
