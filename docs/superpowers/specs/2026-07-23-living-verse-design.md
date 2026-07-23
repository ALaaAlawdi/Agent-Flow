# Living Verse — Design Spec

**Date:** 2026-07-23
**Status:** Draft — approved by ALaaAlawdi during brainstorming
**Author:** brainstorming session with Claude Code (Opus 4.7)

## Goal

Turn the current click-to-tick `/world` page into a **living, autonomous agent environment**
where the user can see, in real time:

- **How agents interact** with each other (who talks to whom).
- **How messages flow** (asks, answers, greetings).
- **How agents share info** (knowledge, memories about each other).
- **How they learn** (skill acquisition, confidence growth, question counters).

The existing 2D canvas map is preserved on the left; a new right-hand panel exposes the
interaction and learning dynamics that are currently invisible.

## Design choices

| Question | Choice |
|----------|--------|
| Layout | **C** — Split screen: 2D canvas map (left) + interaction stream + learning cards + world pulse (right). |
| Runtime | Autonomous. ▶ Start / ⏸ Pause header controls. Backend loops on its own, sleeping `pace_seconds` between ticks. |
| Transport | Reuse existing WebSocket `/world/agentverse/ws`. No SSE. |
| Language of interactions | Templated for v1 (uses existing `HermesBrain` questions + `AgentBrain.answer_question` templates). Real-LLM mode is deferred. |
| Persistence | None in this round. Session recording/replay is a separate, already-drafted feature (`2026-07-23-live-agentverse-design.md`). |
| Backwards compat | Existing "▶️ Run World (60 ticks)" button remains. Autonomous mode is additive. |

## Non-goals

- No LLM-powered conversations in v1 (templates only — real LLM already exists on `/hermes-agents`; can be wired later behind a toggle).
- No session recording, replay, or SQLite persistence of events (out of scope; separate spec covers it).
- No new frontend routes (only `/world` is modified). No sidebar changes.
- No changes to `agent_flow.db` schema.
- No new Python or npm dependencies.
- No frontend unit tests (project has none).

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI backend (:8000)                   │
│                                                              │
│  ┌─────────────────────┐    ┌─────────────────────────┐     │
│  │   AutonomousTicker  │───▶│   WorldWebSocketManager │     │
│  │   (asyncio task,    │    │   (broadcasts events    │     │
│  │   ticks every N s)  │    │    to all subscribers)  │     │
│  └──────────┬──────────┘    └──────────┬──────────────┘     │
│             │                          │                     │
│             ▼                          ▼                     │
│  ┌─────────────────────┐    ┌─────────────────────────┐     │
│  │  WorldEngine.tick() │    │  /world/{name}/ws       │     │
│  │  returns InteractionDelta──▶ broadcasts new events │     │
│  └─────────────────────┘    └─────────────────────────┘     │
└──────────────────────────────┬───────────────────────────────┘
                               │ WebSocket JSON messages
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                Next.js frontend (:3000)                      │
│                                                              │
│  /world  (updated split layout)                              │
│  ├─ left:  <canvas> (existing 2D map)                       │
│  └─ right: <InteractionStream>                              │
│            <AgentLearningCards>                             │
│            <WorldPulse>                                     │
└──────────────────────────────────────────────────────────────┘
```

**Runtime flow (autonomous mode):**
1. Frontend sends WS command `{action: "start", pace_seconds: 3}`.
2. Backend spawns one `AutonomousTicker` asyncio task per world (only one runs at a time; second `start` is a no-op).
3. Ticker loops: `await world.tick()` → collect `InteractionDelta` → broadcast typed events → `await asyncio.sleep(pace_seconds)`.
4. Frontend receives typed events (`agent_asked`, `agent_answered`, `agent_learned`, `agent_moved`, `agent_greeted`, `world_pulse`) and updates the appropriate panel.
5. Frontend sends `{action: "pause"}` → ticker's stop flag is set → loop exits after its next iteration.
6. Frontend sends `{action: "set_pace", pace_seconds: 5}` → ticker's pace is updated in place.

**Isolation guarantees:**
- `AutonomousTicker` doesn't import `ws.py`'s broadcaster — it takes it as an injected dependency.
- `WorldEngine.tick()` returns a plain dataclass (`InteractionDelta`) — no WebSocket coupling.
- Frontend components take props only — no `useWebSocket` inside `InteractionStream` or `AgentLearningCards`. The page hooks own the socket and pass data down.

## Backend components

### `agent_flow/agents/world/engine.py` (modified)

The current `WorldEngine.tick()` mutates state and returns nothing. Change it to also
return an `InteractionDelta` describing what happened this tick, so the ticker can build
typed WS events without re-reading state.

```python
@dataclass
class InteractionDelta:
    tick: int
    greetings: list[dict]      # [{from, from_name, to, to_name, message}]
    asks: list[dict]           # [{from, from_name, to, to_name, question}]
    answers: list[dict]        # [{from, from_name, to, to_name, question, answer}]
    learnings: list[dict]      # [{agent, agent_name, kind, detail}] where kind in {skill, memory, knowledge}
    moves: list[dict]          # [{agent, agent_name, from_pos, to_pos}]
