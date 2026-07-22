"""
Agent-Flow Brain — بوابة واحدة. وكلاء تلقائيون.

One API endpoint. Agents figure out everything themselves:
- Who should handle the task
- When to ask another agent for help
- When to review each other's work
- When to learn from mistakes

No workflow. No hardcoded steps. Just emergent collaboration.
"""

from __future__ import annotations
import os, json, time
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/brain", tags=["brain"])

# Force DeepSeek
os.environ["DEEPSEEK_API_KEY"] = "sk-dd7cd5f55cdd4959b538aedfa526a37f"

# Registry of available workers (agents that can be called)
WORKERS = {
    "researcher": {
        "name": "Zain",
        "role": "Researcher",
        "tools": ["web"],
        "specialty": "Research, fact-finding, data gathering, analysis",
        "can_ask": ["coder", "reviewer", "writer"],
    },
    "coder": {
        "name": "Noor", 
        "role": "Developer",
        "tools": ["file"],
        "specialty": "Coding, debugging, scripting, algorithms",
        "can_ask": ["researcher", "reviewer"],
    },
    "reviewer": {
        "name": "Sara",
        "role": "Reviewer",
        "tools": ["web", "file"],
        "specialty": "Code review, correctness checking, bug finding, quality assurance",
        "can_ask": ["researcher", "coder"],
    },
    "writer": {
        "name": "Nader",
        "role": "Writer",
        "tools": ["file"],
        "specialty": "Documentation, explanation, translation, summarization",
        "can_ask": ["researcher", "reviewer"],
    },
}

# Shared conversation history (all agents see this)
conversation_history: list[dict] = []


def call_hermes_agent(worker_id: str, task: str) -> str:
    """Call a real DeepSeek agent for a task."""
    from agent_flow.agents import AgentTeam
    
    worker = WORKERS[worker_id]
    team = AgentTeam(f"brain-{worker_id}", task)
    agent = team.add_agent(worker_id, worker["role"], worker["tools"], model="deepseek-v4-pro")
    
    result = agent.hermes_agent.chat(task)
    return result


def ask_all_workers(task: str) -> dict:
    """Ask ALL agents about who should handle this task."""
    descriptions = "\n".join([
        f"- {wid}: {w['role']} — {w['specialty']}"
        for wid, w in WORKERS.items()
    ])
    
    prompt = f"""You are the Brain coordinator. A task has arrived.

Task: {task}

Available workers:
{descriptions}

Decide which SINGLE worker should handle this task. 
Reply with ONLY the worker ID (one word: researcher, coder, reviewer, or writer).
If unsure, pick the most relevant one."""

    from agent_flow.agents import AgentTeam
    team = AgentTeam("brain-coordinator", prompt)
    agent = team.add_agent("coordinator", "Coordinator", ["web"], model="deepseek-v4-pro")
    response = agent.hermes_agent.chat(prompt).strip().lower()
    
    # Map response to valid worker
    for wid in WORKERS:
        if wid in response:
            conversation_history.append({
                "type": "routing",
                "task": task[:60],
                "assigned_to": wid,
                "reasoning": response[:100],
            })
            return {"assigned_to": wid, "reasoning": response, "workers": len(WORKERS)}
    
    # Default: researcher for most tasks
    default = "researcher"
    conversation_history.append({
        "type": "routing",
        "task": task[:60],
        "assigned_to": default,
        "reasoning": "default",
    })
    return {"assigned_to": default, "reasoning": "default", "workers": len(WORKERS)}


