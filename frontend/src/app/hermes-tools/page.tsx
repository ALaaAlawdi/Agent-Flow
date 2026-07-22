"use client";

import { useEffect, useState } from "react";

export default function HermesToolsPage() {
  const [tab, setTab] = useState("kanban");
  const [data, setData] = useState<any>({});

  const load = async (endpoint: string) => {
    try {
      const res = await fetch(`/api/hermes/${endpoint}`);
      const json = await res.json();
      setData(json);
      setTab(endpoint.split("/")[0]);
    } catch {}
  };

  useEffect(() => { load("kanban/stats"); }, []);

  const tabs = [
    { id: "kanban", label: "📋 Kanban", endpoint: "kanban/list" },
    { id: "sessions", label: "📊 Sessions", endpoint: "sessions/stats" },
    { id: "memory", label: "🧠 Memory", endpoint: "memory/status" },
    { id: "insights", label: "📈 Insights", endpoint: "insights" },
    { id: "curator", label: "🔍 Curator", endpoint: "curator/status" },
  ];

  return (
    <div className="p-6 max-w-5xl mx-auto" dir="ltr">
      <h1 className="text-2xl font-bold text-white mb-6">🔧 Hermes CLI Tools</h1>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-zinc-800 pb-3">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => load(t.endpoint)}
            className={`px-4 py-2 rounded-lg text-sm transition-colors ${
              tab === t.id ? "bg-violet-600 text-white" : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6">
        {tab === "kanban" && <KanbanView data={data} reload={() => load("kanban/list")} />}
        {tab === "sessions" && <SessionsView data={data} />}
        {tab === "memory" && <MemoryView data={data} />}
        {tab === "insights" && <InsightsView data={data} />}
        {tab === "curator" && <CuratorView data={data} />}
      </div>
    </div>
  );
}

function KanbanView({ data, reload }: { data: any; reload: () => void }) {
  const tasks = data?.tasks || [];
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");

  const create = async () => {
    if (!title) return;
    await fetch(`/api/hermes/kanban/create?title=${title}`, { method: "POST" });
    setTitle("");
    setCreating(false);
    reload();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">📋 Kanban Board</h2>
        <button onClick={() => setCreating(!creating)} className="px-3 py-1.5 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm">
          + Task
        </button>
      </div>
      
      {creating && (
        <div className="mb-4 flex gap-2">
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Task title..." className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm" />
          <button onClick={create} className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm">Add</button>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        {["todo","in_progress","done","blocked"].map((s) => {
          const count = tasks.filter((t: any) => t.status === s).length;
          const colors: Record<string,string> = { todo: "zinc", in_progress: "blue", done: "emerald", blocked: "red" };
          return (
            <div key={s} className={`bg-${colors[s]}-900/20 border border-${colors[s]}-800/50 rounded-xl p-3 text-center`}>
              <p className={`text-${colors[s]}-400 text-sm font-semibold`}>{s.replace("_"," ")}</p>
              <p className="text-white text-lg font-bold">{count}</p>
            </div>
          );
        })}
      </div>

      <div className="space-y-2">
        {tasks.slice(0, 10).map((t: any) => (
          <div key={t.id} className="flex items-center justify-between bg-zinc-800/40 rounded-lg p-3">
            <div>
              <p className="text-white text-sm">{t.title}</p>
              {t.assignee && <p className="text-zinc-500 text-xs">👤 {t.assignee}</p>}
            </div>
            <span className={`text-xs px-2 py-1 rounded ${
              t.status === "done" ? "bg-emerald-500/20 text-emerald-400" :
              t.status === "in_progress" ? "bg-blue-500/20 text-blue-400" :
              t.status === "blocked" ? "bg-red-500/20 text-red-400" :
              "bg-zinc-600/30 text-zinc-400"
            }`}>{t.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function SessionsView({ data }: { data: any }) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-white mb-4">📊 Sessions</h2>
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-zinc-800/40 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{data?.total_sessions || 0}</p>
          <p className="text-zinc-500 text-xs">Total</p>
        </div>
        <div className="bg-zinc-800/40 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{data?.total_messages || 0}</p>
          <p className="text-zinc-500 text-xs">Messages</p>
        </div>
        <div className="bg-zinc-800/40 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{data?.active_today || 0}</p>
          <p className="text-zinc-500 text-xs">Active Today</p>
        </div>
      </div>
      {data?.by_agent && (
        <div className="text-zinc-400 text-xs">
          <p>By agent: {JSON.stringify(data.by_agent)}</p>
        </div>
      )}
    </div>
  );
}

function MemoryView({ data }: { data: any }) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-white mb-4">🧠 Memory</h2>
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-zinc-800/40 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{data?.total_items || 0}</p>
          <p className="text-zinc-500 text-xs">Items</p>
        </div>
        <div className="bg-zinc-800/40 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{data?.agents || 0}</p>
          <p className="text-zinc-500 text-xs">Agents</p>
        </div>
      </div>
      <p className="text-zinc-400 text-xs mt-4">
        Status: {data?.enabled ? "🟢 Enabled" : "🔴 Disabled"}
      </p>
    </div>
  );
}

function InsightsView({ data }: { data: any }) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-white mb-4">📈 Insights</h2>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-zinc-800/40 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{data?.total_events || 0}</p>
          <p className="text-zinc-500 text-xs">Events</p>
        </div>
        <div className="bg-zinc-800/40 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{data?.sessions || 0}</p>
          <p className="text-zinc-500 text-xs">Sessions</p>
        </div>
        <div className="bg-zinc-800/40 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{data?.kanban_tasks || 0}</p>
          <p className="text-zinc-500 text-xs">Tasks</p>
        </div>
        <div className="bg-zinc-800/40 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{data?.memory_items || 0}</p>
          <p className="text-zinc-500 text-xs">Memories</p>
        </div>
      </div>
    </div>
  );
}

function CuratorView({ data }: { data: any }) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-white mb-4">🔍 Curator — Skill Manager</h2>
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-zinc-800/40 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{data?.total_skills || 0}</p>
          <p className="text-zinc-500 text-xs">Total Skills</p>
        </div>
        <div className="bg-zinc-800/40 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-emerald-400">{data?.active || 0}</p>
          <p className="text-zinc-500 text-xs">Active</p>
        </div>
        <div className="bg-zinc-800/40 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-zinc-400">{data?.archived || 0}</p>
          <p className="text-zinc-500 text-xs">Archived</p>
        </div>
      </div>
    </div>
  );
}