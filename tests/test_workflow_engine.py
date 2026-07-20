"""Test for workflow engine."""

import unittest
from unittest.mock import Mock, AsyncMock, patch


class TestWorkflowEngine(unittest.TestCase):
    """Test WorkflowEngine class."""
    
    def test_workflow_creation(self):
        """Test creating a workflow."""
        from agent_flow.agents import Workflow, WorkflowEngine
        
        # Create mock team
        mock_team = Mock()
        mock_team.events = Mock()
        mock_team.events.emit = Mock()
        mock_team.environment = Mock()
        mock_team.environment.add_memory = Mock()
        
        # Create workflow engine
        engine = WorkflowEngine(mock_team)
        
        # Create workflow
        workflow = engine.create_workflow("Test Workflow", "A test workflow")
        
        self.assertEqual(workflow.name, "Test Workflow")
        self.assertEqual(workflow.description, "A test workflow")
        self.assertEqual(len(workflow.steps), 0)
    
    def test_workflow_steps(self):
        """Test adding steps to workflow."""
        from agent_flow.agents import Workflow
        
        # Create mock team
        mock_team = Mock()
        mock_team.events = Mock()
        mock_team.events.emit = Mock()
        mock_team.environment = Mock()
        mock_team.environment.add_memory = Mock()
        
        # Create workflow
        workflow = Workflow("wf_1", "Test", mock_team)
        
        # Add steps
        step1 = workflow.add_step("Research", "agent1", "Research task")
        step2 = workflow.add_step("Code", "agent2", "Code task", depends_on=["step_0"])
        
        self.assertEqual(len(workflow.steps), 2)
        self.assertEqual(step1.id, "step_0")
        self.assertEqual(step2.id, "step_1")
        self.assertEqual(step2.depends_on, ["step_0"])
    
    def test_workflow_get_ready_steps(self):
        """Test getting ready steps."""
        from agent_flow.agents import Workflow, WorkflowEngine
        
        mock_team = Mock()
        mock_team.events = Mock()
        mock_team.events.emit = Mock()
        mock_team.environment = Mock()
        mock_team.environment.add_memory = Mock()
        
        workflow = Workflow("wf_1", "Test", mock_team)
        
        # Add step with no dependencies
        workflow.add_step("Step 1", "agent1", "Task 1")
        
        # Add step that depends on step_0
        workflow.add_step("Step 2", "agent2", "Task 2", depends_on=["step_0"])
        
        # First step should be ready (no dependencies)
        ready = workflow.get_ready_steps(set())
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0].id, "step_0")
        
        # After step_0 completes, step_1 should be ready
        ready = workflow.get_ready_steps({"step_0"})
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0].id, "step_1")


if __name__ == "__main__":
    unittest.main()
