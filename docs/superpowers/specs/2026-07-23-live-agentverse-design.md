# Live AgentVerse — Design Spec

**Date:** 2026-07-23
**Status:** Draft — awaiting user review
**Author:** brainstorming session with ALaaAlawdi

## Goal

Turn the current click-to-tick AgentVerse page into a **presentation-quality live viewer** for agent interactions:

- Watch agents talk to each other in real time, paced so a human audience can follow.
- Rich visualization (animated network graph) alongside the transcript, so viewers see *how* agents interact, not just what they say.
- Persist every session so a demo can be **replayed on demand** — the safety net for live pitches when the LLM misbehaves.

## Design choices (from brainstorming)

| Question | Choice |
|----------|--------|
| Interaction model | **A** — Autonomous. User hits ▶ Start, backend ticks on its own, ⏸ Stop when done. |
| Pacing | **A** — Backend sleeps `pace_seconds` (default 3s, configurable 1–10s) between ticks. No frontend typewriter. |
| Visualization | **C+D** — Split screen: animated network graph left, live chat top-right, agent stats bottom-right. |
| Persistence | **C** — Every session recorded to SQLite. Dedicated `/sessions` page + replay view with 1x/2x/5x speed. |
| Live delivery | **SSE** (Server-Sent Events) — one-way stream, simpler than WebSocket, proxies cleanly through Next.js `/api`. |

## Non-goals

- No multi-session isolation beyond in-memory session IDs (single-tenant demo tool).
- No pause/resume of a session's backend runner (stop is terminal). Replay covers pause/scrub.
- No mid-session snapshot restore (server crash = session marked `crashed`, replay still works up to crash point).
- No frontend unit tests (project has none today; we add backend tests only).
- Old `/hermes-agents` page (manual tick UI) is left untouched for backward compatibility.

## Architecture overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI backend (:8000)                  │
│                                                             │
│  ┌──────────────────┐   ┌──────────────────┐               │
│  │  SessionRunner   │──▶│    EventBus      │               │
│  │  (asyncio task,  │   │  (in-process     │               │
│  │  ticks every N s)│   │   pub/sub)       │               │
│  └──────────────────┘   └────────┬─────────┘               │
│           │                      │                          │
│           ▼                      ▼                          │
│  ┌──────────────────┐   ┌──────────────────┐               │
│  │   SQLite (WAL)   │   │  SSE endpoint    │               │
│  │  sessions/events │   │  /agentverse/    │               │
│  │  /snapshots      │   │  stream          │               │
│  └──────────────────┘   └──────────────────┘               │
└──────────────────────────────┬──────────────────────────────┘
                               │ SSE (text/event-stream)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                Next.js frontend (:3001)                     │
│                                                             │
│  /agentverse/live        ── EventSource ── graph+chat+stats │
│  /agentverse/sessions    ── list of past runs               │
│  /agentverse/sessions/[id] ── replay from DB                │
└─────────────────────────────────────────────────────────────┘
```

**Runtime flow:**
1. `POST /api/agentverse/sessions` → creates session row, spawns `SessionRunner` asyncio task, returns `{session_id}`.
2. Runner loops: pick agents → tick (existing AgentVerse logic) → build event → publish to EventBus → append to SQLite → `await asyncio.sleep(pace)`.
3. Frontend `EventSource('/api/agentverse/stream?session_id=X')` receives each event and updates graph/chat/stats.
4. `POST /api/agentverse/sessions/{id}/stop` → runner exits cleanly, session row marked `stopped`.
5. `/agentverse/sessions` lists past sessions. Replay reads events from SQLite and dispatches them on a client-side timer (with speed control).

**Isolation guarantees:**
- `SessionRunner` doesn't import SSE code.
- `EventBus` doesn't import SQLite code.
- Frontend components (`AgentGraph`, `LiveChat`, `AgentStatsPanel`) take props only — no API knowledge.
- Each layer is testable in isolation.

## Backend components

### `agent_flow/agents/world/session_runner.py` (new, ~120 LOC)

```python
class SessionRunner:
    def __init__(self, session_id, pace_seconds, event_bus, session_store, agent_verse):
        ...
    async def run(self): ...        # main loop
    def stop(self): ...             # sets self._stop_flag = True
