"use client";

import { useEffect, useState } from "react";
import { api, Scenario } from "@/lib/api";
import Link from "next/link";
import { Search } from "lucide-react";

export default function ScenariosPage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.listScenarios().then((s) => setScenarios(s.scenarios)).catch(() => {});
  }, []);

  const filtered = scenarios.filter((s) =>
    s.title.includes(search) || s.description.includes(search)
  );

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">🚀 Demo Scenarios</h1>
        <p className="text-zinc-400 text-sm mt-1">
          One-click scenarios that pre-fill teams, agents, and run realistic workflows
        </p>
      </div>

      {/* Search */}
      <div className="relative mb-6 max-w-md">
        <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
        <input
          type="text"
          placeholder="Search scenarios..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-zinc-900 border border-zinc-800 rounded-xl py-2.5 pr-10 text-white text-sm placeholder-zinc-500 focus:outline-none focus:border-violet-500/50 transition-colors"
        />
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map((s) => (
          <Link
            key={s.scenario_id}
            href={`/scenarios/${s.scenario_id}`}
            className="bg-zinc-900/40 hover:bg-zinc-900/80 border border-zinc-800 rounded-xl p-5 transition-all hover:border-violet-500/30 group"
          >
            <span className="text-3xl block mb-3">{s.icon}</span>
            <h3 className="text-white font-medium text-sm group-hover:text-violet-400 transition-colors">
              {s.title}
            </h3>
            <p className="text-zinc-500 text-xs mt-1.5 line-clamp-2">{s.description}</p>
            <div className="flex items-center gap-3 mt-4 text-xs text-zinc-600">
              <span>👥 {s.team_size} agents</span>
              <span>📝 {s.step_count} steps</span>
              <span>⏱️ {s.estimated_time}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}