"""Tests for the Living Verse — autonomous /world with interaction & learning viz."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from agent_flow.agents.world import ws as ws_module
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

    def test_tick_does_not_double_greet_same_pair(self):
        """When A and B are mutually within 20 units, only one greeting fires per pair."""
        async def run():
            world = WorldEngine(name="test", width=300, height=300)
            _place_two_agents_close(world)
            delta = await world.tick()
            return delta

        delta = asyncio.run(run())
        # At most one greeting event should have been emitted for this pair.
        self.assertLessEqual(len(delta.greetings), 1)

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


class AutonomousTickerTests(unittest.TestCase):
    def test_ticker_start_stop_publishes_status(self):
        from agent_flow.agents.world.ticker import AutonomousTicker

        world = WorldEngine(name="tick-test", width=300, height=300)
        _place_two_agents_close(world)
        fake_mgr = MagicMock()
        fake_mgr.broadcast = AsyncMock()

        async def run():
            ticker = AutonomousTicker("tick-test", world, fake_mgr, pace_seconds=1.0)
            await ticker.start()
            await asyncio.sleep(1.5)   # let at least one tick happen at 1s pace
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
            ticker = AutonomousTicker("crash-test", broken_world, fake_mgr, pace_seconds=1.0)
            await ticker.start()
            # Wait long enough for 3 failures + backoff: 3 ticks + 2*pace backoffs ~= 5s; 6s is safe.
            await asyncio.sleep(6.0)
            return ticker

        ticker = asyncio.run(run())
        self.assertFalse(ticker.is_running())

        crashed_frames = [
            c.args[1] for c in fake_mgr.broadcast.await_args_list
            if c.args[1].get("type") == "world_ticker" and c.args[1].get("status") == "crashed"
        ]
        self.assertTrue(len(crashed_frames) >= 1)
        self.assertIn("error", crashed_frames[0])

    def test_ticker_world_pulse_includes_companies(self):
        from agent_flow.agents.world.ticker import AutonomousTicker

        world = WorldEngine(name="companies-test", width=300, height=300)
        _place_two_agents_close(world)
        fake_mgr = MagicMock()
        fake_mgr.broadcast = AsyncMock()

        async def run():
            ticker = AutonomousTicker("companies-test", world, fake_mgr, pace_seconds=1.0)
            await ticker.start()
            await asyncio.sleep(1.5)
            await ticker.stop()
            return fake_mgr

        mgr = asyncio.run(run())
        pulse_frames = [
            c.args[1] for c in mgr.broadcast.await_args_list
            if c.args[1].get("type") == "world_pulse"
        ]
        self.assertTrue(len(pulse_frames) >= 1)
        # Every world_pulse payload's state MUST include a companies key (may be empty list).
        for p in pulse_frames:
            self.assertIn("companies", p["state"])


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


if __name__ == "__main__":
    unittest.main()
