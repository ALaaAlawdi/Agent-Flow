"""Event System - Track all team activities."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from enum import Enum

from hermes_cli.profiles import get_profile_dir
class EventType(str, Enum):
    """Types of events tracked."""
    # Team events
    TEAM_CREATED = "team_created"
    TEAM_GOAL_SET = "team_goal_set"
    
    # Agent events
    AGENT_ADDED = "agent_added"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    
    # Communication events
    AGENT_MESSAGE_SENT = "agent_message_sent"
    AGENT_MESSAGE_RECEIVED = "agent_message_received"
    
    # Task events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    # Knowledge events
    KNOWLEDGE_ADDED = "knowledge_added"
    KNOWLEDGE_ACCESSED = "knowledge_accessed"
    
    # Learning events
    FEEDBACK_ADDED = "feedback_added"
    IMPROVEMENT_SUGGESTED = "improvement_suggested"
    
    # Workflow events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_STEP_STARTED = "workflow_step_started"
    WORKFLOW_STEP_COMPLETED = "workflow_step_completed"
    WORKFLOW_STEP_FAILED = "workflow_step_failed"


class Event:
    """An event in the system."""
    
    def __init__(
        self,
        event_type: EventType,
        team_name: str,
        data: dict[str, Any],
        agent_id: Optional[str] = None,
    ):
        self.id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{EventType}"
        self.event_type = event_type
        self.team_name = team_name
        self.agent_id = agent_id
        self.data = data
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            "team_name": self.team_name,
            "agent_id": self.agent_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        event = cls(
            event_type=EventType(data["event_type"]),
            team_name=data["team_name"],
            data=data.get("data", {}),
            agent_id=data.get("agent_id"),
        )
        event.id = data.get("id", event.id)
        event.timestamp = data.get("timestamp", event.timestamp)
        return event


class EventStore:
    """Store and retrieve events."""
    
    def __init__(self, team_name: str):
        self.team_name = team_name
        self.profile_dir = get_profile_dir(team_name)
        self.events_dir = self.profile_dir / "events"
        self.events_dir.mkdir(parents=True, exist_ok=True)
        
        self._events: list[Event] = []
        self._load_events()
    
    def _load_events(self):
        """Load events from disk."""
        events_file = self.events_dir / "events.json"
        if events_file.exists():
            try:
                data = json.loads(events_file.read_text())
                self._events = [Event.from_dict(e) for e in data]
            except Exception:
                self._events = []
    
    def _save_events(self):
        """Save events to disk."""
        events_file = self.events_dir / "events.json"
        data = [e.to_dict() for e in self._events]
        # Keep last 1000 events
        data = data[-1000:]
        events_file.write_text(json.dumps(data, indent=2))
    
    def emit(
        self,
        event_type: EventType,
        data: dict[str, Any],
        agent_id: Optional[str] = None,
    ):
        """Emit an event."""
        event = Event(event_type, self.team_name, data, agent_id)
        self._events.append(event)
        self._save_events()
        return event
    
    def get_events(
        self,
        event_type: Optional[EventType] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[Event]:
        """Get events with optional filters."""
        events = self._events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]
        
        return events[-limit:]
    
    def get_team_timeline(self, limit: int = 50) -> list[dict]:
        """Get timeline of all events."""
        events = self._events[-limit:]
        return [e.to_dict() for e in events]
    
    def get_agent_history(self, agent_id: str, limit: int = 50) -> list[dict]:
        """Get history for a specific agent."""
        events = [e for e in self._events if e.agent_id == agent_id][-limit:]
        return [e.to_dict() for e in events]
    
    def clear(self):
        """Clear all events."""
        self._events = []
        self._save_events()
