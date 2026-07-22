"""LIVE Demo API — agents execute in real-time, visible output."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/live", tags=["live"])


@router.post("/execute")
async def live_execute(task: str = "Explain AI in one sentence"):
    """Run a REAL agent task with DeepSeek and return the result."""
    import os
    os.environ["DEEPSEEK_API_KEY"] = os.getenv("DEEPSEEK_API_KEY", "")

    from agent_flow.agents import AgentTeam
    from agent_flow.agents.hermes_auto_wire import on_agent_created, on_agent_speak, on_task_created
    
    # Create a quick team
    team = AgentTeam("live-demo", task)
    agent = team.add_agent("demo-agent", "AI Agent", ["web"], model="deepseek-v4-pro")
    
    on_agent_created(agent.id, agent.display_name, agent.role)
    on_task_created(task)
    
    # Execute REAL DeepSeek call
    result = agent.hermes_agent.chat(task)
    
    on_agent_speak(agent.id, agent.display_name, result)
    
    return {
        "agent": agent.display_name,
        "role": agent.role,
        "task": task,
        "response": result[:500],
        "learning_loop": agent.learning_loop.summary(),
    }


LIVE_DEMO_HTML = """<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="UTF-8">
<title>Agent-Flow Live Demo</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f0f23;color:#e0e0e0;font-family:system-ui,sans-serif;padding:2rem;max-width:700px;margin:auto}
h1{font-size:1.8rem;background:linear-gradient(135deg,#8b5cf6,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.5rem}
.sub{color:#666;margin-bottom:2rem;font-size:.9rem}
.task-bar{display:flex;gap:.5rem;margin-bottom:1.5rem}
.task-bar input{flex:1;background:#1a1a3e;border:1px solid #2a2a5e;border-radius:12px;padding:.8rem 1rem;color:#fff;font-size:.9rem;outline:none}
.task-bar input:focus{border-color:#8b5cf6}
.task-bar button{background:#8b5cf6;color:#fff;border:none;border-radius:12px;padding:.8rem 1.5rem;font-size:.9rem;cursor:pointer;font-weight:600;transition:.2s}
.task-bar button:hover{background:#7c3aed}
.task-bar button:disabled{background:#333;cursor:wait}
.presets{display:flex;gap:.4rem;flex-wrap:wrap;margin-bottom:1.5rem}
.preset{background:#1a1a3e;border:1px solid #2a2a5e;border-radius:8px;padding:.4rem .8rem;font-size:.75rem;color:#888;cursor:pointer;transition:.2s}
.preset:hover{background:#2a2a5e;color:#fff}
.result{background:#1a1a3e;border:1px solid #2a2a5e;border-radius:16px;padding:1.5rem;margin-top:1rem;display:none}
.result.show{display:block;animation:fadeIn .3s}
.result .agent{display:flex;align-items:center;gap:.8rem;margin-bottom:1rem}
.result .avatar{width:40px;height:40px;border-radius:12px;background:#8b5cf6;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:1.2rem}
.result .role{color:#888;font-size:.8rem}
.result .response{color:#d0d0d0;font-size:.95rem;line-height:1.6;padding:1rem;background:#0f0f23;border-radius:10px;border-left:3px solid #8b5cf6}
.result .meta{display:flex;gap:1.5rem;margin-top:1rem;font-size:.75rem;color:#666}
.loading{display:none;text-align:center;padding:2rem}
.loading.show{display:block}
.spinner{display:inline-block;width:30px;height:30px;border:3px solid #333;border-top:3px solid #8b5cf6;border-radius:50%;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;margin-top:1rem;font-size:.75rem}
.stat{background:#0f0f23;border-radius:8px;padding:.6rem;text-align:center}
.stat .val{color:#8b5cf6;font-size:1.1rem;font-weight:700}
.stat .lbl{color:#666;font-size:.7rem}
</style>
</head>
<body>
<h1>🧠 Agent-Flow Live</h1>
<p class="sub">وكلاء حقيقيون بـ DeepSeek — اضغط وهم يتكلمون</p>

<div class="task-bar">
<input id="task" placeholder="Ask the agent anything..." value="Explain how AI agents learn from mistakes in 2 sentences">
<button id="run" onclick="execute()">▶️ Run</button>
</div>

<div class="presets">
<span class="preset" onclick="fill('Explain how AI agents learn from mistakes in 2 sentences')">🧠 التعلم</span>
<span class="preset" onclick="fill('What is context engineering in 2 sentences')">🔧 Context</span>
<span class="preset" onclick="fill('Compare DeepSeek vs OpenAI in one sentence')">🤖 LLMs</span>
<span class="preset" onclick="fill('Write a Python function to sort a list')">💻 Code</span>
<span class="preset" onclick="fill('What is the future of multi-agent systems')">🏢 Multi-Agent</span>
</div>

<div id="loading" class="loading"><div class="spinner"></div><p style="color:#666;margin-top:1rem">🤖 Agent is thinking...</p></div>

<div id="result" class="result">
<div class="agent">
<div class="avatar">🤖</div>
<div><strong id="agentName">Agent-Flow</strong><br><span class="role" id="agentRole">AI Agent</span></div>
</div>
<div class="response" id="agentResponse"></div>
<div class="meta">
<span>⚡ DeepSeek v4-pro</span>
<span id="respTime"></span>
</div>
<div class="stats">
<div class="stat"><div class="val" id="skills">0</div><div class="lbl">Skills</div></div>
<div class="stat"><div class="val" id="memories">0</div><div class="lbl">Memories</div></div>
<div class="stat"><div class="val" id="tasks">0</div><div class="lbl">Tasks</div></div>
<div class="stat"><div class="val" id="tick">0</div><div class="lbl">Tick</div></div>
</div>
</div>

<script>
function fill(t){document.getElementById('task').value=t}
async function execute(){
  const task=document.getElementById('task').value;
  const btn=document.getElementById('run');
  const load=document.getElementById('loading');
  const res=document.getElementById('result');
  
  btn.disabled=true; load.classList.add('show'); res.classList.remove('show');
  const start=Date.now();
  
  try{
    const r=await fetch('/api/live/execute?task='+encodeURIComponent(task),{method:'POST'});
    const d=await r.json();
    
    document.getElementById('agentName').textContent=d.agent;
    document.getElementById('agentRole').textContent=d.role;
    document.getElementById('agentResponse').textContent=d.response;
    document.getElementById('respTime').textContent='⏱ '+(Date.now()-start)/1000+'s';
    
    const ll=d.learning_loop||{};
    document.getElementById('skills').textContent=ll.total_skills||0;
    document.getElementById('memories').textContent=ll.memory_items||0;
    document.getElementById('tasks').textContent=ll.tasks_completed||0;
    document.getElementById('tick').textContent=ll.iteration||0;
    
    res.classList.add('show');
  }catch(e){
    document.getElementById('agentResponse').textContent='Error: '+e.message;
    res.classList.add('show');
  }
  btn.disabled=false; load.classList.remove('show');
}
execute();
</script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse)
async def live_demo_ui():
    return HTMLResponse(LIVE_DEMO_HTML)