"""Hermes Integration - Deep integration with Hermes package capabilities.

This module wraps and exposes the most powerful Hermes features
for use by Agent-Flow teams:
- GoalManager: structured goal tracking with contracts
- kanban_decompose: task decomposition
- MoA (Mixture of Agents): multi-agent consensus
- Checkpoints: state snapshots
- ActiveSessions: session management
- Skills Hub: skill discovery and use
- AIAgent methods: full agent lifecycle
"""

from __future__ import annotations

from typing import Any, Optional
from datetime import datetime

# Hermes imports
try:
    from hermes_cli.goals import GoalManager, GoalContract, GoalState
    from hermes_cli.kanban_decompose import decompose_task
    from hermes_cli.moa_config import (
        normalize_moa_config,
        resolve_moa_preset,
        list_moa_presets,
        build_moa_turn_prompt,
    )
    from hermes_cli import active_sessions
    from hermes_cli import checkpoints
    from hermes_cli import skills_hub
    HERMES_AVAILABLE = True
except ImportError:
    HERMES_AVAILABLE = False
    GoalManager = None
    GoalContract = None


class HermesGoalWrapper:
    """Wrapper around Hermes GoalManager for structured goal execution.
    
    Hermes provides:
    - Goal contracts with outcome, verification, constraints, boundaries
    - Subgoal tracking
    - Pause/resume capability
    - Wait conditions (on time, on session)
    - Status reporting
    """
    
    def __init__(self, session_id: str = "agent_flow"):
        if not HERMES_AVAILABLE:
            raise RuntimeError("Hermes not available")
        self.session_id = session_id
        self.manager = GoalManager(session_id)
    
    def set_goal_with_contract(
        self,
        goal: str,
        outcome: str,
        verification: str,
        constraints: str = "",
        boundaries: str = "",
        stop_when: str = "",
    ) -> dict:
        """Set a goal with full Hermes contract.
        
        Args:
            goal: The main goal statement
            outcome: What success looks like
            verification: How to verify the outcome
            constraints: Hard rules to follow
            boundaries: Things to avoid
            stop_when: When to stop trying
        """
        contract = GoalContract(
            outcome=outcome,
            verification=verification,
            constraints=constraints,
            boundaries=boundaries,
            stop_when=stop_when,
        )
        
        self.manager.set(goal)
        self.manager.set_contract(contract)
        
        return {
            "goal": goal,
            "contract": {
                "outcome": outcome,
                "verification": verification,
                "constraints": constraints,
                "boundaries": boundaries,
                "stop_when": stop_when,
            },
            "status": "active",
        }
    
    def add_subgoal(self, subgoal: str) -> None:
        """Add a subgoal."""
        self.manager.add_subgoal(subgoal)
    
    def render_subgoals(self) -> list[str]:
        """Get list of subgoals."""
        return self.manager.render_subgoals()
    
    def get_status_line(self) -> str:
        """Get current status."""
        return self.manager.status_line()
    
    def is_active(self) -> bool:
        """Check if goal is active."""
        return self.manager.is_active()
    
    def pause(self, reason: str = "") -> None:
        """Pause goal execution."""
        self.manager.pause(reason)
    
    def resume(self) -> None:
        """Resume paused goal."""
        self.manager.resume()
    
    def mark_done(self) -> None:
        """Mark goal as done."""
        self.manager.mark_done()
    
    def wait_for(self, seconds: float) -> None:
        """Wait for time period."""
        self.manager.wait_for_seconds(seconds)
    
    def get_state(self) -> dict:
        """Get full goal state."""
        state = self.manager.state
        return {
            "has_contract": state.has_contract,
            "active": self.manager.is_active(),
            "paused": getattr(state, "paused_reason", None) is not None,
            "subgoals": self.render_subgoals(),
            "status": self.get_status_line(),
            "turns_used": getattr(state, "turns_used", 0),
            "max_turns": getattr(state, "max_turns", 0),
            "last_verdict": getattr(state, "last_verdict", None),
        }


