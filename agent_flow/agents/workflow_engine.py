"""Workflow Orchestration - Multi-step agent workflows."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable, Optional
from enum import Enum

from .events import EventStore, EventType


class WorkflowStatus(str, Enum):
    """Workflow status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Step status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStep:
    """A single step in a workflow."""
    
    def __init__(
        self,
        step_id: str,
        name: str,
        agent_id: str,
        task: str,
        depends_on: Optional[list[str]] = None,
        condition: Optional[Callable[[dict], bool]] = None,
    ):
        self.id = step_id
        self.name = name
        self.agent_id = agent_id
        self.task = task
        self.depends_on = depends_on or []
        self.condition = condition
        
        self.status = StepStatus.PENDING
        self.result: Optional[str] = None
        self.error: Optional[str] = None
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "agent_id": self.agent_id,
            "task": self.task[:100] + "..." if len(self.task) > 100 else self.task,
            "depends_on": self.depends_on,
            "status": self.status.value,
            "result": self.result[:200] + "..." if self.result and len(self.result) > 200 else self.result,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
    
    def can_run(self, completed_steps: set[str]) -> bool:
        """Check if step can run."""
        # Check dependencies
        if not all(dep in completed_steps for dep in self.depends_on):
            return False
        # Check condition
        if self.condition:
            return False  # Conditions evaluated at runtime
        return True


