# Agent-Flow

**Agent-Flow is a persistent operating system for an AI-native venture civilization.** It forms dynamic squads, turns missions into dependency-gated ventures, requires evidence for every completion, enforces budgets, separates producers from reviewers, preserves an event ledger, and stops at a human launch gate.

This repository deliberately separates two layers:

- **Company Runtime — working in v0.1:** deterministic state, budgets, task dependencies, assignments, evidence, reputation, review gates, lessons, and approvals.
- **AI Workers — next layer:** replaceable LLM/agent adapters that consume constrained task packets and return artifact proposals. Workers will never receive direct state-mutation authority.

## Why this is different

Most multi-agent demos are several prompts connected by arrows. Agent-Flow models a company as an institution:

```text
Mission → Dynamic Squad → Evidence Market → Prototype
        → Independent Falsification → Board → Human Gate
        → Organizational Lesson
```

Agents gain reputation from accepted work, not eloquence. A mission spends finite credits. Reviewers are structurally independent. The company remembers why it built, pivoted, killed, or recovered from an incident.

## Requirements

- Python 3.11+
- No runtime dependencies for v0.1

## Run immediately

```bash
python3 -m agent_flow.cli --db /tmp/agent-flow-demo.db demo
```

The demo executes a complete venture workflow and intentionally stops at:

```json
{
  "mission_status": "active",
  "next_gate": "human_launch_approval",
  "next_gate_status": "ready",
  "human_approval_recorded": false
}
```

## CLI

```bash
# Bootstrap a persistent company
python3 -m agent_flow.cli --db company.db init

# Inspect the agent civilization
python3 -m agent_flow.cli --db company.db agents

# Create and staff a venture
python3 -m agent_flow.cli --db company.db mission create \
  --title "Arabic Agent Reliability" \
  --brief "Decide which Arabic enterprise agents may enter production" \
  --budget 120 \
  --risk high

# Inspect bounded work packets for external AI/Hermes workers
python3 -m agent_flow.cli --db company.db mission packets MISSION_ID

# Submit an artifact proposal; the runtime validates assignment, evidence, dependencies, and budget
python3 -m agent_flow.cli --db company.db mission complete MISSION_ID TASK_ID \
  --actor ASSIGNED_AGENT \
  --artifact "artifacts/result.json" \
  --verification "tests and independent review performed" \
  --summary "bounded conclusion supported by the artifact"

# Inspect a mission
python3 -m agent_flow.cli --db company.db mission status MISSION_ID

# Inspect the audit timeline and organizational memory
python3 -m agent_flow.cli --db company.db events
python3 -m agent_flow.cli --db company.db lessons

# Local operator approval after all gates are complete
python3 -m agent_flow.cli --db company.db mission approve MISSION_ID \
  --actor "Human Operator" \
  --rationale "Reviewed evidence, risk, rollback, and external consequences"
```

The CLI exposes bounded task packets and evidence submission for external workers. v0.1 deliberately leaves worker process orchestration to the operator; distributed claiming, leases, heartbeats, and provider adapters are the next milestone.

## Python API

```python
from agent_flow import CompanyRuntime

company = CompanyRuntime("company.db")
company.bootstrap()
mission_id = company.create_mission(
    "Reliability Gate",
    "Test Arabic AI agents before production.",
    budget=120,
    risk="high",
)
assignments = company.form_squad(mission_id)
print(company.mission(mission_id))
```

## Tests

```bash
python3 -W error::ResourceWarning -m unittest discover -s tests -v
python3 -m compileall -q agent_flow tests
```

## Safety and honest limitations

- The current demo uses deterministic simulated evidence; it does not call an LLM.
- `actor_type="human"` in the local API is an operator assertion, not cryptographic authentication.
- SQLite is intended for a single local operator in v0.1, not concurrent distributed workers.
- Evidence handles are recorded but their content is not yet hashed or independently fetched.
- No production deployments, payments, contracts, or customer-data access are automated.
- Market and financial conclusions remain hypotheses until backed by real customer evidence.

See [the vision](docs/VISION.md), [the architecture](docs/ARCHITECTURE.md), and [the constitution](AGENTS.md).
