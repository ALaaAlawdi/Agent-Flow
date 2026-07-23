# Living Verse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `/world` into a living autonomous agent environment where users can see, in real time, how agents talk, ask, share info, and learn.

**Architecture:** Backend adds an `AutonomousTicker` asyncio task that repeatedly calls `WorldEngine.tick()` and broadcasts typed WS events; `WorldEngine.tick()` is refactored to return an `InteractionDelta` describing greetings/asks/answers/learnings/moves per tick. Frontend `/world` page adds three new right-column panels (interaction stream, agent learning cards, world pulse strip) and header controls (▶ Start / ⏸ Pause + pace slider). Existing 2D canvas map and manual-tick commands stay intact.

**Tech Stack:** FastAPI + asyncio + Uvicorn (backend), Next.js + React + Tailwind (frontend), WebSocket (transport), `unittest` (tests, run via `uv run python -m unittest discover -s tests -v`).

## Global Constraints

- No new Python or npm dependencies.
- No new frontend routes; only `/world` is modified.
- No `agent_flow.db` schema changes.
- All backend changes must keep existing 29 tests passing (`uv run python -m unittest discover -s tests -v` → 29/29 OK becomes 33+/33+ OK after this plan).
- Reuse the existing WebSocket endpoint `/world/agentverse/ws` — no SSE, no new transports.
- Templated interactions only in v1. Real-LLM mode is out of scope (deferred future work).
- `frontend/AGENTS.md` warns that this Next.js has breaking changes from public docs. Nothing in this plan requires new Next.js features (pure React + Tailwind + client-side WebSocket), but if you hit an API surprise, consult `node_modules/next/dist/docs/` before improvising.
- Pace clamped to [1.0, 10.0] seconds server-side.
- All new code and comments follow the terse style of the existing Agent-Flow modules — Arabic docstrings where the codebase uses them, English where it doesn't. Match neighboring code.

## File Structure

**Backend — 6 files affected:**

| Path | Change | Responsibility |
|------|--------|----------------|
| `agent_flow/agents/world/engine.py` | Modify | Add `InteractionDelta` dataclass; `WorldEngine.tick()` returns it; new templated ask/answer inside tick; enrich `WorldAgent.as_dict()` with brain snapshot; enrich `WorldEngine.get_state()` stats. |
| `agent_flow/agents/world/ticker.py` | Create | `AutonomousTicker` class: start/stop/set_pace/crash-detection loop. |
| `agent_flow/agents/world/ws.py` | Modify | Add module-level `tickers` dict; add `broadcast_delta()` helper; update `run_world_ticks()` to broadcast typed events. |
| `agent_flow/agents/world/api.py` | Modify | WS handler adds `start` / `pause` / `set_pace` commands; on connect, sends current ticker status. |
| `production.py` | Modify | Shutdown handler stops all live tickers. |
| `tests/test_living_verse.py` | Create | Unit tests for `InteractionDelta`, `AutonomousTicker`, WS commands. |

**Frontend — 4 files affected:**

| Path | Change | Responsibility |
|------|--------|----------------|
| `frontend/src/components/world/WorldPulse.tsx` | Create | Small horizontal strip: status dot, tick, pace, counters. |
| `frontend/src/components/world/InteractionStream.tsx` | Create | Scrollable feed of greeted / asked / answered / learned events with slide-in animation. |
| `frontend/src/components/world/AgentLearningCards.tsx` | Create | Grid of per-agent cards with skills, personality bars, counters, knowledge; flash on delta. |
| `frontend/src/app/world/page.tsx` | Modify | Split layout, header controls, new state, new WS message handling. |

---

### Task 1: `InteractionDelta` dataclass + `WorldEngine.tick()` returns it

**Files:**
- Modify: `agent_flow/agents/world/engine.py`
- Create: `tests/test_living_verse.py`

**Interfaces:**
- Consumes: existing `WorldEngine`, `WorldAgent`, `HermesBrain`.
- Produces:
  - `InteractionDelta` dataclass with fields `tick: int`, `greetings: list[dict]`, `asks: list[dict]`, `answers: list[dict]`, `learnings: list[dict]`, `moves: list[dict]` (all default `[]`).
  - `WorldEngine.tick()` signature changes from `-> None` to `-> InteractionDelta`.
  - Each dict shape defined in the spec's "WebSocket protocol → Server → client message types" section.

- [ ] **Step 1: Create the test file with failing tests**

Create `tests/test_living_verse.py`:

```python
"""Tests for the Living Verse — autonomous /world with interaction & learning viz."""

import asyncio
import unittest
from unittest.mock import AsyncMock

from agent_flow.agents.world.engine import (
    AgentState, InteractionDelta, Position, WorldAgent, WorldEngine,
)


def _place_two_agents_close(world: WorldEngine) -> tuple[WorldAgent, WorldAgent]:
    """Place two agents at distance 10 (well within the 20 unit talk radius)."""
    a1 = WorldAgent("agent-a", "Alpha", Position(100, 100), skills=["exploring"])
    a2 = WorldAgent("agent-b", "Beta",  Position(110, 100), skills=["writing"])
    world.spawn_agent(a1)
    world.spawn_agent(a2)
    return a1, a2


class InteractionDeltaTests(unittest.TestCase):
    def test_delta_dataclass_defaults(self):
        d = InteractionDelta(tick=1)
        self.assertEqual(d.tick, 1)
        self.assertEqual(d.greetings, [])
        self.assertEqual(d.asks, [])
        self.assertEqual(d.answers, [])
        self.assertEqual(d.learnings, [])
        self.assertEqual(d.moves, [])

    def test_tick_returns_delta_with_greeting_when_agents_close(self):
        async def run():
            world = WorldEngine(name="test", width=300, height=300)
            _place_two_agents_close(world)
            delta = await world.tick()
            return delta

        delta = asyncio.run(run())
        self.assertIsInstance(delta, InteractionDelta)
        self.assertEqual(delta.tick, 1)
        # Both agents are within 20 units of each other, so at least one greeting fires.
        self.assertGreaterEqual(len(delta.greetings), 1)
        g = delta.greetings[0]
        self.assertIn(g["from"], {"agent-a", "agent-b"})
        self.assertIn(g["to"],   {"agent-a", "agent-b"})
        self.assertNotEqual(g["from"], g["to"])
        self.assertIn("Nice to meet you", g["text"])

    def test_tick_produces_learnings_when_agents_meet(self):
        async def run():
            world = WorldEngine(name="test", width=300, height=300)
            _place_two_agents_close(world)
            delta = await world.tick()
            return delta

        delta = asyncio.run(run())
        # After a greeting, both agents should have at least one learning event
        # (a memory entry for the new acquaintance).
        agent_ids_with_learnings = {L["agent"] for L in delta.learnings}
        self.assertIn("agent-a", agent_ids_with_learnings)
        # (Beta hasn't necessarily reciprocated on tick 1 — depends on order —
        # but Alpha's memory of Beta is guaranteed to be recorded.)

    def test_tick_records_moves(self):
        """When an agent is far from other agents, it moves toward the nearest location."""
        async def run():
            world = WorldEngine(name="test", width=300, height=300)
            # Solo agent far from any other agents; nearest location is Hub at (150,150).
            # Default world has locations already; let's use create_default_world.
            world2 = WorldEngine.create_default_world()
            delta = await world2.tick()
            return delta

        delta = asyncio.run(run())
        self.assertIsInstance(delta, InteractionDelta)
        # Some agents will have moved this tick (or greeted — either is fine).
        self.assertTrue(len(delta.moves) + len(delta.greetings) >= 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to confirm they fail**

Run:
```powershell
uv run python -m unittest tests.test_living_verse -v
```
Expected: `ImportError: cannot import name 'InteractionDelta' from 'agent_flow.agents.world.engine'` (or equivalent).

- [ ] **Step 3: Add `InteractionDelta` dataclass to `engine.py`**

In `agent_flow/agents/world/engine.py`, immediately after the `WorldEvent` dataclass (~line 302), add:

```python
@dataclass
class InteractionDelta:
    """What happened during a single tick — for typed WS event broadcasts."""
    tick: int
    greetings: list[dict] = field(default_factory=list)
    asks: list[dict] = field(default_factory=list)
    answers: list[dict] = field(default_factory=list)
    learnings: list[dict] = field(default_factory=list)
    moves: list[dict] = field(default_factory=list)
