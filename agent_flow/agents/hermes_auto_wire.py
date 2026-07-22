"""
Agent-Flow × Hermes — Complete Integration Layer.

Every agent action automatically triggers:
- Session logging (sessions)
- Memory storage (memory)
- Insights tracking (insights)
- Learning events (learning/journey)
- Memory graph building (memory-graph)
- Kanban task updates (kanban)

No manual wiring needed. It just works.
"""

from __future__ import annotations

import json, time
from typing import Optional

from agent_flow.agents.hermes_cli_api import (
    sessions_store, memory_items, insights_events,
    learning_events, memory_graph, kanban_tasks, KanbanTask,
    curator_skills
)

_session_counter = 0
_task_counter = 0

# ═══════════════════════════════════════════
# AUTO-WIRING — happens on every agent event
# ═══════════════════════════════════════════

def on_agent_created(agent_id: str, name: str, role: str):
    """Called when ANY agent is created in Agent-Flow."""
    global _session_counter
    
    # 1. Session
    _session_counter += 1
    sessions_store.append({
        "id": f"auto-{agent_id}-{int(time.time())}",
        "name": f"{name} ({role})",
        "agent_id": agent_id,
        "messages": [],
        "created_at": time.time(),
        "updated_at": time.time(),
    })
    
    # 2. Memory
    if agent_id not in memory_items:
        memory_items[agent_id] = []
    memory_items[agent_id].append({
        "key": "creation",
        "value": f"Created as {role}",
        "timestamp": time.time(),
    })
    
    # 3. Insights
    insights_events.append({
        "type": "agent_created",
        "data": json.dumps({"id": agent_id, "name": name, "role": role}),
        "timestamp": time.time(),
    })
    
    # 4. Learning
    learning_events.append({
        "event": f"Agent {name} ({role}) joined the world",
        "agent_id": agent_id,
        "timestamp": time.time(),
    })
    
    # 5. Memory Graph — connect to all existing agents
    for existing_id in memory_graph:
        if existing_id != agent_id:
            memory_graph[existing_id].append(agent_id)
    memory_graph[agent_id] = [aid for aid in memory_graph if aid != agent_id]


def on_agent_speak(speaker_id: str, speaker_name: str, message: str, target_id: str = ""):
    """Called when any agent speaks to another."""
    
    # 1. Session message
    for s in sessions_store:
        if s["agent_id"] == speaker_id:
            s["messages"].append({
                "role": speaker_name,
                "content": message,
                "timestamp": time.time(),
            })
            s["updated_at"] = time.time()
            break
    
    # 2. Memory — store interaction
    if speaker_id in memory_items:
        memory_items[speaker_id].append({
            "key": f"spoke_to_{target_id}" if target_id else "broadcast",
            "value": message[:100],
            "timestamp": time.time(),
        })
    
    # 3. Insights
    insights_events.append({
        "type": "agent_speak",
        "data": json.dumps({"from": speaker_id, "to": target_id, "len": len(message)}),
        "timestamp": time.time(),
    })
    
    # 4. Learning
    learning_events.append({
        "event": f"{speaker_name}: {message[:80]}",
        "agent_id": speaker_id,
        "timestamp": time.time(),
    })


def on_task_created(task_title: str, assignee: str = ""):
    """Called when a new task is created."""
    global _task_counter
    _task_counter += 1
    
    task = KanbanTask(
        id=f"auto-task-{_task_counter}",
        title=task_title,
        assignee=assignee,
        status="todo",
        created_at=time.time(),
    )
    kanban_tasks[task.id] = task
    
    insights_events.append({
        "type": "task_created",
        "data": json.dumps({"title": task_title, "assignee": assignee}),
        "timestamp": time.time(),
    })
    
    return task.id


def on_task_completed(task_id: str):
    """Called when a task is completed."""
    if task_id in kanban_tasks:
        kanban_tasks[task_id].status = "done"
    
    insights_events.append({
        "type": "task_completed",
        "data": task_id,
        "timestamp": time.time(),
    })


