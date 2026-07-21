"""AgentVerse UI — simple HTML page for the Hermes-powered world."""

from fastapi.responses import HTMLResponse

AGENTVERSE_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<title>AgentVerse — وكلاء يتكلمون</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f0f23;color:#e0e0e0;font-family:system-ui,sans-serif;padding:2rem;max-width:800px;margin:auto}
h1{font-size:1.5rem;margin-bottom:.5rem;background:linear-gradient(135deg,#8b5cf6,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{color:#666;font-size:.85rem;margin-bottom:2rem}
.agent-card{background:#1a1a3e;border-radius:12px;padding:1rem;margin-bottom:1rem;border:1px solid #2a2a5e}
.agent-name{font-weight:700;font-size:1.1rem}
.agent-job{color:#888;font-size:.85rem}
.agent-stats{display:flex;gap:1rem;margin-top:.5rem;font-size:.8rem;color:#666}
.conversation{padding:.8rem 1rem;border-radius:8px;margin-bottom:.3rem;font-size:.9rem}
.ask{background:#2a1a5e;border-right:3px solid #8b5cf6}
.answer{background:#1a2a3e;border-right:3px solid #06b6d4}
.system{background:#1a1a1a;border-right:3px solid #666;color:#888;font-size:.8rem}
.controls{display:flex;gap:.5rem;margin:1.5rem 0}
button{padding:.6rem 1.2rem;border:none;border-radius:8px;font-size:.9rem;cursor:pointer;transition:all .2s}
.btn-tick{background:#8b5cf6;color:#fff}
.btn-tick:hover{background:#7c3aed}
.btn-reset{background:#333;color:#ccc}
.btn-reset:hover{background:#444}
.msg-from{color:#888;font-size:.75rem}
.loading{text-align:center;padding:2rem;color:#666}
</style>
</head>
<body>
<h1>🌍 AgentVerse</h1>
<p class="sub">وكلاء يتكلمون بـ DeepSeek — محادثات حقيقية، ذكاء حقيقي</p>

<div class="controls">
<button class="btn-tick" onclick="tick()">▶️ نبضة (تick)</button>
<button class="btn-tick" onclick="tick5()">▶️▶️ 5 نبضات</button>
<button class="btn-reset" onclick="reset()">🔄 إعادة</button>
<button class="btn-reset" onclick="refresh()">🔄 تحديث</button>
</div>

<div id="agents"></div>
<h2 style="margin:1.5rem 0 .5rem;font-size:1.1rem">💬 المحادثات</h2>
<div id="conversations" class="loading">⏳ جاري التحميل...</div>

<script>
const API = '/agentverse';

async function load() {
  try {
    const res = await fetch(API + '/');
    const data = await res.json();

    // Agents
    const agentsDiv = document.getElementById('agents');
    agentsDiv.innerHTML = Object.values(data.agents).map(a => `
      <div class="agent-card">
        <div class="agent-name">${a.name}</div>
        <div class="agent-job">${a.job_title}</div>
        <div class="agent-stats">
          <span>💬 ${a.interactions} تفاعل</span>
          <span>🧠 مهارات: ${Object.keys(a.skills).slice(0,3).join('، ')}</span>
          <span>🎭 ${a.personality.curiosity > 0.8 ? 'فضولي' : a.personality.talkativity > 0.8 ? 'اجتماعي' : 'متوازن'}</span>
        </div>
      </div>
    `).join('');

    // Conversations 
    const convDiv = document.getElementById('conversations');
    const conv = data.conversations || [];
    if (conv.length === 0) {
      convDiv.innerHTML = '<div class="loading">لا توجد محادثات بعد. اضغط نبضة!</div>';
      return;
    }
    convDiv.innerHTML = conv.map(c => {
      const msg = c.msg || '';
      let cls = 'system';
      if (msg.includes('asks:')) cls = 'ask';
      else if (msg.includes('💬') || msg.includes(':') && !msg.includes('✨') && !msg.includes('🧠')) cls = 'answer';
      const first = msg.split(':')[0] || '';
      return `<div class="conversation ${cls}"><span class="msg-from">${first}</span> ${msg.slice(first.length+1).trim()}</div>`;
    }).join('');
    agentsDiv.scrollIntoView({behavior:'smooth'});
  } catch(e) {
    document.getElementById('conversations').innerHTML = `<div class="loading">❌ خطأ: ${e.message}</div>`;
  }
}

async function tick() {
  document.getElementById('conversations').innerHTML = '<div class="loading">⏳ وكلاء يتكلمون...</div>';
  await fetch(API + '/tick?count=3', {method:'POST'});
  load();
}

async function tick5() {
  document.getElementById('conversations').innerHTML = '<div class="loading">⏳ 5 نبضات...</div>';
  await fetch(API + '/tick?count=5', {method:'POST'});
  load();
}

async function reset() {
  await fetch(API + '/reset', {method:'POST'});
  load();
}

function refresh() { load(); }
load();
</script>
</body>
</html>
"""

def get_agentverse_ui():
    return HTMLResponse(AGENTVERSE_HTML)