```

`WorldEngine.tick()` behavior change:
- When two agents are within `hear_range` of each other, the currently-generated "Hello X! I'm Y. Nice to meet you!" greeting stays as `greetings`.
- New: after greeting, with probability `personality.curiosity`, agent asks a question drawn from a curiosity-weighted template list (see `AgentBrain.ask_question()` in `agent_verse.py`). Emitted as `asks`.
- New: the target agent answers via templated logic (`AgentBrain.answer_question()`) — emitted as `answers`.
- New: after any successful ask/answer/greet, the involved agent's `HermesBrain` records a `Memory` and/or promotes a skill (`asking`, `answering`, `greeting`). Each such change appended to `learnings`.
- `moves`: any agent whose `position` changed from pre-tick snapshot.

**Critical constraint:** `WorldEngine.tick()` remains an `async` method. Interaction is
pure Python (no LLM, no I/O), so the tick body itself does not need `await`. Templated
Q&A takes microseconds.

The existing `run(ticks, interval)` method (used by the old "Run 60 ticks" button)
should continue to work unchanged — internally it calls the new `tick()` and discards
the delta.

### `agent_flow/agents/world/ticker.py` (new, ~90 LOC)

```python
class AutonomousTicker:
    def __init__(self, world_name: str, world: WorldEngine,
                 ws_manager: WorldWebSocketManager,
                 pace_seconds: float = 3.0):
        self._world_name = world_name
        self._world = world
        self._ws = ws_manager
        self._pace = pace_seconds
        self._stop = asyncio.Event()
        self._task: asyncio.Task | None = None

    def is_running(self) -> bool: ...
    async def start(self) -> None: ...     # spawns _run(); idempotent
    async def stop(self) -> None: ...      # sets _stop; awaits _task
    def set_pace(self, pace_seconds: float) -> None: ...  # 1.0 <= pace <= 10.0

    async def _run(self) -> None:
        while not self._stop.is_set():
            delta = await self._world.tick()
            await self._broadcast_delta(delta)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self._pace)
            except asyncio.TimeoutError:
                pass

    async def _broadcast_delta(self, delta: InteractionDelta) -> None:
        # Delegates to shared broadcast_delta() helper in ws.py.
        await broadcast_delta(self._world_name, self._world, delta)
```

Registered in a module-level `tickers: dict[str, AutonomousTicker]` so the WS handler
can look up "the ticker for this world_name".

Pace clamped 1.0 ≤ pace ≤ 10.0. Values outside are silently clipped.

### `agent_flow/agents/world/ws.py` (modified, +~30 LOC)

Two changes:

1. Add module-level `tickers: dict[str, AutonomousTicker]` so the WS handler can look up per-world tickers.
2. Update `run_world_ticks()` (used by the old "Burst 60" path) so it also captures the `InteractionDelta` returned by each `world.tick()` and broadcasts the same typed events (`agent_greeted`, `agent_asked`, `agent_answered`, `agent_learned`, `world_pulse`) that the autonomous ticker emits. This is what makes acceptance criterion #6 work — Burst 60 ticks appear in the InteractionStream too.

To avoid duplication, extract the broadcast-delta logic into a shared helper:

```python
async def broadcast_delta(world_name: str, world: WorldEngine, delta: InteractionDelta) -> None:
    # Sends agent_greeted, agent_asked, agent_answered, agent_learned frames,
    # then a rollup world_pulse frame with world.get_state().
