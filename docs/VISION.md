# Vision: The AI Company That Invents Companies

## Thesis

The future AI company is not a chatbot with a list of personas. It is an executable institution staffed by AI agents: employees reason with tools, delegate bounded work, remember experience, learn reusable procedures, and operate continuously; a deterministic control plane allocates authority and capital; adversarial peers falsify claims; and humans retain control over real-world consequences.

Agent-Flow aims to become a **company operating system for AI employees** capable of running many temporary micro-companies. Each mission forms its own squad, budget, evidence graph, risk model, and memory. Successful patterns become reusable skills; failures become regression scenarios.

## Design lineage: inspired by Hermes, governed like a company

[Hermes Agent](https://github.com/NousResearch/hermes-agent) demonstrates a practical agent operating model: a persistent agent loop, tool use, delegation, skills learned from experience, cross-session memory, scheduled work, isolated profiles, and multiple human-facing gateways. Agent-Flow adopts those patterns as the foundation for an AI employee, then adds a company-wide institutional layer.

```text
Human owners / board
        ↓ consequential approvals
Agent-Flow company control plane
  roles · budgets · missions · evidence · policy · audit
        ↓ bounded task packets and capability tokens
Hermes-inspired AI employees
  tools · skills · memory · delegation · scheduled execution
        ↓ artifact proposals and verification receipts
Independent reviewers → deterministic state transitions
```

The separation is intentional:

- **Hermes-inspired employee runtime:** reasons, calls tools, delegates subtasks, resumes sessions, and improves reusable skills.
- **Agent-Flow company runtime:** decides who may do what, how much may be spent, which evidence is required, when independent review is mandatory, and which actions require a human.
- **Human governance:** controls production, money, legal commitments, sensitive data, destructive actions, and increases in delegated authority.

Agent-Flow is an independent project, not an official Hermes extension or fork. The current v0.1 implements the deterministic company kernel and a secure worker submission boundary; a real Hermes worker adapter, durable scheduling, employee memory isolation, and skill lifecycle integration remain roadmap work.

## The fantasy made concrete

Imagine opening a control room and stating:

> Discover a Saudi enterprise AI product that can become infrastructure, not a wrapper.

The civilization then:

1. Spawns competing venture theses rather than converging on the first plausible idea.
2. Buys evidence with a finite research budget.
3. Forms temporary squads from agents with measured reputations.
4. Builds the cheapest experiment capable of killing each thesis.
5. Sends survivors into architecture and prototype worlds.
6. Lets a skeptic, red team, and economist attack independently.
7. Runs a counterfactual board: build, pivot, or kill.
8. Stops before external consequences and asks a human.
9. Converts the trajectory into reusable organizational memory.

## Product direction

The first company built by this civilization should be an **Arabic AI Production Gate** for Riyadh enterprises:

```text
Arabic regression tests
→ RAG and citation evaluation
→ tool-call trajectory evaluation
→ policy and permission checks
→ failure simulation
→ incident replay
→ deployment decision
```

This wedge can expand into an Enterprise Agent Simulation Cloud. The moat is not the model: it is the accumulating library of Arabic failure scenarios, production trajectories, policy packs, system simulators, and recovery evidence.

## AI employee operating model

Every AI employee should eventually have:

1. **Role profile:** purpose, capabilities, model/provider policy, risk ceiling, and escalation rules.
2. **Tool contract:** an explicit allowlist with task-scoped credentials rather than ambient authority.
3. **Working session:** resumable context for the current assignment, isolated from other employees.
4. **Role memory:** durable facts relevant to the employee's function, separate from company truth.
5. **Skill portfolio:** versioned procedures promoted only after verification and replay.
6. **Task inbox:** durable, dependency-aware assignments with leases, deadlines, retries, and heartbeats.
7. **Evidence outbox:** artifacts, hashes, test receipts, citations, costs, and bounded conclusions.
8. **Learning loop:** accepted work updates reputation and proposes skills; failures produce regression cases.

No employee can promote its own output to company truth. The control plane validates capabilities, budget, dependencies, evidence, and reviewer independence before committing a transition.

## Future mechanics

### Internal prediction market

Agents stake finite reputation credits on falsifiable claims. Calibration matters more than confidence. Incorrect certainty costs more than an honest abstention.

### Dynamic micro-companies

There is no permanent backend team or marketing department. Squads form around capabilities required by the mission, dissolve after the outcome, and leave behind artifacts and lessons.

### Evolution laboratory

Repeated bottlenecks propose new roles, tools, or workflow mutations. Mutations run in shadow mode against historical missions before joining the constitution.

### Simulation worlds

Customer, CRM, ERP, IAM, finance, and attacker simulators expose ventures to timeouts, duplicate side effects, conflicting records, permission changes, prompt injection, and stale memory.

### Counterfactual board

Before committing capital, separate agents argue build, pivot, and kill using the same evidence set. The runtime records which assumptions drive the disagreement.

### Organizational genome

The company's durable advantage becomes a versioned genome of:

- trusted skills;
- failure scenarios;
- policy rules;
- integration adapters;
- evaluation suites;
- incident trajectories;
- calibrated agent reputations.

## Milestones

1. **v0.1 — Institutional kernel:** persistent missions, squads, budgets, evidence, gates, events, lessons, and task-scoped worker capabilities.
2. **v0.2 — Hermes workforce bridge:** provider-neutral worker protocol, Hermes adapter, isolated employee profiles, bounded toolsets, and artifact proposals.
3. **v0.3 — Verifiable evidence:** content hashes, fetchers, test receipts, signed reviewer decisions, and conditional-remediation loops.
4. **v0.4 — Durable company operations:** transactional inbox/outbox, leases, heartbeats, retries, idempotency, recovery, and scheduled missions.
5. **v0.5 — Organizational learning:** role memory, skill promotion, regression replay, provenance, and skill rollback.
6. **v0.6 — Venture portfolio:** competing theses, capital allocation, kill/pivot economics, and calibrated prediction markets.
7. **v0.7 — Simulation worlds:** enterprise systems, Arabic failure scenarios, adversarial environments, and incident rehearsal.
8. **v1.0 — Company control room:** distributed AI employees, enterprise IAM approvals, observability, replay, policy packs, and portfolio UI.

## North-star metrics

- Cost per accepted successful mission.
- Percentage of assumptions falsified before build.
- Human intervention rate by risk class.
- Unsafe or unauthorized action rate.
- Duplicate side-effect rate.
- Successful resume and recovery rate.
- Incidents converted into regression tests.
- Forecast calibration by agent and claim type.

The goal is not maximum autonomy. The goal is **maximum economically useful autonomy per unit of verified trust**.
