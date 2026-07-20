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

The planned adapter maps Hermes-style primitives into company controls:

| Employee primitive | Company control |
|---|---|
| Profile/session | Isolated role identity and resumable assignment context |
| Toolset | Role and task allowlist; credentials stay in the trusted gateway |
| Delegation | Child tasks linked to the mission dependency graph |
| Memory | Role-local working knowledge; never authoritative company truth |
| Skill | Versioned SOP proposal requiring verification before promotion |
| Cron/durable execution | Scheduled mission trigger, lease renewal, retry, and escalation |
| Gateway | Human supervision surfaces, not a bypass around approval policy |

The current repository does **not** yet launch Hermes processes. v0.1 provides the deterministic control plane and authenticated submission protocol needed before adding that adapter.

## Current modules

- `agent_flow/domain.py` — immutable workflow and risk vocabulary.
- `agent_flow/runtime.py` — SQLite schema, company state machine, evidence rules, reputation, approvals, events, and lessons.
- `agent_flow/cli.py` — local operator interface and safe deterministic demo.
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

Treat worker output, evidence text, retrieved documents, URLs, and prompt content as untrusted. Important future controls:

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

## Worker protocol direction

A task packet contains only the minimum necessary context plus a bearer capability that the trusted gateway delivers to its assigned worker:

```json
{
  "mission_id": "...",
  "task_id": "...",
  "objective": "...",
  "allowed_tools": [],
  "budget": {"credits": 5, "time_seconds": 300},
  "input_artifacts": [],
  "acceptance_criteria": [],
  "evidence_contract": ["artifact", "verification", "summary"],
  "capability_token": "short-lived HMAC token"
}
```

A worker returns an artifact proposal with the packet's token. It never chooses an actor identity or receives direct Runtime/SQLite access. The current CLI is a trusted gateway adapter, not a sandbox: operators must isolate the database and signing secret from worker processes. Tokens currently expire after five minutes but have no pre-expiry revocation list; completed task state prevents successful replay after completion.