```

- [ ] **Step 4: Add module-level `_QUESTION_BANK` in `engine.py`**

At the top of `engine.py` (below the `EventType` enum, ~line 50), add a module-level list so `tick()` can pick a random question without importing from `agent_verse.py`:

```python
_QUESTION_BANK: list[str] = [
    "What do you do here?",
    "How does this place work?",
    "What skills do you have?",
    "Can you teach me something?",
    "What have you learned recently?",
    "What's the most interesting thing you know?",
    "Have you seen anything strange around here?",
    "Do you know any good places to explore?",
    "What are you working on?",
    "Who else should I meet?",
]
```

- [ ] **Step 5: Rewrite `WorldEngine.tick()` to build and return an `InteractionDelta`**

Replace the entire `tick` method (lines ~378-427 in the current file) with:

```python
    async def tick(self) -> InteractionDelta:
        """نبضة العالم — تحرك + حواس + محادثات + تعلم. تُرجع InteractionDelta."""
        import random as _random  # local import to avoid tainting module globals

        async with self._lock:
            self.tick_count += 1
            delta = InteractionDelta(tick=self.tick_count)

            # Snapshot positions for move detection.
            pre_positions: dict[str, tuple[float, float]] = {
                aid: (a.position.x, a.position.y) for aid, a in self.agents.items()
            }
            # Snapshot per-agent skill count / confidence sum / memory count.
            pre_learning: dict[str, dict[str, float]] = {
                aid: {
                    "skills": len(a.brain.learned_skills),
                    "confidence_sum": sum(s.confidence for s in a.brain.learned_skills.values()),
                    "memories": len(a.brain.memories),
                }
                for aid, a in self.agents.items()
            }

            # Each agent acts.
            for agent in list(self.agents.values()):
                if agent.state == AgentState.SLEEPING:
                    agent.rest(2)
                    continue

                agent.rest(0.5)
                seen = agent.see(self)
                if not seen:
                    continue

                # First: any agent within 20 units → greet + maybe ask.
                talked = False
                for thing in seen:
                    if thing["type"] != "agent" or thing["distance"] >= 20:
                        continue
                    target_id = thing["id"]
                    target = self.agents.get(target_id)
                    if not target:
                        continue

                    # 1. Greet.
                    greeting = f"Hello {thing['name']}! I'm {agent.name}. Nice to meet you!"
                    msg = agent.speak(greeting, target=target_id)
                    self.send_message(msg)
                    delta.greetings.append({
                        "from": agent.agent_id, "from_name": agent.name,
                        "to":   target_id,      "to_name":   thing["name"],
                        "text": greeting,
                    })
                    # Both sides record the meeting → memory delta detected later.
                    agent.brain.meet_agent(target.agent_id, target.name)
                    target.brain.meet_agent(agent.agent_id, agent.name)
                    agent.brain.learn_from_activity("greeting", "success")

                    # 2. Maybe ask a question — curiosity-gated.
                    curiosity = agent.brain.personality_traits.get("curiosity", 0.5)
                    if _random.random() < curiosity:
                        question = _random.choice(_QUESTION_BANK)
                        delta.asks.append({
                            "from": agent.agent_id, "from_name": agent.name,
                            "to":   target_id,      "to_name":   thing["name"],
                            "text": question,
                        })
                        agent.brain.learn_from_activity("asking", "success")

                        # 3. Target answers via existing HermesBrain templated logic.
                        response = target.brain.process_conversation_turn({
                            "sender_id":   agent.agent_id,
                            "sender_name": agent.name,
                            "content":     question,
                        })
                        delta.answers.append({
                            "from": target_id,      "from_name": target.name,
                            "to":   agent.agent_id, "to_name":   agent.name,
                            "text": response,
                        })
                        target.brain.learn_from_activity("answering", "success")

                    talked = True
                    break

                if talked:
                    continue

                # No one nearby → move toward the nearest location.
                nearest = min(seen, key=lambda x: x["distance"])
                if nearest["type"] == "location":
                    target_loc = self.locations.get(nearest["id"])
                    if target_loc:
                        agent.move_toward(target_loc.position, speed=3)

            # Sync hearing states.
            self._clean_old_messages()
            for agent in self.agents.values():
                heard = agent.hear(self)
                if heard:
                    agent.state = AgentState.LISTENING
                elif agent.state == AgentState.TALKING:
                    agent.state = AgentState.IDLE

            # Compute moves delta.
            for aid, agent in self.agents.items():
                pre = pre_positions.get(aid)
                if pre and (pre[0] != agent.position.x or pre[1] != agent.position.y):
                    delta.moves.append({
                        "agent": aid, "agent_name": agent.name,
                        "from_pos": {"x": pre[0], "y": pre[1]},
                        "to_pos":   {"x": agent.position.x, "y": agent.position.y},
                    })

            # Compute learnings delta (skills gained/promoted, new memories).
            for aid, agent in self.agents.items():
                pre = pre_learning.get(aid, {"skills": 0, "confidence_sum": 0.0, "memories": 0})
                cur_skills = len(agent.brain.learned_skills)
                cur_conf   = sum(s.confidence for s in agent.brain.learned_skills.values())
                cur_mem    = len(agent.brain.memories)

                if cur_skills > pre["skills"]:
                    # New skill(s) created.
                    new_names = list(agent.brain.learned_skills.keys())[pre["skills"]:]
                    for name in new_names:
                        sk = agent.brain.learned_skills[name]
                        delta.learnings.append({
                            "agent":      aid, "agent_name": agent.name,
                            "kind_of":    "skill",
                            "detail":     f"{name} ({sk.confidence:.0%})",
                        })
                elif cur_conf > pre["confidence_sum"] + 1e-6:
                    # Same skills but confidence went up → one learning event summary.
                    delta.learnings.append({
                        "agent":      aid, "agent_name": agent.name,
                        "kind_of":    "skill",
                        "detail":     f"improved existing skills (+{cur_conf - pre['confidence_sum']:.2f} conf)",
                    })

                if cur_mem > pre["memories"]:
                    added = cur_mem - pre["memories"]
                    delta.learnings.append({
                        "agent":      aid, "agent_name": agent.name,
                        "kind_of":    "memory",
                        "detail":     f"remembers {added} new {'agent' if added == 1 else 'agents'}",
                    })

            # Company sync every 5 ticks — unchanged.
            if self.tick_count % 5 == 0:
                from agent_flow.agents.world.company_integration import sync_world_with_companies
                asyncio.create_task(sync_world_with_companies(self))

            return delta
```

- [ ] **Step 6: Run tests — verify pass**

Run:
```powershell
uv run python -m unittest tests.test_living_verse.InteractionDeltaTests -v
```
Expected: 4 tests pass.

- [ ] **Step 7: Run the full suite — verify no regressions**

Run:
```powershell
uv run python -W error::ResourceWarning -m unittest discover -s tests -v
```
Expected: All previously-passing tests (29) still pass, plus the 4 new ones = 33 OK.

- [ ] **Step 8: Commit**

```bash
git add agent_flow/agents/world/engine.py tests/test_living_verse.py
git commit -m "feat(world): InteractionDelta + tick() returns typed interaction events

WorldEngine.tick() now returns a dataclass describing greetings, asks,
answers, learnings, and moves for the tick. Templated Q&A logic uses
existing HermesBrain.process_conversation_turn for answers. No behavior
change for callers that discard the return value."
```

---

### Task 2: Enrich `get_state()` with brain snapshots + `total_interactions` / `total_learnings`

**Files:**
- Modify: `agent_flow/agents/world/engine.py:237-253` (`WorldAgent.as_dict`) and `engine.py:439-457` (`WorldEngine.get_state`)
- Modify: `tests/test_living_verse.py` (add test class)

**Interfaces:**
- Consumes: existing `WorldAgent.brain: HermesBrain` (properties `learned_skills`, `memories`, `personality_traits`, `total_interactions`, `discover_role()`).
- Produces:
  - Every `WorldAgent.as_dict()` entry now has a `brain` sub-object matching the shape defined in the spec's "Data model extensions" section.
  - `WorldEngine.get_state()['stats']` gains `total_interactions: int` and `total_learnings: int`.
  - `WorldEngine._total_learnings: int` attribute — running counter incremented inside `tick()` each time an item is appended to `delta.learnings`.

- [ ] **Step 1: Write failing test**

Append to `tests/test_living_verse.py`:

```python
class StateEnrichmentTests(unittest.TestCase):
    def test_agent_dict_includes_brain_snapshot(self):
        world = WorldEngine(name="test", width=300, height=300)
        a = WorldAgent("agent-x", "Xin", Position(50, 50), skills=["exploring"])
        world.spawn_agent(a)

        d = a.as_dict()
        self.assertIn("brain", d)
        brain = d["brain"]
        self.assertIn("role", brain)
        self.assertIn("personality", brain)
        self.assertIn("skills", brain)  # list of {name, confidence, times_used}
        self.assertIsInstance(brain["skills"], list)
        self.assertIn("memory_count", brain)
        self.assertIn("knowledge_recent", brain)
        self.assertIn("questions_asked", brain)
        self.assertIn("questions_answered", brain)

    def test_get_state_stats_include_totals(self):
        world = WorldEngine(name="test", width=300, height=300)
        a1 = WorldAgent("a", "A", Position(100, 100), skills=["writing"])
        a2 = WorldAgent("b", "B", Position(110, 100), skills=["coding"])
        world.spawn_agent(a1)
        world.spawn_agent(a2)

        asyncio.run(world.tick())
        state = world.get_state()
        stats = state["stats"]
        self.assertIn("total_interactions", stats)
        self.assertIn("total_learnings", stats)
        self.assertGreaterEqual(stats["total_interactions"], 1)
        self.assertGreaterEqual(stats["total_learnings"], 1)
```

- [ ] **Step 2: Confirm failure**

Run:
```powershell
uv run python -m unittest tests.test_living_verse.StateEnrichmentTests -v
```
Expected: 2 failures (missing keys `brain`, `total_interactions`).

- [ ] **Step 3: Extend `WorldAgent.as_dict()` with a brain snapshot**

Replace `WorldAgent.as_dict()` in `engine.py` with:

```python
    def as_dict(self) -> dict:
        top_skills = sorted(
            self.brain.learned_skills.values(),
            key=lambda s: (-s.confidence, -s.times_used),
        )[:3]
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "position": self.position.as_dict(),
            "state": self.state.value,
            "energy": round(self.energy, 1),
            "skills": self.skills,
            "sense_range": self.sense_range,
            "hear_range": self.hear_range,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "discovered": len(self.agents_discovered),
            "current_location": self.current_location,
            "memory_count": len(self.memory),
            "created_at": self.created_at,
            "brain": {
                "role": self.brain.discover_role(),
                "personality": {
                    "curiosity":    round(self.brain.personality_traits.get("curiosity", 0.0), 2),
                    "talkativity":  round(self.brain.personality_traits.get("sociability", 0.0), 2),
                    "friendliness": round(self.brain.personality_traits.get("generosity", 0.0), 2),
                },
                "skills": [
                    {"name": s.name, "confidence": round(s.confidence, 2), "times_used": s.times_used}
                    for s in top_skills
                ],
                "memory_count": len(self.brain.memories),
                "knowledge_recent": [
                    m.entity_name for m in list(self.brain.memories.values())[-3:]
                ],
                "questions_asked": self.brain.learned_skills.get("asking").times_used
                    if "asking" in self.brain.learned_skills else 0,
                "questions_answered": self.brain.learned_skills.get("answering").times_used
                    if "answering" in self.brain.learned_skills else 0,
            },
        }
```

- [ ] **Step 4: Add `_total_learnings` counter to `WorldEngine.__init__`**

In `WorldEngine.__init__` (~line 308-319), add one line after `self.tick_count = 0`:

```python
        self._total_learnings = 0
```

- [ ] **Step 5: Increment `_total_learnings` inside `tick()`**

In the block at the end of `tick()` that builds `delta.learnings`, add `self._total_learnings += 1` inside each `delta.learnings.append(...)` block. There are three `append` sites — increment after each.

- [ ] **Step 6: Extend `get_state()` stats**

Replace the `stats` block inside `WorldEngine.get_state()` with:

```python
            "stats": {
                "total_agents": len(self.agents),
                "total_locations": len(self.locations),
                "total_events": len(self.events),
                "active_messages": len(self.active_messages),
                "uptime_seconds": round(time.time() - self.created_at, 1),
                "total_interactions": sum(a.brain.total_interactions for a in self.agents.values()),
                "total_learnings": self._total_learnings,
            },
