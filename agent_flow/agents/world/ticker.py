"""AutonomousTicker — background asyncio task that ticks a WorldEngine.

Broadcasts a world_ticker WS frame on every status change (start / pause /
set_pace / crash). Interactions each tick go through broadcast_delta.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from agent_flow.agents.world.engine import InteractionDelta, WorldEngine
from agent_flow.agents.world.ws import WorldWebSocketManager

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
        self._pace = float(pace_seconds)
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
                await self._broadcast_delta(delta)
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

    async def _broadcast_delta(self, delta: InteractionDelta) -> None:
        """Broadcast each interaction event plus a world_pulse rollup via self._ws."""
        wn = self._world_name
        for i, m in enumerate(delta.moves):
            await self._ws.broadcast(wn, {
                "type": "agent_moved",
                "id": f"mv_{delta.tick:05d}_{i}",
                **m,
                "tick": delta.tick,
            })
        for i, g in enumerate(delta.greetings):
            await self._ws.broadcast(wn, {
                "type": "agent_greeted",
                "id": f"grt_{delta.tick:05d}_{i}",
                **g,
                "tick": delta.tick,
            })
        for i, a in enumerate(delta.asks):
            await self._ws.broadcast(wn, {
                "type": "agent_asked",
                "id": f"ask_{delta.tick:05d}_{i}",
                **a,
                "tick": delta.tick,
            })
        for i, a in enumerate(delta.answers):
            await self._ws.broadcast(wn, {
                "type": "agent_answered",
                "id": f"ans_{delta.tick:05d}_{i}",
                **a,
                "tick": delta.tick,
            })
        for i, L in enumerate(delta.learnings):
            await self._ws.broadcast(wn, {
                "type": "agent_learned",
                "id": f"lrn_{delta.tick:05d}_{i}",
                **L,
                "tick": delta.tick,
            })
        state = self._world.get_state()
        await self._ws.broadcast(wn, {
            "type": "world_pulse",
            "tick": delta.tick,
            "state": state,
        })

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
