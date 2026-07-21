"""
Hermes Learning Loop — ينشأ تلقائياً لكل وكيل عند إنشائه.

يمنح كل وكيل ثلاث قدرات (مثل Hermes تماماً):
1. ذاكرة منظمة — الوكيل يقرر ما يتذكره + تذكير ذاتي دوري
2. إنشاء مهارات تلقائي — بعد المهام المعقدة، يستخرج الأنماط
3. مهارات تتحسن ذاتياً — كل استخدام يصقلها
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# === Store ===

class MemoryStore:
    """ذاكرة الوكيل — يحفظ ما يتعلمه، يسترجع عند الحاجة."""

    def __init__(self, agent_id: str, storage_dir: str = "/opt/data/Agent-Flow/agent_memories"):
        self.agent_id = agent_id
        self.dir = Path(storage_dir) / agent_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.memories: list[dict] = []
        self.nudge_count = 0
        self._load()

    def add(self, event_type: str, data: dict, importance: float = 0.5):
        """إضافة ذكرى — الأهم = تذكير أكثر."""
        mem = {
            "type": event_type,
            "data": data,
            "importance": min(1.0, importance),
            "timestamp": time.time(),
            "nudged_at": None,
        }
        self.memories.append(mem)
        if len(self.memories) > 200:
            self.memories = self.memories[-150:]
        self._save()

    def recall(self, query: str = "", limit: int = 10) -> list[dict]:
        """استرجاع ذكريات — حسب الكلمة أو الأهم."""
        if query:
            return [m for m in self.memories if query.lower() in json.dumps(m).lower()][-limit:]
        return sorted(self.memories, key=lambda m: m["importance"], reverse=True)[:limit]

    def nudge(self) -> Optional[str]:
        """تذكير ذاتي — يشجع الوكيل على استخدام ما تعلمه."""
        self.nudge_count += 1
        high_importance = [m for m in self.memories if m["importance"] > 0.7 and not m["nudged_at"]]
        if not high_importance:
            return None

        mem = high_importance[0]
        mem["nudged_at"] = time.time()
        self._save()
        return f"💡 تذكير: {json.dumps(mem['data'], ensure_ascii=False)[:100]}"

    def _save(self):
        try:
            (self.dir / "memory.json").write_text(json.dumps(self.memories, ensure_ascii=False, indent=2))
        except Exception:
            pass

    def _load(self):
        mf = self.dir / "memory.json"
        if mf.exists():
            try:
                self.memories = json.loads(mf.read_text())
            except Exception:
                self.memories = []


# === Skill System ===

@dataclass
class AgentSkill:
    """مهارة — مثل SKILL.md في Hermes."""
    name: str
    description: str
    confidence: float = 0.3
    times_used: int = 0
    created_at: float = 0.0
    last_used: float = 0.0
    tags: list[str] = field(default_factory=list)

    def use(self):
        """استخدام المهارة — تتحسن تلقائياً."""
        self.times_used += 1
        self.last_used = time.time()
        self.confidence = min(1.0, self.confidence + 0.05)

    def as_markdown(self) -> str:
        """كتابة المهارة كـ SKILL.md."""
        return f"""---
name: {self.name}
description: {self.description}
confidence: {self.confidence:.0%}
uses: {self.times_used}
tags: {', '.join(self.tags)}
---

# {self.name}

{self.description}

## Confidence
{self.confidence:.0%} — {self.times_used} uses