```

- [ ] **Step 7: Run tests — verify pass**

```powershell
uv run python -m unittest tests.test_living_verse -v
```
Expected: 6 tests pass (4 from Task 1 + 2 new).

- [ ] **Step 8: Run full suite — verify no regressions**

```powershell
uv run python -W error::ResourceWarning -m unittest discover -s tests -v
```
Expected: All tests pass.

- [ ] **Step 9: Commit**

```bash
git add agent_flow/agents/world/engine.py tests/test_living_verse.py
git commit -m "feat(world): enrich get_state with brain snapshot + totals

WorldAgent.as_dict now embeds a compact brain snapshot (role, personality,
top skills, memory count, question counters). WorldEngine.get_state
exposes total_interactions and total_learnings stats for the frontend
WorldPulse strip."
```

---

### Task 3: `broadcast_delta` helper + `tickers` dict in `ws.py`, update `run_world_ticks`

**Files:**
- Modify: `agent_flow/agents/world/ws.py`
- Modify: `tests/test_living_verse.py` (add test class using an `AsyncMock`ed WS manager)

**Interfaces:**
- Consumes: `InteractionDelta` from `engine.py`, `WorldWebSocketManager` from `ws.py`.
- Produces:
  - Module-level `tickers: dict[str, AutonomousTicker]` (populated in Task 4, referenced here so Task 5 can see it exists).
  - `async def broadcast_delta(world_name: str, world: WorldEngine, delta: InteractionDelta) -> None` — broadcasts one WS frame per event type + a `world_pulse` rollup, in the following order: moves, greetings, asks, answers, learnings, world_pulse.
  - `run_world_ticks(world_name, ticks, interval)` unchanged signature but now calls `broadcast_delta` per tick (in addition to the existing `world_tick` broadcast for backward compat).

- [ ] **Step 1: Write failing test**

Append to `tests/test_living_verse.py`:

```python
from unittest.mock import AsyncMock, MagicMock, patch

from agent_flow.agents.world import ws as ws_module


class BroadcastDeltaTests(unittest.TestCase):
    def test_broadcast_delta_emits_typed_events_in_order(self):
        world = WorldEngine(name="test", width=300, height=300)
        _place_two_agents_close(world)

        async def run():
            delta = await world.tick()
            fake_mgr = MagicMock()
            fake_mgr.broadcast = AsyncMock()
            # Patch the module-level ws_manager used inside broadcast_delta.
            with patch.object(ws_module, "ws_manager", fake_mgr):
                await ws_module.broadcast_delta("test", world, delta)
            return fake_mgr

        mgr = asyncio.run(run())
        calls = mgr.broadcast.await_args_list

        # Every call is (world_name, dict-with-'type').
        types_broadcast = [c.args[1]["type"] for c in calls]

        # We expect a world_pulse at the end, and at least one interaction event before it.
        self.assertEqual(types_broadcast[-1], "world_pulse")
        self.assertTrue(any(t == "agent_greeted" for t in types_broadcast))

        # world_pulse payload must include tick + state.agents (from get_state).
        pulse_payload = calls[-1].args[1]
        self.assertIn("tick", pulse_payload)
        self.assertIn("state", pulse_payload)
        self.assertIn("agents", pulse_payload["state"])

    def test_run_world_ticks_broadcasts_delta_events(self):
        """Backward-compat: the old ``Burst 60'' code path must also emit typed events."""
        world = WorldEngine.create_default_world()
        # Register the world in the manager dict so run_world_ticks finds it.
        ws_module.world_manager["burst-test"] = world

        try:
            async def run():
                fake_mgr = MagicMock()
                fake_mgr.broadcast = AsyncMock()
                with patch.object(ws_module, "ws_manager", fake_mgr):
                    await ws_module.run_world_ticks("burst-test", ticks=2, interval=0.01)
                return fake_mgr

            mgr = asyncio.run(run())
            types_broadcast = [c.args[1]["type"] for c in mgr.broadcast.await_args_list]
            self.assertIn("world_pulse", types_broadcast)
        finally:
            ws_module.world_manager.pop("burst-test", None)
```

- [ ] **Step 2: Confirm failure**

```powershell
uv run python -m unittest tests.test_living_verse.BroadcastDeltaTests -v
```
Expected: `AttributeError: module 'agent_flow.agents.world.ws' has no attribute 'broadcast_delta'`.

- [ ] **Step 3: Replace the entirety of `ws.py` with the extended version**

Replace `agent_flow/agents/world/ws.py` with:

```python
"""World WebSocket — real-time agent interactions for the frontend."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any

from agent_flow.agents.world.engine import InteractionDelta, WorldEngine

if TYPE_CHECKING:
    from agent_flow.agents.world.ticker import AutonomousTicker


class WorldWebSocketManager:
    """يدير اتصالات WebSocket للعالم."""

    def __init__(self):
        self.connections: dict[str, list] = {}  # world_name -> [websocket connections]

    def register(self, world_name: str, websocket: Any):
        if world_name not in self.connections:
            self.connections[world_name] = []
        self.connections[world_name].append(websocket)

    def unregister(self, world_name: str, websocket: Any):
        if world_name in self.connections:
            self.connections[world_name] = [ws for ws in self.connections[world_name] if ws != websocket]
            if not self.connections[world_name]:
                del self.connections[world_name]

    async def broadcast(self, world_name: str, data: dict):
        """إرسال تحديث لجميع المتصلين بالعالم."""
        if world_name not in self.connections:
            return
        dead = []
        for ws in self.connections[world_name]:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.unregister(world_name, ws)


# World manager — يحتفظ بكل العوالم النشطة.
world_manager: dict[str, WorldEngine] = {}
ws_manager = WorldWebSocketManager()
# Autonomous tickers, keyed by world name — one per world.
tickers: dict[str, "AutonomousTicker"] = {}


def get_or_create_world(name: str = "agentverse") -> WorldEngine:
    """الحصول على عالم أو إنشائه إن لم يوجد."""
    if name not in world_manager:
        world_manager[name] = WorldEngine.create_default_world()
    return world_manager[name]


def _pulse_payload(world: WorldEngine, tick: int) -> dict:
    """Build the world_pulse WS frame payload (state + companies)."""
    from agent_flow.agents.world.company_integration import company_store
    state = world.get_state()
    state["companies"] = [c.as_dict() for c in company_store.all()]
    return {"type": "world_pulse", "tick": tick, "state": state}


async def broadcast_delta(world_name: str, world: WorldEngine, delta: InteractionDelta) -> None:
    """Send one WS frame per interaction, plus a rollup world_pulse.

    Order: moves → greetings → asks → answers → learnings → world_pulse.
    """
    for i, m in enumerate(delta.moves):
        await ws_manager.broadcast(world_name, {
            "type": "agent_moved",
            "id": f"mv_{delta.tick:05d}_{i}",
            **m,
            "tick": delta.tick,
        })
    for i, g in enumerate(delta.greetings):
        await ws_manager.broadcast(world_name, {
            "type": "agent_greeted",
            "id": f"grt_{delta.tick:05d}_{i}",
            **g,
            "tick": delta.tick,
        })
    for i, a in enumerate(delta.asks):
        await ws_manager.broadcast(world_name, {
            "type": "agent_asked",
            "id": f"ask_{delta.tick:05d}_{i}",
            **a,
            "tick": delta.tick,
        })
    for i, a in enumerate(delta.answers):
        await ws_manager.broadcast(world_name, {
            "type": "agent_answered",
            "id": f"ans_{delta.tick:05d}_{i}",
            **a,
            "tick": delta.tick,
        })
    for i, L in enumerate(delta.learnings):
        await ws_manager.broadcast(world_name, {
            "type": "agent_learned",
            "id": f"lrn_{delta.tick:05d}_{i}",
            **L,
            "tick": delta.tick,
        })
    await ws_manager.broadcast(world_name, _pulse_payload(world, delta.tick))


async def run_world_ticks(world_name: str, ticks: int = 20, interval: float = 2.0):
    """تشغيل نبضات العالم مع بث التحديثات للواجهة."""
    world = world_manager.get(world_name)
    if not world:
        return

    for _ in range(ticks):
        delta = await world.tick()
        await broadcast_delta(world_name, world, delta)
        await asyncio.sleep(interval)
```

- [ ] **Step 4: Run tests — verify pass**

```powershell
uv run python -m unittest tests.test_living_verse.BroadcastDeltaTests -v
```
Expected: 2 tests pass.

- [ ] **Step 5: Run full suite**

```powershell
uv run python -W error::ResourceWarning -m unittest discover -s tests -v
```
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add agent_flow/agents/world/ws.py tests/test_living_verse.py
git commit -m "feat(world): broadcast_delta helper + tickers registry

Shared helper that broadcasts one WS frame per interaction type plus a
world_pulse rollup. run_world_ticks now uses this helper too so the
old Burst-60 button surfaces the same typed events as the autonomous
ticker will."
```

---

### Task 4: `AutonomousTicker` class

**Files:**
- Create: `agent_flow/agents/world/ticker.py`
- Modify: `tests/test_living_verse.py` (add test class)

**Interfaces:**
- Consumes: `WorldEngine` (`tick()` returns `InteractionDelta`), `WorldWebSocketManager`, `broadcast_delta` helper.
- Produces:
  - `class AutonomousTicker` with methods:
    - `__init__(self, world_name: str, world: WorldEngine, ws_manager: WorldWebSocketManager, pace_seconds: float = 3.0)`
    - `is_running(self) -> bool`
    - `pace_seconds: float` (property, read-only)
    - `async def start(self) -> None` (idempotent)
    - `async def stop(self) -> None` (waits for task to finish)
    - `def set_pace(self, pace_seconds: float) -> None` (clamps to [1.0, 10.0])
  - Publishes `world_ticker` WS frames on start/stop/set_pace/crash with `{"type": "world_ticker", "status": "running"|"paused"|"crashed", "pace_seconds": float, "error"?: str}`.
  - Crash rule: 3 consecutive `tick()` exceptions → publish crashed, exit.

- [ ] **Step 1: Write failing test**

Append to `tests/test_living_verse.py`:

```python
class AutonomousTickerTests(unittest.TestCase):
    def test_ticker_start_stop_publishes_status(self):
        from agent_flow.agents.world.ticker import AutonomousTicker

        world = WorldEngine(name="tick-test", width=300, height=300)
        _place_two_agents_close(world)
        fake_mgr = MagicMock()
        fake_mgr.broadcast = AsyncMock()

        async def run():
            ticker = AutonomousTicker("tick-test", world, fake_mgr, pace_seconds=0.05)
            await ticker.start()
            await asyncio.sleep(0.2)   # let ~3-4 ticks happen
            await ticker.stop()
            return ticker

        ticker = asyncio.run(run())
        self.assertFalse(ticker.is_running())

        types_broadcast = [c.args[1]["type"] for c in fake_mgr.broadcast.await_args_list]
        # world_ticker frames on start and on stop.
        ticker_frames = [
            c.args[1] for c in fake_mgr.broadcast.await_args_list
            if c.args[1]["type"] == "world_ticker"
        ]
        self.assertTrue(any(f["status"] == "running" for f in ticker_frames))
        self.assertTrue(any(f["status"] == "paused"  for f in ticker_frames))
        # And at least one world_pulse frame from the ticks that happened.
        self.assertIn("world_pulse", types_broadcast)

    def test_ticker_set_pace_clamps(self):
        from agent_flow.agents.world.ticker import AutonomousTicker

        world = WorldEngine(name="pace-test", width=300, height=300)
        fake_mgr = MagicMock()
        fake_mgr.broadcast = AsyncMock()
        ticker = AutonomousTicker("pace-test", world, fake_mgr, pace_seconds=3.0)

        ticker.set_pace(0.5)   # below floor
        self.assertEqual(ticker.pace_seconds, 1.0)
        ticker.set_pace(99.0)  # above ceiling
        self.assertEqual(ticker.pace_seconds, 10.0)
        ticker.set_pace(4.0)
        self.assertEqual(ticker.pace_seconds, 4.0)

    def test_ticker_crashes_after_three_failures(self):
        from agent_flow.agents.world.ticker import AutonomousTicker

        # Broken world: tick() always raises.
        broken_world = MagicMock()
        broken_world.tick = AsyncMock(side_effect=RuntimeError("boom"))
        broken_world.get_state = MagicMock(return_value={"stats": {}, "agents": []})

        fake_mgr = MagicMock()
        fake_mgr.broadcast = AsyncMock()

        async def run():
            ticker = AutonomousTicker("crash-test", broken_world, fake_mgr, pace_seconds=0.01)
            await ticker.start()
            # Wait long enough for 3 failures + a bit.
            await asyncio.sleep(0.5)
            return ticker

        ticker = asyncio.run(run())
        self.assertFalse(ticker.is_running())

        crashed_frames = [
            c.args[1] for c in fake_mgr.broadcast.await_args_list
            if c.args[1].get("type") == "world_ticker" and c.args[1].get("status") == "crashed"
        ]
        self.assertTrue(len(crashed_frames) >= 1)
        self.assertIn("error", crashed_frames[0])
```

- [ ] **Step 2: Confirm failure**

```powershell
uv run python -m unittest tests.test_living_verse.AutonomousTickerTests -v
```
Expected: `ModuleNotFoundError: No module named 'agent_flow.agents.world.ticker'`.

- [ ] **Step 3: Create `ticker.py`**

Create `agent_flow/agents/world/ticker.py`:

```python
"""AutonomousTicker — background asyncio task that ticks a WorldEngine.

