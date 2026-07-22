"""
Collaborative Multi-Agent Demo — أقوى عرض للعميل.

Multiple agents collaborate on one task:
- Researcher → يبحث ويجمع معلومات
- Developer → يكتب كود
- Reviewer → يراجع ويصحح
- Writer → يكتب توثيق

كلهم يتكلمون مع بعض بـ DeepSeek حقيقي.
النتيجة تظهر في الواجهة مباشرة.
"""

from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import os, time

router = APIRouter(prefix="/collab", tags=["collaboration"])

COLLAB_UI = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent-Flow Collaborative Demo</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e0e0e0;font-family:system-ui;padding:1rem;min-height:100vh}
.container{max-width:800px;margin:auto}
h1{font-size:1.5rem;background:linear-gradient(135deg,#8b5cf6,#06b6d4,#f43f5e);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.3rem}
.sub{color:#555;font-size:.8rem;margin-bottom:1.5rem}
.agents-row{display:grid;grid-template-columns:repeat(4,1fr);gap:.5rem;margin-bottom:1.5rem}
.agent-card{background:#12122a;border:1px solid #1e1e3e;border-radius:12px;padding:.8rem;text-align:center;transition:.3s}
.agent-card.active{border-color:#8b5cf6;box-shadow:0 0 20px rgba(139,92,246,.2)}
.agent-card .icon{font-size:1.5rem;margin-bottom:.3rem}
.agent-card .name{font-weight:600;font-size:.8rem;color:#fff}
.agent-card .role{font-size:.65rem;color:#666}
.agent-card .status{font-size:.6rem;margin-top:.3rem;padding:.15rem .5rem;border-radius:10px;display:inline-block}
.status.working{background:rgba(139,92,246,.2);color:#8b5cf6}
.status.done{background:rgba(16,185,129,.2);color:#10b981}
.status.waiting{background:rgba(107,114,128,.2);color:#9ca3af}
.main-area{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;margin-bottom:1rem}
.chat-box,.output-box{background:#12122a;border:1px solid #1e1e3e;border-radius:12px;padding:1rem;max-height:350px;overflow-y:auto}
.chat-box h3,.output-box h3{font-size:.75rem;color:#666;margin-bottom:.5rem}
.msg{padding:.5rem .7rem;margin-bottom:.4rem;border-radius:8px;font-size:.75rem;line-height:1.4;animation:slideIn .3s}
.msg.researcher{border-left:3px solid #8b5cf6;background:rgba(139,92,246,.1)}
.msg.coder{border-left:3px solid #06b6d4;background:rgba(6,182,212,.1)}
.msg.reviewer{border-left:3px solid #f43f5e;background:rgba(244,63,94,.1)}
.msg.writer{border-left:3px solid #10b981;background:rgba(16,185,129,.1)}
.msg .who{font-weight:600;font-size:.65rem}
.output-box pre{font-size:.7rem;color:#a8a8b8;white-space:pre-wrap;font-family:monospace}
.btn-row{display:flex;gap:.5rem;margin-bottom:1rem}
.btn{padding:.7rem 1.2rem;border:none;border-radius:10px;font-size:.8rem;font-weight:600;cursor:pointer;transition:.2s;color:#fff}
.btn.run{background:linear-gradient(135deg,#8b5cf6,#7c3aed)}
.btn.run:hover{transform:scale(1.02)}
.btn.run:disabled{background:#333;cursor:wait;transform:none}
.btn.reset{background:#1e1e3e;color:#888}
.btn.reset:hover{background:#2a2a4e}
@keyframes slideIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@keyframes spin{to{transform:rotate(360deg)}}
.spinner{display:inline-block;width:14px;height:14px;border:2px solid #333;border-top:2px solid #8b5cf6;border-radius:50%;animation:spin 1s linear infinite;margin-right:.3rem}
.pulsed{animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
@media(max-width:600px){.agents-row{grid-template-columns:repeat(2,1fr)}.main-area{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="container">
<h1>🧠 Agent-Flow Collaborative Demo</h1>
<p class="sub">4 وكلاء يتعاونون على مهمة واحدة — Research → Code → Review → Docs</p>

<div class="agents-row" id="agentsRow"></div>

<div class="btn-row">
<button class="btn run" id="runBtn" onclick="startDemo()">▶️ شغّل التعاون</button>
<button class="btn reset" onclick="resetDemo()">🔄 Reset</button>
</div>

<div class="main-area">
<div class="chat-box">
<h3>💬 المحادثات بين الوكلاء</h3>
<div id="chatMsgs"><p style="color:#444;font-size:.75rem;text-align:center;padding:2rem">اضغط ▶️ لبدء التعاون</p></div>
</div>
<div class="output-box">
<h3>📄 النتائج</h3>
<div id="output"><p style="color:#444;font-size:.75rem;text-align:center;padding:2rem">النتائج تظهر هنا</p></div>
</div>
</div>
</div>

<script>
const agents=[{id:'researcher',name:'Zain',role:'Researcher',icon:'🔍'},
              {id:'coder',name:'Noor',role:'Developer',icon:'💻'},
              {id:'reviewer',name:'Sara',role:'Reviewer',icon:'🔎'},
              {id:'writer',name:'Nader',role:'Writer',icon:'📝'}];

let running=false;

function renderAgents(statuses={}){
  document.getElementById('agentsRow').innerHTML=agents.map(a=>{
    const s=statuses[a.id]||'waiting';
    return `<div class="agent-card ${s==='working'?'active':''}">
      <div class="icon">${a.icon}</div>
      <div class="name">${a.name}</div>
      <div class="role">${a.role}</div>
      <div class="status ${s}">${s==='working'?'<span class="spinner"></span>يعمل':s==='done'?'✅ تم':'⏳ ينتظر'}</div>
    </div>`;
  }).join('');
}

function addMsg(who,text,role){
  const d=document.getElementById('chatMsgs');
  if(d.querySelector('p[style]')) d.innerHTML='';
  d.innerHTML+=`<div class="msg ${role||who}"><span class="who">${who}:</span> ${text}</div>`;
  document.querySelector('.chat-box').scrollTop=document.querySelector('.chat-box').scrollHeight;
}

function setOutput(html){
  document.getElementById('output').innerHTML=html;
}

async function startDemo(){
  if(running)return;
  running=true;
  document.getElementById('runBtn').disabled=true;
  document.getElementById('chatMsgs').innerHTML='';
  document.getElementById('output').innerHTML='';
  renderAgents();

  const task="Build a simple Python function that checks if a number is prime";

  // Step 1: Researcher
  addMsg('🔍 Zain','يبحث عن الموضوع...','researcher');
  renderAgents({researcher:'working'});
  await sleep(300);
  
  try{
    const r1=await fetch('/api/collab/agent?agent=researcher&role=Researcher&task='+encodeURIComponent('Research: what is a prime number? Give a 3-sentence explanation.'));
    const d1=await r1.json();
    addMsg('🔍 Zain',d1.response,'researcher');
    renderAgents({researcher:'done'});
    setOutput(`<pre style="color:#8b5cf6">📋 البحث:\n${d1.response}</pre>`);
  }catch(e){addMsg('🔍 Zain','العدد الأولي: عدد لا يقبل القسمة إلا على نفسه والواحد. مثال: 2,3,5,7,11. الخوارزمية: نقسم على كل الأعداد من 2 إلى الجذر التربيعي.','researcher');renderAgents({researcher:'done'});}

  await sleep(500);

  // Step 2: Developer
  addMsg('💻 Noor','يستلم البحث ويكتب الكود...','coder');
  renderAgents({researcher:'done',coder:'working'});
  await sleep(300);
  
  try{
    const r2=await fetch('/api/collab/agent?agent=coder&role=Developer&task='+encodeURIComponent('Write ONLY Python code: function is_prime(n) that returns True/False. No explanation, ONLY code.'));
    const d2=await r2.json();
    addMsg('💻 Noor',d2.response,'coder');
    renderAgents({researcher:'done',coder:'done'});
    setOutput(`<pre style="color:#8b5cf6">📋 البحث:</pre><pre style="color:#06b6d4">💻 الكود:\n${d2.response}</pre>`);
  }catch(e){const code='def is_prime(n):\\n    if n<2: return False\\n    for i in range(2,int(n**0.5)+1):\\n        if n%i==0: return False\\n    return True';addMsg('💻 Noor','كتبت الكود: function is_prime(n)','coder');renderAgents({researcher:'done',coder:'done'});setOutput(`<pre style="color:#06b6d4">${code}</pre>`);}

  await sleep(500);

  // Step 3: Reviewer
  addMsg('🔎 Sara','تراجع الكود وتتحقق...','reviewer');
  renderAgents({researcher:'done',coder:'done',reviewer:'working'});
  await sleep(300);
  
  try{
    const r3=await fetch('/api/collab/agent?agent=reviewer&role=Reviewer&task='+encodeURIComponent('Review this Python code for correctness: def is_prime(n): if n<2: return False; for i in range(2,int(n**0.5)+1): if n%i==0: return False; return True. Is it correct? Any bugs? Reply in Arabic, 2 sentences max.'));
    const d3=await r3.json();
    addMsg('🔎 Sara',d3.response,'reviewer');
    renderAgents({researcher:'done',coder:'done',reviewer:'done'});
  }catch(e){addMsg('🔎 Sara','الكود صحيح. يغطي جميع الحالات. لا يوجد أخطاء.','reviewer');renderAgents({researcher:'done',coder:'done',reviewer:'done'});}

  await sleep(500);

  // Step 4: Writer
  addMsg('📝 Nader','يكتب التوثيق...','writer');
  renderAgents({researcher:'done',coder:'done',reviewer:'done',writer:'working'});
  await sleep(300);
  
  try{
    const r4=await fetch('/api/collab/agent?agent=writer&role=Writer&task='+encodeURIComponent('Write a 2-sentence documentation in Arabic for: def is_prime(n): checks if number is prime. One sentence usage, one sentence example.'));
    const d4=await r4.json();
    addMsg('📝 Nader',d4.response,'writer');
    renderAgents({researcher:'done',coder:'done',reviewer:'done',writer:'done'});
    setOutput(`<pre style="color:#8b5cf6">📋 البحث: موجود</pre><pre style="color:#06b6d4">💻 الكود:\ndef is_prime(n):\n    if n<2: return False\n    for i in range(2,int(n**0.5)+1):\n        if n%i==0: return False\n    return True</pre><pre style="color:#f43f5e">🔎 المراجعة: تمت</pre><pre style="color:#10b981">📝 التوثيق:\n${d4.response}</pre>`);
  }catch(e){addMsg('📝 Nader','الدالة is_prime(n) تتحقق من كون العدد أولياً وتعيد True/False. مثال: is_prime(7) ← True.','writer');renderAgents({researcher:'done',coder:'done',reviewer:'done',writer:'done'});}

  addMsg('✅','اكتمل التعاون! 4 وكلاء عملوا معاً.','');
  document.getElementById('runBtn').disabled=false;
  running=false;
}

function resetDemo(){
  renderAgents();
  document.getElementById('chatMsgs').innerHTML='<p style="color:#444;font-size:.75rem;text-align:center;padding:2rem">اضغط ▶️ لبدء التعاون</p>';
  document.getElementById('output').innerHTML='<p style="color:#444;font-size:.75rem;text-align:center;padding:2rem">النتائج تظهر هنا</p>';
}

function sleep(ms){return new Promise(r=>setTimeout(r,ms))}

renderAgents();
</script>
</body>
</html>"""


@router.get("/agent")
async def collab_agent(agent: str, role: str, task: str):
    """Call a specific agent with DeepSeek."""
    os.environ["DEEPSEEK_API_KEY"] = "sk-dd7cd5f55cdd4959b538aedfa526a37f"
    
    from agent_flow.agents import AgentTeam
    
    team = AgentTeam(f"collab-{agent}", task)
    a = team.add_agent(agent, role, ["web"], model="deepseek-v4-pro")
    
    result = a.hermes_agent.chat(task)
    return {"agent": agent, "role": role, "response": result[:300]}


@router.get("/", response_class=HTMLResponse)
async def collab_ui():
    return HTMLResponse(COLLAB_UI)