"use client";

import { useEffect, useState } from "react";
import { api, Team, Interaction, Agent } from "@/lib/api";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowRight, Bot, Activity, MessageSquare, Brain, Target, Zap, Users } from "lucide-react";

export default function TeamDetailPage() {
  const params = useParams();
  const teamName = params.team_name as string;

  const [team, setTeam] = useState<Team & { agents?: Agent[] } | null>(null);
  const [stats, setStats] = useState<{ total_interactions: number; by_type: Record<string, number> } | null>(null);
  const [agents, setAgents] = useState<{ agent_id: string; interactions: number }[]>([]);
  const [history, setHistory] = useState<{ timestamp: string; action: string }[]>([]);

  useEffect(() => {
    api.getTeam(teamName).then(setTeam).catch(() => {});
    api.getInteractionStats(teamName).then(setStats).catch(() => {});
    api.getActiveAgents(teamName).then((a) => setAgents(a.active_agents)).catch(() => {});
    api.getHistory(teamName).then((h) => setHistory(h.history.slice(0, 20))).catch(() => {});
  }, [teamName]);

  if (!team) return <div className="p-8 text-zinc-500">Loading...</div>;

  return (
    <div className="p-8">
      <Link href="/teams" className="inline-flex items-center gap-1 text-zinc-500 hover:text-white text-sm mb-6 transition-colors">
        <ArrowRight className="w-4 h-4" />
        Back to teams
      </Link>

      <div className="flex items-center gap-4 mb-8">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
          <Bot className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">{team.name}</h1>
          <p className="text-zinc-400 text-sm">{team.goal}</p>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
          <Activity className="w-4 h-4 text-violet-400 mb-2" />
          <p className="text-2xl font-bold text-white">{stats?.total_interactions || 0}</p>
          <p className="text-zinc-500 text-xs">Interactions</p>
        </div>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
          <Bot className="w-4 h-4 text-emerald-400 mb-2" />
          <p className="text-2xl font-bold text-white">{agents.length}</p>
          <p className="text-zinc-500 text-xs">Active Agents</p>
        </div>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
          <Target className="w-4 h-4 text-amber-400 mb-2" />
          <p className="text-2xl font-bold text-white">{history.length}+</p>
          <p className="text-zinc-500 text-xs">History Events</p>
        </div>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
          <MessageSquare className="w-4 h-4 text-blue-400 mb-2" />
          <p className="text-2xl font-bold text-white">{Object.keys(stats?.by_type || {}).length}</p>
          <p className="text-zinc-500 text-xs">Interaction Types</p>
        </div>
      </div>

      {/* Two Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Active Agents */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">🤖 Active Agents</h2>
          {agents.length === 0 ? (
            <p className="text-zinc-600 text-sm">No active agents</p>
          ) : (
            <div className="space-y-2">
              {agents.map((a) => (
                <div key={a.agent_id} className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-4 flex items-center justify-between">
                  <span className="text-white text-sm font-medium">{a.agent_id}</span>
                  <span className="text-zinc-500 text-xs">{a.interactions} interactions</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Interaction Types */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">📊 Interaction Types</h2>
          {!stats || Object.keys(stats.by_type).length === 0 ? (
            <p className="text-zinc-600 text-sm">No data</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(stats.by_type).sort(([, a], [, b]) => b - a).slice(0, 10).map(([type, count]) => (
                <div key={type} className="flex items-center gap-3">
                  <span className="text-zinc-400 text-xs w-40 truncate">{type}</span>
                  <div className="flex-1 bg-zinc-800 rounded-full h-2.5 overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-full transition-all"
                      style={{ width: `${Math.min(100, (count / Math.max(...Object.values(stats.by_type))) * 100)}%` }} />
                  </div>
                  <span className="text-zinc-500 text-xs w-8 text-right">{count}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* History */}
        <div className="lg:col-span-2">
          <h2 className="text-lg font-semibold text-white mb-4">📝 History</h2>
          {history.length === 0 ? (
            <p className="text-zinc-600 text-sm">No history yet</p>
          ) : (
            <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-4 max-h-80 overflow-y-auto">
              <div className="space-y-2">
                {history.map((h, i) => (
                  <div key={i} className="flex items-start gap-3 text-sm">
                    <span className="text-zinc-600 text-xs whitespace-nowrap mt-0.5">
                      {new Date(h.timestamp).toLocaleTimeString("ar-EG")}
                    </span>
                    <span className="text-zinc-300">{h.action}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3 mt-8">
        <Link href={`/scenarios`} className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-colors">
          <Zap className="w-4 h-4" /> Run Scenario
        </Link>
        <button className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-5 py-2.5 rounded-xl text-sm font-medium transition-colors">
          <Users className="w-4 h-4" /> Add Agent
        </button>
        <button className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-5 py-2.5 rounded-xl text-sm font-medium transition-colors">
          <MessageSquare className="w-4 h-4" /> Broadcast
        </button>
        <button className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-5 py-2.5 rounded-xl text-sm font-medium transition-colors">
          <Brain className="w-4 h-4" /> Set Goal
        </button>
      </div>
    </div>
  );
}