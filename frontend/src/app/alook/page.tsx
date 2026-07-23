"use client";

import { useEffect, useState } from "react";

export default function AlookPage() {
  const [status, setStatus] = useState<any>(null);
  const [org, setOrg] = useState<any>(null);
  const [exported, setExported] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    const [s, o] = await Promise.all([
      fetch('/api/alook/status').then(r => r.json()),
      fetch('/api/alook/org').then(r => r.json()),
    ]);
    setStatus(s);
    setOrg(o);
  };

  useEffect(() => { load(); }, []);

  const exportOrg = async () => {
    setLoading(true);
    const d = await fetch('/api/alook/export', { method: 'POST' }).then(r => r.json());
    setExported(d);
    setLoading(false);
    load();
  };

  return (
    <div className="p-6 max-w-6xl mx-auto" dir="ltr">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Alook Integration</h1>
          <p className="text-zinc-500 text-sm mt-1">Agent-Flow workforce exported for Alook orchestration</p>
        </div>
        <button
          onClick={exportOrg}
          disabled={loading}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white text-sm font-semibold disabled:opacity-60"
        >
          {loading ? '⏳ Exporting...' : '📦 Export Org Chart'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Stat title="Alook CLI" value={status?.cli_available ? 'Ready' : 'Missing'} />
        <Stat title="CLI Version" value={status?.cli_version || '-'} />
        <Stat title="Brain Agents" value={String(status?.brain_agents || 0)} />
        <Stat title="Constitution" value={status?.constitution_coverage || '-'} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-5">
          <h2 className="text-white font-semibold mb-4">Runtime Status</h2>
          <div className="space-y-2 text-sm">
            <Row k="Web UI (15210)" v={status?.web_running ? 'running' : 'not running'} />
            <Row k="Email Worker (15211)" v={status?.email_worker_running ? 'running' : 'not running'} />
            <Row k="WS Worker (15212)" v={status?.ws_worker_running ? 'running' : 'not running'} />
            <Row k="Export file" v={status?.export_exists ? status?.export_file : 'not generated yet'} />
          </div>
          {exported && (
            <div className="mt-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-3 text-emerald-300 text-sm">
              Exported {exported.agents} agents to <span className="font-mono">{exported.path}</span>
            </div>
          )}
        </section>

        <section className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-5">
          <h2 className="text-white font-semibold mb-4">Alook Value</h2>
          <ul className="space-y-2 text-sm text-zinc-300 list-disc pl-5">
            <li>Email-native orchestration for the same workforce.</li>
            <li>Org-chart export from the live Agent-Flow brain.</li>
            <li>Local-first operation with traceable collaboration.</li>
            <li>Enterprise demo story: planning, research, review, redteam, archive.</li>
          </ul>
        </section>
      </div>

      <section className="mt-6 bg-zinc-900/50 border border-zinc-800 rounded-2xl p-5">
        <h2 className="text-white font-semibold mb-4">Org Chart</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {(org?.org_chart || []).map((agent: any) => (
            <div key={agent.id} className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="text-white font-medium">{agent.name}</p>
                  <p className="text-zinc-500 text-xs">{agent.role}</p>
                </div>
                <span className="text-xs px-2 py-1 rounded bg-zinc-800 text-zinc-300">{agent.id}</span>
              </div>
              <p className="text-zinc-400 text-xs mb-3 leading-relaxed">{agent.specialty}</p>
              <div className="flex flex-wrap gap-1 mb-2">
                {(agent.tools || []).map((t: string) => (
                  <span key={t} className="px-2 py-0.5 rounded bg-violet-500/10 text-violet-300 text-xs">{t}</span>
                ))}
              </div>
              <p className="text-zinc-600 text-xs">reports to: {agent.reports_to || 'none'}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function Stat({ title, value }: { title: string; value: string }) {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-4">
      <p className="text-zinc-500 text-xs mb-2">{title}</p>
      <p className="text-white font-semibold">{value}</p>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-zinc-800/60 pb-2 last:border-0">
      <span className="text-zinc-500">{k}</span>
      <span className="text-white text-right">{v}</span>
    </div>
  );
}