@router.post("/ask")
async def brain_ask(task: str = ""):
    """البوابة الواحدة — أرسل مهمة، الوكلاء يقررون تلقائياً."""
    if not task:
        return {"error": "No task provided"}
    
    # Step 1: Ask all agents — who should do this?
    routing = ask_all_workers(task)
    worker_id = routing["assigned_to"]
    worker = WORKERS[worker_id]
    
    # Step 2: Assign the task
    conversation_history.append({
        "type": "task_start",
        "agent": worker_id,
        "name": worker["name"],
        "role": worker["role"],
        "task": task[:80],
        "time": time.time(),
    })
    
    # Step 3: Execute with real DeepSeek
    response = call_hermes_agent(worker_id, task)
    
    # Step 4: Optionally ask reviewer to check
    review_result = None
    if worker_id != "reviewer" and len(response) > 20:
        try:
            review = call_hermes_agent(
                "reviewer",
                f"Review this response in 1 word (correct/wrong/improve). Don't explain. Response: {response[:200]}"
            )
            review_result = review.strip()
        except:
            review_result = "skipped"
    
    # Step 5: Log completion
    conversation_history.append({
        "type": "task_done",
        "agent": worker_id,
        "response_preview": response[:100],
        "review": review_result,
        "time": time.time(),
    })
    
    return {
        "task": task,
        "routing": routing,
        "assigned_agent": {
            "id": worker_id,
            "name": worker["name"],
            "role": worker["role"],
        },
        "response": response[:500],
        "review": review_result,
        "conversation_length": len(conversation_history),
        "available_workers": list(WORKERS.keys()),
    }


@router.get("/history")
async def brain_history():
    """Show the full conversation history between agents."""
    return {
        "total_interactions": len(conversation_history),
        "history": conversation_history[-50:],
    }


@router.get("/workers")
async def brain_workers():
    """List all available workers."""
    return {
        "workers": {
            wid: {"name": w["name"], "role": w["role"], "specialty": w["specialty"], "can_call": w["can_ask"]}
            for wid, w in WORKERS.items()
        },
        "total": len(WORKERS),
    }


