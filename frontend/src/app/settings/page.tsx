"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [health, setHealth] = useState("");
  const [models, setModels] = useState<{ short_name: string; provider: string }[]>([]);
  const [defaultModel, setDefaultModel] = useState("");

  useEffect(() => {
    api.health().then((h) => setHealth(h.status)).catch(() => setHealth("offline"));
    api.listModels().then((m) => setModels(m.models)).catch(() => {});
    api.defaultModel().then((d) => setDefaultModel(`${d.provider}/${d.model}`)).catch(() => {});
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-white mb-2">⚙️ Settings</h1>
      <p className="text-zinc-400 text-sm mb-8">Agent-Flow server configuration and models</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Server Status */}
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-white font-semibold mb-4">Server</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-zinc-400 text-sm">Status</span>
              <span className={`text-sm font-medium ${health === "healthy" ? "text-emerald-400" : "text-red-400"}`}>
                {health === "healthy" ? "🟢 Online" : "🔴 Offline"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-400 text-sm">Default Model</span>
              <span className="text-white text-sm">{defaultModel || "–"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-400 text-sm">API Endpoints</span>
              <span className="text-white text-sm">83</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-400 text-sm">Cognitive Capabilities</span>
              <span className="text-white text-sm">21</span>
            </div>
          </div>
        </div>

        {/* Models */}
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-white font-semibold mb-4">Models</h2>
          <div className="max-h-64 overflow-y-auto space-y-2">
            {models.map((m) => (
              <div key={m.short_name} className="flex items-center justify-between py-1.5 border-b border-zinc-800/50 last:border-0">
                <span className="text-white text-sm">{m.short_name}</span>
                <span className="text-zinc-500 text-xs">{m.provider}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}