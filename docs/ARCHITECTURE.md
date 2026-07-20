# Architecture

## Core boundary

```text
Untrusted model output
        ↓
Typed task proposal / artifact manifest
        ↓
Deterministic validation
        ↓
Budget + dependency + authority checks
        ↓
State transition + append-only event
        ↓
Independent verification
```

Models never write the database directly. Provider adapters are replaceable and must return data; the runtime alone decides whether a transition is legal. External worker submissions use short-lived HMAC capability tokens issued in bounded task packets rather than caller-supplied actor identities. Human approval remains a separate operator assertion path and never accepts worker capabilities.

## Hermes-inspired company architecture

Agent-Flow treats an agent runtime such as [Hermes Agent](https://github.com/NousResearch/hermes-agent) as an **AI employee runtime**, not as the company database or policy authority.

```text
Human channels / control room
             ↓
Agent-Flow company control plane
  mission graph · roles · budgets · policy · event ledger
             ↓ task packet + scoped capability
AI employee adapter (Hermes first; provider-neutral contract)
  profile · session · tools · memory · skills · delegation
             ↓ artifact proposal + evidence receipt
Deterministic validation → independent review → state transition
```

The Hermes adapter maps employee-runtime primitives into company controls:

| Employee primitive | Company control |
|---|---|
| Profile/session | Isolated role identity and resumable assignment context |
| Toolset | Role and task allowlist; credentials stay in the trusted gateway |
| Delegation | Child tasks linked to the mission dependency graph |
| Memory | Role-local working knowledge; never authoritative company truth |
| Skill | Versioned SOP proposal requiring verification before promotion |
| Cron/durable execution | Scheduled mission trigger, lease renewal, retry, and escalation |
| Gateway | Human supervision surfaces, not a bypass around approval policy |

v0.2 invokes the official `NousResearch/hermes-agent` GitHub `main` source through its `hermes --oneshot` CLI entry point; Agent-Flow does not copy or reimplement Hermes. `uv.lock` records the resolved upstream commit. `agent_flow/hermes.py` is limited to task projection, process invocation, and Evidence Proposal validation, while `agent_flow/cli.py` performs the deterministic Runtime submission.

## Current modules

- `agent_flow/domain.py` — immutable workflow and risk vocabulary.
- `agent_flow/runtime.py` — SQLite schema, company state machine, evidence rules, reputation, approvals, events, and lessons.
- `agent_flow/hermes.py` — Hermes package subprocess boundary, packet sanitization, and evidence validation.
- `agent_flow/cli.py` — local operator interface, Hermes task execution, and safe deterministic demo.
- `tests/` — end-to-end invariants against disposable databases.

## Persistent model

### Agents

Stable identity, title, capabilities, availability, and bounded reputation.

### Missions

Title, brief, risk class, lifecycle status, total credits, and spent credits.

### Tasks

Ordered dependency graph with capability, fixed credit cost, assignment, status, evidence, independence flag, and human-only flag.

### Events

Append-only application ledger recording material transitions. v0.1 prevents update/delete through the public API; database-level immutability and cryptographic chaining are future work.

### Lessons

Board-gated build/pivot/kill/incident conclusions that become organizational memory.

## State invariants

1. Root tasks begin `ready`; dependent tasks begin `blocked`.
2. A blocked task becomes ready only when all dependencies are done.
3. A task can complete only when ready and by its assigned agent.
4. Evidence requires artifact, verification, and summary.
5. Task cost cannot make mission spending exceed its budget.
6. Human-only tasks cannot use the agent completion path.
7. Launch approval requires all upstream gates and a local human assertion.
8. A lesson requires completed board review.
9. Every successful material mutation appends an event in the same transaction.

## Threat model

Treat worker output, evidence text, retrieved documents, URLs, and prompt content as untrusted. Hermes `--oneshot` auto-bypasses interactive tool approval, so the adapter rejects wildcard toolsets and requires an explicit profile and existing workspace; operators must still provide OS/container isolation. Important remaining controls:

- durable worker identity and short-lived task leases (v0.1 capability tokens authenticate a task packet, not a person or process);
- content-addressed artifacts and sandboxed verification;
- prompt-injection and data-classification gateways;
- capability tokens scoped to one task and tool;
- idempotency keys and side-effect receipts;
- chained or externally anchored event hashes;
- enterprise IAM-bound human approvals;
- separation between proposer, executor, and verifier.

## Concurrency

v0.1 is intentionally a local single-operator kernel. SQLite transactions provide local atomicity, but no lease/heartbeat protocol exists. Distributed workers require explicit claiming, expiry, retries, idempotency, and stale-worker recovery before concurrency is enabled.

## Worker protocol

The Runtime can emit a general external-worker packet containing minimum task context plus a short-lived bearer capability. The trusted `run-hermes` gateway does **not** pass that bearer to Hermes. It projects only the task scope and declares the actual enabled Hermes toolsets:

```json
{
  "mission_id": "...",
  "task_id": "...",
  "worker_id": "founder",
  "objective": "...",
  "mission_context": {"title": "...", "brief": "...", "risk": "medium"},
  "budget": {"credits": 8},
  "input_artifacts": [],
  "acceptance_criteria": ["..."],
  "evidence_contract": ["artifact", "verification", "summary"],
  "decision_options": [],
  "authority": {
    "may_mutate_company_state": false,
    "may_approve_own_work": false,
    "may_trigger_external_side_effects": false
  },
  "enabled_toolsets": ["web"]
}
```

Hermes returns only an artifact proposal. The adapter accepts exactly non-empty `artifact`, `verification`, and `summary` strings plus an optional valid `decision`. The trusted CLI then submits that proposal with its retained capability. Hermes never chooses an actor identity and never receives Runtime/SQLite access or signing authority.

The more general `mission packets` / `mission complete` path still exposes a bearer capability to a separately operated gateway. Those tokens expire after five minutes and have no pre-expiry revocation list; completed task state prevents successful replay after completion. Operators must isolate the database and signing secret from every worker process.
