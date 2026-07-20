"""Planning Engine - Agents plan their actions and predict outcomes."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class Plan:
    """A plan with steps and dependencies."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.steps: list[dict] = []
        self.created_at = datetime.now().isoformat()
        self.status = "draft"  # draft, active, completed, failed
        self.dependencies: dict[int, list[int]] = defaultdict(list)
    
    def add_step(
        self,
        action: str,
        agent: str,
        expected_outcome: str,
        estimated_time: float = 30.0,
        dependencies: Optional[list[int]] = None,
        priority: int = 5,
    ) -> int:
        """Add a step to the plan. Returns step index."""
        step = {
            "index": len(self.steps),
            "action": action,
            "agent": agent,
            "expected_outcome": expected_outcome,
            "estimated_time": estimated_time,
            "priority": priority,
            "status": "pending",
            "actual_outcome": None,
            "actual_time": None,
            "started_at": None,
            "completed_at": None,
        }
        self.steps.append(step)
        
        if dependencies:
            for dep in dependencies:
                self.dependencies[step["index"]].append(dep)
        
        return step["index"]
    
    def get_ready_steps(self) -> list[dict]:
        """Get steps that are ready to execute (dependencies met)."""
        completed = {s["index"] for s in self.steps if s["status"] == "completed"}
        ready = []
        
        for step in self.steps:
            if step["status"] != "pending":
                continue
            
            deps = self.dependencies.get(step["index"], [])
            if all(d in completed for d in deps):
                ready.append(step)
        
        # Sort by priority
        ready.sort(key=lambda s: -s["priority"])
        return ready
    
    def get_total_estimated_time(self) -> float:
        """Get total estimated time (parallel-aware)."""
        # Simple: assume steps can be parallelized based on dependencies
        if not self.steps:
            return 0.0
        
        # Calculate critical path
        # For now, just sum all estimated times
        return sum(s["estimated_time"] for s in self.steps)
    
    def get_progress(self) -> dict:
        """Get plan progress."""
        total = len(self.steps)
        completed = sum(1 for s in self.steps if s["status"] == "completed")
        failed = sum(1 for s in self.steps if s["status"] == "failed")
        in_progress = sum(1 for s in self.steps if s["status"] == "in_progress")
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": total - completed - failed - in_progress,
            "progress_percent": (completed / total * 100) if total > 0 else 0,
        }


