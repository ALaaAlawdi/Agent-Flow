# Agent-Flow

**Agent-Flow is an operating system for a company staffed by AI agents.** Specialized agents work as founders, researchers, architects, builders, reviewers, governors, and organizational memory. The company forms dynamic squads, turns missions into dependency-gated ventures, requires evidence for every completion, enforces budgets, separates producers from reviewers, preserves an event ledger, and stops at a human launch gate.

The operating model is inspired by [Hermes Agent](https://github.com/NousResearch/hermes-agent): agents use bounded tools, delegate work, retain memory, learn reusable skills, and execute scheduled missions. Agent-Flow adds the institutional layer around those workers—roles, capital allocation, task authority, evidence contracts, independent review, and human governance. Agent-Flow is an independent project, not an official Hermes component or fork.

This repository deliberately separates two layers:

- **Company Control Plane — working in v0.1:** deterministic state, budgets, task dependencies, assignments, evidence, reputation, review gates, lessons, approvals, and an append-only event trail.
- **AI Employee Runtime — next layer:** replaceable LLM/agent adapters, beginning with a Hermes adapter, that consume constrained task packets and return artifact proposals. Employees never receive direct state-mutation authority.

## Why this is different

Most multi-agent demos are several prompts connected by arrows. Agent-Flow models a company as an institution:

```text
Mission → Dynamic Squad → Evidence Market → Prototype
        → Independent Falsification → Board → Human Gate
        → Organizational Lesson
```

Agents gain reputation from accepted work, not eloquence. A mission spends finite credits. Reviewers are structurally independent. The company remembers why it built, pivoted, killed, or recovered from an incident.

## Hermes-inspired company model

| Hermes pattern | Agent-Flow company interpretation |
|---|---|
| Agent loop + tools | An AI employee performs bounded work with an explicit job packet and allowed tools. |
| Delegation | A mission becomes a dependency graph staffed by a temporary squad. |
| Skills | Successful procedures become versioned company SOPs; incidents become regression skills. |
| Persistent memory | Agents retain role context while the company retains evidence, decisions, events, and lessons. |
| Profiles and toolsets | Each employee has an isolated role, capabilities, budget, and least-privilege authority. |
| Cron and durable work | The company runs recurring operations, resumes interrupted missions, and escalates failures. |
| Gateway surfaces | Humans supervise the same company through CLI, API, or messaging channels. |

The intended execution stack is **Hermes-like agents as employees, Agent-Flow as the company control plane, and humans as owners of consequential authority**. See the official [Hermes documentation](https://hermes-agent.nousresearch.com/docs/) for the system that inspired these worker patterns.

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
# Keep this gateway secret out of source, state, evidence, and logs.
export AGENT_FLOW_CAPABILITY_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
python3 -m agent_flow.cli --db company.db mission packets MISSION_ID

# A trusted gateway gives one packet/token to its assigned worker. The worker
# returns that token with its proposal; it does not choose or assert an actor ID.
python3 -m agent_flow.cli --db company.db mission complete MISSION_ID TASK_ID \
  --artifact "artifacts/result.json" \
  --verification "tests and independent review performed" \
  --summary "bounded conclusion supported by the artifact" \
  < /secure/path/task-capability-token

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

The CLI exposes bounded task packets and authenticated evidence submission for a trusted operator-controlled gateway. Worker capability tokens are HMAC-authenticated, scoped to one mission/task/assigned worker, and expire after five minutes. Completion reads the token from standard input so it is not exposed in process arguments. Keep the gateway secret and SQLite file inaccessible to workers; packets contain bearer credentials and must be delivered only to the assigned worker. v0.1 deliberately leaves worker process isolation and orchestration to the operator; distributed claiming, leases, heartbeats, revocation, and provider adapters are the next milestone.

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
- SQLite and `AGENT_FLOW_CAPABILITY_SECRET` must remain available only to the trusted gateway; v0.1 does not provide process sandboxing or concurrent distributed worker isolation.
- Evidence handles are recorded but their content is not yet hashed or independently fetched.
- No production deployments, payments, contracts, or customer-data access are automated.
- Market and financial conclusions remain hypotheses until backed by real customer evidence.

See [the vision](docs/VISION.md), [the architecture](docs/ARCHITECTURE.md), and [the constitution](AGENTS.md).