Broadcasts a world_ticker WS frame on every status change (start / pause /
set_pace / crash). Interactions each tick go through broadcast_delta.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from agent_flow.agents.world.engine import WorldEngine
from agent_flow.agents.world.ws import (
    WorldWebSocketManager,
    broadcast_delta,
)

log = logging.getLogger(__name__)

_PACE_MIN = 1.0
_PACE_MAX = 10.0
_CRASH_THRESHOLD = 3


class AutonomousTicker:
    """Runs an asyncio loop that repeatedly ticks a WorldEngine."""

    def __init__(
        self,
        world_name: str,
        world: WorldEngine,
        ws_manager: WorldWebSocketManager,
        pace_seconds: float = 3.0,
    ):
        self._world_name = world_name
        self._world = world
        self._ws = ws_manager
        self._pace = _clamp_pace(pace_seconds)
        self._stop = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    @property
    def pace_seconds(self) -> float:
        return self._pace

    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        """Idempotent — a second start on a running ticker is a no-op."""
        if self.is_running():
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._run())
        await self._publish_status("running")

    async def stop(self) -> None:
        if not self.is_running():
            return
        self._stop.set()
        assert self._task is not None
        try:
            await asyncio.wait_for(self._task, timeout=self._pace * 2 + 1.0)
        except asyncio.TimeoutError:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        self._task = None
        await self._publish_status("paused")

    def set_pace(self, pace_seconds: float) -> None:
        self._pace = _clamp_pace(pace_seconds)

    async def _run(self) -> None:
        consecutive_failures = 0
        while not self._stop.is_set():
            try:
                delta = await self._world.tick()
                await broadcast_delta(self._world_name, self._world, delta)
                consecutive_failures = 0
            except Exception as exc:  # noqa: BLE001 — resilient background loop
                consecutive_failures += 1
                log.exception("AutonomousTicker tick failed (%d/%d)",
                              consecutive_failures, _CRASH_THRESHOLD)
                if consecutive_failures >= _CRASH_THRESHOLD:
                    await self._publish_status("crashed", error=str(exc))
                    return
                # Back off a little to avoid hot-looping on repeated failures.
                await self._sleep(self._pace * 2)
                continue

            await self._sleep(self._pace)

    async def _sleep(self, seconds: float) -> None:
        """Sleep interruptibly — returns immediately if _stop is set."""
        try:
            await asyncio.wait_for(self._stop.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            pass

    async def _publish_status(self, status: str, *, error: Optional[str] = None) -> None:
        payload = {
            "type": "world_ticker",
            "status": status,
            "pace_seconds": self._pace,
        }
        if error is not None:
            payload["error"] = error
        await self._ws.broadcast(self._world_name, payload)


def _clamp_pace(value: float) -> float:
    if value < _PACE_MIN:
        return _PACE_MIN
    if value > _PACE_MAX:
        return _PACE_MAX
    return float(value)
```

- [ ] **Step 4: Run tests — verify pass**

```powershell
uv run python -m unittest tests.test_living_verse.AutonomousTickerTests -v
```
Expected: 3 tests pass.

- [ ] **Step 5: Full suite check**

```powershell
uv run python -W error::ResourceWarning -m unittest discover -s tests -v
```
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add agent_flow/agents/world/ticker.py tests/test_living_verse.py
git commit -m "feat(world): AutonomousTicker

Background asyncio task that ticks a WorldEngine on a configurable pace
[1s..10s], broadcasts world_ticker status on start/pause/set_pace/crash,
and exits cleanly after 3 consecutive tick failures."
```

---

### Task 5: WS command handler — start / pause / set_pace + connect-time status

**Files:**
- Modify: `agent_flow/agents/world/api.py:184-239` (`world_websocket`)
- Modify: `tests/test_living_verse.py` (add test class using FastAPI's `TestClient`)

**Interfaces:**
- Consumes: `AutonomousTicker`, `tickers` dict from `ws.py`.
- Produces:
  - New client → server actions on `/world/{world_name}/ws`: `start`, `pause`, `set_pace`.
  - On connect, in addition to `world_state`, server sends one `world_ticker` frame reflecting current status (`"idle"` if no ticker exists yet, otherwise `"running"`/`"paused"`).

- [ ] **Step 1: Write failing test**

Append to `tests/test_living_verse.py`:

```python
class WebSocketCommandTests(unittest.TestCase):
    def _client(self):
        # Import here so failing production import doesn't blow up the whole test file.
        from fastapi.testclient import TestClient
        from agent_flow.agents.api.main import app  # type: ignore
        return TestClient(app)

    def test_connect_sends_world_state_and_ticker_status(self):
        client = self._client()
        with client.websocket_connect("/world/test-cmd/ws") as ws:
            frame1 = ws.receive_json()
            frame2 = ws.receive_json()
        # Order isn't strictly guaranteed, but both must appear in the first two frames.
        types = {frame1["type"], frame2["type"]}
        self.assertIn("world_state", types)
        self.assertIn("world_ticker", types)

    def test_start_action_launches_ticker(self):
        client = self._client()
        with client.websocket_connect("/world/test-start/ws") as ws:
            ws.receive_json()  # world_state
            ws.receive_json()  # world_ticker (idle)
            ws.send_json({"action": "start", "pace_seconds": 0.05})
            # Expect at least one world_ticker(status=running) frame in the next few messages.
            got_running = False
            for _ in range(10):
                frame = ws.receive_json()
                if frame.get("type") == "world_ticker" and frame.get("status") == "running":
                    got_running = True
                    break
            ws.send_json({"action": "pause"})
        self.assertTrue(got_running)

    def test_set_pace_clamps_and_broadcasts(self):
        client = self._client()
        with client.websocket_connect("/world/test-pace/ws") as ws:
            ws.receive_json()  # world_state
            ws.receive_json()  # world_ticker (idle)
            ws.send_json({"action": "start", "pace_seconds": 3.0})
            # drain until running frame
            for _ in range(5):
                f = ws.receive_json()
                if f.get("type") == "world_ticker" and f.get("status") == "running":
                    break

            ws.send_json({"action": "set_pace", "pace_seconds": 99.0})
            frame = None
            for _ in range(10):
                f = ws.receive_json()
                if f.get("type") == "world_ticker" and f.get("pace_seconds") == 10.0:
                    frame = f
                    break

            ws.send_json({"action": "pause"})

        self.assertIsNotNone(frame)
```

- [ ] **Step 2: Confirm failure**

```powershell
uv run python -m unittest tests.test_living_verse.WebSocketCommandTests -v
```
Expected: `KeyError` or missing action / status frame not delivered.

- [ ] **Step 3: Update the WS handler in `api.py`**

Replace the `world_websocket` function (lines ~184-239 of `api.py`) with:

```python
@router.websocket("/{world_name}/ws")
async def world_websocket(websocket: WebSocket, world_name: str):
    """WebSocket للتحديثات الحية للعالم."""
    await websocket.accept()
    world = get_or_create_world(world_name)
    ws_manager.register(world_name, websocket)

    try:
        # Initial world state.
        state = world.get_state()
        state["companies"] = [c.as_dict() for c in company_store.all()]
        await websocket.send_json({
            "type": "world_state",
            "data": state,
        })

        # Initial ticker status (idle | running | paused).
        from agent_flow.agents.world.ws import tickers
        existing = tickers.get(world_name)
        if existing and existing.is_running():
            status, pace = "running", existing.pace_seconds
        elif existing:
            status, pace = "paused", existing.pace_seconds
        else:
            status, pace = "idle", 3.0
        await websocket.send_json({
            "type": "world_ticker",
            "status": status,
            "pace_seconds": pace,
        })

        # Command loop.
        from agent_flow.agents.world.ticker import AutonomousTicker

        while True:
            data = await websocket.receive_text()
            try:
                cmd = json.loads(data)
                action = cmd.get("action", "")

                if action == "speak":
                    agent = world.agents.get(cmd.get("agent_id", ""))
                    if agent:
                        msg = agent.speak(cmd.get("content", ""), cmd.get("target", "nearby"))
                        world.send_message(msg)
                        await ws_manager.broadcast(world_name, {
                            "type": "agent_spoke",
                            "message": msg.as_dict(),
                        })

                elif action == "move":
                    agent = world.agents.get(cmd.get("agent_id", ""))
                    if agent:
                        agent.move_toward(Position(cmd["x"], cmd["y"]))
                        await ws_manager.broadcast(world_name, {
                            "type": "agent_moved",
                            "agent_id": agent.agent_id,
                            "position": agent.position.as_dict(),
                        })

                elif action == "tick":
                    for _ in range(cmd.get("count", 1)):
                        delta = await world.tick()
                        from agent_flow.agents.world.ws import broadcast_delta
                        await broadcast_delta(world_name, world, delta)

                elif action == "start":
                    pace = float(cmd.get("pace_seconds", 3.0))
                    ticker = tickers.get(world_name)
                    if ticker is None:
                        ticker = AutonomousTicker(world_name, world, ws_manager, pace_seconds=pace)
                        tickers[world_name] = ticker
                    else:
                        ticker.set_pace(pace)
                    await ticker.start()

                elif action == "pause":
                    ticker = tickers.get(world_name)
                    if ticker:
                        await ticker.stop()

                elif action == "set_pace":
                    pace = float(cmd.get("pace_seconds", 3.0))
                    ticker = tickers.get(world_name)
                    if ticker:
                        ticker.set_pace(pace)
                        # Reflect new pace to all subscribers.
                        await ws_manager.broadcast(world_name, {
                            "type": "world_ticker",
                            "status": "running" if ticker.is_running() else "paused",
                            "pace_seconds": ticker.pace_seconds,
                        })

            except (json.JSONDecodeError, KeyError, ValueError):
                pass

    except WebSocketDisconnect:
        ws_manager.unregister(world_name, websocket)
```

- [ ] **Step 4: Run tests — verify pass**

```powershell
uv run python -m unittest tests.test_living_verse.WebSocketCommandTests -v
```
Expected: 3 tests pass.

- [ ] **Step 5: Full suite check**

```powershell
uv run python -W error::ResourceWarning -m unittest discover -s tests -v
```
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add agent_flow/agents/world/api.py tests/test_living_verse.py
git commit -m "feat(world): WS start/pause/set_pace commands + connect-time status

The /world/{name}/ws endpoint now accepts start/pause/set_pace actions
routed to a per-world AutonomousTicker, and sends the current ticker
status right after the initial world_state on connect."
```

---

### Task 6: Shutdown handler — stop all tickers cleanly

**Files:**
- Modify: `production.py`

**Interfaces:**
- Consumes: `tickers` dict from `agent_flow.agents.world.ws`.
- Produces: FastAPI shutdown handler that awaits each ticker's `.stop()`.

- [ ] **Step 1: Read the current `production.py` to find the FastAPI app object**

Run:
```powershell
Get-Content e:\ai_projects\Agent-Flow\production.py | Select-Object -First 60
```
Note the app variable name (likely `app`) and whether it already has lifespan handlers.

- [ ] **Step 2: Add shutdown handler**

Add near the end of `production.py`, after the app is constructed and before the uvicorn call:

```python
@app.on_event("shutdown")
async def _stop_all_tickers() -> None:
    """Cleanly stop every AutonomousTicker so Uvicorn shuts down without warnings."""
    from agent_flow.agents.world.ws import tickers
    for name, ticker in list(tickers.items()):
        try:
            await ticker.stop()
        except Exception:
            pass
        tickers.pop(name, None)
```

If `production.py` uses the newer `lifespan` context manager pattern instead of `@app.on_event`, put the equivalent stop loop in the shutdown branch of that context. Check by reading the file first.

- [ ] **Step 3: Smoke test — start & stop the server**

```powershell
uv run python production.py > backend.stdout.log 2> backend.stderr.log
# In another shell:
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing | Select-Object -ExpandProperty Content
# Then Ctrl+C the backend and verify no "Task was destroyed but it is pending!" warnings appear in backend.stderr.log.
```
Expected: server exits within a couple of seconds; no dangling-task warnings.

- [ ] **Step 4: Commit**

```bash
git add production.py
git commit -m "chore(server): stop AutonomousTickers on FastAPI shutdown

Avoids 'Task was destroyed but it is pending!' warnings from Uvicorn
when the user Ctrl+Cs the process while a ticker is running."
```

---

### Task 7: Frontend `WorldPulse.tsx`

**Files:**
- Create: `frontend/src/components/world/WorldPulse.tsx`

**Interfaces:**
- Consumes: props (see below) — no direct WS or backend access.
- Produces: a pure presentational component exported as default.
- Consumed by (Task 10): `frontend/src/app/world/page.tsx`.

```ts
export type WorldPulseProps = {
  tick: number;
  status: "idle" | "running" | "paused" | "crashed";
  paceSeconds: number;
  uptimeSeconds: number;
  agentCount: number;
  totalInteractions: number;
  totalLearnings: number;
};
```

- [ ] **Step 1: Ensure the components/world folder exists**

Run:
```powershell
if (-not (Test-Path e:\ai_projects\Agent-Flow\frontend\src\components\world)) { New-Item -ItemType Directory e:\ai_projects\Agent-Flow\frontend\src\components\world | Out-Null }
```

- [ ] **Step 2: Create `WorldPulse.tsx`**

Create `frontend/src/components/world/WorldPulse.tsx`:

```tsx
"use client";

export type WorldPulseStatus = "idle" | "running" | "paused" | "crashed";

export type WorldPulseProps = {
  tick: number;
  status: WorldPulseStatus;
  paceSeconds: number;
  uptimeSeconds: number;
  agentCount: number;
  totalInteractions: number;
  totalLearnings: number;
};

const DOT_COLOR: Record<WorldPulseStatus, string> = {
  idle:    "bg-amber-400",
  running: "bg-emerald-400 animate-pulse",
  paused:  "bg-zinc-500",
  crashed: "bg-rose-500",
};

const STATUS_LABEL: Record<WorldPulseStatus, string> = {
  idle:    "idle",
  running: "running",
  paused:  "paused",
  crashed: "crashed",
};

function formatUptime(sec: number): string {
  if (sec < 60) return `${sec.toFixed(0)}s`;
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}m ${s}s`;
}

export default function WorldPulse({
  tick, status, paceSeconds, uptimeSeconds, agentCount, totalInteractions, totalLearnings,
}: WorldPulseProps) {
  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-zinc-900/60 border border-zinc-800 rounded-xl text-xs tabular-nums text-zinc-300">
      <span className="flex items-center gap-1.5">
        <span className={`inline-block h-2 w-2 rounded-full ${DOT_COLOR[status]}`} />
        <span className="capitalize">{STATUS_LABEL[status]}</span>
      </span>
      <span className="text-zinc-600">·</span>
      <span>tick <span className="text-white">{tick}</span></span>
      <span className="text-zinc-600">·</span>
      <span>pace <span className="text-white">{paceSeconds.toFixed(1)}s</span></span>
      <span className="text-zinc-600">·</span>
      <span>{agentCount} agents</span>
      <span className="text-zinc-600">·</span>
      <span>↔ {totalInteractions}</span>
      <span className="text-zinc-600">·</span>
      <span>✨ {totalLearnings}</span>
      <span className="ml-auto text-zinc-500">{formatUptime(uptimeSeconds)}</span>
    </div>
  );
}
```

- [ ] **Step 3: Smoke check — confirm the file compiles**

The frontend dev server already reloads on file changes. Just visit any page in the browser — no console error. Full wiring happens in Task 10.

Alternatively, run a one-off typecheck:
```powershell
cd e:\ai_projects\Agent-Flow\frontend
npx tsc --noEmit
```
Expected: no new errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/world/WorldPulse.tsx
git commit -m "feat(world/ui): WorldPulse component

Horizontal telemetry strip: status dot, tick counter, pace, agent count,
interaction/learning totals, uptime. Pure presentational — driven by
props from the /world page."
```

---

### Task 8: Frontend `InteractionStream.tsx`

**Files:**
- Create: `frontend/src/components/world/InteractionStream.tsx`
- Modify: `frontend/src/app/globals.css` (add one keyframe animation)

**Interfaces:**
- Consumes: props (see below).
- Produces: a pure presentational component exported as default.
- Consumed by (Task 10): `frontend/src/app/world/page.tsx`.

```ts
export type InteractionEventKind = "greeted" | "asked" | "answered" | "learned";
export type InteractionEvent =
  | { kind: "greeted";  id: string; from: string; from_name: string; to_name: string; text: string; tick: number }
  | { kind: "asked";    id: string; from: string; from_name: string; to_name: string; text: string; tick: number }
  | { kind: "answered"; id: string; from: string; from_name: string; to_name: string; text: string; tick: number }
  | { kind: "learned";  id: string; agent: string; agent_name: string; detail: string; kind_of: "skill"|"memory"|"knowledge"; tick: number };

export type InteractionStreamProps = {
  events: InteractionEvent[];   // oldest first, newest at the end
  agentColors: Record<string, string>;  // agent_id → hex
};
```

- [ ] **Step 1: Add slide-in keyframe to `globals.css`**

Append to `frontend/src/app/globals.css` (bottom of file):

```css
@keyframes lv-slide-in {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0);   }
}
.lv-slide-in { animation: lv-slide-in 300ms ease-out; }

