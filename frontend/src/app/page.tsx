"use client";

import { useEffect, useState } from "react";
import { api, Scenario, Team } from "@/lib/api";
import { Bot, Cpu, Play, Activity, Zap, Globe, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function HomePage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [health, setHealth] = useState("checking...");
  const [totalInteractions, setTotalInteractions] = useState(0);

  useEffect(() => {
    api.health().then((h) => setHealth(h.status)).catch(() => setHealth("offline"));
    api.listScenarios().then((s) => setScenarios(s.scenarios.slice(0, 4))).catch(() => {});
    api.listTeams().then(async (t) => {
      setTeams(t.teams);
      let total = 0;
      for (const team of t.teams.slice(0, 5)) {
        try {
          const s = await api.getInteractionStats(team.name);
          total += s.total_interactions;
        } catch {}
      }
      setTotalInteractions(total);
    }).catch(() => {});
  }, []);

  const statCards = [
    { label: "Cognitive Capabilities", value: "21", icon: Cpu, color: "from-violet-500 to-purple-500" },
    { label: "API Endpoints", value: "83", icon: Zap, color: "from-blue-500 to-cyan-500" },
    { label: "AI Models", value: `${scenarios.length}+`, icon: Globe, color: "from-emerald-500 to-teal-500" },
    { label: "Interactions", value: totalInteractions > 0 ? `${totalInteractions}` : "–", icon: Activity, color: "from-amber-500 to-orange-500" },
  ];

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Agent-Flow</h1>
            <p className="text-zinc-400 text-sm mt-1">
              Multi-agent platform · <span className={health === "healthy" ? "text-emerald-400" : "text-red-400"}>{health}</span>
            </p>
          </div>
          <Link
            href="/scenarios"
            className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 text-white px-5 py-2.5 rounded-xl transition-colors text-sm font-medium"
          >
            <Play className="w-4 h-4" />
            Run Demo
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((card) => (
          <div
            key={card.label}
            className="relative bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 overflow-hidden"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-zinc-500 text-xs mb-1">{card.label}</p>
                <p className="text-2xl font-bold text-white">{card.value}</p>
              </div>
              <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${card.color} p-2.5`}>
                <card.icon className="w-5 h-5 text-white" />
              </div>
            </div>
            <div className={`absolute bottom-0 left-0 h-0.5 w-full bg-gradient-to-r ${card.color} opacity-30`} />
          </div>
        ))}
      </div>

      {/* Two columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Scenarios */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">🚀 Demo Scenarios</h2>
          <div className="space-y-3">
            {scenarios.slice(0, 5).map((s) => (
              <Link
                key={s.scenario_id}
                href={`/scenarios/${s.scenario_id}`}
                className="flex items-center gap-4 bg-zinc-900/40 hover:bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 transition-colors group"
              >
                <span className="text-2xl">{s.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-medium group-hover:text-violet-400 transition-colors">
                    {s.title}
                  </p>
                  <p className="text-zinc-500 text-xs mt-0.5">{s.description}</p>
                </div>
                <span className="text-xs text-zinc-600 whitespace-nowrap">
                  {s.team_size} agents
                </span>
              </Link>
            ))}
          </div>
        </div>

        {/* Live Activity */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">🤖 Active Teams</h2>
          <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400 text-sm font-medium">
                {totalInteractions > 0 ? `${totalInteractions} interactions across ${teams.length} teams` : "No teams yet"}
              </span>
            </div>
            <div className="space-y-2">
              {teams.length === 0 ? (
                <p className="text-zinc-600 text-sm text-center py-6">
                  Run a scenario to start tracking agent interactions
                </p>
              ) : (
                teams.map((t) => (
                  <Link
                    key={t.name}
                    href={`/teams/${t.name}`}
                    className="flex items-center justify-between bg-zinc-800/50 hover:bg-zinc-800 rounded-lg p-3 transition-colors group"
                  >
                    <div>
                      <p className="text-white text-sm font-medium group-hover:text-violet-400 transition-colors">{t.name}</p>
                      <p className="text-zinc-500 text-xs mt-0.5">{t.goal.slice(0, 60)}</p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-zinc-600 group-hover:text-violet-400 transition-colors" />
                  </Link>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}