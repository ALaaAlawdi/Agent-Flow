# Agent-Flow Enterprise v1 — Sales Readiness

## Positioning

Agent-Flow is an AI company operating system staffed by specialized agents.
It is built for companies that want AI workers with explicit roles, review loops,
audit trails, and human approval gates.

## Why this version is sellable

- **10 constitution agents live**: Founder, Researcher, Coder, Reviewer, Writer, Skeptic, Archivist, Anthropologist, Economist, Redteam.
- **Provider-neutral runtime**: can work with DeepSeek today and expand to more providers.
- **Human-gated consequences**: architecture separates proposals from approvals.
- **Traceability**: conversations, handoffs, and decisions are recorded.
- **Alook-ready**: org chart can be exported for Alook orchestration.

## Enterprise use cases

1. Internal AI task force for research + coding + review.
2. AI PMO / operating office for planning, synthesis, and execution tracking.
3. AI venture studio for testing ideas, pricing, and product prototypes.
4. AI redteam and governance workflow before launch decisions.

## Demo flow for first customer

1. Show `/brain-chat` for a multi-turn conversation.
2. Show `/brain/status` to prove 10 agents are active.
3. Trigger `/brain/handoff` to show agent-to-agent delegation.
4. Show `/alook/status` and `/alook/org` to demonstrate Alook readiness.
5. Show `/company` control-room APIs for deterministic runtime controls.

## Packaging suggestion

### Starter Pilot
- 10 agents
- 1 workspace
- local deployment
- weekly support
- fixed-scope onboarding

### Business
- multi-team setup
- custom roles
- process mapping
- managed upgrades

### Enterprise
- SSO / IAM integration
- audit exports
- on-prem deployment
- custom security review

## Current technical proof points

- Next.js frontend builds successfully.
- Python backend test suite passes.
- Brain supports session memory and handoffs.
- Alook CLI is detectable and can be bootstrapped locally.
- Alook export file can be generated from the current org chart.

## Honest limitations

- Alook orchestration is integrated as readiness/export/bootstrap for now, not deep bidirectional syncing.
- External publication / legal / financial actions still need explicit human approval.
- Some demo modules remain experimental and should be sold as pilot capabilities, not fully autonomous operations.
