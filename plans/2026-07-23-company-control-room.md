# Company Control Room Implementation Plan

## features / show case

Build a visible company-runtime surface inside Agent-Flow that turns the existing deterministic `CompanyRuntime` into a product feature:

- create a mission from the UI
- auto-form the squad for that mission
- see all workflow tasks in a kanban-style board
- inspect assigned agent, dependencies, evidence, and launch gate status
- review recent company ledger events
- expose this through `/missions` in the frontend and `/missions/*` in the FastAPI backend

This is the first Alook-inspired "real work board" for Agent-Flow, but grounded in the project's own constitution, missions, budgets, and evidence model.

## designs overview

### Backend
- Add a dedicated FastAPI router for the deterministic company runtime instead of bloating `agent_flow/agents/api/main.py` further.
- Reuse the existing `CompanyRuntime` in `agent_flow/runtime.py`; do not invent a second mission/task store.
- Provide endpoints for:
  - `GET /missions`
  - `POST /missions`
  - `GET /missions/{mission_id}`
  - `POST /missions/{mission_id}/form-squad`
  - `GET /missions/{mission_id}/packets`
  - `GET /company/events`
- Keep writes minimal and deterministic. No fake agent execution yet.

### Frontend
- Add a new `/missions` page that acts like a control room dashboard.
- Add a create-mission form in-page.
- Show mission cards with budget, risk, status, progress.
- Show selected mission task columns grouped by `blocked`, `ready`, `done`.
- Show recent event ledger entries.
- Add sidebar navigation to `/missions`.

### Testing
- Strict TDD for backend API behavior.
- Validate frontend with build/lint after implementation.
- Run full backend unittest suite before reporting complete.

## new deps

- None.

## TODOS

- [x] **Task 1 — add failing API tests for mission list/create/detail and squad formation**
  - Files:
    - create `tests/test_company_api.py`
    - read `agent_flow/runtime.py`
    - read `agent_flow/agents/api/main.py`
  - Cover:
    - bootstrap-backed mission listing starts empty
    - mission creation returns mission id and persisted mission detail
    - form-squad assigns agents to non-human tasks
    - packets endpoint returns ready mission packets after squad formation
    - company events endpoint returns append-only events

- [x] **Task 2 — implement company runtime FastAPI router**
  - Files:
    - create `agent_flow/agents/company_api.py`
    - modify `agent_flow/agents/api/main.py`
  - Add a small runtime factory using env-configurable DB path:
    - default `.agent-flow/company.db`
    - optional capability secret from `AGENT_FLOW_CAPABILITY_SECRET`
  - Keep route handlers thin and translate `KeyError`/`ValueError`/`RuntimeError`/`PermissionError` into proper HTTP responses.

- [x] **Task 3 — add failing frontend usage path by extending API client types**
  - Files:
    - modify `frontend/src/lib/api.ts`
  - Add typed helpers for:
    - list missions
    - create mission
    - get mission detail
    - form squad
    - get mission packets
    - get company events

- [x] **Task 4 — build the Missions control-room page**
  - Files:
    - create `frontend/src/app/missions/page.tsx`
    - modify `frontend/src/components/Sidebar.tsx`
    - read `frontend/AGENTS.md`
  - UI sections:
    - create mission form
    - mission list rail
    - selected mission summary
    - task board grouped by status
    - ready packets panel
    - recent ledger events
  - Use existing visual language from the current dark dashboard.

- [x] **Task 5 — update landing/dashboard copy only if needed for discoverability**
  - Files:
    - optionally modify `frontend/src/app/page.tsx`
  - Only add a small CTA card/link to `/missions` if the page feels hidden after sidebar nav.

- [x] **Task 6 — verification and cleanup**
  - Run targeted API tests first.
  - Run frontend lint/build.
  - Run full backend unittest suite.
  - Update this plan checkboxes when done.

### test cases
- [x] create a mission with valid title/brief/budget/risk
- [x] reject invalid mission payloads with 4xx
- [x] form a squad and confirm task assignments exist
- [x] packets endpoint only exposes ready non-human tasks
- [x] events endpoint includes mission creation and squad formation events
- [x] frontend renders mission list and selected mission summary from live API data
- [x] frontend create flow refreshes the selected mission after creation

## QA tests

- [x] **Create mission journey** — route `/missions`; fill title/brief/budget/risk; confirm new mission card appears; backend signal: new row in `missions`, `mission_created` event in `events`
- [x] **Form squad journey** — route `/missions`; click form squad on selected mission; confirm task cards show assigned agents; backend signal: `assigned_agent` values in `tasks`, `squad_formed` event in `events`
- [x] **Inspect ready work journey** — route `/missions`; verify ready packet count and task board columns; backend signal: `GET /missions/{id}/packets` returns only ready non-human tasks
- [x] **Ledger visibility journey** — route `/missions`; verify recent events panel updates after create/form squad; backend signal: ordered rows from `events`