class PlanningEngine:
    """Engine for planning and strategy.
    
    Features:
    - Multi-step plan creation
    - Dependency management
    - Progress tracking
    - Plan adaptation
    - Strategy selection
    """
    
    def __init__(self):
        self.plans: dict[str, Plan] = {}
        self.strategies: dict[str, list[str]] = {}
        
        # Plan execution history
        self.plan_history: list[dict] = []
    
    def create_plan(
        self,
        name: str,
        goal: str,
        strategy: str = "default",
    ) -> Plan:
        """Create a new plan."""
        plan = Plan(name, goal)
        self.plans[name] = plan
        
        # Generate plan from strategy
        if strategy in self.strategies:
            self._apply_strategy(plan, strategy, goal)
        
        return plan
    
    def register_strategy(self, name: str, steps: list[str]):
        """Register a reusable strategy."""
        self.strategies[name] = steps
    
    def _apply_strategy(self, plan: Plan, strategy: str, goal: str):
        """Apply a strategy template to a plan."""
        steps = self.strategies.get(strategy, [])
        
        for step_template in steps:
            plan.add_step(
                action=step_template.format(goal=goal),
                agent="auto",
                expected_outcome=f"Step completed: {step_template[:50]}",
            )
    
    def decompose_goal(self, goal: str) -> Plan:
        """Decompose a goal into a plan.
        
        Uses heuristics to break down the goal.
        """
        plan = Plan(f"plan_{int(datetime.now().timestamp())}", goal)
        goal_lower = goal.lower()
        
        # Research phase
        if any(w in goal_lower for w in ["research", "find", "analyze", "ابحث", "حلل"]):
            plan.add_step(
                action=f"Research: {goal}",
                agent="researcher",
                expected_outcome="Research findings",
                estimated_time=60,
                priority=10,
            )
        
        # Design phase
        if any(w in goal_lower for w in ["build", "create", "develop", "ابنِ", "طور"]):
            plan.add_step(
                action=f"Design: {goal}",
                agent="analyst",
                expected_outcome="Design specification",
                estimated_time=45,
                priority=9,
            )
            plan.add_step(
                action=f"Implement: {goal}",
                agent="coder",
                expected_outcome="Working implementation",
                estimated_time=120,
                priority=8,
            )
        
        # Review phase
        if any(w in goal_lower for w in ["quality", "production", "review", "جودة"]):
            plan.add_step(
                action=f"Review: {goal}",
                agent="reviewer",
                expected_outcome="Quality assurance",
                estimated_time=30,
                priority=7,
            )
        
        # Test phase
        if any(w in goal_lower for w in ["test", "verify", "اختبر"]):
            plan.add_step(
                action=f"Test: {goal}",
                agent="tester",
                expected_outcome="Tests passing",
                estimated_time=45,
                priority=6,
            )
        
        # Deploy phase
        if any(w in goal_lower for w in ["deploy", "release", "نشر"]):
            plan.add_step(
                action=f"Deploy: {goal}",
                agent="devops",
                expected_outcome="Deployed successfully",
                estimated_time=30,
                priority=5,
            )
        
        # If no specific phases, add a general step
        if not plan.steps:
            plan.add_step(
                action=f"Execute: {goal}",
                agent="auto",
                expected_outcome="Goal achieved",
            )
        
        return plan
    
    def adapt_plan(self, plan_name: str, feedback: str):
        """Adapt a plan based on feedback.
        
        Adds new steps or modifies existing ones.
        """
        if plan_name not in self.plans:
            return None
        
        plan = self.plans[plan_name]
        
        # Add a step based on feedback
        plan.add_step(
            action=f"Address feedback: {feedback}",
            agent="auto",
            expected_outcome="Feedback addressed",
            priority=8,
        )
        
        return plan
    
    def get_recommended_plan(self, goal: str) -> dict:
        """Get plan recommendation for a goal."""
        plan = self.decompose_goal(goal)
        
        return {
            "name": plan.name,
            "steps_count": len(plan.steps),
            "estimated_time": plan.get_total_estimated_time(),
            "phases": [s["action"] for s in plan.steps],
        }
    
    def execute_step(self, plan_name: str, step_index: int) -> dict:
        """Mark a step as in progress."""
        if plan_name not in self.plans:
            return {"error": "Plan not found"}
        
        plan = self.plans[plan_name]
        if step_index >= len(plan.steps):
            return {"error": "Step not found"}
        
        step = plan.steps[step_index]
        step["status"] = "in_progress"
        step["started_at"] = datetime.now().isoformat()
        
        return {"status": "started", "step": step}
    
    def complete_step(self, plan_name: str, step_index: int, outcome: str = "") -> dict:
        """Mark a step as completed."""
        if plan_name not in self.plans:
            return {"error": "Plan not found"}
        
        plan = self.plans[plan_name]
        if step_index >= len(plan.steps):
            return {"error": "Step not found"}
        
        step = plan.steps[step_index]
        step["status"] = "completed"
        step["actual_outcome"] = outcome
        step["completed_at"] = datetime.now().isoformat()
        
        # Calculate actual time
        if step["started_at"]:
            start = datetime.fromisoformat(step["started_at"])
            elapsed = (datetime.now() - start).total_seconds()
            step["actual_time"] = elapsed
        
        # Check if plan is complete
        if all(s["status"] == "completed" for s in plan.steps):
            plan.status = "completed"
            self.plan_history.append({
                "plan": plan.name,
                "completed_at": datetime.now().isoformat(),
                "steps": len(plan.steps),
            })
        
        return {"status": "completed", "step": step}
    
    def fail_step(self, plan_name: str, step_index: int, error: str = "") -> dict:
        """Mark a step as failed."""
        if plan_name not in self.plans:
            return {"error": "Plan not found"}
        
        plan = self.plans[plan_name]
        if step_index >= len(plan.steps):
            return {"error": "Step not found"}
        
        step = plan.steps[step_index]
        step["status"] = "failed"
        step["actual_outcome"] = f"Error: {error}"
        step["completed_at"] = datetime.now().isoformat()
        
        return {"status": "failed", "step": step}