def on_agent_learned(agent_id: str, skill: str, confidence: float):
    """Called when an agent learns/improves a skill."""
    
    # 1. Memory
    if agent_id in memory_items:
        memory_items[agent_id].append({
            "key": f"skill_{skill}",
            "value": f"Confidence: {confidence:.0%}",
            "timestamp": time.time(),
        })
    
    # 2. Curator
    curator_skills[skill] = {
        "name": skill,
        "status": "active",
        "confidence": confidence,
        "updated_at": time.time(),
    }
    
    # 3. Learning
    learning_events.append({
        "event": f"{agent_id} improved {skill} to {confidence:.0%}",
        "agent_id": agent_id,
        "timestamp": time.time(),
    })
    
    # 4. Insights
    insights_events.append({
        "type": "skill_improved",
        "data": json.dumps({"agent": agent_id, "skill": skill, "confidence": confidence}),
        "timestamp": time.time(),
    })


def on_agent_mistake(agent_id: str, action: str, error: str, lesson: str):
    """Called when an agent makes a mistake and learns from it."""
    
    # 1. Memory — store the lesson
    if agent_id in memory_items:
        memory_items[agent_id].append({
            "key": "mistake_lesson",
            "value": lesson,
            "timestamp": time.time(),
        })
    
    # 2. Learning
    learning_events.append({
        "event": f"{agent_id}: ❌ {action} → learned: {lesson}",
        "agent_id": agent_id,
        "timestamp": time.time(),
    })
    
    # 3. Insights
    insights_events.append({
        "type": "mistake",
        "data": json.dumps({"agent": agent_id, "action": action[:50], "lesson": lesson}),
        "timestamp": time.time(),
    })


# ═══════════════════════════════════════════
# DASHBOARD — get full state
# ═══════════════════════════════════════════

def get_full_hermes_state() -> dict:
    """Get complete Hermes integration state for dashboard."""
    return {
        "sessions": {
            "total": len(sessions_store),
            "active": sum(1 for s in sessions_store if time.time() - s.get("updated_at", 0) < 3600),
        },
        "kanban": {
            "total": len(kanban_tasks),
            "todo": sum(1 for t in kanban_tasks.values() if t.status == "todo"),
            "in_progress": sum(1 for t in kanban_tasks.values() if t.status == "in_progress"),
            "done": sum(1 for t in kanban_tasks.values() if t.status == "done"),
        },
        "memory": {
            "agents": len(memory_items),
            "total_items": sum(len(v) for v in memory_items.values()),
        },
        "insights": {
            "total_events": len(insights_events),
            "today": sum(1 for e in insights_events if time.time() - e.get("timestamp", 0) < 86400),
        },
        "learning": {
            "total_events": len(learning_events),
        },
        "memory_graph": {
            "nodes": len(memory_graph),
            "edges": sum(len(v) for v in memory_graph.values()),
        },
        "curator": {
            "total_skills": len(curator_skills),
            "active": sum(1 for s in curator_skills.values() if s.get("status") == "active"),
        },
    }


# Auto-wire: create initial agents
on_agent_created("zain", "Zain", "Junior Researcher")
on_agent_created("noor", "Noor", "Code Apprentice")
on_agent_created("sara", "Sara", "Design Explorer")

on_task_created("Build AgentVerse UI", "noor")
on_task_created("Research Hermes Learning Loop", "zain")
on_task_created("Design Agent Society", "sara")

on_agent_speak("zain", "Zain", "Hey Noor! What are you working on?", "noor")
on_agent_speak("noor", "Noor", "Building the UI. What did you learn today?", "zain")
on_agent_speak("sara", "Sara", "I just discovered constraints spark creativity!", "noor")

on_agent_learned("zain", "asking", 0.65)
on_agent_learned("noor", "coding", 0.55)
on_agent_learned("sara", "design", 0.70)

on_agent_mistake("noor", "forgot to import module", "ModuleNotFoundError", "Always import before using")
on_agent_mistake("zain", "deleted research notes", "FileNotFoundError", "Always backup before deleting")