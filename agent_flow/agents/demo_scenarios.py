"""Demo Scenarios - Pre-built examples that populate data and run agents.

Each scenario:
1. Creates a team
2. Adds agents
3. Runs them on a realistic task
4. Generates rich interaction history

Perfect for: UI demo, testing, onboarding, showcase.
"""

from __future__ import annotations

from typing import Any
import asyncio
from datetime import datetime


class DemoScenario:
    """A demo scenario that runs end-to-end."""
    
    def __init__(
        self,
        scenario_id: str,
        title: str,
        description: str,
        icon: str,
        category: str,
        team_config: dict,
        run_steps: list[dict],
    ):
        self.scenario_id = scenario_id
        self.title = title
        self.description = description
        self.icon = icon
        self.category = category
        self.team_config = team_config
        self.run_steps = run_steps
    
    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "title": self.title,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "team_size": len(self.team_config.get("agents", [])),
            "step_count": len(self.run_steps),
            "estimated_time": f"{len(self.run_steps) * 30}s",
        }


# === PRE-BUILT SCENARIOS ===

SCENARIOS = {
    "research_team": DemoScenario(
        scenario_id="research_team",
        title="فريق البحث العلمي",
        description="فريق من 3 باحثين يحللون موضوعاً معقداً ويتبادلون المعرفة",
        icon="🔬",
        category="research",
        team_config={
            "name": "research-demo",
            "goal": "تحليل تأثير الذكاء الاصطناعي على سوق العمل",
            "agents": [
                {"id": "lead_researcher", "role": "researcher", "tools": ["web"], 
                 "prompt": "أنت باحث رئيسي خبير"},
                {"id": "data_analyst", "role": "analyst", "tools": ["web"],
                 "prompt": "أنت محلل بيانات متخصص"},
                {"id": "writer", "role": "writer", "tools": ["file"],
                 "prompt": "أنت كاتب محتوى محترف"},
            ],
        },
        run_steps=[
            {"action": "decompose", "args": {"goal": "تحليل تأثير الذكاء الاصطناعي"}},
            {"action": "decide", "args": {"decision_type": "lead_researcher", 
                                          "options": ["agent1", "agent2"]}},
            {"action": "create_plan", "args": {"goal": "بحث شامل"}},
            {"action": "message", "from": "lead_researcher", "to": "data_analyst",
             "content": "هل يمكنك جمع إحصائيات عن تأثير AI؟"},
            {"action": "message", "from": "data_analyst", "to": "lead_researcher",
             "content": "سأبدأ البحث الآن"},
            {"action": "message", "from": "data_analyst", "to": "writer",
             "content": "وجدت تقرير مهم عن AI في الوظائف"},
            {"action": "add_task", "args": {"description": "كتابة التقرير النهائي",
                                           "agent": "writer"}},
            {"action": "dream", "agent": "lead_researcher"},
            {"action": "negotiate", "from": "lead_researcher", "to": "writer",
             "resource": "time", "amount": 60, "priority": 8},
            {"action": "complete_task", "agent": "writer"},
            {"action": "request_help", "from": "writer", "to": "team",
             "task": "مراجعة نهائية"},
        ],
    ),
    
    "software_team": DemoScenario(
        scenario_id="software_team",
        title="فريق تطوير البرمجيات",
        description="فريق من 4 مطوّرين يبني تطبيق ويب كاملاً",
        icon="💻",
        category="development",
        team_config={
            "name": "dev-demo",
            "goal": "بناء تطبيق ويب لإدارة المهام",
            "agents": [
                {"id": "architect", "role": "architect", "tools": ["terminal"],
                 "prompt": "أنت مهندس معماري محترف"},
                {"id": "frontend_dev", "role": "coder", "tools": ["terminal"],
                 "prompt": "أنت مطوّر واجهات أمامية"},
                {"id": "backend_dev", "role": "coder", "tools": ["terminal"],
                 "prompt": "أنت مطوّر backend"},
                {"id": "qa_tester", "role": "tester", "tools": ["terminal"],
                 "prompt": "أنت مهندس QA"},
            ],
        },
        run_steps=[
            {"action": "create_plan", "args": {"goal": "تطبيق ويب كامل"}},
            {"action": "message", "from": "architect", "to": "frontend_dev",
             "content": "صممت الـAPI، ابدأ الواجهة"},
            {"action": "message", "from": "architect", "to": "backend_dev",
             "content": "صممت قاعدة البيانات، ابدأ الـendpoints"},
            {"action": "add_task", "args": {"description": "بناء صفحة Login", 
                                           "agent": "frontend_dev"}},
            {"action": "add_task", "args": {"description": "بناء API المستخدمين",
                                           "agent": "backend_dev"}},
            {"action": "message", "from": "frontend_dev", "to": "backend_dev",
             "content": "أي endpoint للدخول؟"},
            {"action": "message", "from": "backend_dev", "to": "frontend_dev",
             "content": "/api/auth/login - سأرسل الـdocs"},
            {"action": "negotiate", "from": "frontend_dev", "to": "backend_dev",
             "resource": "database_access", "amount": 5, "priority": 7},
            {"action": "complete_task", "agent": "frontend_dev"},
            {"action": "complete_task", "agent": "backend_dev"},
            {"action": "add_task", "args": {"description": "اختبار شامل",
                                           "agent": "qa_tester"}},
            {"action": "conflict", "type": "code_style",
             "agents": ["frontend_dev", "backend_dev"]},
            {"action": "dream", "agent": "architect"},
            {"action": "complete_task", "agent": "qa_tester"},
        ],
    ),
    
    "creative_team": DemoScenario(
        scenario_id="creative_team",
        title="فريق الإبداع والتسويق",
        description="فريق إبداعي يصمم حملة تسويقية كاملة",
        icon="🎨",
        category="creative",
        team_config={
            "name": "creative-demo",
            "goal": "تصميم حملة إطلاق منتج جديد",
            "agents": [
                {"id": "creative_director", "role": "creative", "tools": ["web"],
                 "prompt": "أنت مدير إبداعي مبدع"},
                {"id": "copywriter", "role": "writer", "tools": ["file"],
                 "prompt": "أنت كاتب إعلاني"},
                {"id": "designer", "role": "designer", "tools": ["file"],
                 "prompt": "أنت مصمم جرافيك"},
                {"id": "strategist", "role": "analyst", "tools": ["web"],
                 "prompt": "أنت استراتيجي تسويق"},
            ],
        },
        run_steps=[
            {"action": "decompose", "args": {"goal": "حملة إطلاق منتج"}},
            {"action": "message", "from": "creative_director", "to": "strategist",
             "content": "نحتاج تحليل السوق أولاً"},
            {"action": "message", "from": "strategist", "to": "creative_director",
             "content": "وجدت 3 فرص واعدة"},
            {"action": "brainstorm", "agent": "creative_director",
             "topic": "concept ideas"},
            {"action": "message", "from": "creative_director", "to": "copywriter",
             "content": "اكتب شعار للحملة"},
            {"action": "message", "from": "creative_director", "to": "designer",
             "content": "صمم الهوية البصرية"},
            {"action": "dream", "agent": "creative_director"},
            {"action": "message", "from": "copywriter", "to": "designer",
             "content": "الشعار جاهز: Innovate Tomorrow"},
            {"action": "negotiate", "from": "copywriter", "to": "designer",
             "resource": "feedback_time", "amount": 3, "priority": 6},
            {"action": "add_task", "args": {"description": "إنتاج الفيديو الترويجي",
                                           "agent": "designer"}},
        ],
    ),
    
    "support_team": DemoScenario(
        scenario_id="support_team",
        title="فريق خدمة العملاء الذكي",
        description="فريق دعم يعالج طلبات العملاء بسرعة",
        icon="🎧",
        category="support",
        team_config={
            "name": "support-demo",
            "goal": "معالجة طلبات العملاء بكفاءة",
            "agents": [
                {"id": "triage_agent", "role": "coordinator", "tools": ["web"],
                 "prompt": "أنت وكيل تصنيف"},
                {"id": "tech_support", "role": "expert", "tools": ["terminal"],
                 "prompt": "أنت دعم فني"},
                {"id": "billing_support", "role": "expert", "tools": ["file"],
                 "prompt": "أنت دعم الفواتير"},
            ],
        },
        run_steps=[
            {"action": "message", "from": "triage_agent", "to": "tech_support",
             "content": "عميل يواجه مشكلة في API"},
            {"action": "message", "from": "tech_support", "to": "triage_agent",
             "content": "سأبدأ التحقيق"},
            {"action": "message", "from": "triage_agent", "to": "billing_support",
             "content": "عميل يسأل عن الفاتورة"},
            {"action": "message", "from": "billing_support", "to": "triage_agent",
             "content": "تم إرسال الفاتورة"},
            {"action": "decide", "args": {"decision_type": "priority",
                                          "options": ["high", "medium", "low"]}},
            {"action": "add_task", "args": {"description": "إصلاح API call timeout",
                                           "agent": "tech_support"}},
            {"action": "complete_task", "agent": "tech_support"},
            {"action": "dream", "agent": "triage_agent"},
        ],
    ),
    
    "data_science": DemoScenario(
        scenario_id="data_science",
        title="فريق علوم البيانات",
        description="فريق يحلل بيانات ويكتشف أنماطاً",
        icon="📊",
        category="data",
        team_config={
            "name": "data-demo",
            "goal": "تحليل بيانات المبيعات واكتشاف أنماط",
            "agents": [
                {"id": "data_engineer", "role": "engineer", "tools": ["terminal"],
                 "prompt": "أنت مهندس بيانات"},
                {"id": "ml_engineer", "role": "ml_engineer", "tools": ["terminal"],
                 "prompt": "أنت مهندس ML"},
                {"id": "analyst", "role": "analyst", "tools": ["file"],
                 "prompt": "أنت محلل بيانات"},
            ],
        },
        run_steps=[
            {"action": "message", "from": "data_engineer", "to": "analyst",
             "content": "جهزت البيانات - 1M صف"},
            {"action": "message", "from": "analyst", "to": "ml_engineer",
             "content": "وجدت نمط غير عادي"},
            {"action": "message", "from": "ml_engineer", "to": "analyst",
             "content": "سأبني نموذج للتنبؤ"},
            {"action": "decide", "args": {"decision_type": "model_choice",
                                          "options": ["XGBoost", "Neural Net"]}},
            {"action": "add_task", "args": {"description": "تدريب النموذج",
                                           "agent": "ml_engineer"}},
            {"action": "predict", "args": {"metric": "revenue", "horizon": "1m"}},
            {"action": "complete_task", "agent": "ml_engineer"},
            {"action": "dream", "agent": "data_engineer"},
        ],
    ),
    
    "education_team": DemoScenario(
        scenario_id="education_team",
        title="فريق التعليم والتدريب",
        description="فريق يصمم منهجاً تعليمياً تفاعلياً",
        icon="📚",
        category="education",
        team_config={
            "name": "edu-demo",
            "goal": "تصميم دورة Python للمبتدئين",
            "agents": [
                {"id": "curriculum_designer", "role": "designer", "tools": ["file"],
                 "prompt": "أنت مصمم مناهج"},
                {"id": "instructor", "role": "teacher", "tools": ["file"],
                 "prompt": "أنت معلم خبير"},
                {"id": "content_writer", "role": "writer", "tools": ["file"],
                 "prompt": "أنت كاتب محتوى تعليمي"},
            ],
        },
        run_steps=[
            {"action": "create_plan", "args": {"goal": "دورة Python متكاملة"}},
            {"action": "decompose", "args": {"goal": "10 دروس للمبتدئين"}},
            {"action": "message", "from": "curriculum_designer", "to": "instructor",
             "content": "صممت الهيكل، ما رأيك؟"},
            {"action": "message", "from": "instructor", "to": "content_writer",
             "content": "احتاج شرح للمتغيرات والحلقات"},
            {"action": "add_task", "args": {"description": "درس المتغيرات",
                                           "agent": "content_writer"}},
            {"action": "complete_task", "agent": "content_writer"},
            {"action": "dream", "agent": "instructor"},
        ],
    ),
    
    "emergency_response": DemoScenario(
        scenario_id="emergency_response",
        title="فريق الاستجابة للطوارئ",
        description="فريق يتعامل مع أزمة بشكل سريع ومنظم",
        icon="🚨",
        category="emergency",
        team_config={
            "name": "emergency-demo",
            "goal": "التعامل مع انقطاع في الخدمة",
            "agents": [
                {"id": "incident_commander", "role": "coordinator", "tools": ["web"],
                 "prompt": "أنت قائد الحادث"},
                {"id": "tech_lead", "role": "engineer", "tools": ["terminal"],
                 "prompt": "أنت قائد تقني"},
                {"id": "comms_lead", "role": "coordinator", "tools": ["file"],
                 "prompt": "أنت مسؤول التواصل"},
            ],
        },
        run_steps=[
            {"action": "message", "from": "incident_commander", "to": "tech_lead",
             "content": "🚨 انقطاع في الخدمة الرئيسية"},
            {"action": "decide", "args": {"decision_type": "severity",
                                          "options": ["critical", "high", "medium"]}},
            {"action": "add_task", "args": {"description": "تشخيص المشكلة",
                                           "agent": "tech_lead"}, "priority": "urgent"},
            {"action": "message", "from": "incident_commander", "to": "comms_lead",
             "content": "أبلغ العملاء عن الانقطاع"},
            {"action": "message", "from": "tech_lead", "to": "incident_commander",
             "content": "وجدت السبب - database connection pool"},
            {"action": "negotiate", "from": "tech_lead", "to": "incident_commander",
             "resource": "compute", "amount": 10, "priority": 10},
            {"action": "complete_task", "agent": "tech_lead"},
            {"action": "complete_task", "agent": "comms_lead"},
        ],
    ),
    
    "startup_team": DemoScenario(
        scenario_id="startup_team",
        title="فريقStartup ناشئ",
        description="فريقStartup يبني MVP في أسبوع",
        icon="🚀",
        category="startup",
        team_config={
            "name": "startup-demo",
            "goal": "بناء MVP لتطبيق توصيل طعام",
            "agents": [
                {"id": "founder", "role": "coordinator", "tools": ["web"],
                 "prompt": "أنت المؤسس"},
                {"id": "cto", "role": "architect", "tools": ["terminal"],
                 "prompt": "أنت CTO"},
                {"id": "growth_hacker", "role": "marketer", "tools": ["web"],
                 "prompt": "أنت خبير نمو"},
            ],
        },
        run_steps=[
            {"action": "decompose", "args": {"goal": "MVP في أسبوع"}},
            {"action": "message", "from": "founder", "to": "cto",
             "content": "نبدأ بـ React Native للسرعة"},
            {"action": "message", "from": "cto", "to": "founder",
             "content": "موافق، سأبني الـbackend"},
            {"action": "message", "from": "founder", "to": "growth_hacker",
             "content": "استعد لحملة الإطلاق"},
            {"action": "decide", "args": {"decision_type": "tech_stack",
                                          "options": ["React Native", "Flutter"]}},
            {"action": "add_task", "args": {"description": "بناء الـMVP",
                                           "agent": "cto"}},
            {"action": "predict", "args": {"metric": "users", "horizon": "1m"}},
            {"action": "dream", "agent": "founder"},
        ],
    ),
}


