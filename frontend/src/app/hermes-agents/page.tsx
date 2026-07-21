"use client";

import { useEffect, useState } from "react";

type HermesAgent = {
  name: string;
  job_title: string;
  personality: { curiosity: number; talkativity: number; friendliness: number };
  local_skills: Record<string, number>;
  interactions: number;
  learning_loop?: {
    total_skills: number;
    memory_items: number;
    tasks_completed: number;
    best_skill: string;
  };
};

type ConvMsg = { from: string; msg: string; tick: number };

const COLORS: Record<string, string> = {
  Zain: "#8b5cf6",
  Noor: "#06b6d4",
  Sara: "#f43f5e",
  "🙋": "#f59e0b",
  "💬": "#22c55e",
  "👋": "#3b82f6",
  "🧠": "#a855f7",
  "✨": "#6b7280",
};

export default function HermesAgentsPage() {
  const [agents, setAgents] = useState<Record<string, HermesAgent>>({});
  const [conversations, setConversations] = useState<ConvMsg[]>([]);
  const [tick, setTick] = useState(0);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    try {
      const res = await fetch("/api/agentverse");
      const data = await res.json();
      setAgents(data.agents || {});
      setConversations(data.conversations || []);
      setTick(data.tick || 0);
    } catch {}
  };

  useEffect(() => { load(); }, []);

  const doTick = async (count: number) => {
    setLoading(true);
    await fetch(`/api/agentverse/tick?count=${count}`, { method: "POST" });
    await load();
    setLoading(false);
  };

  const reset = async () => {
    await fetch("/api/agentverse/reset", { method: "POST" });
    await load();
  };

  const agentList = Object.values(agents);

  return (
    <div className="p-6 max-w-5xl mx-auto" dir="ltr">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          🧠 AgentVerse — Powered by DeepSeek
        </h1>
        <p className="text-zinc-500 text-sm">
          وكلاء يتكلمون حقيقياً · يتعلمون · يسألون · يجاوبون · يكتشفون أدوارهم
        </p>
        <div className="flex items-center justify-center gap-3 mt-4">
          <button
            onClick={() => doTick(1)}
            disabled={loading}
            className="px-5 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-700 text-white rounded-xl text-sm font-medium transition-all"
          >
            {loading ? "⏳" : "▶️"} Tick
          </button>
          <button
            onClick={() => doTick(5)}
            disabled={loading}
            className="px-5 py-2.5 bg-violet-700 hover:bg-violet-600 disabled:bg-zinc-700 text-white rounded-xl text-sm font-medium transition-all"
          >
            5x
          </button>
          <button
            onClick={() => doTick(10)}
            disabled={loading}
            className="px-5 py-2.5 bg-violet-800 hover:bg-violet-700 disabled:bg-zinc-700 text-white rounded-xl text-sm font-medium transition-all"
          >
            10x
          </button>
          <button
            onClick={reset}
            className="px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl text-sm transition-all"
          >
            🔄 Reset
          </button>
        </div>
        <p className="text-zinc-600 text-xs mt-2">Tick #{tick}</p>
      </div>

      {/* Agent Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {agentList.map((a) => {
          const color = COLORS[a.name] || "#8b5cf6";
          return (
            <div
              key={a.name}
              className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-5 relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 h-1 w-full" style={{ backgroundColor: color }} />
              
              {/* Name + Title */}
              <div className="flex items-center gap-3 mb-4">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-white text-lg font-bold"
                  style={{ backgroundColor: color }}
                >
                  {a.name[0]}
                </div>
                <div>
                  <p className="text-white font-semibold">{a.name}</p>
                  <p className="text-zinc-400 text-xs">{a.job_title}</p>
                </div>
              </div>

              {/* Personality */}
              <div className="mb-4">
                <div className="flex items-center gap-1 text-xs text-zinc-500 mb-1">
                  <span>🎭</span>
                  <span>Personality</span>
                </div>
                <div className="space-y-1">
                  {Object.entries(a.personality).map(([trait, val]) => (
                    <div key={trait} className="flex items-center gap-2 text-xs">
                      <span className="text-zinc-500 w-20 capitalize">{trait}</span>
                      <div className="flex-1 bg-zinc-800 rounded-full h-2">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{ width: `${val * 100}%`, backgroundColor: color }}
                        />
                      </div>
                      <span className="text-zinc-400 w-8 text-right">{Math.round(val * 100)}%</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Skills */}
              <div className="mb-4">
                <div className="flex items-center gap-1 text-xs text-zinc-500 mb-1">
                  <span>🛠️</span>
                  <span>Skills</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(a.local_skills || {}).slice(0, 5).map(([skill, val]) => (
                    <span
                      key={skill}
                      className="px-2 py-0.5 rounded-lg text-xs font-medium"
                      style={{
                        backgroundColor: `${color}20`,
                        color: color,
                        border: `1px solid ${color}40`,
                      }}
                    >
                      {skill} {(val as number * 100).toFixed(0)}%
                    </span>
                  ))}
                </div>
              </div>

              {/* Learning Loop Stats */}
              {a.learning_loop && (
                <div className="grid grid-cols-2 gap-2 pt-3 border-t border-zinc-800/50">
                  <div className="text-center">
                    <p className="text-white text-sm font-semibold">{a.learning_loop.memory_items}</p>
                    <p className="text-zinc-500 text-[10px]">Memories</p>
                  </div>
                  <div className="text-center">
                    <p className="text-white text-sm font-semibold">{a.learning_loop.total_skills}</p>
                    <p className="text-zinc-500 text-[10px]">Skills</p>
                  </div>
                  <div className="text-center">
                    <p className="text-white text-sm font-semibold">{a.learning_loop.tasks_completed}</p>
                    <p className="text-zinc-500 text-[10px]">Tasks</p>
                  </div>
                  <div className="text-center">
                    <p className="text-white text-sm font-semibold">{a.interactions}</p>
                    <p className="text-zinc-500 text-[10px]">Talks</p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Conversations */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">
          💬 Conversations — {conversations.length} messages
        </h2>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-4 max-h-96 overflow-y-auto space-y-1">
          {conversations.length === 0 ? (
            <p className="text-zinc-600 text-sm text-center py-8">
              اضغط Tick لبدء المحادثات
            </p>
          ) : (
            conversations.slice(-40).map((c, i) => {
              const isQuestion = c.msg.includes("asks:");
              const isAnswer = c.msg.includes(":") && !c.msg.includes("asks:") && !c.msg.includes("learned");
              const isSystem = c.from === "✨" || c.from === "🧠";

              return (
                <div
                  key={i}
                  className={`px-3 py-2 rounded-lg text-sm ${
                    isQuestion
                      ? "bg-violet-900/20 border-l-2 border-violet-500"
                      : isAnswer
                      ? "bg-zinc-800/40"
                      : "bg-zinc-800/20 text-zinc-500 text-xs"
                  }`}
                >
                  {!isSystem && (
                    <span
                      className="inline-block w-5 h-5 rounded-full text-[10px] leading-5 text-center mr-2"
                      style={{
                        backgroundColor: (COLORS[c.msg.split(":")[0]] || "#6b7280") + "30",
                        color: COLORS[c.msg.split(":")[0]] || "#6b7280",
                      }}
                    >
                      {c.msg.split(":")[0]?.[0] || "?"}
                    </span>
                  )}
                  <span className={isSystem ? "text-zinc-500 italic" : "text-zinc-200"}>
                    {c.msg}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Auto-refresh */}
      <p className="text-center text-zinc-700 text-xs mt-6">
        DeepSeek v4-pro · كل نبضة = محادثة حقيقية بين وكلاء
      </p>
    </div>
  );
}