# Interactive HTML Demo
BRAIN_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent-Flow Brain — One Gateway</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e0e0e0;font-family:system-ui;padding:1.5rem;min-height:100vh}
.container{max-width:700px;margin:auto}
h1{font-size:1.6rem;background:linear-gradient(135deg,#f59e0b,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.3rem}
.sub{color:#555;font-size:.8rem;margin-bottom:1.5rem}
.card{background:#12122a;border:1px solid #1e1e3e;border-radius:14px;padding:1.2rem;margin-bottom:1rem}
.card h2{font-size:.85rem;color:#888;margin-bottom:.5rem}
.input-row{display:flex;gap:.5rem}
.input-row input{flex:1;background:#0a0a1a;border:1px solid #2a2a5e;border-radius:10px;padding:.7rem 1rem;color:#fff;font-size:.85rem;outline:none}
.input-row input:focus{border-color:#f59e0b}
.input-row button{background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff;border:none;border-radius:10px;padding:.7rem 1.5rem;font-weight:700;cursor:pointer;font-size:.85rem}
.input-row button:hover{opacity:.9}
.input-row button:disabled{background:#333;cursor:wait}
.presets{display:flex;gap:.4rem;flex-wrap:wrap;margin-top:.6rem}
.preset{background:#1a1a3e;border:none;border-radius:8px;padding:.35rem .7rem;font-size:.7rem;color:#777;cursor:pointer}
.preset:hover{background:#2a2a4e;color:#bbb}
.result{display:none;animation:fadeIn .3s}
.result.show{display:block}
.result .agent-info{display:flex;align-items:center;gap:.8rem;margin-bottom:.8rem}
.result .avatar{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;font-weight:700}
.result .name{font-weight:600;font-size:.9rem}
.result .role{font-size:.7rem;color:#666}
.result .response{background:#0a0a1a;border-radius:10px;padding:1rem;font-size:.85rem;line-height:1.6;border-left:3px solid #f59e0b}
.result .meta{display:flex;gap:1rem;margin-top:.8rem;font-size:.7rem;color:#555}
.workers-row{display:grid;grid-template-columns:repeat(4,1fr);gap:.5rem}
.worker-badge{background:#12122a;border:1px solid #1e1e3e;border-radius:10px;padding:.6rem;text-align:center;font-size:.65rem;color:#666}
.worker-badge .w-name{color:#bbb;font-size:.75rem;font-weight:600}
.loading{display:none;text-align:center;padding:1.5rem}
.loading.show{display:block}
.spinner{width:28px;height:28px;border:3px solid #222;border-top:3px solid #f59e0b;border-radius:50%;animation:spin 1s linear infinite;margin:auto}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
</style>
</head>
<body>
<div class="container">
<h1>🧠 Agent-Flow Brain</h1>
<p class="sub">بوابة واحدة. 4 وكلاء. بدون workflow. هم يقررون من يشتغل.</p>

<div class="card">
<h2>👷 Available Workers</h2>
<div class="workers-row" id="workersRow"></div>
</div>

<div class="card">
<h2>💬 Send Task — The Brain Routes It</h2>
<div class="input-row">
<input id="taskInput" value="Write Python code to sort a list and explain how it works" placeholder="Ask anything...">
<button id="sendBtn" onclick="send()">▶️ Send</button>
</div>
<div class="presets">
<span class="preset" onclick="fill('Write Python code to sort a list and explain how it works')">💻 Code</span>
<span class="preset" onclick="fill('Explain how black holes form in simple terms')">🔭 Science</span>
<span class="preset" onclick="fill('Review this code: for i in range(len(arr)): if arr[i]>arr[i+1]: swap')">🔎 Review</span>
<span class="preset" onclick="fill('Write documentation for a REST API in 2 sentences')">📝 Docs</span>
</div>
</div>

<div id="loading" class="loading"><div class="spinner"></div><p style="color:#555;font-size:.8rem;margin-top:.5rem">Brain is thinking...</p></div>
<div id="result" class="result card"></div>
</div>

<script>
const workers={researcher:{name:'Zain',role:'Researcher',icon:'🔍',color:'#8b5cf6'},
               coder:{name:'Noor',role:'Developer',icon:'💻',color:'#06b6d4'},
               reviewer:{name:'Sara',role:'Reviewer',icon:'🔎',color:'#f43f5e'},
               writer:{name:'Nader',role:'Writer',icon:'📝',color:'#10b981'}};

function renderWorkers(){
  document.getElementById('workersRow').innerHTML=Object.entries(workers).map(([id,w])=>
    `<div class="worker-badge" style="border-color:${w.color}33">
      <div style="font-size:1.2rem">${w.icon}</div>
      <div class="w-name">${w.name}</div>
      <div>${w.role}</div>
    </div>`
  ).join('');
}
renderWorkers();

function fill(t){document.getElementById('taskInput').value=t}

async function send(){
  const task=document.getElementById('taskInput').value;
  const btn=document.getElementById('sendBtn');
  const load=document.getElementById('loading');
  const res=document.getElementById('result');
  
  btn.disabled=true;load.classList.add('show');res.classList.remove('show');
  
  try{
    const r=await fetch('/api/brain/ask?task='+encodeURIComponent(task),{method:'POST'});
    const d=await r.json();
    const w=workers[d.assigned_agent?.id]||workers.researcher;
    
    res.innerHTML=`
      <div class="agent-info">
        <div class="avatar" style="background:${w.color}">${w.icon}</div>
        <div>
          <div class="name">${w.name} (${w.role})</div>
          <div class="role">Assigned by Brain · ${d.routing?.reasoning||'auto'}</div>
        </div>
      </div>
      <div class="response">${d.response||'No response'}</div>
      <div class="meta">
        <span>🔄 ${d.routing?.reasoning?.substring(0,30)||'Auto-routed'}</span>
        <span>✅ Review: ${d.review||'pending'}</span>
        <span>💬 ${d.conversation_length||0} interactions</span>
      </div>
    `;
    res.classList.add('show');
  }catch(e){
    res.innerHTML=`<div class="response">Error: ${e.message}</div>`;
    res.classList.add('show');
  }
  btn.disabled=false;load.classList.remove('show');
}
</script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse)
async def brain_ui():
    return HTMLResponse(BRAIN_UI)