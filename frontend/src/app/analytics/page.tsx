"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { BarChart3, Activity } from "lucide-react";

export default function AnalyticsPage() {
  const [teams, setTeams] = useState<{ name: string }[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<string>("");
  const [stats, setStats] = useState<Record<string, number> | null>(null);

  useEffect(() => {
    api.listTeams().then((t) => {
      setTeams(t.teams);
      if (t.teams.length > 0) setSelectedTeam(t.teams[0].name);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedTeam) return;
    api.getTeamStats(selectedTeam).then((s) => setStats(s.by_type)).catch(() => {});
  }, [selectedTeam]);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-white mb-2">📊 Analytics</h1>
      <p className="text-zinc-400 text-sm mb-6">Interaction breakdown by type</p>

      <div className="mb-6">
        <select
          value={selectedTeam}
          onChange={(e) => setSelectedTeam(e.target.value)}
          className="bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-violet-500/50"
        >
          {teams.map((t) => (
            <option key={t.name} value={t.name}>{t.name}</option>
          ))}
        </select>
      </div>

      {stats && (
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-6">
          <div className="space-y-3">
            {Object.entries(stats)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 20)
              .map(([type, count]) => (
                <div key={type} className="flex items-center gap-4">
                  <span className="text-zinc-400 text-sm w-48 truncate">{type}</span>
                  <div className="flex-1 bg-zinc-800 rounded-full h-3 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-full transition-all"
                      style={{ width: `${Math.min(100, (count / Math.max(...Object.values(stats))) * 100)}%` }}
                    />
                  </div>
                  <span className="text-zinc-500 text-xs w-12 text-left">{count}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {!stats && (
        <div className="flex flex-col items-center justify-center py-20 text-zinc-600">
          <BarChart3 className="w-12 h-12 mb-4 opacity-30" />
          <Activity className="w-12 h-12 mb-4 opacity-30" />
          <p>No data. Run a scenario first.</p>
        </div>
      )}
    </div>
  );
}