"use client";

import { useState, useEffect } from "react";

type Msg = { role: "user" | "agent"; text: string; agent?: string; time: number };

export default function BrainChatPage() {
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("اكتب كود بايثون يحسب الأعداد الأولية");
  const [loading, setLoading] = useState(false);
  const [turn, setTurn] = useState(0);
  const [activeAgent, setActiveAgent] = useState("");

  const send = async () => {
    if (!input.trim() || loading) return;
    const task = input.trim();
    setInput("");
    setLoading(true);

    setMessages(prev => [...prev, { role: "user", text: task, time: Date.now() }]);

    try {
      const res = await fetch(`/api/brain/chat?task=${encodeURIComponent(task)}&session_id=${sessionId}`, { method: "POST" });
      const d = await res.json();
      if (!sessionId) setSessionId(d.session_id);
      
      setActiveAgent(d.agent);
      setTurn(d.turn);
      setMessages(prev => [...prev, { 
        role: "agent", 
        text: d.response || "No response", 
        agent: `${d.agent} (${d.role})`,
        time: Date.now() 
      }]);
    } catch (e: any) {
      setMessages(prev => [...prev, { role: "agent", text: "Error: " + e.message, time: Date.now() }]);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#08081a] flex flex-col" dir="ltr">
      {/* Header */}
      <div className="text-center py-6 border-b border-zinc-800/50">
        <h1 className="text-xl font-bold text-white">🧠 Agent Brain Chat</h1>
        <p className="text-zinc-500 text-xs mt-1">
          محادثة متعددة الأدوار — الوكيل يتذكر السياق
          {sessionId && <span className="text-zinc-600 ml-2">· Session: {sessionId}</span>}
          {turn > 0 && <span className="text-zinc-600 ml-2">· Turn: {turn}</span>}
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 max-w-3xl mx-auto w-full space-y-3" style={{ maxHeight: "calc(100vh - 180px)" }}>
        {messages.length === 0 && (
          <div className="text-center py-16">
            <p className="text-4xl mb-4">🧠</p>
            <p className="text-zinc-500 text-sm">اكتب مهمة — Brain يختار الوكيل تلقائياً</p>
            <div className="flex gap-2 justify-center mt-4 flex-wrap">
              {["اكتب كود بايثون لحساب factorial","اشرح كيف يتعلم الذكاء الاصطناعي","راجع هذا الكود: def sort(arr): return sorted(arr)","اكتب توثيق لـ REST API"].map((s,i) => (
                <button key={i} onClick={() => { setInput(s); }} className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-zinc-400 text-xs transition-colors">{s.substring(0,25)}...</button>
              ))}
            </div>
          </div>
        )}
        
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${
              m.role === "user" 
                ? "bg-violet-600 text-white" 
                : "bg-zinc-900 border border-zinc-800 text-zinc-200"
            }`}>
              {m.agent && <p className="text-xs text-violet-400 mb-1 font-semibold">🤖 {m.agent}</p>}
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{m.text}</p>
              <p className="text-xs text-zinc-600 mt-1">{new Date(m.time).toLocaleTimeString("ar-SA", { hour: "2-digit", minute: "2-digit" })}</p>
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="flex justify-start">
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl px-4 py-3 flex items-center gap-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full bg-violet-500 animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-2 h-2 rounded-full bg-violet-500 animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-2 h-2 rounded-full bg-violet-500 animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
              <p className="text-zinc-500 text-sm">{activeAgent || "Brain"} is thinking...</p>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-zinc-800/50 p-4">
        <div className="max-w-3xl mx-auto flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && send()}
            placeholder="اكتب مهمتك... Brain يختار الوكيل المناسب"
            className="flex-1 bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-violet-500"
            dir="rtl"
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            className="px-6 py-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 disabled:from-zinc-700 disabled:to-zinc-700 text-white rounded-xl font-semibold text-sm transition-all"
          >
            {loading ? "⏳" : "▶️"}
          </button>
        </div>
        <p className="text-zinc-600 text-xs text-center mt-2">اضغط Enter للإرسال · الوكيل يتذكر المحادثة كاملة</p>
      </div>
    </div>
  );
}