@keyframes lv-flash {
  0%   { background-color: rgba(250, 204, 21, 0.35); }
  100% { background-color: transparent; }
}
.lv-flash { animation: lv-flash 400ms ease-out; }
```

- [ ] **Step 2: Create `InteractionStream.tsx`**

Create `frontend/src/components/world/InteractionStream.tsx`:

```tsx
"use client";

import { useEffect, useRef } from "react";

export type InteractionEventKind = "greeted" | "asked" | "answered" | "learned";
export type InteractionEvent =
  | { kind: "greeted";  id: string; from: string; from_name: string; to_name: string; text: string; tick: number }
  | { kind: "asked";    id: string; from: string; from_name: string; to_name: string; text: string; tick: number }
  | { kind: "answered"; id: string; from: string; from_name: string; to_name: string; text: string; tick: number }
  | { kind: "learned";  id: string; agent: string; agent_name: string; detail: string; kind_of: "skill"|"memory"|"knowledge"; tick: number };

export type InteractionStreamProps = {
  events: InteractionEvent[];
  agentColors: Record<string, string>;
};

const KIND_ICON: Record<InteractionEventKind, string> = {
  greeted:  "👋",
  asked:    "🙋",
  answered: "💬",
  learned:  "✨",
};

const LEARN_ICON: Record<"skill" | "memory" | "knowledge", string> = {
  skill:     "🛠",
  memory:    "🤝",
  knowledge: "📖",
};

