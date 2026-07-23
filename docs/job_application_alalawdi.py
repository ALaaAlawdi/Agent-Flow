"""
Job Application — علاء الدين العودي
AI/ML Engineer — Saudi Arabia
"""

# ============================================
# 📄 Professional CV Summary
# ============================================
CV = """
ALA'A AL-DIN AL-AWDI
=====================
Riyadh, Saudi Arabia | Alawdisoft@gmail.com | +966-5X-XXX-XXXX
GitHub: github.com/ALaaAlawdi | LinkedIn: linkedin.com/in/alaa-alawdi

SUMMARY
-------
AI/ML Engineer with deep expertise in building multi-agent AI systems, LLM integration,
and production-grade AI applications. Creator of Agent-Flow — an open-source multi-agent
platform with 70+ API endpoints, 56 tests, and 7 autonomous AI agents. Experienced with
Hermes Agent, DeepSeek, OpenAI, FastAPI, Next.js, and Docker.

TECHNICAL SKILLS
----------------
• AI/ML: LLMs, RAG, Multi-Agent Systems, Learning Loops, DeepSeek, OpenAI, Hermes Agent
• Backend: Python, FastAPI, REST APIs, Docker, SQLite, PostgreSQL
• Frontend: Next.js, TypeScript, React, Tailwind CSS
• Tools: Git, Docker Compose, CI/CD, Unit Testing
• Languages: Arabic (native), English (professional)

PROJECTS
--------
Agent-Flow (2026) — github.com/ALaaAlawdi/Agent-Flow
• Built open-source multi-agent platform with 7 AI agents (Founder, Researcher, Coder,
  Reviewer, Writer, Skeptic, Archivist)
• Integrated Hermes Agent closed learning loop — agents learn from mistakes automatically
• 70+ API endpoints, 65+ Hermes CLI integrations, 56 passing tests
• Real-time agent collaboration with DeepSeek v4-pro LLM execution

Hermes Brain (2026) — github.com/ALaaAlawdi/hermes-brain
• Multi-agent research department with Obsidian knowledge base
• Automated research pipelines with 3 specialized Hermes profiles

VirtualCorp (2026) — AI-powered virtual company
• 8-department AI company simulation with autonomous agents

EDUCATION
---------
AI Engineering & Cybersecurity — [University, Saudi Arabia]
• Focus on multi-agent systems, LLM architectures, and autonomous AI

CERTIFICATIONS
--------------
• DeepSeek API Integration
• Hermes Agent Platform
• Docker & Container Orchestration
"""

# ============================================
# 📝 Cover Letter Template
# ============================================
COVER_LETTER = """
Subject: Application for {position} — Alaa Al-Din Al-Awdi

Dear Hiring Team at {company},

I am excited to apply for the {position} role at {company}. As an AI Engineer
specializing in multi-agent systems and LLM integration, I believe my experience
building real-world AI products aligns perfectly with your needs.

Key highlights:
• Built Agent-Flow: an open-source multi-agent platform with 7 autonomous AI agents
  that research, code, review, and learn — all powered by DeepSeek LLM
• 70+ production API endpoints with 56 passing tests
• Deep integration with Hermes Agent's closed learning loop — agents self-improve
  through autonomous skill creation and memory curation
• Full-stack: FastAPI, Next.js, Docker, TypeScript, Python

I am particularly drawn to {company}'s work in AI and would love to contribute
my experience building production AI systems that actually learn and improve.

My GitHub: github.com/ALaaAlawdi
Portfolio includes Agent-Flow, Hermes Brain, and VirtualCorp.

I would welcome the opportunity to discuss how I can contribute to your team.

Best regards,
Alaa Al-Din Al-Awdi
Alawdisoft@gmail.com
Riyadh, Saudi Arabia
"""

# ============================================
# 🎯 Job Applications
# ============================================
APPLICATIONS = [
    {
        "company": "Mozn",
        "position": "AI Engineer",
        "location": "Riyadh",
        "link": "https://www.linkedin.com/jobs/view/ai-engineer-at-mozn-",
        "status": "ready",
    },
    {
        "company": "Tamm",
        "position": "AI Solution Engineer", 
        "location": "Riyadh",
        "link": "https://www.linkedin.com/jobs/view/ai-solution-engineer-at-tamm-",
        "status": "ready",
    },
    {
        "company": "Uxbert",
        "position": "AI Engineer",
        "location": "Riyadh",
        "link": "https://www.linkedin.com/jobs/view/ai-engineer-at-uxbert-",
        "status": "ready",
    },
]

if __name__ == "__main__":
    print("📄 CV for Alaa Al-Din Al-Awdi")
    print(CV[:300] + "...")
    print()
    print("📝 Cover Letter")
    print(CONTENT_LETTER[:200] + "...")
    print()
    print(f"🎯 {len(APPLICATIONS)} applications ready!")