```

Loop body:
1. Check `_stop_flag`, break if set.
2. Increment tick counter, emit `tick_start` event.
3. Call the existing world tick: `await asyncio.to_thread(world.tick)`. **This is critical** — `world.tick()` is synchronous and makes blocking LLM HTTP calls; calling it directly would freeze the event loop and stall SSE for every subscriber.
4. Diff `world.conversations` against pre-tick snapshot; convert each new entry into a `message` event, publish + persist.
5. Every 5 ticks: build `snapshot` event with per-agent deltas (skills/memory/tasks counter deltas vs the previous snapshot), publish + persist.
6. `await asyncio.sleep(pace_seconds)`.

Error handling: three consecutive `tick_once()` exceptions → emit `error` event with `recoverable=False`, mark session `crashed`, exit.

### `agent_flow/agents/world/event_bus.py` (new, ~60 LOC)

```python
class EventBus:
    def subscribe(self, session_id: str) -> asyncio.Queue: ...
    def publish(self, session_id: str, event: dict) -> None: ...
    def unsubscribe(self, session_id: str, queue: asyncio.Queue) -> None: ...
```

Internal: `dict[str, list[asyncio.Queue]]`. Each queue `maxsize=100`, drop-oldest on overflow (via `queue.get_nowait()` before `put_nowait()` when full). Multiple subscribers per session supported. No threading — asyncio only.

### `agent_flow/agents/world/session_store.py` (new, ~150 LOC)

Plain `sqlite3` (no ORM). Connection opened with `check_same_thread=False`, `journal_mode=WAL`, `synchronous=NORMAL`.

Methods:
- `create_session(session_id, pace_seconds, agent_roster) -> None`
- `end_session(session_id, status) -> None`  # status: stopped | crashed
- `append_event(session_id, kind, payload) -> int`  # returns new seq
- `list_sessions(limit=100) -> list[SessionRow]`
- `read_events(session_id, since_seq=0) -> Iterator[EventRow]`
- `mark_running_as_crashed_on_startup() -> None`  # startup cleanup

### `agent_flow/agents/world/hermes_api.py` (modified, +8 endpoints)

New routes (all under `/agentverse`):

| Method | Path | Purpose |
|--------|------|---------|
| POST   | `/sessions` | Create + start. Body: `{pace_seconds?}`. Returns `{session_id}`. |
| POST   | `/sessions/{id}/stop` | Cleanly stop runner. |
| POST   | `/sessions/{id}/pace` | Change `pace_seconds` mid-run. Body: `{pace_seconds}`. |
| GET    | `/sessions` | List sessions, most recent first. |
| GET    | `/sessions/{id}` | Session metadata + agent roster + counts. |
| GET    | `/sessions/{id}/events?since_seq=N` | Read historical events for replay. |
| GET    | `/stream?session_id=X` | **SSE endpoint** — live event stream. |

SSE implementation: `StreamingResponse(media_type="text/event-stream")` over an async generator that pulls from an `EventBus.subscribe(session_id)` queue, formats each event as `event: <kind>\ndata: <json>\n\n`, cleans up on client disconnect.

Existing `/agentverse/tick` endpoint stays for backward compat.

### `production.py` (modified, +~10 LOC)

FastAPI lifespan handler:
- On startup: instantiate singleton `EventBus` and `SessionStore`, attach to `app.state`. Call `session_store.mark_running_as_crashed_on_startup()`.
- On shutdown: call `.stop()` on any running `SessionRunner`, close store connection.

## Frontend components

Location: `frontend/src/`.

### `components/agentverse/AgentGraph.tsx` (new, ~180 LOC)

Pure SVG network graph.

**Props:**
```ts
{
  agents: Array<{ name: string; job_title: string; color: string }>;
  activePulse: { from: string; to: string; id: string } | null;
  edgeWeights: Map<string, number>;  // key = "a→b", value = interaction count
}
```

**Layout:** N agents placed on a ring around center. For agent `i` of `n`:
`x = cx + R·cos(2πi/n − π/2)`, `y = cy + R·sin(2πi/n − π/2)`.

**Rendering:**
- Base layer: all-pairs edges as `<line>` with `stroke-width = 1 + log(weight+1)`, `stroke-opacity = 0.15 + 0.5·(weight/maxWeight)`.
- Nodes: `<circle>` per agent + `<text>` label. Node radius 32px.
- Pulse: when `activePulse.id` changes, mount a `<circle r=6>` at the `from` node, animate `cx/cy` toward `to` node via CSS `@keyframes` (500ms linear), unmount at end. The `from` and `to` node get a temporary `filter: drop-shadow(...)` glow via a keyed class.

No external graph library. Recharts already in deps but overkill here.

### `components/agentverse/LiveChat.tsx` (new, ~80 LOC)

**Props:** `{ messages: ChatMessage[]; agentColors: Record<string, string> }`.

Renders same visual style as the current `/hermes-agents` chat log. New messages get `animate-slide-in` CSS class for 300ms after mount (opacity 0→1, translateY 8px→0).

Sticky scroll: track `atBottom` ref via `onScroll`. If `atBottom`, auto-scroll to newest message on prop change. If user scrolled up, don't yank the view.

### `components/agentverse/AgentStatsPanel.tsx` (new, ~100 LOC)

**Props:** `{ agents: Record<string, HermesAgent>; recentDeltas: Record<string, {skills?: number; memory?: number}> }`.

Compact grid of agent cards (reuse styling from current page). When a counter changes (via `recentDeltas`), that specific counter gets a `animate-flash` class (yellow background pulse 400ms). `recentDeltas` cleared by parent after the flash duration.

### `lib/useAgentverseStream.ts` (new, ~60 LOC)

```ts
function useAgentverseStream(sessionId: string | null): {
  events: SessionEvent[];
  agents: Record<string, HermesAgent>;
  edgeWeights: Map<string, number>;
  activePulse: { from: string; to: string; id: string } | null;
  recentDeltas: Record<string, { skills?: number; memory?: number; tasks?: number }>;
  status: 'idle' | 'connecting' | 'live' | 'closed';
};
```

- Opens `EventSource` when `sessionId` transitions from null to a string.
- Registers `addEventListener` for each event kind: `message`, `snapshot`, `tick_start`, `error`.
- On `message`: append to `events`, increment `edgeWeights[from→to]`, set `activePulse` with a fresh id (auto-cleared 500ms later via `setTimeout`).
- On `snapshot`: merge deltas into `agents`, publish deltas into `recentDeltas`, then auto-clear `recentDeltas` 400ms later so `AgentStatsPanel`'s flash animation gets a clean signal.
- Cleans up on unmount / sessionId change.
- Browser handles reconnection automatically.

### `lib/useReplay.ts` (new, ~80 LOC)

```ts
function useReplay(sessionId: string, speed: 1 | 2 | 5): {
  events: SessionEvent[];
  agents: Record<string, HermesAgent>;
  edgeWeights: Map<string, number>;
  activePulse: { from: string; to: string; id: string } | null;
  playing: boolean;
  play(): void; pause(): void; restart(): void;
};
```

- On mount: fetch `/api/agentverse/sessions/{id}/events` (all at once), fetch `/api/agentverse/sessions/{id}` for roster.
- Dispatches events via a `setTimeout` chain: gap between event `i` and `i+1` = `(t[i+1] − t[i]) / speed`, minimum 50ms.
- Same reducer logic as live hook — components reused unchanged.

### Pages

**`app/agentverse/live/page.tsx` (new, ~120 LOC)**

Split layout (CSS grid):
```
+------------------+---------------------+
|                  |    LiveChat         |
|   AgentGraph     +---------------------+
|                  |    AgentStatsPanel  |
+------------------+---------------------+
```
Header bar: ▶ Start / ⏸ Stop, pace slider (1–10s), session id chip, connection status badge.

**`app/agentverse/sessions/page.tsx` (new, ~60 LOC)**

Table: started_at | duration | status | message_count | "Open replay →" link.

**`app/agentverse/sessions/[id]/page.tsx` (new, ~150 LOC)**

Same three panels as live page. Header replaced with replay controls: ▶/⏸/⏮ + speed buttons (1x/2x/5x) + progress bar showing event N of total.

### Navigation

`components/Sidebar.tsx` adds one entry: "Live" → `/agentverse/live` (icon: `Radio` from lucide-react). "Sessions" grouped underneath.

## Data model

### SQLite schema (extends `agent_flow.db`)

```sql
CREATE TABLE IF NOT EXISTS sessions (
  id            TEXT PRIMARY KEY,
  started_at    TEXT NOT NULL,
  ended_at      TEXT,
  pace_seconds  REAL NOT NULL,
  status        TEXT NOT NULL,          -- running | stopped | crashed
  agent_roster  TEXT NOT NULL,          -- JSON
  tick_count    INTEGER NOT NULL DEFAULT 0,
  message_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS session_events (
  session_id   TEXT NOT NULL,
  seq          INTEGER NOT NULL,
  timestamp    TEXT NOT NULL,
  kind         TEXT NOT NULL,           -- message | tick_start | snapshot | error
  payload      TEXT NOT NULL,           -- JSON
  PRIMARY KEY (session_id, seq),
  FOREIGN KEY (session_id) REFERENCES sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_events_session_seq
  ON session_events(session_id, seq);
```

Snapshots live inside the event stream as `kind='snapshot'` rows — no separate table. Replay just reads all events in order.

Sessions table survives migrations by using `CREATE TABLE IF NOT EXISTS`. No formal migration framework — schema evolution handled by additive-only ALTERs when needed.

### Event payload shapes

```jsonc
// kind = "tick_start"
{ "tick": 12 }

// kind = "message"
{ "from": "Zain", "to": "Noor", "text": "asks: what's your best skill?", "tick": 12 }

// kind = "snapshot"      (written every 5 ticks)
{ "tick": 12, "agent_deltas": { "Noor": { "skills": 1, "memory": 2 } } }

// kind = "error"
{ "message": "LLM timeout", "recoverable": true }
```

### SSE wire format

```
event: message
data: {"seq":42,"session_id":"...","from":"Zain","to":"Noor","text":"...","tick":12}

event: snapshot
data: {"seq":43,"tick":12,"agent_deltas":{...}}

```

Each frame ends with a blank line (SSE spec requirement). `seq` on every payload for potential future resume-from-seq support.

### Storage estimate

~200 bytes/event × ~200 events per demo run = ~40KB/session. 1000 sessions ≈ 40MB. Well within SQLite's comfort zone.

## Error handling & edge cases

| Scenario | Handling |
|----------|----------|
| LLM call fails once | Emit `error` event (recoverable=true), continue after extra `pace_seconds`. |
| 3 consecutive LLM failures | Emit final `error` event (recoverable=false), mark session `crashed`, runner exits. |
| Client disconnects mid-stream | EventBus removes their queue when `StreamingResponse` generator finalizes. Runner unaffected. |
| Slow client | Bounded queue drops oldest events for that subscriber only. Other subscribers keep pace. |
| Server SIGINT/crash | On next startup, `mark_running_as_crashed_on_startup()` flips orphaned sessions to `crashed`. Events already persisted remain replayable. |
| Replay after crash | Works up to the last persisted event. UI shows "session crashed at tick N" banner. |
| Two `/live` tabs open, same session | Both get all events (EventBus supports multiple subscribers per session). |
| Reset button on old `/hermes-agents` page | Clears in-memory AgentVerse state only. Does not affect recorded sessions in DB. |

## Testing

Extends existing `tests/` (currently 29/29 passing).

- **`tests/test_session_runner.py`** — stubbed `AgentVerse` + injected fake clock; assert (a) events emitted in order, (b) `pace_seconds` respected between ticks, (c) `stop()` interrupts loop cleanly, (d) 3 consecutive tick failures → status=crashed.
- **`tests/test_event_bus.py`** — subscribe/publish round-trip; multiple subscribers per session all receive; unsubscribe cleanup; bounded queue drops oldest.
- **`tests/test_session_store.py`** — create/append/read round-trip; WAL concurrent read while another connection writes; `mark_running_as_crashed_on_startup` behavior. Uses a temp DB per test, cleaned up on tear-down.
- **`tests/test_hermes_api_sessions.py`** — POST create → SSE stream yields at least N events → POST stop → GET session shows `status=stopped`.

No frontend unit tests (project has none). Manual acceptance criteria below serve as smoke test.

## Acceptance criteria

1. Click ▶ Start on `/agentverse/live` → within 5s, first message appears in the chat panel AND first pulse animates on the graph.
2. Subsequent messages arrive at approximately `pace_seconds` intervals. Graph pulse always aligns with the chat message for the same tick (visual sync ≤ 200ms).
3. Click ⏸ Stop → no further events arrive. Session appears at the top of `/agentverse/sessions` with correct duration and message count.
4. Open a past session from `/agentverse/sessions` → replay reproduces the run in the same order; 2x/5x speed buttons scale gaps proportionally.
5. `Ctrl+C` the server mid-session → restart → the interrupted session appears in the list with `status=crashed`, and replay works up to the last event that was persisted before the crash.
6. All existing 29 tests still pass; new tests bring total to 33+ passing.

## Rollout

- Old `/hermes-agents` page unchanged. New `/agentverse/live` and `/agentverse/sessions` added.
- No database migration required — new tables created with `IF NOT EXISTS` on first run.
- No new Python dependencies. SSE implementable with FastAPI's built-in `StreamingResponse`.
- No new frontend dependencies. Uses existing SVG, Tailwind, and native `EventSource`.

## Open questions

None at time of writing. All decisions confirmed during brainstorming.
