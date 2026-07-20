# Agent Civilization MVP Implementation Plan

> **For Hermes:** Implement this plan task-by-task using strict TDD and independent review.

**Goal:** Turn Agent-Flow from an empty repository into an executable, persistent simulation of an AI-native venture company that forms dynamic squads, enforces evidence and approvals, tracks budgets/reputation, and learns from mission outcomes.

**Architecture:** A zero-dependency Python package with an SQLite event/state store, deterministic company runtime, reusable venture workflow, CLI, and optional future LLM adapter boundary. The deterministic runtime owns authorization, budgets, dependencies, gates, and evidence; models may propose work but cannot mutate state directly.

**Tech Stack:** Python 3.11+ standard library, `sqlite3`, `argparse`, `dataclasses`, `unittest`.

---

## Product thesis

Agent-Flow is not a chat interface or static org chart. It is an **AI venture civilization runtime**:

1. A mission enters the company.
2. A dynamic squad is formed from specialized agents.
3. Work follows a dependency graph from thesis to experiment, build, red-team, and board decision.
4. Every completion requires evidence and consumes budget.
5. Independent gates can reject or request rework.
6. Human approval is mandatory for launch, money, contracts, production, and sensitive data.
7. Outcomes update agent reputation and create reusable organizational lessons.

## MVP scope

### In scope

- Persistent SQLite company state and append-only event ledger.
- Agent registry with role, capabilities, reputation, and available status.
- Mission creation with budget and risk class.
- Dynamic squad formation based on task capabilities.
- Dependency-gated venture workflow.
- Evidence-required task completion and budget accounting.
- Independent review gates and human launch approval.
- Mission status, event timeline, and company dashboard.
- Deterministic demo scenario and automated tests.

### Out of scope

- Autonomous legal incorporation, banking, contracts, payments, or production deployment.
- Unsupervised access to customer data or external systems.
- A web UI, distributed workers, or concurrent task leasing.
- Provider-specific LLM integration in v0.1.
- Claims that deterministic orchestration alone constitutes autonomous AI.

## Workflow

```text
mission_thesis
├── market_intelligence
├── customer_pain
└── risk_hypothesis
       ↓
venture_design
├── experiment_design
└── architecture
       ↓
prototype
       ↓
independent_verification
├── red_team
└── economics_review
       ↓
board_review
       ↓
human_launch_approval
```

## Authority model

- Agents may propose, produce evidence, review, and score.
- The deterministic runtime validates state transitions and budgets.
- A producer cannot approve its own review gate.
- Human approval is required before any launch state.
- The event ledger is append-only from the application interface.

## Files

- Create `pyproject.toml` — package and CLI metadata.
- Create `agent_flow/__init__.py` — public API.
- Create `agent_flow/domain.py` — roles, workflow templates, validation.
- Create `agent_flow/store.py` — SQLite schema and persistence.
- Create `agent_flow/runtime.py` — company state machine and business rules.
- Create `agent_flow/cli.py` — executable commands.
- Create `tests/test_runtime.py` — end-to-end state, gate, budget, and audit tests.
- Create `tests/test_cli.py` — CLI smoke test.
- Create `AGENTS.md` — constitution, roles, and authority boundaries.
- Create `docs/VISION.md` — company/product thesis and scaling path.
- Replace `README.md` — setup, demo, commands, limitations.
- Create `.gitignore`.

## TDD tasks

### Task 1: Bootstrap company and agent registry

1. Write failing test creating a temporary database and asserting default agents exist.
2. Run the focused test; verify import/schema failure.
3. Implement minimal store schema and `CompanyRuntime.bootstrap()`.
4. Run focused and full tests.

### Task 2: Create mission and dependency graph

1. Write failing test for mission creation, budget, task graph, and only root tasks being ready.
2. Implement workflow template and persistence.
3. Verify events include `company_bootstrapped` and `mission_created`.

### Task 3: Dynamic squad formation

1. Write failing test that assigns each task to an eligible agent by capability.
2. Ensure independent review tasks are not assigned to the producer of their prerequisite.
3. Implement deterministic selection using availability and reputation.

### Task 4: Evidence and budget enforcement

1. Write failing tests for empty evidence rejection, dependency rejection, and budget overrun rejection.
2. Implement task start/completion and budget accounting.
3. Verify successful completion promotes downstream tasks.

### Task 5: Review and human approval gates

1. Write failing test that launch remains blocked until verification, red-team, economics, and board tasks pass.
2. Write failing test that an agent cannot grant human approval.
3. Implement approval API requiring actor type `human` and recorded rationale.

### Task 6: Reputation and organizational learning

1. Write failing test that accepted work increases reputation and rejected work decreases it within bounds.
2. Write failing test that mission closure records a reusable lesson.
3. Implement score update and lesson persistence.

### Task 7: CLI and demonstration

1. Write CLI smoke test for `init`, `mission create`, `status`, and `events`.
2. Implement argparse commands and JSON/text output.
3. Add `demo` command that exercises a complete non-launch mission safely.

### Task 8: Documentation and release verification

1. Document exact capabilities and limits.
2. Run `python -m compileall agent_flow tests`.
3. Run `python -m unittest discover -s tests -v`.
4. Run a disposable database scenario and inspect state transitions/events.
5. Run static secret/dangerous-pattern scans.
6. Request independent diff review and fix blocking issues.

## Verification criteria

- New database bootstraps without external dependencies.
- Root tasks are ready; dependent tasks are blocked.
- No task completes without non-empty evidence.
- Spending cannot exceed the mission budget.
- Review is independent from production.
- Launch cannot occur without an explicit human approval event.
- Every material state transition produces an event.
- Tests run against temporary databases and leave no repository state behind.
- README distinguishes the working deterministic runtime from future LLM workers.

## Scaling path

1. Add OpenAI-compatible and Hermes worker adapters behind a task-packet interface.
2. Add signed artifacts, content-addressed evidence, and replayable execution traces.
3. Add task leasing and heartbeat recovery for distributed workers.
4. Add a venture portfolio, internal prediction market, and capital allocation.
5. Add simulation worlds, customer agents, adversarial agents, and counterfactual boards.
6. Add a web control room only after the runtime invariants are stable.