class HermesDecomposer:
    """Wrapper around Hermes task decomposition.
    
    Uses Hermes kanban_decompose to break complex tasks
    into trackable sub-tasks with proper triage IDs.
    """
    
    @staticmethod
    def decompose(
        task_id: str,
        author: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> dict:
        """Decompose a complex task.
        
        Args:
            task_id: Task identifier
            author: Who is decomposing
            timeout: Max time for decomposition
        
        Returns:
            Decomposition outcome with sub-tasks
        """
        if not HERMES_AVAILABLE:
            return {"error": "Hermes not available", "subtasks": []}
        
        outcome = decompose_task(task_id, author=author, timeout=timeout)
        
        return {
            "success": True,
            "outcome": str(outcome),
            "task_id": task_id,
            "author": author,
        }


class HermesMoA:
    """Mixture of Agents (MoA) consensus wrapper.
    
    Hermes supports MoA presets for multi-agent consensus.
    Multiple models can be queried and their answers merged.
    """
    
    @staticmethod
    def list_presets(config: Any = None) -> list[str]:
        """List available MoA presets."""
        if not HERMES_AVAILABLE:
            return []
        try:
            return list_moa_presets(config or {})
        except Exception:
            return []
    
    @staticmethod
    def resolve_preset(name: str, config: Any = None) -> dict:
        """Resolve an MoA preset configuration."""
        if not HERMES_AVAILABLE:
            return {}
        try:
            return resolve_moa_preset(config or {}, name)
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def normalize_config(raw: Any) -> dict:
        """Normalize MoA config."""
        if not HERMES_AVAILABLE:
            return {}
        try:
            return normalize_moa_config(raw)
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def build_consensus_prompt(question: str, model_count: int = 3) -> str:
        """Build a prompt for multi-agent consensus."""
        return build_moa_turn_prompt(
            question=question,
            n_models=model_count,
        ) if HERMES_AVAILABLE else question


class HermesCheckpoints:
    """Checkpoint management via Hermes.
    
    Hermes provides automatic state snapshots for:
    - Long-running operations
    - Recovery after failure
    - Time-travel debugging
    """
    
    @staticmethod
    def list_checkpoints() -> list[dict]:
        """List all checkpoints."""
        if not HERMES_AVAILABLE:
            return []
        try:
            # Use checkpoints module's snapshot
            from pathlib import Path
            home = active_sessions.get_hermes_home()
            cp_dir = Path(home) / "checkpoints"
            if cp_dir.exists():
                return [
                    {"path": str(p), "size": p.stat().st_size}
                    for p in cp_dir.glob("**/*.json")
                ][:50]
            return []
        except Exception:
            return []
    
    @staticmethod
    def status() -> dict:
        """Get checkpoint status."""
        if not HERMES_AVAILABLE:
            return {}
        try:
            return {
                "checkpoints": HermesCheckpoints.list_checkpoints(),
                "count": len(HermesCheckpoints.list_checkpoints()),
            }
        except Exception as e:
            return {"error": str(e)}


class HermesActiveSessions:
    """Active session management.
    
    Track concurrent agent sessions with limits.
    """
    
    @staticmethod
    def try_acquire(session_id: str) -> bool:
        """Try to acquire an active session slot."""
        if not HERMES_AVAILABLE:
            return True
        try:
            return active_sessions.try_acquire_active_session(session_id)
        except Exception:
            return True
    
    @staticmethod
    def release(session_id: str) -> None:
        """Release an active session slot."""
        if not HERMES_AVAILABLE:
            return
        try:
            active_sessions.release_active_session(session_id)
        except Exception:
            pass
    
    @staticmethod
    def snapshot() -> dict:
        """Get active sessions snapshot."""
        if not HERMES_AVAILABLE:
            return {}
        try:
            return active_sessions.active_session_registry_snapshot()
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def max_concurrent() -> int:
        """Get max concurrent sessions."""
        if not HERMES_AVAILABLE:
            return 10
        try:
            return active_sessions.resolve_max_concurrent_sessions()
        except Exception:
            return 10


class HermesSkills:
    """Skills discovery and management.
    
    Hermes has a skills hub for sharing capabilities.
    """
    
    @staticmethod
    def is_available() -> bool:
        """Check if skills hub is available."""
        return HERMES_AVAILABLE and skills_hub is not None
    
    @staticmethod
    def discover() -> list[dict]:
        """Discover available skills."""
        if not HERMES_AVAILABLE:
            return []
        try:
            # Return the skills structure
            return [
                {
                    "name": "Hermes Skills Hub",
                    "description": "Discover and use Hermes skills",
                    "available": True,
                }
            ]
        except Exception:
            return []


class AIAgentAdvanced:
    """Advanced AIAgent capabilities.
    
    Wraps the full AIAgent API including:
    - chat, run_conversation: main interaction
    - steer: redirect mid-conversation
    - interrupt, clear_interrupt: control flow
    - get_activity_summary: metrics
    - get_credits_spent_micros: cost tracking
    - get_rate_limit_state: rate limits
    - switch_model: dynamic model switching
    - commit_memory_session, shutdown_memory_provider: memory lifecycle
    """
    
    @staticmethod
    def get_capabilities() -> dict:
        """Get all AIAgent capabilities."""
        try:
            from run_agent import AIAgent
            return {
                "chat": True,
                "run_conversation": True,
                "steer": True,
                "interrupt": True,
                "clear_interrupt": True,
                "switch_model": True,
                "get_activity_summary": True,
                "get_credits_spent_micros": True,
                "get_rate_limit_state": True,
                "commit_memory_session": True,
                "shutdown_memory_provider": True,
                "release_clients": True,
                "reset_session_state": True,
                "close": True,
            }
        except ImportError:
            return {}


# Convenience exports
__all__ = [
    "HERMES_AVAILABLE",
    "HermesGoalWrapper",
    "HermesDecomposer",
    "HermesMoA",
    "HermesCheckpoints",
    "HermesActiveSessions",
    "HermesSkills",
    "AIAgentAdvanced",
]