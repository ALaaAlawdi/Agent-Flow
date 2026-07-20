"""CLI for Agent Team System."""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Optional

from agent_flow.agents.team import AgentTeam


class TeamCLI:
    """Command-line interface for agent teams."""
    
    def __init__(self):
        self.teams: dict[str, AgentTeam] = {}
    
    def create_team(self, name: str, goal: str = "") -> AgentTeam:
        """Create a new team."""
        team = AgentTeam(name, goal)
        self.teams[name] = team
        print(f"✓ Created team: {name}")
        if goal:
            print(f"  Goal: {goal}")
        return team
    
    def add_agent(
        self,
        team_name: str,
        agent_id: str,
        role: str,
        tools: list[str],
        system_prompt: str = "",
    ):
        """Add agent to team."""
        if team_name not in self.teams:
            print(f"✗ Team not found: {team_name}")
            return
        
        team = self.teams[team_name]
        team.add_agent(agent_id, role, tools, system_prompt)
        print(f"✓ Added {agent_id} ({role}) to team {team_name}")
    
    def set_goal(self, team_name: str, goal: str):
        """Set team goal."""
        if team_name not in self.teams:
            print(f"✗ Team not found: {team_name}")
            return
        
        self.teams[team_name].set_goal(goal)
        print(f"✓ Set goal for {team_name}: {goal}")
    
    def add_knowledge(self, team_name: str, key: str, value: str):
        """Add shared knowledge."""
        if team_name not in self.teams:
            print(f"✗ Team not found: {team_name}")
            return
        
        self.teams[team_name].add_knowledge(key, value)
        print(f"✓ Added knowledge: {key}")
    
    def run_task(self, team_name: str, task: str, mode: str = "collaborative"):
        """Run a task with the team."""
        if team_name not in self.teams:
            print(f"✗ Team not found: {team_name}")
            return
        
        team = self.teams[team_name]
        
        print(f"\n🚀 Running task with team {team_name}...")
        print(f"   Task: {task[:100]}...")
        print(f"   Mode: {mode}")
        print()
        
        if mode == "sequential":
            result = team.run_sequential(task)
        else:
            result = team.run_collaborative(task)
        
        print("\n📊 Results:")
        for agent_id, res in result.get("results", {}).items():
            role = res.get("role", "unknown")
            status = res.get("status", "unknown")
            print(f"\n  [{agent_id}] ({role}) - {status}")
            
            if "result" in res:
                print(f"  {str(res['result'])[:300]}...")
            elif "error" in res:
                print(f"  Error: {res['error'][:200]}")
        
        return result
    
    def status(self, team_name: str):
        """Show team status."""
        if team_name not in self.teams:
            print(f"✗ Team not found: {team_name}")
            return
        
        team = self.teams[team_name]
        status = team.get_team_status()
        
        print(f"\n📋 Team: {status['name']}")
        print(f"   Goal: {status['goal']}")
        print(f"\n👥 Agents ({len(status['agents'])}):")
        for agent in status['agents']:
            print(f"   - {agent['id']} ({agent['role']})")
            print(f"     Tasks: {agent['tasks_completed']} completed, {agent['tasks_failed']} failed")
            perf = agent.get('performance', {})
            if perf:
                print(f"     Success rate: {perf.get('success_rate', 0)*100:.1f}%")
        
        if status.get('goals'):
            print(f"\n🎯 Goals:")
            for goal in status['goals']:
                print(f"   - {goal.get('goal', '')}")
        
        if status.get('knowledge'):
            print(f"\n📚 Knowledge ({len(status['knowledge'])} items):")
            for key in status['knowledge'][:5]:
                print(f"   - {key}")
    
    def learning(self, team_name: str):
        """Show team learning."""
        if team_name not in self.teams:
            print(f"✗ Team not found: {team_name}")
            return
        
        team = self.teams[team_name]
        learning = team.get_learning()
        
        print(f"\n📈 Learning for team {team_name}:")
        for agent_id, data in learning.items():
            print(f"\n  Agent: {agent_id}")
            perf = data.get('performance', {})
            print(f"    Success rate: {perf.get('success_rate', 0)*100:.1f}%")
            print(f"    Total tasks: {perf.get('total_tasks', 0)}")
            
            suggestions = data.get('suggestions', [])
            if suggestions:
                print(f"    Suggestions:")
                for s in suggestions:
                    print(f"      - {s}")
    
    def message(self, team_name: str, from_id: str, to_id: str, content: str):
        """Send message between agents."""
        if team_name not in self.teams:
            print(f"✗ Team not found: {team_name}")
            return
        
        self.teams[team_name].message_agent(from_id, to_id, content)
        print(f"✓ Message sent from {from_id} to {to_id}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Agent Team CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create team
    create_parser = subparsers.add_parser("create", help="Create a new team")
    create_parser.add_argument("name", help="Team name")
    create_parser.add_argument("--goal", "-g", help="Team goal", default="")
    
    # Add agent
    add_parser = subparsers.add_parser("add", help="Add agent to team")
    add_parser.add_argument("team", help="Team name")
    add_parser.add_argument("agent_id", help="Agent ID")
    add_parser.add_argument("role", help="Agent role")
    add_parser.add_argument("tools", help="Comma-separated tools")
    add_parser.add_argument("--prompt", "-p", help="System prompt", default="")
    
    # Set goal
    goal_parser = subparsers.add_parser("goal", help="Set team goal")
    goal_parser.add_argument("team", help="Team name")
    goal_parser.add_argument("goal", help="Goal description")
    
    # Add knowledge
    knowledge_parser = subparsers.add_parser("knowledge", help="Add shared knowledge")
    knowledge_parser.add_argument("team", help="Team name")
    knowledge_parser.add_argument("key", help="Knowledge key")
    knowledge_parser.add_argument("value", help="Knowledge value")
    
    # Run task
    run_parser = subparsers.add_parser("run", help="Run task with team")
    run_parser.add_argument("team", help="Team name")
    run_parser.add_argument("task", help="Task description")
    run_parser.add_argument("--mode", "-m", choices=["collaborative", "sequential"], 
                          default="collaborative", help="Execution mode")
    
    # Status
    status_parser = subparsers.add_parser("status", help="Show team status")
    status_parser.add_argument("team", help="Team name")
    
    # Learning
    learning_parser = subparsers.add_parser("learning", help="Show team learning")
    learning_parser.add_argument("team", help="Team name")
    
    # Message
    msg_parser = subparsers.add_parser("message", help="Send message between agents")
    msg_parser.add_argument("team", help="Team name")
    msg_parser.add_argument("from_", help="From agent ID")
    msg_parser.add_argument("to", help="To agent ID")
    msg_parser.add_argument("content", help="Message content")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = TeamCLI()
    
    if args.command == "create":
        cli.create_team(args.name, args.goal)
    
    elif args.command == "add":
        tools = args.tools.split(",")
        cli.add_agent(args.team, args.agent_id, args.role, tools, args.prompt)
    
    elif args.command == "goal":
        cli.set_goal(args.team, args.goal)
    
    elif args.command == "knowledge":
        cli.add_knowledge(args.team, args.key, args.value)
    
    elif args.command == "run":
        cli.run_task(args.team, args.task, args.mode)
    
    elif args.command == "status":
        cli.status(args.team)
    
    elif args.command == "learning":
        cli.learning(args.team)
    
    elif args.command == "message":
        cli.message(args.team, args.from_, args.to, args.content)


if __name__ == "__main__":
    main()
