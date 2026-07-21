"use client";

import { useEffect, useState } from "react";
import { api, Team } from "@/lib/api";
import Link from "next/link";
import { Database } from "lucide-react";

export default function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);

  useEffect(() => {
    api.listTeams().then((t) => setTeams(t.teams)).catch(() => {});
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-white mb-2">🤖 Teams</h1>
      <p className="text-zinc-400 text-sm mb-6">Teams created via demo scenarios or API</p>

      {teams.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-zinc-600">
          <Database className="w-12 h-12 mb-4 opacity-30" />
          <p>No teams yet. Run a scenario first.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {teams.map((t) => (
            <Link
              key={t.name}
              href={`/teams/${t.name}`}
              className="bg-zinc-900/40 hover:bg-zinc-900/80 border border-zinc-800 rounded-xl p-5 transition-colors"
            >
              <h3 className="text-white font-medium mb-1">{t.name}</h3>
              <p className="text-zinc-500 text-xs mb-3">{t.goal}</p>
              <span className="text-zinc-600 text-xs">{new Date(t.created_at).toLocaleDateString("ar-EG")}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}