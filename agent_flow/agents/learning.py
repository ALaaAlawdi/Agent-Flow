"""Learning Engine - Agents learn and improve from experiences."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Optional
from collections import defaultdict

from .memory import AgentMemory, TeamMemory, MemoryEntry
from .events import EventStore, EventType


class LearningMetric:
    """Track a learning metric over time."""
    
    def __init__(self, name: str):
        self.name = name
        self.values: list[tuple[str, float]] = []  # (timestamp, value)
    
    def add(self, value: float, timestamp: Optional[str] = None):
        """Add a metric value."""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        self.values.append((timestamp, value))
    
    def average(self, window: int = 10) -> float:
        """Get average of last N values."""
        if not self.values:
            return 0.0
        recent = self.values[-window:]
        return sum(v for _, v in recent) / len(recent)
    
    def trend(self, window: int = 10) -> float:
        """Get trend (positive = improving)."""
        if len(self.values) < 2:
            return 0.0
        recent = self.values[-window:]
        if len(recent) < 2:
            return 0.0
        first_half = sum(v for _, v in recent[:len(recent)//2])
        second_half = sum(v for _, v in recent[len(recent)//2:])
        return second_half - first_half


class AgentLearning:
    """Learning system for a single agent.
    
    Tracks performance and improves over time.
    """
    
    def __init__(self, agent_id: str, memory: AgentMemory):
        self.agent_id = agent_id
        self.memory = memory
        
        # Performance metrics
        self.metrics = {
            "success_rate": LearningMetric("success_rate"),
            "response_time": LearningMetric("response_time"),
            "task_complexity": LearningMetric("task_complexity"),
            "collaboration_score": LearningMetric("collaboration_score"),
        }
        
        # Learning state
        self.learned_skills: list[dict] = []
        self.improvement_areas: list[str] = []
        
        # Training data for self-improvement
        self.task_history: list[dict] = []
    
    def record_task(
        self,
        task: str,
        result: str,
        success: bool,
        response_time: float,
        complexity: float = 0.5,
        helpers: Optional[list[str]] = None,
    ):
        """Record a task execution for learning."""
        # Record in memory
        self.memory.learn_from_task(
            task=task,
            result=result,
            success=success,
        )
        
        # Update metrics
        self.metrics["success_rate"].add(1.0 if success else 0.0)
        self.metrics["response_time"].add(response_time)
        self.metrics["task_complexity"].add(complexity)
        
        if helpers:
            self.metrics["collaboration_score"].add(min(1.0, len(helpers) / 3))
        
        # Store in history
        self.task_history.append({
            "task": task,
            "result": result[:200],
            "success": success,
            "response_time": response_time,
            "complexity": complexity,
            "helpers": helpers or [],
            "timestamp": datetime.now().isoformat(),
        })
        
        # Extract new skills if successful
        if success:
            self._extract_new_skills(task, result)
    
    def _extract_new_skills(self, task: str, result: str):
        """Extract potential new skills from successful task."""
        # Simple heuristic: if task was complex and successful,
        # extract the approach as a skill
        if len(self.task_history) > 0:
            last_task = self.task_history[-1]
            if last_task["complexity"] > 0.7:
                skill = {
                    "from_task": task,
                    "approach": result[:100],
                    "timestamp": datetime.now().isoformat(),
                }
                if skill not in self.learned_skills:
                    self.learned_skills.append(skill)
    
    def get_performance_report(self) -> dict:
        """Get agent performance report."""
        return {
            "agent_id": self.agent_id,
            "success_rate": self.metrics["success_rate"].average(),
            "success_trend": self.metrics["success_rate"].trend(),
            "avg_response_time": self.metrics["response_time"].average(),
            "response_time_trend": self.metrics["response_time"].trend(),
            "avg_complexity": self.metrics["task_complexity"].average(),
            "collaboration": self.metrics["collaboration_score"].average(),
            "learned_skills_count": len(self.learned_skills),
            "task_history_count": len(self.task_history),
        }
    
    def get_suggestions(self) -> list[str]:
        """Get improvement suggestions based on learning."""
        suggestions = []
        
        # Check success rate
        if self.metrics["success_rate"].average() < 0.7:
            suggestions.append("Success rate is low - consider seeking help more often")
        
        # Check response time
        if self.metrics["response_time"].average() > 60:  # > 60 seconds
            suggestions.append("Response time is high - consider optimizing approach")
        
        # Check collaboration
        if self.metrics["collaboration_score"].average() < 0.3:
            suggestions.append("Low collaboration - consider working with other agents")
        
        # Check for improvement areas
        for area in self.improvement_areas:
            suggestions.append(f"Focus on improving: {area}")
        
        return suggestions
    
    def improve(self, focus_area: str):
        """Focus improvement on specific area."""
        if focus_area not in self.improvement_areas:
            self.improvement_areas.append(focus_area)


class TeamLearning:
    """Team-wide learning system.
    
    Coordinates learning across all agents and identifies team patterns.
    """
    
    def __init__(self, team_name: str, memory: TeamMemory):
        self.team_name = team_name
        self.memory = memory
        self.events = EventStore(f"learning_{team_name}")
        
        # Per-agent learning
        self.agent_learning: dict[str, AgentLearning] = {}
        
        # Team patterns
        self.team_strengths: list[str] = []
        self.team_weaknesses: list[str] = []
        
        # Shared learnings
        self.best_practices: list[dict] = []
    
    def get_agent_learning(self, agent_id: str) -> AgentLearning:
        """Get or create learning for an agent."""
        if agent_id not in self.agent_learning:
            agent_memory = self.memory.get_agent_memory(agent_id)
            self.agent_learning[agent_id] = AgentLearning(agent_id, agent_memory)
        return self.agent_learning[agent_id]
    
    def record_task(
        self,
        agent_id: str,
        task: str,
        result: str,
        success: bool,
        response_time: float,
        complexity: float = 0.5,
        helpers: Optional[list[str]] = None,
    ):
        """Record task for team learning."""
        # Get agent learning
        agent_learning = self.get_agent_learning(agent_id)
        
        # Record task
        agent_learning.record_task(
            task=task,
            result=result,
            success=success,
            response_time=response_time,
            complexity=complexity,
            helpers=helpers,
        )
        
        # Emit learning event
        self.events.emit(
            EventType.TASK_COMPLETED if success else EventType.TASK_FAILED,
            {
                "agent_id": agent_id,
                "task": task[:100],
                "success": success,
                "response_time": response_time,
            }
        )
        
        # If successful and had help, share the learning
        if success and helpers:
            self._share_learning(agent_id, task, result)
    
    def _share_learning(self, agent_id: str, task: str, result: str):
        """Share learning with team."""
        # Share successful approach
        self.memory.share_knowledge(
            agent_id=agent_id,
            content=f"Task: {task}\nSuccessful approach: {result[:200]}",
            importance=0.7,
            tags=["success", "approach"],
        )
        
        # Emit event
        self.events.emit(
            EventType.INSIGHT_GAINED,
            {
                "agent_id": agent_id,
                "task": task[:50],
            }
        )
    
    def analyze_team_performance(self) -> dict:
        """Analyze overall team performance."""
        if not self.agent_learning:
            return {"status": "no_data"}
        
        # Aggregate metrics
        total_success = 0.0
        total_response_time = 0.0
        total_collaboration = 0.0
        agent_count = len(self.agent_learning)
        
        for agent_id, learning in self.agent_learning.items():
            report = learning.get_performance_report()
            total_success += report["success_rate"]
            total_response_time += report["avg_response_time"]
            total_collaboration += report["collaboration"]
        
        # Identify strengths
        avg_success = total_success / agent_count
        if avg_success > 0.8:
            self.team_strengths.append("High success rate")
        
        if total_collaboration / agent_count > 0.5:
            self.team_strengths.append("Strong collaboration")
        
        # Identify weaknesses
        if avg_success < 0.6:
            self.team_weaknesses.append("Low success rate")
        
        if total_response_time / agent_count > 60:
            self.team_weaknesses.append("Slow response times")
        
        return {
            "team_name": self.team_name,
            "agent_count": agent_count,
            "avg_success_rate": total_success / agent_count,
            "avg_response_time": total_response_time / agent_count,
            "avg_collaboration": total_collaboration / agent_count,
            "strengths": list(set(self.team_strengths)),
            "weaknesses": list(set(self.team_weaknesses)),
        }
    
    def get_best_practices(self) -> list[dict]:
        """Get team best practices."""
        # Query team knowledge
        knowledge = self.memory.query_team_knowledge("successful approach", limit=20)
        
        best_practices = []
        for entry in knowledge:
            best_practices.append({
                "content": entry.content,
                "importance": entry.importance,
                "tags": entry.tags,
            })
        
        return best_practices
    
    def suggest_improvements(self) -> list[str]:
        """Suggest team-wide improvements."""
        suggestions = []
        
        analysis = self.analyze_team_performance()
        
        if "Low success rate" in analysis.get("weaknesses", []):
            suggestions.append("Team needs more training or guidance")
        
        if "Slow response times" in analysis.get("weaknesses", []):
            suggestions.append("Consider optimizing task routing or agent capabilities")
        
        # Check for patterns
        for agent_id, learning in self.agent_learning.items():
            suggestions.extend([
                f"{agent_id}: {s}" 
                for s in learning.get_suggestions()
            ])
        
        return suggestions
    
    def auto_improve(self) -> dict:
        """Automatically improve team based on learning."""
        improvements = []
        
        # Analyze performance
        analysis = self.analyze_team_performance()
        
        # Find low-performing agents
        for agent_id, learning in self.agent_learning.items():
            report = learning.get_performance_report()
            
            if report["success_rate"] < 0.6:
                # Suggest focus area
                learning.improve("success_rate")
                improvements.append(f"{agent_id}: Focusing on success rate")
        
        # Share best practices
        best = self.get_best_practices()
        if best:
            improvements.append(f"Sharing {len(best)} best practices across team")
        
        return {
            "improvements": improvements,
            "analysis": analysis,
        }
