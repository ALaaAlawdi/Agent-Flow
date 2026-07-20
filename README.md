# Agent-Flow

**Agent-Flow is an operating system for a company staffed by AI agents.** Specialized agents work as founders, researchers, architects, builders, reviewers, governors, and organizational memory. The company forms dynamic squads, turns missions into dependency-gated ventures, requires evidence for every completion, enforces budgets, separates producers from reviewers, preserves an event ledger, and stops at a human launch gate.

The employee runtime uses the official [Hermes Agent](https://github.com/NousResearch/hermes-agent) package: agents use bounded tools, role-isolated profiles, memory, skills, and delegation while Agent-Flow adds the institutional layer—roles, capital allocation, task authority, evidence contracts, independent review, and human governance. Agent-Flow remains an independent project, not an official Hermes component or fork.

This repository deliberately separates two layers:

- **Company Control Plane:** deterministic state, budgets, task dependencies, assignments, capabilities, evidence, reputation, review gates, lessons, approvals, and an append-only event trail.
- **Hermes AI Employee Runtime — working in v0.2:** the official `NousResearch/hermes-agent` source from GitHub `main` consumes sanitized task packets through its `--oneshot` CLI entry point and returns evidence proposals. Agent-Flow retains state-mutation authority.

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

- Python 3.11–3.13 (matching the official Hermes source requirements)
- [`uv`](https://docs.astral.sh/uv/) recommended
- A configured Hermes provider/model

## Install

```bash
uv sync
uv run hermes setup
```

`pyproject.toml` consumes `hermes-agent` directly from the official NousResearch GitHub `main` branch. `uv.lock` records the resolved upstream commit, so installs remain reproducible until the lock is intentionally refreshed.

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

# Create an isolated Hermes employee profile once.
uv run hermes profile create agent-flow-founder \
  --description "Bounded founder worker for Agent-Flow missions"

# Run one currently-ready task with the official Hermes source. v0.2 permits
# only Hermes' read-only web toolset; terminal/file access requires future OS isolation.
mkdir -p /tmp/agent-flow-workspaces/MISSION_ID/TASK_ID
uv run agent-flow --db company.db mission run-hermes MISSION_ID TASK_ID \
  --profile agent-flow-founder \
  --toolsets web \
  --workdir /tmp/agent-flow-workspaces/MISSION_ID/TASK_ID

# Inspect bounded work packets for other external AI workers.
# Keep the gateway secret out of source, state, evidence, and logs.
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

The `run-hermes` command is a trusted in-process gateway. It requests a capability-free packet projection, invokes the official Hermes CLI, validates an exact Evidence Proposal schema, and asks the deterministic Runtime to complete the task using the already assigned worker identity. No HMAC bearer or signing secret is needed on this path. The general `packets`/`complete` protocol remains available for separately operated gateways and still requires short-lived bearer capabilities.

**Important:** Hermes `--oneshot` mode automatically bypasses interactive tool approvals. v0.2 therefore permits only Hermes' official `web` toolset and rejects terminal, file, browser, image-generation, plugin, MCP, wildcard, and unknown toolsets. Output streams are bounded and the dedicated process group is killed on completion, timeout, or overflow. This is still not a complete OS sandbox; broader employee powers require a disposable container/VM with explicit filesystem, network, and credential policy.

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

- The deterministic `demo` still uses simulated evidence; real Hermes execution is available only through `mission run-hermes`.
- Hermes output is untrusted: the adapter validates JSON shape and Runtime authority, but it does not independently prove the artifact contents.
- `--oneshot` bypasses interactive Hermes approvals; bounded toolsets/profile/workdir reduce scope but do not provide OS-level process or network isolation.
- `actor_type="human"` in the local API is an operator assertion, not cryptographic authentication.
- SQLite and `AGENT_FLOW_CAPABILITY_SECRET` must remain available only to the trusted gateway; distributed claiming, leases, and worker revocation are not implemented.
- Evidence handles are recorded but their content is not yet hashed or independently fetched.
- No production deployments, payments, contracts, or customer-data access are automated.
- Market and financial conclusions remain hypotheses until backed by real customer evidence.

See [the vision](docs/VISION.md), [the architecture](docs/ARCHITECTURE.md), and [the constitution](AGENTS.md).
