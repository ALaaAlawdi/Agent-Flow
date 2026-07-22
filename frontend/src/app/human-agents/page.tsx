"use client";

import { useEffect, useState } from "react";

type Personality = { curiosity: number; caution: number; sociability: number; persistence: number; creativity: number };
type Agent = { name: string; role: string; personality: Personality; mood: string; age: number; memory: { mistakes: number; successes: number; recent_lessons: string[]; known_agents: number } };
type Event = { time: number; event: string };

const COLORS: Record<string, string> = {
  Zain: "#8b5cf6",
  Noor: "#06b6d4",
  Sara: "#f43f5e",
};

export default function HumanAgentsPage() {
  const [agents, setAgents] = useState<Record<string, Agent>>({});
  const [events, setEvents] = useState<Event[]>([]);
  const [time, setTime] = useState(0);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    try {
      const res = await fetch("/api/society/");
      const data = await res.json();
      setAgents(data.agents || {});
      setEvents((data.conversations || []).slice(-30));
      setTime(data.time || 0);
    } catch {}
  };

  useEffect(() => { load(); }, []);

  const step = async (count: number) => {
    setLoading(true);
    await fetch(`/api/society/step?count=${count}`, { method: "POST" });
    await load();
    setLoading(false);
  };

  const reset = async () => {
    await fetch("/api/society/reset", { method: "POST" });
    await load();
  };

  const agentList = Object.values(agents);

  return (
    <div className="p-6 max-w-6xl mx-auto" dir="ltr">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          🧠 Human-Like Agents
        </h1>
        <p className="text-zinc-500 text-sm">
          وكلاء يبدأون من الصفر · يتعلمون من أخطائهم · يتواصلون مع بعضهم
        </p>
        <div className="flex items-center justify-center gap-3 mt-4">
          <button onClick={() => step(1)} disabled={loading} className="px-5 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-700 text-white rounded-xl text-sm font-medium">
            {loading ? "⏳" : "▶️"} Step
          </button>
          <button onClick={() => step(5)} disabled={loading} className="px-5 py-2.5 bg-violet-700 hover:bg-violet-600 disabled:bg-zinc-700 text-white rounded-xl text-sm">
            5x
          </button>
          <button onClick={() => step(15)} disabled={loading} className="px-5 py-2.5 bg-violet-800 hover:bg-violet-700 disabled:bg-zinc-700 text-white rounded-xl text-sm">
            15x
          </button>
          <button onClick={reset} className="px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl text-sm">
            🔄 Reset
          </button>
        </div>
        <p className="text-zinc-600 text-xs mt-2">Step #{time}</p>
      </div>

      {/* Agent Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {agentList.map((a) => {
          const color = COLORS[a.name] || "#8b5cf6";
          const mom = a.memory || { mistakes: 0, successes: 0, recent_lessons: [], known_agents: 0 };
          const moodEmoji = { happy: "😊", frustrated: "😤", curious: "🤔", confident: "💪", neutral: "😐" }[a.mood || "neutral"] || "😐";
          
          return (
            <div key={a.name} className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-5 relative">
              <div className="absolute top-0 left-0 h-1 w-full" style={{ backgroundColor: color }} />
              
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white text-lg font-bold" style={{ backgroundColor: color }}>
                  {a.name[0]}
                </div>
                <div>
                  <p className="text-white font-semibold">{a.name} {moodEmoji}</p>
                  <p className="text-zinc-400 text-xs">{a.role}</p>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-2 mb-4 text-center">
                <div>
                  <p className="text-red-400 text-sm font-semibold">{mom.mistakes}</p>
                  <p className="text-zinc-500 text-[10px]">Mistakes</p>
                </div>
                <div>
                  <p className="text-emerald-400 text-sm font-semibold">{mom.successes}</p>
                  <p className="text-zinc-500 text-[10px]">Successes</p>
                </div>
              </div>

              {/* Lessons learned */}
              <div className="mb-3">
                <p className="text-zinc-500 text-[10px] mb-1">📝 Lessons from mistakes:</p>
                {mom.recent_lessons?.length > 0 ? mom.recent_lessons.slice(-2).map((l, i) => (
                  <p key={i} className="text-zinc-400 text-xs mb-1 border-l-2 border-amber-500/50 pl-2">{l}</p>
                )) : <p className="text-zinc-600 text-xs italic">No mistakes yet — still innocent</p>}
              </div>

              {/* Personality */}
              <div className="pt-3 border-t border-zinc-800/50">
                <div className="flex flex-wrap gap-1">
                  {Object.entries(a.personality || {}).slice(0, 5).map(([trait, val]) => (
                    <span key={trait} className="px-2 py-0.5 rounded text-[10px]" style={{ backgroundColor: `${color}15`, color }}>
                      {trait}: {Math.round((val as number) * 100)}%
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Event Log */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">📜 Life Events</h2>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-4 max-h-80 overflow-y-auto space-y-1">
          {events.length === 0 ? (
            <p className="text-zinc-600 text-sm text-center py-8">No events yet. Press Step.</p>
          ) : (
            events.map((e, i) => {
              const isError = e.event.startsWith("❌");
              const isSuccess = e.event.startsWith("✅");
              const isTalk = e.event.startsWith("💬");
              const isReflect = e.event.startsWith("🧠");
              
              return (
                <div key={i} className={`px-3 py-1.5 rounded-lg text-sm ${
                  isError ? "bg-red-900/20 border-l-2 border-red-500" :
                  isSuccess ? "bg-emerald-900/20 border-l-2 border-emerald-500" :
                  isTalk ? "bg-blue-900/20 border-l-2 border-blue-500" :
                  isReflect ? "bg-violet-900/20 border-l-2 border-violet-500" :
                  "bg-zinc-800/40"
                }`}>
                  <span className="text-zinc-200">{e.event}</span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}