## Last Used
{time.strftime('%Y-%m-%d %H:%M', time.localtime(self.last_used)) if self.last_used else 'Never'}
"""


class SkillSystem:
    """نظام المهارات — ينشئ، يشحذ، يحسّن."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.skills: dict[str, AgentSkill] = {}
        self.skills_created_count = 0

    def get_or_create(self, name: str, description: str = "", tags: list[str] = None) -> AgentSkill:
        """الحصول على مهارة أو إنشائها — تستخدمها فتتحسن."""
        key = name.lower().replace(" ", "_")
        if key in self.skills:
            skill = self.skills[key]
            skill.use()
            return skill

        skill = AgentSkill(
            name=name,
            description=description or f"Skill: {name}",
            created_at=time.time(),
            tags=tags or [],
        )
        self.skills[key] = skill
        self.skills_created_count += 1
        return skill

    def create_from_experience(self, task: str, outcome: str) -> Optional[AgentSkill]:
        """إنشاء مهارة من تجربة — مثل Hermes تماماً."""
        # يستخرج النمط من النجاح
        if "success" not in outcome.lower() and "completed" not in outcome.lower():
            return None

        skill_name = task.lower().replace(" ", "_")[:30]
        return self.get_or_create(
            name=skill_name,
            description=f"Learned from: {task[:60]}",
            tags=["auto-created", "from-experience"],
        )

    def best_skill(self) -> Optional[AgentSkill]:
        if not self.skills:
            return None
        return max(self.skills.values(), key=lambda s: s.confidence * s.times_used)

    def to_dict(self) -> dict:
        return {k: {"name": v.name, "confidence": round(v.confidence, 2), "uses": v.times_used}
                for k, v in sorted(self.skills.items(), key=lambda x: -x[1].confidence)}

    def all_as_markdown(self, output_dir: str = "") -> list[str]:
        """تصدير كل المهارات كملفات SKILL.md."""
        files = []
        for skill in self.skills.values():
            md = skill.as_markdown()
            if output_dir:
                path = Path(output_dir) / f"{skill.name}.md"
                path.write_text(md)
                files.append(str(path))
        return files


# === Learning Loop Engine ===

class AgentLearningLoop:
    """حلقة التعلم — تجمع الذاكرة + المهارات + التذكير الذاتي."""

    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.memory = MemoryStore(agent_id)
        self.skills = SkillSystem(agent_id)
        self.iteration_count = 0
        self.tasks_completed = 0

    def after_action(self, action: str, result: str):
        """بعد كل إجراء — يسجل في الذاكرة ويبني مهارات."""
        self.iteration_count += 1

        # سجّل في الذاكرة
        importance = 0.5
        if "completed" in result.lower() or "success" in result.lower():
            importance = 0.8
            self.tasks_completed += 1
        elif "failed" in result.lower() or "error" in result.lower():
            importance = 0.7  # نتعلم من الأخطاء أيضاً

        self.memory.add(
            event_type="action",
            data={"action": action, "result": result, "iteration": self.iteration_count},
            importance=importance,
        )

        # إذا المهمة معقدة — أنشئ مهارة جديدة
        if len(action.split()) > 5 and importance >= 0.7:
            self.skills.create_from_experience(action, result)

        # مهارات تتحسن مع الاستخدام
        self.skills.get_or_create(action[:20])

        # تذكير ذاتي كل 10 دورات
        if self.iteration_count % 10 == 0:
            return self.memory.nudge()

        return None

    def get_context_for_llm(self) -> str:
        """يحضر سياقاً موجزاً للـ LLM — كل ما تعلمه الوكيل."""
        parts = [f"Agent: {self.agent_name}"]
        best = self.skills.best_skill()
        if best:
            parts.append(f"Best skill: {best.name} ({best.confidence:.0%})")
        parts.append(f"Tasks: {self.tasks_completed}")
        return " | ".join(parts)

    def summary(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "memory_items": len(self.memory.memories),
            "skills_created": self.skills.skills_created_count,
            "total_skills": len(self.skills.skills),
            "tasks_completed": self.tasks_completed,
            "iteration": self.iteration_count,
            "best_skill": self.skills.best_skill().name if self.skills.best_skill() else "none",
        }


# === Factory — ينشئ حلقة تعلم تلقائياً لكل وكيل ===

class AgentLearningFactory:
    """عند إنشاء أي وكيل في AgentVerse، يحصل على Learning Loop تلقائياً."""

    _instances: dict[str, AgentLearningLoop] = {}

    @classmethod
    def create_for(cls, agent_id: str, agent_name: str) -> AgentLearningLoop:
        """إنشاء حلقة تعلم جديدة للوكيل."""
        loop = AgentLearningLoop(agent_id, agent_name)
        cls._instances[agent_id] = loop
        return loop

    @classmethod
    def get(cls, agent_id: str) -> Optional[AgentLearningLoop]:
        return cls._instances.get(agent_id)

    @classmethod
    def all(cls) -> dict[str, AgentLearningLoop]:
        return cls._instances