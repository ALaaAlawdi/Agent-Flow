"""Dynamic Agent Factory - Creates Hermes AIAgent from user config."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

# Hermes imports
from run_agent import AIAgent
from hermes_cli.toolset_validation import validate_platform_toolsets
from hermes_cli.profiles import get_profile_dir


# Default toolset validator - accepts common toolset names
def _default_toolset_validator(toolset: str) -> bool:
    """Default validator that accepts common toolsets."""
    # Common toolsets that might be valid
    common_toolsets = {
        "web", "terminal", "file", "code", "editor",
        "bash", "shell", "cli", "mcp", "gateway",
    }
    # Accept if it's in common toolsets or starts with common prefix
    if toolset.lower() in common_toolsets:
        return True
    # Accept any toolset that looks reasonable (alphanumeric with dashes)
    return toolset.replace("-", "").replace("_", "").isalnum() and len(toolset) > 1


class DynamicAgentFactory:
    """Factory that creates Hermes AIAgent instances from user configuration.
    
    All agent creation is powered by Hermes package - no custom agent logic.
    
    Default model: OpenAI (gpt-4o-mini)
    Supported: Any model in MODEL_REGISTRY below
    """
    
    # Available models - OpenAI is the default
    MODEL_REGISTRY = {
        # OpenAI models (default)
        "gpt-4o": "openai/gpt-4o",
        "gpt-4o-mini": "openai/gpt-4o-mini",
        "gpt-4-turbo": "openai/gpt-4-turbo",
        "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
        "o1-preview": "openai/o1-preview",
        "o1-mini": "openai/o1-mini",
        # Anthropic models (still available)
        "claude-sonnet-4": "anthropic/claude-sonnet-4",
        "claude-opus-4": "anthropic/claude-opus-4",
        "claude-haiku": "anthropic/claude-haiku",
        # Other providers
        "gemini-pro": "google/gemini-pro",
        "llama-3": "meta/llama-3",
    }
    
    DEFAULT_MODEL = "gpt-4o-mini"  # OpenAI default
    
    def __init__(self, network_name: str = "default", default_model: Optional[str] = None):
        """Initialize factory with network name.
        
        Args:
            network_name: Name of the agent network (for storage)
            default_model: Default model for agents (defaults to gpt-4o-mini)
        """
        self.network_name = network_name
        self.default_model = default_model or self.DEFAULT_MODEL
        # get_profile_dir requires 'name' argument
        self.profile_dir = get_profile_dir(network_name) / "networks" / network_name
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Agent configs storage
        self.agents_dir = self.profile_dir / "agents"
        self.agents_dir.mkdir(exist_ok=True)
    
    def create_agent(
        self,
        name: str,
        role: str,
        tools: list[str],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_iterations: int = 50,
        collaborates_with: Optional[list[str]] = None,
    ) -> AIAgent:
        """Create Hermes AIAgent from user configuration.
        
        Args:
            name: Agent name (unique identifier)
            role: Agent role (researcher, coder, etc.)
            tools: List of enabled toolsets (validated via Hermes)
            system_prompt: Custom system instructions
            model: Model to use (default: OpenAI gpt-4o-mini)
                   Can be short name like "gpt-4o" or full "openai/gpt-4o"
            max_iterations: Max iterations (default: 50)
            collaborates_with: List of roles to collaborate with
            
        Returns:
            Hermes AIAgent instance
            
        Raises:
            ValueError: If tools are invalid
        """
        # Resolve model name
        resolved_model = self._resolve_model(model or self.default_model)
        
        # 1. Validate tools using Hermes built-in validation
        warnings = validate_platform_toolsets(tools, _default_toolset_validator)
        # Log warnings if any
        if warnings:
            import logging
            logger = logging.getLogger(__name__)
            for w in warnings:
                logger.warning(f"Toolset warning: {w}")
        
        # 2. Build system prompt from config
        prompt = self._build_prompt(
            name=name,
            role=role,
            system_prompt=system_prompt,
            collaborates_with=collaborates_with or [],
        )
        
        # 3. Create Hermes AIAgent (THE CORE - from run_agent)
        agent = AIAgent(
            session_id=name,  # Use session_id as name
            enabled_toolsets=tools,
            ephemeral_system_prompt=prompt,
            max_iterations=max_iterations,
            model=resolved_model,
            
            # Callbacks for tracking
            tool_progress_callback=self._on_tool_progress,
            step_callback=self._on_step,
        )
        
        # 4. Save config to Hermes profile storage
        config = {
            "name": name,
            "role": role,
            "tools": tools,
            "system_prompt": system_prompt,
            "model": resolved_model,
            "max_iterations": max_iterations,
            "collaborates_with": collaborates_with or [],
        }
        self._save_config(name, config)
        
        return agent
    
    def _resolve_model(self, model: str) -> str:
        """Resolve short model name to full provider/name format.
        
        Args:
            model: Short name (e.g., "gpt-4o") or full name ("openai/gpt-4o")
            
        Returns:
            Full model name with provider prefix
        """
        # If already has provider prefix, use as-is
        if "/" in model:
            return model
        
        # Look up in registry
        if model in self.MODEL_REGISTRY:
            return self.MODEL_REGISTRY[model]
        
        # Default: assume OpenAI
        return f"openai/{model}"
    
    @classmethod
    def list_available_models(cls) -> list[dict]:
        """List all available models."""
        return [
            {
                "short_name": short,
                "full_name": full,
                "provider": full.split("/")[0] if "/" in full else "unknown",
            }
            for short, full in cls.MODEL_REGISTRY.items()
        ]
    
    def _build_prompt(
        self,
        name: str,
        role: str,
        system_prompt: Optional[str],
        collaborates_with: list[str],
    ) -> str:
        """Build system prompt from agent config."""
        prompt = f"""# Agent: {name}
Role: {role}

"""
        
        if system_prompt:
            prompt += f"{system_prompt}\n\n"
        
        prompt += """## Communication
You can message other agents using: @agent-name: your message
Share findings with your team members.
"""
        
        if collaborates_with:
            prompt += f"\n## Team Members\n"
            for collab_role in collaborates_with:
                prompt += f"- {collab_role} (can collaborate when needed)\n"
        
        return prompt
    
    def _save_config(self, agent_name: str, config: dict):
        """Save agent config to Hermes profile directory."""
        agent_dir = self.agents_dir / agent_name
        agent_dir.mkdir(exist_ok=True)
        config_file = agent_dir / "config.json"
        config_file.write_text(json.dumps(config, indent=2))
    
    def load_config(self, agent_name: str) -> Optional[dict]:
        """Load agent config from storage."""
        config_file = self.agents_dir / agent_name / "config.json"
        if config_file.exists():
            return json.loads(config_file.read_text())
        return None
    
    def list_agents(self) -> list[str]:
        """List all saved agent configs."""
        return [d.name for d in self.agents_dir.iterdir() if d.is_dir()]
    
    def delete_agent(self, agent_name: str):
        """Delete agent config and storage."""
        import shutil
        agent_dir = self.agents_dir / agent_name
        if agent_dir.exists():
            shutil.rmtree(agent_dir)
    
    def _on_tool_progress(self, tool_name: str, input_data: Any):
        """Callback for tool progress - can be overridden."""
        pass
    
    def _on_step(self, step_info: dict):
        """Callback for each step - can be overridden."""
        pass