class Workflow:
    """A workflow with multiple steps."""
    
    def __init__(
        self,
        workflow_id: str,
        name: str,
        team: Any,  # AgentTeam
        description: str = "",
    ):
        self.id = workflow_id
        self.name = name
        self.team = team
        self.description = description
        
        self.steps: list[WorkflowStep] = []
        self.status = WorkflowStatus.PENDING
        
        self.created_at = datetime.now().isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        
        # Results from all steps
        self.step_results: dict[str, str] = {}
    
    def add_step(
        self,
        name: str,
        agent_id: str,
        task: str,
        step_id: Optional[str] = None,
        depends_on: Optional[list[str]] = None,
    ) -> "WorkflowStep":
        """Add a step to the workflow."""
        if step_id is None:
            step_id = f"step_{len(self.steps)}"
        
        # Create step with context injection
        full_task = self._build_task_context(task)
        
        step = WorkflowStep(
            step_id=step_id,
            name=name,
            agent_id=agent_id,
            task=full_task,
            depends_on=depends_on,
        )
        self.steps.append(step)
        return step
    
    def _build_task_context(self, task: str) -> str:
        """Build task with context from previous steps."""
        if not self.step_results:
            return task
        
        context = f"""## Previous Steps Results

"""
        for step_id, result in self.step_results.items():
            context += f"### {step_id}\n{result[:500]}\n\n"
        
        context += f"""---

## Current Task

{task}

---

## Instructions
Build on the results from previous steps. If previous steps failed, adapt accordingly.
"""
        return context
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_ready_steps(self, completed: set[str]) -> list[WorkflowStep]:
        """Get steps that are ready to run."""
        ready = []
        for step in self.steps:
            # Skip non-pending steps
            if step.status != StepStatus.PENDING:
                continue
            # Skip already completed steps
            if step.id in completed:
                continue
            # Check dependencies
            if all(dep in completed for dep in step.depends_on):
                ready.append(step)
        return ready
    
    async def run(
        self,
        parallel: bool = False,
        stop_on_failure: bool = True,
    ) -> dict[str, Any]:
        """Run the workflow.
        
        Args:
            parallel: Run independent steps in parallel
            stop_on_failure: Stop workflow if a step fails
        """
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.now().isoformat()
        
        # Emit event
        self.team.events.emit(
            EventType.WORKFLOW_STARTED,
            {"workflow_id": self.id, "name": self.name, "steps": len(self.steps)}
        )
        
        completed: set[str] = set()
        failed: set[str] = set()
        
        max_iterations = len(self.steps) * 2  # Safety limit
        iteration = 0
        
        while len(completed) + len(failed) < len(self.steps) and iteration < max_iterations:
            iteration += 1
            
            # Get ready steps
            ready_steps = self.get_ready_steps(completed)
            
            if not ready_steps:
                break
            
            if parallel:
                # Run all ready steps in parallel
                await self._run_steps_parallel(ready_steps, completed, failed, stop_on_failure)
            else:
                # Run one step at a time
                await self._run_step(ready_steps[0], completed, failed, stop_on_failure)
        
        # Determine final status
        if failed and stop_on_failure:
            self.status = WorkflowStatus.FAILED
        elif len(completed) == len(self.steps):
            self.status = WorkflowStatus.COMPLETED
        else:
            self.status = WorkflowStatus.FAILED
        
        self.completed_at = datetime.now().isoformat()
        
        # Emit completion event
        self.team.events.emit(
            EventType.WORKFLOW_COMPLETED,
            {
                "workflow_id": self.id,
                "status": self.status.value,
                "completed": len(completed),
                "failed": len(failed),
            }
        )
        
        return {
            "workflow_id": self.id,
            "name": self.name,
            "status": self.status.value,
            "completed_steps": len(completed),
            "failed_steps": len(failed),
            "results": {s.id: s.result for s in self.steps if s.result},
        }
    
    async def _run_step(
        self,
        step: WorkflowStep,
        completed: set[str],
        failed: set[str],
        stop_on_failure: bool,
    ):
        """Run a single step."""
        if step.id in completed or step.id in failed:
            return
        
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now().isoformat()
        
        # Emit step started event
        self.team.events.emit(
            EventType.WORKFLOW_STEP_STARTED,
            {"workflow_id": self.id, "step_id": step.id, "name": step.name}
        )
        
        try:
            # Run the agent
            if step.agent_id not in self.team.agents:
                raise ValueError(f"Agent not found: {step.agent_id}")
            
            agent = self.team.agents[step.agent_id]
            result = agent.hermes_agent.chat(step.task)
            
            step.status = StepStatus.COMPLETED
            step.result = result
            step.completed_at = datetime.now().isoformat()
            
            # Store result for dependent steps
            self.step_results[step.id] = result
            completed.add(step.id)
            
            # Add to team memory
            self.team.environment.add_memory(
                step.agent_id,
                f"Workflow step '{step.name}' completed: {str(result)[:200]}"
            )
            
            # Emit step completed event
            self.team.events.emit(
                EventType.WORKFLOW_STEP_COMPLETED,
                {"workflow_id": self.id, "step_id": step.id, "name": step.name}
            )
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.now().isoformat()
            failed.add(step.id)
            
            # Emit step failed event
            self.team.events.emit(
                EventType.WORKFLOW_STEP_FAILED,
                {"workflow_id": self.id, "step_id": step.id, "name": step.name, "error": str(e)}
            )
            
            if stop_on_failure:
                # Skip dependent steps
                for s in self.steps:
                    if s.id not in completed and s.id not in failed:
                        if any(dep in failed for dep in s.depends_on):
                            s.status = StepStatus.SKIPPED
    
    async def _run_steps_parallel(
        self,
        steps: list[WorkflowStep],
        completed: set[str],
        failed: set[str],
        stop_on_failure: bool,
    ):
        """Run multiple steps in parallel."""
        tasks = [self._run_step(s, completed, failed, stop_on_failure) for s in steps]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def to_dict(self) -> dict:
        """Export workflow as dict."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class WorkflowEngine:
    """Engine for managing multiple workflows."""
    
    def __init__(self, team: Any):
        self.team = team
        self.workflows: dict[str, Workflow] = {}
    
    def create_workflow(
        self,
        name: str,
        description: str = "",
    ) -> Workflow:
        """Create a new workflow."""
        workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workflow = Workflow(workflow_id, name, self.team, description)
        self.workflows[workflow_id] = workflow
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self, status: Optional[WorkflowStatus] = None) -> list[Workflow]:
        """List workflows, optionally filtered by status."""
        workflows = list(self.workflows.values())
        if status:
            workflows = [w for w in workflows if w.status == status]
        return workflows
    
    async def run_workflow(
        self,
        workflow_id: str,
        parallel: bool = False,
    ) -> dict[str, Any]:
        """Run a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}
        
        return await workflow.run(parallel=parallel)
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            return True
        return False
