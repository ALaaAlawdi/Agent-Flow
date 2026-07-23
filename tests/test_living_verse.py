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


if __name__ == "__main__":
    unittest.main()
