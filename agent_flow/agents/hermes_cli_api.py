"""
Hermes Integration API — Sessions, Kanban, Curator, Memory, Insights, Webhooks.

Direct equivalents of Hermes CLI commands, accessible via Agent-Flow API.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from fastapi import APIRouter, HTTPException
from pathlib import Path

router = APIRouter(prefix="/hermes", tags=["hermes-integration"])

# ================================================
# 📊 SESSIONS
# ================================================

sessions_store: list[dict] = []
session_counter = 0


@router.get("/sessions")
async def list_sessions():
    """hermes sessions list — عرض الجلسات"""
    return {"sessions": sessions_store, "total": len(sessions_store)}


@router.post("/sessions")
async def create_session(name: str, agent_id: str = ""):
    """Create a new session record"""
    global session_counter
    session_counter += 1
    session = {
        "id": f"session_{session_counter}",
        "name": name,
        "agent_id": agent_id,
        "messages": [],
        "created_at": time.time(),
        "updated_at": time.time(),
    }
    sessions_store.append(session)
    return session


@router.post("/sessions/{session_id}/messages")
async def add_message(session_id: str, role: str, content: str):
    """Add a message to a session"""
    for s in sessions_store:
        if s["id"] == session_id:
            s["messages"].append({
                "role": role,
                "content": content,
                "timestamp": time.time(),
            })
            s["updated_at"] = time.time()
            return s
    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/sessions/export")
async def export_sessions():
    """hermes sessions export — تصدير JSONL"""
    lines = [json.dumps(s, ensure_ascii=False) for s in sessions_store]
    return {"format": "jsonl", "data": "\n".join(lines), "count": len(sessions_store)}


@router.get("/sessions/stats")
async def sessions_stats():
    """hermes sessions stats — إحصائيات"""
    now = time.time()
    return {
        "total_sessions": len(sessions_store),
        "total_messages": sum(len(s.get("messages", [])) for s in sessions_store),
        "active_today": sum(1 for s in sessions_store if now - s.get("updated_at", 0) < 86400),
        "by_agent": _group_by_agent(),
    }


def _group_by_agent() -> dict:
    groups = {}
    for s in sessions_store:
        aid = s.get("agent_id", "unknown")
        groups[aid] = groups.get(aid, 0) + 1
    return groups


# ================================================
# 📋 KANBAN
# ================================================

@dataclass
class KanbanTask:
    id: str
    title: str
    description: str = ""
    status: str = "todo"  # todo, in_progress, done, blocked
    assignee: str = ""
    priority: int = 1
    board: str = "default"
    created_at: float = 0.0
    comments: list[dict] = field(default_factory=list)
    links: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()


kanban_tasks: dict[str, KanbanTask] = {}
kanban_counter = 0


@router.post("/kanban/init")
async def kanban_init():
    """hermes kanban init — تهيئة لوحة"""
    return {"status": "initialized", "boards": ["default"]}


@router.post("/kanban/create")
async def kanban_create(title: str, description: str = "", priority: int = 1, board: str = "default"):
    """hermes kanban create — إنشاء مهمة"""
    global kanban_counter
    kanban_counter += 1
    task = KanbanTask(
        id=f"task_{kanban_counter}",
        title=title,
        description=description,
        priority=priority,
        board=board,
    )
    kanban_tasks[task.id] = task
    return task.__dict__


@router.get("/kanban/list")
async def kanban_list(status: str = "", board: str = "default"):
    """hermes kanban list — عرض المهام"""
    tasks = [t.__dict__ for t in kanban_tasks.values() if t.board == board]
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    return {"tasks": tasks, "total": len(tasks)}


@router.get("/kanban/{task_id}")
async def kanban_show(task_id: str):
    """hermes kanban show — تفاصيل مهمة"""
    if task_id not in kanban_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return kanban_tasks[task_id].__dict__


@router.post("/kanban/{task_id}/assign")
async def kanban_assign(task_id: str, assignee: str):
    """hermes kanban assign — تعيين وكيل"""
    if task_id not in kanban_tasks:
        raise HTTPException(status_code=404)
    kanban_tasks[task_id].assignee = assignee
    kanban_tasks[task_id].status = "in_progress"
    return kanban_tasks[task_id].__dict__


@router.post("/kanban/{task_id}/comment")
async def kanban_comment(task_id: str, author: str, text: str):
    """hermes kanban comment — تعليق"""
    if task_id not in kanban_tasks:
        raise HTTPException(status_code=404)
    kanban_tasks[task_id].comments.append({
        "author": author,
        "text": text,
        "timestamp": time.time(),
    })
    return kanban_tasks[task_id].__dict__


@router.post("/kanban/{task_id}/complete")
async def kanban_complete(task_id: str):
    """hermes kanban complete — إكمال مهمة"""
    if task_id not in kanban_tasks:
        raise HTTPException(status_code=404)
    kanban_tasks[task_id].status = "done"
    return kanban_tasks[task_id].__dict__


@router.post("/kanban/{task_id}/block")
async def kanban_block(task_id: str, reason: str = ""):
    """hermes kanban block — حظر مهمة"""
    if task_id not in kanban_tasks:
        raise HTTPException(status_code=404)
    kanban_tasks[task_id].status = "blocked"
    if reason:
        kanban_tasks[task_id].comments.append({
            "author": "system",
            "text": f"Blocked: {reason}",
            "timestamp": time.time(),
        })
    return kanban_tasks[task_id].__dict__


@router.get("/kanban/stats")
async def kanban_stats():
    """hermes kanban stats — إحصائيات"""
    tasks = list(kanban_tasks.values())
    return {
        "total": len(tasks),
        "todo": sum(1 for t in tasks if t.status == "todo"),
        "in_progress": sum(1 for t in tasks if t.status == "in_progress"),
        "done": sum(1 for t in tasks if t.status == "done"),
        "blocked": sum(1 for t in tasks if t.status == "blocked"),
    }


# ================================================
# 🧠 MEMORY
# ================================================

memory_enabled = True
memory_items: dict[str, list[dict]] = {}


@router.get("/memory/status")
async def memory_status():
    """hermes memory status — حالة الذاكرة"""
    return {
        "enabled": memory_enabled,
        "total_items": sum(len(v) for v in memory_items.values()),
        "agents": len(memory_items),
    }


@router.post("/memory/setup")
async def memory_setup(enabled: bool = True):
    """hermes memory setup — إعداد الذاكرة"""
    global memory_enabled
    memory_enabled = enabled
    return {"status": "configured", "enabled": memory_enabled}


@router.post("/memory/add")
async def memory_add(agent_id: str, key: str, value: str):
    """Add a memory item for an agent"""
    if agent_id not in memory_items:
        memory_items[agent_id] = []
    memory_items[agent_id].append({
        "key": key,
        "value": value,
        "timestamp": time.time(),
    })
    return {"status": "added"}


@router.get("/memory/{agent_id}")
async def memory_get(agent_id: str, key: str = ""):
    """Get memories for an agent"""
    items = memory_items.get(agent_id, [])
    if key:
        items = [i for i in items if i["key"] == key]
    return {"agent_id": agent_id, "memories": items}


# ================================================
# 📈 INSIGHTS
# ================================================

insights_events: list[dict] = []


@router.get("/insights")
async def get_insights(days: int = 7):
    """hermes insights — تحليلات الاستخدام"""
    now = time.time()
    recent = [e for e in insights_events if now - e.get("timestamp", 0) < days * 86400]
    return {
        "total_events": len(insights_events),
        "recent_events": len(recent),
        "sessions": len(sessions_store),
        "kanban_tasks": len(kanban_tasks),
        "memory_items": sum(len(v) for v in memory_items.values()),
        "by_type": _group_by_type(recent),
    }


def _group_by_type(events: list) -> dict:
    groups = {}
    for e in events:
        t = e.get("type", "unknown")
        groups[t] = groups.get(t, 0) + 1
    return groups


@router.post("/insights/track")
async def track_event(type: str, data: str = ""):
    """Track an event for insights"""
    insights_events.append({
        "type": type,
        "data": data,
        "timestamp": time.time(),
    })
    return {"status": "tracked"}


# ================================================
# 🔍 CURATOR
# ================================================

curator_skills: dict[str, dict] = {}


@router.get("/curator/status")
async def curator_status():
    """hermes curator status — حالة المهارات"""
    return {
        "total_skills": len(curator_skills),
        "active": sum(1 for s in curator_skills.values() if s.get("status") == "active"),
        "archived": sum(1 for s in curator_skills.values() if s.get("status") == "archived"),
        "skills": curator_skills,
    }


@router.post("/curator/pin/{skill_name}")
async def curator_pin(skill_name: str):
    """hermes curator pin — تثبيت مهارة"""
    curator_skills[skill_name] = {"name": skill_name, "status": "pinned", "pinned_at": time.time()}
    return {"status": "pinned", "skill": skill_name}


@router.post("/curator/archive/{skill_name}")
async def curator_archive(skill_name: str):
    """hermes curator archive — أرشفة مهارة"""
    if skill_name in curator_skills:
        curator_skills[skill_name]["status"] = "archived"
        curator_skills[skill_name]["archived_at"] = time.time()
    return {"status": "archived", "skill": skill_name}


@router.post("/curator/run")
async def curator_run():
    """hermes curator run — تشغيل الصيانة"""
    archived = sum(1 for s in curator_skills.values() if s.get("status") == "archived")
    active = sum(1 for s in curator_skills.values() if s.get("status") in ("active", "pinned"))
    return {"status": "completed", "active": active, "archived": archived}