function renderRow(ev: InteractionEvent, agentColors: Record<string, string>) {
  const actor = ev.kind === "learned" ? ev.agent : ev.from;
  const actorName = ev.kind === "learned" ? ev.agent_name : ev.from_name;
  const color = agentColors[actor] ?? "#8b5cf6";
  const icon = ev.kind === "learned" ? LEARN_ICON[ev.kind_of] : KIND_ICON[ev.kind];

  let body: React.ReactNode;
  switch (ev.kind) {
    case "greeted":
      body = <><span className="text-white">{ev.from_name}</span><span className="text-zinc-500"> → </span><span className="text-white">{ev.to_name}</span>: <span className="text-zinc-300">{ev.text}</span></>;
      break;
    case "asked":
      body = <><span className="text-white">{ev.from_name}</span><span className="text-zinc-500"> asks </span><span className="text-white">{ev.to_name}</span>: <span className="text-amber-300">"{ev.text}"</span></>;
      break;
    case "answered":
      body = <><span className="text-white">{ev.from_name}</span><span className="text-zinc-500"> answers </span><span className="text-white">{ev.to_name}</span>: <span className="text-emerald-300">"{ev.text}"</span></>;
      break;
    case "learned":
      body = <><span className="text-white">{ev.agent_name}</span><span className="text-zinc-500"> learned </span><span className="text-violet-300">{ev.detail}</span></>;
      break;
  }

  return (
    <div key={ev.id} className="lv-slide-in flex items-start gap-2 text-xs py-1 px-2 border-b border-zinc-900/60">
      <span className="inline-block h-2 w-2 rounded-full mt-1.5 flex-shrink-0" style={{ backgroundColor: color }} />
      <span className="w-4 flex-shrink-0 text-center" aria-hidden>{icon}</span>
      <span className="text-zinc-400 tabular-nums flex-shrink-0">t{ev.tick}</span>
      <span className="flex-1 min-w-0 break-words">{body}</span>
    </div>
  );
}