```

Both `AutonomousTicker._broadcast_delta` and `run_world_ticks` call this helper.

### `agent_flow/agents/world/api.py` (modified, +~50 LOC to the WS handler)

Extend the command switch inside `world_websocket()` with three new actions:

| Action | Payload | Effect |
|--------|---------|--------|
| `start` | `{pace_seconds?}` | Get-or-create ticker for `world_name`; call `.start()`. Broadcast `{"type": "world_ticker", "status": "running", "pace_seconds": p}`. |
| `pause` | `{}` | If ticker exists and running, call `.stop()`. Broadcast `{"type": "world_ticker", "status": "paused"}`. |
| `set_pace` | `{pace_seconds}` | Call `.set_pace(p)`. Broadcast `{"type": "world_ticker", "status": running|paused, "pace_seconds": p}`. |

Existing `speak`, `move`, `tick` commands unchanged.

Also: on WS connect, immediately send the current ticker status alongside `world_state`
so newly-connected clients know if the world is already running.

### `production.py` (modified, +~5 LOC)

Add FastAPI shutdown handler that iterates `tickers` and calls `.stop()` on each so
the server shuts down cleanly.

## Frontend components

Location: `frontend/src/`.

**Reminder:** `frontend/AGENTS.md` says this Next.js has breaking changes from public
docs. Before touching any Next.js primitive (routing, `use client`, streaming APIs),
consult `node_modules/next/dist/docs/` first. Nothing in this design requires new
Next.js features — all changes are pure React + Tailwind on an existing client-side
page. But when we go to implement, we should verify.

### `components/world/InteractionStream.tsx` (new, ~90 LOC)

**Props:**
```ts
{
  events: InteractionEvent[];   // last ~100, oldest first
  agentColors: Record<string, string>;   // agent_id -> hex
}

type InteractionEvent =
  | { kind: 'greeted';  id: string; from: string; from_name: string; to_name: string; text: string; tick: number }
  | { kind: 'asked';    id: string; from: string; from_name: string; to_name: string; text: string; tick: number }
  | { kind: 'answered'; id: string; from: string; from_name: string; to_name: string; text: string; tick: number }
  | { kind: 'learned';  id: string; agent: string; agent_name: string; detail: string; kind_of: 'skill'|'memory'|'knowledge'; tick: number };
```

Rendered as a vertical scrollable list. Each row: colored dot for the actor, emoji for
the kind (👋 greeted, 🙋 asked, 💬 answered, ✨ learned), a compact one-line description.
New rows arrive with `animate-slide-in` (opacity 0→1, translateY 8px→0) over 300ms.

Sticky scroll: track `atBottom` ref via `onScroll`. Auto-scroll to newest only when
`atBottom` is true; otherwise leave the user's scroll position alone.

Empty state: "Waiting for the world to come alive..." with a subtle pulse animation.

### `components/world/AgentLearningCards.tsx` (new, ~120 LOC)

**Props:**
```ts
{
  agents: Agent[];   // from WorldState.agents
  brains: Record<string, BrainSnapshot>;   // agent_id -> brain
  recentDeltas: Record<string, { skills?: number; memory?: number; knowledge?: number }>;
}

