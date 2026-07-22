"""
Agent-Flow Telegram Gateway — تحدث مع وكلائك من Telegram.

Commands:
/start — بدء المحادثة مع Agent-Flow
/agents — عرض الوكلاء النشطين
/task — إنشاء مهمة جديدة
/status — حالة المشروع
/talk — محادثة مباشرة مع DeepSeek
/kanban — عرض لوحة المهام
/learn — عرض ما تعلمه الوكلاء
"""

from __future__ import annotations

import os
import json
import time
import subprocess
from typing import Optional

# Telegram bot token (set via env or param)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


def send_message(chat_id: str, text: str) -> dict:
    """Send a message to Telegram chat."""
    if not TOKEN:
        return {"error": "No TELEGRAM_BOT_TOKEN set"}
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        import urllib.request
        import urllib.parse
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }).encode()
        req = urllib.request.Request(url, data=data)
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def get_updates(offset: int = 0) -> list[dict]:
    """Get recent updates from Telegram."""
    if not TOKEN:
        return []
    
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=30"
    try:
        import urllib.request
        resp = urllib.request.urlopen(url, timeout=35)
        data = json.loads(resp.read().decode())
        return data.get("result", [])
    except Exception:
        return []


class AgentFlowTelegramBot:
    """Telegram bot that talks to Agent-Flow agents."""

    def __init__(self, token: str = ""):
        global TOKEN
        self.token = token or TOKEN or os.getenv("TELEGRAM_BOT_TOKEN", "")
        TOKEN = self.token
        
        # Dependencies loaded lazily
        self.team = None
        self.agents = {}
        
    def _ensure_agents(self):
        """Lazy-load agents."""
        if self.team:
            return
        
        from agent_flow.agents import AgentTeam
        self.team = AgentTeam("telegram-team", "Help users from Telegram")
        
        # Add default agents
        for cfg in [
            ("bot-researcher", "Researcher", ["web"]),
            ("bot-coder", "Developer", ["file"]),
            ("bot-writer", "Writer", ["file"]),
        ]:
            agent = self.team.add_agent(cfg[0], cfg[1], cfg[2], model="deepseek-v4-pro")
            self.agents[cfg[0]] = agent

    def handle_command(self, command: str, chat_id: str, args: str = "") -> str:
        """Process a Telegram command."""
        cmd = command.lower().replace("/", "")

        if cmd == "start":
            return (
                "🧠 *Agent-Flow Telegram Bot*\n\n"
                "أهلاً! أنا متصل بـ Agent-Flow.\n\n"
                "الأوامر:\n"
                "/agents — عرض الوكلاء\n"
                "/task — إنشاء مهمة\n"
                "/talk — دردشة مع DeepSeek\n"
                "/kanban — لوحة المهام\n"
                "/status — حالة النظام\n"
                "/learn — ما تعلمه الوكلاء"
            )

        elif cmd == "agents":
            self._ensure_agents()
            lines = ["🤖 *الوكلاء النشطين:*\n"]
            for id, agent in self.agents.items():
                lines.append(f"• {agent.display_name} — {agent.role}")
            lines.append(f"\nالإجمالي: {len(self.agents)} وكلاء")
            return "\n".join(lines)

        elif cmd == "task":
            if not args:
                return "📋 استخدم: `/task وصف المهمة`\nمثال: `/task Build landing page`"
            
            self._ensure_agents()
            from agent_flow.agents.hermes_auto_wire import on_task_created
            task_id = on_task_created(args)
            return f"✅ *تم إنشاء المهمة!*\n📋 {args}\n🆔 {task_id}"

        elif cmd == "talk":
            if not args:
                return "💬 استخدم: `/talk سؤالك`\nمثال: `/talk What is AI?`"
            
            self._ensure_agents()
            agent = list(self.agents.values())[0]
            try:
                response = agent.hermes_agent.chat(args)
                return f"🤖 *{agent.display_name}*:\n{response[:300]}"
            except Exception as e:
                return f"❌ خطأ: {e}"

        elif cmd == "kanban":
            from agent_flow.agents.hermes_cli_api import kanban_tasks
            tasks = list(kanban_tasks.values())
            if not tasks:
                return "📋 لا توجد مهام حالياً.\nأنشئ مهمة: `/task وصف المهمة`"
            
            lines = [f"📋 *Kanban Board* ({len(tasks)} مهام):\n"]
            for t in tasks[:8]:
                emoji = {"todo": "⏳", "in_progress": "🔄", "done": "✅", "blocked": "🚫"}.get(t.status, "❓")
                lines.append(f"{emoji} {t.title[:40]}")
                if t.assignee:
                    lines[-1] += f" — 👤 {t.assignee}"
            return "\n".join(lines)

        elif cmd == "status":
            from agent_flow.agents.hermes_auto_wire import get_full_hermes_state
            state = get_full_hermes_state()
            return (
                "📊 *Agent-Flow Status:*\n\n"
                f"📊 Sessions: {state['sessions']['total']} ({state['sessions']['active']} active)\n"
                f"📋 Tasks: {state['kanban']['total']}\n"
                f"🧠 Memory: {state['memory']['total_items']} items\n"
                f"📈 Events: {state['insights']['total_events']}\n"
                f"🎓 Learning: {state['learning']['total_events']} events"
            )

        elif cmd == "learn":
            from agent_flow.agents.hermes_cli_api import learning_events
            recent = learning_events[-5:] if learning_events else []
            if not recent:
                return "🎓 لا توجد أحداث تعلم بعد."
            lines = ["🎓 *آخر ما تعلمه الوكلاء:*\n"]
            for e in recent:
                lines.append(f"• {e['event'][:80]}")
            return "\n".join(lines)

        else:
            return f"❓ أمر غير معروف: /{cmd}\nاكتب /start للمساعدة"

    def poll(self, process_one: bool = True):
        """Poll Telegram for new messages and respond."""
        if not self.token:
            return "No token configured"

        updates = get_updates()
        handled = 0

        for update in updates:
            msg = update.get("message", {})
            text = msg.get("text", "")
            chat_id = str(msg.get("chat", {}).get("id", ""))

            if not text or not chat_id:
                continue

            handled += 1

            # Parse command
            if text.startswith("/"):
                parts = text.split(" ", 1)
                cmd = parts[0]
                args = parts[1] if len(parts) > 1 else ""
                response = self.handle_command(cmd, chat_id, args)
                send_message(chat_id, response)

            if process_one:
                break

        return f"Processed {handled} messages"


# Quick test
if __name__ == "__main__":
    print("🤖 Agent-Flow Telegram Bot")
    print("=========================")
    print(f"Token: {'SET' if TOKEN else 'NOT SET — export TELEGRAM_BOT_TOKEN=...'}")
    print()
    
    if not TOKEN:
        print("💡 To use: first create a bot with @BotFather on Telegram")
        print("   Then: export TELEGRAM_BOT_TOKEN='your_token_here'")
    else:
        bot = AgentFlowTelegramBot()
        bot._ensure_agents()
        print(f"✅ Connected! {len(bot.agents)} agents ready.")
        print(f"   Send /start to your bot on Telegram to begin.")