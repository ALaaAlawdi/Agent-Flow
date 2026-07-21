# 🧠 Agent-Flow v1.0

**Multi-agent AI platform — 21 cognitive capabilities, 83 API endpoints, real DeepSeek-powered agents.**

وكلاء يتكلمون حقيقياً، يتعلمون ذاتياً، يكتشفون أدوارهم، ويتواصلون مع بعضهم البعض.

---

## 🚀 Quick Start

### المتطلبات:

- Python 3.11+
- Node.js 20+
- Git
- [uv](https://docs.astral.sh/uv/) (للتثبيت السريع)
- DeepSeek API key (مجاني)

### التثبيت:

```bash
# 1. حمل المشروع
git clone https://github.com/ALaaAlawdi/Agent-Flow.git
cd Agent-Flow

# 2. ثبت الـ dependencies
uv sync

# 3. أضف الـ API key
echo 'DEEPSEEK_API_KEY=sk-yOUR-kEy-hErE' > .env

# 4. شغّل السيرفر
uv run python production.py
```

**→ http://localhost:8000/docs**

---

### تشغيل الواجهة (Next.js):

```bash
cd frontend
npm install
npm run dev
```

**→ http://localhost:3000**

---

## 📁 هيكل المشروع:

```
Agent-Flow/
├── agent_flow/              # Python backend
│   └── agents/              # 21 قدرة معرفية
│       ├── api/             # FastAPI (83 endpoints)
│       ├── world/           # AgentVerse engine
│       └── hermes_learning_loop.py  # نظام التعلم
├── frontend/                # Next.js UI
│   └── src/app/             # 10 pages
├── tests/                   # 29 unit tests
├── production.py            # Production entrypoint
├── docker-compose.yml       # Docker deployment
└── .env.example             # Environment template
```

---

## 🎨 الصفحات:

| الصفحة | الرابط | الوصف |
|--------|--------|-------|
| 🏠 Dashboard | `/` | إحصائيات + سناريوهات |
| 🧠 Hermes Agents | `/hermes-agents` | وكلاء يتكلمون بـ DeepSeek |
| 🚀 Scenarios | `/scenarios` | 8 سناريوهات جاهزة |
| 🌍 AgentVerse | `/world` | عالم الوكلاء |
| 🤖 Teams | `/teams` | إدارة الفرق |
| 📊 Analytics | `/analytics` | تحليل البيانات |
| ⚙️ Settings | `/settings` | الإعدادات + الموديلز |

---

## 🧪 تشغيل الاختبارات:

```bash
uv run python -W error::ResourceWarning -m unittest discover -s tests -v
```

النتيجة المتوقعة: `29/29 OK`

---

## 🐳 Docker:

```bash
docker compose up -d
# → API: http://localhost:8000
# → UI:  http://localhost:3000
```

---

## 🔑 Environment Variables:

انسخ `.env.example` إلى `.env` واملأ القيم:

```env
# DeepSeek API key
DEEPSEEK_API_KEY=sk-...

# Default model
HERMES_DEFAULT_MODEL=deepseek-v4-pro
HERMES_DEFAULT_PROVIDER=deepseek

# Optional: API key authentication
API_KEY=my-secret-key

# Optional: Rate limiting
RATE_LIMIT_PER_MINUTE=60
```

---

## 🧠 AgentVerse — وكلاء يتكلمون:

```bash
# عبر API
curl http://localhost:8000/agentverse

# نبضة = وكيلان يتكلمان بـ DeepSeek
curl -X POST http://localhost:8000/agentverse/tick?count=5

# أو من الواجهة
open http://localhost:3000/hermes-agents
```

كل وكيل عنده:
- **اسم** (Zain, Noor, Sara)
- **مسمى وظيفي** (Researcher, Developer, Designer)
- **شخصية** (curiosity, talkativity, friendliness)
- **Learning Loop** (ذاكرة + مهارات + تحسين ذاتي)
- **محادثات حقيقية** عبر DeepSeek

---

## 📡 API Documentation:

```bash
open http://localhost:8000/docs
```

### أهم الـ endpoints:

| Method | Path | الوصف |
|--------|------|-------|
| GET | `/health` | صحة السيرفر |
| GET | `/scenarios` | قائمة السناريوهات |
| POST | `/scenarios/{id}/run` | تشغيل سناريو |
| GET | `/teams` | قائمة الفرق |
| POST | `/teams` | إنشاء فريق |
| POST | `/teams/{name}/agents` | إضافة وكيل |
| GET | `/teams/{name}/agents/{id}/learning` | حلقة التعلم |
| GET | `/agentverse` | حالة العالم |
| POST | `/agentverse/tick` | نبضة (محادثة) |
| GET | `/agentverse/conversations` | المحادثات |

---

## 🏗️ الميزات:

- ✅ 21 قدرة معرفية (SuperReasoner, Oracle, Creativity, ...)
- ✅ 83 API endpoint
- ✅ 8 demo scenarios (one-click)
- ✅ وكلاء بـ DeepSeek حقيقي (ليس محاكاة)
- ✅ Hermes Learning Loop (ذاكرة + مهارات + تحسين ذاتي)
- ✅ Next.js 16 UI (10 pages, dark theme, RTL Arabic)
- ✅ SQLite persistence
- ✅ WebSocket real-time
- ✅ Docker Compose
- ✅ API Key authentication
- ✅ Rate limiting
- ✅ 29/29 tests passing

---

## 📖 بناءً على:

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) — self-improving agent runtime
- [DeepSeek](https://deepseek.com) — LLM provider
- [Next.js 16](https://nextjs.org) — frontend framework
- [FastAPI](https://fastapi.tiangolo.com) — backend framework

---

## 📜 License:

MIT

---

## 👤 Author:

[ALaaAlawdi](https://github.com/ALaaAlawdi)
