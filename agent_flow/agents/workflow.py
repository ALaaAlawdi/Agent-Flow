"""Dynamic Workflow - Execute tasks with Hermes AIAgent."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

# Hermes imports
from run_agent import AIAgent

from .registry import DynamicAgentRegistry
from .communication import AgentCommunication, AgentMessage


class DynamicWorkflow:
    """Execute tasks using Hermes AIAgent instances.
    
    Supports single agent execution and team workflows with
    inter-agent communication.
    """
    
    def __init__(
        self,
        registry: DynamicAgentRegistry,
        communication: AgentCommunication,
    ):
        """Initialize workflow executor.
        
        Args:
            registry: Agent registry
            communication: Message broker
        """
        self.registry = registry
        self.comm = communication
    
    async def run_single(
        self,
        agent_id: str,
        task: str,
    ) -> dict[str, Any]:
        """Run a single agent on a task.
        
        Args:
            agent_id: Agent to run
            task: Task description
            
        Returns:
            Result dict with agent output
        """
        agent = self.registry.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Check for pending messages
        messages = self.comm.get_messages(agent_id)
        
        # Build context
        context = self._build_context(task, messages)
        
        # Update status
        self.registry.set_status(agent_id, "busy")
        
        try:
            # Run agent (Hermes handles execution)
            # AIAgent.chat() may be async or sync depending on config
            if asyncio.iscoroutinefunction(agent.chat):
                result = await agent.chat(context)
            else:
                result = agent.chat(context)
            
            return {
                "agent_id": agent_id,
                "result": result,
                "messages_received": len(messages),
                "status": "success",
            }
        except Exception as e:
            return {
                "agent_id": agent_id,
                "error": str(e),
                "messages_received": len(messages),
                "status": "error",
            }
        finally:
            self.registry.set_status(agent_id, "online")
    
    async def run_team(
        self,
        agent_ids: list[str],
        task: str,
    ) -> dict[str, Any]:
        """Run multiple agents with communication.
        
        Args:
            agent_ids: List of agent IDs to run
            task: Task description
            
        Returns:
            Dict of results per agent
        """
        results = {}
        
        for agent_id in agent_ids:
            # Get messages from teammates
            messages = self.comm.get_messages(agent_id)
            
            # Build context with team context
            context = self._build_context(task, messages, results)
            
            # Update status
            self.registry.set_status(agent_id, "busy")
            
            try:
                agent = self.registry.get(agent_id)
                if not agent:
                    results[agent_id] = {"error": f"Agent {agent_id} not found"}
                    continue
                
                # Run agent
                if asyncio.iscoroutinefunction(agent.chat):
                    result = await agent.chat(context)
                else:
                    result = agent.chat(context)
                
                results[agent_id] = {
                    "result": result,
                    "messages_received": len(messages),
                }
                
                # Broadcast completion to collaborators
                config = self.registry.get_config(agent_id)
                if config:
                    collaborators = config.get("collaborates_with", [])
                    for collab_role in collaborators:
                        collab_ids = self.registry.find_by_role(collab_role)
                        for collab_id in collab_ids:
                            if collab_id != agent_id:
                                self.comm.send_message(
                                    agent_id,
                                    collab_id,
                                    f"Completed: {str(result)[:200]}...",
                                )
            
            except Exception as e:
                results[agent_id] = {"error": str(e)}
            
            finally:
                self.registry.set_status(agent_id, "online")
        
        return results
    
    async def run_sequential(
        self,
        agent_ids: list[str],
        task: str,
    ) -> dict[str, Any]:
        """Run agents sequentially, passing results to next.
        
        Args:
            agent_ids: List of agent IDs in order
            task: Initial task
            
        Returns:
            Dict of results with chain
        """
        results = {}
        current_context = task
        
        for agent_id in agent_ids:
            # Get messages
            messages = self.comm.get_messages(agent_id)
            
            # Build context with previous results
            context = self._build_context(
                current_context,
                messages,
                results,
            )
            
            # Update status
            self.registry.set_status(agent_id, "busy")
            
            try:
                agent = self.registry.get(agent_id)
                if not agent:
                    results[agent_id] = {"error": f"Agent {agent_id} not found"}
                    continue
                
                # Run agent
                if asyncio.iscoroutinefunction(agent.chat):
                    result = await agent.chat(context)
                else:
                    result = agent.chat(context)
                
                results[agent_id] = {
                    "result": result,
                    "messages_received": len(messages),
                }
                
                # Pass result to next agent
                current_context = f"""Previous agent results:
{agent_id}: {result}

Original task:
{task}
"""
            
            except Exception as e:
                results[agent_id] = {"error": str(e)}
            
            finally:
                self.registry.set_status(agent_id, "online")
        
        return results
    
    async def run_parallel(
        self,
        agent_ids: list[str],
        task: str,
    ) -> dict[str, Any]:
        """Run agents in parallel (concurrently).
        
        Args:
            agent_ids: List of agent IDs
            task: Task for all agents
            
        Returns:
            Dict of results per agent
        """
        # Create tasks
        tasks = [self.run_single(agent_id, task) for agent_id in agent_ids]
        
        # Run all concurrently
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build results dict
        results = {}
        for agent_id, result in zip(agent_ids, results_list):
            if isinstance(result, Exception):
                results[agent_id] = {"error": str(result)}
            else:
                results[agent_id] = result
        
        return results
    
    def _build_context(
        self,
        task: str,
        messages: list[AgentMessage],
        previous_results: Optional[dict[str, Any]] = None,
    ) -> str:
        """Build context prompt for agent.
        
        Args:
            task: Main task
            messages: Messages from other agents
            previous_results: Results from previous agents
            
        Returns:
            Context string for agent
        """
        context = f"""Task: {task}

"""
        
        if messages:
            context += """## Messages from Team Members
"""
            for msg in messages:
                context += f"- {msg.from_agent}: {msg.content}\n"
            context += "\n"
        
        if previous_results:
            context += """## Previous Agent Results
"""
            for agent_id, result in previous_results.items():
                if isinstance(result, dict) and "result" in result:
                    content = str(result["result"])[:500]
                    context += f"- {agent_id}: {content}...\n"
            context += "\n"
        
        return context
    
    def get_available_agents(self) -> list[dict[str, Any]]:
        """Get list of available agents for a task.
        
        Returns:
            List of agent info dicts
        """
        return self.registry.list_agents()
    
    def auto_select_agents(
        self,
        task: str,
        required_roles: Optional[list[str]] = None,
    ) -> list[str]:
        """Auto-select agents based on task.
        
        Args:
            task: Task description
            required_roles: Optional list of required roles
            
        Returns:
            List of agent IDs
        """
        # If specific roles required, use those
        if required_roles:
            agent_ids = []
            for role in required_roles:
                agents = self.registry.find_by_role(role)
                agent_ids.extend(agents)
            return agent_ids
        
        # Otherwise return all online agents
        return self.registry.get_online_agents()
