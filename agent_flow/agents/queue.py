"""Task Queue - Manage tasks for agent teams."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from enum import Enum

from hermes_cli.profiles import get_profile_dir


class TaskStatus(str, Enum):
    """Task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    """Task priority (higher = more important)."""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    URGENT = 20


class Task:
    """A task in the queue."""
    
    def __init__(
        self,
        task_id: str,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        assigned_agent: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        self.id = task_id
        self.description = description
        self.priority = priority
        self.assigned_agent = assigned_agent
        self.metadata = metadata or {}
        
        self.status = TaskStatus.PENDING
        self.result: Optional[str] = None
        self.error: Optional[str] = None
        
        self.created_at = datetime.now().isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "priority": self.priority.value,
            "assigned_agent": self.assigned_agent,
            "metadata": self.metadata,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        task = cls(
            task_id=data["id"],
            description=data["description"],
            priority=TaskPriority(data["priority"]),
            assigned_agent=data.get("assigned_agent"),
            metadata=data.get("metadata", {}),
        )
        task.status = TaskStatus(data.get("status", "pending"))
        task.result = data.get("result")
        task.error = data.get("error")
        task.created_at = data.get("created_at", task.created_at)
        task.started_at = data.get("started_at")
        task.completed_at = data.get("completed_at")
        return task
    
    def start(self, agent_id: str):
        """Start task execution."""
        self.status = TaskStatus.RUNNING
        self.assigned_agent = agent_id
        self.started_at = datetime.now().isoformat()
    
    def complete(self, result: str):
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now().isoformat()
    
    def fail(self, error: str):
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now().isoformat()
    
    def cancel(self):
        """Cancel task."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now().isoformat()


class TaskQueue:
    """Queue for managing tasks."""
    
    def __init__(self, team_name: str, queue_name: str = "default"):
        self.team_name = team_name
        self.queue_name = queue_name
        self.profile_dir = get_profile_dir(team_name)
        self.queue_dir = self.profile_dir / "queues" / queue_name
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        
        self._tasks: dict[str, Task] = {}
        self._load_tasks()
    
    def _load_tasks(self):
        """Load tasks from disk."""
        tasks_file = self.queue_dir / "tasks.json"
        if tasks_file.exists():
            try:
                data = json.loads(tasks_file.read_text())
                self._tasks = {t["id"]: Task.from_dict(t) for t in data}
            except Exception:
                self._tasks = {}
    
    def _save_tasks(self):
        """Save tasks to disk."""
        tasks_file = self.queue_dir / "tasks.json"
        data = [t.to_dict() for t in self._tasks.values()]
        tasks_file.write_text(json.dumps(data, indent=2))
    
    def add(
        self,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        task_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Task:
        """Add a task to the queue."""
        if task_id is None:
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = Task(task_id, description, priority, metadata=metadata)
        self._tasks[task_id] = task
        self._save_tasks()
        return task
    
    def get(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    def get_next(self, agent_id: Optional[str] = None) -> Optional[Task]:
        """Get next task to execute."""
        # Filter pending tasks
        pending = [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]
        
        if not pending:
            return None
        
        # Filter by agent if specified
        if agent_id:
            # Prefer tasks assigned to this agent
            assigned = [t for t in pending if t.assigned_agent == agent_id]
            if assigned:
                # Return highest priority
                return max(assigned, key=lambda t: t.priority)
        
        # Return highest priority
        return max(pending, key=lambda t: t.priority)
    
    def get_by_status(self, status: TaskStatus) -> list[Task]:
        """Get tasks by status."""
        return [t for t in self._tasks.values() if t.status == status]
    
    def get_by_agent(self, agent_id: str) -> list[Task]:
        """Get tasks assigned to an agent."""
        return [t for t in self._tasks.values() if t.assigned_agent == agent_id]
    
    def get_all(self) -> list[Task]:
        """Get all tasks."""
        return list(self._tasks.values())
    
    def update(self, task: Task):
        """Update a task."""
        self._tasks[task.id] = task
        self._save_tasks()
    
    def remove(self, task_id: str) -> bool:
        """Remove a task."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            self._save_tasks()
            return True
        return False
    
    def clear_completed(self):
        """Clear completed tasks."""
        self._tasks = {
            k: v for k, v in self._tasks.items() 
            if v.status != TaskStatus.COMPLETED
        }
        self._save_tasks()
    
    def get_stats(self) -> dict:
        """Get queue statistics."""
        tasks = list(self._tasks.values())
        return {
            "total": len(tasks),
            "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "running": len([t for t in tasks if t.status == TaskStatus.RUNNING]),
            "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in tasks if t.status == TaskStatus.FAILED]),
        }