type BrainSnapshot = {
  role: string;
  personality: { curiosity: number; talkativity: number; friendliness: number };
  skills: Array<{ name: string; confidence: number; times_used: number }>;
  memory_count: number;
  knowledge_recent: string[];   // last 3
  questions_asked: number;
  questions_answered: number;
};
```

Grid of small cards (2 cols on wide viewports, 1 on narrow):
- Header: colored dot + agent name + role (auto-discovered).
- Personality: three thin horizontal bars (curiosity, talkativity, friendliness).
- Skills (top 3): name + confidence bar + `×N` uses.
- Counters row: 🙋 asked / 💬 answered / 🧠 memories / ✨ knowledge.
- Knowledge: last 3 items, muted text.

**Flash animation:** any counter that appears in `recentDeltas` for its agent gets a
yellow background pulse for 400ms via a keyed `animate-flash` class. The parent hook
clears `recentDeltas` after 400ms so the animation only fires once per delta.

### `components/world/WorldPulse.tsx` (new, ~40 LOC)

**Props:**
```ts
{
  tick: number;
  status: 'idle' | 'running' | 'paused';
  paceSeconds: number;
  uptimeSeconds: number;
  agentCount: number;
  totalInteractions: number;
  totalLearnings: number;
}
```

Small horizontal strip above the interaction stream:
`● running · tick 42 · pace 3s · 3 agents · ↔ 128 interactions · ✨ 41 learnings`

Green dot when running, amber when idle, gray when paused. Numbers use `tabular-nums`
so they don't jump width.

### `frontend/src/app/world/page.tsx` (modified)

Change 1 — **layout split** using CSS grid instead of the current flex row:

```
+------------------+---------------------------+
|                  |  WorldPulse (strip)       |
|                  +---------------------------+
|   <canvas>       |  InteractionStream        |
|   (existing)     |  (scrollable, flex-1)     |
|                  +---------------------------+
|                  |  AgentLearningCards        |
+------------------+---------------------------+
```

The canvas keeps its current 660×660 size. The right column takes the remaining
viewport width.

Change 2 — **header controls**:

- Replace "▶️ Run World (60 ticks)" with a group: `▶ Start Living` (autonomous),
  `⏸ Pause`, and a pace slider (1s—10s labeled). Old "⏭️ Tick" (single manual tick)
  stays for debugging.
- The "Run World (60 ticks)" button is repurposed as "▶ Burst 60" — kept for
  backward compatibility and short demos.

Change 3 — **new state + WebSocket handlers**:

- Add `interactionEvents`, `brains`, `recentDeltas`, `tickerStatus`, `paceSeconds` to
  the component state.
- On WS `agent_greeted` / `agent_asked` / `agent_answered` / `agent_learned`, append
  a stable-id event to `interactionEvents` (cap 100). For `agent_learned`, also bump
  the appropriate counter in `recentDeltas[agent_id]` and schedule a 400ms clear.
- On WS `world_pulse`, merge `state.agents` and refresh `brains` from the state
  payload (which will now include `brain` snapshots).
- On WS `world_ticker`, update `tickerStatus` and `paceSeconds`.

Change 4 — **command wiring**:

- ▶ Start Living → `sendCommand("start", { pace_seconds: paceSeconds })`.
- ⏸ Pause → `sendCommand("pause")`.
- Slider onChange → `sendCommand("set_pace", { pace_seconds: value })`.

## WebSocket protocol

### Server → client message types

Existing (unchanged): `world_state`, `world_tick`, `agent_spoke`, `agent_spawned`,
`agent_removed`, `agent_moved`.

New:

```jsonc
// A greeting exchange between two agents
{ "type": "agent_greeted",
  "id": "int_00042_a1_a2",
  "from": "agent-1", "from_name": "Zain",
  "to":   "agent-2", "to_name":   "Noor",
  "text": "Hello Noor! I'm Zain. Nice to meet you!",
  "tick": 42 }

// A question asked
{ "type": "agent_asked",
  "id": "int_00043_a1_a2",
  "from": "agent-1", "from_name": "Zain",
  "to":   "agent-2", "to_name":   "Noor",
  "text": "What skills do you have?",
  "tick": 43 }

// An answer given
{ "type": "agent_answered",
  "id": "int_00044_a2_a1",
  "from": "agent-2", "from_name": "Noor",
  "to":   "agent-1", "to_name":   "Zain",
  "text": "I know exploring, coding, analysis.",
  "tick": 44 }

// A learning event
{ "type": "agent_learned",
  "id": "lrn_00045_a1",
  "agent": "agent-1", "agent_name": "Zain",
  "kind_of": "skill",         // or "memory" or "knowledge"
  "detail": "asking (0.35)",  // human-readable
  "tick": 45 }

// End-of-tick rollup
{ "type": "world_pulse",
  "tick": 45,
  "state": { /* WorldEngine.get_state() enriched with brains + counters */ } }

// Ticker status change (start / pause / set_pace)
{ "type": "world_ticker",
  "status": "running",
  "pace_seconds": 3.0 }
