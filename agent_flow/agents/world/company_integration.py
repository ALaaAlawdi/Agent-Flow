"""
Company Integration — bridges Agent-Flow teams with the AgentVerse world.

Every team/company becomes a location in the world.
Agents at their company location work on tasks.
Agents from different companies can meet and collaborate.
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Optional

from agent_flow.agents.world.engine import WorldEngine, WorldAgent, Position, Location, AgentState
from agent_flow.agents.world.ws import ws_manager, world_manager


class CompanyStore:
    """يحتفظ بجميع الشركات (الفرق) في العالم."""

    def __init__(self):
        self.companies: dict[str, Company] = {}

    def register(self, company: "Company"):
        self.companies[company.name] = company

    def unregister(self, name: str):
        if name in self.companies:
            del self.companies[name]

    def get(self, name: str) -> Optional["Company"]:
        return self.companies.get(name)

    def all(self) -> list["Company"]:
        return list(self.companies.values())


class Company:
    """شركة في العالم — لها موقع، وكلاء، مهام، وحالة."""

    def __init__(
        self,
        name: str,
        description: str,
        world_name: str = "agentverse",
        position: Optional[Position] = None,
    ):
        self.name = name
        self.description = description
        self.world_name = world_name
        self.position = position or Position(
            random.randint(50, 250),
            random.randint(50, 250),
        )
        self.employees: list[str] = []  # agent_ids
        self.active_projects: list[dict] = []
        self.completed_tasks = 0
        self.revenue = 0.0
        self.created_at = time.time()
        self.status = "active"  # active, busy, idle

    def to_location(self) -> Location:
        """تحويل الشركة إلى موقع في العالم."""
        types = {
            "Agent-Flow": "lab",
            "VirtualCorp": "market",
            "Hermes Brain": "library",
            "DataSphere": "workshop",
        }
        loc_type = types.get(self.name, "general")
        return Location(
            id=f"company_{self.name.lower().replace(' ', '_')}",
            name=f"🏢 {self.name}",
            description=self.description,
            position=self.position,
            capacity=20,
            type=loc_type,
            properties={
                "company": True,
                "employees": len(self.employees),
                "status": self.status,
                "projects": len(self.active_projects),
                "tasks_completed": self.completed_tasks,
            },
        )

    def add_employee(self, agent_id: str):
        """إضافة وكيل للشركة."""
        if agent_id not in self.employees:
            self.employees.append(agent_id)

    def remove_employee(self, agent_id: str):
        if agent_id in self.employees:
            self.employees.remove(agent_id)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "position": self.position.as_dict(),
            "employees": self.employees,
            "projects": len(self.active_projects),
            "completed_tasks": self.completed_tasks,
            "revenue": round(self.revenue, 2),
            "status": self.status,
            "created_at": self.created_at,
        }


# Global company store
company_store = CompanyStore()


def create_default_companies(world: WorldEngine):
    """إنشاء الشركات الافتراضية في العالم."""
    companies_data = [
        Company(
            "Agent-Flow",
            "Multi-agent AI platform — builds cognitive architectures",
            position=Position(60, 60),
        ),
        Company(
            "VirtualCorp",
            "AI-driven virtual software company — zero employees",
            position=Position(240, 60),
        ),
        Company(
            "Hermes Brain",
            "3-agent research department powered by Hermes + Obsidian",
            position=Position(60, 240),
        ),
        Company(
            "DataSphere",
            "Data engineering and AI training pipeline",
            position=Position(240, 240),
        ),
    ]

    for company in companies_data:
        company_store.register(company)
        world.add_location(company.to_location())

    return companies_data


async def assign_agents_to_companies(world: WorldEngine):
    """تعيين الوكلاء للشركات بشكل ذكي حسب مهاراتهم."""
    assignments = {
        "agent-1": "Agent-Flow",     # Zain — research
        "agent-2": "VirtualCorp",    # Noor — coding
        "agent-3": "Hermes Brain",   # Sara — design
    }

    for agent_id, company_name in assignments.items():
        agent = world.agents.get(agent_id)
        company = company_store.get(company_name)
        if agent and company:
            company.add_employee(agent_id)
            agent.current_location = f"company_{company_name.lower().replace(' ', '_')}"
            # Start agents near their company
            company_pos = company.position
            agent.position = Position(
                company_pos.x + random.uniform(-15, 15),
                company_pos.y + random.uniform(-15, 15),
            )


def get_agent_company(agent_id: str) -> Optional[Company]:
    """معرفة شركة الوكيل."""
    for company in company_store.all():
        if agent_id in company.employees:
            return company
    return None


def get_company_agents(world: WorldEngine, company_name: str) -> list:
    """معرفة وكلاء شركة معينة في العالم."""
    company = company_store.get(company_name)
    if not company:
        return []
    return [a for a_id, a in world.agents.items() if a_id in company.employees]


def get_nearby_companies(world: WorldEngine, position: Position, range_m: float = 50) -> list[dict]:
    """الشركات القريبة من موقع معين."""
    nearby = []
    for company in company_store.all():
        dist = position.distance_to(company.position)
        if dist <= range_m:
            nearby.append({
                "company": company.name,
                "distance": round(dist, 1),
                "employees": len(company.employees),
                "status": company.status,
            })
    return sorted(nearby, key=lambda x: x["distance"])


async def sync_world_with_companies(world: WorldEngine):
    """مزامنة العالم مع حالة الشركات — تنقل الوكلاء بين العمل والتفاعل."""
    for agent_id, agent in world.agents.items():
        company = get_agent_company(agent_id)
        if not company:
            continue

        # إذا الوكيل قريب من شركته → يشتغل
        dist = agent.position.distance_to(company.position)
        if dist < 20:
            agent.state = AgentState.WORKING
            company.status = "busy"
            # ينجز مهمة كل 10 نبضات
            if world.tick_count % 10 == 0:
                company.completed_tasks += 1
                company.revenue += random.uniform(0.5, 5.0)

                # يرسل رسالة عن إنجازه
                tasks = [
                    f"Just shipped a new feature for {company.name}! 🚀",
                    f"Completed task #{company.completed_tasks} — code merged ✅",
                    f"Optimized the pipeline, saved 30% on token cost 💰",
                    f"New architecture design ready for review 📐",
                ]
                msg = agent.speak(random.choice(tasks), target="nearby")
                world.send_message(msg)
        else:
            # إذا بعيد عن شركته → يستكشف
            agent.state = AgentState.MOVING if agent.state != AgentState.TALKING else agent.state

    # بث التحديثات
    await ws_manager.broadcast(world.world_name or "agentverse", {
        "type": "companies_update",
        "companies": [c.as_dict() for c in company_store.all()],
    })