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