export default function InteractionStream({ events, agentColors }: InteractionStreamProps) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const atBottomRef = useRef(true);

  const onScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    atBottomRef.current = nearBottom;
  };

  useEffect(() => {
    if (atBottomRef.current && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events.length]);

  return (
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-2 h-full flex flex-col">
      <div className="text-white font-semibold text-sm px-2 pb-2">💭 Interactions</div>
      <div
        ref={scrollRef}
        onScroll={onScroll}
        className="flex-1 overflow-y-auto min-h-0 rounded-lg"
      >
        {events.length === 0 ? (
          <p className="text-zinc-600 text-xs px-3 py-6 text-center animate-pulse">
            Waiting for the world to come alive...
          </p>
        ) : (
          events.map((e) => renderRow(e, agentColors))
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Typecheck**

```powershell
cd e:\ai_projects\Agent-Flow\frontend
npx tsc --noEmit
```
Expected: no new errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/world/InteractionStream.tsx frontend/src/app/globals.css
git commit -m "feat(world/ui): InteractionStream component

Scrollable feed of greeted / asked / answered / learned events with
sticky-bottom auto-scroll and slide-in animation. Uses two new global
keyframes: lv-slide-in and lv-flash."
```

---

### Task 9: Frontend `AgentLearningCards.tsx`

**Files:**
- Create: `frontend/src/components/world/AgentLearningCards.tsx`

**Interfaces:**
- Consumes: props (see below).
- Produces: a pure presentational component exported as default.
- Consumed by (Task 10): `frontend/src/app/world/page.tsx`.

```ts
export type BrainSnapshot = {
  role: string;
  personality: { curiosity: number; talkativity: number; friendliness: number };
  skills: Array<{ name: string; confidence: number; times_used: number }>;
  memory_count: number;
  knowledge_recent: string[];
  questions_asked: number;
  questions_answered: number;
};

export type AgentLearningCardsProps = {
  agents: Array<{ agent_id: string; name: string }>;
  brains: Record<string, BrainSnapshot>;    // agent_id → snapshot
  recentDeltas: Record<string, { asked?: boolean; answered?: boolean; memories?: boolean; skills?: boolean }>;
  agentColors: Record<string, string>;
};
```

- [ ] **Step 1: Create `AgentLearningCards.tsx`**

Create `frontend/src/components/world/AgentLearningCards.tsx`:

```tsx
"use client";

export type BrainSnapshot = {
  role: string;
  personality: { curiosity: number; talkativity: number; friendliness: number };
  skills: Array<{ name: string; confidence: number; times_used: number }>;
  memory_count: number;
  knowledge_recent: string[];
  questions_asked: number;
  questions_answered: number;
};

export type AgentLearningCardsProps = {
  agents: Array<{ agent_id: string; name: string }>;
  brains: Record<string, BrainSnapshot>;
  recentDeltas: Record<string, { asked?: boolean; answered?: boolean; memories?: boolean; skills?: boolean }>;
  agentColors: Record<string, string>;
};

function Bar({ value, label, color = "bg-violet-500" }: { value: number; label: string; color?: string }) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div className="flex items-center gap-1.5 text-[10px]">
      <span className="w-14 text-zinc-500">{label}</span>
      <div className="flex-1 h-1 bg-zinc-800 rounded overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-6 text-right text-zinc-400 tabular-nums">{Math.round(pct)}%</span>
    </div>
  );
}

function Counter({ label, value, flash, icon }: { label: string; value: number; flash?: boolean; icon: string }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 tabular-nums ${flash ? "lv-flash" : ""}`}>
      <span aria-hidden>{icon}</span>
      <span className="text-zinc-500">{label}</span>
      <span className="text-white">{value}</span>
    </span>
  );
}

export default function AgentLearningCards({
  agents, brains, recentDeltas, agentColors,
}: AgentLearningCardsProps) {
  if (agents.length === 0) {
    return <p className="text-zinc-600 text-xs">No agents yet.</p>;
  }
  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-2">
      {agents.map((a) => {
        const brain = brains[a.agent_id];
        const color = agentColors[a.agent_id] ?? "#8b5cf6";
        const delta = recentDeltas[a.agent_id] ?? {};
        if (!brain) {
          return (
            <div key={a.agent_id} className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-3">
              <div className="flex items-center gap-2 mb-2">
                <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-white text-sm font-medium">{a.name}</span>
                <span className="text-zinc-500 text-xs">loading…</span>
              </div>
            </div>
          );
        }
        return (
          <div key={a.agent_id} className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-2">
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-white text-sm font-medium">{a.name}</span>
              <span className="text-zinc-500 text-[10px] uppercase tracking-wider">{brain.role}</span>
            </div>

            <div className="space-y-1 mb-2">
              <Bar label="curiosity"    value={brain.personality.curiosity}    color="bg-amber-400" />
              <Bar label="talkativity"  value={brain.personality.talkativity}  color="bg-sky-400" />
              <Bar label="friendliness" value={brain.personality.friendliness} color="bg-emerald-400" />
            </div>

            <div className="space-y-1 mb-2">
              {brain.skills.slice(0, 3).map((s) => (
                <div key={s.name} className={`flex items-center gap-1.5 text-[10px] ${delta.skills ? "lv-flash rounded" : ""}`}>
                  <span className="w-14 text-zinc-400 truncate">{s.name}</span>
                  <div className="flex-1 h-1 bg-zinc-800 rounded overflow-hidden">
                    <div className="h-full bg-violet-500" style={{ width: `${s.confidence * 100}%` }} />
                  </div>
                  <span className="w-8 text-right text-zinc-500 tabular-nums">×{s.times_used}</span>
                </div>
              ))}
            </div>

            <div className="flex flex-wrap gap-1 text-[10px] mb-1">
              <Counter label="asked"    value={brain.questions_asked}    flash={delta.asked}    icon="🙋" />
              <Counter label="answered" value={brain.questions_answered} flash={delta.answered} icon="💬" />
              <Counter label="memories" value={brain.memory_count}       flash={delta.memories} icon="🤝" />
            </div>

            {brain.knowledge_recent.length > 0 && (
              <div className="text-[10px] text-zinc-500 mt-1 truncate">
                📖 {brain.knowledge_recent.slice(-3).join(" · ")}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: Typecheck**

```powershell
cd e:\ai_projects\Agent-Flow\frontend
npx tsc --noEmit
```
Expected: no new errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/world/AgentLearningCards.tsx
git commit -m "feat(world/ui): AgentLearningCards component

Per-agent cards with personality bars, top-3 skills w/ confidence + use
count, ask/answer/memory counters that flash yellow on recent deltas,
and a short recent-knowledge trail."
```

---

### Task 10: `/world` page rewrite — split layout, header controls, new WS state

**Files:**
- Modify: `frontend/src/app/world/page.tsx` (full rewrite)

**Interfaces:**
- Consumes: components from Tasks 7-9 (`WorldPulse`, `InteractionStream`, `AgentLearningCards`), backend WS events (`world_state`, `world_pulse`, `world_ticker`, `agent_greeted`, `agent_asked`, `agent_answered`, `agent_learned`, `agent_moved`, `agent_spoke`, `agent_spawned`, `agent_removed`).
- Produces: an updated `/world` page. No new routes.

- [ ] **Step 1: Rewrite `frontend/src/app/world/page.tsx`**

Replace the entire file with:

```tsx
"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import WorldPulse, { WorldPulseStatus } from "@/components/world/WorldPulse";
import InteractionStream, { InteractionEvent } from "@/components/world/InteractionStream";
import AgentLearningCards, { BrainSnapshot } from "@/components/world/AgentLearningCards";

type Agent = {
  agent_id: string;
  name: string;
  position: { x: number; y: number };
  state: string;
  energy: number;
  skills: string[];
  discovered: number;
  messages_sent: number;
  messages_received: number;
  brain?: BrainSnapshot;
};
type Location = { id: string; name: string; position: { x: number; y: number }; type: string };
type Message = { message_id: string; sender_name: string; content: string; target: string };
type Company = { name: string; description: string; position: { x: number; y: number }; employees: string[]; completed_tasks: number; revenue: number; status: string };
type WorldStats = {
  total_agents: number;
  uptime_seconds: number;
  total_interactions: number;
  total_learnings: number;
};
type WorldState = {
  name: string; width: number; height: number;
  agents: Agent[]; locations: Location[]; active_messages: Message[];
  companies?: Company[];
  stats?: WorldStats;
  tick?: number;
};

const AGENT_COLORS: Record<string, string> = {
  "agent-1": "#8b5cf6",
  "agent-2": "#06b6d4",
  "agent-3": "#f43f5e",
};
const COMPANY_COLORS: Record<string, string> = {
  "Agent-Flow": "#8b5cf6",
  "VirtualCorp": "#06b6d4",
  "Hermes Brain": "#f43f5e",
  "DataSphere": "#22c55e",
};

const WORLD_SIZE = 300;
const BG_COLOR = "#0f0f23";
const GRID_COLOR = "#1a1a3e";
const MAX_INTERACTIONS = 100;
const DELTA_FLASH_MS = 400;

export default function WorldPage() {
  const [state, setState] = useState<WorldState | null>(null);
  const [tick, setTick] = useState(0);
  const [tickerStatus, setTickerStatus] = useState<WorldPulseStatus>("idle");
  const [paceSeconds, setPaceSeconds] = useState(3);
  const [interactionEvents, setInteractionEvents] = useState<InteractionEvent[]>([]);
  const [brains, setBrains] = useState<Record<string, BrainSnapshot>>({});
  const [recentDeltas, setRecentDeltas] = useState<Record<string, { asked?: boolean; answered?: boolean; memories?: boolean; skills?: boolean }>>({});
  const [log, setLog] = useState<string[]>([]);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const addLog = useCallback((msg: string) => {
    setLog((prev) => [...prev.slice(-49), `${new Date().toLocaleTimeString()} ${msg}`]);
  }, []);

  const appendInteraction = useCallback((ev: InteractionEvent) => {
    setInteractionEvents((prev) => {
      const next = [...prev, ev];
      return next.length > MAX_INTERACTIONS ? next.slice(-MAX_INTERACTIONS) : next;
    });
  }, []);

  const flashDelta = useCallback((agentId: string, keys: Array<"asked" | "answered" | "memories" | "skills">) => {
    setRecentDeltas((prev) => {
      const cur = prev[agentId] ?? {};
      const merged = { ...cur };
      for (const k of keys) merged[k] = true;
      return { ...prev, [agentId]: merged };
    });
    setTimeout(() => {
      setRecentDeltas((prev) => {
        if (!prev[agentId]) return prev;
        const cleared = { ...prev };
        delete cleared[agentId];
        return cleared;
      });
    }, DELTA_FLASH_MS);
  }, []);

  // Connect WebSocket
  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.hostname}:8000/world/agentverse/ws`;
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      addLog("🟢 Connected to AgentVerse");
      wsRef.current = socket;
    };

    socket.onmessage = (event) => {
      let data: Record<string, unknown>;
      try { data = JSON.parse(event.data); } catch { return; }
      const type = data.type as string;

      if (type === "world_state" || type === "world_tick") {
        const payload = (data.data ?? data) as WorldState;
        setState(payload);
        setTick(payload.tick ?? 0);
        setBrains(Object.fromEntries((payload.agents ?? []).filter(a => a.brain).map(a => [a.agent_id, a.brain as BrainSnapshot])));
      } else if (type === "world_pulse") {
        const payload = data.state as WorldState;
        setState(payload);
        setTick((data.tick as number) ?? payload.tick ?? 0);
        setBrains(Object.fromEntries((payload.agents ?? []).filter(a => a.brain).map(a => [a.agent_id, a.brain as BrainSnapshot])));
      } else if (type === "world_ticker") {
        const status = data.status as WorldPulseStatus;
        setTickerStatus(status);
        if (typeof data.pace_seconds === "number") setPaceSeconds(data.pace_seconds);
        if (status === "crashed" && data.error) addLog(`💥 Ticker crashed: ${data.error}`);
      } else if (type === "agent_greeted") {
        appendInteraction({
          kind: "greeted", id: data.id as string,
          from: data.from as string, from_name: data.from_name as string,
          to_name: data.to_name as string, text: data.text as string,
          tick: (data.tick as number) ?? 0,
        });
      } else if (type === "agent_asked") {
        const from = data.from as string;
        appendInteraction({
          kind: "asked", id: data.id as string,
          from, from_name: data.from_name as string,
          to_name: data.to_name as string, text: data.text as string,
          tick: (data.tick as number) ?? 0,
        });
        flashDelta(from, ["asked"]);
      } else if (type === "agent_answered") {
        const from = data.from as string;
        appendInteraction({
          kind: "answered", id: data.id as string,
          from, from_name: data.from_name as string,
          to_name: data.to_name as string, text: data.text as string,
          tick: (data.tick as number) ?? 0,
        });
        flashDelta(from, ["answered"]);
      } else if (type === "agent_learned") {
        const agent = data.agent as string;
        const kindOf = data.kind_of as "skill" | "memory" | "knowledge";
        appendInteraction({
          kind: "learned", id: data.id as string,
          agent, agent_name: data.agent_name as string,
          detail: data.detail as string, kind_of: kindOf,
          tick: (data.tick as number) ?? 0,
        });
        flashDelta(agent, [kindOf === "memory" ? "memories" : "skills"]);
      } else if (type === "agent_spoke") {
        const msg = (data as { message: { sender_name: string; content: string } }).message;
        addLog(`💬 ${msg.sender_name}: "${msg.content.slice(0, 60)}..."`);
      } else if (type === "agent_spawned") {
        const a = (data as { agent: { name: string } }).agent;
        addLog(`🆕 Agent ${a.name} joined the world`);
      } else if (type === "agent_removed") {
        addLog(`🚫 Agent ${(data as { agent_id: string }).agent_id} left the world`);
      }
    };

    socket.onclose = () => addLog("🔴 Disconnected");
    socket.onerror = () => addLog("❌ WebSocket error");

    return () => socket.close();
  }, [addLog, appendInteraction, flashDelta]);

  // Canvas drawing (unchanged from the previous version, kept intact)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !state) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const scale = canvas.width / WORLD_SIZE;

    ctx.fillStyle = BG_COLOR;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = GRID_COLOR;
    ctx.lineWidth = 1;
    for (let i = 0; i <= WORLD_SIZE; i += 50) {
      ctx.beginPath(); ctx.moveTo(i * scale, 0); ctx.lineTo(i * scale, canvas.height); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, i * scale); ctx.lineTo(canvas.width, i * scale); ctx.stroke();
    }

    state.locations.forEach((loc) => {
      const x = loc.position.x * scale, y = loc.position.y * scale;
      ctx.fillStyle = "#22c55e40"; ctx.strokeStyle = "#22c55e"; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(x, y, 20 * scale, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      ctx.fillStyle = "#22c55e"; ctx.font = `${11 * scale}px sans-serif`; ctx.textAlign = "center";
      ctx.fillText(loc.name, x, y - 28 * scale);
      const icons: Record<string, string> = { market: "🏪", library: "📚", workshop: "🔧", lab: "🔬", general: "🏛️" };
      ctx.font = `${16 * scale}px sans-serif`;
      ctx.fillText(icons[loc.type] || "📍", x, y + 6 * scale);
    });

    ctx.lineWidth = 1; ctx.setLineDash([3, 3]);
    state.agents.forEach((a) => {
      state.agents.forEach((b) => {
        if (a.agent_id < b.agent_id) {
          const dx = a.position.x - b.position.x, dy = a.position.y - b.position.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.strokeStyle = `${AGENT_COLORS[a.agent_id] || "#8b5cf6"}40`;
            ctx.beginPath();
            ctx.moveTo(a.position.x * scale, a.position.y * scale);
            ctx.lineTo(b.position.x * scale, b.position.y * scale);
            ctx.stroke();
          }
        }
      });
    });
    ctx.setLineDash([]);

    state.agents.forEach((agent) => {
      const x = agent.position.x * scale, y = agent.position.y * scale;
      const color = AGENT_COLORS[agent.agent_id] || "#8b5cf6";
      const radius = 14 * scale;

      const glow = ctx.createRadialGradient(x, y, 0, x, y, radius * 2);
      glow.addColorStop(0, `${color}60`); glow.addColorStop(1, "transparent");
      ctx.fillStyle = glow; ctx.beginPath(); ctx.arc(x, y, radius * 2, 0, Math.PI * 2); ctx.fill();

      ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI * 2); ctx.fill();

      if (agent.energy < 100) {
        ctx.fillStyle = "#333"; ctx.fillRect(x - radius, y + radius + 4, radius * 2, 3);
        ctx.fillStyle = agent.energy > 50 ? "#22c55e" : agent.energy > 25 ? "#f59e0b" : "#ef4444";
        ctx.fillRect(x - radius, y + radius + 4, radius * 2 * (agent.energy / 100), 3);
      }

      ctx.fillStyle = "#fff"; ctx.font = `bold ${11 * scale}px sans-serif`; ctx.textAlign = "center";
      ctx.fillText(agent.name, x, y - radius - 8 * scale);

      const stateDots: Record<string, string> = { idle: "#6b7280", moving: "#3b82f6", working: "#f59e0b", talking: "#22c55e", listening: "#8b5cf6", sleeping: "#9ca3af" };
      ctx.fillStyle = stateDots[agent.state] || "#6b7280";
      ctx.beginPath(); ctx.arc(x + radius + 4 * scale, y - radius + 4 * scale, 3 * scale, 0, Math.PI * 2); ctx.fill();
    });

    state.active_messages.forEach((msg) => {
      const sender = state.agents.find((a) => a.name === msg.sender_name);
      if (!sender) return;
      const x = sender.position.x * scale, y = sender.position.y * scale - 25 * scale;
      ctx.fillStyle = "#ffffff20"; ctx.strokeStyle = "#ffffff40"; ctx.lineWidth = 1;
      const tw = ctx.measureText(msg.content.slice(0, 30)).width;
      const bw = Math.max(60, tw + 20), bh = 24, bx = x - bw / 2, by = y - bh - 8;
      ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, 6); ctx.fill(); ctx.stroke();
      ctx.fillStyle = "#fff"; ctx.font = `${10 * scale}px sans-serif`; ctx.textAlign = "center";
      ctx.fillText(msg.content.slice(0, 30), x, y - bh + bh / 2 + 3.5 * scale);
    });
  }, [state]);

  const sendCommand = useCallback((action: string, data: Record<string, unknown> = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action, ...data }));
    }
  }, []);

  const startLiving = () => sendCommand("start", { pace_seconds: paceSeconds });
  const pauseLiving = () => sendCommand("pause");
  const onPaceChange = (v: number) => {
    setPaceSeconds(v);
    sendCommand("set_pace", { pace_seconds: v });
  };
  const burst60 = () => sendCommand("tick", { count: 60 });

  const agentList = useMemo(
    () => (state?.agents ?? []).map((a) => ({ agent_id: a.agent_id, name: a.name })),
    [state?.agents],
  );

  return (
    <div className="p-4" dir="ltr">
      <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-white">🌍 AgentVerse</h1>
          <p className="text-zinc-400 text-xs">
            {state ? `${state.agents.length} agents · ${state.locations.length} locations` : "Connecting..."}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {tickerStatus === "running" ? (
            <button onClick={pauseLiving}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-sm font-medium transition-colors">
              ⏸ Pause
            </button>
          ) : (
            <button onClick={startLiving}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition-colors">
              ▶ Start Living
            </button>
          )}
          <label className="flex items-center gap-2 text-xs text-zinc-400 bg-zinc-900/60 border border-zinc-800 rounded-lg px-2 py-1.5">
            <span>pace</span>
            <input
              type="range" min={1} max={10} step={0.5}
              value={paceSeconds}
              onChange={(e) => onPaceChange(parseFloat(e.target.value))}
              className="w-28"
            />
            <span className="tabular-nums w-10 text-right text-white">{paceSeconds.toFixed(1)}s</span>
          </label>
          <button onClick={burst60}
            className="px-3 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm transition-colors">
            ▶️ Burst 60
          </button>
          <button onClick={() => sendCommand("tick", { count: 1 })}
            className="px-3 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm transition-colors">
            ⏭️ Tick
          </button>
        </div>
      </div>

      <div className="grid grid-cols-[660px,minmax(0,1fr)] gap-4">
        {/* Left: canvas */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
          <canvas ref={canvasRef} width={660} height={660} className="block" />
        </div>

        {/* Right: pulse + interactions + learning cards */}
        <div className="flex flex-col gap-3 min-w-0">
          <WorldPulse
            tick={tick}
            status={tickerStatus}
            paceSeconds={paceSeconds}
            uptimeSeconds={state?.stats?.uptime_seconds ?? 0}
            agentCount={state?.stats?.total_agents ?? 0}
            totalInteractions={state?.stats?.total_interactions ?? 0}
            totalLearnings={state?.stats?.total_learnings ?? 0}
          />

          <div className="h-72">
            <InteractionStream events={interactionEvents} agentColors={AGENT_COLORS} />
          </div>

          <AgentLearningCards
            agents={agentList}
            brains={brains}
            recentDeltas={recentDeltas}
            agentColors={AGENT_COLORS}
          />

          {/* Companies + event log (kept for parity with old page) */}
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-3">
            <h2 className="text-white font-semibold text-sm mb-2">🏢 Companies</h2>
            <div className="space-y-1">
              {state?.companies?.map((c) => (
                <div key={c.name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COMPANY_COLORS[c.name] || "#8b5cf6" }} />
                    <span className="text-white">{c.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${c.status === "busy" ? "bg-emerald-500/20 text-emerald-400" : "bg-zinc-700 text-zinc-400"}`}>
                      {c.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-zinc-500">
                    <span>👥{c.employees.length}</span>
                    <span>✅{c.completed_tasks}</span>
                    <span>💰${c.revenue.toFixed(1)}</span>
                  </div>
                </div>
              ))}
              {(!state?.companies || state.companies.length === 0) && (
                <p className="text-zinc-600 text-xs">No companies yet</p>
              )}
            </div>
          </div>

          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-3">
            <h2 className="text-white font-semibold text-sm mb-2">📜 Event Log</h2>
            <div className="h-40 overflow-y-auto space-y-0.5 text-xs font-mono">
              {log.length === 0 ? (
                <p className="text-zinc-600">Waiting for events...</p>
              ) : (
                log.map((entry, i) => <p key={i} className="text-zinc-400">{entry}</p>)
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Typecheck**

```powershell
cd e:\ai_projects\Agent-Flow\frontend
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 3: Smoke test in browser**

Restart backend + frontend if not already running:
```powershell
uv run python e:\ai_projects\Agent-Flow\production.py > backend.stdout.log 2> backend.stderr.log &
cd e:\ai_projects\Agent-Flow\frontend
npm run dev > ..\frontend.stdout.log 2> ..\frontend.stderr.log &
```

Open http://localhost:3000/world.

Verify manually:
1. Header shows ▶ Start Living, pace slider (default 3.0s), ⏸ Pause (hidden until running), Burst 60, ⏭ Tick.
2. Right side shows WorldPulse strip (● idle · tick 0 · pace 3.0s · ...), an empty InteractionStream with "Waiting for the world to come alive...", and three AgentLearningCards.
3. Click ▶ Start Living → within ~3s pulse dot goes green, tick counter climbs, interactions appear, some cards flash yellow.
4. Move pace slider to 1.0s → cadence accelerates. Move to 10.0s → cadence slows.
5. Click ⏸ Pause → pulse dot goes gray, no new interactions. Refresh — page reconnects, world_ticker shows paused.
6. Click Burst 60 → interactions still appear in the stream (backward compat).

- [ ] **Step 4: Full backend test suite one more time**

```powershell
uv run python -W error::ResourceWarning -m unittest discover -s tests -v
```
Expected: 32+ OK.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/world/page.tsx
git commit -m "feat(world/ui): autonomous /world with interaction & learning viz

Rewrites the /world page around a two-column layout: 2D canvas map on
the left, WorldPulse strip + InteractionStream + AgentLearningCards on
the right. Header controls: Start Living / Pause / pace slider / Burst
60 / single Tick. Ingests the new typed WS event kinds and manages
counter-flash deltas from the client side."
```

- [ ] **Step 6: Final acceptance check against the spec**

Re-read `docs/superpowers/specs/2026-07-23-living-verse-design.md` "Acceptance criteria" — walk through each of criteria 1-6 in the browser and terminal, mark them ✅ in the PR description.

---

## Self-review

**1. Spec coverage** — walking the spec section-by-section:

- Design choices table → all reflected. Layout (Task 10), autonomous ticker (Task 4), templated Q&A (Task 1), reuse WS (Task 3/5), no persistence (nothing in this plan touches SQLite), backwards compat Burst 60 (Task 3 + acceptance check).
- Non-goals → respected. No new deps, routes, or DB migrations in any task.
- Architecture diagram → Tasks 1-6 implement the backend side; Tasks 7-10 the frontend side.
- Backend components (engine.py, ticker.py, ws.py, api.py, production.py) → Tasks 1, 2, 4, 3, 5, 6 respectively.
- Frontend components (WorldPulse, InteractionStream, AgentLearningCards, page.tsx) → Tasks 7, 8, 9, 10.
- WebSocket protocol → Task 3 defines the frame shapes; Task 5 wires the commands; Task 10 consumes.
- Data model extensions (brain snapshot in `as_dict`, `total_interactions`/`total_learnings` in stats) → Task 2.
- Error handling & edge cases → Task 4 crash-3× rule, Task 5 clamping, Task 6 shutdown handler.
- Testing → Task 1 has 4 tests, Task 2 has 2, Task 3 has 2, Task 4 has 3, Task 5 has 3. Total: 14 new tests. Spec asked for 3+ test files (test_engine_delta, test_ticker, test_ws_commands); this plan consolidates into `test_living_verse.py` with 5 test classes — same coverage, one file (kept DRY; the file is not so large that splitting improves anything).
- Acceptance criteria (6 items) → all verifiable at Task 10 Step 3.
- Rollout & Future work → informational; no plan changes needed.

**2. Placeholder scan** — Grepped mentally for "TBD", "TODO", "implement later". None present. Every step has full code.

**3. Type consistency** —
- `InteractionDelta` fields match across engine.py definition, ws.py `broadcast_delta`, and ticker tests.
- WS frame shapes in `broadcast_delta` (Task 3) match the frontend handlers in `page.tsx` (Task 10): `agent_greeted` has `from`, `from_name`, `to`, `to_name`, `text`, `tick`, `id` — verified.
- `BrainSnapshot` fields in `AgentLearningCards.tsx` match what `WorldAgent.as_dict()["brain"]` produces in Task 2: role, personality {curiosity, talkativity, friendliness}, skills[], memory_count, knowledge_recent[], questions_asked, questions_answered — all present.
- `world_ticker` status values: server emits `"running" | "paused" | "crashed"`; the `WorldPulseStatus` type also allows `"idle"` for the connect-time case where no ticker exists — that's fine because `idle` is emitted by `api.py` (Task 5), not by the ticker itself.

No fixes needed.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-23-living-verse.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
