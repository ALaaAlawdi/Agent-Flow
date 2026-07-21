"use client";

import { useEffect, useState } from "react";
import { api, Scenario, ScenarioResult } from "@/lib/api";
import { useParams } from "next/navigation";
import { ArrowRight, Play, CheckCircle, XCircle, Clock, Users, MessageSquare, Zap } from "lucide-react";
import Link from "next/link";

export default function ScenarioDetailPage() {
  const params = useParams();
  const id = params.scenario_id as string;

  const [scenario, setScenario] = useState<(Scenario & { team_config?: Record<string, unknown> }) | null>(null);
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    api.getScenario(id).then(setScenario).catch(() => {});
  }, [id]);

  const run = async () => {
    setRunning(true);
    setResult(null);
    try {
      const r = await api.runScenario(id);
      setResult(r);
    } catch (e) {
      console.error(e);
    }
    setRunning(false);
  };

  if (!scenario) return <div className="p-8 text-zinc-500">Loading...</div>;

  return (
    <div className="p-8">
      {/* Back */}
      <Link
        href="/scenarios"
        className="inline-flex items-center gap-1 text-zinc-500 hover:text-white text-sm mb-6 transition-colors"
      >
        <ArrowRight className="w-4 h-4" />
        Back to scenarios
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div className="flex items-start gap-4">
          <span className="text-4xl">{scenario.icon}</span>
          <div>
            <h1 className="text-2xl font-bold text-white">{scenario.title}</h1>
            <p className="text-zinc-400 text-sm mt-1">{scenario.description}</p>
            <div className="flex items-center gap-4 mt-3 text-sm text-zinc-500">
              <span className="flex items-center gap-1"><Users className="w-3.5 h-3.5" /> {scenario.team_size} agents</span>
              <span className="flex items-center gap-1"><MessageSquare className="w-3.5 h-3.5" /> {scenario.step_count} steps</span>
              <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> {scenario.estimated_time}</span>
            </div>
          </div>
        </div>

        <button
          onClick={run}
          disabled={running}
          className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-700 text-white px-6 py-3 rounded-xl transition-colors text-sm font-medium"
        >
          <Play className={`w-4 h-4 ${running ? "animate-pulse" : ""}`} />
          {running ? "Running..." : "Run Scenario"}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="space-y-6">
          {/* Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
              <p className="text-zinc-500 text-xs mb-1">Team</p>
              <p className="text-white font-semibold">{result.team_name}</p>
            </div>
            <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
              <p className="text-zinc-500 text-xs mb-1">Steps</p>
              <p className="text-emerald-400 font-semibold">
                {result.successful_steps}/{result.steps_executed}
              </p>
            </div>
            <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
              <p className="text-zinc-500 text-xs mb-1">Interactions</p>
              <p className="text-white font-semibold">{result.stats.interactions.total_interactions}</p>
            </div>
            <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
              <p className="text-zinc-500 text-xs mb-1">Agents</p>
              <p className="text-white font-semibold">{result.agents_added.length}</p>
            </div>
          </div>

          {/* Agents */}
          <div>
            <h2 className="text-lg font-semibold text-white mb-3">🤖 Agents</h2>
            <div className="flex flex-wrap gap-2">
              {result.agents_added.map((a) => (
                <span key={a} className="bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-lg text-sm border border-zinc-700">
                  {a}
                </span>
              ))}
            </div>
          </div>

          {/* Active Agents */}
          <div>
            <h2 className="text-lg font-semibold text-white mb-3">⚡ Active Agents</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {result.stats.active_agents.map((a) => (
                <div key={a.agent_id} className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-3 flex items-center justify-between">
                  <span className="text-white text-sm">{a.agent_id}</span>
                  <span className="text-zinc-500 text-xs">{a.interactions} interactions</span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2 p-4 bg-zinc-900/40 border border-zinc-800 rounded-xl">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <span className="text-emerald-400 text-sm font-medium">
              ✅ Scenario &quot;{scenario.title}&quot; completed successfully!
            </span>
          </div>
        </div>
      )}

      {!result && !running && (
        <div className="flex items-center justify-center py-20 text-zinc-600">
          <p className="text-center">Click &quot;Run Scenario&quot; to start</p>
        </div>
      )}
    </div>
  );
}