```

### Client → server commands

Existing (unchanged): `speak`, `move`, `tick`.

New:

```jsonc
{ "action": "start", "pace_seconds": 3.0 }   // pace optional; server clamps to [1, 10]
{ "action": "pause" }
{ "action": "set_pace", "pace_seconds": 5.0 }
```

## Data model extensions

`WorldEngine.get_state()` currently returns `agents`, `locations`, `active_messages`,
`recent_events`, and `stats`. Extend each agent entry with a `brain` sub-object so
`AgentLearningCards` has everything it needs from a single `world_pulse`:

```jsonc
{
  "agent_id": "agent-1",
  "name": "Zain",
  "position": { "x": 80.0, "y": 82.4 },
  "state": "talking",
  "energy": 87.3,
  "skills": ["exploring", "writing"],
  "messages_sent": 12,
  "messages_received": 9,
  "discovered": 2,
  "brain": {
    "role": "Junior Explorer",
    "personality": { "curiosity": 0.87, "talkativity": 0.73, "friendliness": 0.65 },
    "skills": [
      { "name": "asking", "confidence": 0.55, "times_used": 6 },
      { "name": "exploring", "confidence": 0.42, "times_used": 5 }
    ],
    "memory_count": 4,
    "knowledge_recent": ["Met Noor (agent)", "Learned skill: asking", "Met Sara (agent)"],
    "questions_asked": 6,
    "questions_answered": 3
  }
}
```

`stats` gets two new fields: `total_interactions` (sum across agents) and
`total_learnings` (counter maintained by `WorldEngine`).

## Error handling & edge cases

| Scenario | Handling |
|----------|----------|
| Client connects mid-run | On WS connect, server sends `world_state` + a fresh `world_ticker` frame with current status/pace. |
| Two `/world` tabs open | Both get all events (existing `ws_manager` supports multiple subscribers per world). |
| `start` called while already running | No-op. Server re-broadcasts current ticker status. |
| `pause` called while already paused | No-op. |
| `set_pace` with value outside [1,10] | Clamped, broadcast reflects clamped value. |
| Ticker exception (unexpected bug in `tick()`) | Log with agent state, wait 2×pace, retry. Three consecutive exceptions → send `{"type":"world_ticker", "status":"crashed", "error": str}` and exit. Front-end shows red badge. |
| Server SIGINT | Shutdown handler stops all tickers cleanly before Uvicorn exits. |
| Old "Burst 60 ticks" button while autonomous is running | The burst path calls `run_world_ticks()` which shares the same world lock; ticker's `world.tick()` and burst's `world.tick()` interleave safely because `WorldEngine.tick` already takes `self._lock`. Result: mixed ticks. This is fine for a debug button. |

## Testing

New tests added to existing `tests/` (currently 29/29 passing).

- **`tests/test_ticker.py`** — construct a stub `WorldEngine` (returns canned `InteractionDelta`s) and a stub `WorldWebSocketManager` (records broadcasts). Assert (a) `start()` runs at least N ticks over 3×pace seconds using a small pace like 0.1s, (b) `stop()` interrupts within one pace period, (c) `set_pace` mid-run halves the tick rate, (d) three consecutive exceptions → status broadcast is "crashed".
- **`tests/test_engine_delta.py`** — pre-position two agents 10 units apart, call `await world.tick()`, assert the returned `InteractionDelta` contains at least one `greetings` entry and (over 5 ticks) at least one `asks` + `answers` + `learnings` entry. Assert `HermesBrain` memory count increased for both agents.
- **`tests/test_ws_commands.py`** — extend existing WS tests (if any; otherwise minimal FastAPI TestClient websocket setup) to cover `start`, `pause`, `set_pace`. Assert the correct `world_ticker` frame is broadcast.

No frontend tests (project has none). Manual acceptance criteria below serve as smoke.

## Acceptance criteria

1. Click ▶ Start Living on `/world` → within 5 seconds, the right-side pulse shows
   `● running · tick N · pace 3s`, at least one greeting/ask/answer appears in the
   InteractionStream, and at least one AgentLearningCard shows a yellow counter flash.
2. Move the pace slider from 3s → 1s → new events arrive noticeably faster. Slider
   from 3s → 10s → they slow down. `world_ticker` broadcasts confirm the pace change.
3. Click ⏸ Pause → no new events in the stream for at least 15 seconds. Canvas
   remains rendered with the last positions. `world_pulse` dot turns gray.
4. Kill the backend (`Ctrl+C`) mid-run → server exits cleanly (no zombie asyncio
   warnings). Restart → `/world` reconnects, no old ticker task lingers.
5. All existing 29 tests still pass. New tests bring total to 32+ passing.
6. Existing "▶️ Burst 60" (old "Run World (60 ticks)") button still works and its
   ticks are visible in the InteractionStream too.

## Rollout

- Single feature branch. All backend + frontend changes ship together.
- No database migration. No new dependencies. No new frontend routes.
- Old `/world` behavior (manual ticks, WebSocket, canvas map) is preserved. All
  new functionality is additive.
- After merge, `README.md`'s Pages table gets a short update ("🌍 AgentVerse — now
  autonomous, watch agents interact & learn").

## Open questions

None. All key decisions confirmed during brainstorming.

## Future work (explicitly deferred)

- **Real-LLM conversations toggle** — swap templated `ask()`/`answer_question()` for
  calls to OpenAI gpt-4o-mini (using the existing `.env` key) via an async wrapper.
  Would require: an "LLM Mode" toggle in the header, per-tick rate limiting, error
  handling for API failures, and probably a longer default pace (5-8s) to stay under
  cost.
- **Session recording/replay** — the drafted `2026-07-23-live-agentverse-design.md`
  spec covers this. It's independent of Living Verse; both can coexist by having the
  replay layer subscribe to the same WS event stream.
- **Companies interaction** — the existing `company_integration.py` sync fires every
  5 ticks. Its outputs are already visible in the current right-panel "Companies"
  block; not extended here.