class DemoRunner:
    """Runs demo scenarios end-to-end."""
    
    @staticmethod
    def list_scenarios() -> list[dict]:
        """List all available scenarios."""
        return [s.to_dict() for s in SCENARIOS.values()]
    
    @staticmethod
    def get_scenario(scenario_id: str) -> Optional[DemoScenario]:
        """Get a scenario by ID."""
        return SCENARIOS.get(scenario_id)
    
    @staticmethod
    async def run_scenario(scenario_id: str, teams_registry: dict) -> dict:
        """Run a scenario - creates team, agents, and executes steps.
        
        Args:
            scenario_id: Scenario to run
            teams_registry: The teams registry from the API
            
        Returns:
            Result with summary
        """
        scenario = SCENARIOS.get(scenario_id)
        if not scenario:
            return {"error": f"Scenario '{scenario_id}' not found"}
        
        # 1. Create team
        team_name = scenario.team_config["name"]
        
        # If team exists, remove it first
        if team_name in teams_registry:
            del teams_registry[team_name]
        
        from .team import AgentTeam
        team = AgentTeam(
            team_name,
            scenario.team_config["goal"],
        )
        teams_registry[team_name] = team
        
        # 2. Add agents
        agents_added = []
        for agent_config in scenario.team_config["agents"]:
            team.add_agent(
                agent_id=agent_config["id"],
                role=agent_config["role"],
                tools=agent_config["tools"],
                system_prompt=agent_config["prompt"],
            )
            agents_added.append(agent_config["id"])
        
        # 3. Run steps
        executed_steps = []
        
        for step in scenario.run_steps:
            try:
                result = await DemoRunner._execute_step(team, step)
                executed_steps.append({
                    "step": step["action"],
                    "status": "ok",
                    "result": result,
                })
            except Exception as e:
                executed_steps.append({
                    "step": step["action"],
                    "status": "error",
                    "error": str(e),
                })
        
        # 4. Force persistence save
        team.auto_persistence.flush()
        
        # 5. Get final stats
        stats = {
            "interactions": team.get_interaction_statistics(),
            "active_agents": team.get_active_agents(),
        }
        
        return {
            "scenario_id": scenario_id,
            "title": scenario.title,
            "team_name": team_name,
            "agents_added": agents_added,
            "steps_executed": len(executed_steps),
            "successful_steps": len([s for s in executed_steps if s["status"] == "ok"]),
            "stats": stats,
            "executed_steps": executed_steps,
            "message": f"✅ Scenario '{scenario.title}' completed successfully!",
        }
    
    @staticmethod
    async def _execute_step(team, step: dict) -> str:
        """Execute a single step."""
        action = step["action"]
        args = step.get("args", {})
        
        if action == "decompose":
            team.decompose_goal(args.get("goal", ""))
            return f"Goal decomposed: {args.get('goal', '')}"
        
        elif action == "create_plan":
            team.create_plan(args.get("goal", ""))
            return f"Plan created: {args.get('goal', '')}"
        
        elif action == "decide":
            team.decide(
                args.get("decision_type", "default"),
                args.get("options", []),
            )
            return f"Decision made: {args.get('decision_type')}"
        
        elif action == "message":
            team.message_agent(
                step["from"],
                step["to"],
                step["content"],
            )
            return f"Message: {step['from']} → {step['to']}"
        
        elif action == "broadcast":
            team.broadcast(step["from"], step["content"])
            return f"Broadcast from {step['from']}"
        
        elif action == "add_task":
            priority_name = step.get("priority", "normal").upper()
            from .queue import TaskPriority
            priority_map = {
                "low": TaskPriority.LOW,
                "normal": TaskPriority.NORMAL,
                "high": TaskPriority.HIGH,
                "urgent": TaskPriority.URGENT,
            }
            priority = priority_map.get(priority_name.lower(), TaskPriority.NORMAL)
            
            task = team.add_task(
                args.get("description", ""),
                priority=priority,
                assigned_to=args.get("agent"),
            )
            return f"Task added: {args.get('description', '')}"
        
        elif action == "complete_task":
            agent_id = step["agent"]
            # Get the latest task assigned to this agent
            for task in team.queue.tasks.values():
                if task.assigned_agent == agent_id and task.status.value == "in_progress":
                    team.complete_task(task.id, f"Completed by {agent_id}")
                    return f"Task completed by {agent_id}"
            # Fallback: just complete any pending task
            for task in team.queue.tasks.values():
                if task.status.value == "pending":
                    task.assigned_agent = agent_id
                    team.complete_task(task.id, f"Completed by {agent_id}")
                    return f"Task completed by {agent_id}"
            return "No task to complete"
        
        elif action == "fail_task":
            agent_id = step["agent"]
            for task in team.queue.tasks.values():
                if task.assigned_agent == agent_id and task.status.value == "in_progress":
                    team.fail_task(task.id, "Simulated failure")
                    return f"Task failed by {agent_id}"
            return "No task to fail"
        
        elif action == "request_help":
            team.request_help(
                step["from"],
                step.get("task", ""),
                step.get("description", ""),
            )
            return f"Help requested by {step['from']}"
        
        elif action == "negotiate":
            team.negotiate_resource(
                step["from"],
                step["to"],
                step["resource"],
                step.get("amount", 1),
                step.get("priority", 5),
            )
            return f"Negotiation: {step['from']} ↔ {step['to']}"
        
        elif action == "conflict":
            team.resolve_conflict(
                step["type"],
                step["agents"],
                {"scenario": "demo"},
            )
            return f"Conflict resolved: {step['type']}"
        
        elif action == "dream":
            team.dream(step["agent"])
            return f"{step['agent']} dreamed"
        
        elif action == "brainstorm":
            # Use creative engine
            try:
                team.creative.brainstorm_solutions(step.get("topic", ""), num_solutions=3)
            except:
                pass
            return f"{step.get('agent', 'team')} brainstormed"
        
        elif action == "predict":
            # Use oracle
            try:
                team.oracle.detect_trends([1, 2, 3, 4, 5, 6, 7, 8])
            except:
                pass
            return f"Prediction made for {args.get('metric')}"
        
        elif action == "send_thought":
            team.send_thought(
                step["from"],
                step["content"],
            )
            return f"Thought sent by {step['from']}"
        
        elif action == "connect_minds":
            team.connect_minds(step["a"], step["b"], step.get("strength", 0.5))
            return f"Minds connected: {step['a']} ↔ {step['b']}"
        
        elif action == "merge_minds":
            team.merge_minds(step["agents"], step.get("purpose", ""))
            return f"Minds merged"
        
        elif action == "start_conversation":
            team.start_conversation(step["participants"], step.get("topic", ""))
            return f"Conversation started"
        
        elif action == "superposition":
            options = {opt: 1.0/len(step["options"]) for opt in step["options"]}
            team.superposition_decision(step["agent"], step.get("decision_id", "d1"), options)
            return f"Superposition created"
        
        elif action == "snapshot":
            team.snapshot_state({"step": "snapshot"}, args.get("label"))
            return f"State snapshotted"
        
        elif action == "discover_purpose":
            team.discover_purpose(
                step["agent"],
                step.get("experiences", []),
                step.get("values", []),
            )
            return f"{step['agent']} discovered purpose"
        
        return f"Unknown action: {action}"